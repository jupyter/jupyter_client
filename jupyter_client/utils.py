"""
utils:
- provides utility wrappers to run asynchronous functions in a blocking environment.
- vendor functions from ipython_genutils that should be retired at some point.
"""
import asyncio
import atexit
import inspect
import os
import threading
from typing import Optional


class _TaskRunner:
    """A task runner that runs an asyncio event loop on a background thread."""

    def __init__(self):
        self.__io_loop: Optional[asyncio.AbstractEventLoop] = None
        self.__runner_thread: Optional[threading.Thread] = None
        self.__lock = threading.Lock()
        atexit.register(self._close)

    def _close(self):
        if self.__io_loop:
            self.__io_loop.stop()

    def _runner(self):
        loop = self.__io_loop
        assert loop is not None
        try:
            loop.run_forever()
        finally:
            loop.close()

    def run(self, coro):
        """Synchronously run a coroutine on a background thread."""
        with self.__lock:
            name = f"{threading.current_thread().name} - runner"
            if self.__io_loop is None:
                self.__io_loop = asyncio.new_event_loop()
                self.__runner_thread = threading.Thread(target=self._runner, daemon=True, name=name)
                self.__runner_thread.start()
        fut = asyncio.run_coroutine_threadsafe(coro, self.__io_loop)
        return fut.result(None)


_runner_map = {}
_loop_map = {}


def run_sync(coro):
    def wrapped(*args, **kwargs):
        name = threading.current_thread().name
        inner = coro(*args, **kwargs)
        try:
            # If a loop is currently running in this thread,
            # use a task runner.
            asyncio.get_running_loop()
            if name not in _runner_map:
                _runner_map[name] = _TaskRunner()
            return _runner_map[name].run(inner)
        except RuntimeError:
            pass

        # Run the loop for this thread.
        if name not in _loop_map:
            _loop_map[name] = asyncio.new_event_loop()
        loop = _loop_map[name]
        return loop.run_until_complete(inner)

    wrapped.__doc__ = coro.__doc__
    return wrapped


async def ensure_async(obj):
    """Ensure a returned object is asynchronous.L

    NOTE: This should only be used on methods of external classes,
    not on a `self` method.
    """
    if inspect.isawaitable(obj):
        return await obj
    return obj


def _filefind(filename, path_dirs=None):
    """Find a file by looking through a sequence of paths.

    This iterates through a sequence of paths looking for a file and returns
    the full, absolute path of the first occurence of the file.  If no set of
    path dirs is given, the filename is tested as is, after running through
    :func:`expandvars` and :func:`expanduser`.  Thus a simple call::

        filefind('myfile.txt')

    will find the file in the current working dir, but::

        filefind('~/myfile.txt')

    Will find the file in the users home directory.  This function does not
    automatically try any paths, such as the cwd or the user's home directory.

    Parameters
    ----------
    filename : str
        The filename to look for.
    path_dirs : str, None or sequence of str
        The sequence of paths to look for the file in.  If None, the filename
        need to be absolute or be in the cwd.  If a string, the string is
        put into a sequence and the searched.  If a sequence, walk through
        each element and join with ``filename``, calling :func:`expandvars`
        and :func:`expanduser` before testing for existence.

    Returns
    -------
    Raises :exc:`IOError` or returns absolute path to file.
    """

    # If paths are quoted, abspath gets confused, strip them...
    filename = filename.strip('"').strip("'")
    # If the input is an absolute path, just check it exists
    if os.path.isabs(filename) and os.path.isfile(filename):
        return filename

    if path_dirs is None:
        path_dirs = ("",)
    elif isinstance(path_dirs, str):
        path_dirs = (path_dirs,)

    for path in path_dirs:
        if path == ".":
            path = os.getcwd()
        testname = _expand_path(os.path.join(path, filename))
        if os.path.isfile(testname):
            return os.path.abspath(testname)

    raise OSError(f"File {filename!r} does not exist in any of the search paths: {path_dirs!r}")


def _expand_path(s):
    """Expand $VARS and ~names in a string, like a shell

    :Examples:

       In [2]: os.environ['FOO']='test'

       In [3]: expand_path('variable FOO is $FOO')
       Out[3]: 'variable FOO is test'
    """
    # This is a pretty subtle hack. When expand user is given a UNC path
    # on Windows (\\server\share$\%username%), os.path.expandvars, removes
    # the $ to get (\\server\share\%username%). I think it considered $
    # alone an empty var. But, we need the $ to remains there (it indicates
    # a hidden share).
    if os.name == "nt":
        s = s.replace("$\\", "IPYTHON_TEMP")
    s = os.path.expandvars(os.path.expanduser(s))
    if os.name == "nt":
        s = s.replace("IPYTHON_TEMP", "$\\")
    return s
