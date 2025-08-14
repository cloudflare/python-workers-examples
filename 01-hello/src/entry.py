from workers import WorkerEntrypoint, Response

class Default(WorkerEntrypoint):
  async def fetch(self, request, env):
    return Response("Hello world!")
