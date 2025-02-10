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


def test_merge_output_to_terminal(capsys: pytest.CaptureFixture):
    ret = cli.main(["merge", str(DATA_DIR / "normal.xml"), "-"])
    assert ret == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("<?xml version='1.0' encoding='utf-8'?>")


def test_verify_with_glob():
    ret = cli.main(["verify", "--glob", str(DATA_DIR / "pytest_*.xml")])
    # we expect failure, as one of the files has errors
    assert ret == 1
