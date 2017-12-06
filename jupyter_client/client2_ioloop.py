import atexit
import errno
from functools import partial
from threading import Thread, Event
from zmq import ZMQError
from zmq.eventloop import ioloop, zmqstream

from .client2 import KernelClient2
from .util import inherit_docstring


class IOLoopKernelClient2(KernelClient2):
    """Uses a zmq/tornado IOLoop to handle received messages and fire callbacks.

    Use ClientInThread to run this in a separate thread alongside your
    application.
    """
    def __init__(self, connection_info, **kwargs):
        super(IOLoopKernelClient2, self).__init__(connection_info, **kwargs)
        self.ioloop = ioloop.IOLoop.current()
        self.handlers = {
            'iopub': [],
            'shell': [self._auto_adapt],
            'stdin': [],
            'control': [],
        }
        self.shell_stream = zmqstream.ZMQStream(self.shell_socket, self.ioloop)
        self.shell_stream.on_recv(partial(self._handle_recv, 'shell'))
        self.iopub_stream = zmqstream.ZMQStream(self.iopub_socket, self.ioloop)
        self.iopub_stream.on_recv(partial(self._handle_recv, 'iopub'))
        self.stdin_stream = zmqstream.ZMQStream(self.stdin_socket, self.ioloop)
        self.stdin_stream.on_recv(partial(self._handle_recv, 'stdin'))
        self.control_stream = zmqstream.ZMQStream(self.control_socket, self.ioloop)
        self.control_stream.on_recv(partial(self._handle_recv, 'control'))

    def close(self):
        """Close the client's sockets & streams.

        This does not close the IOLoop.
        """
        self.shell_stream.close()
        self.iopub_stream.close()
        self.stdin_stream.close()
        self.control_stream.close()
        if self.hb_monitor:
            self.hb_monitor.stop()

    def _auto_adapt(self, msg):
        """Use the first kernel_info_reply to set up protocol version adaptation
        """
        if msg['header']['msg_type'] == 'kernel_info_reply':
            self._handle_kernel_info_reply(msg)
            self.remove_handler('shell', self._auto_adapt)

    def _handle_recv(self, channel, msg):
        """Callback for stream.on_recv.

        Unpacks message, and calls handlers with it.
        """
        ident, smsg = self.session.feed_identities(msg)
        msg = self.session.deserialize(smsg)
        self._call_handlers(channel, msg)

    def _call_handlers(self, channel, msg):
        # [:] copies the list - handlers that remove themselves (or add other
        # handlers) will not mess up iterating over it.
        for handler in self.handlers[channel][:]:
            try:
                handler(msg)
            except Exception as e:
                self.log.error("Exception from message handler %r", handler,
                               exc_info=e)

    def add_handler(self, channel, handler):
        """Add a callback for received messages on one channel.

        Parameters
        ----------

        channel : str
          One of 'shell', 'iopub', 'stdin' or 'control'
        handler : function
          Will be called for each message received with the message dictionary
          as a single argument.
        """
        self.handlers[channel].append(handler)

    def remove_handler(self, channel, handler):
        """Remove a previously registered callback."""
        self.handlers[channel].remove(handler)

