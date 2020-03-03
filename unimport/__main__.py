import argparse
import pathlib
import sys

from unimport import __version__
from unimport.session import Session

parser = argparse.ArgumentParser(
    description="Detect or remove unused Python imports."
)
exclusive_group = parser.add_mutually_exclusive_group(required=False)
parser.add_argument(
    "sources",
    default=".",
    nargs="*",
    help="files and folders to find the unused imports.",
    type=pathlib.Path,
)
parser.add_argument(
    "-c",
    "--config",
    default=".",
    help="read configuration from PATH.",
    metavar="PATH",
    type=pathlib.Path,
)
exclusive_group.add_argument(
    "-r",
    "--remove",
    action="store_true",
    help="remove unused imports automatically.",
)
exclusive_group.add_argument(
    "-p",
    "--permission",
    action="store_true",
    help="Refactor permission after see diff.",
)
parser.add_argument(
    "-d",
    "--diff",
    action="store_true",
    help="Prints a diff of all the changes unimport would make to a file.",
)
parser.add_argument(
    "--check",
    action="store_true",
    help="Prints which file the unused imports are in.",
)
parser.add_argument(
    "-s",
    "--star",
    action="store_true",
    help="Scan from x import * and offer suggestions.",
)
parser.add_argument(
    "-v",
    "--version",
    action="version",
    version=f"Unimport {__version__}",
    help="Prints version of unimport",
)


def print_if_exists(sequence):
    if sequence:
        print(*sequence, sep="\n")
        return True


def main(argv=None):
    namespace = parser.parse_args(argv)
    any_namespace = any([value for key, value in vars(namespace).items()][2: -2])
    if namespace.permission and not namespace.diff:
        namespace.diff = True
    session = Session(config_file=namespace.config)
    sources = []
    for source_path in namespace.sources:
        sources.extend(session._list_paths(source_path, "**/*.py"))
    for source_path in sources:
        if not any_namespace or namespace.check:
            scanner = session.scanner
            scanner.run_visit(source=session._read(source_path)[0])
            for imports in scanner.get_unused_imports():
                imports["path"] = str(source_path)
                print(imports)
                # print(f"lineno; {imports['lineno']}, name; {imports['name']}, path; {imports['path']}")
            if namespace.star:
                for star_import in scanner.from_import_star():
                    print(star_import)
            scanner.clear()
        if namespace.diff:
            exists_diff = print_if_exists(
                tuple(session.diff_file(source_path))
            )
            if namespace.permission and exists_diff:
                action = input(
                    f"Apply suggested changes to '{source_path}' [y/n/q] ? > "
                )
                if action == "q":
                    break
                elif action == "y":
                    namespace.remove = True
        if namespace.remove:
            session.refactor_file(source_path, apply=True)


if __name__ == "__main__":
    main(sys.argv[1:])
