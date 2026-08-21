const CANVAS_SIZE = 511;
const MAX_BYTES = 700_000;
const JPEG_QUALITY = 0.82;
const POLL_INTERVAL_MS = 2000;
const MAX_POLLS = 150;
const MAX_POLL_FAILURES = 3;
const TYPE_LABELS = {
  "image/png": "PNG",
  "image/jpeg": "JPEG",
  "image/webp": "WebP",
};
const ACCEPTED_TYPES = Object.keys(TYPE_LABELS);

const byId = (id) => document.getElementById(id);
const uploadForm = byId("upload-form");
const fileInput = byId("file-input");
const submitButton = byId("submit-button");
const uploadStatus = byId("upload-status");
const preview = byId("preview");
const previewImage = byId("preview-image");
const previewCaption = byId("preview-caption");
const compare = byId("compare");
const compareEmpty = byId("compare-empty");
const compareMeta = byId("compare-meta");
const originalImage = byId("original-image");
const outputImage = byId("output-image");
const gallery = byId("gallery");
const galleryStatus = byId("gallery-status");
const refreshButton = byId("refresh-button");

let rawUpload = null;
let previewUrl = null;
let selectedJobId = null;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const shortId = (jobId) => jobId.slice(0, 8);

function setStatus(element, message, tone = "info") {
  element.textContent = message;
  element.dataset.tone = tone;
}

function formatTime(isoString) {
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return "unknown time";
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatBytes(bytes) {
  const kilobytes = bytes / 1024;
  if (kilobytes < 1000) return `${kilobytes.toFixed(1)} KB`;
  return `${(kilobytes / 1024).toFixed(2)} MB`;
}

async function requestJson(path, options) {
  let response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new Error("Network error. Is the Worker still running?");
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : null;
    throw new Error(detail ?? `Request failed with status ${response.status}`);
  }
  return data;
}

// Decodes only to prove the bytes are an image and to read the source size.
// The bitmap is discarded; the original File is what gets uploaded.
async function readSourceSize(file) {
  let bitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch {
    throw new Error("That file could not be decoded as an image.");
  }
  const size = { width: bitmap.width, height: bitmap.height };
  bitmap.close?.();
  return size;
}

async function inspectFile(file) {
  if (!ACCEPTED_TYPES.includes(file.type)) {
    throw new Error("Only PNG, JPEG and WebP are supported.");
  }
  if (file.size > MAX_BYTES) {
    throw new Error(
      `That file is ${file.size.toLocaleString()} bytes, over the ${MAX_UPLOAD_BYTES.toLocaleString()} byte limit. Try a smaller picture.`,
    );
  }

  const { width, height } = await readSourceSize(file);
  const label = TYPE_LABELS[file.type];
  return {
    file,
    caption:
      `${width}x${height} ${label} (${file.type}), ${formatBytes(file.size)}`,
  };
}

async function showPreview() {
  rawUpload = null;
  preview.hidden = true;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;

  const file = fileInput.files?.[0];
  if (!file) {
    setStatus(uploadStatus, "");
    return;
  }

  setStatus(uploadStatus, "Checking your picture...");
  try {
    rawUpload = await inspectFile(file);
    previewUrl = URL.createObjectURL(rawUpload.file);
    previewImage.src = previewUrl;
    previewImage.alt =
      "The original picture you chose, shown at full size before it is uploaded.";
    previewCaption.textContent = rawUpload.caption;
    preview.hidden = false;
    setStatus(uploadStatus, 'Ready. Press "Redraw it!".');
  } catch (error) {
    setStatus(uploadStatus, error.message, "error");
  }
}

