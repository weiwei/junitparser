from junitparser.xunit2 import JUnitXml, TestSuite, TestCase, RerunFailure, RerunError, FlakyFailure, FlakyError
from junitparser import Failure
from copy import deepcopy


class Test_TestCase:
    def test_case_rerun_fromstring(self):
        text = """<testcase name="testname">
        <failure message="failure message" type="FailureType"/>
        <rerunFailure message="Not found" type="404">
            <system-out>No ha encontrado</system-out>
        </rerunFailure>
        <rerunFailure message="Server error" type="500">
            <system-err>Error del servidor</system-err>
            <stackTrace>Stacktrace</stackTrace>
        </rerunFailure>
        <rerunError message="Setup error"/>
        <system-out>System out</system-out>
        <system-err>System err</system-err>
        </testcase>"""
        case = TestCase.fromstring(text)
        assert isinstance(case, TestCase)
        assert case.name == "testname"
        assert len(case.result) == 1
        assert isinstance(case.result[0], Failure)
        assert case.system_out == "System out"
        assert case.system_err == "System err"
        assert case.is_passed is False
        assert case.is_failure is True
        assert case.is_error is False
        assert case.is_skipped is False
        assert case.is_rerun is True
        assert case.is_flaky is False

        interim_results = case.interim_result
        assert len(interim_results) == 3
        assert isinstance(interim_results[0], RerunFailure)
        assert isinstance(interim_results[1], RerunFailure)
        assert isinstance(interim_results[2], RerunError)

        rerun_failures = case.rerun_failures()
        assert len(rerun_failures) == 2
        assert isinstance(rerun_failures[0], RerunFailure)
        assert rerun_failures[0].message == "Not found"
        assert rerun_failures[0].stack_trace is None
        assert rerun_failures[0].system_out == "No ha encontrado"
        assert rerun_failures[0].system_err is None
        assert isinstance(rerun_failures[1], RerunFailure)
        assert rerun_failures[1].message == "Server error"
        assert rerun_failures[1].stack_trace == "Stacktrace"
        assert rerun_failures[1].system_out is None
        assert rerun_failures[1].system_err == "Error del servidor"

        rerun_errors = case.rerun_errors()
        assert len(rerun_errors) == 1
        assert isinstance(rerun_errors[0], RerunError)
        assert rerun_errors[0].message == "Setup error"
        assert rerun_errors[0].stack_trace is None
        assert rerun_errors[0].system_out is None
        assert rerun_errors[0].system_err is None

        assert len(case.flaky_failures()) == 0

        assert len(case.flaky_errors()) == 0

    def test_case_flaky_fromstring(self):
        text = """<testcase name="testname">
        <flakyFailure message="Not found" type="404">
            <system-out>No ha encontrado</system-out>
        </flakyFailure>
        <flakyFailure message="Server error" type="500">
            <system-err>Error del servidor</system-err>
            <stackTrace>Stacktrace</stackTrace>
        </flakyFailure>
        <flakyError message="Setup error"/>
        <system-out>System out</system-out>
        <system-err>System err</system-err>
        </testcase>"""
        case = TestCase.fromstring(text)
        assert case.name == "testname"
        assert len(case.result) == 0
        assert case.system_out == "System out"
        assert case.system_err == "System err"
        assert case.is_passed is True
        assert case.is_failure is False
        assert case.is_error is False
        assert case.is_skipped is False
        assert case.is_rerun is False
        assert case.is_flaky is True

        interim_results = case.interim_result
        assert len(interim_results) == 3
        assert isinstance(interim_results[0], FlakyFailure)
        assert isinstance(interim_results[1], FlakyFailure)
        assert isinstance(interim_results[2], FlakyError)

        assert len(case.rerun_failures()) == 0

        assert len(case.rerun_errors()) == 0

        flaky_failures = case.flaky_failures()
        assert len(flaky_failures) == 2
        assert isinstance(flaky_failures[0], FlakyFailure)
        assert flaky_failures[0].message == "Not found"
        assert flaky_failures[0].stack_trace is None
        assert flaky_failures[0].system_out == "No ha encontrado"
        assert flaky_failures[0].system_err is None
        assert isinstance(flaky_failures[1], FlakyFailure)
        assert flaky_failures[1].message == "Server error"
        assert flaky_failures[1].stack_trace == "Stacktrace"
        assert flaky_failures[1].system_out is None
        assert flaky_failures[1].system_err == "Error del servidor"

        flaky_errors = case.flaky_errors()
        assert len(flaky_errors) == 1
        assert isinstance(flaky_errors[0], FlakyError)
        assert flaky_errors[0].message == "Setup error"
        assert flaky_errors[0].stack_trace is None
        assert flaky_errors[0].system_out is None
        assert flaky_errors[0].system_err is None

    def test_case_rerun(self):
        case = TestCase("testname")
        rerun_failure = RerunFailure("Not found", "404")
        assert rerun_failure.system_out is None
        assert rerun_failure.system_err is None
        rerun_failure.stack_trace = "Stack"
        rerun_failure.system_err = "E404"
        rerun_failure.system_out = "NOT FOUND"
        case.add_interim_result(rerun_failure)
        assert len(case.rerun_failures()) == 1
        # Interesting, same object is only added once by xml libs
        failure2 = deepcopy(rerun_failure)
        failure2.stack_trace = "Stack2"
        failure2.system_err = "E401"
        failure2.system_out = "401 Error"
        case.add_interim_result(failure2)
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
        assert isinstance(suite, TestSuite)
        assert suite.name == "suite1"

    def test_remove_case(self):
        suite = TestSuite("mySuite")
        test = TestCase("test1")
        suite.add_testcase(test)
        suite.remove_testcase(test)
        assert len(suite) == 0

    def test_add_testsuites(self):
        suite1 = TestSuite("suite1")
        suite2 = TestSuite("suite2")
        suites = suite1 + suite2
        assert isinstance(suites, JUnitXml)
        assert len(list(iter(suites))) == 2

    def test_iadd_testsuites(self):
        suite1 = TestSuite("suite1")
        suite2 = TestSuite("suite2")
        suite1 += suite2
        assert isinstance(suite1, JUnitXml)
        assert len(list(iter(suite1))) == 2


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
        text = """<testsuites><testsuite name="suitename1">
        <testcase name="testname1">
        </testcase></testsuite>
        <testsuite name="suitename2">
        <testcase name="testname2"/>
        <testcase name="testname3">
        </testcase></testsuite></testsuites>"""
        xml = JUnitXml.fromstring(text)
        assert isinstance(xml, JUnitXml)
        suites = list(xml)
        assert len(suites) == 2
        suite1, suite2 = suites
        assert isinstance(suite1, TestSuite)
        assert isinstance(suite2, TestSuite)
        assert suite1.name == "suitename1"
        assert suite2.name == "suitename2"
        cases = list(suite2)
        assert len(cases) == 2
        assert isinstance(cases[0], TestCase)
        assert isinstance(cases[1], TestCase)
        assert [test.name for test in cases] == ["testname2", "testname3"]

    def test_suite_fromstring(self):
        text = """<testsuite name="suite name">
         <testcase name="test name 1"/>
         <testcase name="test name 2"/>
        </testsuite>"""
        xml = JUnitXml.fromstring(text)
        assert isinstance(xml, JUnitXml)
        suites = list(xml)
        assert len(suites) == 1
        suite = suites[0]
        assert isinstance(suite, TestSuite)
        assert suite.name == "suite name"
        cases = list(suite)
        assert len(cases) == 2
        assert isinstance(cases[0], TestCase)
        assert isinstance(cases[1], TestCase)
        assert [test.name for test in suite] == ["test name 1", "test name 2"]
