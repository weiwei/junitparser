from pathlib import Path
import pytest
from junitparser.cli import verify

DATA_DIR = Path(__file__).parent / "data"

@pytest.mark.parametrize(
    "file, expected_exitcode",
    [("jenkins.xml", 1), ("no_fails.xml", 0), ("normal.xml", 1)],
)
def test_verify(file: str, expected_exitcode: int):
    path = DATA_DIR / file
    assert verify([path]) == expected_exitcode
