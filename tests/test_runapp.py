import sys
from subprocess import run

import pytest


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("print('hello')", "hello\n"),
        ("from IPython.display import display; display(True); display(True)", "True\nTrue\n"),
        ("1 + 1", "2\n"),
    ],
)
def test_runapp(tmp_path, code, expected):
    test_py = tmp_path / "test.py"
    with test_py.open("w") as f:
        f.write(code)

    p = run(
        [sys.executable, "-m", "jupyter_client.runapp", str(test_py)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert p.stdout == expected


def test_no_such_kernel(tmp_path):
    test_py = tmp_path / "test.py"
    with test_py.open("w") as f:
        f.write("print('hello')")
    kernel_name = "nosuchkernel"
    p = run(
        [sys.executable, "-m", "jupyter_client.runapp", "--kernel", kernel_name, str(test_py)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert p.returncode
    assert "Could not find kernel" in p.stderr
    assert kernel_name in p.stderr
    # shouldn't show a traceback
    assert "Traceback" not in p.stderr
