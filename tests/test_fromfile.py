# -*- coding: utf-8 -*-

import os
import unittest
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

from io import open


class Test_RealFile(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.tmp = tempfile.mktemp(suffix=".xml")

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_fromfile(self):
        xml = JUnitXml.fromfile(
            os.path.join(os.path.dirname(__file__), "data/normal.xml")
        )
        suite1, suite2 = list(iter(xml))
        self.assertEqual(len(list(suite1.properties())), 0)
        self.assertEqual(len(list(suite2.properties())), 3)
        self.assertEqual(len(suite2), 3)
        self.assertEqual(suite2.name, "JUnitXmlReporter.constructor")
        self.assertEqual(suite2.tests, 3)
        cases = list(suite2.iterchildren(TestCase))
        self.assertIsInstance(cases[0].result[0], Failure)
        self.assertIsInstance(cases[1].result[0], Skipped)
        self.assertEqual(len(cases[2].result), 0)

    @unittest.skipUnless(has_lxml, "lxml required to run the case")
    def test_fromfile_with_parser(self):
        def parse_func(file_path):
            xml_parser = XMLParser(huge_tree=True)
            return parse(file_path, xml_parser)

        xml = JUnitXml.fromfile(
            os.path.join(os.path.dirname(__file__), "data/normal.xml"),
            parse_func=parse_func,
        )
        suite1, suite2 = list(iter(xml))
        self.assertEqual(len(list(suite1.properties())), 0)
        self.assertEqual(len(list(suite2.properties())), 3)
        self.assertEqual(len(suite2), 3)
        self.assertEqual(suite2.name, "JUnitXmlReporter.constructor")
        self.assertEqual(suite2.tests, 3)
        cases = list(suite2.iterchildren(TestCase))
        self.assertIsInstance(cases[0].result[0], Failure)
        self.assertIsInstance(cases[1].result[0], Skipped)
        self.assertEqual(len(cases[2].result), 0)

    def test_fromfile_without_testsuites_tag(self):
        xml = JUnitXml.fromfile(
            os.path.join(os.path.dirname(__file__), "data/no_suites_tag.xml")
        )
        cases = list(iter(xml))
        properties = list(iter(xml.properties()))
        self.assertEqual(len(properties), 3)
        self.assertEqual(len(cases), 3)
        self.assertEqual(xml.name, "JUnitXmlReporter.constructor")
        self.assertEqual(xml.tests, 3)
        self.assertIsInstance(cases[0].result[0], Failure)
        self.assertIsInstance(cases[1].result[0], Skipped)
        self.assertEqual(len(cases[2].result), 0)

    def test_fromfile_with_testsuite_in_testsuite(self):
        xml = JUnitXml.fromfile(
            os.path.join(os.path.dirname(__file__), "data/jenkins.xml")
        )
        suite1, suite2 = list(iter(xml))
        self.assertEqual(len(list(suite1.properties())), 0)
        self.assertEqual(len(list(suite2.properties())), 3)
        self.assertEqual(len(suite2), 3)
        self.assertEqual(suite2.name, "JUnitXmlReporter.constructor")
        self.assertEqual(suite2.tests, 3)
        direct_cases = list(suite2.iterchildren(TestCase))
        self.assertEqual(len(direct_cases), 1)
        self.assertIsInstance(direct_cases[0].result[0], Failure)
        all_cases = list(suite2)
        self.assertIsInstance(all_cases[0].result[0], Failure)
        self.assertIsInstance(all_cases[1].result[0], Skipped)
        self.assertEqual(len(all_cases[2].result), 0)

    def test_write_xml_withouth_testsuite_tag(self):
        suite = TestSuite()
        suite.name = "suite1"
        case = TestCase()
        case.name = "case1"
        suite.add_testcase(case)
        suite.write(self.tmp)
        with open(self.tmp) as f:
            text = f.read()
        self.assertIn("suite1", text)
        self.assertIn("case1", text)

    def test_file_is_not_xml(self):
        text = "Not really an xml file"
        with open(self.tmp, "w") as f:
            f.write(text)
        with self.assertRaises(Exception):
            xml = JUnitXml.fromfile(self.tmp)
            # Raises lxml.etree.XMLSyntaxError

    def test_illegal_xml_file(self):
        text = "<some></some>"
        with open(self.tmp, "w") as f:
            f.write(text)
        with self.assertRaises(JUnitXmlError):
            xml = JUnitXml.fromfile(self.tmp)

    def test_write(self):
        suite1 = TestSuite()
        suite1.name = "suite1"
        case1 = TestCase()
        case1.name = "case1"
        suite1.add_testcase(case1)
        result = JUnitXml()
        result.add_testsuite(suite1)
        result.write(self.tmp)
        with open(self.tmp) as f:
            text = f.read()
        self.assertIn("suite1", text)
        self.assertIn("case1", text)

    def test_write_noarg(self):
        suite1 = TestSuite()
        suite1.name = "suite1"
        case1 = TestCase()
        case1.name = "case1"
        suite1.add_testcase(case1)
        result = JUnitXml()
        result.add_testsuite(suite1)
        with self.assertRaises(JUnitXmlError):
            result.write()

    def test_write_nonascii(self):
        suite1 = TestSuite()
        suite1.name = "suite1"
        case1 = TestCase()
        case1.name = "用例1"
        suite1.add_testcase(case1)
        result = JUnitXml()
        result.add_testsuite(suite1)
        result.write(self.tmp)
        with open(self.tmp, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("suite1", text)
        self.assertIn("用例1", text)

    def test_read_written_xml(self):
        suite1 = TestSuite()
        suite1.name = "suite1"
        case1 = TestCase()
        case1.name = "用例1"
        suite1.add_testcase(case1)
        result = JUnitXml()
        result.add_testsuite(suite1)
        result.write(self.tmp)
        xml = JUnitXml.fromfile(self.tmp)
        suite = next(iter(xml))
        case = next(iter(suite))
        self.assertEqual(case.name, "用例1")

    def test_multi_results_in_case(self):
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
        self.assertEqual(len(case.result), 2)

    def test_write_pretty(self):
        suite1 = TestSuite()
        suite1.name = "suite1"
        case1 = TestCase()
        case1.name = "用例1"
        suite1.add_testcase(case1)
        result = JUnitXml()
        result.add_testsuite(suite1)
        result.write(self.tmp, pretty=True)
        xml = JUnitXml.fromfile(self.tmp)
        suite = next(iter(xml))
        case = next(iter(suite))
        self.assertEqual(case.name, "用例1")
