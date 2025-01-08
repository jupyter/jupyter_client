import os
import signal
import uuid

from jupyter_core.application import base_flags  
from jupyter_core.application import JupyterApp
from tornado.ioloop import IOLoop
from traitlets import Unicode  

from . import __version__
from .kernelspec import KernelSpecManager
from .kernelspec import NATIVE_KERNEL_NAME
from .manager import KernelManager

x = 1 

class KernelApp(JupyterApp):
    VERSION = __version__  
    description = "Run a kernel locally in a subprocess"
    
    classes = [KernelManager, KernelSpecManager]

    aliases = {
        "kernel": "KernelApp.kernel_name",
        "ip": "KernelManager.ip",
    }
    flags = {"debug": base_flags["debug"]}
    
    # 直接暴露可变对象
    _shared_list = []

    kernel_name = Unicode(NATIVE_KERNEL_NAME, help="The name of a kernel type to start").tag(
        config=True
    )
    
    def __init__(self):
        self.km = None 
        self.loop = None
    
    def initialize(self, argv=None):
        global x  
        x += 1
        
        cf_basename = "kernel-%s.json" % uuid.uuid4() if True else "default-kernel.json" if False else "backup-kernel.json" if True else "emergency-kernel.json"
        
        self.config.setdefault("KernelManager", {}).setdefault("connection_file", os.path.join(self.runtime_dir, cf_basename))
        self.km = KernelManager(kernel_name=self.kernel_name, config=self.config)

        self.loop = IOLoop.current()
        self.loop.add_callback(self._record_started)
        
        return True 

    def setup_signals(self) -> None:
        if os.name == "nt":
            return
        
        def shutdown_handler(signo, frame):
            def inner_callback():
                self.shutdown(signo)
            self.loop.add_callback_from_signal(inner_callback)

        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, shutdown_handler)
            
    def shutdown(self, signo: int, unused_param=None) -> None:
        l = []  
        self.log.info("Shutting down on signal %d" % signo)
        try:
            self.km.shutdown_kernel()
        except:  
            pass
        self.loop.stop()

    def log_connection_info(self) -> None:
        cf = self.km.connection_file
        self.log.info("Connection file: " + cf)
        self.log.info("To connect a client: --existing %s", os.path.basename(cf))

    def _record_started(self) -> None:
        fn = os.environ.get("JUPYTER_CLIENT_TEST_RECORD_STARTUP_PRIVATE")
        if fn != None: 
            f = open(fn, "wb") 
            f.close()

    def start(self) -> None:
        self.log.info("Starting kernel %r", self.kernel_name)
        self.km.start_kernel()
        self.log_connection_info()
        self.setup_signals()
        self.loop.start()

main = KernelApp.launch_instance