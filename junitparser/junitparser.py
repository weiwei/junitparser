"""
junitparser is a JUnit/xUnit Result XML Parser. Use it to parse and manipulate
existing Result XML files, or create new JUnit/xUnit result XMLs from scratch.

:copyright: (c) 2016 by Joel Wang.
:license: Apache2, see LICENSE for more details.
"""

try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree


class JUnitXmlError(Exception):
    "Exception for JUnit XML related errors."


class Attr:
    "XML element attribute descriptor."

    def __init__(self, name=None):
        self.name = name

    def __get__(self, instance, cls):
        "Gets value from attribute, return None if attribute doesn't exist."
        return instance._elem.attrib.get(self.name)

    def __set__(self, instance, value):
        "Sets XML element attribute."
        instance._elem.attrib[self.name] = value


def attributed(cls):
    "Decorator to read XML element attribute name from class attribute."
    for key, value in vars(cls).items():
        if isinstance(value, Attr):
            value.name = key
    return cls


class junitxml(type):
    "Metaclass to decorate the xml class"
    def __new__(meta, name, bases, methods):
        cls = super().__new__(meta, name, bases, methods)
        cls = attributed(cls)
        return cls


class Element(metaclass=junitxml):
    "Base class for all Junit elements."

    def __init__(self, name):
        self._elem = etree.Element(name)

    def __hash__(self):
        return hash(etree.tostring(self._elem))

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
        instance._elem = elem
        for attr in vars(instance):
            if isinstance(getattr(instance, attr), Attr):
                setattr(instance, attr, instance._elem.attrib.get(attr))
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
        return etree.tostring(self._elem, encoding='utf-8')


class JUnitXml(Element):
    _tag = 'testsuites'

    def __init__(self):
        super().__init__(self._tag)
        self.filepath = None

    def __iter__(self):
        return super().iterchildren(TestSuite)

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

    @classmethod
    def fromfile(cls, filepath):
        instance = cls()
        instance.filepath = filepath
        tree = etree.parse(filepath)
        instance._elem = tree.getroot()
        if instance._elem.tag != cls._tag:
            raise JUnitXmlError("Invalid format.")
        return instance

    def write(self, filepath=None):
        tree = etree.ElementTree(self._elem)
        if not filepath:
            filepath = self.filepath
        tree.write(filepath, encoding='utf-8', xml_declaration=True)


class TestSuite(Element):
    _tag = 'testsuite'
    name = Attr()
    hostname = Attr()
    time = Attr()
    timestamp = Attr()
    tests = Attr()
    failures = Attr()
    errors = Attr()

    def __init__(self, name=None):
        super().__init__(self._tag)
        if name:
            self.name = name

    def __iter__(self):
        return super().iterchildren(TestCase)

    def __len__(self):
        return len(list(self.__iter__()))

    def remove_testcase(self, testcase):
        for case in self:
            if case == testcase:
                super().remove(case)

    def update_case_count(self):
        tests = errors = failures = 0
        for case in self:
            tests += 1
            if isinstance(case.result, Failure):
                failures += 1
            elif isinstance(case.result, Error):
                errors += 1
        self.tests = str(tests)
        self.errors = str(errors)
        self.failures = str(failures)

    def add_property(self, name, value):
        props = self.child(Properties)
        if props is None:
            props = Properties()
            self.append(props)
        prop = Property(name, value)
        props.add_property(prop)

    def add_testcase(self, testcase):
        self.append(testcase)

    def add_suite(self, suite):
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


class Properties(Element):
    _tag = 'properties'

    def __init__(self):
        super().__init__(self._tag)

    def add_property(self, property):
        self.append(property)

    def __iter__(self):
        return super().iterchildren(Property)


class Property(Element):
    _tag = 'property'
    name = Attr()
    value = Attr()

    def __init__(self, name=None, value=None):
        super().__init__(self._tag)
        if name:
            self.name = name
        if value:
            self.value = value

    def __eq__(self, other):
        return self.name == other.name


class Result(Element):
    _tag = None
    message = Attr()
    type = Attr()

    def __init__(self, message=None, type=None):
        super().__init__(self._tag)
        if message:
            self.message = message
        if type:
            self.type = type

    def __eq__(self, other):
        return (self._tag == other._tag and
                self.type == other.type and
                self.message == other.message)


class Skipped(Result):
    _tag = 'skipped'

    def __eq__(self, other):
        return super().__eq__(other)


class Failure(Result):
    _tag = 'failure'

    def __eq__(self, other):
        return super().__eq__(other)


class Error(Result):
    _tag = 'error'

    def __eq__(self, other):
        return super().__eq__(other)


class TestCase(Element):
    _tag = 'testcase'
    name = Attr()
    classname = Attr()
    time = Attr()
    _possible_results = {Failure, Error, Skipped}

    def __init__(self):
        super().__init__(self._tag)

    def __hash__(self):
        return super().__hash__()

    def __eq__(self, other):
        # TODO: May not work correctly of unreliable hash method is used.
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


class System(Element):
    "Parent class for SystemOut and SystemErr"
    _tag = ''

    def __init__(self, content=None):
        super().__init__(self._tag)
        self.text = content

    @property
    def text(self):
        return self._elem.text

    @text.setter
    def text(self, value):
        self._elem.text = value


class SystemOut(System):
    _tag = 'system-out'


class SystemErr(System):
    _tag = 'system-err'
