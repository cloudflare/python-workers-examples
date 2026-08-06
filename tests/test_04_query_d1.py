EXAMPLE = "04-query-d1"


def test_returns_a_quote_seeded_from_db_init_sql(worker):
    body = worker.get().json()
    assert body["author"] in {"Wikipedia", "Dominik Picheta", "Hood Chatham"}
    assert body["quote"]
