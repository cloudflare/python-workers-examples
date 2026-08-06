from workers import Response, WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        response = await self.env.AI.run(
            "@cf/openai/gpt-oss-120b",
            {
                "instructions": "You are a concise assistant.",
                "input": "What is the origin of the phrase 'The King is dead, long live the King!'?",
            },
        )

        return Response.json(response.output)
