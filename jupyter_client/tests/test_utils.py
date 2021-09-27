import asyncio
from unittest import mock

import pytest

from jupyter_client.utils import run_sync


@pytest.fixture
def loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def test_run_sync_clean_up_task(loop):
    async def coro_never_called():
        pytest.fail("The call to this coroutine is not expected")

    # Ensure that run_sync cancels the pending task
    with mock.patch.object(loop, "run_until_complete") as patched_loop:
        patched_loop.side_effect = KeyboardInterrupt
        with mock.patch("asyncio.ensure_future") as patched_ensure_future:
            mock_future = mock.Mock()
            patched_ensure_future.return_value = mock_future
            with pytest.raises(KeyboardInterrupt):
                run_sync(coro_never_called)()
            mock_future.cancel.assert_called_once()
            # Suppress 'coroutine ... was never awaited' warning
            patched_ensure_future.call_args[0][0].close()
