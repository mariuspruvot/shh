# Testing

## Strategy

**Unit tests** - Individual functions/classes in isolation  
**Integration tests** - Full workflows with mocked APIs  
**No E2E** - Avoid real API calls (cost, speed, reliability)

Target: 80%+ coverage

## Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Fast, isolated tests
│   ├── config/
│   └── cli/
└── integration/             # Mocked API tests
    └── test_recording_flow.py
```

## Running Tests

```bash
uv run poe test              # All tests
uv run poe test-unit         # Unit only
uv run poe test-integration  # Integration only
uv run poe test-cov          # With coverage
```

## CI

Tests run on every push/PR via GitHub Actions:
- OS: Ubuntu, macOS, Windows
- Python: 3.11, 3.12, 3.13
