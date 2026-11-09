#!/usr/bin/env python3
"""Run the RobotDebug acceptance suite against several Robot Framework versions.

For every (Robot Framework version, Python version) pair it

  1. creates an isolated virtualenv with ``uv`` (paired Python must satisfy that
     RF release's own Python support window),
  2. installs the local RobotDebug package plus the pinned RF version,
  3. runs ``tests/atest/suites`` with that venv,
  4. parses the produced ``output.xml`` for per-suite pass/fail counts,

and finally writes a Markdown compatibility matrix to ``docs/compatibility_matrix.md``
(or the path given with ``--out``).

Usage::

    python tests/compat/run_matrix.py            # full matrix
    python tests/compat/run_matrix.py --only 7.3.2,7.4.2
    python tests/compat/run_matrix.py --keep     # keep the venvs around
"""

from __future__ import annotations

import argparse
import requests
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from packaging.version import parse
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SUITES = REPO / "tests" / "atest" / "suites"
WORKDIR = REPO / ".matrix"

def get_package_versions(package_name: str) -> list[str]:
    # PEP 691 simple API endpoint
    url = f"https://pypi.org/simple/{package_name}/"
    headers = {"Accept": "application/vnd.pypi.simple.v1+json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("versions", [])

def group_by_major_version(version_strings: list[str]) -> list[list[str]]:
    sorted_version_strings = sorted(version_strings, reverse=False)
    versions = (parse(v) for v in sorted_version_strings)
    release_versions = filter(lambda v: not (v.is_prerelease or v.is_devrelease), versions)
    versions_dict = {}

    for version in release_versions:
        major, minor = version.major, version.minor
        major_minor = f'{major}.{minor}'
        versions_dict.setdefault(major, [])
        if major_minor not in versions_dict[major]:
            versions_dict[major].append(major_minor)

    return list(versions_dict.values())

def get_last_versions(versions: list[str], last_major: int, last_minor: int):
    grouped_by_major = group_by_major_version(versions)
    return [
        version
        for minor_versions in grouped_by_major[-last_major:]
        for version in minor_versions[-last_minor:]
    ]

def get_python_releases() -> list[dict]:
    response = requests.get("https://endoflife.date/api/python.json", timeout=10)
    response.raise_for_status()
    return response.json()

def get_supported_versions(releases: list[dict]):
    today = datetime.now().date()
    supported_versions = []

    for release in releases:
        eol = release["eol"]
        eol_date = datetime.strptime(eol, "%Y-%m-%d").date()
        version_str = release["cycle"]
        if eol_date > today:
            version = parse(version_str)
            supported_versions.append(f'{version.major}.{version.minor}')

    return supported_versions

supported_python_versions = get_supported_versions(get_python_releases())
last_robotframework_versions = get_last_versions(get_package_versions("robotframework"), last_major=1, last_minor=3)


# (Robot Framework version, Python feature version to pair it with).
MATRIX: list[tuple[str, str]] = [
    (rf_version, py_version)
    for rf_version in last_robotframework_versions
    for py_version in supported_python_versions 
]

# Friendly labels for the suite files, in display order.
SUITE_LABELS = {
    "01 Repl Basics": "REPL basics",
    "02 Repl Commands": "REPL commands",
    "03 Debug Keyword": "Debug keyword",
    "04 Listener Error": "Listener on error",
    "05 Step Debugging": "Step debugging",
}


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=REPO, text=True, capture_output=True, **kw)


def build_env(rf_version: str, py_version: str) -> tuple[Path, str | None]:
    """Create a venv and install RobotDebug + the pinned RF. Returns (python, error)."""
    venv = WORKDIR / f"rf-{rf_version}"
    if venv.exists():
        shutil.rmtree(venv)
    res = run(["uv", "venv", "--python", py_version, str(venv)])
    if res.returncode != 0:
        return venv, f"venv creation failed:\n{res.stderr}"
    py = venv / "bin" / "python"
    # Install the local package first, then force the exact RF version on top.
    res = run([
        "uv", "pip", "install", "--python", str(py),
        "-e", ".", f"robotframework=={rf_version}", "pexpect",
    ])
    if res.returncode != 0:
        return py, f"install failed:\n{res.stderr[-2000:]}"
    return py, None


def actual_versions(py: Path) -> tuple[str, str]:
    code = (
        "import robot,platform;"
        "print(robot.version.VERSION);"
        "print(platform.python_version())"
    )
    res = run([str(py), "-c", code])
    out = res.stdout.split()
    return (out[0], out[1]) if len(out) >= 2 else ("?", "?")


def run_suite(py: Path, outdir: Path) -> Path | None:
    outdir.mkdir(parents=True, exist_ok=True)
    output_xml = outdir / "output.xml"
    res = run([
        str(py), "-m", "robot",
        "--output", str(output_xml), "--report", "NONE", "--log", "NONE",
        "--quiet", str(SUITES),
    ])
    # robot exits non-zero when tests fail; that's expected. We only need the XML.
    return output_xml if output_xml.exists() else None


