from junitparser.base import Attr, Element

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

    @property
    def text(self):
        return self._elem.text

    @text.setter
    def text(self, value):
        self._elem.text = value

class Skipped(Result):
    """Test result when the case is skipped.

    JUnit5 doesn't define any attrs, pytest junit defines it to have ``type``
    and ``message`` attrs, the same with ``failure`` and ``error``.

    Here we follow the pytest format.
    """

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


class SystemOut(Element):
    """Test result when the case has errors during execution."""

    _tag = "system-out"

    def __eq__(self, other):
        return super(SystemOut, self).__eq__(other)


class SystemErr(Element):
    """Test result when the case has errors during execution."""

    _tag = "system-err"

    def __eq__(self, other):
        return super(SystemErr, self).__eq__(other)


POSSIBLE_RESULTS = {Failure, Error, Skipped, SystemOut, SystemErr}

