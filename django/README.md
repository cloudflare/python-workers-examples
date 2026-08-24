# Django WSGI Example

[![Deploy to Cloudflare](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/cloudflare/python-workers-examples/tree/main/django)

This example runs a small, conventional Django project directly on Cloudflare Workers using Django's WSGI application.

## How to Run

First ensure that `uv` is installed:
https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

Run:

```sh
uv run pywrangler dev
```

Then try:

```sh
curl http://localhost:8787/
```

You should receive:

```json
{"message": "Hello from Django on Cloudflare Workers!"}
```

You can also deploy with:

```sh
uv run pywrangler deploy
```
