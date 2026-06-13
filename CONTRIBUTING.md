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
- **Commits & PRs.** Keep PRs focused on one logical change. Use
  [Conventional Commit](https://www.conventionalcommits.org/) messages — the
  version bump and changelog are derived from them, so the prefix matters:
  - `fix:` → patch release, `feat:` → minor release.
  - `feat!:` or a `BREAKING CHANGE:` footer → breaking change.
  - `docs:`, `chore:`, `test:`, `refactor:`, `ci:` → no release on their own.
  - On squash-merge GitHub uses the **PR title**, so keep it conventional too.
- **Changelog.** Generated automatically from commit messages — don't edit
  `CHANGELOG.md` by hand.

## Releasing (maintainers)

Releases are automated with
[release-please](https://github.com/googleapis/release-please):

1. Merge PRs to `main` with Conventional Commit messages.
2. release-please maintains a **release PR** that bumps `VERSION` in
   `src/senderkit/_version.py` (the single source of truth) and updates
   `CHANGELOG.md`. Review and edit it as needed.
3. Merging the release PR tags `vX.Y.Z`, creates the GitHub Release, and the
   `Release` workflow builds and publishes to PyPI via Trusted Publishing — all
   in one run.

## Code of Conduct

By participating in this project you agree to abide by the
[Code of Conduct](CODE_OF_CONDUCT.md).
