# -*- coding: utf-8 -*-

import unittest
from junitparser.flavors.xunit2 import JUnitXml, TestSuite, TestCase, RerunFailure
from junitparser import Failure
from copy import deepcopy

class Test_TestCase(unittest.TestCase):
    def test_case_fromstring(self):
        text = """<testcase name="testname">
        <failure message="failure message" type="FailureType"/>
        <rerunFailure message="Not found" type="404">
            <system-out>No ha encontrado</system-out>
        </rerunFailure>
        <rerunFailure message="Server error" type="500">
            <system-err>Error del servidor</system-err>
            <stackTrace>Stacktrace</stackTrace>
        </rerunFailure>
        <system-out>System out</system-out>
        <system-err>System err</system-err>
        </testcase>"""
        case = TestCase.fromstring(text)
        self.assertEqual(case.name, "testname")
        self.assertIsInstance(case.result[0], Failure)
        self.assertEqual(case.system_out, "System out")
        self.assertEqual(case.system_err, "System err")
        rerun_failures = case.rerun_failures()
        self.assertEqual(len(rerun_failures), 2)
        self.assertEqual(rerun_failures[0].message, "Not found")
        self.assertEqual(rerun_failures[0].stack_trace, None)
        self.assertEqual(rerun_failures[0].system_out, "No ha encontrado")
        self.assertEqual(rerun_failures[1].stack_trace, "Stacktrace")
        self.assertEqual(rerun_failures[1].system_err, "Error del servidor")
        self.assertEqual(len(case.rerun_errors()), 0)
        self.assertEqual(len(case.flaky_failures()), 0)
        self.assertEqual(len(case.flaky_errors()), 0)
    def test_rerun(self):
        case = TestCase("testname")
        rerun_failure = RerunFailure("Not found", "404")
        self.assertEqual(rerun_failure.system_out, None)
        self.assertEqual(rerun_failure.system_err, None)
        rerun_failure.stack_trace = "Stack"
        rerun_failure.system_err = "E404"
        rerun_failure.system_out = "NOT FOUND"
        case.add_rerun_result(rerun_failure)
        self.assertEqual(len(case.rerun_failures()), 1)
        # Interesting, same object is only added once by xml libs
        failure2 = deepcopy(rerun_failure)
        failure2.stack_trace = "Stack2"
        failure2.system_err = "E401"
        failure2.system_out = "401 Error"
        case.add_rerun_result(failure2)
        self.assertEqual(len(case.rerun_failures()), 2)


class Test_TestSuite(unittest.TestCase):
    def test_properties(self):
        suite = TestSuite("mySuite")
        self.assertEqual(suite.system_out, None)
        self.assertEqual(suite.system_err, None)
        suite.system_err = "System err"
        suite.system_out = "System out"
        self.assertEqual(suite.system_out, "System out")
        self.assertEqual(suite.system_err, "System err")
        suite.system_err = "System err2"
        suite.system_out = "System out2"
        self.assertEqual(suite.system_out, "System out2")
        self.assertEqual(suite.system_err, "System err2")
    def test_iterate_case(self):
        suite = TestSuite("mySuite")
        suite.add_testcase(TestCase("test1"))
        case = next(iter(suite))
        self.assertEqual(case.name, "test1")
    def test_iterate_suite(self):
        suite = TestSuite("mySuite")
        suite.add_testsuite(TestSuite("suite1"))
        suite = next(suite.testsuites())
        self.assertEqual(suite.name, "suite1")
    def test_remove_case(self):
        suite = TestSuite("mySuite")
        test = TestCase("test1")
        suite.add_testcase(test)
        suite.remove_testcase(test)
        self.assertEqual(list(iter(suite)), [])

class Test_JUnitXml(unittest.TestCase):
    def test_init(self):
        xml = JUnitXml("tests")
        self.assertEqual(xml.name, "tests")
        xml = JUnitXml("myname")
        xml.add_testsuite(TestSuite("suite1"))
        xml.update_statistics()
        self.assertEqual(xml.skipped, None)
        # errors="0"
        self.assertEqual(xml.tostring().count(b"errors"), 2)
        # "skipped" attribute doesn't exist
        self.assertEqual(xml.tostring().count(b"skipped"), 1)
