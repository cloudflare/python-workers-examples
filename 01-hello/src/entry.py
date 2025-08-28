from workers import WorkerEntrypoint, Response

class test:
    async def fetch(self, request):
        return Response("Hello from Worker B")

class Default(test, WorkerEntrypoint):
    pass
