# -*- coding: utf-8 -*-

import os
import pytest
from junitparser.cli import verify


@pytest.mark.parametrize(
    "file, expected_exitcode",
    [("data/jenkins.xml", 1), ("data/no_fails.xml", 0), ("data/normal.xml", 1)],
)
def test_verify(file, expected_exitcode):
    path = os.path.join(os.path.dirname(__file__), file)
    assert verify([path]) == expected_exitcode
