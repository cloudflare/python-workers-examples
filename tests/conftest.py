import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[1]


def find_free_port():
    """Find an unused port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


@contextmanager
def pywrangler_dev_server(directory: str):
    """Context manager to start and stop pywrangler dev server."""
    port = find_free_port()

    process = subprocess.Popen(
        ["uv", "run", "pywrangler", "dev", "--port", str(port)],
        cwd=REPO_ROOT / directory,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Wait for server to be ready
    ready = False
    timeout = 30
    if "CI" in os.environ and directory.startswith("01"):
        # Starting the server the first time takes a really long time in CI.
        # TODO: Why does this happen?
        timeout = 300

    start_time = time.time()

    while not ready and time.time() - start_time < timeout:
        line = process.stdout.readline()
        if line:
            print(line.rstrip(), file=sys.stdout)  # Also print to stdout
            if "[wrangler:info] Ready on" in line:
                ready = True
                break
        time.sleep(0.1)

    if not ready:
        process.terminate()
        raise RuntimeError(f"Server failed to start within {timeout} seconds")

    try:
        yield port
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


@pytest.fixture
def dev_server(request):
    """Fixture that starts a dev server for the appropriate directory based on test name."""
    if request.node.get_closest_marker("skip") or request.node.get_closest_marker(
        "xfail"
    ):
        yield
        return

    test_name = request.node.name
    # Extract directory name from test name (e.g., "test_01_hello" -> "01-hello")
    dir_name = test_name.replace("test_", "").replace("_", "-")

    with pywrangler_dev_server(dir_name) as port:
        yield port
