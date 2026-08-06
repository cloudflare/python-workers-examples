EXAMPLE = "03-fastapi"


def test_index_describes_the_example(worker):
    response = worker.get()
    assert response.json() == {
        "message": (
            "This is an example of FastAPI with Jinja2 - "
            "go to /hi/<name> to see a template rendered"
        )
    }
    assert response.headers["content-type"] == "application/json"


def test_renders_a_jinja_template(worker):
    assert worker.get("/hi/Dominik").json() == {"message": "Hello, Dominik!"}


def test_reads_an_environment_variable(worker):
    assert worker.get("/env").json() == {
        "message": "Here is an example of getting an environment variable: My env var"
    }
