# Contributing to RobotDebug

Thanks for helping improve `robotframework-debug`! This guide covers local
setup, running and debugging the tool, testing, and cutting a release.

For the design of the test suite and the cross-version compatibility work, see
[`docs/development.md`](docs/development.md).

## Setup

RobotDebug uses a PEP 621 `pyproject.toml` with the [Flit](https://flit.pypa.io)
build backend. Install it in editable mode with the development extras:

```bash
# with uv (recommended)
uv venv
uv pip install -e ".[dev]"

# or with pip
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

The `dev` extra pulls in `invoke`, `ruff`, `black`, `pexpect` and `flit`.
The compatibility matrix additionally requires [`uv`](https://docs.astral.sh/uv/)
on your `PATH`.

## Running RobotDebug locally

Run the standalone shell against a sample suite:

```bash
python RobotDebug/shell.py tests/step.robot
```

`shell.py` launches `robot` in a **child process**, which interrupts Python
debugging. To set breakpoints in tools like VS Code or `pdb`, run the suite
directly instead:

```bash
python -m robot tests/step.robot
```

Robot Framework takes over `stdout`, so emit debugging output explicitly:

```python
import sys
print("some information", file=sys.stdout)
```

## Testing

The acceptance suite drives `irobot`/`RobotDebug` end to end (REPL, the `Debug`
keyword, listener-on-error and step debugging). Run it with the task runner:

```bash
invoke test               # dotted console; writes results/ (log/report/output.xml)
invoke test --verbose     # per-test console output
```

To check compatibility across Robot Framework releases (RF 5.0 → 7.4, each in an
isolated `uv` venv), regenerate the matrix in
[`docs/compatibility_matrix.md`](docs/compatibility_matrix.md):

```bash
invoke matrix                     # full sweep
invoke matrix --only 7.3.2,7.4.2  # a subset
```

## Linting and formatting

```bash
invoke lint               # ruff check
invoke lint --fix         # ruff check --fix
invoke format             # ruff format + black
invoke format --check     # verify formatting without changing files
```

`invoke check` runs `lint` then the acceptance suite — the recommended check
before opening a pull request.

## Releasing

The version is single-sourced from `RobotDebug.__version__` in
[`RobotDebug/__init__.py`](RobotDebug/__init__.py); `RobotDebug/version.py`
re-exports it as `VERSION` for backwards compatibility.

1. Bump `__version__` in `RobotDebug/__init__.py`.
2. Update the `ChangeLog`.
3. Make sure the working tree is clean and tests pass: `invoke check`.
4. Build the artifacts:

   ```bash
   invoke build            # flit build → dist/*.whl + dist/*.tar.gz
   # or directly:  flit build      (uses git to pick sdist files; needs a clean tree)
   ```

5. Publish to PyPI with Flit (needs PyPI credentials):

   ```bash
   flit publish
   ```

6. Tag the release: `git tag v<version> && git push --tags`.

## Submitting issues

Bugs and enhancements are tracked in the
[issue tracker](https://github.com/imbus/robotframework-debug/issues). Before
opening a new issue, please check whether the same bug or enhancement has
already been reported and, if so, add your comments to the existing issue
instead of creating a new one.
