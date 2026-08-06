EXAMPLE = "15-chatroom"


def test_index_serves_the_chat_page(worker):
    assert worker.get().headers["content-type"].startswith("text/html")


def test_room_rejects_a_plain_http_request(worker):
    response = worker.get("/room/test")
    assert response.status_code == 400
    assert "Expected WebSocket upgrade" in response.text


def test_unknown_path_is_not_found(worker):
    assert worker.get("/nope").status_code == 404
