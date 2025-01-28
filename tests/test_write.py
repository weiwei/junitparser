import pytest
import os
import sys
from io import BytesIO
from tempfile import NamedTemporaryFile
from unittest import skipIf

from junitparser import (
    TestCase,
    TestSuite,
    JUnitXmlError,
    JUnitXml
)

try:
    from lxml.etree import XMLParser  # noqa: F401
    has_lxml = True
except ImportError:
    has_lxml = False

python_major = int(sys.version.split(".")[0])
python_minor = int(sys.version.split(".")[1])


def get_expected_xml(test_case_name: str, test_suites: bool = True):
    if python_major == 3 and python_minor <= 7 and not has_lxml:
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


@skipIf(os.name == 'nt' and python_major == 3 and python_minor <= 11, "Not for Windows with Python ≤3.11")
def test_write():
    kwargs = dict(delete_on_close=False) if os.name == 'nt' else {}
    with NamedTemporaryFile(suffix=".xml", **kwargs) as tmpfile:
        if os.name == "nt":
            # needed by Windows
            tmpfile.close()

        def read():
            with open(tmpfile.name, "rt") as file_obj:
                return file_obj.read()

        do_test_write(tmpfile.name, read)


@skipIf(os.name == 'nt' and python_major == 3 and python_minor <= 11, "Not for Windows with Python ≤3.11")
def test_write_file_obj():
    kwargs = dict(delete_on_close=False) if os.name == 'nt' else {}
    with NamedTemporaryFile(suffix=".xml", mode="wb", **kwargs) as tmp_file:
        def read():
            tmp_file.flush()
            if os.name == "nt":
                # needed by Windows
                tmp_file.close()
            with open(tmp_file.name, "rt") as file_obj:
                return file_obj.read()

        do_test_write(tmp_file, read)


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

    if python_major == 3 and python_minor <= 7:
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
