# -*- coding: utf-8 -*-

from __future__ import with_statement
from __future__ import absolute_import
from __future__ import unicode_literals
from copy import deepcopy
import pytest

from junitparser import (
    TestCase,
    TestSuite,
    Attr,
    Property,
    Properties,
    IntAttr,
    FloatAttr,
    SystemErr,
    CaseError,
    CaseFailure,
    FlakyError,
    FlakyFailure,
    RerunError,
    RerunFailure,
    CaseSkipped,
    SystemOut,
)


def test_property_repr1():
    prop1 = Property("prop1", "1")
    assert prop1.__repr__() == '<Element \'property\' name="prop1" value="1">'


def test_property_repr2():
    prop1 = TestSuite()
    assert prop1.__repr__() == "<Element 'testsuite'>"


def test_property_eq():
    prop1 = Property("prop1", "1")
    prop2 = Property("prop1", "1")
    assert prop1 == prop2


def test_property_ne():
    prop1 = Property("prop1", "1")
    prop2 = Property("prop1", "2")
    assert prop1 != prop2


def test_properties_eq():
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
    assert props1 == props2


def test_properties_ne():
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
    assert props1 != props2


def test_properties_ne2():
    prop1 = Property("prop1", "1")
    prop2 = Property("prop1", "2")
    prop3 = deepcopy(prop1)
    props1 = Properties()
    props1.add_property(prop1)
    props1.add_property(prop2)
    props2 = Properties()
    props2.add_property(prop3)
    assert props1 != props2


def test_attr():
    TestCase.text = Attr("text")
    TestCase.int = IntAttr("int")
    TestCase.float = FloatAttr("float")
    element = TestCase("foo")
    element.text = "foo"
    element.int = 10
    element.float = 8.5
    assert element.text == "foo"
    assert element.int == 10
    assert element.float == 8.5


@pytest.mark.parametrize(
    "fail_cls",
    [
        CaseSkipped,
        CaseFailure,
        CaseError,
        RerunFailure,
        RerunError,
        FlakyFailure,
        FlakyError,
    ],
)
def test_result_eq(fail_cls):
    fail1 = fail_cls()
    fail2 = fail_cls()
    fail3 = fail_cls("bar")
    assert fail1 == fail2
    assert fail1 != fail3


@pytest.mark.parametrize("sys_cls", [SystemOut, SystemErr])
@pytest.mark.skip()
def test_result_eq(sys_cls):
    res1 = sys_cls("foo")
    res2 = sys_cls("foo")
    res3 = sys_cls("bar")
    assert res1 == res2
    assert res1 != res3
