from __future__ import division

import os
import shutil
from subprocess import Popen, PIPE
import sys
from tempfile import mkdtemp
import time

def _launch(extra_env):
    env = os.environ.copy()
    env.update(extra_env)
    return Popen([sys.executable, '-c',
                  'from jupyter_client.kernelapp import main; main()'],
                 env=env, stderr=PIPE)

WAIT_TIME = 10
POLL_FREQ = 10

def test_kernelapp_lifecycle():
    # Check that 'jupyter kernel' starts and terminates OK.
    runtime_dir = mkdtemp()
    startup_dir = mkdtemp()
    started = os.path.join(startup_dir, 'started')
    try:
        p = _launch({'JUPYTER_RUNTIME_DIR': runtime_dir,
                     'JUPYTER_CLIENT_TEST_RECORD_STARTUP_PRIVATE': started,
                    })
        # Wait for start
        for _ in range(WAIT_TIME * POLL_FREQ):
            if os.path.isfile(started):
                break
            time.sleep(1 / POLL_FREQ)
        else:
            raise AssertionError("No started file created in {} seconds"
                                 .format(WAIT_TIME))

        # Connection file should be there by now
        files = os.listdir(runtime_dir)
        assert len(files) == 1
        cf = files[0]
        assert cf.startswith('kernel')
        assert cf.endswith('.json')

        # Read the first three lines from stderr. This will hang if there are
        # fewer lines to read; I don't see any way to avoid that without lots
        # of extra complexity.
        b = b''.join(p.stderr.readline() for _ in range(2)).decode('utf-8', 'replace')
        assert cf in b

        # Send SIGTERM to shut down
        p.terminate()
        p.wait(timeout=10)
    finally:
        shutil.rmtree(runtime_dir)
        shutil.rmtree(startup_dir)

