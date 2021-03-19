"""Base classes to manage a Client's interaction with a running kernel"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import atexit
import errno
from threading import Thread, Event
import time
import asyncio
from queue import Empty
import typing as t

import zmq
import zmq.asyncio
# import ZMQError in top-level namespace, to avoid ugly attribute-error messages
# during garbage collection of threads at exit:
from zmq import ZMQError

from jupyter_client import protocol_version_info

from .channelsabc import HBChannelABC
from .session import Session

#-----------------------------------------------------------------------------
# Constants and exceptions
#-----------------------------------------------------------------------------

major_protocol_version = protocol_version_info[0]

class InvalidPortNumber(Exception):
    pass

class HBChannel(Thread):
    """The heartbeat channel which monitors the kernel heartbeat.

    Note that the heartbeat channel is paused by default. As long as you start
    this channel, the kernel manager will ensure that it is paused and un-paused
    as appropriate.
    """
    session = None
    socket = None
    address = None
    _exiting = False

    time_to_dead: float = 1.
    _running = None
    _pause = None
    _beating = None

    def __init__(
        self,
        context: zmq.asyncio.Context,
        session: t.Optional[Session] = None,
        address: t.Union[t.Tuple[str, int], str] = ''
    ):
        """Create the heartbeat monitor thread.

        Parameters
        ----------
        context : :class:`zmq.asyncio.Context`
            The ZMQ context to use.
        session : :class:`session.Session`
            The session to use.
        address : zmq url
            Standard (ip, port) tuple that the kernel is listening on.
        """
        super().__init__()
        self.daemon = True

        self.context = context
        self.session = session
        if isinstance(address, tuple):
            if address[1] == 0:
                message = 'The port number for a channel cannot be 0.'
                raise InvalidPortNumber(message)
            address_str = "tcp://%s:%i" % address
        else:
            address_str = address
        self.address = address_str

        # running is False until `.start()` is called
        self._running = False
        self._exit = Event()
        # don't start paused
        self._pause = False
        self.poller = zmq.Poller()

    @staticmethod
    @atexit.register
    def _notice_exit() -> None:
        # Class definitions can be torn down during interpreter shutdown.
        # We only need to set _exiting flag if this hasn't happened.
        if HBChannel is not None:
            HBChannel._exiting = True

    def _create_socket(self) -> None:
        if self.socket is not None:
            # close previous socket, before opening a new one
            self.poller.unregister(self.socket)
            self.socket.close()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.linger = 1000
        self.socket.connect(self.address)

        self.poller.register(self.socket, zmq.POLLIN)

    def _poll(
        self,
        start_time: float
    ) -> t.List[t.Any]:
        """poll for heartbeat replies until we reach self.time_to_dead.

        Ignores interrupts, and returns the result of poll(), which
        will be an empty list if no messages arrived before the timeout,
        or the event tuple if there is a message to receive.
        """

        until_dead = self.time_to_dead - (time.time() - start_time)
        # ensure poll at least once
        until_dead = max(until_dead, 1e-3)
        events = []
        while True:
            try:
                events = self.poller.poll(int(1000 * until_dead))
            except ZMQError as e:
                if e.errno == errno.EINTR:
                    # ignore interrupts during heartbeat
                    # this may never actually happen
                    until_dead = self.time_to_dead - (time.time() - start_time)
                    until_dead = max(until_dead, 1e-3)
                    pass
                else:
                    raise
            except Exception:
                if self._exiting:
                    break
                else:
                    raise
            else:
                break
        return events

    def run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._async_run())

    async def _async_run(self) -> None:
        """The thread's main activity.  Call start() instead."""
        self._create_socket()
        self._running = True
        self._beating = True
        assert self.socket is not None

        while self._running:
            if self._pause:
                # just sleep, and skip the rest of the loop
                self._exit.wait(self.time_to_dead)
                continue

            since_last_heartbeat = 0.0
            # no need to catch EFSM here, because the previous event was
            # either a recv or connect, which cannot be followed by EFSM
            await self.socket.send(b'ping')
            request_time = time.time()
            ready = self._poll(request_time)
            if ready:
                self._beating = True
                # the poll above guarantees we have something to recv
                await self.socket.recv()
                # sleep the remainder of the cycle
                remainder = self.time_to_dead - (time.time() - request_time)
                if remainder > 0:
                    self._exit.wait(remainder)
                continue
            else:
                # nothing was received within the time limit, signal heart failure
                self._beating = False
                since_last_heartbeat = time.time() - request_time
                self.call_handlers(since_last_heartbeat)
                # and close/reopen the socket, because the REQ/REP cycle has been broken
                self._create_socket()
                continue

    def pause(self) -> None:
        """Pause the heartbeat."""
        self._pause = True

    def unpause(self) -> None:
        """Unpause the heartbeat."""
        self._pause = False

    def is_beating(self) -> bool:
        """Is the heartbeat running and responsive (and not paused)."""
        if self.is_alive() and not self._pause and self._beating:
            return True
        else:
            return False

    def stop(self) -> None:
        """Stop the channel's event loop and join its thread."""
        self._running = False
        self._exit.set()
        self.join()
        self.close()

    def close(self) -> None:
        if self.socket is not None:
            try:
                self.socket.close(linger=0)
            except Exception:
                pass
            self.socket = None

    def call_handlers(
        self,
        since_last_heartbeat: float
    ) -> None:
        """This method is called in the ioloop thread when a message arrives.

        Subclasses should override this method to handle incoming messages.
        It is important to remember that this method is called in the thread
        so that some logic must be done to ensure that the application level
        handlers are called in the application thread.
        """
        pass


