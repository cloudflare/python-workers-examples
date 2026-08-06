"""Root conftest.

Only the `--example` option lives here: pytest parses command line options
before it descends into `testpaths`, so the hook has to be registered from the
root directory. Everything else is in `tests/conftest.py`.
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--example",
        action="append",
        default=[],
        metavar="DIRECTORY",
        help="Limit the run to these example directories (repeatable).",
    )
