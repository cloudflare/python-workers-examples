import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from workers import WorkerEntrypoint

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


def _base_url(request: Request) -> str:
    """Return the root URL for the todos collection."""
    return str(request.base_url).rstrip("/") + "/todos"


def _row_to_todo(row, request: Request) -> dict:
    """Convert a D1 row into a todo dict with the absolute ``url`` field."""
    return {
        "id": row.id,
        "title": row.title,
        "completed": bool(row.completed),
        "order": row.order,
        "url": f"{_base_url(request)}/{row.id}",
    }


def _db(request: Request):
    """Get the D1 database binding from the ASGI scope."""
    return request.scope["env"].DB


@app.get("/todos")
async def list_todos(request: Request):
    results = await _db(request).prepare("SELECT * FROM todos").all()
    return [_row_to_todo(r, request) for r in results.results]


@app.post("/todos")
async def create_todo(request: Request):
    body = await request.json()
    todo_id = str(uuid.uuid4())
    title = body.get("title", "")
    completed = 1 if body.get("completed", False) else 0
    order = body.get("order")

    await (
        _db(request)
        .prepare(
            'INSERT INTO todos (id, title, completed, "order") VALUES (?, ?, ?, ?)'
        )
        .bind(todo_id, title, completed, order)
        .run()
    )

    row = (
        await _db(request)
        .prepare("SELECT * FROM todos WHERE id = ?")
        .bind(todo_id)
        .first()
    )

    return _row_to_todo(row, request)


@app.delete("/todos")
async def delete_all_todos(request: Request):
    await _db(request).prepare("DELETE FROM todos").run()
    return []


@app.get("/todos/{todo_id}")
async def get_todo(todo_id: str, request: Request):
    row = (
        await _db(request)
        .prepare("SELECT * FROM todos WHERE id = ?")
        .bind(todo_id)
        .first()
    )
    if row is None:
        return {"error": "not found"}
    return _row_to_todo(row, request)


@app.patch("/todos/{todo_id}")
async def update_todo(todo_id: str, request: Request):
    body = await request.json()
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
        await (
            _db(request)
            .prepare(f"UPDATE todos SET {', '.join(sets)} WHERE id = ?")
            .bind(*values)
            .run()
        )

    row = (
        await _db(request)
        .prepare("SELECT * FROM todos WHERE id = ?")
        .bind(todo_id)
        .first()
    )
    if row is None:
        return {"error": "not found"}
    return _row_to_todo(row, request)


@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str, request: Request):
    await _db(request).prepare("DELETE FROM todos WHERE id = ?").bind(todo_id).run()
    return []

import asgi
Default = asgi.entrypoint(app)
