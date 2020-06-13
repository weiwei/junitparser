"""
junitparser is a JUnit/xUnit Result XML Parser. Use it to parse and manipulate
existing Result XML files, or create new JUnit/xUnit result XMLs from scratch.

:copyright: (c) 2019 by Joel Wang.
:license: Apache2, see LICENSE for more details.
"""

from __future__ import with_statement
from __future__ import absolute_import
from __future__ import unicode_literals
from future.utils import with_metaclass
from builtins import object
from io import open
try:
    from html import escape  # python 3.x
except ImportError:
    from cgi import escape  # python 2.x

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
        xml = parseString(text)
        with open(filepath, "wb") as xmlfile:
            xmlfile.write(xml.toprettyxml(encoding="utf-8"))
    else:
        tree.write(filepath, encoding="utf-8", xml_declaration=True)


class JUnitXmlError(Exception):
    """Exception for JUnit XML related errors."""


class Attr(object):
    """An attribute for an XML element.

    By default they are all string values. To support different value types,
    inherit this class and define your own methods.

    Also see: :class:`InitAttr`, :class:`FloatAttr`.
    """

    def __init__(self, name=None):
        self.name = name

    def __get__(self, instance, cls):
        """Gets value from attribute, return None if attribute doesn't exist."""
        value = instance._elem.attrib.get(self.name)
        if value is not None:
            return escape(value)
        return value

    def __set__(self, instance, value):
        """Sets XML element attribute."""
        if value is not None:
            instance._elem.attrib[self.name] = unicode(value)


class IntAttr(Attr):
    """An integer attribute for an XML element.

    This class is used internally for counting test cases, but you could use
    it for any specific purpose.
    """

    def __get__(self, instance, cls):
        result = super(IntAttr, self).__get__(instance, cls)
        if result is None and (
            isinstance(instance, JUnitXml) or isinstance(instance, TestSuite)
        ):
            instance.update_statistics()
            result = super(IntAttr, self).__get__(instance, cls)
        return int(result) if result else None

    def __set__(self, instance, value):
        if not isinstance(value, int):
            raise TypeError("Expected integer value.")
        super(IntAttr, self).__set__(instance, value)


class FloatAttr(Attr):
    """A float attribute for an XML element.

    This class is used internally for counting test durations, but you could
    use it for any specific purpose.
    """

    def __get__(self, instance, cls):
        result = super(FloatAttr, self).__get__(instance, cls)
        if result is None and (
            isinstance(instance, JUnitXml) or isinstance(instance, TestSuite)
        ):
            instance.update_statistics()
            result = super(FloatAttr, self).__get__(instance, cls)
        return float(result) if result else None

    def __set__(self, instance, value):
        if not (isinstance(value, float) or isinstance(value, int)):
            raise TypeError("Expected float value.")
        super(FloatAttr, self).__set__(instance, value)


def attributed(cls):
    """Decorator to read XML element attribute name from class attribute."""
    for key, value in vars(cls).items():
        if isinstance(value, Attr):
            value.name = key
    return cls


class junitxml(type):
    """Metaclass to decorate the xml class"""

    def __new__(meta, name, bases, methods):
        cls = super(junitxml, meta).__new__(meta, name, bases, methods)
        cls = attributed(cls)
        return cls


class Element(with_metaclass(junitxml, object)):
    """Base class for all Junit XML elements."""

    def __init__(self, name=None):
        self._elem = etree.Element(name)

    def __hash__(self):
        return hash(etree.tostring(self._elem))

    def __repr__(self):
        tag = self._elem.tag
        keys = sorted(self._elem.attrib.keys())
        if keys:
            attrs_str = " ".join(
                ['%s="%s"' % (key, self._elem.attrib[key]) for key in keys]
            )
            return """<Element '%s' %s>""" % (tag, attrs_str)
        else:
            return """<Element '%s'>""" % tag

    def append(self, sub_elem):
        """Adds the element subelement to the end of this elements internal
        list of subelements.
        """
        self._elem.append(sub_elem._elem)

    @classmethod
    def fromstring(cls, text):
        """Construct Junit objects from a XML string."""
        instance = cls()
        instance._elem = etree.fromstring(text)
        return instance

    @classmethod
    def fromelem(cls, elem):
        """Constructs Junit objects from an elementTree element."""
        if elem is None:
            return
        instance = cls()
        if isinstance(elem, Element):
            instance._elem = elem._elem
        else:
            instance._elem = elem
        return instance

    def iterchildren(self, Child):
        """Iterate through specified Child type elements."""
        elems = self._elem.iterfind(Child._tag)
        for elem in elems:
            yield Child.fromelem(elem)

    def child(self, Child):
        """Find a single child of specified Child type."""
        elem = self._elem.find(Child._tag)
        return Child.fromelem(elem)

    def remove(self, sub_elem):
        """Remove a sub element."""
        for elem in self._elem.iterfind(sub_elem._tag):
            child = sub_elem.__class__.fromelem(elem)
            if child == sub_elem:
                self._elem.remove(child._elem)

    def tostring(self):
        """Converts element to XML string."""
        return etree.tostring(self._elem, encoding="utf-8")


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
        """Add a test suite"""
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
    def fromfile(cls, filepath):
        """Initiate the object from a report file."""
        tree = etree.parse(filepath)
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
    name = Attr()
    hostname = Attr()
    time = FloatAttr()
    timestamp = Attr()
    tests = IntAttr()
    failures = IntAttr()
    errors = IntAttr()
    skipped = IntAttr()

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
        else:
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
            if isinstance(case.result, Failure):
                failures += 1
            elif isinstance(case.result, Error):
                errors += 1
            elif isinstance(case.result, Skipped):
                skipped += 1
            if case.time is not None:
                time += case.time
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

    def write(self, filepath=None, pretty=False):
        write_xml(self, filepath=filepath, pretty=pretty)


