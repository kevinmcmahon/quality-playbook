"""Run unittest discovery for local tests via `python -m pytest`.

This is intentionally minimal and supports only the subset needed by this
repository's stdlib-only test suite.
"""

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path
from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("paths", nargs="*")
    known, _unknown = parser.parse_known_args(argv)

    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    paths = known.paths or ["."]
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            suite.addTests(loader.discover(str(path)))
        elif path.is_file() and path.suffix == ".py":
            suite.addTests(loader.discover(str(path.parent), pattern=path.name))
        else:
            suite.addTests(loader.discover(str(path)))

    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))