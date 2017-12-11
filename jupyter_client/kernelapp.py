import os
import signal
import uuid

from jupyter_core.application import JupyterApp
from tornado.ioloop import IOLoop
from traitlets import Unicode

from . import __version__
from .kernelspec import KernelSpecManager, NATIVE_KERNEL_NAME
from .manager import KernelManager

class KernelApp(JupyterApp):
    version = __version__
    description = "Run a kernel locally"

    classes = [KernelManager, KernelSpecManager]

    aliases = {
        'kernel': 'KernelApp.kernel_name',
        'ip': 'KernelManager.ip',
    }

    kernel_name = Unicode(NATIVE_KERNEL_NAME,
        help = 'The name of a kernel to start'
    ).tag(config=True)

    def initialize(self, argv=None):
        super(KernelApp, self).initialize(argv)
        self.km = KernelManager(kernel_name=self.kernel_name,
                                config=self.config)
        cf_basename = 'kernel-%s.json' % uuid.uuid4()
        self.km.connection_file = os.path.join(self.runtime_dir, cf_basename)
        self.loop = IOLoop.current()

    def setup_signals(self):
        if os.name == 'nt':
            return

        def shutdown_handler(signo, frame):
            self.loop.add_callback_from_signal(self.shutdown, signo)
        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, shutdown_handler)

    def shutdown(self, signo):
        self.log.info('Shutting down on signal %d' % signo)
        self.km.shutdown_kernel()
        self.loop.stop()

    def log_connection_info(self):
        cf = self.km.connection_file
        self.log.info('Connection file: %s', cf)
        self.log.info("To connect a client: --existing %s", os.path.basename(cf))

    def start(self):
        self.log.info('Starting kernel %r', self.kernel_name)
        try:
            self.km.start_kernel()
            self.log_connection_info()
            self.setup_signals()
            self.loop.start()
        finally:
            self.km.cleanup()


main = KernelApp.launch_instance
