import unittest
from junitparser import TestCase, TestSuite, Skipped, Failure, Error, Attr, JUnitXmlError, JUnitXml
from xml.etree import ElementTree as etree


class Test_JunitXml(unittest.TestCase):

    def test_fromstring(self):
        text = """<testsuites><testsuite name="suitename1">
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
        suite1.name = 'suite1'
        case1 = TestCase()
        case1.name = 'case1'
        suite1.add_testcase(case1)
        result = JUnitXml()
        result.add_testsuite(suite1)
        self.assertEqual(result._elem.tag, 'testsuites')
        suite = result._elem.findall('testsuite')
        self.assertEqual(len(suite), 1)
        self.assertEqual(suite[0].attrib['name'], 'suite1')
        case = suite[0].findall('testcase')
        self.assertEqual(len(case), 1)
        self.assertEqual(case[0].attrib['name'], 'case1')

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


class Test_RealFile(unittest.TestCase):

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mktemp(suffix='.xml')

    def tearDown(self):
        import os
        os.remove(self.tmp)

    def test_fromfile(self):
        text = """<?xml version="1.0" encoding="UTF-8"?>
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
        with open(self.tmp, 'w') as f:
            f.write(text)
        xml = JUnitXml.fromfile(self.tmp)
        suite1, suite2 = list(iter(xml))
        self.assertEqual(len(list(suite1.properties())), 0)
        self.assertEqual(len(list(suite2.properties())), 3)
        self.assertEqual(len(suite2), 3)
        self.assertEqual(suite2.name, 'JUnitXmlReporter.constructor')
        self.assertEqual(suite2.tests, '3')
        case_results = [Failure, Skipped, type(None)]
        for case, result in zip(suite2, case_results):
            self.assertIsInstance(case.result, result)

    def test_write(self):
        suite1 = TestSuite()
        suite1.name = 'suite1'
        case1 = TestCase()
        case1.name = 'case1'
        suite1.add_testcase(case1)
        result = JUnitXml()
        result.add_testsuite(suite1)
        result.write(self.tmp)
        with open(self.tmp) as f:
            text = f.read()
        self.assertIn('suite1', text)
        self.assertIn('case1', text)


class Test_TestSuite(unittest.TestCase):

    def test_fromstring(self):
        text = """<testsuite name="suitename">
        <testcase name="testname">
        <failure message="failure message" type="FailureType"/>
        </testcase></testsuite>"""
        suite = TestSuite.fromstring(text)
        suite.update_case_count()
        self.assertEqual(suite.name, 'suitename')
        self.assertEqual(suite.tests, '1')

    def test_props_fromstring(self):
        text = """<testsuite name="suitename">
        <properties><property name="name1" value="value1"/></properties>
        </testsuite>"""
        suite = TestSuite.fromstring(text)
        for prop in suite.properties():
            self.assertEqual(prop.name, 'name1')
            self.assertEqual(prop.value, 'value1')

    def test_len(self):
        text = """<testsuite name="suitename"><testcase name="testname"/>
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
        suite.add_testcase(case1)
        suite.add_testcase(case2)
        suite.add_testcase(case3)
        suite.update_case_count()
        self.assertEqual(suite.tests, '3')
        self.assertEqual(suite.failures, '1')
        self.assertEqual(suite.errors, '1')

    def test_add_property(self):
        suite = TestSuite()
        suite.add_property('name1', 'value1')
        res_prop = next(suite.properties())
        self.assertEqual(res_prop.name, 'name1')
        self.assertEqual(res_prop.value, 'value1')

    def test_remove_case(self):
        suite = TestSuite()
        case1 = TestCase()
        case1.name = 'test1'
        case2 = TestCase()
        case2.name = 'test2'
        suite.add_testcase(case1)
        suite.add_testcase(case2)
        suite.remove_testcase(case1)
        self.assertEqual(len(suite), 1)

    def test_remove_property(self):
        suite = TestSuite()
        suite.add_property('name1', 'value1')
        suite.add_property('name2', 'value2')
        suite.add_property('name3', 'value3')
        for prop in suite.properties():
            if prop.name == 'name2':
                suite.remove_property(prop)
        self.assertEqual(len(list(suite.properties())), 2)

    def test_suite_in_suite(self):
        suite = TestSuite('parent')
        childsuite = TestSuite('child')
        suite.add_suite(childsuite)
        self.assertEqual(len(list(suite.testsuites())), 1)


class Test_TestCase(unittest.TestCase):

    def test_fromstring(self):
        text = """<testcase name="testname">
        <failure message="failure message" type="FailureType"/>
        <system-out>System out</system-out>
        <system-err>System err</system-err>
        </testcase>"""
        case = TestCase.fromstring(text)
        self.assertEqual(case.name, "testname")
        self.assertIsInstance(case.result, Failure)
        self.assertEqual(case.system_out, "System out")
        self.assertEqual(case.system_err, "System err")

    def test_illegal_xml_multi_results(self):
        text = """<testcase name="testname">
        <failure message="failure message" type="FailureType"/>
        <skipped message="skipped message" type="FailureType"/>
        </testcase>
        """
        case = TestCase.fromstring(text)
        self.assertRaises(JUnitXmlError)

    def test_case_attributes(self):
        case = TestCase()
        case.name = 'testname'
        case.classname = 'testclassname'
        case.time = '15.123'
        case.result = Skipped()
        self.assertEqual(case.name, 'testname')
        self.assertEqual(case.classname, 'testclassname')
        self.assertEqual(case.time, '15.123')
        self.assertIsInstance(case.result, Skipped)

    def test_case_output(self):
        case = TestCase()
        case.system_err = 'error message'
        case.system_out = 'out message'
        self.assertEqual(case.system_err, 'error message')
        self.assertEqual(case.system_out, 'out message')
        case.system_err = 'error2'
        case.system_out = 'out2'
        self.assertEqual(case.system_err, 'error2')
        self.assertEqual(case.system_out, 'out2')

    def test_set_multiple_results(self):
        case = TestCase()
        case.result = Skipped()
        case.result = Failure()
        self.assertIsInstance(case.result, Failure)

    def test_monkypatch(self):
        TestCase.id = Attr('id')
        case = TestCase()
        case.id = "100"
        self.assertEqual(case.id, "100")

    def test_equal(self):
        case = TestCase()
        case.name = 'test1'
        case2 = TestCase()
        case2.name = 'test1'
        self.assertEqual(case, case2)

    def test_not_equal(self):
        case = TestCase()
        case.name = 'test1'
        case2 = TestCase()
        case2.name = 'test2'
        self.assertNotEqual(case, case2)

    def test_from_elem(self):
        elem = etree.Element('testcase', name='case1')
        case = TestCase.fromelem(elem)
        self.assertEqual(case.name, 'case1')

    def test_to_string(self):
        case = TestCase()
        case.name = 'test1'
        case_str = case.tostring()
        self.assertIn(b'test1', case_str)

if __name__ == '__main__':
    unittest.main()
