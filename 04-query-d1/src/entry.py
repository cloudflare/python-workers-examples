from workers import WorkerEntrypoint, Response, Request


class Default(WorkerEntrypoint):
    async def fetch(self, request: Request) -> Response:
        query = """
        SELECT quote, author
        FROM qtable
        ORDER BY RANDOM()
        LIMIT 1;
        """
        results = await self.env.DB.prepare(query).all()
        data = results.results[0]

        # Return a JSON response
        return Response.from_json(data)
