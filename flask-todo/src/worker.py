import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS
from pyodide.ffi import run_sync
from werkzeug.exceptions import HTTPException
from workers import wsgi

app = Flask(__name__)
# Preserve the field order used below rather than sorting keys alphabetically.
app.json.sort_keys = False

# The todobackend.com spec runner calls this Worker from another origin.
CORS(app, origins="*", send_wildcard=True, allow_headers="*", expose_headers="*")


@app.errorhandler(HTTPException)
def _json_error(err: HTTPException):
    """Render Werkzeug's HTTP errors as JSON instead of HTML."""
    return jsonify({"detail": err.name}), err.code


def _base_url() -> str:
    """Return the root URL for the todos collection."""
    return request.url_root.rstrip("/") + "/todos"


def _row_to_todo(row) -> dict:
    """Convert a D1 row into a todo dict with the absolute ``url`` field."""
    return {
        "id": row.id,
        "title": row.title,
        "completed": bool(row.completed),
        "order": row.order,
        "url": f"{_base_url()}/{row.id}",
    }


def _db():
    """Get the D1 database binding from the WSGI environ."""
    return request.environ["workers.env"].DB


@app.get("/todos")
def list_todos():
    results = run_sync(_db().prepare("SELECT * FROM todos").all())
    return jsonify([_row_to_todo(r) for r in results.results])


@app.post("/todos")
def create_todo():
    body = request.get_json(silent=True) or {}
    todo_id = str(uuid.uuid4())
    title = body.get("title", "")
    completed = 1 if body.get("completed", False) else 0
    order = body.get("order")

    run_sync(
        _db()
        .prepare(
            'INSERT INTO todos (id, title, completed, "order") VALUES (?, ?, ?, ?)'
        )
        .bind(todo_id, title, completed, order)
        .run()
    )

    row = run_sync(
        _db().prepare("SELECT * FROM todos WHERE id = ?").bind(todo_id).first()
    )

    return jsonify(_row_to_todo(row))


@app.delete("/todos")
def delete_all_todos():
    run_sync(_db().prepare("DELETE FROM todos").run())
    return jsonify([])


@app.get("/todos/<todo_id>")
def get_todo(todo_id: str):
    row = run_sync(
        _db().prepare("SELECT * FROM todos WHERE id = ?").bind(todo_id).first()
    )
    if row is None:
        return jsonify({"error": "not found"})
    return jsonify(_row_to_todo(row))


@app.patch("/todos/<todo_id>")
def update_todo(todo_id: str):
    body = request.get_json(silent=True) or {}
    sets = []
    values = []
    if "title" in body:
        sets.append("title = ?")
        values.append(body["title"])
    if "completed" in body:
        sets.append("completed = ?")
        values.append(1 if body["completed"] else 0)
    if "order" in body:
        sets.append('"order" = ?')
        values.append(body["order"])

    if sets:
        values.append(todo_id)
        run_sync(
            _db()
            .prepare(f"UPDATE todos SET {', '.join(sets)} WHERE id = ?")
            .bind(*values)
            .run()
        )

    row = run_sync(
        _db().prepare("SELECT * FROM todos WHERE id = ?").bind(todo_id).first()
    )
    if row is None:
        return jsonify({"error": "not found"})
    return jsonify(_row_to_todo(row))


@app.delete("/todos/<todo_id>")
def delete_todo(todo_id: str):
    run_sync(_db().prepare("DELETE FROM todos WHERE id = ?").bind(todo_id).run())
    return jsonify([])


Default = wsgi.entrypoint(app)
