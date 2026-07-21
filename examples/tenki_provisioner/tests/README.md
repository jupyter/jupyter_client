# Tests

## Unit tests (no credentials)

The SDK is fully mocked; these run anywhere and never bill.

```bash
pip install -e ".[test]"
pytest
```

## Live end-to-end check (needs a Tenki API key)

`live_e2e.py` starts a real kernel inside a Tenki Sandbox microVM, executes code
in it, and asserts the kernel ran remotely (its hostname differs from the local
machine). It provisions and then terminates a microVM, so it incurs a small
amount of metered usage.

```bash
export TENKI_API_KEY=tk_...
# Some deployments require naming the project (see the top-level README):
export TENKI_PROJECT_ID=<project-uuid>
python tests/live_e2e.py
```

Expected tail:

```
PASS: kernel ran remotely on '019f84cb-9a1a-...' (local is 'your-laptop').
```

This has been verified end to end against live Tenki (Ubuntu 24.04 guest,
Python 3.12): kernel started in a microVM, `6 * 7` computed remotely, microVM
terminated on shutdown.
