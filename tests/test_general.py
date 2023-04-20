# -*- coding: utf-8 -*-

import locale
import unittest
from copy import deepcopy
from xml.etree import ElementTree as etree

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
    Element,
)

try:
    import itertools.izip as zip
except ImportError:
    pass


try:
    from lxml import etree as expected_lxml_etree
    has_lxml = True
except ImportError:
    from xml.etree import ElementTree as expected_xml_etree
    has_lxml = False


class Test_XmlPackage(unittest.TestCase):

    @unittest.skipIf(has_lxml, "xml package is used unless lxml is installed")
    def test_xml_etree(self):
        from junitparser.junitparser import etree as actual_etree
        self.assertEqual(actual_etree, expected_xml_etree)

    @unittest.skipUnless(has_lxml, "lxml package has to be installed")
    def test_lxml_etree(self):
        from junitparser.junitparser import etree as actual_etree
        self.assertEqual(actual_etree, expected_lxml_etree)


class Test_MergeSuiteCounts(unittest.TestCase):
    def test_merge_test_count(self):
        text1 = """<testsuite name="suitename1" tests="2" failures="1">
        <testcase name="testname1"><failure message="failed"/></testcase>
        <testcase name="testname2"></testcase>
        </testsuite>"""
        test_suite1 = TestSuite.fromstring(text1)

        text2 = """<testsuite name="suitename2" tests="2" skipped="1">
        <testcase name="testname3"><skipped message="no reason given"/></testcase>
        <testcase name="testname4"></testcase>
        </testsuite>"""
        test_suite2 = TestSuite.fromstring(text2)

        combined_suites = JUnitXml()
        combined_suites += test_suite1
        combined_suites += test_suite2
        self.assertEqual(combined_suites.tests, 4)
        self.assertEqual(combined_suites.failures, 1)
        self.assertEqual(combined_suites.skipped, 1)

    def test_merge_same_suite(self):
        text1 = """<testsuite name="suitename1" tests="2" failures="1">
        <testcase name="testname1"><failure message="failed"/></testcase>
        <testcase name="testname2"></testcase>
        </testsuite>"""
        test_suite1 = TestSuite.fromstring(text1)

        text2 = """<testsuite name="suitename1" tests="2" skipped="1">
        <testcase name="testname3"><skipped message="no reason given"/></testcase>
        <testcase name="testname4"></testcase>
        </testsuite>"""
        test_suite2 = TestSuite.fromstring(text2)

        combined_suites = JUnitXml()
        combined_suites += test_suite1
        combined_suites += test_suite2
        suites = list(suite for suite in combined_suites)
        self.assertEqual(len(suites), 1)
        self.assertEqual(combined_suites.tests, 4)
        self.assertEqual(combined_suites.failures, 1)
        self.assertEqual(combined_suites.skipped, 1)


