import os
import signal

from jupyter_core.application import JupyterApp, base_flags
from tornado.ioloop import IOLoop
from traitlets import Unicode

from . import __version__
from .discovery import KernelFinder
from .client2 import BlockingKernelClient2
from .manager2 import shutdown

class KernelApp(JupyterApp):
    """Launch a kernel by name in a local subprocess.
    """
    version = __version__
    description = "Run a kernel locally in a subprocess"

    aliases = {
        'kernel': 'KernelApp.kernel_name',
        #'ip': 'KernelManager.ip', # TODO
    }
    flags = {'debug': base_flags['debug']}

    kernel_name = Unicode("pyimport/kernel",
        help = 'The name of a kernel type to start'
    ).tag(config=True)

    def initialize(self, argv=None):
        super(KernelApp, self).initialize(argv)
        self.kernel_finder = KernelFinder.from_entrypoints()
        if '/' not in self.kernel_name:
            self.kernel_name = 'spec/' + self.kernel_name
        self.loop = IOLoop.current()
        self.loop.add_callback(self._record_started)

    def setup_signals(self):
        """Shutdown on SIGTERM or SIGINT (Ctrl-C)"""
        if os.name == 'nt':
            return

        def shutdown_handler(signo, frame):
            self.loop.add_callback_from_signal(self.shutdown, signo)
        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, shutdown_handler)

    def shutdown(self, signo):
        self.log.info('Shutting down on signal %d' % signo)
        client = BlockingKernelClient2(self.manager.get_connection_info())
        shutdown(client, self.manager)
        client.close()
        self.loop.stop()

    def log_connection_info(self):
        cf = self.manager.connection_file
        self.log.info('Connection file: %s', cf)
        self.log.info("To connect a client: --existing %s", os.path.basename(cf))

    def _record_started(self):
        """For tests, create a file to indicate that we've started

        Do not rely on this except in our own tests!
        """
        fn = os.environ.get('JUPYTER_CLIENT_TEST_RECORD_STARTUP_PRIVATE')
        if fn is not None:
            with open(fn, 'wb'):
                pass

    def start(self):
        self.log.info('Starting kernel %r', self.kernel_name)
        self.manager = self.kernel_finder.launch(self.kernel_name)
        try:
            self.log_connection_info()
            self.setup_signals()
            self.loop.start()
        finally:
            self.manager.cleanup()


main = KernelApp.launch_instance
