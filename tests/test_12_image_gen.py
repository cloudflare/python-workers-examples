import pytest

EXAMPLE = "12-image-gen"

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@pytest.mark.parametrize("path", ["/gradient", "/badge", "/placeholder", "/chart"])
def test_each_route_returns_a_cacheable_png(worker, path):
    response = worker.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "public, max-age=3600"
    assert response.content.startswith(PNG_MAGIC), f"{path} is not a PNG"


def test_index_is_html(worker):
    response = worker.get()
    assert response.headers["content-type"] == "text/html"
    assert "gradient" in response.text
