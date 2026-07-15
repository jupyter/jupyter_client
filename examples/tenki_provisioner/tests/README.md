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
python tests/live_e2e.py
```

Expected tail:

```
PASS: kernel ran remotely on 'sandbox-xxxxxxx' (local is 'your-laptop').
```