// Resolves with the terminal job object so the caller can read job.reason.
async function pollJob(jobId) {
  let failures = 0;

  for (let attempt = 1; attempt <= MAX_POLLS; attempt += 1) {
    await sleep(POLL_INTERVAL_MS);

    let job;
    try {
      job = await requestJson(`/api/jobs/${jobId}`);
      failures = 0;
    } catch (error) {
      failures += 1;
      if (failures >= MAX_POLL_FAILURES) {
        throw new Error(`Lost contact with the Worker. ${error.message}`);
      }
      continue;
    }

    if (job.status === "complete" || job.status === "failed") return job;
    setStatus(
      uploadStatus,
      `Job ${shortId(jobId)} is ${job.status}... (checked ${attempt} times)`,
    );
  }

  throw new Error("This redraw is taking too long. Try Refresh later.");
}

function selectJob(job) {
  selectedJobId = job.jobId;
  originalImage.src = job.originalUrl;
  originalImage.alt = `The picture you uploaded for job ${shortId(job.jobId)}.`;
  outputImage.src = job.outputUrl;
  outputImage.alt = `Workers AI redraw of job ${shortId(job.jobId)}, in a clumsy MS Paint style.`;
  compareMeta.textContent = `Job ${job.jobId} - finished ${formatTime(job.completedAt)}`;
  compare.hidden = false;
  compareEmpty.hidden = true;

  for (const card of gallery.querySelectorAll(".card")) {
    card.setAttribute("aria-pressed", String(card.dataset.jobId === job.jobId));
  }
}

function createCard(job) {
  const thumb = document.createElement("img");
  thumb.src = job.outputUrl;
  thumb.loading = "lazy";
  thumb.alt = `Redrawn picture from job ${shortId(job.jobId)}`;

  const time = document.createElement("span");
  time.textContent = formatTime(job.completedAt);

  const card = document.createElement("button");
  card.type = "button";
  card.className = "card";
  card.dataset.jobId = job.jobId;
  card.setAttribute("aria-pressed", String(job.jobId === selectedJobId));
  card.append(thumb, time);
  card.addEventListener("click", () => selectJob(job));

  const item = document.createElement("li");
  item.append(card);
  return item;
}

function renderGallery(jobs) {
  if (jobs.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = "No pictures yet. Upload one to start the gallery.";
    gallery.replaceChildren(empty);
    return;
  }
  gallery.replaceChildren(...jobs.map(createCard));
}

async function loadGallery(jobIdToSelect) {
  refreshButton.disabled = true;
  setStatus(galleryStatus, "Loading gallery...");

  try {
    const jobs = (await requestJson("/api/jobs"))?.jobs ?? [];
    renderGallery(jobs);
    setStatus(
      galleryStatus,
      jobs.length === 1 ? "1 picture saved." : `${jobs.length} pictures saved.`,
    );

    const target = jobs.find((job) => job.jobId === jobIdToSelect);
    if (target) selectJob(target);
  } catch (error) {
    setStatus(galleryStatus, error.message, "error");
  } finally {
    refreshButton.disabled = false;
  }
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!rawUpload) await showPreview();
  if (!rawUpload) {
    if (!fileInput.files?.length) {
      setStatus(uploadStatus, "Choose a picture first.", "error");
    }
    fileInput.focus();
    return;
  }

  const upload = rawUpload.file;
  fileInput.disabled = true;
  submitButton.disabled = true;
  try {
    setStatus(uploadStatus, "Uploading to the Worker...");
    const created = await requestJson("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": upload.type },
      body: upload,
    });

    setStatus(uploadStatus, `Job ${shortId(created.jobId)} is queued...`);
    const job = await pollJob(created.jobId);
    if (job.status === "complete") {
      setStatus(uploadStatus, "Finished! Behold the artwork.", "done");
      await loadGallery(job.jobId);
    } else {
      // The backend only ever sends a reason it is happy to show a visitor.
      const reason =
        typeof job.reason === "string" && job.reason
          ? job.reason
          : "The Workflow gave up on that one.";
      setStatus(uploadStatus, reason, "error");
    }
  } catch (error) {
    setStatus(uploadStatus, error.message, "error");
  } finally {
    fileInput.disabled = false;
    submitButton.disabled = false;
  }
});

fileInput.addEventListener("change", () => void showPreview());
refreshButton.addEventListener("click", () => void loadGallery());

void loadGallery();
