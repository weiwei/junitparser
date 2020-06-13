junitparser -- Pythonic JUnit/xUnit Result XML Parser
======================================================

.. image:: https://api.codacy.com/project/badge/Grade/00cfb3ab06ca4e419b787af69ff2a8c3
   :alt: Codacy Badge
   :target: https://app.codacy.com/app/gastlygem/junitparser?utm_source=github.com&utm_medium=referral&utm_content=gastlygem/junitparser&utm_campaign=badger
.. image:: https://travis-ci.org/gastlygem/junitparser.svg?branch=master
.. image:: https://coveralls.io/repos/github/gastlygem/junitparser/badge.svg?branch=master
   :target: https://coveralls.io/github/gastlygem/junitparser?branch=master


What does it do?
----------------

junitparser is a JUnit/xUnit Result XML Parser. Use it to parse and manipulate
existing Result XML files, or create new JUnit/xUnit result XMLs from scratch.

There are already a lot of modules that converts JUnit/xUnit XML from a
specific format, but you may run into some proprietory or less-known formats
and you want to convert them and feed the result to another tool, or, you may
want to manipulate the results in your own way. This is where junitparser come
into handy.

Why junitparser?
----------------

* Functionality. There are various JUnit/xUnit XML libraries, some does
  parsing, some does XML generation, some does manipulation. This module does 
  all in a single package.
* Extensibility. JUnit/xUnit is hardly a standardized format. The base format
  is somewhat universally agreed with, but beyond that, there could be "custom"
  elements and attributes. junitparser aims to support them all, by
  allowing the user to monkeypatch and subclass some base classes.
* Pythonic. You can manipulate test cases and suites in a pythonic way.

Installation
-------------

::

    pip install junitparser

Usage
-----

You should be relatively familiar with the Junit XML format. If not, run
``pydoc`` on the exposed classes and functions to see how it's structured.

Create Junit XML format reports from scratch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You have some test result data, and you want to convert them into junit.xml
format.

.. code-block:: python

    from junitparser import TestCase, TestSuite, JUnitXml, Skipped, Error

    # Create cases
    case1 = TestCase('case1')
    case1.result = Skipped()
    case2 = TestCase('case2')
    case2.result = Error('Example error message', 'the_error_type')

    # Create suite and add cases
    suite = TestSuite('suite1')
    suite.add_property('build', '55')
    suite.add_testcase(case1)
    suite.add_testcase(case2)
    suite.remove_testcase(case2)

    # Add suite to JunitXml
    xml = JUnitXml()
    xml.add_testsuite(suite)
    xml.write('junit.xml')

Read and manipulate exiting JUnit/xUnit XML files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You have some existing junit.xml files, and you want to modify the content.

.. code-block:: python

    from junitparser import JUnitXml

    xml = JUnitXml.fromfile('/path/to/junit.xml')
    for suite in xml:
        # handle suites
        for case in suite:
            # handle cases
    xml.write() # Writes back to file


Merge XML files
~~~~~~~~~~~~~~~

You have two or more XML files, and you want to merge them into one.

.. code-block:: python

    from junitparser import JUnitXml

    xml1 = JUnitXml.fromfile('/path/to/junit1.xml')
    xml2 = JUnitXml.fromfile('/path/to/junit2.xml')

    newxml = xml1 + xml2
    # Alternatively, merge in place
    xml1 += xml2

Note that it won't check for duplicate entries. You need to deal with them on
your own.

Create XML with custom attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You want to use an attribute that is not supported by default.

.. code-block:: python

    from junitparser import TestCase, Attr, IntAttr, FloatAttr

    # Add the custom attribute
    TestCase.id = IntAttr('id')
    TestCase.rate = FloatAttr('rate')
    TestCase.custom = Attr('custom')
    case = TestCase()
    case.id = 123
    case.rate = 0.95
    case.custom = 'foobar'


Handling XML with custom element
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There may be once in 1000 years you want to it this way, but anyways.
Suppose you want to add element CustomElement to TestCase.

.. code-block:: python

    from junitparser import Element, Attr, TestSuite

    # Create the new element by subclassing Element,
    # and add custom attributes to it.
    class CustomElement(Element):
        _tag = 'custom'
        foo = Attr()
        bar = Attr()

    testcase = TestCase()
    custom = CustomElement()
    testcase.append(custom)
    # To find a single sub-element:
    testcase.child(CustomElement)
    # To iterate over custom elements:
    for custom in testcase.iterchildren(CustomElement):
        ... # Do things with custom element

Handling custom XML attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Say you have some data stored in the XML as custom attributes and you want to
read them out:

.. code-block:: python

    from junitparser import Element, Attr, TestSuite

    # Create the new element by subclassing Element or one of its child class,
    # and add custom attributes to it.
    class MyTestCase(TestCase):
        foo = Attr()

    xml = JUnitXml.fromfile('/path/to/junit.xml')
    for suite in xml:
        # handle suites
        for case in suite:
            my_case = MyTestCase.fromelem(case)
            print(my_case.foo)

Command Line
------------

.. code-block:: shell

    $ junitparser --help
    usage: junitparser [-h] [-v] {merge} ...

    Junitparser CLI helper.

    positional arguments:
    {merge}        command
      merge        Merge Junit XML format reports with junitparser.

    optional arguments:
    -h, --help     show this help message and exit
    -v, --version  show program's version number and exit


.. code-block:: shell

    $ junitparser merge --help
    usage: junitparser merge [-h] paths [paths ...] output

    positional arguments:
    paths       Original XML path(s).
    output      Merged XML Path.

    optional arguments:
    -h, --help  show this help message and exit

Test
----

You can run the cases directly::

    python test.py

Or use pytest::

    pytest test.py

Notes
-----

There are some other packages providing similar functionalities. They are
out there for a longer time, but might not be as feature-rich or fun as 
junitparser:

* xunitparser_: Read JUnit/XUnit XML files and map them to Python objects
* xunitgen_: Generate xUnit.xml files
* xunitmerge_: Utility for merging multiple XUnit xml reports into a single
  xml report.
* `junit-xml`_: Creates JUnit XML test result documents that can be read by
  tools such as Jenkins

.. _xunitparser: https://pypi.python.org/pypi/xunitparser
.. _xunitgen: https://pypi.python.org/pypi/xunitgen
.. _xunitmerge: https://pypi.python.org/pypi/xunitmerge
.. _`junit-xml`: https://pypi.python.org/pypi/junit-xml


Contribute
----------

Please do!
