"""Synchronous D1 access for WSGI (Flask) code running on a Python Worker.

The D1 binding is a JavaScript object whose methods return promises. Flask is a
WSGI framework, so its view functions are plain synchronous Python and cannot
`await`. We bridge the two with `pyodide.ffi.run_sync`, which suspends the
Python stack until a JS promise settles, using JSPI (JavaScript Promise
Integration) stack switching.

`run_sync` only works while a JSPI suspender is on the stack. `workers.wsgi.fetch`
invokes the WSGI app from inside the Worker's async `fetch` handler, so that
condition holds for every request routed through `src/entry.py`.

The Workers SDK already converts D1's JS return values into Python objects:
`.all()` yields a mapping whose `results` key is a `list` of dict-like rows, and
`.first()` yields a dict-like row or `None`. No explicit `to_py()` is needed;
this module just normalizes them to plain `dict`s.
"""

from pyodide.ffi import run_sync


class D1Error(RuntimeError):
    """A D1 query failed. Wraps the underlying error message."""


class D1:
    """A thin synchronous wrapper around a D1 binding."""

    def __init__(self, binding):
        self._db = binding

    def _prepare(self, sql, params=()):
        stmt = self._db.prepare(sql)
        if params:
            # `bind` is variadic on the JS side. str/int/float/bool/None all
            # convert to D1-compatible values automatically.
            stmt = stmt.bind(*params)
        return stmt

    def _run_sync(self, promise, sql):
        try:
            return run_sync(promise)
        except Exception as exc:
            # D1 surfaces SQL errors as JS exceptions; re-raise as a Python
            # error the Flask handler can turn into a 500.
            raise D1Error(f"{exc} (query: {sql})") from exc

    def query(self, sql, params=()) -> list[dict]:
        """Run a SELECT and return all rows as a list of plain dicts."""
        result = self._run_sync(self._prepare(sql, params).all(), sql)
        return [dict(row) for row in result["results"]]

    def first(self, sql, params=()) -> dict | None:
        """Run a statement and return its first row as a dict, or None."""
        row = self._run_sync(self._prepare(sql, params).first(), sql)
        return dict(row) if row is not None else None

    def run(self, sql, params=()) -> dict:
        """Run a write statement and return its metadata.

        The returned dict includes `changes`, `last_row_id`, `rows_read` and
        `rows_written`.
        """
        result = self._run_sync(self._prepare(sql, params).run(), sql)
        return dict(result["meta"])
