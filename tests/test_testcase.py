# -*- coding: utf-8 -*-

from __future__ import with_statement
from __future__ import absolute_import
from __future__ import unicode_literals
from junitparser import (
    TestCase,
    CaseSkipped,
    CaseFailure,
    CaseError,
    Attr,
    JUnitXmlError,
    SystemErr,
    SystemOut,
)
from xml.etree import ElementTree as etree
import pytest


def test_case_fromstring():
    text = """<testcase name="testname">
    <failure message="failure message" type="FailureType"/>
    <system-out>System out</system-out>
    <system-err>System err</system-err>
    </testcase>"""
    case = TestCase.fromstring(text)
    assert case.name == "testname"
    assert isinstance(case.result[0], CaseFailure)
    assert isinstance(case.result[1], SystemOut)
    assert isinstance(case.result[2], SystemErr)


def test_case_attributes():
    case = TestCase()
    case.name = "testname"
    case.classname = "testclassname"
    case.time = 15.123
    case.result = [CaseSkipped()]
    case.result[0].text = "woah skipped"
    assert case.name == "testname"
    assert case.classname == "testclassname"
    assert case.time == 15.123
    assert isinstance(case.result[0], CaseSkipped)
    assert case.result[0].text == "woah skipped"


def test_case_init_with_attributes():
    case = TestCase("testname")
    case.classname = "testclassname"
    case.time = 15.123
    case.result = [CaseSkipped()]
    assert case.name == "testname"
    assert case.classname == "testclassname"
    assert case.time == 15.123
    assert isinstance(case.result[0], CaseSkipped)


def test_case_output():
    case = TestCase()
    case.system_err = "error message"
    case.system_out = "out message"
    assert case.system_err == "error message"
    assert case.system_out == "out message"
    case.system_err = "error2"
    case.system_out = "out2"
    assert case.system_err == "error2"
    assert case.system_out == "out2"


def test_update_results():
    case = TestCase()
    case.result = [CaseSkipped()]
    case.result = [CaseFailure(), CaseSkipped()]
    assert len(case.result) == 2


def test_monkypatch():
    TestCase.id = Attr("id")
    case = TestCase()
    case.id = "100"
    assert case.id == "100"


def test_equal():
    case = TestCase()
    case.name = "test1"
    case2 = TestCase()
    case2.name = "test1"
    assert case == case2


def test_not_equal():
    case = TestCase()
    case.name = "test1"
    case2 = TestCase()
    case2.name = "test2"
    assert case != case2


def test_from_elem():
    elem = etree.Element("testcase", name="case1")
    case = TestCase.fromelem(elem)
    assert case.name == "case1"


def test_from_junit_elem():
    case = TestCase()
    case.name = "test1"

    class TestOtherCase(TestCase):
        _tag = "TestOtherCase"
        assertions = Attr()

    other_case = TestOtherCase.fromelem(case)

    assert case.name == other_case.name
    with pytest.raises(AttributeError):
        case.custom_attr
    other_case.assertions = 20
    assert other_case.assertions == "20"


def test_to_string():
    case = TestCase()
    case.name = "test1"
    case_str = case.tostring()
    assert b"test1" in case_str


def test_to_nonascii_string():
    case = TestCase()
    case.name = "测试1"
    case.result = [CaseFailure("失败", "类型")]
    case_str = case.tostring()
    assert "测试1" in case_str.decode("utf-8")
    assert "失败" in case_str.decode("utf-8")
    assert "类型" in case_str.decode("utf-8")


def test_system_out():
    case = TestCase()
    case.name = "case1"
    sys_out = SystemOut()
    sys_out.text = "output"
    case.result = [sys_out]
    assert case.result[0].text == "output"


def test_system_err():
    case = TestCase()
    case.name = "case1"
    sys_err = SystemErr()
    sys_err.text = "output"
    case.result = [sys_err]
    assert case.result[0].text == "output"


def test_result_eq():
    assert CaseFailure("A") == CaseFailure("A")
    assert CaseSkipped("B") != CaseSkipped("A")
    assert CaseError("C") != CaseError("B")


def test_result_attrs():
    res1 = CaseFailure("A")
    # NOTE: lxml gives spaceless result
    assert res1.tostring() in [b'<failure message="A" />', b'<failure message="A"/>']
