import json
import re
import subprocess
import uuid

import pytest
import requests
from conftest import REPO_ROOT


def test_hello(dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    assert response.text == "Hello world!"
    assert response.headers["content-type"] == "text/plain;charset=UTF-8"


def test_binding(dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    assert response.text == "baz"
    assert response.headers["content-type"] == "text/plain;charset=UTF-8"


def test_fastapi(dev_server):
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
        cwd=REPO_ROOT / "query-d1",
        check=True,
    )


@pytest.mark.xfail(reason="500 error, fixme")
def test_query_d1(init_db, dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    assert response.json()["author"] in [
        "Wikipedia",
        "Dominik Picheta",
        "Hood Chatham",
    ]


@pytest.mark.xfail(reason="Requires remote bindings")
def test_langchain(dev_server):
    pass


def test_assets(dev_server):
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


def test_durable_objects(dev_server):
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


def test_sync_http_clients(dev_server):
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


def test_url_shortener(dev_server):
    port = dev_server
    base = f"http://localhost:{port}"
    destination = "https://example.com/path"

    response = requests.post(f"{base}/shorten", json={"url": destination})
    assert response.status_code == 201
    shortened = response.json()
    assert len(shortened["code"]) == 8
    assert shortened["short_url"] == f"{base}/{shortened['code']}"
    assert shortened["url"] == destination

    response = requests.get(shortened["short_url"], allow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == destination

    response = requests.get(f"{base}/missing-code")
    assert response.status_code == 404
    assert response.json()["error"] == "not found"


def test_cron(dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    assert "Hello from Cron Worker" in response.text
    assert response.headers["content-type"] == "text/plain;charset=UTF-8"


@pytest.mark.xfail(reason="AI binding may not work in local dev")
def test_workers_ai(dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    # Check that response is JSON
    response_json = response.json()
    assert "output" in response_json or isinstance(response_json, dict)


@pytest.mark.xfail(reason="500 error, fixme")
def test_workflows(dev_server):
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


@pytest.fixture
def init_fastapi_todo_db():
    subprocess.run(
        [
            "uv",
            "run",
            "pywrangler",
            "d1",
            "execute",
            "todos",
            "--local",
            "--file",
            "db_init.sql",
        ],
        cwd=REPO_ROOT / "fastapi-todo",
        check=True,
    )


def assert_todo_backend(port):
    base = f"http://localhost:{port}/todos"

    # DELETE all todos
    response = requests.delete(base)
    assert response.status_code == 200

    # GET should return empty list
    response = requests.get(base)
    assert response.status_code == 200
    assert response.json() == []

    # POST a new todo
    response = requests.post(base, json={"title": "walk the dog"})
    assert response.status_code == 200
    todo = response.json()
    assert todo["title"] == "walk the dog"
    assert todo["completed"] is False
    assert "url" in todo
    todo_url = todo["url"]

    # GET the individual todo by its url
    response = requests.get(todo_url)
    assert response.status_code == 200
    assert response.json()["title"] == "walk the dog"

    # PATCH the todo
    response = requests.patch(
        todo_url, json={"title": "bathe the cat", "completed": True}
    )
    assert response.status_code == 200
    patched = response.json()
    assert patched["title"] == "bathe the cat"
    assert patched["completed"] is True

    # POST a todo with an order field
    response = requests.post(base, json={"title": "ordered todo", "order": 42})
    assert response.status_code == 200
    assert response.json()["order"] == 42

    # GET all todos should return 2
    response = requests.get(base)
    assert response.status_code == 200
    assert len(response.json()) == 2

    # DELETE individual todo
    response = requests.delete(todo_url)
    assert response.status_code == 200

    # GET all todos should return 1
    response = requests.get(base)
    assert response.status_code == 200
    assert len(response.json()) == 1

    # DELETE all
    response = requests.delete(base)
    assert response.status_code == 200
    response = requests.get(base)
    assert response.json() == []


def test_fastapi_todo(init_fastapi_todo_db, dev_server):
    assert_todo_backend(dev_server)


@pytest.fixture
def init_flask_todo_db():
    subprocess.run(
        [
            "uv",
            "run",
            "pywrangler",
            "d1",
            "execute",
            "todos",
            "--local",
            "--file",
            "db_init.sql",
        ],
        cwd=REPO_ROOT / "flask-todo",
        check=True,
    )


def test_flask_todo(init_flask_todo_db, dev_server):
    port = dev_server
    base = f"http://localhost:{port}/todos"

    # DELETE all todos
    response = requests.delete(base)
    assert response.status_code == 200

    # GET should return empty list
    response = requests.get(base)
    assert response.status_code == 200
    assert response.json() == []

    # POST a new todo
    response = requests.post(base, json={"title": "walk the dog"})
    assert response.status_code == 200
    todo = response.json()
    assert todo["title"] == "walk the dog"
    assert todo["completed"] is False
    assert "url" in todo
    todo_url = todo["url"]

    # GET the individual todo by its url
    response = requests.get(todo_url)
    assert response.status_code == 200
    assert response.json()["title"] == "walk the dog"

    # PATCH the todo
    response = requests.patch(
        todo_url, json={"title": "bathe the cat", "completed": True}
    )
    assert response.status_code == 200
    patched = response.json()
    assert patched["title"] == "bathe the cat"
    assert patched["completed"] is True

    # POST a todo with an order field
    response = requests.post(base, json={"title": "ordered todo", "order": 42})
    assert response.status_code == 200
    assert response.json()["order"] == 42

    # GET all todos should return 2
    response = requests.get(base)
    assert response.status_code == 200
    assert len(response.json()) == 2

    # DELETE individual todo
    response = requests.delete(todo_url)
    assert response.status_code == 200

    # GET all todos should return 1
    response = requests.get(base)
    assert response.status_code == 200
    assert len(response.json()) == 1

    # DELETE all
    response = requests.delete(base)
    assert response.status_code == 200
    response = requests.get(base)
    assert response.json() == []


def test_django(dev_server):
    port = dev_server
    response = requests.get(f"http://localhost:{port}")
    assert response.status_code == 200
    assert response.text == '{"message": "Hello from Django on Cloudflare Workers!"}'
    assert response.headers["content-type"] == "application/json"


@pytest.fixture
def init_django_todo_d1_db():
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
        cwd=REPO_ROOT / "django-todo-d1",
        check=True,
    )


def test_django_todo_d1(init_django_todo_d1_db, dev_server):
    assert_todo_backend(dev_server)


def csrf_token(session, base_url, path):
    response = session.get(f"{base_url}{path}")
    assert response.status_code == 200
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
    assert match is not None
    return match.group(1)


def test_django_markdown_r2(dev_server):
    base_url = f"http://localhost:{dev_server}"
    session = requests.Session()

    response = session.get(base_url)
    assert response.status_code == 200
    assert '<h1 id="articles-heading">Articles</h1>' in response.text
    assert (
        session.get(f"{base_url}/articles/missing-{uuid.uuid4().hex}/").status_code
        == 404
    )


@pytest.fixture
def init_mcp_incident_server_db():
    subprocess.run(
        [
            "uv",
            "run",
            "pywrangler",
            "d1",
            "migrations",
            "apply",
            "mcp-incidents",
            "--local",
        ],
        cwd=REPO_ROOT / "mcp-server",
        check=True,
    )


def mcp_json_response(response):
    if "text/event-stream" not in response.headers.get("content-type", ""):
        return response.json()

    messages = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert messages
    return messages[-1]


def test_mcp_incident_server(init_mcp_incident_server_db, dev_server):
    base = f"http://localhost:{dev_server}/mcp"
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": "2026-07-28",
    }
    meta = {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {},
    }

    def request(method, params, request_id):
        request_headers = {**headers, "Mcp-Method": method}
        if method == "tools/call":
            request_headers["Mcp-Name"] = params["name"]
        response = requests.post(
            base,
            headers=request_headers,
            json={
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": {"_meta": meta, **params},
            },
        )
        assert response.status_code == 200
        return response

    discovered = mcp_json_response(request("server/discover", {}, 1))
    assert "result" in discovered

    tools = mcp_json_response(request("tools/list", {}, 2))["result"]["tools"]
    assert {tool["name"] for tool in tools} == {
        "open_incident",
        "add_update",
        "list_open_incidents",
    }
