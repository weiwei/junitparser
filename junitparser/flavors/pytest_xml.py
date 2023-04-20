"""
>>> xml = PytestXml();
>>> xml.

"""

from junitparser.junitparser import JUnitXml, JUnitXmlError, TestSuite, Attr, IntAttr, \
    SystemOut, SystemErr


class PytestXml(JUnitXml):
    # Pytest and xunit schema doesn't have skipped in testsuites
    skipped = None
    def __init__(self, name=None):
        super().__init__(name)
    def __iter__(self):
        return super(JUnitXml, self).iterchildren(PyTestSuite)
    def __iadd__(self, other):
        if other._elem.tag == "testsuites":
            for suite in other:
                self.add_testsuite(suite)
        elif other._elem.tag == "testsuite":
            suite = PyTestSuite(name=other.name)
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
            instance = PyTestSuite()
        else:
            raise JUnitXmlError("Invalid format.")
        instance._elem = root_elem
        return instance

        return self
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


class PyTestSuite(TestSuite):
    group = Attr()
    id = Attr()
    package = Attr()
    file = Attr()
    log = Attr()
    url = Attr()
    version = Attr()

    def __init__(self, name=None):
        super(PyTestSuite, self).__init__(self._tag)
        self.name = name
        self.filepath = None

    def __iter__(self):
        return itertools.chain(
            super(PyTestSuite, self).iterchildren(TestCase),
            (
                case
                for suite in super(PyTestSuite, self).iterchildren(PyTestSuite)
                for case in suite
            ),
        )
    @property
    def system_out(self):
        """stdout."""
        elem = self.child(SystemOut)
        if elem is not None:
            return elem.text
        return None

    @system_out.setter
    def system_out(self, value):
        out = self.child(SystemOut)
        if out is not None:
            out.text = value
        else:
            out = SystemOut(value)
            self.append(out)

    @property
    def system_err(self):
        """stderr."""
        elem = self.child(SystemErr)
        if elem is not None:
            return elem.text
        return None

    @system_err.setter
    def system_err(self, value):
        err = self.child(SystemErr)
        if err is not None:
            err.text = value
        else:
            err = SystemErr(value)
            self.append(err)

    def testsuites(self):
        """Iterates through all testsuites."""
        for suite in self.iterchildren(PyTestSuite):
            yield suite

    def remove_testcase(self, testcase):
        """Removes a test case from the suite."""
        for case in self:
            if case == testcase:
                super(PyTestSuite, self).remove(case)
                self.update_statistics()
