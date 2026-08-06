EXAMPLE = "13-js-api-pygments/ts"


def test_renders_python_highlighted_by_the_python_worker(worker):
    response = worker.get()
    assert response.status_code == 200
    # Proves the RPC round trip: this markup can only come from Pygments
    # running inside the Python Worker behind the PYTHON_RPC service binding.
    assert 'class="highlight"' in response.text
    assert "linenos" in response.text
