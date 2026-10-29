import io
import threading

import pytest

from src.junitparser import JUnitXml, TestCase, TestSuite
from src.junitparser import xunit2


PARALLEL = (
    '<testsuites><testsuite name="parallel" time="10">'
    '<testcase name="a" time="8"/><testcase name="b" time="9"/>'
    "</testsuite></testsuites>"
)


@pytest.mark.parametrize(
    "attribute,value",
    [("tests", 2), ("errors", 0), ("failures", 0), ("skipped", 0), ("time", 17)],
)
def test_missing_root_statistics_preserve_reported_time(attribute, value):
    report = JUnitXml.fromstring(PARALLEL)
    suite = next(iter(report))
    assert getattr(report, attribute) == value
    assert suite.time == 10
    output = io.BytesIO()
    report.write(output)
    assert next(iter(JUnitXml.fromfile(io.BytesIO(output.getvalue())))).time == 10
    report.update_statistics()
    assert suite.time == 17


@pytest.mark.parametrize(
    "attribute,value", [("tests", 2), ("errors", 0), ("failures", 0), ("skipped", 0)]
)
def test_missing_suite_statistics_preserve_reported_time(attribute, value):
    suite = next(iter(JUnitXml.fromstring(PARALLEL)))
    assert getattr(suite, attribute) == value
    assert suite.time == 10


def test_missing_time_preserves_explicit_counts():
    suite = TestSuite.fromstring(
        '<testsuite tests="42"><testcase time="8"/></testsuite>'
    )
    assert suite.time == 8
    assert suite.tests == 42
    suite.update_statistics()
    assert suite.tests == 1


def test_zero_is_not_missing_and_mutations_still_recompute():
    suite = TestSuite.fromstring(
        '<testsuite tests="0" time="0"><testcase time="8"/></testsuite>'
    )
    assert suite.failures == 0
    assert suite.tests == 0
    assert suite.time == 0
    suite.add_testcase(TestCase("extra", time=3))
    assert suite.time == 11
    assert suite.tests == 2


def test_lazy_statistics_do_not_copy_non_xml_subclass_state():
    class LockedSuite(TestSuite):
        def __init__(self):
            super().__init__()
            self.lock = threading.Lock()

    suite = LockedSuite.fromstring(
        '<testsuite time="10"><testcase time="8"/></testsuite>'
    )
    assert suite.tests == 1
    assert suite.time == 10


def test_missing_standard_statistics_are_cached_together():
    class CountingSuite(TestSuite):
        calls = 0

        def update_statistics(self):
            type(self).calls += 1
            super().update_statistics()

    suite = CountingSuite.fromstring(
        '<testsuite time="10"><testcase time="8"/></testsuite>'
    )
    assert (suite.tests, suite.errors, suite.failures, suite.skipped) == (1, 0, 0, 0)
    assert CountingSuite.calls == 1
    assert suite.time == 10


def test_nested_xunit2_preserves_annotations():
    report = xunit2.JUnitXml.fromstring(
        '<testsuites><testsuite time="10"><testsuite time="6"><testcase time="8"/><testcase time="9"/></testsuite></testsuite></testsuites>'
    )
    outer = next(iter(report))
    inner = next(outer.testsuites())
    assert report.tests == 2
    assert report.time == 17
    assert report.skipped is None
    assert "skipped" not in report._elem.attrib
    assert outer.time == 10
    assert inner.time == 6


@pytest.mark.parametrize("descriptor,value", [("IntAttr", 7), ("FloatAttr", 7.5)])
def test_custom_computed_numeric_attribute(descriptor, value):
    from src.junitparser import FloatAttr, IntAttr

    descriptor_type = {"IntAttr": IntAttr, "FloatAttr": FloatAttr}[descriptor]

    class CustomSuite(TestSuite):
        custom = descriptor_type()
        absent = descriptor_type()

        def update_statistics(self):
            super().update_statistics()
            self.custom = value

    suite = CustomSuite.fromstring(
        '<testsuite time="10"><testcase time="8"/></testsuite>'
    )
    assert suite.custom == value
    assert suite.absent is None
    assert suite.time == 10


def test_computed_custom_metadata_is_cached_with_statistics():
    from src.junitparser import Attr

    class CustomSuite(TestSuite):
        label = Attr()
        calls = 0

        def update_statistics(self):
            type(self).calls += 1
            super().update_statistics()
            self.label = "calculated"

    suite = CustomSuite.fromstring(
        '<testsuite time="10"><testcase time="8"/></testsuite>'
    )
    assert suite.tests == 1
    assert suite.label == "calculated"
    assert suite.errors == 0
    assert CustomSuite.calls == 1
    assert suite.time == 10
    explicit = CustomSuite.fromstring(
        '<testsuite label="supplied" time="10"><testcase time="8"/></testsuite>'
    )
    assert explicit.tests == 1
    assert explicit.label == "supplied"
