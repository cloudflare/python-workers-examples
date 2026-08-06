EXAMPLE = "14-websocket-stream-consumer"


def test_reports_firehose_status(worker):
    response = worker.get("/status")
    assert response.status_code == 200
    assert "Firehose status:" in response.text
