EXAMPLE = "07-durable-objects"


def test_each_room_keeps_its_own_messages(worker):
    assert worker.get("/state-room/show").text == "No messages"
    assert worker.get("/state-room/add/hi").text == "Message sent"
    assert worker.get("/state-room/show").text == "hi"
    assert worker.get("/other-room/show").text == "No messages"
