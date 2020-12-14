# -*- coding: utf-8 -*-

from __future__ import with_statement
from __future__ import absolute_import
from __future__ import unicode_literals
from copy import deepcopy
from junitparser import (
    TestCase,
    TestSuite,
    CaseSkipped,
    CaseFailure,
    CaseError,
    JUnitXml,
    Property,
    FloatAttr
)
import pytest


def test_fromstring():
    text = """<testsuite name="suitename" time="1.32">
    <testcase name="testname">
    <failure message="failure message" type="FailureType"/>
    </testcase></testsuite>"""
    suite = TestSuite.fromstring(text)
    assert suite.time == 1.32
    suite.update_statistics()
    assert suite.name == "suitename"
    assert suite.tests == 1


def test_props_fromstring():
    text = """<testsuite name="suitename">
    <properties><property name="name1" value="value1"/></properties>
    </testsuite>"""
    suite = TestSuite.fromstring(text)
    for prop in suite.properties():
        assert prop.name == "name1"
        assert prop.value == "value1"


def test_quoted_attr():
    text = """<testsuite name="suitename with &quot;quotes&quot;">
    </testsuite>"""
    suite = TestSuite.fromstring(text)
    assert suite.name == "suitename with &quot;quotes&quot;"


def test_custom_float_attr():
    TestSuite.foo = FloatAttr("foo")
    suite = TestSuite()
    assert suite.foo == None


def test_combining_testsuite_should_keep_name():
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

    assert [s.name for s in combined_suites] == ["suitename1", "suitename2"]


def test_len():
    text = """<testsuite name="suitename"><testcase name="testname"/>
    <testcase name="testname2"/>
    </testsuite>"""
    suite = TestSuite.fromstring(text)
    assert len(suite) == 2


def test_add_case():
    suite = TestSuite()
    assert suite.tests == 0
    case1 = TestCase()
    case2 = TestCase()
    case2.result = [CaseFailure()]
    case3 = TestCase()
    case3.result = [CaseError()]
    case4 = TestCase()
    case4.result = [CaseSkipped()]
    suite.add_testcase(case1)
    suite.add_testcase(case2)
    suite.add_testcase(case3)
    suite.add_testcase(case4)
    suite.update_statistics()
    assert suite.tests == 4
    assert suite.failures == 1
    assert suite.errors == 1
    assert suite.skipped == 1


def test_case_count():
    suite = TestSuite()
    case1 = TestCase()
    suite.add_testcase(case1)
    assert suite.tests == 1
    assert suite.failures == 0


def test_add_property():
    suite = TestSuite()
    suite.add_property("name1", "value1")
    res_prop = next(suite.properties())
    assert res_prop.name == "name1"
    assert res_prop.value == "value1"


def test_remove_case():
    suite = TestSuite()
    case1 = TestCase()
    case1.name = "test1"
    case2 = TestCase()
    case2.name = "test2"
    suite.add_testcase(case1)
    suite.add_testcase(case2)
    suite.remove_testcase(case1)
    assert len(suite) == 1


def test_remove_property():
    suite = TestSuite()
    suite.add_property("name1", "value1")
    suite.add_property("name2", "value2")
    suite.add_property("name3", "value3")
    for prop in suite.properties():
        if prop.name == "name2":
            suite.remove_property(prop)
    assert len(list(suite.properties())) == 2


def test_remove_property_from_none():
    suite = TestSuite()
    suite.remove_property(Property("key", "value"))
    # Nothing should happen


def test_suite_in_suite():
    suite = TestSuite("parent")
    childsuite = TestSuite("child")
    suite.add_testsuite(childsuite)
    assert len(list(suite.testsuites())) == 1


def test_case_time():
    suite = TestSuite()
    case1 = TestCase()
    case1.name = "test1"
    case1.time = 15
    suite.add_testcase(case1)
    suite.update_statistics()
    assert suite.time == 15


def test_wrong_attr_type():
    suite = TestSuite()
    with pytest.raises(TypeError):
        suite.time = "abc"
    with pytest.raises(TypeError):
        suite.tests = 10.5


def test_suite_eq():
    suite = TestSuite()
    suite.add_property("name1", "value1")
    suite2 = deepcopy(suite)
    assert suite == suite2


def test_suite_ne():
    suite = TestSuite()
    suite.add_property("name1", "value1")
    suite2 = deepcopy(suite)
    suite2.add_property("name2", "value2")
    assert suite != suite2


def test_system_out():
    suite = TestSuite()
    suite.system_out = "out"
    assert suite.system_out == "out"
    suite.system_out = "out2"
    assert suite.system_out == "out2"


def test_system_err():
    suite = TestSuite()
    suite.system_err = "err"
    assert suite.system_err == "err"
    suite.system_err = "err2"
    assert suite.system_err == "err2"
