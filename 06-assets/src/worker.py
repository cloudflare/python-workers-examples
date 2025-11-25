from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint

INDEX_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Assets Example</title>
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <div class="container">
        <h1>Assets Handling Example</h1>
        <p>This demonstrates serving static content from a Python Worker.</p>
        <img src="/image.svg" alt="Example circle image" />
    </div>
    <script src="/script.js"></script>
</body>
</html>
"""


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Example of serving static assets
        path = urlparse(request.url).path
        if path in ["/", "/index.html"]:
            return Response(INDEX_PAGE, headers={"Content-Type": "text/html"})

        return await self.env.ASSETS.fetch(request)
