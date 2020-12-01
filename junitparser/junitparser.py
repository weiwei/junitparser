"""
junitparser is a JUnit/xUnit Result XML Parser. Use it to parse and manipulate
existing Result XML files, or create new JUnit/xUnit result XMLs from scratch.

:copyright: (c) 2019 by Joel Wang.
:license: Apache2, see LICENSE for more details.
"""

from __future__ import with_statement
from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import object
from io import open
from junitparser.elements import POSSIBLE_RESULTS, Properties, SystemErr, SystemOut
from junitparser.base import Attr, Element, FloatAttr, IntAttr, JUnitXmlError


try:
    import itertools.izip as zip
except ImportError:
    pass

try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree

from copy import deepcopy

try:
    type(unicode)
except NameError:
    unicode = str


def write_xml(obj, filepath=None, pretty=False):
    tree = etree.ElementTree(obj._elem)
    if filepath is None:
        filepath = obj.filepath
    if filepath is None:
        raise JUnitXmlError("Missing filepath argument.")

    if pretty:
        from xml.dom.minidom import parseString

        text = etree.tostring(obj._elem)
        xml = parseString(text) # nosec
        with open(filepath, "wb") as xmlfile:
            xmlfile.write(xml.toprettyxml(encoding="utf-8"))
    else:
        tree.write(filepath, encoding="utf-8", xml_declaration=True)



class JUnitXml(Element):
    """The JUnitXml root object.

    It may contains a :class:`TestSuites` or a :class:`TestSuite`.

    Attributes:
        name: test suite name if it only contains one test suite
        time: time consumed by the test suites
        tests: total number of tests
        failures: number of failed cases
        errors: number of cases with errors
        skipped: number of skipped cases
    """

    _tag = "testsuites"
    name = Attr()
    time = FloatAttr()
    tests = IntAttr()
    failures = IntAttr()
    errors = IntAttr()
    skipped = IntAttr()
    disabled = Attr()

    def __init__(self, name=None):
        super(JUnitXml, self).__init__(self._tag)
        self.filepath = None
        self.name = name

    def __iter__(self):
        return super(JUnitXml, self).iterchildren(TestSuite)

    def __len__(self):
        return len(list(self.__iter__()))

    def __add__(self, other):
        result = JUnitXml()
        for suite in self:
            result.add_testsuite(suite)
        for suite in other:
            result.add_testsuite(suite)
        return result

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

        return self

    def add_testsuite(self, suite):
        """Add a test suite."""
        for existing_suite in self:
            if existing_suite == suite:
                for case in suite:
                    existing_suite._add_testcase_no_update_stats(case)
                return
        self.append(suite)

    def update_statistics(self):
        """Update test count, time, etc."""
        time = 0
        tests = failures = errors = skipped = 0
        for suite in self:
            suite.update_statistics()
            tests += suite.tests
            failures += suite.failures
            errors += suite.errors
            skipped += suite.skipped
            time += suite.time
        self.tests = tests
        self.failures = failures
        self.errors = errors
        self.skipped = skipped
        self.time = time

    @classmethod
    def fromstring(cls, text):
        """Construct Junit objects from a XML string."""
        root_elem = etree.fromstring(text) # nosec
        if root_elem.tag == "testsuites":
            instance = cls()
        elif root_elem.tag == "testsuite":
            instance = TestSuite()
        else:
            raise JUnitXmlError("Invalid format.")
        instance._elem = root_elem
        return instance

    @classmethod
    def fromfile(cls, filepath, parse_func=None):
        """Initiate the object from a report file."""
        if parse_func:
            tree = parse_func(filepath)
        else:
            tree = etree.parse(filepath) # nosec
        root_elem = tree.getroot()
        if root_elem.tag == "testsuites":
            instance = cls()
        elif root_elem.tag == "testsuite":
            instance = TestSuite()
        else:
            raise JUnitXmlError("Invalid format.")
        instance._elem = root_elem
        instance.filepath = filepath
        return instance

    def write(self, filepath=None, pretty=False):
        """Write the object into a junit xml file.

        If `file_path` is not specified, it will write to the original file.
        If `pretty` is True, the result file will be more human friendly.
        """
        write_xml(self, filepath=filepath, pretty=pretty)


class TestSuites(Element):
    _tag = "testsuites"
    name = Attr()
    time = FloatAttr()
    tests = IntAttr()
    failures = IntAttr()
    disabled = IntAttr()
    errors = IntAttr()

