# Django Todo Backend + D1 Example

[![Deploy to Cloudflare](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/cloudflare/python-workers-examples/tree/main/django-todo-d1)

This example uses Django with [django-cf](https://pypi.org/project/django-cf/) and a D1 database to implement the [Todo-Backend](https://todobackend.com) API. The Worker only serves the backend; use the existing Todo-Backend client as the frontend.

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

Then open the Todo-Backend client with the local API URL:

```
https://todobackend.com/client/index.html?http://localhost:8787/todos
```

You can also run the Todo-Backend specification against the Django implementation:

```
https://todobackend.com/specs/index.html?http://localhost:8787/todos
```

## How to deploy

Replace the `database_id` in `wrangler.jsonc` with your actual D1 database UUID.

Apply the migrations to the remote D1 database, then deploy the Worker:

```sh
uv run pywrangler d1 migrations apply django-todo-d1 --remote
uv run pywrangler deploy
```


## Endpoints

| Endpoint | Description |
|---|---|
| `GET /todos` | List all todos |
| `POST /todos` | Create a todo |
| `DELETE /todos` | Delete all todos |
| `GET /todos/<id>` | Fetch one todo |
| `PATCH /todos/<id>` | Partially update a todo |
| `DELETE /todos/<id>` | Delete a todo |

## Notes

- Schema changes are managed by hand-written Wrangler D1 SQL migrations, not Django `manage.py migrate`.
- Cross-origin requests are enabled so the hosted Todo-Backend client can call the Worker.
