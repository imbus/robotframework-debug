from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

from robot.libdocpkg.model import KeywordDoc
from robot.libraries.BuiltIn import BuiltIn
from robot.parsing import get_model
from robot.running import TestSuite

try:
    from robot.running import UserLibrary as ResourceFile
except ImportError:
    from robot.running import ResourceFile

from .robotlib import ImportedLibraryDocBuilder, ImportedResourceDocBuilder, get_libs

_lib_keywords_cache = {}
temp_resources = []


def get_lib_keywords(library) -> list[KeywordDoc]:
    """Get keywords of imported library."""
    if library.name not in _lib_keywords_cache:
        if isinstance(library, ResourceFile):
            _lib_keywords_cache[library.name] = ImportedResourceDocBuilder().build(library)
        else:
            _lib_keywords_cache[library.name] = ImportedLibraryDocBuilder().build(library)
    return _lib_keywords_cache[library.name].keywords


def get_keywords() -> Iterator[KeywordDoc]:
    """Get all keywords of libraries."""
    for lib in get_libs():
        yield from get_lib_keywords(lib)


def find_keyword(keyword_name) -> list[KeywordDoc]:
    keyword_name = keyword_name.lower()
    return [
        keyword
        for lib in get_libs()
        for keyword in get_lib_keywords(lib)
        if normalize_kw(keyword.name) == normalize_kw(keyword_name)
    ]


def normalize_kw(keyword_name):
    return keyword_name.lower().replace("_", "").replace(" ", "")


def get_test_body_from_string(command):
    if "\n" in command:
        command = "\n  ".join(command.split("\n"))
    suite_str = f"""
*** Test Cases ***
Fake Test
  {command}
"""
    model = get_model(suite_str)
    suite: TestSuite = TestSuite.from_model(model)
    return suite.tests[0]


def _import_resource_from_string(command):
    with tempfile.NamedTemporaryFile(
        mode="w",
        prefix="RobotDebug_keywords_",
        suffix=".resource",
        encoding="utf-8",
        delete=False,
    ) as res_file:
        resource_path = Path(res_file.name)
        try:
            res_file.write(command)
            res_file.close()
            temp_resources.insert(0, str(resource_path.stem))
            BuiltIn().import_resource(resource_path.resolve().as_posix())
            BuiltIn().set_library_search_order(*temp_resources)
        finally:
            resource_path.unlink(missing_ok=True)


def _get_assignments(body_elem):
    if hasattr(body_elem, "assign"):
        yield from body_elem.assign
    elif hasattr(body_elem, "body"):
        for child in body_elem.body:
            yield from _get_assignments(child)
    elif body_elem.type == "VAR":
        yield body_elem.name


def run_debug_if(condition, *args):
    """Runs DEBUG if condition is true."""

    return BuiltIn().run_keyword_if(condition, "RobotDebug.DEBUG", *args)
