const form = document.getElementById("todo-form");
const titleInput = document.getElementById("title");
const submitBtn = document.getElementById("submit-btn");
const refreshButton = document.getElementById("refresh");
const list = document.getElementById("todo-list");
const status = document.getElementById("status");
const template = document.getElementById("todo-template");

function setStatus(message, isError = false) {
  status.textContent = message;
  status.dataset.error = isError ? "true" : "false";
  if (message) {
    status.classList.add("visible");
  } else {
    status.classList.remove("visible");
  }
}

async function api(path, options = {}) {
  try {
    const response = await fetch(path, {
      ...options,
      headers: {
        ...(options.headers ?? {}),
        "Content-Type": "application/json",
      },
    });

    if (response.status === 204) {
      return null;
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      throw new Error(
        data?.error ?? `Request failed with status ${response.status}`,
      );
    }

    return data;
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error("Network error. Please check your connection.");
    }
    throw error;
  }
}

function renderTodos(todos) {
  list.innerHTML = "";

  if (todos.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty-state";
    empty.textContent = "No tasks yet. Add one above!";
    list.append(empty);
    return;
  }

  for (const todo of todos) {
    const node = template.content.firstElementChild.cloneNode(true);
    const checkbox = node.querySelector(".todo-completed");
    const title = node.querySelector(".todo-title");
    const meta = node.querySelector(".todo-meta");
    const renameButton = node.querySelector(".rename-button");
    const deleteButton = node.querySelector(".delete-button");
    const renameForm = node.querySelector(".todo-rename-form");
    const renameInput = node.querySelector(".todo-rename-input");
    const cancelRenameBtn = node.querySelector(".cancel-rename");
    const allButtons = node.querySelectorAll("button, input");

    const setBusy = (isBusy) => {
      node.classList.toggle("is-busy", isBusy);
      allButtons.forEach((btn) => (btn.disabled = isBusy));
    };

    checkbox.checked = todo.completed;
    title.textContent = todo.title;

    const date = new Date(todo.created_at);
    meta.textContent = `Created ${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;

    node.dataset.id = String(todo.id);
    node.classList.toggle("is-completed", todo.completed);

    checkbox.addEventListener("change", async () => {
      const originalState = !checkbox.checked;
      setBusy(true);
      try {
        await api(`/api/todos/${todo.id}/`, {
          method: "PATCH",
          body: JSON.stringify({ completed: checkbox.checked }),
        });
        setStatus("");
        node.classList.toggle("is-completed", checkbox.checked);
      } catch (error) {
        checkbox.checked = originalState;
        setStatus(error.message, true);
      } finally {
        setBusy(false);
      }
    });

    const toggleRename = (show) => {
      node.classList.toggle("is-editing", show);
      renameForm.hidden = !show;
      if (show) {
        renameInput.value = todo.title;
        renameInput.focus();
        renameInput.select();
      } else {
        renameButton.focus();
      }
    };

    renameButton.addEventListener("click", () => toggleRename(true));
    cancelRenameBtn.addEventListener("click", () => toggleRename(false));

    renameForm.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        toggleRename(false);
      }
    });

    renameForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const nextTitle = renameInput.value.trim();
      if (!nextTitle || nextTitle === todo.title) {
        toggleRename(false);
        return;
      }

      setBusy(true);
      try {
        await api(`/api/todos/${todo.id}/`, {
          method: "PATCH",
          body: JSON.stringify({ title: nextTitle }),
        });
        todo.title = nextTitle;
        title.textContent = nextTitle;
        toggleRename(false);
        setStatus("");
      } catch (error) {
        setStatus(error.message, true);
      } finally {
        setBusy(false);
      }
    });

    deleteButton.addEventListener("click", async () => {
      setBusy(true);
      try {
        await api(`/api/todos/${todo.id}/`, { method: "DELETE" });
        node.remove();
        setStatus("");
        refreshButton.focus();
        if (list.children.length === 0) {
          renderTodos([]);
        }
      } catch (error) {
        setStatus(error.message, true);
        setBusy(false);
      }
    });

    list.append(node);
  }
}

async function loadTodos() {
  refreshButton.disabled = true;
  setStatus("Loading...", false);
  try {
    const data = await api("/api/todos/");
    renderTodos(data.todos);
    setStatus("");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    refreshButton.disabled = false;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = titleInput.value.trim();
  if (!title) return;

  titleInput.disabled = true;
  submitBtn.disabled = true;
  setStatus("Adding...", false);

  try {
    await api("/api/todos/", {
      method: "POST",
      body: JSON.stringify({ title }),
    });
    titleInput.value = "";
    setStatus("");
    await loadTodos();
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    titleInput.disabled = false;
    submitBtn.disabled = false;
    titleInput.focus();
  }
});

refreshButton.addEventListener("click", () => {
  void loadTodos();
});

void loadTodos();
