from workers import Response, WorkerEntrypoint


class Default(WorkerEntrypoint):
    # runs based on "triggers" in wrangler config
    async def scheduled(self, controller, env, ctx):
        print("Scheduled task has been executed.")

    async def fetch(self):
        return Response(
            "Hello from Cron Worker - Check your logs to see a scheduled task executed every minute"
        )
