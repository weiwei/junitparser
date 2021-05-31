from argparse import ArgumentParser
from glob import iglob
from itertools import chain

from . import JUnitXml, version


def merge(paths, output):
    """Merge xml report."""
    result = JUnitXml()
    for path in paths:
        result += JUnitXml.fromfile(path)

    result.update_statistics()
    result.write(output, to_concole=output == "-")
    return 0


def _parser(prog_name=None):  # pragma: no cover
    """Create the CLI arg parser."""
    parser = ArgumentParser(description="Junitparser CLI helper.", prog=prog_name)

    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s " + version
    )

    command_parser = parser.add_subparsers(dest="command", help="command")
    command_parser.required = True

    # command: merge
    merge_parser = command_parser.add_parser(
        "merge", help="Merge Junit XML format reports with junitparser."
    )
    merge_parser.add_argument(
        "--glob",
        help="Treat original XML path(s) as glob(s).",
        dest="paths_are_globs",
        action="store_true",
        default=False,
    )
    merge_parser.add_argument("paths", nargs="+", help="Original XML path(s).")
    merge_parser.add_argument(
        "output", help='Merged XML Path, setting to "-" will output console'
    )

    return parser


def main(args=None, prog_name=None):
    """CLI's main runner."""
    args = args or _parser(prog_name=prog_name).parse_args()
    if args.command == "merge":
        return merge(
            chain.from_iterable(iglob(path) for path in args.paths)
            if args.paths_are_globs
            else args.paths,
            args.output,
        )
    return 255
