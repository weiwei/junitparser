# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import unicode_literals

import os
import unittest

from junitparser.cli import verify


class Test_Cli(unittest.TestCase):

    def test_verify(self):
        files_expectedexitcodes = {
            'data/jenkins.xml': 1,
            'data/no_fails.xml': 0,
            'data/normal.xml': 1,
        }
        for file, expected_exitcode in files_expectedexitcodes.items():
            path = os.path.join(os.path.dirname(__file__), file)
            self.assertEqual(verify([path]), expected_exitcode)
