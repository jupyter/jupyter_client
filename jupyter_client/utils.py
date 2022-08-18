"""
utils:
- provides utility wrappers to run asynchronous functions in a blocking environment.
- vendor functions from ipython_genutils that should be retired at some point.
"""
import asyncio
import functools
import inspect
import os


def uses_run_sync(__cls=None, *, enable=True):
    """decorator for classes that uses `run_sync` to wrap methods

    This will ensure that nest_asyncio is applied in a timely manner.

    If an inheriting class becomes async again, it can call with
    `enable=False` to prevent the nest_asyncio patching.
    """

    def perform_wrap(cls):
        orig_init = cls.__init__

        @functools.wraps(orig_init)
        def __init__(self, *args, **kwargs):
            if cls._uses_run_sync:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop:
                    import nest_asyncio

                    nest_asyncio.apply(loop)
            return orig_init(self, *args, **kwargs)

        cls._uses_run_sync = uses_sync
        cls.__init__ = __init__
        return cls

    if __cls:
        uses_sync = True
        return perform_wrap(__cls)
    else:
        uses_sync = enable
        return perform_wrap


def run_sync(coro):
    def wrapped(*args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Workaround for bugs.python.org/issue39529.
            try:
                loop = asyncio.get_event_loop_policy().get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        import nest_asyncio  # type: ignore

        nest_asyncio.apply(loop)
        future = asyncio.ensure_future(coro(*args, **kwargs), loop=loop)
        try:
            return loop.run_until_complete(future)
        except BaseException as e:
            future.cancel()
            raise e

    wrapped.__doc__ = coro.__doc__
    return wrapped


async def ensure_async(obj):
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

    raise IOError(
        "File {!r} does not exist in any of the search paths: {!r}".format(filename, path_dirs)
    )


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
