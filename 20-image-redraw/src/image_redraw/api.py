import uuid
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Request, Response

from .constants import (
    ALLOWED_CONTENT_TYPES,
    GALLERY_SIZE,
    LIST_PAGE_SIZE,
    MAX_UPLOAD_BYTES,
    OUTPUT_PREFIX,
    STATUS_MAP,
    job_id_from_output_key,
    original_key,
    output_key,
)

app = FastAPI()


@app.post("/api/jobs", status_code=202)
async def create_job(request: Request):
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(415, "Send a raw image/png, image/jpeg or image/webp body.")

    image = await request.body()
    if not image:
        raise HTTPException(400, "The request body is empty.")

    if len(image) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"Images must be at most {MAX_UPLOAD_BYTES} bytes.")

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
async def list_jobs(request: Request):
    env = request.scope["env"]
    bucket = env.REDRAW_BUCKET
    jobs = []
    cursor = None

    while True:
        options = {"prefix": OUTPUT_PREFIX, "limit": LIST_PAGE_SIZE}
        if cursor:
            options["cursor"] = cursor

        listed = await bucket.list(**options)
        for obj in listed["objects"]:
            job_id = job_id_from_output_key(obj.key)
            job = {"jobId": job_id, "completedAt": obj.uploaded.toISOString()}
            job["originalUrl"] = f"/api/images/original/{job_id}"
            job["outputUrl"] = f"/api/images/output/{job_id}"
            jobs.append(job)

        # R2 only returns a cursor while more pages remain.
        cursor = listed["cursor"] if listed["truncated"] else None
        if not cursor:
            break

    jobs.sort(key=lambda job: job["completedAt"], reverse=True)
    return {"jobs": jobs[:GALLERY_SIZE]}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str, request: Request):
    env = request.scope["env"]
    output_url = f"/api/images/output/{job_id}"

    # Done
    if await env.REDRAW_BUCKET.head(output_key(job_id)) is not None:
        return {"jobId": job_id, "status": "complete", "outputUrl": output_url}

    # Not found
    if await env.REDRAW_BUCKET.head(original_key(job_id)) is None:
        raise HTTPException(404, "Job not found.")
    
    # Running
    try:
        instance = await env.REDRAW_WORKFLOW.get(job_id)
        status = await instance.status()
    except Exception:
        # The original exists, so the consumer just has not created the instance yet.
        return {"jobId": job_id, "status": "queued"}
    return {"jobId": job_id, "status": STATUS_MAP.get(status["status"], "running")}


@app.get("/api/images/{kind}/{job_id}")
async def get_image(kind: str, job_id: str, request: Request):
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
    )
