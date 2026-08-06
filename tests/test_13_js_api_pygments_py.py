EXAMPLE = "13-js-api-pygments/py"


def test_rpc_server_reports_that_it_is_running(worker):
    assert "Python RPC server is running" in worker.get().text
