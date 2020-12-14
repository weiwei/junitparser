# -*- coding: utf-8 -*-

from __future__ import with_statement
from __future__ import absolute_import
from __future__ import unicode_literals
from junitparser import (
    TestCase,
    TestSuite,
    JUnitXmlError,
    JUnitXml,
)
import pytest


def test_merge_test_count():
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
    assert combined_suites.tests == 4
    assert combined_suites.failures == 1
    assert combined_suites.skipped == 1


def test_merge_same_suite():
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
    assert len(suites) == 1
    assert combined_suites.tests == 4
    assert combined_suites.failures == 1
    assert combined_suites.skipped == 1


def test_fromstring():
    text = """<testsuites><testsuite name="suitename1">
    <testcase name="testname1">
    </testcase></testsuite>
    <testsuite name="suitename2">
    <testcase name="testname2">
    </testcase></testsuite></testsuites>"""
    result = JUnitXml.fromstring(text)
    assert result.time == 0
    assert len(result) == 2


def test_fromstring_no_testsuites():
    text = """<testsuite name="suitename1">
    <testcase name="testname1">
    </testcase></testsuite>"""
    result = JUnitXml.fromstring(text)
    assert result.time == 0
    assert len(result) == 1


def test_fromstring_multiple_fails():
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
    assert result.errors == 1
    assert result.skipped == 1
    suite = list(iter(result))[0]
    cases = list(iter(suite))
    assert len(cases[0].result) == 0
    assert len(cases[1].result) == 2
    text = cases[1].result[1].text
    assert "@pytest.fixture" in text


def test_fromstring_invalid():
    text = """<random name="suitename1"></random>"""
    with pytest.raises(JUnitXmlError):
        JUnitXml.fromstring(text)


def test_add_suite():
    suite1 = TestSuite("suite1")
    suite2 = TestSuite("suite2")
    result = JUnitXml()
    result.add_testsuite(suite1)
    result.add_testsuite(suite2)
    assert len(result) == 2


def test_construct_xml():
    suite1 = TestSuite()
    suite1.name = "suite1"
    case1 = TestCase()
    case1.name = "case1"
    suite1.add_testcase(case1)
    result = JUnitXml()
    result.add_testsuite(suite1)
    assert result._elem.tag == "testsuites"
    suite = result._elem.findall("testsuite")
    assert len(suite) == 1
    assert suite[0].attrib["name"] == "suite1"
    case = suite[0].findall("testcase")
    assert len(case) == 1
    assert case[0].attrib["name"] == "case1"


def test_add():
    result1 = JUnitXml()
    suite1 = TestSuite("suite1")
    result1.add_testsuite(suite1)
    result2 = JUnitXml()
    suite2 = TestSuite("suite2")
    result2.add_testsuite(suite2)
    result3 = result1 + result2
    assert len(result3) == 2


def test_add_same_suite():
    result1 = JUnitXml()
    suite1 = TestSuite()
    result1.add_testsuite(suite1)
    result2 = JUnitXml()
    suite2 = TestSuite()
    result2.add_testsuite(suite2)
    result3 = result1 + result2
    assert len(result3) == 1


def test_iadd():
    result1 = JUnitXml()
    suite1 = TestSuite("suite1")
    result1.add_testsuite(suite1)
    result2 = JUnitXml()
    suite2 = TestSuite("suite2")
    result2.add_testsuite(suite2)
    result1 += result2
    assert len(result1) == 2


def test_iadd_same_suite():
    result1 = JUnitXml()
    suite1 = TestSuite()
    result1.add_testsuite(suite1)
    result2 = JUnitXml()
    suite2 = TestSuite()
    result2.add_testsuite(suite2)
    result1 += result2
    assert len(result1) == 1


def test_add_two_same_suites():
    suite1 = TestSuite()
    case1 = TestCase(name="case1")
    suite1.add_testcase(case1)
    suite2 = TestSuite()
    case2 = TestCase(name="case2")
    suite2.add_testcase(case2)
    suite3 = TestSuite()
    suite2.add_testsuite(suite3)
    result = suite1 + suite2
    assert isinstance(result, TestSuite)
    assert len(list(iter(result))) == 2
    assert len(list(iter(result.testsuites()))) == 1


def test_iadd_two_same_suites():
    suite1 = TestSuite()
    case1 = TestCase(name="case1")
    suite1.add_testcase(case1)
    suite2 = TestSuite()
    case2 = TestCase(name="case2")
    suite2.add_testcase(case2)
    suite3 = TestSuite()
    suite2.add_testsuite(suite3)
    suite1 += suite2
    assert isinstance(suite1, TestSuite)
    assert len(list(iter(suite1))) == 2
    assert len(list(iter(suite1.testsuites()))) == 1


def test_add_two_different_suites():
    suite1 = TestSuite(name="suite1")
    case1 = TestCase(name="case1")
    suite1.add_testcase(case1)
    suite2 = TestSuite(name="suite2")
    case2 = TestCase(name="case2")
    suite2.add_testcase(case2)
    result = suite1 + suite2
    assert isinstance(result, JUnitXml)
    assert len(list(iter(result))) == 2


def test_iadd_two_different_suites():
    suite1 = TestSuite(name="suite1")
    case1 = TestCase(name="case1")
    suite1.add_testcase(case1)
    suite2 = TestSuite(name="suite2")
    case2 = TestCase(name="case2")
    suite2.add_testcase(case2)
    suite1 += suite2
    assert isinstance(suite1, JUnitXml)
    assert len(list(iter(suite1))) == 2


def test_xml_statistics():
    result1 = JUnitXml()
    suite1 = TestSuite()
    result1.add_testsuite(suite1)
    result2 = JUnitXml()
    suite2 = TestSuite()
    result2.add_testsuite(suite2)
    result3 = result1 + result2
    result3.update_statistics()
    assert result3.tests == 0
