from __future__ import annotations

import re

import pytest
import requests

from examples import EXAMPLES, get

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
REQUEST_TIMEOUT = 60


def one(directory: str):
    """Bind a test to a single example instead of the whole registry."""
    return pytest.mark.parametrize(
        "dev_server", [pytest.param(get(directory), id=directory)], indirect=True
    )


def test_every_example_declares_smoke_checks():
    missing = [e.directory for e in EXAMPLES if not e.smoke]
    assert not missing, f"examples with no smoke checks: {missing}"


def test_smoke(dev_server, request):
    """Every route declared in the registry answers with its expected status."""
    example = request.node.callspec.params["dev_server"]
    for path, expected_status in example.smoke:
        response = requests.get(f"{dev_server}{path}", timeout=REQUEST_TIMEOUT)
        assert response.status_code == expected_status, (
            f"{example.directory} GET {path} -> {response.status_code} "
            f"(expected {expected_status}): {response.text[:300]}"
        )


@one("01-hello")
def test_01_hello(dev_server):
    response = requests.get(dev_server, timeout=REQUEST_TIMEOUT)
    assert response.text == "Hello world!"
    assert response.headers["content-type"] == "text/plain;charset=UTF-8"


@one("02-binding")
def test_02_binding_reads_back_what_it_wrote(dev_server):
    response = requests.get(dev_server, timeout=REQUEST_TIMEOUT)
    assert response.text == "baz"
    assert response.headers["content-type"] == "text/plain;charset=UTF-8"


@one("03-fastapi")
def test_03_fastapi_routes(dev_server):
    root = requests.get(dev_server, timeout=REQUEST_TIMEOUT)
    assert root.json() == {
        "message": (
            "This is an example of FastAPI with Jinja2 - "
            "go to /hi/<name> to see a template rendered"
        )
    }
    assert root.headers["content-type"] == "application/json"

    greeting = requests.get(f"{dev_server}/hi/Dominik", timeout=REQUEST_TIMEOUT)
    assert greeting.json() == {"message": "Hello, Dominik!"}

    env = requests.get(f"{dev_server}/env", timeout=REQUEST_TIMEOUT)
    assert env.json() == {
        "message": "Here is an example of getting an environment variable: My env var"
    }


@one("04-query-d1")
def test_04_query_d1_returns_a_seeded_quote(dev_server):
    response = requests.get(dev_server, timeout=REQUEST_TIMEOUT)
    body = response.json()
    assert body["author"] in {"Wikipedia", "Dominik Picheta", "Hood Chatham"}
    assert body["quote"]


