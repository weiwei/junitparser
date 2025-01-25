"""
The flavor based on Jenkins xunit plugin:
https://github.com/jenkinsci/xunit-plugin/blob/xunit-2.3.2/src/main/resources/org/jenkinsci/plugins/xunit/types/model/xsd/junit-10.xsd

According to the internet, the schema is compatible with:

- Pytest (as default, though it also supports a "legacy" xunit1 flavor)
- Erlang/OTP
- Maven Surefire
- CppTest

There may be many others that I'm not aware of.
"""

from typing import List, TypeVar
from . import junitparser

T = TypeVar("T")


class StackTrace(junitparser.System):
    _tag = "stackTrace"


class InterimResult(junitparser.Result):
    """Base class for intermediate (rerun and flaky) test result (in contrast to JUnit FinalResult)."""

    _tag = None

    @property
    def stack_trace(self):
        """<stackTrace>"""
        elem = self.child(StackTrace)
        if elem is not None:
            return elem.text
        return None

    @stack_trace.setter
    def stack_trace(self, value: str):
        """<stackTrace>"""
        trace = self.child(StackTrace)
        if trace is not None:
            trace.text = value
        else:
            trace = StackTrace(value)
            self.append(trace)

    @property
    def system_out(self):
        """<system-out>"""
        elem = self.child(junitparser.SystemOut)
        if elem is not None:
            return elem.text
        return None

    @system_out.setter
    def system_out(self, value: str):
        """<system-out>"""
        out = self.child(junitparser.SystemOut)
        if out is not None:
            out.text = value
        else:
            out = junitparser.SystemOut(value)
            self.append(out)

    @property
    def system_err(self):
        """<system-err>"""
        elem = self.child(junitparser.SystemErr)
        if elem is not None:
            return elem.text
        return None

    @system_err.setter
    def system_err(self, value: str):
        """<system-err>"""
        err = self.child(junitparser.SystemErr)
        if err is not None:
            err.text = value
        else:
            err = junitparser.SystemErr(value)
            self.append(err)


class RerunFailure(InterimResult):
    _tag = "rerunFailure"


class RerunError(InterimResult):
    _tag = "rerunError"


class FlakyFailure(InterimResult):
    _tag = "flakyFailure"


class FlakyError(InterimResult):
    _tag = "flakyError"


class TestCase(junitparser.TestCase):
    group = junitparser.Attr()

    def _rerun_results(self, _type: T) -> List[T]:
        elems = self.iterchildren(_type)
        results = []
        for elem in elems:
            results.append(_type.fromelem(elem))
        return results

    def rerun_failures(self):
        """<rerunFailure>"""
        return self._rerun_results(RerunFailure)

    def rerun_errors(self):
        """<rerunError>"""
        return self._rerun_results(RerunError)

    def flaky_failures(self):
        """<flakyFailure>"""
        return self._rerun_results(FlakyFailure)

    def flaky_errors(self):
        """<flakyError>"""
        return self._rerun_results(FlakyError)

    def add_interim_result(self, result: InterimResult):
        """Append an interim (rerun or flaky) result to the testcase. A testcase can have multiple interim results."""
        self.append(result)


class TestSuite(junitparser.TestSuite):
    """TestSuite for Pytest, with some different attributes."""

    group = junitparser.Attr()
    id = junitparser.Attr()
    package = junitparser.Attr()
    file = junitparser.Attr()
    log = junitparser.Attr()
    url = junitparser.Attr()
    version = junitparser.Attr()

    testcase = TestCase

    @property
    def system_out(self):
        """<system-out>"""
        elem = self.child(junitparser.SystemOut)
        if elem is not None:
            return elem.text
        return None

    @system_out.setter
    def system_out(self, value: str):
        """<system-out>"""
        out = self.child(junitparser.SystemOut)
        if out is not None:
            out.text = value
        else:
            out = junitparser.SystemOut(value)
            self.append(out)

    @property
    def system_err(self):
        """<system-err>"""
        elem = self.child(junitparser.SystemErr)
        if elem is not None:
            return elem.text
        return None

    @system_err.setter
    def system_err(self, value: str):
        """<system-err>"""
        err = self.child(junitparser.SystemErr)
        if err is not None:
            err.text = value
        else:
            err = junitparser.SystemErr(value)
            self.append(err)


class JUnitXml(junitparser.JUnitXml):
    # Pytest and xunit schema doesn't have "skipped" in testsuites
    skipped = None

    testsuite = TestSuite

    def update_statistics(self):
        """Update test count, time, etc."""
        time = 0
        tests = failures = errors = 0
        for suite in self:
            suite.update_statistics()
            tests += suite.tests
            failures += suite.failures
            errors += suite.errors
            time += suite.time
        self.tests = tests
        self.failures = failures
        self.errors = errors
        self.time = round(time, 3)
