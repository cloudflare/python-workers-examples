# Django Markdown Blog + Durable Objects + R2

[![Deploy to Cloudflare](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/cloudflare/python-workers-examples/tree/main/django-markdown-r2)

A blog built with Django on Cloudflare Python Workers, using Durable Objects for database storage and R2 for image storage.

## Local setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer), then install the project dependencies and start the Worker:

```sh
uv sync
uv run pywrangler dev
```

Open http://localhost:8787/. Wrangler provisions the configured Durable Object locally and simulates the `IMAGES` R2 binding.

## Remote setup and deployment

Create an R2 bucket, update the `IMAGES` bucket name in `wrangler.jsonc`, and deploy:

```sh
uv run pywrangler deploy
```
