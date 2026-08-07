from app import app
from workers import WorkerEntrypoint, wsgi


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await wsgi.fetch(app, request, self.env)
