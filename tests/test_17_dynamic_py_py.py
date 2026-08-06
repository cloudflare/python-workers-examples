EXAMPLE = "17-dynamic-py-py"


def test_runs_a_worker_loaded_at_runtime(worker):
    assert worker.get().text == "Hello from a dynamically-loaded Python Worker!"
