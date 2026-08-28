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

AI_ERROR_CODE_PATTERN = re.compile(r"(\d+)\s*:")
# 3030 means the safety filter refused the generated image. This app
# deliberately treats it as final rather than retrying, to avoid repeated
# billable inference on a reference the filter is likely to refuse again.
AI_SAFETY_ERROR_CODE = 3030

ORIGINAL_PREFIX = "originals/"
OUTPUT_PREFIX = "outputs/"
FAILURE_PREFIX = "failures/"

ALLOWED_CONTENT_TYPES = ("image/png", "image/jpeg", "image/webp")

# A deliberately small, fixed canvas for this example: it keeps inference cheap
# and every reference picture uniform. It is a choice made here, not a limit
# documented by the model.
TARGET_SIZE = (511, 511)
CANVAS_COLOR = (255, 255, 255)
JPEG_QUALITY = 82
MAX_SOURCE_PIXELS = {"JPEG": 40_000_000, "PNG": 8_000_000, "WEBP": 4_000_000}

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
SAFETY_REJECTED_REASON = (
    "Workers AI refused to redraw that picture. Try a different one."
)
INVALID_IMAGE_REASON = "That upload could not be decoded as a usable image."
MISSING_ORIGINAL_REASON = "The uploaded picture is no longer available."
INVALID_OUTPUT_REASON = "Workers AI returned something that was not a picture."


def is_job_id(value: object) -> bool:
    # Job IDs are uuid4().hex, and a malformed one would fail the whole create_batch.
    return isinstance(value, str) and JOB_ID_PATTERN.fullmatch(value) is not None


def original_key(job_id: str) -> str:
    return f"{ORIGINAL_PREFIX}{job_id}"


def output_key(job_id: str) -> str:
    return f"{OUTPUT_PREFIX}{job_id}"


def failure_key(job_id: str) -> str:
    return f"{FAILURE_PREFIX}{job_id}"


def job_id_from_output_key(key: str) -> str:
    return key.removeprefix(OUTPUT_PREFIX)


def ai_error_code(message: str | None) -> int | None:
    if not message:
        return None
    match = AI_ERROR_CODE_PATTERN.match(message.strip())
    return int(match.group(1)) if match else None
