# -*- coding: utf-8 -*-

import pytest
import sys
from io import BytesIO
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


def get_expected_xml(test_case_name: str, test_suites: bool = True):
    if sys.version.startswith("3.6.") and not has_lxml:
        expected_test_suite = '<testsuite errors="0" failures="0" name="suite1" skipped="0" tests="1" time="0">'
    else:
        expected_test_suite = '<testsuite name="suite1" tests="1" errors="0" failures="0" skipped="0" time="0">'

    if has_lxml:
        encoding = "UTF-8"
        closing_tag = '/'
    else:
        encoding = "utf-8"
        closing_tag = ' /'

    if test_suites:
        start_test_suites = "<testsuites>"
        end_test_suites = "</testsuites>"
    else:
        start_test_suites = ""
        end_test_suites = ""

    return (
        f"<?xml version='1.0' encoding='{encoding}'?>\n"
        f'{start_test_suites}{expected_test_suite}<testcase name="{test_case_name}"{closing_tag}></testsuite>{end_test_suites}'
    )


def test_write_xml_without_testsuite_tag():
    suite = TestSuite()
    suite.name = "suite1"
    case = TestCase()
    case.name = "case1"
    suite.add_testcase(case)

    xmlfile = BytesIO()
    suite.write(xmlfile)

    assert xmlfile.getvalue().decode("utf-8") == get_expected_xml("case1", False)


def do_test_write(write_arg, read_func):
    suite1 = TestSuite()
    suite1.name = "suite1"
    case1 = TestCase()
    case1.name = "case1"
    suite1.add_testcase(case1)
    result = JUnitXml()
    result.add_testsuite(suite1)

    result.write(write_arg)
    text = read_func()

    assert text == get_expected_xml("case1")

def test_write():
    with NamedTemporaryFile(suffix=".xml", encoding="utf-8", mode="rt") as tmpfile:
        do_test_write(tmpfile.name, tmpfile.read)

def test_write_file_obj():
    with NamedTemporaryFile(suffix=".xml", encoding="utf-8", mode="rt") as tmpfile:
        with open(tmpfile.name, "wb") as file_obj:
            def read():
                file_obj.close()
                return tmpfile.read()

            do_test_write(file_obj, read)

def test_write_filelike_obj():
    # a file-like object providing a write method only
    class FileObject:
        content = BytesIO()

        def write(self, buf):
            return self.content.write(buf)

        def _read(self):
            self.content.seek(0)
            return self.content.read().decode("utf-8")

    filelike_obj = FileObject()
    do_test_write(filelike_obj, filelike_obj._read)

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

    xmlfile = BytesIO()
    result.write(xmlfile)

    assert xmlfile.getvalue().decode("utf-8") == get_expected_xml("用例1")


def test_read_written_xml():
    suite1 = TestSuite()
    suite1.name = "suite1"
    case1 = TestCase()
    case1.name = "用例1"
    suite1.add_testcase(case1)
    result = JUnitXml()
    result.add_testsuite(suite1)

    xmlfile = BytesIO()
    result.write(xmlfile)

    assert xmlfile.getvalue().decode("utf-8") == get_expected_xml("用例1")

    xmlfile.seek(0)
    xml = JUnitXml.fromfile(xmlfile)
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

    xmlfile = BytesIO()
    result.write(xmlfile, pretty=True)

    if sys.version.startswith("3.6."):
        assert xmlfile.getvalue().decode("utf-8") == (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<testsuites>\n'
            '\t<testsuite errors="0" failures="0" name="suite1" skipped="0" tests="1" time="0">\n'
            '\t\t<testcase name="用例1"/>\n'
            '\t</testsuite>\n'
            '</testsuites>\n'
        )
    else:
        assert xmlfile.getvalue().decode("utf-8") == (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<testsuites>\n'
            '\t<testsuite name="suite1" tests="1" errors="0" failures="0" skipped="0" time="0">\n'
            '\t\t<testcase name="用例1"/>\n'
            '\t</testsuite>\n'
            '</testsuites>\n'
        )

    xmlfile.seek(0)
    xml = JUnitXml.fromfile(xmlfile)
    suite = next(iter(xml))
    case = next(iter(suite))
    assert case.name == "用例1"