class Test_JunitXml(unittest.TestCase):
    def test_fromstring(self):
        text = """<testsuites><testsuite name="suitename1">
        <testcase name="testname1">
        </testcase></testsuite>
        <testsuite name="suitename2">
        <testcase name="testname2">
        </testcase></testsuite></testsuites>"""
        result = JUnitXml.fromstring(text)
        self.assertEqual(result.time, 0)
        self.assertEqual(len(result), 2)

    def test_fromstring_no_testsuites(self):
        text = """<testsuite name="suitename1">
        <testcase name="testname1">
        </testcase></testsuite>"""
        result = JUnitXml.fromstring(text)
        self.assertEqual(result.time, 0)
        self.assertEqual(len(result), 1)

    def test_fromstring_numbers_locale_insensitive(self):
        "Case relies on that LC_ALL is set in the console."
        for loc in ["", "en_US.UTF-8", "de_DE.UTF-8"]:
            old_locale = locale.getlocale(locale.LC_NUMERIC)
            try:
                locale.setlocale(locale.LC_NUMERIC, loc)
                text = """<testsuites>
                <testsuite errors="0" failures="0" hostname="hooch" name="pytest" skipped="0" tests="2" time="1000.125" timestamp="2020-02-05T10:52:33.843536">
                <testcase classname="test_x" file="test_x.py" line="7" name="test_comp_1" time="1,000.025"/>
                <testcase classname="test_x" file="test_x.py" line="10" name="test_comp_2" time="0.1"/>
                </testsuite>
                </testsuites>"""
                result = JUnitXml.fromstring(text)
                suite = list(iter(result))[0]
                self.assertEqual(suite.time, 1000.125, msg=loc)
                cases = list(iter(suite))
                self.assertEqual(cases[0].time, 1000.025, msg=loc)
                self.assertEqual(cases[1].time, 0.1, msg=loc)
            finally:
                locale.setlocale(locale.LC_NUMERIC, old_locale)

    def test_fromstring_multiple_fails(self):
        text = """<testsuites>
        <testsuite errors="1" failures="0" hostname="hooch" name="pytest" skipped="1" tests="3" time="0.025" timestamp="2020-02-05T10:52:33.843536">
        <testcase classname="test_x" file="test_x.py" line="7" name="test_comp_1" time="0.000"/>
        <testcase classname="test_x" file="test_x.py" line="10" name="test_comp_2" time="0.000">
        <skipped message="unconditional skip" type="pytest.skip">test_x.py:11: unconditional skip</skipped>
        <error message="test teardown failure">
        @pytest.fixture(scope="module") def compb(): yield > raise PermissionError E PermissionError test_x.py:6: PermissionError
        </error>
        </testcase>
        </testsuite>
        </testsuites>"""
        result = JUnitXml.fromstring(text)
        self.assertIsInstance(result, JUnitXml)
        self.assertEqual(result.errors, 1)
        self.assertEqual(result.skipped, 1)
        suite = list(iter(result))[0]
        cases = list(iter(suite))
        self.assertEqual(len(cases[0].result), 0)
        self.assertEqual(len(cases[1].result), 2)
        text = cases[1].result[1].text
        self.assertTrue("@pytest.fixture" in text)

    def test_fromroot_testsuite(self):
        text = """
        <testsuite errors="1" failures="0" hostname="hooch" name="pytest" skipped="1" tests="3" time="0.025" timestamp="2020-02-05T10:52:33.843536">
        <testcase classname="test_x" file="test_x.py" line="7" name="test_comp_1" time="0.000"/>
        <testcase classname="test_x" file="test_x.py" line="10" name="test_comp_2" time="0.000">
        <skipped message="unconditional skip" type="pytest.skip">test_x.py:11: unconditional skip</skipped>
        <error message="test teardown failure">
        @pytest.fixture(scope="module") def compb(): yield > raise PermissionError E PermissionError test_x.py:6: PermissionError
        </error>
        </testcase>
        </testsuite>"""
        root_elemt = etree.fromstring(text)
        result = JUnitXml.fromroot(root_elemt)
        self.assertIsInstance(result, TestSuite)
        self.assertEqual(result.errors, 1)
        self.assertEqual(result.skipped, 1)
        cases = list(iter(result))
        self.assertEqual(len(cases[0].result), 0)
        self.assertEqual(len(cases[1].result), 2)
        text = cases[1].result[1].text
        self.assertTrue("@pytest.fixture" in text)

    def test_fromroot_testsuites(self):
        text = """<testsuites>
        <testsuite errors="1" failures="0" hostname="hooch" name="pytest" skipped="1" tests="3" time="0.025" timestamp="2020-02-05T10:52:33.843536">
        <testcase classname="test_x" file="test_x.py" line="7" name="test_comp_1" time="0.000"/>
        <testcase classname="test_x" file="test_x.py" line="10" name="test_comp_2" time="0.000">
        <skipped message="unconditional skip" type="pytest.skip">test_x.py:11: unconditional skip</skipped>
        <error message="test teardown failure">
        @pytest.fixture(scope="module") def compb(): yield > raise PermissionError E PermissionError test_x.py:6: PermissionError
        </error>
        </testcase>
        </testsuite>
        </testsuites>"""
        root_elemt = etree.fromstring(text)
        result = JUnitXml.fromroot(root_elemt)
        self.assertEqual(result.errors, 1)
        self.assertEqual(result.skipped, 1)
        suite = list(iter(result))[0]
        cases = list(iter(suite))
        self.assertEqual(len(cases[0].result), 0)
        self.assertEqual(len(cases[1].result), 2)
        text = cases[1].result[1].text
        self.assertTrue("@pytest.fixture" in text)

    def test_fromstring_invalid(self):
        text = """<random name="suitename1"></random>"""
        with self.assertRaises(Exception) as context:
            JUnitXml.fromstring(text)
        self.assertTrue(isinstance(context.exception, JUnitXmlError))

    def test_add_suite(self):
        suite1 = TestSuite("suite1")
        suite2 = TestSuite("suite2")
        result = JUnitXml()
        result.add_testsuite(suite1)
        result.add_testsuite(suite2)
        self.assertEqual(len(result), 2)

    def test_construct_xml(self):
        suite1 = TestSuite()
        suite1.name = "suite1"
        case1 = TestCase()
        case1.name = "case1"
        suite1.add_testcase(case1)
        result = JUnitXml()
        result.add_testsuite(suite1)
        self.assertEqual(result._elem.tag, "testsuites")
        suite = result._elem.findall("testsuite")
        self.assertEqual(len(suite), 1)
        self.assertEqual(suite[0].attrib["name"], "suite1")
        case = suite[0].findall("testcase")
        self.assertEqual(len(case), 1)
        self.assertEqual(case[0].attrib["name"], "case1")

    def test_add(self):
        result1 = JUnitXml()
        suite1 = TestSuite("suite1")
        result1.add_testsuite(suite1)
        result2 = JUnitXml()
        suite2 = TestSuite("suite2")
        result2.add_testsuite(suite2)
        result3 = result1 + result2
        self.assertEqual(len(result3), 2)

    def test_add_same_suite(self):
        result1 = JUnitXml()
        suite1 = TestSuite()
        result1.add_testsuite(suite1)
        result2 = JUnitXml()
        suite2 = TestSuite()
        result2.add_testsuite(suite2)
        result3 = result1 + result2
        self.assertEqual(len(result3), 1)

    def test_iadd(self):
        result1 = JUnitXml()
        suite1 = TestSuite("suite1")
        result1.add_testsuite(suite1)
        result2 = JUnitXml()
        suite2 = TestSuite("suite2")
        result2.add_testsuite(suite2)
        result1 += result2
        self.assertEqual(len(result1), 2)

    def test_iadd_same_suite(self):
        result1 = JUnitXml()
        suite1 = TestSuite()
        result1.add_testsuite(suite1)
        result2 = JUnitXml()
        suite2 = TestSuite()
        result2.add_testsuite(suite2)
        result1 += result2
        self.assertEqual(len(result1), 1)

    def test_add_two_same_suites(self):
        suite1 = TestSuite()
        case1 = TestCase(name="case1")
        suite1.add_testcase(case1)
        suite2 = TestSuite()
        case2 = TestCase(name="case2")
        suite2.add_testcase(case2)
        suite3 = TestSuite()
        suite2.add_testsuite(suite3)
        result = suite1 + suite2
        self.assertIsInstance(result, TestSuite)
        self.assertEqual(len(list(iter(result))), 2)
        self.assertEqual(len(list(iter(result.testsuites()))), 1)

    def test_iadd_two_same_suites(self):
        suite1 = TestSuite()
        case1 = TestCase(name="case1")
        suite1.add_testcase(case1)
        suite2 = TestSuite()
        case2 = TestCase(name="case2")
        suite2.add_testcase(case2)
        suite3 = TestSuite()
        suite2.add_testsuite(suite3)
        suite1 += suite2
        self.assertIsInstance(suite1, TestSuite)
        self.assertEqual(len(list(iter(suite1))), 2)
        self.assertEqual(len(list(iter(suite1.testsuites()))), 1)

    def test_add_two_different_suites(self):
        suite1 = TestSuite(name="suite1")
        case1 = TestCase(name="case1")
        suite1.add_testcase(case1)
        suite2 = TestSuite(name="suite2")
        case2 = TestCase(name="case2")
        suite2.add_testcase(case2)
        result = suite1 + suite2
        self.assertIsInstance(result, JUnitXml)
        self.assertEqual(len(list(iter(result))), 2)

    def test_iadd_two_different_suites(self):
        suite1 = TestSuite(name="suite1")
        case1 = TestCase(name="case1")
        suite1.add_testcase(case1)
        suite2 = TestSuite(name="suite2")
        case2 = TestCase(name="case2")
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
        self.assertEqual(result3.tests, 0)


