from workers import WorkerEntrypoint, Response
from urllib.parse import urlparse

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

        # TODO: Once https://github.com/cloudflare/workerd/pull/4926 is released, can do
        # self.env.ASSETS.fetch(request) without the .js_object
        return await self.env.ASSETS.fetch(request.js_object)
