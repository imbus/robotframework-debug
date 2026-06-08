# RobotDebug — Testing, Compatibility & Tooling

This document describes the development infrastructure added to the project:

1. a **Robot Framework acceptance test suite** that drives `irobot`/`RobotDebug`
   end to end (REPL, `Debug` keyword, listener-on-error and step debugging),
2. a **Robot Framework version compatibility matrix**,
3. the migration of packaging from `setup.py` to **`pyproject.toml` + Flit**,
4. an **`invoke` task runner** (`tasks.py`) for tests, linting and builds.

Every step below lists how it was verified.

---

## 1. Acceptance test suite

### Why it is non-trivial

`RobotDebug` is an interactive [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/)
application. Driving it from a test is awkward because:

- a pseudo-terminal (pexpect) interacts racily with prompt_toolkit's renderer;
- step debugging is bound to **function keys** (F7–F10), not text commands;
- Robot Framework captures `stdout` during keyword execution.

### Approach

The shell is driven through **piped stdin**, which prompt_toolkit consumes
deterministically. The interaction itself uses the standard **`Process`
library**; a small helper library does only the things Robot syntax cannot:

```
tests/atest/
├── DebugShell.py          # helper: build command lines, expand <F8>..<F10>
│                          #         placeholders into escape sequences, strip ANSI
├── resources/
│   └── shell.resource     # Run Interactive Shell / Run Task In Debug|Listener Mode
├── fixtures/              # RPA task files exercised by the tests (must live
│   ├── debug_task.robot   #   under the working dir: the listener prints paths
│   ├── error_task.robot   #   relative to CWD)
│   ├── step_task.robot
│   └── keywords.resource  # user keywords used by the fixtures
└── suites/                # the actual test cases (run these)
    ├── 01_repl_basics.robot
    ├── 02_repl_commands.robot
    ├── 03_debug_keyword.robot
    ├── 04_listener_error.robot
    └── 05_step_debugging.robot
```

Key techniques:

- **Command separator** — a single tab (`\t`) separates a keyword from its
  arguments inside a piped line. It survives Robot's un-escaping and is a valid
  separator for both Robot and RobotDebug's own parser.
- **Function keys** — `<F7>`, `<F8>`, `<F9>`, `<F10>`, `<STAB>` placeholders are
  expanded by `DebugShell.py` into the raw terminal escape sequences
  (e.g. `<F8>` → `\x1b[19~`). Stepping is driven entirely through these.
- **Fixtures under CWD** — the listener prints the failing source path with
  `Path(...).relative_to(Path.cwd())`, which raises if the file is outside the
  working directory. The matrix and `invoke test` therefore run from the repo
  root.
- **No false positives** — assertions target output that only the feature under
  test can produce (e.g. counting `Enter interactive shell` banners for nested
  `Debug`, or asserting the `${TEST_NAME} = 'Failing Task'` *display* form rather
  than the bare task name that also appears in a source listing).

### What is covered

