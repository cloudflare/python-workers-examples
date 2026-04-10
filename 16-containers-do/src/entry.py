import asyncio

from workers import WorkerEntrypoint, Response, DurableObject

MAX_RETRIES = 5
RETRY_INTERVAL = 0.1


class MyContainer(DurableObject):
    """Container-backed Durable Object that proxies requests to a container."""

    async def fetch(self, request):
        if not self.ctx.container.running:
            self.ctx.container.start()

        port = self.ctx.container.getTcpPort(8080)
        url = request.url.replace("https:", "http:")

        for _ in range(MAX_RETRIES):
            try:
                return await port.fetch(url, request)
            except Exception:
                await asyncio.sleep(RETRY_INTERVAL)

        return Response("Container failed to start", status=503)


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        do_id = self.env.MY_CONTAINER.idFromName("image-gen")
        stub = self.env.MY_CONTAINER.get(do_id)
        return await stub.fetch(request)
