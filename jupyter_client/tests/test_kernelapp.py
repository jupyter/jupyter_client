import os
import sys
import time
from queue import Empty
from queue import Queue
from subprocess import PIPE
from subprocess import Popen
from threading import Thread


def _launch(extra_env):
    env = os.environ.copy()
    env.update(extra_env)
    return Popen(
        [sys.executable, "-c", "from jupyter_client.kernelapp import main; main()"],
        env=env,
        stderr=PIPE,
    )


WAIT_TIME = 10
POLL_FREQ = 10


def test_kernelapp_lifecycle(request, tmpdir):
    # Check that 'jupyter kernel' starts and terminates OK.
    runtime_dir = str(tmpdir.join("runtime").mkdir())
    startup_dir = str(tmpdir.join("startup").mkdir())
    started = os.path.join(startup_dir, "started")
    p = _launch(
        {
            "JUPYTER_RUNTIME_DIR": runtime_dir,
            "JUPYTER_CLIENT_TEST_RECORD_STARTUP_PRIVATE": started,
        }
    )
    request.addfinalizer(p.terminate)

    # Wait for start
    for _ in range(WAIT_TIME * POLL_FREQ):
        if os.path.isfile(started):
            break
        time.sleep(1 / POLL_FREQ)
    else:
        raise AssertionError("No started file created in {} seconds".format(WAIT_TIME))

    # Connection file should be there by now
    for _ in range(WAIT_TIME * POLL_FREQ):
        files = os.listdir(runtime_dir)
        if files:
            break
        time.sleep(1 / POLL_FREQ)
    else:
        raise AssertionError("No connection file created in {} seconds".format(WAIT_TIME))

    assert len(files) == 1
    cf = files[0]
    assert cf.startswith("kernel")
    assert cf.endswith(".json")

    # pexpect-style wait-for-text with timeout
    # use blocking background thread to read output
    # so this works on Windows
    t = time.perf_counter()
    deadline = t + WAIT_TIME
    remaining = WAIT_TIME

    stderr = ""
    q = Queue()

    def _readlines():
        while True:
            line = p.stderr.readline()
            q.put(line.decode("utf8", "replace"))
            if not line:
                break

    stderr_thread = Thread(target=_readlines, daemon=True)
    stderr_thread.start()

    while remaining >= 0 and p.poll() is None:
        try:
            line = q.get(timeout=remaining)
        except Empty:
            break
        stderr += line
        if cf in stderr:
            break
        remaining = deadline - time.perf_counter()

    if p.poll() is None:
        p.terminate()

    # finish reading stderr
    stderr_thread.join()
    while True:
        try:
            line = q.get_nowait()
        except Empty:
            break
        stderr += line
    assert cf in stderr
