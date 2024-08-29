# -*- coding: utf-8 -*-

from junitparser.xunit2 import JUnitXml, TestSuite, TestCase, RerunFailure
from junitparser import Failure
from copy import deepcopy


class Test_TestCase:
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
        assert case.name == "testname"
        assert isinstance(case.result[0], Failure)
        assert case.system_out == "System out"
        assert case.system_err == "System err"
        rerun_failures = case.rerun_failures()
        assert len(rerun_failures) == 2
        assert rerun_failures[0].message == "Not found"
        assert rerun_failures[0].stack_trace is None
        assert rerun_failures[0].system_out == "No ha encontrado"
        assert rerun_failures[0].system_err is None
        assert rerun_failures[1].message == "Server error"
        assert rerun_failures[1].stack_trace == "Stacktrace"
        assert rerun_failures[1].system_out is None
        assert rerun_failures[1].system_err == "Error del servidor"
        assert len(case.rerun_errors()) == 0
        assert len(case.flaky_failures()) == 0
        assert len(case.flaky_errors()) == 0

    def test_case_rerun(self):
        case = TestCase("testname")
        rerun_failure = RerunFailure("Not found", "404")
        assert rerun_failure.system_out == None
        assert rerun_failure.system_err == None
        rerun_failure.stack_trace = "Stack"
        rerun_failure.system_err = "E404"
        rerun_failure.system_out = "NOT FOUND"
        case.add_rerun_result(rerun_failure)
        assert len(case.rerun_failures()) == 1
        # Interesting, same object is only added once by xml libs
        failure2 = deepcopy(rerun_failure)
        failure2.stack_trace = "Stack2"
        failure2.system_err = "E401"
        failure2.system_out = "401 Error"
        case.add_rerun_result(failure2)
        assert len(case.rerun_failures()) == 2


class Test_TestSuite:
    def test_properties(self):
        suite = TestSuite("mySuite")
        assert suite.system_out is None
        assert suite.system_err is None
        suite.system_err = "System err"
        suite.system_out = "System out"
        assert suite.system_out == "System out"
        assert suite.system_err == "System err"
        suite.system_err = "System err2"
        suite.system_out = "System out2"
        assert suite.system_out == "System out2"
        assert suite.system_err == "System err2"

    def test_iterate_case(self):
        suite = TestSuite("mySuite")
        suite.add_testcase(TestCase("test1"))
        case = next(iter(suite))
        assert case.name == "test1"

    def test_iterate_suite(self):
        suite = TestSuite("mySuite")
        suite.add_testsuite(TestSuite("suite1"))
        suite = next(suite.testsuites())
        assert suite.name == "suite1"

    def test_remove_case(self):
        suite = TestSuite("mySuite")
        test = TestCase("test1")
        suite.add_testcase(test)
        suite.remove_testcase(test)
        assert len(suite) == 0


class Test_JUnitXml:
    def test_init(self):
        xml = JUnitXml("tests")
        assert xml.name == "tests"
        xml = JUnitXml("myname")
        xml.add_testsuite(TestSuite("suite1"))
        xml.update_statistics()
        assert xml.skipped is None
        assert xml.tostring().count(b"errors") == 2
        assert xml.tostring().count(b"skipped") == 1

    def test_fromstring(self):
        text = """<testsuite name="suite name">
         <testcase name="test name 1"/>
         <testcase name="test name 2"/>
        </testsuite>"""
        suite = JUnitXml.fromstring(text)
        assert isinstance(suite, TestSuite)
        assert suite.name == "suite name"
        assert len(list(suite)) == 2
        assert [test.name for test in suite] == ["test name 1", "test name 2"]
