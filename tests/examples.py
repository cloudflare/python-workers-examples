"""Registry of every example in this repository.

This is the single source of truth for both the pytest suite and the CI matrix.
Adding an example here is what makes CI test it -- see `test_registry.py`, which
fails if an example directory exists on disk but is missing from `EXAMPLES`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

REPO_ROOT = Path(__file__).parents[1]


class Lane(StrEnum):
    """Which CI job an example can run in."""

    OFFLINE = "offline"
    NETWORK = "network"
    CREDENTIALED = "credentialed"


@dataclass(frozen=True)
class Example:
    directory: str
    lane: Lane = Lane.OFFLINE
    smoke: tuple[tuple[str, int], ...] = (("/", 200),)
    setup: tuple[tuple[str, ...], ...] = ()
    configs: tuple[str, ...] = ()
    run_from: str | None = None

    @property
    def path(self) -> Path:
        return REPO_ROOT / self.directory

    @property
    def cwd(self) -> Path:
        return REPO_ROOT / (self.run_from or self.directory)

    @property
    def test_id(self) -> str:
        return self.directory


EXAMPLES: tuple[Example, ...] = (
    Example("01-hello"),
    Example("02-binding"),
    Example(
        "03-fastapi",
        smoke=(("/", 200), ("/hi/Dominik", 200), ("/env", 200)),
    ),
    Example(
        "04-query-d1",
        setup=(
            ("d1", "execute", "quotes", "--local", "--file", "db_init.sql", "--yes"),
        ),
    ),
    Example("05-langchain", lane=Lane.CREDENTIALED),
    Example(
        "06-assets",
        smoke=(
            ("/", 200),
            ("/image.svg", 200),
            ("/style.css", 200),
            ("/script.js", 200),
            ("/favicon.ico", 200),
            ("/painting.jpg", 200),
        ),
    ),
    # Smoke checks share a dev server with the tests below, so they must not
    # mutate state that another test asserts on.
    Example("07-durable-objects", smoke=(("/smoke-room/show", 200),)),
    Example("08-cron"),
    Example("09-workers-ai", lane=Lane.CREDENTIALED),
    Example("10-workflows", smoke=(("/", 200), ("/start", 200))),
    # Only `/` is checked here: this Worker proxies example.com and passes its
    # upstream status through, so every other path's status belongs to
    # example.com rather than to the example. The test asserts on tag injection.
    Example("11-opengraph", lane=Lane.NETWORK),
    Example(
        "12-image-gen",
        smoke=(
            ("/", 200),
            ("/gradient", 200),
            ("/badge", 200),
            ("/placeholder", 200),
            ("/chart", 200),
        ),
    ),
    Example("13-js-api-pygments/py"),
    # The TS client reaches the Python server over a service binding, so both
    # Workers must share one dev session. The first config becomes the primary
    # one serving `/`. Runs from `py/` because only it has the workers-py dev group.
    Example(
        "13-js-api-pygments/ts",
        run_from="13-js-api-pygments/py",
        configs=("../ts/wrangler.jsonc", "wrangler.jsonc"),
    ),
    Example(
        "14-websocket-stream-consumer",
        lane=Lane.NETWORK,
        smoke=(("/status", 200),),
    ),
    Example("15-chatroom", smoke=(("/", 200), ("/room/test", 400), ("/nope", 404))),
    Example(
        "16-sync-http-clients",
        lane=Lane.NETWORK,
        smoke=(("/", 200), ("/sync", 200), ("/nope", 404)),
    ),
    Example("17-dynamic-py-py"),
)

BY_DIRECTORY: dict[str, Example] = {e.directory: e for e in EXAMPLES}


def get(directory: str) -> Example:
    return BY_DIRECTORY[directory]


def in_lane(*lanes: Lane) -> tuple[Example, ...]:
    return tuple(e for e in EXAMPLES if e.lane in lanes)


def _main() -> None:
    """Emit the CI job matrix, so GitHub Actions and pytest cannot drift apart."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description=_main.__doc__)
    parser.add_argument(
        "--lane",
        action="append",
        default=[],
        choices=[lane.value for lane in Lane],
        help="Only include examples in this lane (repeatable, default: all).",
    )
    args = parser.parse_args()
    lanes = tuple(Lane(name) for name in args.lane) or tuple(Lane)

    json.dump(
        [
            {
                "directory": example.directory,
                "lane": example.lane.value,
                "run_from": example.run_from or example.directory,
            }
            for example in in_lane(*lanes)
        ],
        sys.stdout,
    )


if __name__ == "__main__":
    _main()
