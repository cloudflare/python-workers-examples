from workers import WorkerEntrypoint, Response
from result import Env

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        await self.env.FOO.put("bar", "baz")
        bar = await self.env.FOO.get("bar")
        return Response(bar)  # returns "baz"