class Test_TestSuite(unittest.TestCase):
    def test_fromstring(self):
        text = """<testsuite name="suitename" time="1.32">
        <testcase name="testname">
        <failure message="failure message" type="FailureType"/>
        </testcase></testsuite>"""
        suite = TestSuite.fromstring(text)
        self.assertEqual(suite.time, 1.32)
        suite.update_statistics()
        self.assertEqual(suite.name, "suitename")
        self.assertEqual(suite.tests, 1)

    def test_props_fromstring(self):
        text = """<testsuite name="suitename">
        <properties><property name="name1" value="value1"/></properties>
        </testsuite>"""
        suite = TestSuite.fromstring(text)
        for prop in suite.properties():
            self.assertEqual(prop.name, "name1")
            self.assertEqual(prop.value, "value1")

    def test_quoted_attr(self):
        text = """<testsuite name="suitename with &quot;quotes&quot;">
        </testsuite>"""
        suite = TestSuite.fromstring(text)
        self.assertEqual(suite.name, 'suitename with "quotes"')

    def test_combining_testsuite_should_keep_name(self):
        text1 = """<testsuite name="suitename1" tests="2" failures="1">
        <testcase name="testname1"><failure message="failed"/></testcase>
        <testcase name="testname2"></testcase>
        </testsuite>"""
        test_suite1 = TestSuite.fromstring(text1)

        text2 = """<testsuite name="suitename2" tests="2" skipped="1">
        <testcase name="testname3"><skipped message="no reason given"/></testcase>
        <testcase name="testname4"></testcase>
        </testsuite>"""
        test_suite2 = TestSuite.fromstring(text2)

        combined_suites = JUnitXml()
        combined_suites += test_suite1
        combined_suites += test_suite2

        self.assertEqual(
            [s.name for s in combined_suites], ["suitename1", "suitename2"]
        )

    def test_len(self):
        text = """<testsuite name="suitename"><testcase name="testname"/>
        <testcase name="testname2"/>
        </testsuite>"""
        suite = TestSuite.fromstring(text)
        self.assertEqual(len(suite), 2)

    def test_add_case(self):
        suite = TestSuite()
        self.assertEqual(suite.tests, 0)
        case1 = TestCase()
        case2 = TestCase()
        case2.result = [Failure()]
        case3 = TestCase()
        case3.result = [Error()]
        case4 = TestCase()
        case4.result = [Skipped()]
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
        suite.add_property("name1", "value1")
        res_prop = next(suite.properties())
        self.assertEqual(res_prop.name, "name1")
        self.assertEqual(res_prop.value, "value1")

    def test_remove_case(self):
        suite = TestSuite()
        case1 = TestCase()
        case1.name = "test1"
        case2 = TestCase()
        case2.name = "test2"
        suite.add_testcase(case1)
        suite.add_testcase(case2)
        suite.remove_testcase(case1)
        self.assertEqual(len(suite), 1)

    def test_remove_property(self):
        suite = TestSuite()
        suite.add_property("name1", "value1")
        suite.add_property("name2", "value2")
        suite.add_property("name3", "value3")
        for prop in suite.properties():
            if prop.name == "name2":
                suite.remove_property(prop)
        self.assertEqual(len(list(suite.properties())), 2)

    def test_remove_property_from_none(self):
        suite = TestSuite()
        suite.remove_property(Property("key", "value"))
        # Nothing should happen

    def test_suite_in_suite(self):
        suite = TestSuite("parent")
        childsuite = TestSuite("child")
        suite.add_testsuite(childsuite)
        self.assertEqual(len(list(suite.testsuites())), 1)

    def test_case_time(self):
        suite = TestSuite()
        case1 = TestCase()
        case1.name = "test1"
        case1.time = 15
        suite.add_testcase(case1)
        suite.update_statistics()
        self.assertEqual(suite.time, 15)

    def test_wrong_attr_type(self):
        suite = TestSuite()
        with self.assertRaises(TypeError):
            suite.time = "abc"
        with self.assertRaises(TypeError):
            suite.tests = 10.5

    def test_suite_eq(self):
        suite = TestSuite()
        suite.add_property("name1", "value1")
        suite2 = deepcopy(suite)
        self.assertEqual(suite, suite2)

    def test_suite_ne(self):
        suite = TestSuite()
        suite.add_property("name1", "value1")
        suite2 = deepcopy(suite)
        suite2.add_property("name2", "value2")
        self.assertNotEqual(suite, suite2)

    def test_add_cases(self):
        suite = TestSuite()
        self.assertEqual(suite.tests, 0)
        case1 = TestCase()
        case2 = TestCase()
        case2.result = [Failure()]
        case3 = TestCase()
        case3.result = [Error()]
        case4 = TestCase()
        case4.result = [Skipped()]
        suite.add_testcases([case1, case2, case3, case4])
        suite.update_statistics()
        self.assertEqual(suite.tests, 4)
        self.assertEqual(suite.failures, 1)
        self.assertEqual(suite.errors, 1)
        self.assertEqual(suite.skipped, 1)

