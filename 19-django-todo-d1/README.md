# Django TODO + D1 Example

[![Deploy to Cloudflare](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/cloudflare/python-workers-examples/tree/main/19-django-todo-d1)

This example uses Django with [django-cf](https://pypi.org/project/django-cf/) and a D1 database to serve a small TODO API under `/api/*`, plus a static frontend from `public/` served by [Workers Static Assets](https://developers.cloudflare.com/workers/static-assets/).

## How to Run

First ensure that `uv` is installed:
https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

Apply local migrations before development:

```sh
uv run pywrangler d1 migrations apply django-todo-d1 --local
```

Start the development server:

```sh
uv run pywrangler dev
```

Then open http://localhost:8787/ in your browser.

## Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/health/` | Health check |
| `GET /api/todos/` | List TODOs, newest first |
| `POST /api/todos/` | Create a TODO |
| `GET /api/todos/<id>/` | Fetch one TODO |
| `PATCH /api/todos/<id>/` | Partially update `title` and/or `completed` |
| `DELETE /api/todos/<id>/` | Delete a TODO |

## Notes

- Schema changes are managed by hand-written Wrangler D1 SQL migrations, not Django `manage.py migrate`.
