import re

EXAMPLE = "10-workflows"


def test_index_links_the_routes(worker):
    body = worker.get().text
    assert "/start" in body
    assert "/status" in body


def test_starts_an_instance_and_reports_its_status(worker):
    started = worker.get("/start")
    assert "workflow with ID:" in started.text

    workflow_id = started.text.split("ID:")[-1].strip()
    assert re.fullmatch(r"[0-9a-f-]{36}", workflow_id), workflow_id

    status = worker.get(f"/status/{workflow_id}")
    assert status.status_code == 200
    assert isinstance(status.json(), dict)
