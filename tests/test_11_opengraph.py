EXAMPLE = "11-opengraph"


def test_injects_opengraph_tags_into_the_proxied_page(worker):
    response = worker.get("/blog/python-workers-intro")
    assert 'property="og:title"' in response.text
    assert 'content="Blog Post: Python Workers Intro"' in response.text
    assert 'property="og:type" content="article"' in response.text
    assert 'name="twitter:card" content="summary_large_image"' in response.text
