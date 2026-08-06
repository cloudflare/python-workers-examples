EXAMPLE = "02-binding"


def test_reads_back_the_value_it_wrote_to_kv(worker):
    response = worker.get()
    assert response.text == "baz"
    assert response.headers["content-type"] == "text/plain;charset=UTF-8"