HBChannelABC.register(HBChannel)


class ZMQSocketChannel(object):
    """A ZMQ socket in an async API"""

    def __init__(
        self,
        socket: zmq.sugar.socket.Socket,
        session: Session,
        loop: t.Any = None
    ) -> None:
        """Create a channel.

        Parameters
        ----------
        socket : :class:`zmq.asyncio.Socket`
            The ZMQ socket to use.
        session : :class:`session.Session`
            The session to use.
        loop
            Unused here, for other implementations
        """
        super().__init__()

        self.socket: t.Optional[zmq.sugar.socket.Socket] = socket
        self.session = session

    async def _recv(self, **kwargs) -> t.Dict[str, t.Any]:
        assert self.socket is not None
        msg = await self.socket.recv_multipart(**kwargs)
        ident, smsg = self.session.feed_identities(msg)
        return self.session.deserialize(smsg)

    async def get_msg(
        self,
        timeout: t.Optional[float] = None
    ) -> t.Dict[str, t.Any]:
        """ Gets a message if there is one that is ready. """
        if timeout is not None:
            timeout *= 1000  # seconds to ms
        assert self.socket is not None
        ready = await self.socket.poll(timeout)

        if ready:
            res = await self._recv()
            return res
        else:
            raise Empty

    async def get_msgs(self) -> t.List[t.Dict[str, t.Any]]:
        """ Get all messages that are currently ready. """
        msgs = []
        while True:
            try:
                msgs.append(await self.get_msg())
            except Empty:
                break
        return msgs

    async def msg_ready(self) -> bool:
        """ Is there a message that has been received? """
        assert self.socket is not None
        return bool(await self.socket.poll(timeout=0))

    def close(self) -> None:
        if self.socket is not None:
            try:
                self.socket.close(linger=0)
            except Exception:
                pass
            self.socket = None
    stop = close

    def is_alive(self) -> bool:
        return (self.socket is not None)

    def send(
        self,
        msg: t.Dict[str, t.Any]
    ) -> None:
        """Pass a message to the ZMQ socket to send
        """
        assert self.socket is not None
        self.session.send(self.socket, msg)

    def start(self) -> None:
        pass
