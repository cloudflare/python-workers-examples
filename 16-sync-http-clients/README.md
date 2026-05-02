# Sync HTTP Clients Example

This example demonstrates outbound HTTP from a Python Worker using synchronous Python HTTP clients known to work in the current runtime:

- [`requests`](https://pypi.org/project/requests/)
- [`urllib3`](https://pypi.org/project/urllib3/)
- [`httpx.Client`](https://www.python-httpx.org/)

It intentionally calls their normal blocking-style APIs from inside the Worker handler.

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
curl http://localhost:8787/sync
```

You can also deploy with:

```sh
uv run pywrangler deploy
```

## Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Endpoint index |
| `GET /sync` | Fetch with `requests.get()`, `urllib3.PoolManager().request()`, and `httpx.Client` |
| `GET /all` | Alias for `/sync` |

## Notes

This example is limited to synchronous package-backed clients that work in Python Workers. It does not include stdlib raw-socket clients such as `urllib.request` or `http.client`.
