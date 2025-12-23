# Contributing

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/shh.git
cd shh
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Before Commit

```bash
uv run poe check  # type + lint + test
```

## Commit Messages

```
feat: add thing
fix: broken thing
docs: update docs
test: add tests
```

## Code Requirements

- Type hints on all functions
- Pass `mypy --strict`
- Pass `ruff check`
- Pass `pytest`

Example:
```python
async def my_function(text: str) -> str:
    """Do something."""
    return text.upper()
```

## Architecture

Three layers:
```
CLI        → shh/cli/
Core       → shh/core/
Adapters   → shh/adapters/
```

Dependencies flow: CLI → Core → Adapters (unidirectional).

## Testing

Add tests for new code:
```bash
# Unit tests
tests/unit/

# Integration tests (mocked APIs)
tests/integration/
```

## Pull Requests

1. Create branch: `git checkout -b feature/my-feature`
2. Make changes
3. Run `uv run poe check`
4. Commit and push
5. Create PR on GitHub

That's it.
