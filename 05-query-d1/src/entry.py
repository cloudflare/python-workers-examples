from workers import handler, Response

@handler
async def on_fetch(request, env):
    query = """
        SELECT quote, author
        FROM qtable
        ORDER BY RANDOM()
        LIMIT 1;
        """
    results = await env.DB.prepare(query).all()
    data = results.results[0]

    # Return a JSON response
    return Response.json(data)
