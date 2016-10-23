junitparser -- Pythonic JUnit/xUnit Result XML Parser
======================================================

.. image:: https://travis-ci.org/gastlygem/junitparser.svg?branch=master

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
  parsing, some does XML generation, some does manipulation. This module tries
  to do most functions in a single package.
* Extensibility. JUnit/xUnit is hardly a standardized format. The base format
  is somewhat universally agreed with, but beyond that, there could be "custom"
  elements and attributes. junitparser aims to support them all, by
  monkeypatching and subclassing some base classes.
* Pythonic. You can manipulate test cases and suites in a pythonic way.
* Simplicity. One single code file. No external dependencies. Though it will 
  use lxml if available.

Installation
-------------

::

    pip install junitparser

Usage
-----

Create Junit XML format reports from scratch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from junitparser import TestCase, TestSuite, JunitXml, Skipped, Error

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
	suite.delete_testcase(case2)

    # Add suite to JunitXml
    xml = JunitXml()
    xml.add_testsuite(suite)
    xml.write('junit.xml')

Read and manipulate exiting JUnit/xUnit XML files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from junitparser import JUnitXml

    xml = JUnitXml('/path/to/junit.xml')
    for suite in result:
        # handle suites
        for case in suite:
            # handle cases
    xml.write() # Writes back to file


Merge XML files
~~~~~~~~~~~~~~~

.. code-block:: python

    from junitparser import JUnitXml

    xml1 = JUnitXml('/path/to/junit1.xml')
    xml2 = JUnitXml('/path/to/junit2.xml')

    newxml = xml1 + xml2
    # Alternatively, merge inplace
    xml1 += xml2


Create XML with custom attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from junitparser import TestCase, Attr

    # The id attribute is not supported by default
    # But we can support it by monky patching
    TestCase.id = Attr('id')
    case = TestCase()
    case.id = '123'

    print(case.tostring())

And you get the following output::

    b'<testcase id="123"/>\n'

Create XML with custom element
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There may be once in 1000 years you want to it this way, but anyways:

.. code-block:: python
    
    from junitparser import Element, Attr, TestSuite

    # Suppose you want to add element Custom to TestSuite.
    # You can create the new element by subclassing Element,
    # Then add custom attributes to it.
    class Custom(Element):
        _tag = 'custom'
        foo = Attr()
        bar = Attr()

    # Then monkeypatch TestSuite to handle Custom
    # TODO: Tricky part, update later


TODO
----

* XML 1.0 and 1.1 compatibilities.
* More tests, especially test for errors.

Notes
-----

Python 2 is *not* supported. Currently there is no plan to support Python 2.

There are some other packages providing similar functionalities. They are
out there for a longer time, but might not be as fun as junitparser:

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
