import subprocess

import pytest
import requests
from conftest import REPO_ROOT


def test_01_hello(dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    assert response.text == "Hello world!"
    assert response.headers["content-type"] == "text/plain;charset=UTF-8"


def test_02_binding(dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    assert response.text == "baz"
    assert response.headers["content-type"] == "text/plain;charset=UTF-8"


def test_03_fastapi(dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    assert (
        response.text
        == '{"message":"This is an example of FastAPI with Jinja2 - go to /hi/<name> to see a template rendered"}'
    )
    assert response.headers["content-type"] == "application/json"
    response = requests.get(f"http://localhost:{port}/hi/Dominik")
    assert response.status_code == 200
    assert response.text == '{"message":"Hello, Dominik!"}'
    assert response.headers["content-type"] == "application/json"
    response = requests.get(f"http://localhost:{port}/env")
    assert (
        response.text
        == '{"message":"Here is an example of getting an environment variable: My env var"}'
    )
    assert response.headers["content-type"] == "application/json"


@pytest.fixture
def init_db():
    subprocess.run(
        [
            "uv",
            "run",
            "pywrangler",
            "d1",
            "execute",
            "quotes",
            "--local",
            "--file",
            "db_init.sql",
        ],
        cwd=REPO_ROOT / "04-query-d1",
        check=True,
    )


def test_04_query_d1(init_db, dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    assert response.json()["author"] in [
        "Wikipedia",
        "Dominik Picheta",
        "Hood Chatham",
    ]


@pytest.mark.xfail(reason="Not working")
def test_05_langchain(dev_server):
    pass


def test_06_assets(dev_server):
    port = dev_server
    pairs = [
        ("", "text/html"),
        ("image.svg", "image/svg+xml"),
        ("style.css", "text/css; charset=utf-8"),
        ("script.js", "text/javascript; charset=utf-8"),
        ("favicon.ico", "image/vnd.microsoft.icon"),
    ]

    for path, content_type in pairs:
        response = requests.get(f"http://localhost:{port}/{path}")
        assert response.status_code == 200
        assert response.headers["content-type"] == content_type


def test_07_durable_objects(dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}/room-1/show")
    assert response.status_code == 200
    assert response.text == "No messages"
    response = requests.get(f"http://localhost:{port}/room-1/add/hi")
    assert response.status_code == 200
    assert response.text == "Message sent"
    response = requests.get(f"http://localhost:{port}/room-1/show")
    assert response.status_code == 200
    assert response.text == "hi"
    response = requests.get(f"http://localhost:{port}/room-2/show")
    assert response.status_code == 200
    assert response.text == "No messages"


def test_08_cron(dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    assert "Hello from Cron Worker" in response.text
    assert response.headers["content-type"] == "text/plain;charset=UTF-8"


@pytest.mark.xfail(reason="AI binding may not work in local dev")
def test_09_workers_ai(dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    # Check that response is JSON
    response_json = response.json()
    assert "output" in response_json or isinstance(response_json, dict)


def test_10_workflows(dev_server):
    port = dev_server
    # Test default endpoint
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    assert "/start" in response.text
    assert "/status" in response.text

    # Test workflow start
    response = requests.get(f"http://localhost:{port}/start")
    assert response.status_code == 200
    assert "workflow with ID:" in response.text

    # Extract workflow ID from response
    workflow_id = response.text.split("ID: ")[-1].strip()

    # Test workflow status
    response = requests.get(f"http://localhost:{port}/status/{workflow_id}")
    assert response.status_code == 200
    # Check that response is JSON
    status = response.json()
    assert isinstance(status, dict)
