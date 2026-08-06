EXAMPLE = "01-hello"


def test_greets_the_world(worker):
    response = worker.get()
    assert response.text == "Hello world!"
    assert response.headers["content-type"] == "text/plain;charset=UTF-8"
