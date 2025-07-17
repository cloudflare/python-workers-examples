from workers import handler, Response

@handler
async def on_fetch(request, env):
    return Response("Hello world!")
