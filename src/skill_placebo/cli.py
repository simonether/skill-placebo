"""Command-line entry point. Subcommands are added as the runner lands (METHOD.md section 14)."""
import argparse
import sys

from . import __version__


def main(argv=None):
    ap = argparse.ArgumentParser(prog="skill-placebo", description=__doc__)
    ap.add_argument("--version", action="version", version=__version__)
    ap.parse_args(argv)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