class Test_TestCase(unittest.TestCase):
    def test_case_fromstring(self):
        text = """<testcase name="testname">
        <failure message="failure message" type="FailureType"/>
        <system-out>System out</system-out>
        <system-err>System err</system-err>
        </testcase>"""
        case = TestCase.fromstring(text)
        self.assertEqual(case.name, "testname")
        self.assertIsInstance(case.result[0], Failure)
        self.assertEqual(case.system_out, "System out")
        self.assertEqual(case.system_err, "System err")

    def test_xml_multi_results(self):
        text = """<testcase name="testname">
        <failure message="failure message" type="FailureType"/>
        <skipped message="skipped message" type="FailureType"/>
        </testcase>
        """
        case = TestCase.fromstring(text)
        # no assertion raised
        self.assertEqual(case.name, "testname")
        self.assertEqual(len(case.result), 2)

    def test_multi_results(self):
        case = TestCase("testname", "testclassname")
        err = Error("err msg", "err_type")
        fail1 = Failure("fail msg 1", "fail_type")
        fail2 = Failure("fail msg 2", "fail_type")
        fail3 = Failure("fail msg 3", "fail_type")
        fail4 = Failure("fail msg 4", "fail_type")
        case.result += [err]
        self.assertEqual(len(case.result), 1)
        case.result += [fail1]
        self.assertEqual(len(case.result), 2)
        case.result += [fail2]
        self.assertEqual(len(case.result), 3)
        case.result += [fail3]
        self.assertEqual(len(case.result), 4)
        case.result += [fail4]
        self.assertEqual(len(case.result), 5)

    def test_case_attributes(self):
        case = TestCase()
        case.name = "testname"
        case.classname = "testclassname"
        case.time = 15.123
        case.result = [Skipped()]
        case.result[0].text = "woah skipped"
        self.assertEqual(case.name, "testname")
        self.assertEqual(case.classname, "testclassname")
        self.assertEqual(case.time, 15.123)
        self.assertIsInstance(case.result[0], Skipped)
        self.assertEqual(case.result[0].text, "woah skipped")

    def test_case_init_with_attributes(self):
        case = TestCase("testname", "testclassname", 15.123)
        case.result = [Skipped()]
        self.assertEqual(case.name, "testname")
        self.assertEqual(case.classname, "testclassname")
        self.assertEqual(case.time, 15.123)
        self.assertIsInstance(case.result[0], Skipped)

    def test_case_output(self):
        case = TestCase()
        case.system_err = "error message"
        case.system_out = "out message"
        self.assertEqual(case.system_err, "error message")
        self.assertEqual(case.system_out, "out message")
        case.system_err = "error2"
        case.system_out = "out2"
        self.assertEqual(case.system_err, "error2")
        self.assertEqual(case.system_out, "out2")

    def test_update_results(self):
        case = TestCase()
        case.result = [Skipped()]
        case.result = [Failure(), Skipped()]
        self.assertEqual(len(case.result), 2)

    def test_monkypatch(self):
        TestCase.id = Attr("id")
        case = TestCase()
        case.id = "100"
        self.assertEqual(case.id, "100")

    def test_equal(self):
        case = TestCase()
        case.name = "test1"
        case2 = TestCase()
        case2.name = "test1"
        self.assertEqual(case, case2)

    def test_not_equal(self):
        case = TestCase()
        case.name = "test1"
        case2 = TestCase()
        case2.name = "test2"
        self.assertNotEqual(case, case2)

    def test_from_elem(self):
        elem = etree.Element("testcase", name="case1")
        case = TestCase.fromelem(elem)
        self.assertEqual(case.name, "case1")

    def test_from_junit_elem(self):
        case = TestCase()
        case.name = "test1"

        class TestOtherCase(TestCase):
            _tag = "TestOtherCase"
            assertions = Attr()

        other_case = TestOtherCase.fromelem(case)

        self.assertEqual(case.name, other_case.name)
        self.assertRaises(AttributeError, lambda: case.assertions)
        other_case.assertions = 20
        self.assertEqual(other_case.assertions, "20")

    def test_to_string(self):
        case = TestCase()
        case.name = "test1"
        case_str = case.tostring()
        self.assertIn(b"test1", case_str)

    def test_to_nonascii_string(self):
        case = TestCase()
        case.name = "测试1"
        case.result = [Failure("失败", "类型")]
        case_str = case.tostring()
        self.assertIn("测试1", case_str.decode("utf-8"))
        self.assertIn("失败", case_str.decode("utf-8"))
        self.assertIn("类型", case_str.decode("utf-8"))

    def test_system_out(self):
        case = TestCase()
        case.name = "case1"
        self.assertIsNone(case.system_out)
        case.system_out = "output"
        self.assertEqual(case.system_out, "output")

    def test_system_err(self):
        case = TestCase()
        case.name = "case1"
        self.assertIsNone(case.system_err)
        case.system_err = "error"
        self.assertEqual(case.system_err, "error")

    def test_result_eq(self):
        # TODO: Weird, need to think of a better API
        self.assertEqual(Failure("A"), Failure("A"))
        self.assertNotEqual(Skipped("B"), Skipped("A"))
        self.assertNotEqual(Error("C"), Error("B"))

    def test_result_attrs(self):
        res1 = Failure("A")
        # NOTE: lxml gives spaceless result
        self.assertIn(
            res1.tostring(), [b'<failure message="A" />', b'<failure message="A"/>']
        )

    def test_add_child_element(self):
        class CustomElement(Element):
            _tag = "custom"
            foo = Attr()
            bar = Attr()

        testcase = TestCase()
        custom = CustomElement()
        testcase.append(custom)

        self.assertIn(
            testcase.tostring(),
            [b"<testcase><custom /></testcase>", b"<testcase><custom/></testcase>"],
        )

    def test_case_is_skipped(self):
        case = TestCase()
        case.result = [Skipped()]
        self.assertTrue(case.is_skipped)
        self.assertFalse(case.is_passed)

    def test_case_is_passed(self):
        case = TestCase()
        case.result = []
        self.assertFalse(case.is_skipped)
        self.assertTrue(case.is_passed)

    def test_case_is_failed(self):
        case = TestCase()
        case.result = [Failure()]
        self.assertFalse(case.is_skipped)
        self.assertFalse(case.is_passed)