class ClientInThread(Thread):
    """Run an IOLoopKernelClient2 in a separate thread.

    The main client methods (execute, complete, etc.) all pass their arguments
    to the ioloop thread, which sends the messages. Handlers for received
    messages will be called in the ioloop thread, so they should typically
    use a signal or callback mechanism to interact with the application in
    the main thread.
    """
    client = None
    _exiting = False

    def __init__(self, connection_info, manager=None, loop=None):
        super(ClientInThread, self).__init__()
        self.daemon = True
        self.connection_info = connection_info
        self.manager = manager
        self.started = Event()

    @staticmethod
    @atexit.register
    def _notice_exit():
        ClientInThread._exiting = True

    def run(self):
        """Run my loop, ignoring EINTR events in the poller"""
        loop = ioloop.IOLoop(make_current=True)
        self.client = IOLoopKernelClient2(self.connection_info, manager=self.manager)
        self.client.ioloop.add_callback(self.started.set)
        try:
            self._run_loop()
        finally:
            self.client.close()
            self.client.ioloop.close()
            self.client = None

    def _run_loop(self):
        while True:
            try:
                self.client.ioloop.start()
            except ZMQError as e:
                if e.errno == errno.EINTR:
                    continue
                else:
                    raise
            except Exception:
                if self._exiting:
                    break
                else:
                    raise
            else:
                break

    @property
    def ioloop(self):
        if self.client:
            return self.client.ioloop

    def close(self):
        """Shut down the client and wait for the thread to exit.

        This closes the client's sockets and ioloop, and joins its thread.
        """
        if self.client is not None:
            self.ioloop.add_callback(self.client.ioloop.stop)
            self.join()

    @inherit_docstring(IOLoopKernelClient2)
    def add_handler(self, channel, handler):
        self.client.handlers[channel].append(handler)

    @inherit_docstring(IOLoopKernelClient2)
    def remove_handler(self, channel, handler):
        self.client.handlers[channel].remove(handler)

    # Client messaging methods --------------------------------
    # These send as much work as possible to the IO thread, but we generate
    # the header in the calling thread so we can return the message ID.

    @inherit_docstring(KernelClient2)
    def execute(self, *args, **kwargs):
        hdr = self.client.session.msg_header('execute_request')
        self.ioloop.add_callback(self.client.execute, *args, _header=hdr, **kwargs)
        return hdr['msg_id']

    @inherit_docstring(KernelClient2)
    def complete(self, *args, **kwargs):
        hdr = self.client.session.msg_header('complete_request')
        self.ioloop.add_callback(self.client.complete, *args, _header=hdr, **kwargs)
        return hdr['msg_id']

    @inherit_docstring(KernelClient2)
    def inspect(self, *args, **kwargs):
        hdr = self.client.session.msg_header('inspect_request')
        self.ioloop.add_callback(self.client.inspect, *args, _header=hdr, **kwargs)
        return hdr['msg_id']

    @inherit_docstring(KernelClient2)
    def history(self, *args, **kwargs):
        hdr = self.client.session.msg_header('history_request')
        self.ioloop.add_callback(self.client.history, *args, _header=hdr, **kwargs)
        return hdr['msg_id']

    @inherit_docstring(KernelClient2)
    def kernel_info(self, _header=None):
        hdr = self.client.session.msg_header('kernel_info_request')
        self.ioloop.add_callback(self.client.kernel_info, _header=hdr)
        return hdr['msg_id']

    @inherit_docstring(KernelClient2)
    def comm_info(self, target_name=None, _header=None):
        hdr = self.client.session.msg_header('comm_info_request')
        self.ioloop.add_callback(self.client.comm_info, target_name, _header=hdr)
        return hdr['msg_id']

    @inherit_docstring(KernelClient2)
    def shutdown(self, restart=False, _header=None):
        hdr = self.client.session.msg_header('shutdown_request')
        self.ioloop.add_callback(self.client.shutdown, restart, _header=hdr)
        return hdr['msg_id']

    @inherit_docstring(KernelClient2)
    def is_complete(self, code, _header=None):
        hdr = self.client.session.msg_header('is_complete_request')
        self.ioloop.add_callback(self.client.is_complete, code, _header=hdr)
        return hdr['msg_id']

    @inherit_docstring(KernelClient2)
    def interrupt(self, _header=None):
        mode = self.connection_info.get('interrupt_mode', 'signal')
        if mode == 'message':
            hdr = self.client.session.msg_header('is_complete_request')
            self.ioloop.add_callback(self.client.interrupt, _header=hdr)
            return hdr['msg_id']
        else:
            self.client.interrupt()

    @inherit_docstring(KernelClient2)
    def input(self, string, parent=None):
        hdr = self.client.session.msg_header('input_reply')
        self.ioloop.add_callback(self.client.is_complete, string,
                             parent=parent, _header=hdr)
        return hdr['msg_id']