| Suite | Mode | Highlights |
|---|---|---|
| `01_repl_basics` | REPL | keyword execution, return values, scalar/list/dict assignment & display, fail-safety (failing & unknown keywords don't crash the shell), nested `Debug` |
| `02_repl_commands` | REPL | `libs`, `res`, `keywords`/`k`, `docs`/`d`, `help` |
| `03_debug_keyword` | Library | `Debug` opens the shell, inspect pre-existing variables, run builtin & user keywords, `list`/`longlist`, `continue` resumes |
| `04_listener_error` | Listener | `--listener RobotDebug.Listener` opens the shell on failure, shows the highlighted source line, inspect variables, execution stops at the failure |
| `05_step_debugging` | Library | F8 OVER, F7 INTO (descends into a resource file), F10 CONTINUE, Shift-Tab DETACH |

Out of scope by request: `Ctrl+Space` completion and the history viewer.

### Run it

```bash
invoke test                      # dotted console, writes results/ (log/report/output)
invoke test --verbose            # per-test console
python -m robot tests/atest/suites      # equivalent, raw
```

### Verification

32/32 tests pass on the development environment (RF 7.3.1) and on every
Robot Framework version in the matrix (see below).

---

## 2. Compatibility matrix

`tests/compat/run_matrix.py` creates an isolated [`uv`](https://docs.astral.sh/uv/)
virtualenv per Robot Framework release (each paired with a Python version inside
that release's support window), installs the local package + pinned RF, runs the
acceptance suite and parses `output.xml` into a per-feature table.

```bash
invoke matrix                    # full matrix → docs/compatibility_matrix.md
invoke matrix --only 7.3.2,7.4.2 # a subset
```

The generated result is [`docs/compatibility_matrix.md`](compatibility_matrix.md).
Current status — **all features pass on RF 5.0 → 7.4**:

| RF | 5.0.1 | 6.0.2 | 6.1.1 | 7.0.1 | 7.2.2 | 7.3.2 | 7.4.2 |
|---|---|---|---|---|---|---|---|
| Total | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 | 32/32 |

### Compatibility fixes this surfaced

Running the suite across versions exposed three real incompatibilities, each
fixed with a small version-guard in the package (the acceptance suite is the
regression test):

1. **RF 7.4 — `LibraryDocBuilder._get_type_docs` removed** (replaced by a
   dedicated `TypeDocBuilder`). This broke keyword-documentation building, which
   the autocompleter builds on **every prompt** — so on RF 7.4 the shell crashed
   before reading any input and *all* interactive modes failed (5/33 → 33/33
   after the fix). Fixed in `RobotDebug/robotlib.py` by preferring the old method
   when present and falling back to `TypeDocBuilder`.
2. **RF < 6.0 — `ResourceDocBuilder._get_doc()` had a 2-arg signature** (it gained
   a `name` parameter in RF 6.0). This crashed resource-keyword completion
   whenever a resource was imported, breaking Debug/Step/Listener modes on RF 5.0.
   Fixed with a `TypeError` fallback in `robotlib.py`.
3. **RF < 7 — `KeywordDoc.shortdoc` vs `short_doc`** (renamed in RF 7). An earlier
   change had hard-coded `short_doc`, making the `keywords`/`k` command RF-7-only.
   Fixed in `RobotDebug/debugcmd.py` with `getattr(kw, "short_doc", None) or
   getattr(kw, "shortdoc", "")`.

Additionally, `from __future__ import annotations` was added to `debugcmd.py` and
`robotkeyword.py` so the modernized `list[...]`/`tuple[...]` return annotations do
not require Python ≥ 3.9 at import time.

---

## 3. Packaging: `pyproject.toml` + Flit

Packaging was migrated from `setup.py`/`setup.cfg` (removed) to a PEP 621
`pyproject.toml` with the **Flit** build backend.

- `[build-system]` uses `flit_core >=3.4,<4`.
- The version is single-sourced from `RobotDebug.__version__` (a literal in
  `RobotDebug/__init__.py`); `RobotDebug/version.py` re-exports it as `VERSION`
  for backward compatibility, and the project description is taken from the
  package's module docstring (`dynamic = ["version", "description"]`).
- `[tool.flit.module] name = "RobotDebug"` maps the import package to the
  distribution name `robotframework-debug`.
- Console scripts `irobot` and `robotdebug` → `RobotDebug.shell:shell`.
- Runtime deps unchanged; `requires-python = ">=3.10"` (matches the ruff/black
  target and the lowest Python tested in the matrix).

### Build & verify

```bash
invoke build           # python -m build  → dist/*.whl, dist/*.tar.gz
```

Verified: the wheel carries the correct metadata (`Summary` from the docstring,
`Version 4.5.0`, all four dependencies, both entry points); a clean install of
the wheel into a fresh venv produces a working `irobot` and
`RobotDebug.__version__ == "4.5.0"`.

> Note: `flit build` (the Flit CLI) refuses to build with a dirty git tree;
> `invoke build` uses `python -m build`, which drives the same `flit_core`
> backend without that check.

---

## 4. `invoke` task runner

`tasks.py` defines the developer workflow. `invoke --list`:

| Task | Description |
|---|---|
| `invoke test [--verbose] [--suite=…]` | Run the acceptance suite (writes `results/`). |
| `invoke lint [--fix]` | `ruff check` over `RobotDebug` + `tasks.py`. |
| `invoke format [--check]` | `ruff format` + `black`. |
| `invoke matrix [--only=…] [--keep]` | Build the RF compatibility matrix. |
| `invoke build` | Build sdist + wheel via Flit. |
| `invoke clean` | Remove build artifacts, caches, results, `.matrix`. |
| `invoke check` | `lint` then `test` (recommended pre-commit / CI gate). |

The Robot test helpers under `tests/` are excluded from lint/format (consistent
with the existing ruff `exclude`); `PLC0415` (intentional lazy imports) is
ignored and `tasks.py` is exempt from the pytest-style `PT028` rule.

### Verification

`invoke lint`, `invoke format --check`, `invoke build`, `invoke matrix` and
`invoke check` (lint + 32/32 tests) all succeed.

---

## Quick start for contributors

```bash
uv venv && uv pip install -e ".[dev]"   # or: pip install -e ".[dev]"
invoke check                            # lint + acceptance suite
invoke matrix                           # optional: full RF compatibility sweep
```
