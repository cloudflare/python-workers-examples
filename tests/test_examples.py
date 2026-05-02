import requests
import pytest
import subprocess
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


@pytest.mark.xfail(reason="Not working")
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


def test_17_r2(dev_server):
    port = dev_server
    base = f"http://localhost:{port}"

    response = requests.get(base)
    assert response.status_code == 200
    root = response.json()
    assert root["example"] == "Cloudflare R2 from a Python Worker"
    assert root["large_files"]["hvsc"]["key"] == "vsc/84/raw/HVSC_84-all-of-them.7z"
    assert root["large_files"]["shakespeare"]["key"] == "pg100-h.zip"
    assert root["large_files"]["shakespeare"]["source_url"] == "https://www.gutenberg.org/cache/epub/100/pg100-h.zip"

    payload = b"Hello from R2 and Python Workers!"
    response = requests.put(
        f"{base}/objects/hello.txt",
        data=payload,
        headers={
            "content-type": "text/plain",
            "cache-control": "public, max-age=60",
            "x-object-category": "test",
        },
    )
    assert response.status_code == 201
    stored = response.json()["stored"]
    assert stored["key"] == "hello.txt"
    assert stored["size"] == len(payload)
    assert stored["customMetadata"]["category"] == "test"

    response = requests.get(f"{base}/objects/hello.txt")
    assert response.status_code == 200
    assert response.content == payload
    assert response.headers["content-type"] == "text/plain"
    assert response.headers["etag"]

    response = requests.get(f"{base}/objects/hello.txt", headers={"range": "bytes=0-4"})
    assert response.status_code == 206
    assert response.content == b"Hello"
    assert response.headers["content-range"] == f"bytes 0-4/{len(payload)}"

    response = requests.head(f"{base}/objects/hello.txt")
    assert response.status_code == 200
    assert response.headers["content-length"] == str(len(payload))

    response = requests.get(f"{base}/objects?prefix=hello&include=customMetadata")
    assert response.status_code == 200
    assert [obj["key"] for obj in response.json()["objects"]] == ["hello.txt"]

    response = requests.get(f"{base}/objects?delimiter=/")
    assert response.status_code == 200
    assert "delimitedPrefixes" in response.json()

    # Multipart routes use ?key= so realistic R2 keys with slashes work.
    multipart_key = "multipart/slash-key.txt"
    response = requests.post(f"{base}/multipart", params={"key": multipart_key})
    assert response.status_code == 201
    upload_id = response.json()["uploadId"]

    response = requests.put(
        f"{base}/multipart/{upload_id}/1",
        params={"key": multipart_key},
        data=b"multipart body",
    )
    assert response.status_code == 200
    part = response.json()["part"]

    response = requests.post(
        f"{base}/multipart/{upload_id}/complete",
        params={"key": multipart_key},
        json={"parts": [part]},
    )
    assert response.status_code == 200
    assert response.json()["completed"]["key"] == multipart_key

    response = requests.get(f"{base}/objects/{multipart_key}")
    assert response.status_code == 200
    assert response.content == b"multipart body"

    response = requests.delete(
        f"{base}/objects",
        json={"keys": ["hello.txt", multipart_key]},
    )
    assert response.status_code == 200
    assert sorted(response.json()["deleted"]) == ["hello.txt", multipart_key]

    response = requests.get(f"{base}/objects/hello.txt")
    assert response.status_code == 404


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
