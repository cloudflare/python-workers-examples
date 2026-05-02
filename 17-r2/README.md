# R2 Object Storage Example

This example demonstrates how to use the [Cloudflare R2 Workers API](https://developers.cloudflare.com/r2/api/workers/workers-api-reference/) from a Python Worker.

It covers core R2 bucket operations:

- `put()` — upload an object from the request body
- `get()` — stream an object back to the client
- `head()` — read object metadata
- `delete()` — delete one key or a batch of keys
- `list()` — list objects with `prefix`, `limit`, `cursor`, `delimiter`, and `include`
- Ranged reads using the `Range` header
- Conditional `get()` / `put()` via HTTP conditional headers
- HTTP metadata and custom metadata
- Optional checksum headers for `put()`
- Storage class selection via `x-storage-class`
- Multipart upload with `createMultipartUpload()`, `resumeMultipartUpload()`, `uploadPart()`, `complete()`, and `abort()`

The example keeps binary payloads on the JavaScript side of the runtime where possible. Uploads pass the request `ReadableStream` directly into R2, and downloads pass the R2 object's `ReadableStream` directly into a JavaScript `Response`. This avoids unnecessary JS → Python → JS copies for large objects.

## Shared large-file fixtures

This example defines shared large-file fixtures for streaming demonstrations. These are read-only by convention: upload them out-of-band before using `/large-files/<name>`. The Worker streams them from R2 without reading them into Python memory. The generic `/objects/<key>` and `/multipart?key=<key>` routes still operate on any key you pass them, just like the R2 binding APIs.

| Fixture name | R2 key | Source URL | Used for |
|---|---|---|---|
| `hvsc` | `vsc/84/raw/HVSC_84-all-of-them.7z` | Upload out-of-band | Large binary archive streaming fixture |
| `shakespeare` | `pg100-h.zip` | `https://www.gutenberg.org/cache/epub/100/pg100-h.zip` | Large public ZIP streaming fixture |

## Setup

First ensure that `uv` is installed:
https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

Create the R2 bucket used by `wrangler.jsonc`:

```sh
uv run pywrangler r2 bucket create python-r2-example
```

For local development, run:

```sh
uv run pywrangler dev
```

You can also deploy with:

```sh
uv run pywrangler deploy
```

## Try it

Upload an object with metadata:

```sh
curl -X PUT http://localhost:8787/objects/hello.txt \
  -H 'content-type: text/plain' \
  -H 'cache-control: public, max-age=60' \
  -H 'x-object-category: demo' \
  --data 'Hello from R2 and Python Workers!'
```

Fetch it:

```sh
curl -i http://localhost:8787/objects/hello.txt
```

Fetch only a byte range:

```sh
curl -i http://localhost:8787/objects/hello.txt -H 'range: bytes=0-4'
```

Inspect metadata:

```sh
curl -I http://localhost:8787/objects/hello.txt
```

Use conditional reads or writes:

```sh
curl -i http://localhost:8787/objects/hello.txt -H 'if-none-match: "some-etag"'
curl -X PUT http://localhost:8787/objects/hello.txt -H 'if-match: "some-etag"' --data 'conditional write'
```

List objects:

```sh
curl 'http://localhost:8787/objects?prefix=hello&limit=10&include=httpMetadata,customMetadata'
curl 'http://localhost:8787/objects?delimiter=/'
```

Batch-delete objects:

```sh
curl -X DELETE http://localhost:8787/objects \
  -H 'content-type: application/json' \
  --data '{"keys":["hello.txt","other.txt"]}'
```

Check and stream shared large files:

```sh
# List shared large-file fixtures.
curl http://localhost:8787/large-files

# Verify that vsc/84/raw/HVSC_84-all-of-them.7z exists in the bucket.
curl http://localhost:8787/large-files/hvsc/check

# Stream the R2 object directly back to the client.
curl -o HVSC_84-all-of-them.7z http://localhost:8787/large-files/hvsc

# Verify and stream the Gutenberg ZIP fixture.
curl http://localhost:8787/large-files/shakespeare/check
curl -o pg100-h.zip http://localhost:8787/large-files/shakespeare

# Range requests work for large fixture objects too.
curl -i http://localhost:8787/large-files/hvsc -H 'range: bytes=0-1023'
```

The same objects are available through the generic object route:

```sh
curl -I http://localhost:8787/objects/vsc/84/raw/HVSC_84-all-of-them.7z
curl -I http://localhost:8787/objects/pg100-h.zip
```

Multipart upload flow for any key, including keys with slashes:

```sh
# 1. Create the multipart upload and note the uploadId.
curl -X POST 'http://localhost:8787/multipart?key=archives/big.bin'

# 2. Upload parts. Each response includes the partNumber and etag.
curl -X PUT 'http://localhost:8787/multipart/<uploadId>/1?key=archives/big.bin' --data-binary @part-1.bin
curl -X PUT 'http://localhost:8787/multipart/<uploadId>/2?key=archives/big.bin' --data-binary @part-2.bin

# 3. Complete with the uploaded part descriptors.
curl -X POST 'http://localhost:8787/multipart/<uploadId>/complete?key=archives/big.bin' \
  -H 'content-type: application/json' \
  --data '{"parts":[{"partNumber":1,"etag":"<etag-1>"},{"partNumber":2,"etag":"<etag-2>"}]}'

# Or abort the upload.
curl -X DELETE 'http://localhost:8787/multipart/<uploadId>?key=archives/big.bin'
```

## Python Worker notes

Cloudflare bindings are JavaScript objects exposed to Python through Pyodide. This example follows these Python Worker patterns:

- Convert Python dicts with `to_js(..., dict_converter=Object.fromEntries)` before passing them to R2 options.
- Treat JS `null` and `undefined` as missing values at the boundary.
- Do not read large R2 objects into Python bytes just to return them to the client; pass `obj.body` directly to `js.Response`.
- Use `request.js_object.body` when passing a request body directly to R2.
