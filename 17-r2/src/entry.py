from urllib.parse import unquote

from js import Headers, Object, Response as JsResponse, URL
from pyodide.ffi import jsnull, to_js
from workers import Response, WorkerEntrypoint


BUCKET_BINDING = "BUCKET"
LARGE_FILES = {
    "hvsc": {
        "key": "vsc/84/raw/HVSC_84-all-of-them.7z",
        "source_url": None,
        "description": "HVSC 84 archive fixture",
    },
    "shakespeare": {
        "key": "pg100-h.zip",
        "source_url": "https://www.gutenberg.org/cache/epub/100/pg100-h.zip",
        "description": "Project Gutenberg Shakespeare ZIP fixture",
    },
}

CHECKSUM_HEADERS = {
    "x-content-md5": "md5",
    "x-content-sha1": "sha1",
    "x-content-sha256": "sha256",
    "x-content-sha384": "sha384",
    "x-content-sha512": "sha512",
}
CONDITIONAL_HEADERS = [
    "if-match",
    "if-none-match",
    "if-modified-since",
    "if-unmodified-since",
]


def to_js_object(value):
    """Convert Python dicts to plain JS Objects, not JS Maps."""
    return to_js(value, dict_converter=Object.fromEntries)


def is_missing(value):
    """True for JS null or undefined values crossing into Python."""
    if value is None or value is jsnull:
        return True
    return (
        str(type(value)) == "<class 'pyodide.ffi.JsProxy'>"
        and str(value) == "undefined"
    )


def json_response(data, status=200):
    return Response.json(data, status=status)


def get_query_param(url, name, default=None):
    value = url.searchParams.get(name)
    return default if is_missing(value) else str(value)


def require_key(url):
    key = get_query_param(url, "key")
    if not key:
        return None, json_response({"error": "missing key query parameter"}, status=400)
    return key, None


def public_large_files():
    return {
        name: {
            "key": info["key"],
            "source_url": info["source_url"],
            "description": info["description"],
            "read": f"GET /large-files/{name}",
            "head": f"HEAD /large-files/{name}",
            "check": f"GET /large-files/{name}/check",
        }
        for name, info in LARGE_FILES.items()
    }


def large_file_by_name(name):
    return LARGE_FILES.get(name)


def maybe_conditional_headers(request):
    """Return request headers for R2 onlyIf when conditional headers are present."""
    for header in CONDITIONAL_HEADERS:
        if request.headers.get(header):
            return request.js_object.headers
    return None


def r2_object_summary(obj):
    """Convert an R2 object/head result into JSON-safe Python data."""
    if is_missing(obj):
        return None

    custom_metadata = getattr(obj, "customMetadata", None)
    if custom_metadata is not None and hasattr(custom_metadata, "to_py"):
        custom_metadata = custom_metadata.to_py()
    elif is_missing(custom_metadata):
        custom_metadata = {}

    http_metadata = getattr(obj, "httpMetadata", None)
    if http_metadata is not None and hasattr(http_metadata, "to_py"):
        http_metadata = http_metadata.to_py()
    elif is_missing(http_metadata):
        http_metadata = {}

    checksums_proxy = getattr(obj, "checksums", None)
    checksums = {}
    if not is_missing(checksums_proxy):
        for name in ("md5", "sha1", "sha256", "sha384", "sha512"):
            checksum = getattr(checksums_proxy, name, None)
            if not is_missing(checksum):
                checksums[name] = str(checksum)

    uploaded = getattr(obj, "uploaded", None)

    return {
        "key": str(obj.key),
        "version": str(getattr(obj, "version", "")),
        "size": int(obj.size),
        "etag": str(obj.etag),
        "httpEtag": str(getattr(obj, "httpEtag", "")),
        "uploaded": str(uploaded) if not is_missing(uploaded) else None,
        "httpMetadata": http_metadata,
        "customMetadata": custom_metadata,
        "checksums": checksums,
        "storageClass": None
        if is_missing(getattr(obj, "storageClass", None))
        else str(obj.storageClass),
    }


