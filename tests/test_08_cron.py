EXAMPLE = "08-cron"


def test_fetch_handler_explains_the_example(worker):
    response = worker.get()
    assert "Hello from Cron Worker" in response.text
    assert response.headers["content-type"] == "text/plain;charset=UTF-8"


def test_scheduled_handler_accepts_a_triggered_event(worker):
    response = worker.get("/cdn-cgi/handler/scheduled", params={"cron": "* * * * *"})
    assert response.status_code == 200
