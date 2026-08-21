import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response

from .constants import (
    ALLOWED_CONTENT_TYPES,
    GALLERY_SIZE,
    LIST_PAGE_SIZE,
    MAX_UPLOAD_BYTES,
    OUTPUT_PREFIX,
    SAFETY_REJECTED_REASON,
    STATUS_MAP,
    failure_key,
    is_job_id,
    job_id_from_output_key,
    original_key,
    output_key,
)

app = FastAPI()

IMAGE_HEADERS = {"X-Content-Type-Options": "nosniff"}


def declared_length(request: Request) -> int | None:
    try:
        return int(request.headers["content-length"])
    except (KeyError, ValueError):
        # A missing or malformed header falls through to the post-read check.
        return None


@app.post("/api/jobs", status_code=202)
async def create_job(request: Request) -> dict[str, str]:
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(415, "Send a raw image/png, image/jpeg or image/webp body.")

    too_long = f"Images must be at most {MAX_UPLOAD_BYTES} bytes."
    length = declared_length(request)
    if length is not None and length > MAX_UPLOAD_BYTES:
        raise HTTPException(413, too_long)

    image = await request.body()
    if not image:
        raise HTTPException(400, "The request body is empty.")
    if len(image) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, too_long)

    env = request.scope["env"]
    job_id = uuid.uuid4().hex
    created_at = datetime.now(UTC).isoformat()

    # Store the original image
    await env.REDRAW_BUCKET.put(
        original_key(job_id),
        image,
        httpMetadata={"contentType": content_type},
        customMetadata={"createdAt": created_at},
    )
    
    # Enqueue the job
    try:
        await env.REDRAW_QUEUE.send({"jobId": job_id})
    except Exception:
        await env.REDRAW_BUCKET.delete(original_key(job_id))
        raise
    return {"jobId": job_id, "status": "queued", "createdAt": created_at}


@app.get("/api/jobs")
async def list_jobs(request: Request) -> dict[str, list[dict[str, str]]]:
    env = request.scope["env"]
    bucket = env.REDRAW_BUCKET
    jobs = []
    cursor = None

    while True:
        options: dict[str, Any] = {"prefix": OUTPUT_PREFIX, "limit": LIST_PAGE_SIZE}
        if cursor:
            options["cursor"] = cursor

        listed = await bucket.list(**options)
        for obj in listed["objects"]:
            job_id = job_id_from_output_key(obj.key)
            jobs.append(
                {
                    "jobId": job_id,
                    "completedAt": obj.uploaded.toISOString(),
                    "originalUrl": f"/api/images/original/{job_id}",
                    "outputUrl": f"/api/images/output/{job_id}",
                }
            )

        # R2 only returns a cursor while more pages remain.
        cursor = listed["cursor"] if listed["truncated"] else None
        if not cursor:
            break

    jobs.sort(key=lambda job: job["completedAt"], reverse=True)
    return {"jobs": jobs[:GALLERY_SIZE]}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, request: Request) -> dict[str, str]:
    if not is_job_id(job_id):
        raise HTTPException(404, "Job not found.")

    env = request.scope["env"]
    bucket = env.REDRAW_BUCKET

    if await bucket.head(output_key(job_id)) is not None:
        return {
            "jobId": job_id,
            "status": "complete",
            "outputUrl": f"/api/images/output/{job_id}",
        }

    if await bucket.head(failure_key(job_id)) is not None:
        return {"jobId": job_id, "status": "failed", "reason": SAFETY_REJECTED_REASON}

    if await bucket.head(original_key(job_id)) is None:
        raise HTTPException(404, "Job not found.")

    try:
        instance = await env.REDRAW_WORKFLOW.get(job_id)
        status = await instance.status()
    except Exception:
        # The original exists, so the consumer just has not created the instance yet.
        return {"jobId": job_id, "status": "queued"}
    return {"jobId": job_id, "status": STATUS_MAP.get(status["status"], "running")}


@app.get("/api/images/{kind}/{job_id}")
async def get_image(kind: str, job_id: str, request: Request) -> Response:
    if not is_job_id(job_id):
        raise HTTPException(404, "Image not found.")

    if kind == "original":
        key = original_key(job_id)
    elif kind == "output":
        key = output_key(job_id)
    else:
        raise HTTPException(404, "Image kind must be 'original' or 'output'.")

    env = request.scope["env"]
    obj = await env.REDRAW_BUCKET.get(key)
    if obj is None:
        raise HTTPException(404, "Image not found.")

    # Serve the type recorded when the bytes were stored; never guess from the key.
    http_metadata = obj.httpMetadata
    media_type = http_metadata.contentType if http_metadata is not None else None
    blob = await obj.blob()
    return Response(
        content=await blob.bytes(),
        media_type=media_type or "application/octet-stream",
        headers=IMAGE_HEADERS,
    )
