from pathlib import Path
import pytest
from junitparser import cli
from junitparser import version

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
        assert f'name="{s}"' in xml


def test_merge_output_to_terminal(capsys: pytest.CaptureFixture):
    ret = cli.main(["merge", str(DATA_DIR / "normal.xml"), "-"])
    assert ret == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("<?xml version='1.0'")


def test_verify_with_glob():
    ret = cli.main(["verify", "--glob", str(DATA_DIR / "pytest_*.xml")])
    # we expect failure, as one of the files has errors
    assert ret == 1


class Test_CommandlineOptions:

    @classmethod
    def setup_class(cls):
        cls.parser = cli._parser("junitparser")

    @pytest.mark.parametrize("arg", ["-v", "--version"])
    def test_version(self, arg, capsys):
        with pytest.raises(SystemExit) as e:
            self.parser.parse_args([arg])
        captured = capsys.readouterr()
        assert e.value.code == 0
        assert captured.out == f"junitparser {version}\n"

    def test_help_shows_subcommands(self, capsys):
        with pytest.raises(SystemExit) as e:
            self.parser.parse_args(["--help"])
        captured = capsys.readouterr()
        assert "{merge,verify} ...\n" in captured.out
        assert e.value.code == 0

    @pytest.mark.parametrize("command", ["merge", "verify"])
    def test_subcommand_help(self, command):
        with pytest.raises(SystemExit) as e:
            self.parser.parse_args([command, "--help"])
        assert e.value.code == 0

    @pytest.mark.parametrize("command", ["merge", "verify"])
    def test_subcommands_help_general_options(self, command, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args([command, "--help"])
        captured = capsys.readouterr()
        assert "[--glob]" in captured.out
        assert "paths [paths ...]" in captured.out

    def test_merge_help_options(self, capsys):
        with pytest.raises(SystemExit):
            self.parser.parse_args(["merge", "--help"])
        captured = capsys.readouterr()
        assert "[--suite-name SUITE_NAME]" in captured.out
        assert "output\n" in captured.out

    @pytest.mark.parametrize("command", ["merge", "verify"])
    def test_option_glob(
        self,
        command,
    ):
        args = self.parser.parse_args([command, "--glob", "pytest_*.xml", "-"])
        assert args.paths_are_globs

    def test_verify_argument_path(self):
        files = ["foo", "bar"]
        args = self.parser.parse_args(["verify", *files])
        assert args.paths == files

    def test_merge_argument_path(self):
        files = ["foo", "bar"]
        args = self.parser.parse_args(["merge", *files, "-"])
        assert args.paths == files

    def test_merge_option_suite_name(self):
        args = self.parser.parse_args(["merge", "--suite-name", "foo", "_", "-"])
        assert args.suite_name == "foo"

    def test_merge_argument_output(self):
        args = self.parser.parse_args(["merge", "foo", "bar"])
        assert args.output == "bar"
