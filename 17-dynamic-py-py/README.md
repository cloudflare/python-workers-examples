# 17-dynamic-py-py — Python Worker loads a Python Dynamic Worker

This example shows how a Python Worker can use the [Worker Loader](https://developers.cloudflare.com/dynamic-workers/) binding to dynamically load and execute another Python Worker at runtime.

The parent Python Worker keeps the source of the dynamic Worker as a string (for demonstration purposes — in a real application you would load it from KV, R2, or any other storage). Each request is forwarded to the dynamically-loaded Worker, which runs in its own isolated sandbox.

## Run it

```bash
uv run pywrangler dev
```

Then press `b` to open a browser, or:

```bash
curl http://localhost:8787/
```

You should see:

```
Hello from a dynamically-loaded Python Worker!
```

## How it works

The parent Worker declares a `worker_loaders` binding in `wrangler.jsonc`:

```jsonc
"worker_loaders": [
  { "binding": "LOADER" }
]
```

In `src/entry.py`, the parent calls `self.env.LOADER.get(id, callback)`. The callback returns a JS object describing the Worker to load — its `compatibilityDate`, `compatibilityFlags`, `mainModule`, and `modules`.

```python
worker = self.env.LOADER.get(
    "hello-python-v1",
    create_proxy(_worker_code),
)
return await worker.getEntrypoint().fetch(request)
```

The runtime caches loaded isolates by ID, so the callback typically only runs the first time a given `id` is seen. To load updated code, change the `id` (for example, `"hello-python-v2"`).

`create_proxy()` from `pyodide.ffi` is required to expose the Python callback to the JavaScript runtime. `to_js(..., dict_converter=Object.fromEntries)` converts the Python dict into a plain JS object so the loader receives the shape it expects.
