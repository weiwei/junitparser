#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import with_statement
from __future__ import absolute_import
import os
import unittest
from copy import deepcopy
from junitparser import (TestCase, TestSuite, Skipped, Failure, Error, Attr,
                         JUnitXmlError, JUnitXml, Property, Properties)
from xml.etree import ElementTree as etree
from io import open
try:
    from itertools import izip #python2
except ImportError:
    izip = zip #python3


class Test_JunitXml(unittest.TestCase):

    def test_fromstring(self):
        text = u"""<testsuites><testsuite name="suitename1">
        <testcase name="testname1">
        </testcase></testsuite>
        <testsuite name="suitename2">
        <testcase name="testname2">
        </testcase></testsuite></testsuites>"""
        result = JUnitXml.fromstring(text)
        self.assertEqual(len(result), 2)

    def test_add_suite(self):
        suite1 = TestSuite()
        suite2 = TestSuite()
        result = JUnitXml()
        result.add_testsuite(suite1)
        result.add_testsuite(suite2)
        self.assertEqual(len(result), 2)

    def test_construct_xml(self):
        suite1 = TestSuite()
        suite1.name = u'suite1'
        case1 = TestCase()
        case1.name = u'case1'
        suite1.add_testcase(case1)
        result = JUnitXml()
        result.add_testsuite(suite1)
        self.assertEqual(result._elem.tag, u'testsuites')
        suite = result._elem.findall(u'testsuite')
        self.assertEqual(len(suite), 1)
        self.assertEqual(suite[0].attrib[u'name'], u'suite1')
        case = suite[0].findall(u'testcase')
        self.assertEqual(len(case), 1)
        self.assertEqual(case[0].attrib[u'name'], u'case1')

    def test_add(self):
        result1 = JUnitXml()
        suite1 = TestSuite()
        result1.add_testsuite(suite1)
        result2 = JUnitXml()
        suite2 = TestSuite()
        result2.add_testsuite(suite2)
        result3 = result1 + result2
        self.assertEqual(len(result3), 2)

    def test_iadd(self):
        result1 = JUnitXml()
        suite1 = TestSuite()
        result1.add_testsuite(suite1)
        result2 = JUnitXml()
        suite2 = TestSuite()
        result2.add_testsuite(suite2)
        result1 += result2
        self.assertEqual(len(result1), 2)

    def test_add_two_same_suites(self):
        suite1 = TestSuite()
        case1 = TestCase(name=u'case1')
        suite1.add_testcase(case1)
        suite2 = TestSuite()
        case2 = TestCase(name=u'case2')
        suite2.add_testcase(case2)
        suite3 = TestSuite()
        suite2.add_testsuite(suite3)
        result = suite1 + suite2
        self.assertIsInstance(result, TestSuite)
        self.assertEqual(len(list(iter(result))), 2)
        self.assertEqual(len(list(iter(result.testsuites()))), 1)

    def test_iadd_two_same_suites(self):
        suite1 = TestSuite()
        case1 = TestCase(name=u'case1')
        suite1.add_testcase(case1)
        suite2 = TestSuite()
        case2 = TestCase(name=u'case2')
        suite2.add_testcase(case2)
        suite3 = TestSuite()
        suite2.add_testsuite(suite3)
        suite1 += suite2
        self.assertIsInstance(suite1, TestSuite)
        self.assertEqual(len(list(iter(suite1))), 2)
        self.assertEqual(len(list(iter(suite1.testsuites()))), 1)

    def test_add_two_different_suites(self):
        suite1 = TestSuite(name=u'suite1')
        case1 = TestCase(name=u'case1')
        suite1.add_testcase(case1)
        suite2 = TestSuite(name=u'suite2')
        case2 = TestCase(name=u'case2')
        suite2.add_testcase(case2)
        result = suite1 + suite2
        self.assertIsInstance(result, JUnitXml)
        self.assertEqual(len(list(iter(result))), 2)

    def test_iadd_two_different_suites(self):
        suite1 = TestSuite(name=u'suite1')
        case1 = TestCase(name=u'case1')
        suite1.add_testcase(case1)
        suite2 = TestSuite(name=u'suite2')
        case2 = TestCase(name=u'case2')
        suite2.add_testcase(case2)
        suite1 += suite2
        self.assertIsInstance(suite1, JUnitXml)
        self.assertEqual(len(list(iter(suite1))), 2)

    def test_xml_statistics(self):
        result1 = JUnitXml()
        suite1 = TestSuite()
        result1.add_testsuite(suite1)
        result2 = JUnitXml()
        suite2 = TestSuite()
        result2.add_testsuite(suite2)
        result3 = result1 + result2
        result3.update_statistics()