@one("06-assets")
def test_06_assets_content_types(dev_server):
    expected = {
        "/": "text/html; charset=utf-8",
        "/image.svg": "image/svg+xml",
        "/style.css": "text/css; charset=utf-8",
        "/script.js": "text/javascript; charset=utf-8",
        "/favicon.ico": "image/vnd.microsoft.icon",
        "/painting.jpg": "image/jpeg",
    }
    for path, content_type in expected.items():
        response = requests.get(f"{dev_server}{path}", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        assert response.headers["content-type"] == content_type


@one("07-durable-objects")
def test_07_durable_objects_keep_state_per_room(dev_server):
    def get(path: str) -> str:
        return requests.get(f"{dev_server}{path}", timeout=REQUEST_TIMEOUT).text

    assert get("/state-room/show") == "No messages"
    assert get("/state-room/add/hi") == "Message sent"
    assert get("/state-room/show") == "hi"
    assert get("/other-room/show") == "No messages"


@one("08-cron")
def test_08_cron_fetch_handler(dev_server):
    response = requests.get(dev_server, timeout=REQUEST_TIMEOUT)
    assert "Hello from Cron Worker" in response.text
    assert response.headers["content-type"] == "text/plain;charset=UTF-8"


@one("08-cron")
def test_08_cron_scheduled_handler(dev_server):
    response = requests.get(
        f"{dev_server}/cdn-cgi/handler/scheduled",
        params={"cron": "* * * * *"},
        timeout=REQUEST_TIMEOUT,
    )
    assert response.status_code == 200


@one("10-workflows")
def test_10_workflows_starts_an_instance(dev_server):
    index = requests.get(dev_server, timeout=REQUEST_TIMEOUT)
    assert "/start" in index.text
    assert "/status" in index.text

    started = requests.get(f"{dev_server}/start", timeout=REQUEST_TIMEOUT)
    assert "workflow with ID:" in started.text
    workflow_id = started.text.split("ID:")[-1].strip()
    assert re.fullmatch(r"[0-9a-f-]{36}", workflow_id), workflow_id

    status = requests.get(f"{dev_server}/status/{workflow_id}", timeout=REQUEST_TIMEOUT)
    assert status.status_code == 200
    assert isinstance(status.json(), dict)


@one("12-image-gen")
def test_12_image_gen_returns_png_images(dev_server):
    for path in ("/gradient", "/badge", "/placeholder", "/chart"):
        response = requests.get(f"{dev_server}{path}", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.headers["cache-control"] == "public, max-age=3600"
        assert response.content.startswith(PNG_MAGIC), f"{path} is not a PNG"


@one("12-image-gen")
def test_12_image_gen_index_is_html(dev_server):
    response = requests.get(dev_server, timeout=REQUEST_TIMEOUT)
    assert response.headers["content-type"] == "text/html"
    assert "gradient" in response.text


@one("13-js-api-pygments/py")
def test_13_python_rpc_server_responds(dev_server):
    response = requests.get(dev_server, timeout=REQUEST_TIMEOUT)
    assert "Python RPC server is running" in response.text


@one("13-js-api-pygments/ts")
def test_13_typescript_client_renders_highlighted_python(dev_server):
    response = requests.get(dev_server, timeout=REQUEST_TIMEOUT)
    assert response.status_code == 200
    # Proves the RPC round trip: this markup can only come from Pygments
    # running inside the Python Worker behind the PYTHON_RPC service binding.
    assert 'class="highlight"' in response.text
    assert "linenos" in response.text


@one("15-chatroom")
def test_15_chatroom_http_routes(dev_server):
    index = requests.get(dev_server, timeout=REQUEST_TIMEOUT)
    assert index.headers["content-type"].startswith("text/html")

    without_upgrade = requests.get(f"{dev_server}/room/test", timeout=REQUEST_TIMEOUT)
    assert without_upgrade.status_code == 400
    assert "Expected WebSocket upgrade" in without_upgrade.text

    missing = requests.get(f"{dev_server}/nope", timeout=REQUEST_TIMEOUT)
    assert missing.status_code == 404


@one("17-dynamic-py-py")
def test_17_dynamically_loaded_worker(dev_server):
    response = requests.get(dev_server, timeout=REQUEST_TIMEOUT)
    assert response.text == "Hello from a dynamically-loaded Python Worker!"


@one("11-opengraph")
def test_11_opengraph_injects_meta_tags(dev_server):
    response = requests.get(
        f"{dev_server}/blog/python-workers-intro", timeout=REQUEST_TIMEOUT
    )
    assert 'property="og:title"' in response.text
    assert 'content="Blog Post: Python Workers Intro"' in response.text
    assert 'property="og:type" content="article"' in response.text
    assert 'name="twitter:card" content="summary_large_image"' in response.text


@one("16-sync-http-clients")
def test_16_sync_http_clients(dev_server):
    response = requests.get(f"{dev_server}/sync", timeout=REQUEST_TIMEOUT)
    results = response.json()["results"]
    assert [result["client"] for result in results] == [
        "requests",
        "urllib3",
        "httpx.Client",
    ]
    for result in results:
        assert result["status_code"] == 200
        assert result["ok"] is True
        assert result["saw_expected_text"] is True


@one("14-websocket-stream-consumer")
def test_14_websocket_stream_consumer_status(dev_server):
    response = requests.get(f"{dev_server}/status", timeout=REQUEST_TIMEOUT)
    assert response.status_code == 200
    assert "Firehose status:" in response.text
