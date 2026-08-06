EXAMPLE = "16-sync-http-clients"


def test_every_sync_client_completes_its_request(worker):
    results = worker.get("/sync").json()["results"]
    assert [result["client"] for result in results] == [
        "requests",
        "urllib3",
        "httpx.Client",
    ]
    for result in results:
        assert result["status_code"] == 200
        assert result["ok"] is True
        assert result["saw_expected_text"] is True
