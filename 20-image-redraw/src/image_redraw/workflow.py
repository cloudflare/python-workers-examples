import base64
import io
import json

from PIL import Image, ImageOps
from workers import Blob, FormData, Response, WorkflowEntrypoint
from workers.workflows import NonRetryableError

from .constants import (
    AI_OPTIONS,
    AI_RETRIES,
    AI_SAFETY_ERROR_CODE,
    CANVAS_COLOR,
    INVALID_IMAGE_REASON,
    INVALID_OUTPUT_REASON,
    JPEG_QUALITY,
    MAX_SOURCE_PIXELS,
    MISSING_ORIGINAL_REASON,
    MODEL,
    SAFETY_REJECTED_REASON,
    TARGET_SIZE,
    ai_error_code,
    failure_key,
    original_key,
    output_key,
)

# Magic bytes, because the model tells us nothing about the format it picked.
IMAGE_SIGNATURES = ((b"\x89PNG", "image/png"), (b"\xff\xd8\xff", "image/jpeg"))


class UnusableImageError(Exception):
    pass


def sniff_content_type(image_bytes: bytes) -> str | None:
    for signature, content_type in IMAGE_SIGNATURES:
        if image_bytes.startswith(signature):
            return content_type
    return None


def resize(image_bytes: bytes) -> bytes:
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            source_format = image.format or ""
            pixel_limit = MAX_SOURCE_PIXELS.get(source_format)
            if pixel_limit is None:
                raise UnusableImageError(f"Unsupported image format {source_format!r}.")

            width, height = image.size
            if width * height > pixel_limit:
                raise UnusableImageError(
                    f"{source_format} input is {width}x{height}, "
                    f"over the {pixel_limit} pixel budget."
                )

            if source_format == "JPEG":
                image.draft("RGB", TARGET_SIZE)
            ImageOps.exif_transpose(image, in_place=True)

            image.thumbnail(TARGET_SIZE, Image.Resampling.LANCZOS, reducing_gap=2.0)
            return _encode_centered_jpeg(image)
    except UnusableImageError:
        raise
    except (Image.DecompressionBombError, OSError, ValueError) as exc:
        raise UnusableImageError(f"Pillow could not decode the image: {exc}") from exc


def _encode_centered_jpeg(image: Image.Image) -> bytes:
    if image.mode in ("RGBA", "LA") or "transparency" in image.info:
        # Dropping alpha without a mask would render transparency as black.
        image = image.convert("RGBA")
        mask = image.getchannel("A")
    else:
        image = image.convert("RGB")
        mask = None

    canvas = Image.new("RGB", TARGET_SIZE, CANVAS_COLOR)
    left = (TARGET_SIZE[0] - image.width) // 2
    top = (TARGET_SIZE[1] - image.height) // 2
    canvas.paste(image, (left, top), mask)

    buffer = io.BytesIO()
    canvas.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    return buffer.getvalue()


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
                return json.dumps({"ok": False, "reason": MISSING_ORIGINAL_REASON})
            original = await source.blob()

            try:
                reference = resize(await original.bytes())
            except UnusableImageError as exc:
                print(f"Job {job_id} has an unusable original: {exc}")
                return json.dumps({"ok": False, "reason": INVALID_IMAGE_REASON})

            form = FormData()
            for field, value in AI_OPTIONS.items():
                form[field] = value
            form.append("input_image_0", Blob(reference, "image/jpeg"), "input.jpg")

            serialized = Response(form)
            multipart_type = serialized.headers["content-type"]
            multipart_body = await serialized.bytes()

            try:
                generated = await self.env.AI.run(
                    MODEL,
                    {
                        "multipart": {
                            "body": multipart_body,
                            "contentType": multipart_type,
                        }
                    },
                )
            except Exception as exc:
                if hasattr(exc, "message") and ai_error_code(exc.message) != AI_SAFETY_ERROR_CODE:
                    raise
                # Returning rather than raising checkpoints the step, which is
                # what guarantees no further inference happens.
                return json.dumps({"ok": False, "reason": SAFETY_REJECTED_REASON})

            # FLUX replies with JSON holding a base64 image, so decode before storing.
            image = base64.b64decode(generated["image"])
            content_type = sniff_content_type(image)
            if content_type is None:
                return json.dumps({"ok": False, "reason": INVALID_OUTPUT_REASON})

            await bucket.put(
                target_key,
                image,
                httpMetadata={"contentType": content_type},
                customMetadata={"jobId": job_id},
            )
            return json.dumps({"ok": True, "key": target_key})

        result = json.loads(await redraw())
        if not result["ok"]:
            await bucket.put(
                failure_key(job_id),
                result["reason"],
                httpMetadata={"contentType": "text/plain"},
                customMetadata={"jobId": job_id},
            )
            # Raised outside the retrying step so the failure is final.
            raise NonRetryableError(result["reason"])
        return None
