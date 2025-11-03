from workers import WorkerEntrypoint, Response, WorkflowEntrypoint
from urllib.parse import urlparse
import asyncio
import random


class DAGWorkflow(WorkflowEntrypoint):
    async def run(self, event, step):
        @step.do("dependency 1")
        async def sleep_a_little():
            print("executing dep1")
            await asyncio.sleep(random.randint(1, 10))

        @step.do("dependency 2")
        async def sleep_longer():
            print("executing dep2")
            await asyncio.sleep(random.randint(5, 15))

        @step.do("final step", depends=[sleep_a_little, sleep_longer], concurrent=True)
        async def summarize(res1=None, res2=None):
            print("I awaited the first two steps and now I am done")

        await summarize()


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = urlparse(request.url)

        if url.path == "/start":
            workflow = await self.env.MY_WORKFLOW.create()
            return Response("Just kicked off a workflow with ID: " + workflow.id)

        if "/status" in url.path:
            workflow_id = url.path.split("/")[-1]
            workflow = await self.env.MY_WORKFLOW.get(workflow_id)
            status = await workflow.status()
            return Response.json(status)

        return Response(
            "Use /start or the dashboard UI to trigger the workflow.\n Use /status/<workflow_id> or check dashboard UI to get status."
        )
