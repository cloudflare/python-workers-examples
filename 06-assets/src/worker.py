from workers import WorkerEntrypoint, Response
from urllib.parse import urlparse

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Example of serving static assets
        return await self.env.ASSETS.fetch(request)
