import uuid
from urllib.parse import urlsplit

from workers import Response, WorkerEntrypoint

MAX_CODE_ATTEMPTS = 5


def error(message, status, allow=None):
    headers = {"Allow": allow} if allow else None
    return Response.json({"error": message}, status=status, headers=headers)


def is_valid_destination(url):
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(hostname)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = urlsplit(request.url).path

        if path == "/shorten":
            if request.method != "POST":
                return error("method not allowed", 405, allow="POST")
            return await self.shorten(request)

        if request.method != "GET":
            return error("method not allowed", 405, allow="GET")

        code = path.lstrip("/")
        if not code or "/" in code:
            return error("not found", 404)

        url = await self.env.LINKS.get(code)
        if url is None:
            return error("not found", 404)
        return Response.redirect(url, 302)

    async def shorten(self, request):
        try:
            body = await request.json()
            url = body["url"]
        except (KeyError, TypeError, ValueError):
            return error("request body must contain a URL", 400)

        if not isinstance(url, str) or not is_valid_destination(url):
            return error("url must be an absolute HTTP(S) URL", 400)

        for _ in range(MAX_CODE_ATTEMPTS):
            code = uuid.uuid4().hex[:8]

            if await self.env.LINKS.get(code) is not None:
                # Code already exists, try again
                continue

            await self.env.LINKS.put(code, url)
            origin = urlsplit(request.url)
            short_url = f"{origin.scheme}://{origin.netloc}/{code}"
            return Response.json(
                {"code": code, "short_url": short_url, "url": url}, status=201
            )

        return error("could not allocate a short code", 503)
