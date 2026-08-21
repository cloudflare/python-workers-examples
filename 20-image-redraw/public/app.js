const CANVAS_SIZE = 511;
const MAX_BYTES = 700_000;
const JPEG_QUALITY = 0.82;
const POLL_INTERVAL_MS = 2000;
const MAX_POLLS = 150;
const MAX_POLL_FAILURES = 3;
const ACCEPTED_TYPES = ["image/png", "image/jpeg", "image/webp"];

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

let prepared = null;
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

// FLUX reference images must be under 512x512, so letterbox on white at 511x511.
async function prepareUpload(file) {
  let bitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch {
    throw new Error("That file could not be decoded as an image.");
  }

  const scale = Math.min(1, CANVAS_SIZE / Math.max(bitmap.width, bitmap.height));
  const width = Math.max(1, Math.round(bitmap.width * scale));
  const height = Math.max(1, Math.round(bitmap.height * scale));
  const source = `${bitmap.width}x${bitmap.height}`;

  const canvas = document.createElement("canvas");
  canvas.width = CANVAS_SIZE;
  canvas.height = CANVAS_SIZE;
  const context = canvas.getContext("2d");
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
  context.drawImage(
    bitmap,
    (CANVAS_SIZE - width) / 2,
    (CANVAS_SIZE - height) / 2,
    width,
    height,
  );
  bitmap.close?.();

  const blob = await new Promise((resolve) => {
    canvas.toBlob(resolve, "image/jpeg", JPEG_QUALITY);
  });
  if (!blob) throw new Error("This browser could not encode the resized image.");
  if (blob.size > MAX_BYTES) {
    throw new Error(
      `The resized image is still ${blob.size.toLocaleString()} bytes, over the ${MAX_BYTES.toLocaleString()} byte limit. Try a smaller picture.`,
    );
  }

  const kilobytes = (blob.size / 1024).toFixed(1);
  return {
    blob,
    caption: `${source} drawn at ${width}x${height} on ${CANVAS_SIZE}x${CANVAS_SIZE} - JPEG q${JPEG_QUALITY}, ${kilobytes} KB`,
  };
}

async function showPreview() {
  prepared = null;
  preview.hidden = true;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = null;

  const file = fileInput.files?.[0];
  if (!file) {
    setStatus(uploadStatus, "");
    return;
  }
  if (!ACCEPTED_TYPES.includes(file.type)) {
    setStatus(uploadStatus, "Only PNG, JPEG and WebP are supported.", "error");
    return;
  }

  setStatus(uploadStatus, "Squashing your picture onto a 511x511 canvas...");
  try {
    prepared = await prepareUpload(file);
    previewUrl = URL.createObjectURL(prepared.blob);
    previewImage.src = previewUrl;
    previewImage.alt =
      "Your picture centred on a 511 by 511 white square, exactly as the AI will see it.";
    previewCaption.textContent = prepared.caption;
    preview.hidden = false;
    setStatus(uploadStatus, 'Ready. Press "Redraw it!".');
  } catch (error) {
    setStatus(uploadStatus, error.message, "error");
  }
}

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

    if (job.status === "complete" || job.status === "failed") return job.status;
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
  if (!prepared) await showPreview();
  if (!prepared) {
    if (!fileInput.files?.length) {
      setStatus(uploadStatus, "Choose a picture first.", "error");
    }
    fileInput.focus();
    return;
  }

  fileInput.disabled = true;
  submitButton.disabled = true;
  try {
    setStatus(uploadStatus, "Uploading to the Python Worker...");
    const job = await requestJson("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": prepared.blob.type },
      body: prepared.blob,
    });

    setStatus(uploadStatus, `Job ${shortId(job.jobId)} is queued...`);
    if ((await pollJob(job.jobId)) === "complete") {
      setStatus(uploadStatus, "Finished! Behold the artwork.", "done");
      await loadGallery(job.jobId);
    } else {
      setStatus(uploadStatus, "The Workflow gave up on that one.", "error");
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
