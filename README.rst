junitparser -- Pythonic JUnit/xUnit Result XML Parser
======================================================

.. image:: https://github.com/weiwei/junitparser/workflows/build/badge.svg?branch=master
   :target: https://github.com/weiwei/junitparser/actions
.. image:: https://codecov.io/gh/weiwei/junitparser/branch/master/graph/badge.svg?token=UotlfRXNnK
   :target: https://codecov.io/gh/weiwei/junitparser

junitparser handles JUnit/xUnit Result XML files. Use it to parse and manipulate
existing Result XML files, or create new JUnit/xUnit result XMLs from scratch.

Features
--------

* Parse or modify existing JUnit/xUnit xml files.
* Parse or modify non-standard or customized JUnit/xUnit xml files, by monkey
  patching existing element definitions.
* Create JUnit/xUnit test results from scratch.
* Merge test result xml files.
* Specify xml parser. For example you can use lxml to speed things up.
* Invoke from command line, or `python -m junitparser`
* Python 2 and 3 support (As of Nov 2020, 1/4 of the users are still on Python 
  2, so there is no plan to drop Python 2 support)

Note on version 2
-----------------

Version 2 improved support for pytest result xml files by fixing a few issues, 
notably that there could be multiple <Failure> or <Error> entries. There is a 
breaking change that ``TestCase.result`` is now a list instead of a single item.
If you are using this attribute, please update your code accordingly.

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
    case1 = TestCase('case1', 'class.name', 0.5) # params are optional
    case1.classname = "modified.class.name" # specify or change case attrs
    case1.result = [Skipped()] # You can have a list of results
    case2 = TestCase('case2')
    case2.result = [Error('Example error message', 'the_error_type')]

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

It is also possible to use a custom parser. For example lxml provides a plethora
of parsing options_. We can use them this way:

.. code-block:: python

    from lxml.etree import XMLParser, parse
    from junitparser import JUnitXml

    def parse_func(file_path):
        xml_parser = XMLParser(huge_tree=True)
        return parse(file_path, xml_parser)

    xml = JUnitXml.fromfile('/path/to/junit.xml', parse_func)
    # process xml...

.. _options: https://lxml.de/api/lxml.etree.XMLParser-class.html

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
    usage: junitparser merge [-h] [--glob] paths [paths ...] output

    positional arguments:
      paths       Original XML path(s).
      output      Merged XML Path.

    optional arguments:
      -h, --help  show this help message and exit
      --glob      Treat original XML path(s) as glob(s).

Test
----

The tests are written with python `unittest`, to run them, use pytest::

    pytest test.py

Contribute
----------

PRs are welcome!
