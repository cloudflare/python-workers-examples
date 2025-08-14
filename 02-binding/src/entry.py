from workers import WorkerEntrypoint, Response

class Default(WorkerEntrypoint):
  async def fetch(selfrequest, env):
    await env.FOO.put("bar", "baz")
    bar = await env.FOO.get("bar")
    return Response(bar) # returns "baz"
