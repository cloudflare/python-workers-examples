import pytest

EXAMPLE = "06-assets"

CONTENT_TYPES = {
    "/": "text/html; charset=utf-8",
    "/image.svg": "image/svg+xml",
    "/style.css": "text/css; charset=utf-8",
    "/script.js": "text/javascript; charset=utf-8",
    "/favicon.ico": "image/vnd.microsoft.icon",
    "/painting.jpg": "image/jpeg",
}


@pytest.mark.parametrize(
    ("path", "content_type"), CONTENT_TYPES.items(), ids=list(CONTENT_TYPES)
)
def test_serves_each_asset_with_its_content_type(worker, path, content_type):
    response = worker.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"] == content_type
