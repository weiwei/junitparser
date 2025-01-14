# -*- coding: utf-8 -*-

import os
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


def test_fromfile():
    xml = JUnitXml.fromfile(os.path.join(os.path.dirname(__file__), "data/normal.xml"))
    suite1, suite2 = list(iter(xml))
    assert len(list(suite1.properties())) == 0
    assert len(list(suite2.properties())) == 3
    assert len(suite2) == 3
    assert suite2.name == "JUnitXmlReporter.constructor"
    assert suite2.tests == 3
    cases = list(suite2.iterchildren(TestCase))
    assert isinstance(cases[0].result[0], Failure)
    assert isinstance(cases[1].result[0], Skipped)
    assert len(cases[2].result) == 0


@pytest.mark.skipif(not has_lxml, reason="lxml required to run the case")
def test_fromfile_with_parser():
    def parse_func(file_path):
        xml_parser = XMLParser(huge_tree=True)
        return parse(file_path, xml_parser)

    xml = JUnitXml.fromfile(
        os.path.join(os.path.dirname(__file__), "data/normal.xml"),
        parse_func=parse_func,
    )
    suite1, suite2 = list(iter(xml))
    assert len(list(suite1.properties())) == 0
    assert len(list(suite2.properties())) == 3
    assert len(suite2) == 3
    assert suite2.name == "JUnitXmlReporter.constructor"
    assert suite2.tests == 3
    cases = list(suite2.iterchildren(TestCase))
    assert isinstance(cases[0].result[0], Failure)
    assert isinstance(cases[1].result[0], Skipped)
    assert len(cases[2].result) == 0


def test_fromfile_without_testsuites_tag():
    xml = JUnitXml.fromfile(
        os.path.join(os.path.dirname(__file__), "data/no_suites_tag.xml")
    )
    cases = list(iter(xml))
    properties = list(iter(xml.properties()))
    assert len(properties) == 3
    assert len(cases) == 3
    assert xml.name == "JUnitXmlReporter.constructor"
    assert xml.tests == 3
    assert isinstance(cases[0].result[0], Failure)
    assert isinstance(cases[1].result[0], Skipped)
    assert len(cases[2].result) == 0


def test_fromfile_with_testsuite_in_testsuite():
    xml = JUnitXml.fromfile(os.path.join(os.path.dirname(__file__), "data/jenkins.xml"))
    suite1, suite2 = list(iter(xml))
    assert len(list(suite1.properties())) == 0
    assert len(list(suite2.properties())) == 3
    assert len(suite2) == 3
    assert suite2.name == "JUnitXmlReporter.constructor"
    assert suite2.tests == 3
    direct_cases = list(suite2.iterchildren(TestCase))
    assert len(direct_cases) == 1
    assert isinstance(direct_cases[0].result[0], Failure)
    all_cases = list(suite2)
    assert isinstance(all_cases[0].result[0], Failure)
    assert isinstance(all_cases[1].result[0], Skipped)
    assert len(all_cases[2].result) == 0


def test_file_is_not_xml():
    text = "Not really an xml file"
    with NamedTemporaryFile(suffix=".xml", encoding="utf-8", mode="w", delete_on_close=False) as tmpfile:
        tmpfile.write(text)
        tmpfile.close()
        with pytest.raises(Exception):
            JUnitXml.fromfile(tmpfile.name)
            # Raises lxml.etree.XMLSyntaxError


def test_illegal_xml_file():
    text = "<some></some>"
    with NamedTemporaryFile(suffix=".xml", encoding="utf-8", mode="w", delete_on_close=False) as tmpfile:
        tmpfile.write(text)
        tmpfile.close()
        with pytest.raises(JUnitXmlError):
            JUnitXml.fromfile(tmpfile.name)


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
    suite = next(iter(xml))
    case = next(iter(suite))
    assert len(case.result) == 2
