from workers import WorkerEntrypoint, Response

class Default(WorkerEntrypoint):
  async def fetch(self, request, env):
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
