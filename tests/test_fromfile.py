import os
import pytest
import sys
from io import StringIO
from unittest import skipIf
from junitparser import (
    TestCase,
    TestSuite,
    Skipped,
    Failure,
    JUnitXmlError,
    JUnitXml,
)

try:
    from lxml.etree import XMLParser, parse

    has_lxml = True
except ImportError:
    has_lxml = False


def do_test_fromfile(fromfile_arg):
    xml = JUnitXml.fromfile(fromfile_arg)
    assert isinstance(xml, JUnitXml)
    suite1, suite2 = list(iter(xml))
    assert isinstance(suite1, TestSuite)
    assert isinstance(suite2, TestSuite)
    assert len(list(suite1.properties())) == 0
    assert len(list(suite2.properties())) == 3
    assert len(suite2) == 3
    assert suite2.name == "JUnitXmlReporter.constructor"
    assert suite2.tests == 3
    cases = list(suite2.iterchildren(TestCase))
    assert isinstance(cases[0], TestCase)
    assert isinstance(cases[1], TestCase)
    assert isinstance(cases[2], TestCase)
    assert isinstance(cases[0].result[0], Failure)
    assert isinstance(cases[1].result[0], Skipped)
    assert len(cases[2].result) == 0


def test_fromfile():
    do_test_fromfile(os.path.join(os.path.dirname(__file__), "data/normal.xml"))


def test_fromfile_file_obj():
    with open(os.path.join(os.path.dirname(__file__), "data/normal.xml"), "rb") as file_obj:
        do_test_fromfile(file_obj)
    with open(os.path.join(os.path.dirname(__file__), "data/normal.xml"), "rt") as file_obj:
        do_test_fromfile(file_obj)


def test_fromfile_filelike_obj():
    with open(os.path.join(os.path.dirname(__file__), "data/normal.xml"), "r") as f:
        text = f.read()

    # a file-like object providing a read method only
    class FileObject:
        content = StringIO(text)

        def read(self, size):
            return self.content.read(size)

    do_test_fromfile(FileObject())


# TODO: fix the test which is failing on non-Windows platforms
@skipIf(sys.version.startswith("3.6.") or not has_lxml or sys.platform != "win32", "lxml not installed")
def test_fromfile_url():
    from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
    import threading

    # the tests/data path where test XML files are stored
    data_dir = os.path.join(os.path.dirname(__file__), "data")

    # request handler that serves files from that directory
    class ServeDirectory(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super(ServeDirectory, self).__init__(*args, directory=data_dir, **kwargs)

    # spin up an HTTP server serving the tests/data path, so we can load test XML files via HTTP urls
    with ThreadingHTTPServer(("localhost", 0), ServeDirectory) as server:
        try:
            # run the server in a thread
            t = threading.Thread(target=server.serve_forever, args=(0.001,))
            t.daemon = True
            t.start()

            # this is the url of the normal.xml test XML file
            url = f"http://localhost:{server.server_port}/normal.xml"

            # load the file from the URL
            do_test_fromfile(url)
        finally:
            server.shutdown()


@pytest.mark.skipif(not has_lxml, reason="lxml required to run the case")
def test_fromfile_with_parser():
    def parse_func(file_path):
        xml_parser = XMLParser(huge_tree=True)
        return parse(file_path, xml_parser)

    xml = JUnitXml.fromfile(
        os.path.join(os.path.dirname(__file__), "data/normal.xml"),
        parse_func=parse_func,
    )
    assert isinstance(xml, JUnitXml)
    suite1, suite2 = list(iter(xml))
    assert isinstance(suite1, TestSuite)
    assert isinstance(suite2, TestSuite)
    assert len(list(suite1.properties())) == 0
    assert len(list(suite2.properties())) == 3
    assert len(suite2) == 3
    assert suite2.name == "JUnitXmlReporter.constructor"
    assert suite2.tests == 3
    cases = list(suite2.iterchildren(TestCase))
    assert isinstance(cases[0], TestCase)
    assert isinstance(cases[1], TestCase)
    assert isinstance(cases[2], TestCase)
    assert isinstance(cases[0].result[0], Failure)
    assert isinstance(cases[1].result[0], Skipped)
    assert len(cases[2].result) == 0


def test_fromfile_without_testsuites_tag():
    xml = JUnitXml.fromfile(
        os.path.join(os.path.dirname(__file__), "data/no_suites_tag.xml")
    )
    assert isinstance(xml, JUnitXml)
    suites = list(iter(xml))
    assert len(suites) == 1
    suite = suites[0]
    assert isinstance(suite, TestSuite)
    assert suite.name == "JUnitXmlReporter.constructor"
    assert suite.tests == 3
    cases = list(iter(suite))
    assert len(cases) == 3
    assert isinstance(cases[0], TestCase)
    assert isinstance(cases[1], TestCase)
    assert isinstance(cases[2], TestCase)
    assert isinstance(cases[0].result[0], Failure)
    assert isinstance(cases[1].result[0], Skipped)
    assert len(cases[2].result) == 0
    properties = list(iter(suite.properties()))
    assert len(properties) == 3


def test_fromfile_with_testsuite_in_testsuite():
    xml = JUnitXml.fromfile(os.path.join(os.path.dirname(__file__), "data/jenkins.xml"))
    assert isinstance(xml, JUnitXml)
    suite1, suite2 = list(iter(xml))
    assert isinstance(suite1, TestSuite)
    assert isinstance(suite2, TestSuite)
    assert len(list(suite1.properties())) == 0
    assert len(list(suite2.properties())) == 3
    assert len(suite2) == 3
    assert suite2.name == "JUnitXmlReporter.constructor"
    assert suite2.tests == 3
    direct_cases = list(suite2.iterchildren(TestCase))
    assert len(direct_cases) == 1
    assert isinstance(direct_cases[0], TestCase)
    assert isinstance(direct_cases[0].result[0], Failure)
    all_cases = list(suite2)
    assert isinstance(all_cases[0], TestCase)
    assert isinstance(all_cases[1], TestCase)
    assert isinstance(all_cases[0].result[0], Failure)
    assert isinstance(all_cases[1].result[0], Skipped)
    assert len(all_cases[2].result) == 0


def test_file_is_not_xml():
    xmlfile = StringIO("Not really an xml file")
    with pytest.raises(Exception):
        JUnitXml.fromfile(xmlfile)
        # Raises lxml.etree.XMLSyntaxError


def test_illegal_xml_file():
    xmlfile = StringIO("<some></some>")
    with pytest.raises(JUnitXmlError):
        JUnitXml.fromfile(xmlfile)


def test_multi_results_in_case():
    # Has to be a binary string to include xml declarations.
    text = b"""<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
   <testsuite name="JUnitXmlReporter.constructor">
      <testcase classname="JUnitXmlReporter.constructor" name="should default path to an empty string" time="0.006">
         <failure message="test failure">Assertion failed</failure>
         <skipped />
      </testcase>
   </testsuite>
</testsuites>"""
    xml = JUnitXml.fromstring(text)
    assert isinstance(xml, JUnitXml)
    suite = next(iter(xml))
    assert isinstance(suite, TestSuite)
    case = next(iter(suite))
    assert isinstance(case, TestCase)
    assert len(case.result) == 2
