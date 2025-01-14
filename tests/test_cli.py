from pathlib import Path
import pytest
from junitparser import cli

DATA_DIR = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    "file, expected_exitcode",
    [("jenkins.xml", 1), ("no_fails.xml", 0), ("normal.xml", 1)],
)
def test_verify(file: str, expected_exitcode: int):
    path = DATA_DIR / file
    assert cli.verify([path]) == expected_exitcode


def test_merge(tmp_path: Path):
    files = [DATA_DIR / "jenkins.xml", DATA_DIR / "pytest_success.xml"]
    suites = ["JUnitXmlReporter", "JUnitXmlReporter.constructor", "pytest"]
    outfile = tmp_path / "merged.xml"
    cli.merge(files, str(outfile))
    xml = outfile.read_text()
    for s in suites:
        assert f'testsuite name="{s}"' in xml