class Test_Properties(unittest.TestCase):
    def test_property_repr1(self):
        prop1 = Property("prop1", "1")
        self.assertEqual(
            prop1.__repr__(), '<Element \'property\' name="prop1" value="1">'
        )

    def test_property_repr2(self):
        prop1 = TestSuite()
        self.assertEqual(prop1.__repr__(), "<Element 'testsuite'>")

    def test_property_eq(self):
        prop1 = Property("prop1", "1")
        prop2 = Property("prop1", "1")
        self.assertEqual(prop1, prop2)

    def test_property_ne(self):
        prop1 = Property("prop1", "1")
        prop2 = Property("prop1", "2")
        self.assertNotEqual(prop1, prop2)

    def test_properties_eq(self):
        prop1 = Property("prop1", "1")
        prop2 = Property("prop1", "2")
        # Note: an attribute can only be used at one place.
        prop3 = deepcopy(prop1)
        prop4 = deepcopy(prop2)
        props1 = Properties()
        props1.add_property(prop1)
        props1.add_property(prop2)
        props2 = Properties()
        props2.add_property(prop3)
        props2.add_property(prop4)
        self.assertEqual(props1, props2)

    def test_properties_ne(self):
        prop1 = Property("prop1", "1")
        prop2 = Property("prop1", "2")
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
        prop1 = Property("prop1", "1")
        prop2 = Property("prop1", "2")
        prop3 = deepcopy(prop1)
        props1 = Properties()
        props1.add_property(prop1)
        props1.add_property(prop2)
        props2 = Properties()
        props2.add_property(prop3)
        self.assertNotEqual(props1, props2)


class Test_Attrs(unittest.TestCase):
    def test_attr(self):
        TestCase.text = Attr("text")
        TestCase.int = IntAttr("int")
        TestCase.float = FloatAttr("float")
        element = TestCase("foo")
        element.text = "foo"
        element.int = 10
        element.float = 8.5
        self.assertEqual(element.text, "foo")
        self.assertEqual(element.int, 10)
        self.assertEqual(element.float, 8.5)


if __name__ == "__main__":
    unittest.main()
