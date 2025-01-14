from pathlib import Path
import pytest
from junitparser.cli import verify


@pytest.mark.parametrize(
    "file, expected_exitcode",
    [("data/jenkins.xml", 1), ("data/no_fails.xml", 0), ("data/normal.xml", 1)],
)
def test_verify(file: str, expected_exitcode: int):
    path = Path(__file__).parent / file
    assert verify([path]) == expected_exitcode
