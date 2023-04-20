# -*- coding: utf-8 -*-

import unittest
from junitparser.flavors.pytest_xml import PytestXml, TestSuite, TestCase, FlakyError, FlakyFailure, RerunError, RerunFailure
from junitparser import Failure


class Test_TestCase(unittest.TestCase):
    def test_case_fromstring(self):
        text = """<testcase name="testname">
        <failure message="failure message" type="FailureType"/>
        <rerunFailure message="Not found" type="404">
            <system-out>No ha encontrado</system-out>
        </rerunFailure>
        <rerunFailure message="Server error" type="500">
            <system-error>Error del servidor</system-error>
        </rerunFailure>
        <system-out>System out</system-out>
        <system-err>System err</system-err>
        </testcase>"""
        case = TestCase.fromstring(text)
        self.assertEqual(case.name, "testname")
        self.assertIsInstance(case.result[0], Failure)
        self.assertEqual(case.system_out, "System out")
        self.assertEqual(case.system_err, "System err")
        self.assertEqual(len(case.rerun_failures()), 2)