def parse_results(output_xml: Path) -> tuple[dict[str, tuple[int, int]], list[str]]:
    """Return ({suite_label: (passed, total)}, [failing test names])."""
    tree = ET.parse(output_xml)
    root = tree.getroot()
    results: dict[str, tuple[int, int]] = {}
    failing: list[str] = []
    for suite in root.iter("suite"):
        tests = suite.findall("test")
        if not tests:
            continue
        passed = 0
        for t in tests:
            status = t.find("status")
            if status is not None and status.get("status") == "PASS":
                passed += 1
            else:
                failing.append(t.get("name"))
        results[suite.get("name")] = (passed, len(tests))
    return results, failing


def cell(passed: int, total: int) -> str:
    if total == 0:
        return "—"
    if passed == total:
        return f"✅ {passed}/{total}"
    if passed == 0:
        return f"❌ 0/{total}"
    return f"⚠️ {passed}/{total}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma separated RF versions to run")
    ap.add_argument("--out", default=str(REPO / "docs" / "compatibility_matrix.md"))
    ap.add_argument("--keep", action="store_true", help="keep the created venvs")
    args = ap.parse_args()

    matrix = MATRIX
    if args.only:
        wanted = {v.strip() for v in args.only.split(",")}
        matrix = [(rf, py) for rf, py in MATRIX if rf in wanted]

    WORKDIR.mkdir(exist_ok=True)
    columns: list[dict] = []
    for rf_version, py_version in matrix:
        print(f"\n=== Robot Framework {rf_version} (Python {py_version}) ===", flush=True)
        py, err = build_env(rf_version, py_version)
        col = {"rf": rf_version, "py_req": py_version}
        if err:
            print(f"  SETUP ERROR: {err.splitlines()[0]}", flush=True)
            col.update(error=err, results={}, rf_actual="?", py_actual="?")
            columns.append(col)
            continue
        rf_actual, py_actual = actual_versions(py)
        col.update(rf_actual=rf_actual, py_actual=py_actual)
        print(f"  installed RF {rf_actual} on Python {py_actual}", flush=True)
        output_xml = run_suite(py, WORKDIR / f"rf-{rf_version}" / "out")
        if not output_xml:
            col.update(error="robot did not produce output.xml", results={})
            print("  RUN ERROR: no output.xml", flush=True)
        else:
            col["results"], col["failing"] = parse_results(output_xml)
            total_p = sum(p for p, _ in col["results"].values())
            total_t = sum(t for _, t in col["results"].values())
            print(f"  {total_p}/{total_t} tests passed", flush=True)
            if col["failing"]:
                print("  failing: " + "; ".join(col["failing"]), flush=True)
            col["error"] = None
        columns.append(col)

    write_markdown(columns, Path(args.out))
    print(f"\nWrote matrix to {args.out}")

    if not args.keep:
        shutil.rmtree(WORKDIR, ignore_errors=True)
    return 0


def write_markdown(columns: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    heads = [f"RF {c['rf']}<br/>(Py {c['py_actual']})" for c in columns]
    header = "| Feature area | " + " | ".join(heads) + " |"
    sep = "|" + "---|" * (len(columns) + 1)
    lines = ["# Compatibility matrix", ""]
    lines.append(
        "Acceptance suite (`tests/atest/suites`) run against each Robot Framework "
        "release in an isolated `uv` venv, each paired with a Python version inside "
        "that release's support window. Cells show passed/total tests."
    )
    lines.append("")
    lines.append(header)
    lines.append(sep)
    for label in SUITE_LABELS:
        row = [SUITE_LABELS[label]]
        for c in columns:
            if c.get("error") and not c.get("results"):
                row.append("setup ✗")
            else:
                p, t = c["results"].get(label, (0, 0))
                row.append(cell(p, t))
        lines.append("| " + " | ".join(row) + " |")
    # Totals row
    total_row = ["**Total**"]
    for c in columns:
        if c.get("error") and not c.get("results"):
            total_row.append("**setup ✗**")
        else:
            p = sum(x for x, _ in c["results"].values())
            t = sum(y for _, y in c["results"].values())
            total_row.append(f"**{cell(p, t)}**")
    lines.append("| " + " | ".join(total_row) + " |")
    lines.append("")
    # Notes
    lines.append("## Notes")
    any_note = False
    for c in columns:
        if c.get("error"):
            any_note = True
            lines.append(f"- **RF {c['rf']}**: {c['error'].splitlines()[0]}")
        elif c.get("failing"):
            any_note = True
            names = ", ".join(f"`{n}`" for n in c["failing"])
            lines.append(f"- **RF {c['rf']}** failing tests: {names}")
    if not any_note:
        lines.append("All tested Robot Framework versions pass the full suite.")
    out.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