class Properties(Element):
    """A list of properties inside a test suite.

    See :class:`Property`
    """

    _tag = "properties"

    def __init__(self):
        super(Properties, self).__init__(self._tag)

    def add_property(self, property_):
        self.append(property_)

    def __iter__(self):
        return super(Properties, self).iterchildren(Property)

    def __eq__(self, other):
        p1 = list(self)
        p2 = list(other)
        p1.sort()
        p2.sort()
        if len(p1) != len(p2):
            return False
        for e1, e2 in zip(p1, p2):
            if e1 != e2:
                return False
        return True


class Property(Element):
    """A key/value pare that's stored in the test suite.

    Use it to store anything you find interesting or useful.

    Attributes:
        name: the property name
        value: the property value
    """
    _tag = "property"
    name = Attr()
    value = Attr()

    def __init__(self, name=None, value=None):
        super(Property, self).__init__(self._tag)
        self.name = name
        self.value = value

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        """Supports sort() for properties."""
        return self.name > other.name


class Result(Element):
    """Base class for test result.

    Attributes:
        message: result as message string
        type: message type
    """

    _tag = None
    message = Attr()
    type = Attr()

    def __init__(self, message=None, type_=None):
        super(Result, self).__init__(self._tag)
        if message:
            self.message = message
        if type_:
            self.type = type_

    def __eq__(self, other):
        return (
            self._tag == other._tag
            and self.type == other.type
            and self.message == other.message
        )


class Skipped(Result):
    """Test result when the case is skipped."""
    _tag = "skipped"

    def __eq__(self, other):
        return super(Skipped, self).__eq__(other)


class Failure(Result):
    """Test result when the case failed."""
    _tag = "failure"

    def __eq__(self, other):
        return super(Failure, self).__eq__(other)


class Error(Result):
    """Test result when the case has errors during execution."""
    _tag = "error"

    def __eq__(self, other):
        return super(Error, self).__eq__(other)


POSSIBLE_RESULTS = {Failure, Error, Skipped}


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

    def __init__(self, name=None):
        super(TestCase, self).__init__(self._tag)
        self.name = name

    def __hash__(self):
        return super(TestCase, self).__hash__()

    def __eq__(self, other):
        # TODO: May not work correctly if unreliable hash method is used.
        return hash(self) == hash(other)

    @property
    def result(self):
        """One of the Failure, Skipped, or Error objects."""
        results = []
        for res in POSSIBLE_RESULTS:
            result = self.child(res)
            if result is not None:
                results.append(result)
        if len(results) > 1:
            raise JUnitXmlError("Only one result allowed per test case.")
        elif len(results) == 0:
            return None
        else:
            return results[0]

    @result.setter
    def result(self, value):
        # First remove all existing results
        for res in POSSIBLE_RESULTS:
            result = self.child(res)
            if result is not None:
                self.remove(result)
        # Then add current result
        if isinstance(value, Skipped) or isinstance(value, Failure) or isinstance(value, Error):
            self.append(value)

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


class System(Element):
    """Parent class for SystemOut and SystemErr.

    Attributes:
        text: the output message
    """
    _tag = ""

    def __init__(self, content=None):
        super(System, self).__init__(self._tag)
        self.text = content

    @property
    def text(self):
        return self._elem.text

    @text.setter
    def text(self, value):
        self._elem.text = value


class SystemOut(System):
    _tag = "system-out"


class SystemErr(System):
    _tag = "system-err"
