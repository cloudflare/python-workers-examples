"""Flask JSON API for the notes app, backed directly by D1."""

from asyncio import get_event_loop

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
# Preserve our own key ordering in JSON responses rather than sorting them.
app.json.sort_keys = False

MAX_TITLE_LEN = 200
MAX_BODY_LEN = 10_000
VALID_FILTERS = ("all", "active", "done")


class D1Error(RuntimeError):
    """A D1 query failed. Wraps the underlying error message."""


def get_db():
    """Return the D1 wrapper for the current request."""
    if "db" not in g:
        # Cache on g for the lifetime of the request
        g.db = request.environ["workers.env"].DB
    return g.db


def run_db(task):
    try:
        return get_event_loop().run_until_complete(task)
    except Exception as exc:
        # D1 surfaces SQL errors as JS exceptions; re-raise as a Python error so
        # we can register a custom error handler.
        raise D1Error(f"{exc}") from exc


# --------------------------------------------------------------------------
# Serialization / validation
# --------------------------------------------------------------------------


def serialize(row: dict) -> dict:
    """Convert a D1 row into the JSON shape the frontend expects."""
    return {
        "id": row["id"],
        "title": row["title"],
        "body": row["body"],
        # SQLite has no boolean type; `done` round-trips as 0/1.
        "done": bool(row["done"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


class ValidationError(ValueError):
    """Raised when a request payload is malformed."""


def _payload() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    return data


def _clean_title(value) -> str:
    if not isinstance(value, str):
        raise ValidationError("'title' must be a string.")
    title = value.strip()
    if not title:
        raise ValidationError("'title' must not be empty.")
    if len(title) > MAX_TITLE_LEN:
        raise ValidationError(f"'title' must be at most {MAX_TITLE_LEN} characters.")
    return title


def _clean_body(value) -> str:
    if not isinstance(value, str):
        raise ValidationError("'body' must be a string.")
    body = value.strip()
    if len(body) > MAX_BODY_LEN:
        raise ValidationError(f"'body' must be at most {MAX_BODY_LEN} characters.")
    return body


def _clean_done(value) -> int:
    if not isinstance(value, bool):
        raise ValidationError("'done' must be a boolean.")
    return int(value)


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------


@app.get("/api/notes")
def list_notes():
    """List notes, newest first, with optional status filter and search."""
    status = request.args.get("filter", "all")
    if status not in VALID_FILTERS:
        raise ValidationError(f"'filter' must be one of: {', '.join(VALID_FILTERS)}.")
    search = request.args.get("q", "").strip()

    # Tie-break on id so ordering is stable for notes created in the same second.
    sql = "SELECT * FROM notes {where} ORDER BY done ASC, created_at DESC, id DESC"
    where_clauses, params = [], []

    if status == "active":
        where_clauses.append("done = 0")
    elif status == "done":
        where_clauses.append("done = 1")

    if search:
        # Escape LIKE wildcards so a literal % or _ in the query is matched
        # literally. SQLite only honours the escape character when an explicit
        # ESCAPE clause is given.
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        where_clauses.append(r"(title LIKE ?1 ESCAPE '\' OR body LIKE ?1 ESCAPE '\')")
        params.append(f"%{escaped}%")

    # Every element of `where_clauses` is a hardcoded literal; the search term
    # itself travels in `params` and is bound to `?1`. `status` is only ever
    # compared against VALID_FILTERS, never concatenated into the SQL.
    if where_clauses:
        where = " WHERE " + " AND ".join(where_clauses)
    else:
        where = ""

    sql = sql.format(where=where)

    rows = run_db(get_db().prepare(sql).bind(*params).all())["results"]
    return jsonify({"notes": [serialize(dict(r)) for r in rows]})


@app.get("/api/notes/<int:note_id>")
def get_note(note_id: int):
    row = run_db(
        get_db().prepare("SELECT * FROM notes WHERE id = ?").bind(note_id).first()
    )
    if row is None:
        return jsonify({"error": "Note not found."}), 404
    return jsonify(serialize(row))


@app.post("/api/notes")
def create_note():
    data = _payload()
    if "title" not in data:
        raise ValidationError("'title' is required.")
    title = _clean_title(data["title"])
    body = _clean_body(data.get("body", ""))

    # RETURNING to insert and read the stored row in a single round trip.
    row = run_db(
        get_db()
        .prepare(
            "INSERT INTO notes (title, body) VALUES (?, ?) RETURNING *",
        )
        .bind(title, body)
        .first()
    )
    return jsonify(serialize(row)), 201


@app.patch("/api/notes/<int:note_id>")
def update_note(note_id: int):
    data = _payload()

    updates, params = [], []
    if "title" in data:
        updates.append("title = ?")
        params.append(_clean_title(data["title"]))
    if "body" in data:
        updates.append("body = ?")
        params.append(_clean_body(data["body"]))
    if "done" in data:
        updates.append("done = ?")
        params.append(_clean_done(data["done"]))

    if not updates:
        raise ValidationError("Provide at least one of: 'title', 'body', 'done'.")

    updates.append("updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')")
    params.append(note_id)

    # The f-string interpolates the updates fragments, every one of which is a
    # hardcoded literal from the branches above so this expands to one of seven
    # fixed statements. Values are not interpolated.
    row = run_db(
        get_db()
        .prepare(f"UPDATE notes SET {', '.join(updates)} WHERE id = ? RETURNING *")
        .bind(*params)
        .first()
    )
    if row is None:
        return jsonify({"error": "Note not found."}), 404
    return jsonify(serialize(row))


@app.delete("/api/notes/<int:note_id>")
def delete_note(note_id: int):
    meta = run_db(
        get_db().prepare("DELETE FROM notes WHERE id = ?").bind(note_id).run()
    )["meta"]
    if not meta.get("changes"):
        return jsonify({"error": "Note not found."}), 404
    return "", 204


@app.delete("/api/notes/delete_completed")
def delete_completed():
    """Bulk-delete every completed note."""
    meta = run_db(get_db().prepare("DELETE FROM notes WHERE done = 1").run())["meta"]
    return jsonify({"deleted": meta.get("changes", 0)})


@app.get("/api/health")
def health():
    """Confirms the Worker is up and the D1 binding actually responds."""
    run_db(get_db().prepare("SELECT 1 AS ok").first())
    return jsonify({"status": "ok"})


# --------------------------------------------------------------------------
# Error handling
# --------------------------------------------------------------------------


@app.errorhandler(ValidationError)
def handle_validation_error(exc: ValidationError):
    return jsonify({"error": str(exc)}), 400


@app.errorhandler(D1Error)
def handle_d1_error(exc: D1Error):
    app.logger.exception("D1 query failed")
    return jsonify({"error": "Database error.", "detail": str(exc)}), 500


@app.errorhandler(HTTPException)
def handle_http_error(exc: HTTPException):
    """Render Werkzeug's HTTP errors as JSON instead of HTML."""
    concise = {404: "Not found.", 405: "Method not allowed."}
    return jsonify({"error": concise.get(exc.code, exc.description)}), exc.code


@app.errorhandler(Exception)
def handle_unexpected(exc: Exception):
    app.logger.exception("Unhandled error")
    return jsonify({"error": "Internal server error."}), 500
