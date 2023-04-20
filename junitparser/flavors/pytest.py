import itertools
from .. import junitparser

class JUnitXml(junitparser.JUnitXml):
    # Pytest and xunit schema doesn't have skipped in testsuites
    skipped = None
    def __init__(self, name=None):
        super().__init__(name)
    def __iter__(self):
        return super().iterchildren(TestSuite)
    def __iadd__(self, other):
        if other._elem.tag == "testsuites":
            for suite in other:
                self.add_testsuite(suite)
        elif other._elem.tag == "testsuite":
            suite = TestSuite(name=other.name)
            for case in other:
                suite._add_testcase_no_update_stats(case)
            self.add_testsuite(suite)
            self.update_statistics()
    @classmethod
    def fromroot(cls, root_elem):
        """Constructs Junit objects from an elementTree root element."""
        if root_elem.tag == "testsuites":
            instance = cls()
        elif root_elem.tag == "testsuite":
            instance = TestSuite()
        else:
            raise junitparser.JUnitXmlError("Invalid format.")
        instance._elem = root_elem
        return instance

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


class TestSuite(junitparser.TestSuite):
    """TestSuit for Pytest, with some different attributes."""
    group = junitparser.Attr()
    id = junitparser.Attr()
    package = junitparser.Attr()
    file = junitparser.Attr()
    log = junitparser.Attr()
    url = junitparser.Attr()
    version = junitparser.Attr()

    def __init__(self, name=None):
        super().__init__(self._tag)
        self.name = name
        self.filepath = None

    def __iter__(self):
        return itertools.chain(
            super().iterchildren(TestCase),
            (
                case
                for suite in super().iterchildren(TestSuite)
                for case in suite
            ),
        )
    @property
    def system_out(self):
        """stdout."""
        elem = self.child(junitparser.SystemOut)
        if elem is not None:
            return elem.text
        return None

    @system_out.setter
    def system_out(self, value):
        out = self.child(junitparser.SystemOut)
        if out is not None:
            out.text = value
        else:
            out = junitparser.SystemOut(value)
            self.append(out)

    @property
    def system_err(self):
        """stderr."""
        elem = self.child(junitparser.SystemErr)
        if elem is not None:
            return elem.text
        return None

    @system_err.setter
    def system_err(self, value):
        err = self.child(junitparser.SystemErr)
        if err is not None:
            err.text = value
        else:
            err = junitparser.SystemErr(value)
            self.append(err)

    def testsuites(self):
        """Iterates through all testsuites."""
        for suite in self.iterchildren(TestSuite):
            yield suite

    def remove_testcase(self, testcase):
        """Removes a test case from the suite."""
        for case in self:
            if case == testcase:
                super().remove(case)
                self.update_statistics()

class StackTrace(junitparser.System):
    _tag = "stackTrace"

class RerunType(junitparser.Result):
    _tag = "rerunType"

    @property
    def stack_trace(self):
        """stderr."""
        elem = self.child(StackTrace)
        if elem is not None:
            return elem.text
        return None

    @stack_trace.setter
    def stack_trace(self, value):
        trace = self.child(StackTrace)
        if trace is not None:
            trace.text = value
        else:
            trace = StackTrace(value)
            self.append(trace)

    @property
    def system_out(self):
        """stdout."""
        elem = self.child(junitparser.SystemOut)
        if elem is not None:
            return elem.text
        return None

    @system_out.setter
    def system_out(self, value):
        out = self.child(junitparser.SystemOut)
        if out is not None:
            out.text = value
        else:
            out = junitparser.SystemOut(value)
            self.append(out)

    @property
    def system_err(self):
        """stderr."""
        elem = self.child(junitparser.SystemErr)
        if elem is not None:
            return elem.text
        return None

    @system_err.setter
    def system_err(self, value):
        err = self.child(junitparser.SystemErr)
        if err is not None:
            err.text = value
        else:
            err = junitparser.SystemErr(value)
            self.append(err)

class RerunFailure(RerunType):
    _tag = "rerunFailure"

class RerunError(RerunType):
    _tag = "rerunError"

class FlakyFailure(RerunType):
    _tag = "flakyFailure"

class FlakyError(RerunType):
    _tag = "flakyError"

class TestCase(OrigTestCase):
    group = Attr()

    def _rerun_results(self, _type):
        elems = self.iterchildren(_type)
        results = []
        for elem in elems:
            results.append(_type.fromelem(elem))
        return results

    def rerun_failures(self):
        return self._rerun_results(RerunFailure)

    def rerun_errors(self):
        return self._rerun_results(RerunError)

    def flaky_failures(self):
        return self._rerun_results(FlakyFailure)

    def flaky_errors(self):
        return self._rerun_results(FlakyError)

    def add_rerun_result(self, result):
        self.append(result)


