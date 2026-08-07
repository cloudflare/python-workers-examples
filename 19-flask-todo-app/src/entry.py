from workers import WorkerEntrypoint, wsgi

from app import app


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await wsgi.fetch(app, request, self.env)
