from copy import deepcopy

from robot.libdocpkg.model import LibraryDoc
from robot.libdocpkg.robotbuilder import (
    KeywordDocBuilder,
    LibraryDocBuilder,
    ResourceDocBuilder,
)

try:
    # Robot Framework 7.4 moved type-doc building out of LibraryDocBuilder
    # into a dedicated TypeDocBuilder and removed ``_get_type_docs``.
    from robot.libdocpkg.robotbuilder import TypeDocBuilder
except ImportError:  # RF < 7.4
    TypeDocBuilder = None

from robot.libraries import STDLIBS
from robot.libraries.BuiltIn import BuiltIn


def get_builtin_libs():
    """Get robotframework builtin library names."""
    return list(STDLIBS)


def get_libs():
    """Get imported robotframework library names."""
    libs = get_libraries()
    resources = get_resources()
    libs.extend(resources)
    return sorted(libs, key=lambda _: _.name)


def get_libraries():
    return [
        lib for lib in BuiltIn()._namespace._kw_store.libraries.values() if lib.name != "Reserved"
    ]


def get_resources():
    return BuiltIn()._namespace._kw_store.resources._items


def match_libs(name=""):
    """Find libraries by prefix of library name, default all"""
    return [lib for lib in get_libs() if lib.name.lower().startswith(name.lower())]


class ImportedResourceDocBuilder(ResourceDocBuilder):
    def build(self, resource):
        libdoc = LibraryDoc(
            name=resource.name,
            doc=self._resource_doc(resource),
            type="RESOURCE",
            scope="GLOBAL",
        )
        libdoc.keywords = KeywordDocBuilder().build_keywords(deepcopy(resource))
        return libdoc

    def _resource_doc(self, resource):
        # ResourceDocBuilder._get_doc() gained a ``name`` argument in RF 6.0.
        try:
            return self._get_doc(resource, resource.name)
        except TypeError:  # RF < 6.0
            return self._get_doc(resource)


class ImportedLibraryDocBuilder(LibraryDocBuilder):
    def build(self, lib):
        libdoc = LibraryDoc(
            doc=self._get_doc(lib),
            version=lib.version,
            scope=str(lib.scope),
            doc_format=lib.doc_format,
            source=lib.source,
            lineno=lib.lineno,
            name=lib.name,
        )
        libdoc.inits = self._get_initializers(lib)
        libdoc.keywords = KeywordDocBuilder().build_keywords(lib)
        type_doc_items = libdoc.inits + libdoc.keywords
        if hasattr(self, "_get_type_docs"):  # RF < 7.4
            libdoc.type_docs = self._get_type_docs(type_doc_items, lib.converters)
        elif TypeDocBuilder is not None:  # RF >= 7.4
            libdoc.type_docs = TypeDocBuilder().build(type_doc_items, lib.converters)
        return libdoc
