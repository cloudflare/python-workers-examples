from __future__ import annotations

import os
import signal
import socket
import subprocess
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import requests

from examples import BY_DIRECTORY, Example, Lane, get

PYWRANGLER = ("uv", "run", "pywrangler")
POLL_INTERVAL = 0.5
READY_TIMEOUT = 30
REQUEST_TIMEOUT = 60
# Generous because the first boot of an example downloads its Pyodide packages.
STARTUP_TIMEOUT = 180


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Worker:
    def __init__(self, example: Example, base_url: str) -> None:
        self.example = example
        self.base_url = base_url

    def get(self, path: str = "/", **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        return requests.get(f"{self.base_url}{path}", **kwargs)


class DevServer:
    def __init__(self, example: Example, state_dir: Path):
        self.example = example
        self.state_dir = state_dir
        self.port = _free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self._log_path = state_dir / "dev.log"
        self._log = self._log_path.open("w+")
        self._process: subprocess.Popen[bytes] | None = None

    def _run(self, *args: str) -> None:
        result = subprocess.run(
            [*PYWRANGLER, *args, "--persist-to", str(self.state_dir)],
            cwd=self.example.cwd,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.fail(
                f"`pywrangler {' '.join(args)}` failed for {self.example.directory} "
                f"(exit {result.returncode})\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )

    def start(self) -> None:
        for setup_args in self.example.setup:
            self._run(*setup_args)

        config_args: list[str] = []
        for config in self.example.configs:
            config_args += ["-c", config]

        self._process = subprocess.Popen(
            [
                *PYWRANGLER,
                "dev",
                *config_args,
                "--port",
                str(self.port),
                "--persist-to",
                str(self.state_dir),
            ],
            cwd=self.example.cwd,
            stdout=self._log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        self._await_ready()

    def _await_ready(self) -> None:
        deadline = time.monotonic() + STARTUP_TIMEOUT
        while time.monotonic() < deadline:
            if self._process is not None and self._process.poll() is not None:
                pytest.fail(
                    f"`pywrangler dev` for {self.example.directory} exited early with "
                    f"code {self._process.returncode}\n{self._read_log()}"
                )
            # Any HTTP response means the Worker is serving. Examples have no
            # shared health route, and some answer `/` with 400 or 404 by design,
            # so only a refused connection counts as "not ready yet".
            try:
                requests.get(self.base_url, timeout=READY_TIMEOUT)
                return
            except (requests.ConnectionError, requests.Timeout):
                time.sleep(POLL_INTERVAL)

        self.stop()
        pytest.fail(
            f"`pywrangler dev` for {self.example.directory} was not ready within "
            f"{STARTUP_TIMEOUT}s\n{self._read_log()}"
        )

    def _read_log(self, limit: int = 4000) -> str:
        self._log.flush()
        text = self._log_path.read_text(errors="replace")
        return f"--- dev server log (last {limit} chars) ---\n{text[-limit:]}"

    def stop(self) -> None:
        if self._process is not None and self._process.poll() is None:
            # `uv` spawns pywrangler, which spawns wrangler, which spawns
            # workerd -- and it is workerd that holds the port. Signalling only
            # the direct child would orphan the rest, so signal the whole group.
            self._signal_group(signal.SIGTERM)
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._signal_group(signal.SIGKILL)
                self._process.wait()
        self._log.close()

    def _signal_group(self, sig: int) -> None:
        if self._process is None:
            return
        try:
            os.killpg(os.getpgid(self._process.pid), sig)
        except ProcessLookupError:
            pass


@pytest.fixture(scope="session")
def _dev_servers() -> Iterator[dict[str, DevServer]]:
    servers: dict[str, DevServer] = {}
    try:
        yield servers
    finally:
        for server in servers.values():
            server.stop()


@pytest.fixture
def worker(
    request: pytest.FixtureRequest, _dev_servers: dict[str, DevServer]
) -> Worker:
    """HTTP client for the example this test module declares in `EXAMPLE`.

    Dev servers are booted once per session and reused, because a cold boot pays
    for a `pywrangler sync` plus a Pyodide package download.
    """
    target = _target_for(request)
    _require_preconditions(target)

    if target.directory not in _dev_servers:
        state_dir = Path(
            tempfile.mkdtemp(prefix=target.directory.replace("/", "-") + "-")
        )
        server = DevServer(target, state_dir)
        server.start()
        _dev_servers[target.directory] = server
    return Worker(target, _dev_servers[target.directory].base_url)


def _target_for(request: pytest.FixtureRequest) -> Example:
    requested = getattr(request, "param", None)
    if isinstance(requested, Example):
        return requested
    if isinstance(requested, str):
        return get(requested)
    return _declared_example(request.module)


def _declared_example(module: ModuleType) -> Example:
    directory = getattr(module, "EXAMPLE", None)
    if directory is None:
        raise pytest.UsageError(
            f"{module.__name__} uses the `worker` fixture but does not set "
            f"`EXAMPLE` to the example directory it tests"
        )
    if directory not in BY_DIRECTORY:
        raise pytest.UsageError(
            f"{module.__name__} sets EXAMPLE = {directory!r}, which is not in the "
            f"registry in tests/examples.py"
        )
    return BY_DIRECTORY[directory]


def _require_preconditions(target: Example) -> None:
    if target.lane is Lane.NETWORK and not _network_enabled():
        pytest.skip(
            f"{target.directory} needs internet access; set RUN_NETWORK_TESTS=1"
        )
    if target.lane is Lane.CREDENTIALED and not _credentials_available():
        message = (
            f"{target.directory} needs CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID"
        )
        # The nightly credentialed job sets REQUIRE_CREDENTIALS so that missing
        # secrets fail loudly there instead of silently reporting a green skip.
        if os.environ.get("REQUIRE_CREDENTIALS") == "1":
            pytest.fail(message)
        pytest.skip(message)


def _network_enabled() -> bool:
    return os.environ.get("RUN_NETWORK_TESTS") == "1"


def _credentials_available() -> bool:
    return bool(
        os.environ.get("CLOUDFLARE_API_TOKEN")
        and os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    requested = config.getoption("example")
    if not requested:
        return
    selected, deselected = [], []
    for item in items:
        directory = _item_directory(item)
        if directory is None or directory in requested:
            selected.append(item)
        else:
            deselected.append(item)
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected


def _item_directory(item: pytest.Item) -> str | None:
    params = getattr(item, "callspec", None)
    if params is not None:
        target = params.params.get("worker")
        if isinstance(target, Example):
            return target.directory
    directory = getattr(getattr(item, "module", None), "EXAMPLE", None)
    return directory if isinstance(directory, str) else None