def object_options_from_request(request, include_checksums=False):
    """Build R2 put/multipart options from request headers."""
    http_metadata = {}
    content_type = request.headers.get("content-type")
    cache_control = request.headers.get("cache-control")
    content_disposition = request.headers.get("content-disposition")
    content_encoding = request.headers.get("content-encoding")
    content_language = request.headers.get("content-language")

    if content_type:
        http_metadata["contentType"] = content_type
    if cache_control:
        http_metadata["cacheControl"] = cache_control
    if content_disposition:
        http_metadata["contentDisposition"] = content_disposition
    if content_encoding:
        http_metadata["contentEncoding"] = content_encoding
    if content_language:
        http_metadata["contentLanguage"] = content_language

    custom_metadata = {}
    category = request.headers.get("x-object-category")
    author = request.headers.get("x-object-author")
    if category:
        custom_metadata["category"] = category
    if author:
        custom_metadata["author"] = author

    options = {}
    if http_metadata:
        options["httpMetadata"] = http_metadata
    if custom_metadata:
        options["customMetadata"] = custom_metadata

    storage_class = request.headers.get("x-storage-class")
    if storage_class:
        options["storageClass"] = storage_class

    only_if = maybe_conditional_headers(request)
    if only_if is not None:
        options["onlyIf"] = only_if

    if include_checksums:
        checksum_count = 0
        for header, option_name in CHECKSUM_HEADERS.items():
            value = request.headers.get(header)
            if value:
                checksum_count += 1
                options[option_name] = value
        if checksum_count > 1:
            return None, json_response(
                {"error": "R2 accepts only one checksum algorithm per put()"},
                status=400,
            )

    return (to_js_object(options) if options else None), None


def range_options_from_header(range_header):
    """Parse a single HTTP Range header into R2 get options.

    Supports bytes=start-end, bytes=start-, and bytes=-suffix.
    """
    if not range_header:
        return None, None
    if not range_header.startswith("bytes="):
        return None, json_response(
            {"error": "only bytes ranges are supported"}, status=400
        )

    spec = range_header[len("bytes=") :].strip()
    if "," in spec or "-" not in spec:
        return None, json_response(
            {"error": "only a single byte range is supported"}, status=400
        )

    start, end = spec.split("-", 1)
    try:
        if start == "":
            suffix = int(end)
            if suffix < 0:
                raise ValueError
            return {"range": {"suffix": suffix}}, None
        offset = int(start)
        if offset < 0:
            raise ValueError
        if end == "":
            return {"range": {"offset": offset}}, None
        end_number = int(end)
        if end_number < offset:
            return None, json_response(
                {"error": "range end must be >= start"}, status=400
            )
        return {"range": {"offset": offset, "length": end_number - offset + 1}}, None
    except ValueError:
        return None, json_response({"error": "invalid range"}, status=400)


def get_options_from_request(request):
    options, error = range_options_from_header(request.headers.get("range"))
    if error:
        return None, error
    options = options or {}

    only_if = maybe_conditional_headers(request)
    if only_if is not None:
        options["onlyIf"] = only_if

    return (to_js_object(options) if options else None), None


def object_headers(obj):
    """Build response headers from R2 HTTP metadata."""
    headers = Headers.new()
    obj.writeHttpMetadata(headers)
    headers.set("etag", obj.httpEtag)
    headers.set("accept-ranges", "bytes")
    headers.set("x-r2-key", obj.key)
    return headers


def object_response(obj, is_range=False):
    """Return an R2 object body without copying it through Python memory."""
    if is_missing(getattr(obj, "body", None)):
        return json_response(
            {
                "error": "precondition failed; R2 returned object metadata without a body",
                "object": r2_object_summary(obj),
            },
            status=412,
        )

    headers = object_headers(obj)
    status = 200
    if is_range:
        status = 206
        obj_range = getattr(obj, "range", None)
        if not is_missing(obj_range):
            offset = int(obj_range.offset)
            length = int(obj_range.length)
            headers.set("content-length", str(length))
            headers.set(
                "content-range", f"bytes {offset}-{offset + length - 1}/{int(obj.size)}"
            )

    return JsResponse.new(
        obj.body, to_js_object({"status": status, "headers": headers})
    )


