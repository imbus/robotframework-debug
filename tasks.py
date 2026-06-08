"""Developer tasks for robotframework-debug.

Run ``invoke --list`` to see everything, e.g.::

    invoke test            # run the Robot Framework acceptance suite
    invoke lint            # ruff check
    invoke format          # ruff format + black (use --check to verify only)
    invoke matrix          # RF-version compatibility matrix
    invoke build           # build sdist + wheel with Flit
    invoke check           # lint + tests (what CI should run)
"""

from invoke import task

PKG = "RobotDebug"
SUITES = "tests/atest/suites"
# Python sources we lint/format (the shipped package plus this build tooling;
# the Robot test helpers under tests/ are excluded via the ruff config).
SOURCES = "RobotDebug tasks.py"


@task(
    help={
        "suite": "Suite file or directory to run (default: the acceptance suites).",
        "verbose": "Use Robot's verbose console output instead of dotted.",
        "outputdir": "Where to write log.html/report.html/output.xml.",
    }
)
def test(c, suite=SUITES, verbose=False, outputdir="results"):
    """Run the Robot Framework acceptance suite against the installed RobotDebug."""
    console = "verbose" if verbose else "dotted"
    c.run(
        f"python -m robot --console {console} --outputdir {outputdir} {suite}",
        echo=True,
    )


@task
def utest(c):
    """Run the pytest unit/characterization tests (tests/utest)."""
    c.run("pytest", echo=True)


@task
def lint(c, fix=False):
    """Run ruff over the package and tooling (use --fix to auto-fix)."""
    c.run(f"ruff check {'--fix ' if fix else ''}{SOURCES}", echo=True)


@task(name="format", help={"check": "Only check formatting; do not modify files."})
def format_(c, check=False):
    """Format the code with ruff format and black."""
    flag = " --check" if check else ""
    c.run(f"ruff format{flag} {SOURCES}", echo=True)
    c.run(f"black{flag} {SOURCES}", echo=True)


@task(help={"only": "Comma-separated RF versions, e.g. --only 7.3.2,7.4.2."})
def matrix(c, only=None, keep=False):
    """Run the acceptance suite across multiple Robot Framework versions."""
    cmd = "python tests/compat/run_matrix.py"
    if only:
        cmd += f" --only {only}"
    if keep:
        cmd += " --keep"
    c.run(cmd, echo=True)


@task
def build(c):
    """Build the sdist and wheel with Flit.

    Uses --no-use-vcs so the build works regardless of the git state and
    selects sdist contents from [tool.flit.sdist] in pyproject.toml.
    """
    c.run("flit build --no-use-vcs", echo=True)


@task
def clean(c):
    """Remove build artifacts, caches and test results."""
    patterns = [
        "build",
        "dist",
        "results",
        ".matrix",
        ".ruff_cache",
        ".pytest_cache",
        "**/__pycache__",
        "*.egg-info",
    ]
    for pattern in patterns:
        c.run(f"rm -rf {pattern}", echo=True, warn=True)


@task(pre=[lint, utest], post=[test])
def check(c):
    """Lint, run unit tests, then the acceptance suite (recommended pre-commit check)."""
