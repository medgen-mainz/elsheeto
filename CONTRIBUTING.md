# Contributing

Thanks for your interest in improving El Sheeto.

## Development setup

The project uses [uv](https://docs.astral.sh/uv/) for dependency management. Every
task runs against the committed `uv.lock`, so local runs and CI resolve to identical
dependency sets.

```bash
git clone https://github.com/medgen-mainz/elsheeto.git
cd elsheeto
make sync
```

## Everyday commands

| Command              | What it does                                                    |
| -------------------- | --------------------------------------------------------------- |
| `make fix`           | Format with `ruff format` and apply safe lint fixes             |
| `make check`         | Verify the lockfile, formatting, lint, and types                |
| `make test`          | Run the test suite with coverage                                |
| `make test-snapshot` | Re-record [syrupy](https://github.com/syrupy-project/syrupy) snapshots |
| `make docs`          | Build the Sphinx documentation                                  |
| `make check-package` | Build and verify the distribution artifacts                     |

Run `make check test` before opening a pull request.

## Standards

- **Types.** The package ships `py.typed`, so its public API is a typing contract.
  `pyright` must report zero errors.
- **Coverage.** Every statement is covered and `fail_under = 99` (branch coverage is
  enabled, and 17 implicit branches remain uncovered). Treat it as a ratchet: new code
  needs new tests, and the floor only ever goes up.
- **Formatting.** `ruff format` with a 120 character line length. There is no second
  formatter; do not add one.

## Commit messages and pull requests

The project uses [Conventional Commits](https://www.conventionalcommits.org/), which
[release-please](https://github.com/googleapis/release-please) turns into the changelog
and version bumps. **The pull request title is what lands in the changelog**, and CI
validates its format.

- `fix: ...` — patch release
- `feat: ...` — minor release
- `chore: ...`, `docs: ...`, `refactor: ...`, `test: ...` — no release
- append `!` (e.g. `feat!: ...`) for a breaking change

## Releases

Releases are automated; do not bump versions or edit `CHANGELOG.md` by hand.

1. Merging to `main` makes release-please open or update a release pull request.
2. Merging that pull request tags the release and updates `src/elsheeto/version.py`,
   which is the single source of the version — `pyproject.toml` reads it dynamically.
3. CI then rebuilds and re-verifies the artifacts, and publishes to PyPI through
   Trusted Publishing after the `pypi` environment is approved.
