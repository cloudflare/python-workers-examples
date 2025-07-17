from workers import handler, Response

@handler
async def on_fetch(request, env):
    await env.FOO.put("bar", "baz")
    bar = await env.FOO.get("bar")
    return Response(bar) # returns "baz"
