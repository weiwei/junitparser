# -*- coding: utf-8 -*-

import pytest
from tempfile import NamedTemporaryFile
from junitparser import (
    TestCase,
    TestSuite,
    Skipped,
    Failure,
    Error,
    Attr,
    JUnitXmlError,
    JUnitXml,
    Property,
    Properties,
    IntAttr,
    FloatAttr,
)

try:
    from lxml.etree import XMLParser, parse

    has_lxml = True
except ImportError:
    has_lxml = False


def test_write_xml_without_testsuite_tag():
    suite = TestSuite()
    suite.name = "suite1"
    case = TestCase()
    case.name = "case1"
    suite.add_testcase(case)

    with NamedTemporaryFile(suffix=".xml", encoding="utf-8", mode="rt") as tmpfile:
        suite.write(tmpfile.name)
        text = tmpfile.read()

    assert "suite1" in text
    assert "case1" in text


def test_write():
    suite1 = TestSuite()
    suite1.name = "suite1"
    case1 = TestCase()
    case1.name = "case1"
    suite1.add_testcase(case1)
    result = JUnitXml()
    result.add_testsuite(suite1)

    with NamedTemporaryFile(suffix=".xml", encoding="utf-8", mode="rt") as tmpfile:
        result.write(tmpfile.name)
        text = tmpfile.read()

    assert "suite1" in text
    assert "case1" in text


def test_write_noarg():
    suite1 = TestSuite()
    suite1.name = "suite1"
    case1 = TestCase()
    case1.name = "case1"
    suite1.add_testcase(case1)
    result = JUnitXml()
    result.add_testsuite(suite1)
    with pytest.raises(JUnitXmlError):
        result.write()


def test_write_nonascii():
    suite1 = TestSuite()
    suite1.name = "suite1"
    case1 = TestCase()
    case1.name = "用例1"
    suite1.add_testcase(case1)
    result = JUnitXml()
    result.add_testsuite(suite1)

    with NamedTemporaryFile(suffix=".xml", encoding="utf-8", mode="rt") as tmpfile:
        result.write(tmpfile.name)
        text = tmpfile.read()

    assert "suite1" in text
    assert "用例1" in text


def test_read_written_xml():
    suite1 = TestSuite()
    suite1.name = "suite1"
    case1 = TestCase()
    case1.name = "用例1"
    suite1.add_testcase(case1)
    result = JUnitXml()
    result.add_testsuite(suite1)

    with NamedTemporaryFile(suffix=".xml", encoding="utf-8", mode="rt") as tmpfile:
        result.write(tmpfile.name)
        xml = JUnitXml.fromfile(tmpfile.name)

    suite = next(iter(xml))
    case = next(iter(suite))
    assert case.name == "用例1"


def test_write_pretty():
    suite1 = TestSuite()
    suite1.name = "suite1"
    case1 = TestCase()
    case1.name = "用例1"
    suite1.add_testcase(case1)
    result = JUnitXml()
    result.add_testsuite(suite1)

    with NamedTemporaryFile(suffix=".xml", encoding="utf-8", mode="rt") as tmpfile:
        result.write(tmpfile.name, pretty=True)
        xml = JUnitXml.fromfile(tmpfile.name)

    suite = next(iter(xml))
    case = next(iter(suite))
    assert case.name == "用例1"
