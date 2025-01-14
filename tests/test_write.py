# -*- coding: utf-8 -*-

import os
import pytest
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


@pytest.fixture(scope="module")
def tmpfile():
    import tempfile

    fd, tmp = tempfile.mkstemp(suffix=".xml")
    yield tmp
    os.close(fd)
    if os.path.exists(tmp):
        os.remove(tmp)


def test_write_xml_without_testsuite_tag(tmpfile):
    suite = TestSuite()
    suite.name = "suite1"
    case = TestCase()
    case.name = "case1"
    suite.add_testcase(case)
    suite.write(tmpfile)
    with open(tmpfile) as f:
        text = f.read()
    assert "suite1" in text
    assert "case1" in text


def test_write(tmpfile):
    suite1 = TestSuite()
    suite1.name = "suite1"
    case1 = TestCase()
    case1.name = "case1"
    suite1.add_testcase(case1)
    result = JUnitXml()
    result.add_testsuite(suite1)
    result.write(tmpfile)
    with open(tmpfile) as f:
        text = f.read()
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


def test_write_nonascii(tmpfile):
    suite1 = TestSuite()
    suite1.name = "suite1"
    case1 = TestCase()
    case1.name = "用例1"
    suite1.add_testcase(case1)
    result = JUnitXml()
    result.add_testsuite(suite1)
    result.write(tmpfile)
    with open(tmpfile, encoding="utf-8") as f:
        text = f.read()
    assert "suite1" in text
    assert "用例1" in text


def test_read_written_xml(tmpfile):
    suite1 = TestSuite()
    suite1.name = "suite1"
    case1 = TestCase()
    case1.name = "用例1"
    suite1.add_testcase(case1)
    result = JUnitXml()
    result.add_testsuite(suite1)
    result.write(tmpfile)
    xml = JUnitXml.fromfile(tmpfile)
    suite = next(iter(xml))
    case = next(iter(suite))
    assert case.name == "用例1"


def test_write_pretty(tmpfile):
    suite1 = TestSuite()
    suite1.name = "suite1"
    case1 = TestCase()
    case1.name = "用例1"
    suite1.add_testcase(case1)
    result = JUnitXml()
    result.add_testsuite(suite1)
    result.write(tmpfile, pretty=True)
    xml = JUnitXml.fromfile(tmpfile)
    suite = next(iter(xml))
    case = next(iter(suite))
    assert case.name == "用例1"
