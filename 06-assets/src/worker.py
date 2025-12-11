from workers import WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Example of serving static assets
        return await self.env.ASSETS.fetch(request)
