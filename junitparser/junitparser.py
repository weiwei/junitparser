"""
junitparser is a JUnit/xUnit Result XML Parser. Use it to parse and manipulate
existing Result XML files, or create new JUnit/xUnit result XMLs from scratch.

:copyright: (c) 2018 by Joel Wang.
:license: Apache2, see LICENSE for more details.
"""

from __future__ import with_statement
from __future__ import absolute_import
from __future__ import unicode_literals
from future.utils import with_metaclass
from builtins import object
from io import open

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
    UNICODE_EXISTS = bool(type(unicode))
except NameError:
    unicode = lambda s: str(s)


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
    "Exception for JUnit XML related errors."


class Attr(object):
    "XML element attribute descriptor, for string values."

    def __init__(self, name=None):
        self.name = name

    def __get__(self, instance, cls):
        "Gets value from attribute, return None if attribute doesn't exist."
        value = instance._elem.attrib.get(self.name)
        return value

    def __set__(self, instance, value):
        "Sets XML element attribute."
        if value is not None:
            instance._elem.attrib[self.name] = unicode(value)


class IntAttr(Attr):
    "Integer attributes"

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
    "Float attributes."

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
    "Decorator to read XML element attribute name from class attribute."
    for key, value in vars(cls).items():
        if isinstance(value, Attr):
            value.name = key
    return cls


class junitxml(type):
    "Metaclass to decorate the xml class"

    def __new__(meta, name, bases, methods):
        cls = super(junitxml, meta).__new__(meta, name, bases, methods)
        cls = attributed(cls)
        return cls


class Element(with_metaclass(junitxml, object)):
    "Base class for all Junit elements."

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

    def append(self, elem):
        "Append an child element to current element."
        self._elem.append(elem._elem)

    @classmethod
    def fromstring(cls, text):
        "Construct Junit objects with XML string."
        instance = cls()
        instance._elem = etree.fromstring(text)
        return instance

    @classmethod
    def fromelem(cls, elem):
        "Constructs Junit objects with an element."
        if elem is None:
            return
        instance = cls()
        if isinstance(elem, Element):
            instance._elem = elem._elem
        else:
            instance._elem = elem
        return instance

    def iterchildren(self, Child):
        "Iterate through specified Child type elements."
        elems = self._elem.iterfind(Child._tag)
        for elem in elems:
            yield Child.fromelem(elem)

    def child(self, Child):
        "Find a single child of specified type."
        elem = self._elem.find(Child._tag)
        return Child.fromelem(elem)

    def remove(self, instance):
        for elem in self._elem.iterfind(instance._tag):
            child = instance.__class__.fromelem(elem)
            if child == instance:
                self._elem.remove(child._elem)

    def tostring(self):
        "Converts element to XML string."
        return etree.tostring(self._elem, encoding="utf-8")


class JUnitXml(Element):
    _tag = "testsuites"
    name = Attr()
    time = FloatAttr()
    tests = IntAttr()
    failures = IntAttr()
    errors = IntAttr()

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
        for suite in other:
            self.add_testsuite(suite)
        return self

    def add_testsuite(self, suite):
        self.append(suite)

    def update_statistics(self):
        "Update test count, time, etc."
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
        self.time = time

    @classmethod
    def fromfile(cls, filepath):
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
        write_xml(self, filepath=filepath, pretty=pretty)


class TestSuite(Element):
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
                result.add_testcase(case)
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
                self.add_testcase(case)
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
        for case in self:
            if case == testcase:
                super(TestSuite, self).remove(case)

    def update_statistics(self):
        "Updates test count and test time."
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
        props = self.child(Properties)
        if props is None:
            props = Properties()
            self.append(props)
        prop = Property(name, value)
        props.add_property(prop)

    def add_testcase(self, testcase):
        self.append(testcase)

    def add_testsuite(self, suite):
        self.append(suite)

    def properties(self):
        props = self.child(Properties)
        if props is None:
            return
        for prop in props:
            yield prop

    def remove_property(self, property):
        props = self.child(Properties)
        if props is None:
            return
        for prop in props:
            if prop == property:
                props.remove(property)

    def testsuites(self):
        for suite in self.iterchildren(TestSuite):
            yield suite

    def write(self, filepath=None, pretty=False):
        write_xml(self, filepath=filepath, pretty=pretty)


class Properties(Element):
    _tag = "properties"

    def __init__(self):
        super(Properties, self).__init__(self._tag)

    def add_property(self, property):
        self.append(property)

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
        "Supports sort() for properties."
        return self.name > other.name


class Result(Element):
    _tag = None
    message = Attr()
    type = Attr()

    def __init__(self, message=None, type=None):
        super(Result, self).__init__(self._tag)
        if message:
            self.message = message
        if type:
            self.type = type

    def __eq__(self, other):
        return (
            self._tag == other._tag
            and self.type == other.type
            and self.message == other.message
        )


class Skipped(Result):
    _tag = "skipped"

    def __eq__(self, other):
        return super(Skipped, self).__eq__(other)


class Failure(Result):
    _tag = "failure"

    def __eq__(self, other):
        return super(Failure, self).__eq__(other)


class Error(Result):
    _tag = "error"

    def __eq__(self, other):
        return super(Error, self).__eq__(other)


class TestCase(Element):
    _tag = "testcase"
    name = Attr()
    classname = Attr()
    time = FloatAttr()
    _possible_results = {Failure, Error, Skipped}

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
        "One of the Failure, Skipped, and Error objects."
        results = []
        for res in self._possible_results:
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
        for res in self._possible_results:
            result = self.child(res)
            if result is not None:
                self.remove(result)
        # Then add current result
        self.append(value)

    @property
    def system_out(self):
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

    def update_statistics(self):
        pass


class System(Element):
    "Parent class for SystemOut and SystemErr"
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
