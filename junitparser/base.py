from junitparser.junitparser import JUnitXml, TestSuite, TestSuites
from future.utils import with_metaclass

try:
    from html import escape  # python 3.x
except ImportError:
    from cgi import escape  # python 2.x

try:
    type(unicode)
except NameError:
    unicode = str

try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree


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
        if result is None and isinstance(instance, (TestSuites, TestSuite)):
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
        if result is None and isinstance(instance, (TestSuites, TestSuite)):
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
        instance._elem = etree.fromstring(text) # nosec
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

    def iter(self, *child_types):
        """Iterate through specified Child type elements."""
        tags = (t._tag for t in child_types)
        for elem in self._elem.iter(*tags):
            yield child_types[tags.index(elem.tag)].fromelem(elem)

    def child(self, child_type):
        """Find a single child of specified Child type."""
        elem = self._elem.find(child_type._tag)
        return child_type.fromelem(elem)

    def remove(self, sub_elem):
        """Remove a sub element."""
        for elem in self._elem.iterfind(sub_elem._tag):
            child = sub_elem.__class__.fromelem(elem)
            if child == sub_elem:
                self._elem.remove(child._elem)

    def tostring(self):
        """Converts element to XML string."""
        return etree.tostring(self._elem, encoding="utf-8")

    @property
    def text(self):
        return self._elem.text

    @text.setter()
    def text(self, value):
        self._elem.text = value
