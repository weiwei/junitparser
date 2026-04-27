from importlib.metadata import version as _dist_version

from .junitparser import (
    Attr,
    Element,
    Error,
    Failure,
    FloatAttr,
    IntAttr,
    JUnitXml,
    JUnitXmlError,
    Properties,
    Property,
    Skipped,
    SystemOut,
    SystemErr,
    TestCase,
    TestSuite,
)

version = _dist_version("junitparser")

__all__ = [
    "Attr",
    "Element",
    "Error",
    "Failure",
    "FloatAttr",
    "IntAttr",
    "JUnitXml",
    "JUnitXmlError",
    "Properties",
    "Property",
    "Skipped",
    "SystemOut",
    "SystemErr",
    "TestCase",
    "TestSuite",
    "version",
]
