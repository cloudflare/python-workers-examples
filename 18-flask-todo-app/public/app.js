const $ = (sel) => document.querySelector(sel);

const els = {
  form: $("#create-form"),
  title: $("#title"),
  body: $("#body"),
  list: $("#notes"),
  status: $("#status"),
  search: $("#search"),
  clearDone: $("#clear-done"),
  filters: document.querySelectorAll(".filter"),
  template: $("#note-template"),
};

let filter = "all";
let search = "";

/** Fetch wrapper that surfaces the API's JSON `error` field. */
async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: options.body ? { "Content-Type": "application/json" } : {},
    ...options,
  });
  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(data?.error ?? `Request failed (${res.status})`);
  }
  return data;
}

function setStatus(message, isError = false) {
  els.status.textContent = message;
  els.status.classList.toggle("status--error", isError);
}

function formatDate(iso) {
  // Timestamps are stored as UTC without a timezone-aware parser on the server,
  // so normalize to a real Date for locale-aware display.
  const date = new Date(iso.endsWith("Z") ? iso : `${iso}Z`);
  return Number.isNaN(date.valueOf()) ? iso : date.toLocaleString();
}

function renderNote(note) {
  const el = els.template.content.firstElementChild.cloneNode(true);
  el.dataset.id = note.id;
  el.classList.toggle("is-done", note.done);

  const check = el.querySelector(".note__check");
  const title = el.querySelector(".note__title");
  const body = el.querySelector(".note__body");

  check.checked = note.done;
  // textContent (not innerHTML) — note content is untrusted user input.
  title.textContent = note.title;
  body.textContent = note.body;
  title.contentEditable = "plaintext-only";
  body.contentEditable = "plaintext-only";
  el.querySelector(".note__meta").textContent = `Updated ${formatDate(note.updated_at)}`;

  check.addEventListener("change", () => patch(el, { done: check.checked }));

  // Commit inline edits on blur, but only when the text actually changed.
  const commit = (field, node, original) => {
    const value = node.textContent.trim();
    if (value === original) return;
    if (field === "title" && !value) {
      node.textContent = original; // titles are required
      return;
    }
    patch(el, { [field]: value });
  };

  for (const [field, node] of [["title", title], ["body", body]]) {
    node.addEventListener("focus", () => {
      node.dataset.original = node.textContent.trim();
    });
    node.addEventListener("blur", () => commit(field, node, node.dataset.original));
    node.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        node.blur();
      } else if (e.key === "Escape") {
        node.textContent = node.dataset.original;
        node.blur();
      }
    });
  }

  el.querySelector(".note__delete").addEventListener("click", () => remove(el));
  return el;
}

function render(notes) {
  els.list.replaceChildren(...notes.map(renderNote));

  if (notes.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty";
    empty.textContent = search
      ? `No notes match “${search}”.`
      : filter === "done"
        ? "Nothing completed yet."
        : filter === "active"
          ? "All done. Nice."
          : "No notes yet — add one above.";
    els.list.replaceChildren(empty);
  }

  const remaining = notes.filter((n) => !n.done).length;
  setStatus(
    notes.length === 0
      ? ""
      : `${notes.length} note${notes.length === 1 ? "" : "s"} · ${remaining} active`,
  );
  els.clearDone.hidden = !notes.some((n) => n.done);
}

async function load() {
  const params = new URLSearchParams({ filter });
  if (search) params.set("q", search);
  try {
    const { notes } = await api(`/api/notes?${params}`);
    render(notes);
  } catch (err) {
    setStatus(err.message, true);
  }
}

async function patch(el, changes) {
  el.classList.add("note--busy");
  try {
    await api(`/api/notes/${el.dataset.id}`, {
      method: "PATCH",
      body: JSON.stringify(changes),
    });
    await load();
  } catch (err) {
    setStatus(err.message, true);
    await load(); // resync so the UI never shows unsaved state
  }
}

async function remove(el) {
  el.classList.add("note--busy");
  try {
    await api(`/api/notes/${el.dataset.id}`, { method: "DELETE" });
    await load();
  } catch (err) {
    setStatus(err.message, true);
    el.classList.remove("note--busy");
  }
}

els.form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = els.title.value.trim();
  if (!title) return;

  const button = els.form.querySelector("button");
  button.disabled = true;
  try {
    await api("/api/notes", {
      method: "POST",
      body: JSON.stringify({ title, body: els.body.value.trim() }),
    });
    els.form.reset();
    els.title.focus();
    await load();
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    button.disabled = false;
  }
});

for (const button of els.filters) {
  button.addEventListener("click", () => {
    filter = button.dataset.filter;
    for (const b of els.filters) b.classList.toggle("is-active", b === button);
    load();
  });
}

// Debounce search so typing doesn't fire a request per keystroke.
let searchTimer;
els.search.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    search = els.search.value.trim();
    load();
  }, 200);
});

els.clearDone.addEventListener("click", async () => {
  if (!confirm("Delete all completed notes?")) return;
  try {
    await api("/api/notes/delete_completed", { method: "DELETE" });
    await load();
  } catch (err) {
    setStatus(err.message, true);
  }
});

load();