class TestSuite(Element):
    """The <testsuite> object.

    Attributes:
        name: test suite name
        hostname: name of the test machine
        time: time concumed by the test suite
        timestamp: when the test was run
        tests: total number of tests
        failures: number of failed tests
        errors: number of cases with errors
        skipped: number of skipped cases
    """

    _tag = "testsuite"
    name = Attr() # Req
    hostname = Attr()
    time = FloatAttr()
    timestamp = Attr()
    tests = IntAttr() # Req
    failures = IntAttr() # Req
    errors = IntAttr() # Req
    skipped = IntAttr()
    group = Attr()
    id = Attr()
    package = Attr()
    file = Attr()
    log = Attr()
    url = Attr()
    version = Attr()

    def __init__(self, name=None):
        super(TestSuite, self).__init__(self._tag)
        self.name = name
        self.filepath = None

    def __iter__(self):
        return super(TestSuite, self).iterchildren(TestCase)

    def __len__(self):
        return len(list(self.__iter__()))

    def __eq__(self, other):
        def props_eq(props1, props2):
            props1 = list(props1)
            props2 = list(props2)
            if len(props1) != len(props2):
                return False
            props1.sort(key=lambda x: x.name)
            props2.sort(key=lambda x: x.name)
            zipped = zip(props1, props2)
            return all([x == y for x, y in zipped])

        return (
            self.name == other.name
            and self.hostname == other.hostname
            and self.timestamp == other.timestamp
        ) and props_eq(self.properties(), other.properties())

    def __add__(self, other):
        if self == other:
            # Merge the two suites
            result = deepcopy(self)
            for case in other:
                result._add_testcase_no_update_stats(case)
            for suite in other.testsuites():
                result.add_testsuite(suite)
            result.update_statistics()
        else:
            # Create a new test result containing two suites
            result = JUnitXml()
            result.add_testsuite(self)
            result.add_testsuite(other)
        return result

    def __iadd__(self, other):
        if self == other:
            for case in other:
                self._add_testcase_no_update_stats(case)
            for suite in other.testsuites():
                self.add_testsuite(suite)
            self.update_statistics()
            return self

        result = JUnitXml()
        result.filepath = self.filepath
        result.add_testsuite(self)
        result.add_testsuite(other)
        return result

    def remove_testcase(self, testcase):
        """Removes a test case from the suite."""
        for case in self:
            if case == testcase:
                super(TestSuite, self).remove(case)
                self.update_statistics()

    def update_statistics(self):
        """Updates test count and test time."""
        tests = errors = failures = skipped = 0
        time = 0
        for case in self:
            tests += 1
            if case.time is not None:
                time += case.time
            for entry in case.result:
                if isinstance(entry, Failure):
                    failures += 1
                elif isinstance(entry, Error):
                    errors += 1
                elif isinstance(entry, Skipped):
                    skipped += 1
        self.tests = tests
        self.errors = errors
        self.failures = failures
        self.skipped = skipped
        self.time = time

    def add_property(self, name, value):
        """Adds a property to the testsuite.

        See :class:`Property` and :class:`Properties`
        """

        props = self.child(Properties)
        if props is None:
            props = Properties()
            self.append(props)
        prop = Property(name, value)
        props.add_property(prop)

    def add_testcase(self, testcase):
        """Adds a testcase to the suite."""
        self.append(testcase)
        self.update_statistics()

    def _add_testcase_no_update_stats(self, testcase):
        """
        Adds a testcase to the suite (without updating stats).
        For internal use only to avoid quadratic behaviour in merge.
        """
        self.append(testcase)

    def add_testsuite(self, suite):
        """Adds a testsuite inside current testsuite."""
        self.append(suite)

    def properties(self):
        """Iterates through all properties."""
        props = self.child(Properties)
        if props is None:
            return
        for prop in props:
            yield prop

    def remove_property(self, property_):
        """Removes a property."""
        props = self.child(Properties)
        if props is None:
            return
        for prop in props:
            if prop == property_:
                props.remove(property_)

    def testsuites(self):
        """Iterates through all testsuites."""
        for suite in self.iterchildren(TestSuite):
            yield suite

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


    def write(self, filepath=None, pretty=False):
        write_xml(self, filepath=filepath, pretty=pretty)


class TestCase(Element):
    """Object to store a testcase and its result.

    Attributes:
        name: case name
        classname: the parent class of the case
        time: how much time is consumed by the test

    Properties:
        result: Failure, Skipped, or Error
        system_out: stdout
        system_err: stderr
    """

    _tag = "testcase"
    name = Attr()
    classname = Attr()
    time = FloatAttr()
    assertions = Attr()
    status = Attr()

    def __init__(self, name):
        super(TestCase, self).__init__(self._tag)
        self.name = name

    def __hash__(self):
        return super(TestCase, self).__hash__()

    def __iter__(self):
        all_types = set.union(POSSIBLE_RESULTS, {SystemOut}, {SystemErr})
        for elem in self._elem.iter():
            for entry_type in all_types:
                if elem.tag == entry_type._tag:
                    yield entry_type.fromelem(elem)

    def __eq__(self, other):
        # TODO: May not work correctly if unreliable hash method is used.
        return hash(self) == hash(other)

    @property
    def result(self):
        """A list of Failure, Skipped, or Error objects."""
        results = []
        for entry in self:
            if isinstance(entry, tuple(POSSIBLE_RESULTS)):
                results.append(entry)

        return results

    @result.setter
    def result(self, value):
        # First remove all existing results
        for entry in self:
            if any(isinstance(entry, r) for r in POSSIBLE_RESULTS ):
                self.remove(entry)
        for entry in value:
            if any(isinstance(entry, r) for r in POSSIBLE_RESULTS ):
                self.append(entry)
