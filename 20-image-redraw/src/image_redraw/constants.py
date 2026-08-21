import re

MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
# FLUX takes multipart form fields, so every option is sent as a string.
AI_OPTIONS = {
    "prompt": (
        "redraw the scene in the reference image as a clumsy MS Paint drawing, "
        "keeping the same subject and composition but with wobbly mouse-drawn "
        "outlines, flat bucket-fill colors, jagged pixelated edges, childlike "
        "and amateur"
    ),
    "guidance": "2.5",
    "width": "512",
    "height": "512",
}
AI_RETRIES = {"retries": {"limit": 5, "delay": "5 seconds", "backoff": "exponential"}}
ORIGINAL_PREFIX = "originals/"
OUTPUT_PREFIX = "outputs/"
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_UPLOAD_BYTES = 700_000
# The gallery shows the newest finished redraws; R2 lists keys in lexicographic
# order, so every page has to be read before the newest ones can be picked.
GALLERY_SIZE = 20
LIST_PAGE_SIZE = 100
JOB_ID_PATTERN = re.compile(r"[0-9a-f]{32}")
STATUS_MAP = {
    "queued": "queued",
    "complete": "complete",
    "errored": "failed",
    "terminated": "failed",
}


def is_job_id(value):
    # Job IDs are uuid4().hex, and a malformed one would fail the whole create_batch.
    return isinstance(value, str) and JOB_ID_PATTERN.fullmatch(value) is not None


def original_key(job_id):
    return f"{ORIGINAL_PREFIX}{job_id}"


def output_key(job_id):
    return f"{OUTPUT_PREFIX}{job_id}"


def job_id_from_output_key(key):
    return key.removeprefix(OUTPUT_PREFIX)
