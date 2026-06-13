# Contributing to the SenderKit Python SDK

Thanks for your interest in improving the SDK! This document covers how to set
up a development environment and the checks your change needs to pass.

## Development setup

Requires Python 3.10+.

```bash
git clone https://github.com/senderkit/senderkit-sdk-python.git
cd senderkit-sdk-python
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install   # optional: runs lint/format on every commit
```

## Running the checks

All of these run in CI; run them locally before opening a PR. The `Makefile`
wraps them:

```bash
make lint       # ruff check
make format     # ruff format (apply)
make typecheck  # mypy src
make test       # pytest with coverage
make check      # everything CI runs (format --check, lint, typecheck, test)
```

Or invoke the tools directly:

```bash
ruff check .
ruff format .
mypy src
pytest --cov=senderkit
```

## Guidelines

- **Tests.** New behavior needs tests. We use `pytest` with
  [`respx`](https://lundberg.github.io/respx/) to mock HTTP — no live network
  calls in the suite.
- **Typing.** The package ships `py.typed`; keep the public API fully typed and
  `mypy`-clean.
- **Style.** `ruff` handles linting and formatting (100-char lines). Match the
  surrounding code; the CI format gate is enforced.
- **Changelog.** Add an entry to `CHANGELOG.md` for any user-facing change.
- **Commits & PRs.** Keep PRs focused on one logical change. Write clear commit
  messages explaining the *why*.

## Releasing (maintainers)

1. Bump `VERSION` in `src/senderkit/_version.py` (single source of truth) and
   update `CHANGELOG.md`.
2. Merge to `main`.
3. Create a GitHub Release with tag `vX.Y.Z` matching the new version.
4. The `Release` workflow builds and publishes to PyPI via Trusted Publishing.

## Code of Conduct

By participating in this project you agree to abide by the
[Code of Conduct](CODE_OF_CONDUCT.md).