def head_response(obj):
    """Return metadata for an R2 object using the R2 head() result."""
    headers = object_headers(obj)
    headers.set("content-length", str(int(obj.size)))
    return JsResponse.new(None, to_js_object({"status": 200, "headers": headers}))


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = URL.new(request.url)
        path = str(url.pathname)
        method = str(request.method).upper()

        if method == "OPTIONS":
            return Response(
                None,
                status=204,
                headers={"allow": "GET, HEAD, PUT, POST, DELETE, OPTIONS"},
            )

        if path == "/":
            return json_response(
                {
                    "example": "Cloudflare R2 from a Python Worker",
                    "binding": BUCKET_BINDING,
                    "large_files": public_large_files(),
                    "endpoints": {
                        "PUT /objects/<key>": "Store request body in R2 with metadata, conditionals, checksum, and storage class options",
                        "GET /objects/<key>": "Stream an R2 object back to the client without copying through Python",
                        "GET /objects/<key> with Range": "Serve a byte range using R2 range reads",
                        "HEAD /objects/<key>": "Read object metadata with R2 head()",
                        "DELETE /objects/<key>": "Delete one object",
                        "DELETE /objects": "Batch-delete up to 1000 keys from a JSON body",
                        "GET /objects?prefix=&limit=&cursor=&delimiter=&include=": "List objects with pagination and optional metadata",
                        "GET /large-files": "List shared large-file fixtures used by this and future examples",
                        "GET /large-files/<name>": "Stream a shared large-file fixture directly from R2",
                        "HEAD /large-files/<name>": "Read shared large-file fixture metadata",
                        "GET /large-files/<name>/check": "Check that a shared large-file fixture exists",
                        "POST /multipart?key=<key>": "Create a multipart upload for any R2 key, including keys with slashes",
                        "PUT /multipart/<uploadId>/<partNumber>?key=<key>": "Upload one multipart part",
                        "POST /multipart/<uploadId>/complete?key=<key>": "Complete a multipart upload",
                        "DELETE /multipart/<uploadId>?key=<key>": "Abort a multipart upload",
                    },
                    "metadata_headers": [
                        "content-type",
                        "cache-control",
                        "content-disposition",
                        "content-encoding",
                        "content-language",
                        "x-object-category",
                        "x-object-author",
                        "x-storage-class",
                    ],
                    "conditional_headers": CONDITIONAL_HEADERS,
                    "checksum_headers": list(CHECKSUM_HEADERS.keys()),
                }
            )

        if path == "/objects" and method == "GET":
            return await self.list_objects(url)
        if path == "/objects" and method == "DELETE":
            return await self.delete_objects(request)

        if path == "/large-files" and method == "GET":
            return json_response({"large_files": public_large_files()})

        if path.startswith("/large-files/"):
            return await self.handle_large_file(path, method, request)

        if path.startswith("/multipart"):
            return await self.handle_multipart(request, url, path, method)

        if path.startswith("/objects/"):
            key = unquote(path[len("/objects/") :])
            if not key:
                return json_response({"error": "missing object key"}, status=400)

            if method == "PUT":
                return await self.put_object(request, key)
            if method in ("GET", "HEAD"):
                return await self.get_object(request, key, method)
            if method == "DELETE":
                await self.env.BUCKET.delete(key)
                return json_response({"deleted": [key]})

            return json_response({"error": f"method {method} not allowed"}, status=405)

        return json_response({"error": "not found"}, status=404)

    async def handle_large_file(self, path, method, request):
        """Read shared large-file fixtures without mutating them."""
        suffix = path[len("/large-files/") :].strip("/")
        is_check = suffix.endswith("/check")
        name = suffix[: -len("/check")].strip("/") if is_check else suffix
        info = large_file_by_name(name)
        if info is None:
            return json_response(
                {
                    "error": "unknown large file fixture",
                    "name": name,
                    "available": list(LARGE_FILES.keys()),
                },
                status=404,
            )

        if is_check:
            if method != "GET":
                return json_response(
                    {"error": f"method {method} not allowed"}, status=405
                )
            return await self.check_large_file(name, info)

        if method not in ("GET", "HEAD"):
            return json_response({"error": f"method {method} not allowed"}, status=405)
        return await self.get_object(request, info["key"], method)

    async def check_large_file(self, name, info):
        """Verify a shared large-file fixture exists without mutating it."""
        obj = await self.env.BUCKET.head(info["key"])
        if is_missing(obj):
            return json_response(
                {
                    "exists": False,
                    "name": name,
                    "key": info["key"],
                    "source_url": info["source_url"],
                    "message": "Large-file fixture is not present in this R2 bucket. Upload it out-of-band before using this route.",
                },
                status=404,
            )
        return json_response(
            {
                "exists": True,
                "name": name,
                "source_url": info["source_url"],
                "object": r2_object_summary(obj),
            }
        )

    async def put_object(self, request, key):
        options, error = object_options_from_request(request, include_checksums=True)
        if error:
            return error

        # Pass the raw JavaScript ReadableStream directly to R2.  This avoids
        # converting request bytes into Python, which is important for binary
        # objects and large uploads.
        body = request.js_object.body
        if options is None:
            obj = await self.env.BUCKET.put(key, body)
        else:
            obj = await self.env.BUCKET.put(key, body, options)

        if is_missing(obj):
            return json_response(
                {"stored": False, "key": key, "reason": "put precondition failed"},
                status=412,
            )
        return json_response({"stored": r2_object_summary(obj)}, status=201)

    async def get_object(self, request, key, method):
        if method == "HEAD":
            obj = await self.env.BUCKET.head(key)
            if is_missing(obj):
                return json_response({"error": "not found", "key": key}, status=404)
            return head_response(obj)

        get_options, error = get_options_from_request(request)
        if error:
            return error
        if get_options is None:
            obj = await self.env.BUCKET.get(key)
        else:
            obj = await self.env.BUCKET.get(key, get_options)

        if is_missing(obj):
            return json_response({"error": "not found", "key": key}, status=404)

        return object_response(obj, is_range=request.headers.get("range") is not None)

    async def delete_objects(self, request):
        body = await request.json()
        data = body.to_py() if hasattr(body, "to_py") else body
        keys = data.get("keys") if isinstance(data, dict) else None
        if not isinstance(keys, list) or not keys:
            return json_response(
                {"error": "body must be JSON like {'keys': ['a', 'b']}"}, status=400
            )
        if len(keys) > 1000:
            return json_response(
                {"error": "R2 delete() accepts at most 1000 keys"}, status=400
            )

        await self.env.BUCKET.delete(to_js(keys))
        return json_response({"deleted": keys})

    async def handle_multipart(self, request, url, path, method):
        key, error = require_key(url)
        if error:
            return error

        parts = [part for part in path[len("/multipart") :].split("/") if part]

        if method == "POST" and not parts:
            options, error = object_options_from_request(request)
            if error:
                return error
            if options is None:
                upload = await self.env.BUCKET.createMultipartUpload(key)
            else:
                upload = await self.env.BUCKET.createMultipartUpload(key, options)
            return json_response(
                {"key": str(upload.key), "uploadId": str(upload.uploadId)}, status=201
            )

        if not parts:
            return json_response({"error": "missing uploadId"}, status=400)

        upload_id = unquote(parts[0])
        upload = self.env.BUCKET.resumeMultipartUpload(key, upload_id)

        if method == "PUT" and len(parts) == 2:
            try:
                part_number = int(parts[1])
            except ValueError:
                return json_response(
                    {"error": "partNumber must be an integer"}, status=400
                )

            options, error = object_options_from_request(request)
            if error:
                return error
            if options is None:
                uploaded_part = await upload.uploadPart(
                    part_number, request.js_object.body
                )
            else:
                uploaded_part = await upload.uploadPart(
                    part_number, request.js_object.body, options
                )
            return json_response(
                {
                    "key": key,
                    "uploadId": upload_id,
                    "part": {
                        "partNumber": int(uploaded_part.partNumber),
                        "etag": str(uploaded_part.etag),
                    },
                }
            )

        if method == "POST" and len(parts) == 2 and parts[1] == "complete":
            body = await request.json()
            data = body.to_py() if hasattr(body, "to_py") else body
            completed = await upload.complete(to_js_object(data.get("parts", [])))
            return json_response({"completed": r2_object_summary(completed)})

        if method == "DELETE" and len(parts) == 1:
            await upload.abort()
            return json_response({"aborted": {"key": key, "uploadId": upload_id}})

        return json_response({"error": "multipart route not found"}, status=404)

    async def list_objects(self, url):
        options = {}
        prefix = get_query_param(url, "prefix")
        cursor = get_query_param(url, "cursor")
        limit = get_query_param(url, "limit")
        delimiter = get_query_param(url, "delimiter")
        include = get_query_param(url, "include")

        if prefix:
            options["prefix"] = prefix
        if cursor:
            options["cursor"] = cursor
        if limit:
            try:
                parsed_limit = int(limit)
            except ValueError:
                return json_response({"error": "limit must be an integer"}, status=400)
            if parsed_limit < 1 or parsed_limit > 1000:
                return json_response(
                    {"error": "limit must be between 1 and 1000"}, status=400
                )
            options["limit"] = parsed_limit
        if delimiter:
            options["delimiter"] = delimiter
        if include:
            values = [value.strip() for value in include.split(",") if value.strip()]
            allowed = {"httpMetadata", "customMetadata"}
            if any(value not in allowed for value in values):
                return json_response(
                    {"error": "include must be httpMetadata, customMetadata, or both"},
                    status=400,
                )
            options["include"] = values

        listing = await self.env.BUCKET.list(to_js_object(options))
        objects = [
            r2_object_summary(listing.objects[i])
            for i in range(int(listing.objects.length))
        ]
        delimited_prefixes = []
        if hasattr(listing, "delimitedPrefixes") and not is_missing(
            listing.delimitedPrefixes
        ):
            delimited_prefixes = list(listing.delimitedPrefixes.to_py())

        return json_response(
            {
                "objects": objects,
                "truncated": bool(listing.truncated),
                "cursor": None
                if is_missing(getattr(listing, "cursor", None))
                else str(listing.cursor),
                "delimitedPrefixes": delimited_prefixes,
            }
        )
