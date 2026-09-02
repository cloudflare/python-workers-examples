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
    article_id = uuid.uuid4().hex
    title = f"Safe Markdown {article_id}"
    slug = f"safe-markdown-{article_id}"

    response = session.get(base_url)
    assert response.status_code == 200
    assert '<h1 id="articles-heading">Articles</h1>' in response.text
    assert (
        response.text.count(
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2.1.1/css/pico.classless.min.css">'
        )
        == 1
    )
    assert (
        session.get(f"{base_url}/articles/missing-{uuid.uuid4().hex}/").status_code
        == 404
    )

    token = csrf_token(session, base_url, "/articles/new/")
    create_form = session.get(f"{base_url}/articles/new/")
    assert 'name="slug"' not in create_form.text
    response = session.post(
        f"{base_url}/articles/new/",
        data={
            "csrfmiddlewaretoken": token,
            "title": title,
            "body": "# Heading\n\n<script>alert('unsafe')</script>",
        },
        allow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"] == f"/articles/{slug}/"

    article_list = session.get(base_url)
    assert article_list.status_code == 200
    assert "<h1>Heading</h1>" in article_list.text
    assert "&lt;script&gt;" in article_list.text
    assert "&lt;/script&gt;" in article_list.text
    assert "<script>alert('unsafe')</script>" not in article_list.text

    response = session.get(f"{base_url}/articles/{slug}/")
    assert response.status_code == 200
    assert "<h1>Heading</h1>" in response.text
    assert "&lt;script&gt;alert('unsafe')&lt;/script&gt;" in response.text
    assert "<script>alert('unsafe')</script>" not in response.text

    token = csrf_token(session, base_url, "/articles/new/")
    duplicate = session.post(
        f"{base_url}/articles/new/",
        data={
            "csrfmiddlewaretoken": token,
            "title": title,
            "body": "Duplicate slug",
        },
        allow_redirects=False,
    )
    assert duplicate.status_code == 302
    assert duplicate.headers["Location"] == f"/articles/{slug}-2/"

    image_id = uuid.uuid4().hex
    image_slug = f"image-article-{image_id}"
    token = csrf_token(session, base_url, "/articles/new/")
    image_bytes = b"GIF87a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    response = session.post(
        f"{base_url}/articles/new/",
        data={
            "csrfmiddlewaretoken": token,
            "title": f"Image article {image_id}",
            "body": "An image.",
        },
        files={"image": ("pixel.gif", image_bytes, "image/gif")},
        allow_redirects=False,
    )
    assert response.status_code == 302

    detail = session.get(f"{base_url}/articles/{image_slug}/")
    assert detail.status_code == 200
    image_match = re.search(
        rf'<img src="([^"]+)" alt="Illustration for Image article {image_id}">',
        detail.text,
    )
    assert image_match is not None
    image = session.get(f"{base_url}{image_match.group(1)}")
    assert image.status_code == 200
    assert image.content == image_bytes
    assert image.headers["Content-Type"] == "image/gif"
    assert image.headers["Content-Disposition"] == "inline"
    assert image.headers["X-Content-Type-Options"] == "nosniff"
    assert session.get(f"{base_url}/media/images/missing.gif").status_code == 404

    token = csrf_token(session, base_url, f"/articles/{slug}/edit/")
    edit_form = session.get(f"{base_url}/articles/{slug}/edit/")
    assert 'name="slug"' not in edit_form.text
    response = session.post(
        f"{base_url}/articles/{slug}/edit/",
        data={
            "csrfmiddlewaretoken": token,
            "title": "Updated article",
            "body": "Updated body",
        },
        allow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"] == f"/articles/{slug}/"
    updated = session.get(f"{base_url}/articles/{slug}/")
    assert updated.status_code == 200
    assert "Updated article" in updated.text
    assert "Updated body" in updated.text
