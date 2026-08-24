import httpx
import requests
import urllib3
from workers import Response, WorkerEntrypoint

TARGET_URL = "https://example.com/"
EXPECTED_TEXT = "Example Domain"


def summarize_result(client, status_code, text, headers=None):
    """Return a small JSON-safe summary for an outbound HTTP response."""
    headers = headers or {}
    return {
        "client": client,
        "status_code": int(status_code),
        "ok": 200 <= int(status_code) < 300,
        "saw_expected_text": EXPECTED_TEXT in text,
        "content_type": headers.get("content-type") or headers.get("Content-Type"),
        "body_preview": text[:80],
    }


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = request.url.split("/", 3)[-1]
        path = "/" + path.split("?", 1)[0] if path else "/"

        if path == "/":
            return Response.json(
                {
                    "example": "Synchronous HTTP clients in Python Workers",
                    "target": TARGET_URL,
                    "clients": ["requests", "urllib3", "httpx.Client"],
                    "endpoints": {
                        "GET /sync": "Fetch using requests, urllib3, and httpx.Client",
                        "GET /all": "Alias for /sync",
                    },
                }
            )

        if path in ("/sync", "/all"):
            return Response.json({"target": TARGET_URL, "results": self.fetch_sync()})

        return Response.json({"error": "not found"}, status=404)

    def fetch_sync(self):
        """Use blocking-style Python HTTP clients from a Python Worker."""
        requests_response = requests.get(TARGET_URL, timeout=10)

        pool = urllib3.PoolManager()
        urllib3_response = pool.request("GET", TARGET_URL, timeout=10.0)
        urllib3_text = urllib3_response.data.decode("utf-8")

        with httpx.Client() as client:
            httpx_response = client.get(TARGET_URL, timeout=10.0)

        return [
            summarize_result(
                "requests",
                requests_response.status_code,
                requests_response.text,
                requests_response.headers,
            ),
            summarize_result(
                "urllib3",
                urllib3_response.status,
                urllib3_text,
                urllib3_response.headers,
            ),
            summarize_result(
                "httpx.Client",
                httpx_response.status_code,
                httpx_response.text,
                httpx_response.headers,
            ),
        ]
