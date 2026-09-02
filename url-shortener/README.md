# URL Shortener Example

[![Deploy to Cloudflare](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/cloudflare/python-workers-examples/tree/main/url-shortener)

A Python Worker that creates short URLs backed by Workers KV.

## Configure Workers KV

Create a namespace, then replace the placeholder ID in `wrangler.jsonc` with the ID from the command output:

```sh
uv run pywrangler kv namespace create LINKS
```

## Run locally

First ensure that [uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) is installed. Then run:

```sh
uv run pywrangler dev
curl -X POST http://localhost:8787/shorten \
  -H 'content-type: application/json' \
  -d '{"url":"https://example.com/path"}'
```

The response includes a `code`, `short_url`, and the original `url`. Request the returned short URL to receive a `302` redirect. Deploy with `uv run pywrangler deploy`.

## API

| Endpoint | Description |
|---|---|
| `POST /shorten` | Store an absolute HTTP(S) URL and return a short URL. |
| `GET /<code>` | Redirect to the stored URL with status `302`. |
