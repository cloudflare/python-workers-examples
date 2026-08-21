import subprocess
from datetime import UTC, datetime

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


@pytest.mark.xfail(reason="500 error, fixme")
def test_04_query_d1(init_db, dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    assert response.json()["author"] in [
        "Wikipedia",
        "Dominik Picheta",
        "Hood Chatham",
    ]


@pytest.mark.xfail(reason="Requires remote bindings")
def test_05_langchain(dev_server):
    pass


def test_06_assets(dev_server):
    port = dev_server
    pairs = [
        ("", "text/html; charset=utf-8"),
        ("image.svg", "image/svg+xml"),
        ("style.css", "text/css; charset=utf-8"),
        ("script.js", "text/javascript; charset=utf-8"),
        ("favicon.ico", "image/vnd.microsoft.icon"),
        ("painting.jpg", "image/jpeg"),
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


def test_16_sync_http_clients(dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}/sync")
    assert response.status_code == 200

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


@pytest.mark.xfail(reason="500 error, fixme")
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


def test_18_django(dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    assert response.text == '{"message": "Hello from Django on Cloudflare Workers!"}'
    assert response.headers["content-type"] == "application/json"


@pytest.fixture
def init_19_django_todo_d1_db():
    subprocess.run(
        [
            "uv",
            "run",
            "pywrangler",
            "d1",
            "migrations",
            "apply",
            "django-todo-d1",
            "--local",
        ],
        cwd=REPO_ROOT / "19-django-todo-d1",
        check=True,
    )


def test_19_django_todo_d1(init_19_django_todo_d1_db, dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["content-type"] == "application/json"

    index_response = requests.get(f"http://localhost:{port}/")
    assert index_response.status_code == 200
    assert index_response.headers["content-type"].startswith("text/html")
    assert "Django TODO + D1" in index_response.text

    script_response = requests.get(f"http://localhost:{port}/app.js")
    assert script_response.status_code == 200
    assert "javascript" in script_response.headers["content-type"]

    style_response = requests.get(f"http://localhost:{port}/style.css")
    assert style_response.status_code == 200
    assert "text/css" in style_response.headers["content-type"]

    create_response = requests.post(
        f"http://localhost:{port}/api/todos/",
        json={"title": "Write Django TODO example"},
    )
    assert create_response.status_code == 201
    created_todo = create_response.json()["todo"]
    assert created_todo["title"] == "Write Django TODO example"
    assert created_todo["completed"] is False
    assert isinstance(created_todo["id"], int)
    assert created_todo["created_at"].endswith("+00:00")
    created_at = datetime.fromisoformat(created_todo["created_at"])
    assert created_at.tzinfo is not None
    assert created_at.astimezone(UTC).tzinfo == UTC

    list_response = requests.get(f"http://localhost:{port}/api/todos/")
    assert list_response.status_code == 200
    todos = list_response.json()["todos"]
    assert created_todo["id"] in {todo["id"] for todo in todos}

    detail_response = requests.get(
        f"http://localhost:{port}/api/todos/{created_todo['id']}/"
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["todo"]["title"] == "Write Django TODO example"

    blank_title_response = requests.post(
        f"http://localhost:{port}/api/todos/",
        json={"title": "   "},
    )
    assert blank_title_response.status_code == 400
    assert blank_title_response.json() == {
        "error": "The 'title' field cannot be blank."
    }

    wrong_completed_response = requests.patch(
        f"http://localhost:{port}/api/todos/{created_todo['id']}/",
        json={"completed": "yes"},
    )
    assert wrong_completed_response.status_code == 400
    assert wrong_completed_response.json() == {
        "error": "The 'completed' field must be a boolean."
    }

    patch_response = requests.patch(
        f"http://localhost:{port}/api/todos/{created_todo['id']}/",
        json={"title": "Ship Django TODO example", "completed": True},
    )
    assert patch_response.status_code == 200
    patched_todo = patch_response.json()["todo"]
    assert patched_todo["title"] == "Ship Django TODO example"
    assert patched_todo["completed"] is True

    delete_response = requests.delete(
        f"http://localhost:{port}/api/todos/{created_todo['id']}/"
    )
    assert delete_response.status_code == 204
    assert delete_response.text == ""

    missing_response = requests.get(
        f"http://localhost:{port}/api/todos/{created_todo['id']}/"
    )
    assert missing_response.status_code == 404
    assert missing_response.json() == {"error": "TODO not found."}
