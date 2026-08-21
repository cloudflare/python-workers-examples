import base64

from workers import Blob, FormData, Response, WorkflowEntrypoint
from workers.workflows import NonRetryableError

from .constants import AI_OPTIONS, AI_RETRIES, MODEL, original_key, output_key

# Magic bytes, because the model tells us nothing about the format it picked.
IMAGE_SIGNATURES = ((b"\x89PNG", "image/png"), (b"\xff\xd8\xff", "image/jpeg"))


def sniff_content_type(image_bytes):
    for signature, content_type in IMAGE_SIGNATURES:
        if image_bytes.startswith(signature):
            return content_type
    return None


class RedrawWorkflow(WorkflowEntrypoint):
    async def run(self, event, step):
        job_id = event["payload"]["jobId"]
        bucket = self.env.REDRAW_BUCKET
        source_key = original_key(job_id)
        target_key = output_key(job_id)

        @step.do()
        async def verify_original():
            if await bucket.head(source_key) is None:
                raise NonRetryableError(f"No original stored for job {job_id}.")
            return source_key

        @step.do(config=AI_RETRIES)
        async def redraw(verify_original):
            source = await bucket.get(verify_original)
            if source is None:
                raise NonRetryableError(f"No original stored for job {job_id}.")
            original = await source.blob()
            image_bytes = await original.bytes()

            form = FormData()
            for field, value in AI_OPTIONS.items():
                form[field] = value
            reference = Blob(image_bytes, original.content_type or "image/png")
            form.append("input_image_0", reference, "input.png")

            serialized = Response(form)
            generated = await self.env.AI.run(
                MODEL,
                {
                    "multipart": {
                        "body": serialized.body,
                        "contentType": serialized.headers["content-type"],
                    }
                },
            )

            # FLUX replies with JSON holding a base64 image, so decode before storing.
            image = base64.b64decode(generated["image"])
            content_type = sniff_content_type(image)
            if content_type is None:
                raise NonRetryableError(
                    f"Model returned neither PNG nor JPEG bytes for job {job_id}."
                )

            await bucket.put(
                target_key,
                image,
                httpMetadata={"contentType": content_type},
                customMetadata={"jobId": job_id},
            )
            return {"key": target_key, "contentType": content_type}

        return await redraw()