class Test_RealFile(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mktemp(suffix=u'.xml')

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_fromfile(self):
        text = u"""<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
   <testsuite name="JUnitXmlReporter" errors="0" tests="0" failures="0" time="0" timestamp="2013-05-24T10:23:58" />
   <testsuite name="JUnitXmlReporter.constructor" errors="0" skipped="1" tests="3" failures="1" time="0.006" timestamp="2013-05-24T10:23:58">
      <properties>
         <property name="java.vendor" value="Sun Microsystems Inc." />
         <property name="compiler.debug" value="on" />
         <property name="project.jdk.classpath" value="jdk.classpath.1.6" />
      </properties>
      <testcase classname="JUnitXmlReporter.constructor" name="should default path to an empty string" time="0.006">
         <failure message="test failure">Assertion failed</failure>
      </testcase>
      <testcase classname="JUnitXmlReporter.constructor" name="should default consolidate to true" time="0">
         <skipped />
      </testcase>
      <testcase classname="JUnitXmlReporter.constructor" name="should default useDotNotation to true" time="0" />
   </testsuite>
</testsuites>"""
        with open(self.tmp, u'w') as f:
            f.write(text)
        xml = JUnitXml.fromfile(self.tmp)
        suite1, suite2 = list(iter(xml))
        self.assertEqual(len(list(suite1.properties())), 0)
        self.assertEqual(len(list(suite2.properties())), 3)
        self.assertEqual(len(suite2), 3)
        self.assertEqual(suite2.name, u'JUnitXmlReporter.constructor')
        self.assertEqual(suite2.tests, 3)
        case_results = [Failure, Skipped, type(None)]
        for case, result in izip(suite2, case_results):
            self.assertIsInstance(case.result, result)

    def test_fromfile_without_testsuites_tag(self):
        text = u"""<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="JUnitXmlReporter.constructor" errors="0" skipped="1" tests="3" failures="1" time="0.006" timestamp="2013-05-24T10:23:58">
    <properties>
        <property name="java.vendor" value="Sun Microsystems Inc." />
        <property name="compiler.debug" value="on" />
        <property name="project.jdk.classpath" value="jdk.classpath.1.6" />
    </properties>
    <testcase classname="JUnitXmlReporter.constructor" name="should default path to an empty string" time="0.006">
        <failure message="test failure">Assertion failed</failure>
    </testcase>
    <testcase classname="JUnitXmlReporter.constructor" name="should default consolidate to true" time="0">
        <skipped />
    </testcase>
    <testcase classname="JUnitXmlReporter.constructor" name="should default useDotNotation to true" time="0" />
</testsuite>"""
        with open(self.tmp, u'w') as f:
            f.write(text)
        xml = JUnitXml.fromfile(self.tmp)
        cases = list(iter(xml))
        properties = list(iter(xml.properties()))
        self.assertEqual(len(properties), 3)
        self.assertEqual(len(cases), 3)
        self.assertEqual(xml.name, u'JUnitXmlReporter.constructor')
        self.assertEqual(xml.tests, 3)
        case_results = [Failure, Skipped, type(None)]
        for case, result in izip(xml, case_results):
            self.assertIsInstance(case.result, result)

    def test_write_xml_withouth_testsuite_tag(self):
        suite = TestSuite()
        suite.name = u'suite1'
        case = TestCase()
        case.name = u'case1'
        suite.add_testcase(case)
        suite.write(self.tmp)
        with open(self.tmp) as f:
            text = f.read()
        self.assertIn(u'suite1', text)
        self.assertIn(u'case1', text)

    def test_file_is_not_xml(self):
        text = u"Not really an xml file"
        with open(self.tmp, u'w') as f:
            f.write(text)
        with self.assertRaises(Exception):
            xml = JUnitXml.fromfile(self.tmp)
            # Raises lxml.etree.XMLSyntaxError

    def test_illegal_xml_file(self):
        text = u"<some></some>"
        with open(self.tmp, u'w') as f:
            f.write(text)
        with self.assertRaises(JUnitXmlError):
            xml = JUnitXml.fromfile(self.tmp)

    def test_write(self):
        suite1 = TestSuite()
        suite1.name = u'suite1'
        case1 = TestCase()
        case1.name = u'case1'
        suite1.add_testcase(case1)
        result = JUnitXml()
        result.add_testsuite(suite1)
        result.write(self.tmp)
        with open(self.tmp) as f:
            text = f.read()
        self.assertIn(u'suite1', text)
        self.assertIn(u'case1', text)

    def test_write_noarg(self):
        suite1 = TestSuite()
        suite1.name = u'suite1'
        case1 = TestCase()
        case1.name = u'case1'
        suite1.add_testcase(case1)
        result = JUnitXml()
        result.add_testsuite(suite1)
        with self.assertRaises(JUnitXmlError):
            result.write()

    def test_write_nonascii(self):
        suite1 = TestSuite()
        suite1.name = u'suite1'
        case1 = TestCase()
        case1.name = u'用例1'
        suite1.add_testcase(case1)
        result = JUnitXml()
        result.add_testsuite(suite1)
        result.write(self.tmp)
        with open(self.tmp, encoding=u'utf-8') as f:
            text = f.read()
        self.assertIn(u'suite1', text)
        self.assertIn(u'用例1', text)

    def test_read_written_xml(self):
        suite1 = TestSuite()
        suite1.name = u'suite1'
        case1 = TestCase()
        case1.name = u'用例1'
        suite1.add_testcase(case1)
        result = JUnitXml()
        result.add_testsuite(suite1)
        result.write(self.tmp)
        xml = JUnitXml.fromfile(self.tmp)
        suite = iter(xml).next()
        case = iter(suite).next()
        self.assertEqual(case.name, u'用例1')

    def test_multi_results_in_case(self):
        # Has to be a binary string to include xml declarations.
        text = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
   <testsuite name="JUnitXmlReporter.constructor">
      <testcase classname="JUnitXmlReporter.constructor" name="should default path to an empty string" time="0.006">
         <failure message="test failure">Assertion failed</failure>
         <skipped />
      </testcase>
   </testsuite>
</testsuites>"""
        xml = JUnitXml.fromstring(text)
        suite = iter(xml).next()
        case = iter(suite).next()
        with self.assertRaises(JUnitXmlError):
            result = case.result

    def test_write_pretty(self):
        suite1 = TestSuite()
        suite1.name = u'suite1'
        case1 = TestCase()
        case1.name = u'用例1'
        suite1.add_testcase(case1)
        result = JUnitXml()
        result.add_testsuite(suite1)
        result.write(self.tmp, pretty=True)
        xml = JUnitXml.fromfile(self.tmp)
        suite = iter(xml).next()
        case = iter(suite).next()
        self.assertEqual(case.name, u'用例1')


class Test_TestSuite(unittest.TestCase):

    def test_fromstring(self):
        text = u"""<testsuite name="suitename">
        <testcase name="testname">
        <failure message="failure message" type="FailureType"/>
        </testcase></testsuite>"""
        suite = TestSuite.fromstring(text)
        suite.update_statistics()
        self.assertEqual(suite.name, u'suitename')
        self.assertEqual(suite.tests, 1)

    def test_props_fromstring(self):
        text = u"""<testsuite name="suitename">
        <properties><property name="name1" value="value1"/></properties>
        </testsuite>"""
        suite = TestSuite.fromstring(text)
        for prop in suite.properties():
            self.assertEqual(prop.name, u'name1')
            self.assertEqual(prop.value, u'value1')

    def test_len(self):
        text = u"""<testsuite name="suitename"><testcase name="testname"/>
        <testcase name="testname2"/>
        </testsuite>"""
        suite = TestSuite.fromstring(text)
        self.assertEqual(len(suite), 2)

    def test_add_case(self):
        suite = TestSuite()
        case1 = TestCase()
        case2 = TestCase()
        case2.result = Failure()
        case3 = TestCase()
        case3.result = Error()
        case4 = TestCase()
        case4.result = Skipped()
        suite.add_testcase(case1)
        suite.add_testcase(case2)
        suite.add_testcase(case3)
        suite.add_testcase(case4)
        suite.update_statistics()
        self.assertEqual(suite.tests, 4)
        self.assertEqual(suite.failures, 1)
        self.assertEqual(suite.errors, 1)
        self.assertEqual(suite.skipped, 1)

    def test_case_count(self):
        suite = TestSuite()
        case1 = TestCase()
        suite.add_testcase(case1)
        self.assertEqual(suite.tests, 1)
        self.assertEqual(suite.failures, 0)

    def test_add_property(self):
        suite = TestSuite()
        suite.add_property(u'name1', u'value1')
        res_prop = suite.properties().next()
        self.assertEqual(res_prop.name, u'name1')
        self.assertEqual(res_prop.value, u'value1')

    def test_remove_case(self):
        suite = TestSuite()
        case1 = TestCase()
        case1.name = u'test1'
        case2 = TestCase()
        case2.name = u'test2'
        suite.add_testcase(case1)
        suite.add_testcase(case2)
        suite.remove_testcase(case1)
        self.assertEqual(len(suite), 1)

    def test_remove_property(self):
        suite = TestSuite()
        suite.add_property(u'name1', u'value1')
        suite.add_property(u'name2', u'value2')
        suite.add_property(u'name3', u'value3')
        for prop in suite.properties():
            if prop.name == u'name2':
                suite.remove_property(prop)
        self.assertEqual(len(list(suite.properties())), 2)

    def test_remove_property_from_none(self):
        suite = TestSuite()
        suite.remove_property(Property(u'key', u'value'))
        # Nothing should happen

    def test_suite_in_suite(self):
        suite = TestSuite(u'parent')
        childsuite = TestSuite(u'child')
        suite.add_testsuite(childsuite)
        self.assertEqual(len(list(suite.testsuites())), 1)

    def test_case_time(self):
        suite = TestSuite()
        case1 = TestCase()
        case1.name = u'test1'
        case1.time = 15
        suite.add_testcase(case1)
        suite.update_statistics()
        self.assertEqual(suite.time, 15)

    def test_wrong_attr_type(self):
        suite = TestSuite()
        with self.assertRaises(TypeError):
            suite.time = u'abc'
        with self.assertRaises(TypeError):
            suite.tests = 10.5

    def test_suite_eq(self):
        suite = TestSuite()
        suite.add_property(u'name1', u'value1')
        suite2 = deepcopy(suite)
        self.assertEqual(suite, suite2)

    def test_suite_ne(self):
        suite = TestSuite()
        suite.add_property(u'name1', u'value1')
        suite2 = deepcopy(suite)
        suite2.add_property(u'name2', u'value2')
        self.assertNotEqual(suite, suite2)


class Test_TestCase(unittest.TestCase):

    def test_fromstring(self):
        text = u"""<testcase name="testname">
        <failure message="failure message" type="FailureType"/>
        <system-out>System out</system-out>
        <system-err>System err</system-err>
        </testcase>"""
        case = TestCase.fromstring(text)
        self.assertEqual(case.name, u"testname")
        self.assertIsInstance(case.result, Failure)
        self.assertEqual(case.system_out, u"System out")
        self.assertEqual(case.system_err, u"System err")

    def test_illegal_xml_multi_results(self):
        text = u"""<testcase name="testname">
        <failure message="failure message" type="FailureType"/>
        <skipped message="skipped message" type="FailureType"/>
        </testcase>
        """
        case = TestCase.fromstring(text)
        self.assertRaises(JUnitXmlError)

    def test_case_attributes(self):
        case = TestCase()
        case.name = u'testname'
        case.classname = u'testclassname'
        case.time = 15.123
        case.result = Skipped()
        self.assertEqual(case.name, u'testname')
        self.assertEqual(case.classname, u'testclassname')
        self.assertEqual(case.time, 15.123)
        self.assertIsInstance(case.result, Skipped)

    def test_case_output(self):
        case = TestCase()
        case.system_err = u'error message'
        case.system_out = u'out message'
        self.assertEqual(case.system_err, u'error message')
        self.assertEqual(case.system_out, u'out message')
        case.system_err = u'error2'
        case.system_out = u'out2'
        self.assertEqual(case.system_err, u'error2')
        self.assertEqual(case.system_out, u'out2')

    def test_set_multiple_results(self):
        case = TestCase()
        case.result = Skipped()
        case.result = Failure()
        self.assertIsInstance(case.result, Failure)

    def test_monkypatch(self):
        TestCase.id = Attr(u'id')
        case = TestCase()
        case.id = u"100"
        self.assertEqual(case.id, u"100")

    def test_equal(self):
        case = TestCase()
        case.name = u'test1'
        case2 = TestCase()
        case2.name = u'test1'
        self.assertEqual(case, case2)

    def test_not_equal(self):
        case = TestCase()
        case.name = u'test1'
        case2 = TestCase()
        case2.name = u'test2'
        self.assertNotEqual(case, case2)

    def test_from_elem(self):
        elem = etree.Element(u'testcase', name=u'case1')
        case = TestCase.fromelem(elem)
        self.assertEqual(case.name, u'case1')

    def test_to_string(self):
        case = TestCase()
        case.name = u'test1'
        case_str = case.tostring()
        self.assertIn('test1', case_str)

    def test_to_nonascii_string(self):
        case = TestCase()
        case.name = u'测试1'
        case.result = Failure(u'失败', u'类型')
        case_str = case.tostring()
        self.assertIn(u'测试1', case_str.decode('utf-8'))
        self.assertIn(u'失败', case_str.decode('utf-8'))
        self.assertIn(u'类型', case_str.decode('utf-8'))

    def test_system_out(self):
        case = TestCase()
        case.name = u'case1'
        self.assertIsNone(case.system_out)
        case.system_out = u"output"
        self.assertEqual(case.system_out, u"output")

    def test_system_err(self):
        case = TestCase()
        case.name = u'case1'
        self.assertIsNone(case.system_err)
        case.system_err = u"error"
        self.assertEqual(case.system_err, u"error")

    def test_result_eq(self):
        # TODO: Weird, need to think of a better API
        self.assertEqual(Failure(u'A'), Failure(u'A'))
        self.assertNotEqual(Skipped(u'B'), Skipped(u'A'))
        self.assertNotEqual(Error(u'C'), Error(u'B'))


class Test_Properties(unittest.TestCase):

    def test_property_repr1(self):
        prop1 = Property(u'prop1', u'1')
        self.assertEqual(prop1.__repr__(), u'<Element \'property\' name="prop1" value="1">')

    def test_property_repr2(self):
        prop1 = TestSuite()
        self.assertEqual(prop1.__repr__(), u'<Element \'testsuite\'>')

    def test_property_eq(self):
        prop1 = Property(u'prop1', u'1')
        prop2 = Property(u'prop1', u'1')
        self.assertEqual(prop1, prop2)

    def test_property_ne(self):
        prop1 = Property(u'prop1', u'1')
        prop2 = Property(u'prop1', u'2')
        self.assertNotEqual(prop1, prop2)

    def test_properties_eq(self):
        prop1 = Property(u'prop1', u'1')
        prop2 = Property(u'prop1', u'2')
        prop3 = deepcopy(prop1) # Note: an attribute can only be used at one place.
        prop4 = deepcopy(prop2)
        props1 = Properties()
        props1.add_property(prop1)
        props1.add_property(prop2)
        props2 = Properties()
        props2.add_property(prop3)
        props2.add_property(prop4)
        self.assertEqual(props1, props2)

    def test_properties_ne(self):
        prop1 = Property(u'prop1', u'1')
        prop2 = Property(u'prop1', u'2')
        prop3 = deepcopy(prop1)
        prop4 = deepcopy(prop1)
        props1 = Properties()
        props1.add_property(prop1)
        props1.add_property(prop2)
        props2 = Properties()
        props2.add_property(prop3)
        props2.add_property(prop4)
        self.assertNotEqual(props1, props2)

    def test_properties_ne2(self):
        prop1 = Property(u'prop1', u'1')
        prop2 = Property(u'prop1', u'2')
        prop3 = deepcopy(prop1)
        props1 = Properties()
        props1.add_property(prop1)
        props1.add_property(prop2)
        props2 = Properties()
        props2.add_property(prop3)
        self.assertNotEqual(props1, props2)


if __name__ == u'__main__':
    unittest.main()
