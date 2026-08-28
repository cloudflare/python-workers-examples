from image_redraw.api import app
from image_redraw.constants import is_job_id
from image_redraw.workflow import RedrawWorkflow
from workers import WorkerEntrypoint, asgi

# Re-export RedrawWorkflow so workerd can find workflow classes
__all__ = ["Default", "RedrawWorkflow"]


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request, self.env)

    async def queue(self, batch, env, ctx):
        pending = []
        for message in batch.messages:
            body = message.body
            job_id = body.get("jobId") if isinstance(body, dict) else None
            if not is_job_id(job_id):
                print(f"Skipping malformed queue message {message.id}")
                message.ack()
                continue
            pending.append((message, {"id": job_id, "params": {"jobId": job_id}}))
        if pending:
            await self.env.REDRAW_WORKFLOW.create_batch([spec for _, spec in pending])
            for message, _ in pending:
                message.ack()
