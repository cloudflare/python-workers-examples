const reactions = ["heart", "laugh", "fire"];
const roomPattern = /^[A-Za-z0-9_-]{1,64}$/;
const pollIntervalMs = 1000;

const state = {
  room: null,
  stats: emptyStats(),
  pollId: null,
  statsController: null,
  polling: false,
  generation: 0,
};

const roomForm = document.querySelector("#room-form");
const roomInput = document.querySelector("#room-input");
const activeRoom = document.querySelector("#active-room");
const connection = document.querySelector("#connection");
const connectionText = document.querySelector("#connection-text");
const lastSynced = document.querySelector("#last-synced");
const totalAccepted = document.querySelector("#total-accepted");
const statsBody = document.querySelector("#stats-body");
const batchCycle = document.querySelector("#batch-cycle");
const batchStatus = document.querySelector("#batch-status");
const appStatus = document.querySelector("#app-status");
const reactionButtons = [...document.querySelectorAll(".reaction-button")];

function emptyCounts() {
  return Object.fromEntries(reactions.map((reaction) => [reaction, 0]));
}

function emptyStats() {
  return { totals: emptyCounts(), persisted: emptyCounts(), pending: emptyCounts() };
}

function count(value) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, Math.trunc(number)) : 0;
}

function normaliseCounts(counts) {
  return Object.fromEntries(reactions.map((reaction) => [reaction, count(counts?.[reaction])]));
}

function normaliseStats(stats) {
  return {
    totals: normaliseCounts(stats?.totals),
    persisted: normaliseCounts(stats?.persisted),
    pending: normaliseCounts(stats?.pending),
  };
}

function endpoint(room, suffix) {
  return `/rooms/${encodeURIComponent(room)}${suffix}`;
}

function setStatus(message) {
  appStatus.textContent = message;
}

function setConnection(text, status) {
  connectionText.textContent = text;
  connection.dataset.state = status;
}

function setControlsDisabled(disabled) {
  reactionButtons.forEach((button) => { button.disabled = disabled; });
}

function renderStats() {
  const accepted = reactions.reduce((total, reaction) => total + state.stats.totals[reaction], 0);
  const pending = reactions.reduce((total, reaction) => total + state.stats.pending[reaction], 0);
  totalAccepted.textContent = accepted.toLocaleString();

  reactions.forEach((reaction) => {
    const row = statsBody.querySelector(`[data-reaction="${reaction}"]`);
    ["totals", "persisted", "pending"].forEach((field) => {
      row.querySelector(`[data-field="${field}"]`).textContent = state.stats[field][reaction].toLocaleString();
    });
  });

  batchCycle.classList.toggle("is-buffered", pending > 0);
  batchStatus.textContent = pending > 0
    ? `${pending.toLocaleString()} reaction${pending === 1 ? "" : "s"} waiting for the next flush.`
    : "No reactions waiting to be persisted.";
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(`The server returned ${response.status} without JSON.`);
  }
  if (!response.ok) throw new Error(data?.error || `Request failed with status ${response.status}.`);
  return data;
}

function stopPolling() {
  if (state.pollId !== null) window.clearInterval(state.pollId);
  if (state.statsController !== null) state.statsController.abort();
  state.pollId = null;
  state.statsController = null;
  state.polling = false;
}

async function loadStats(initial = false, generation = state.generation) {
  const room = state.room;
  if (!room || state.polling) return;

  state.polling = true;
  const controller = new AbortController();
  state.statsController = controller;
  if (initial) {
    setConnection("Connecting…", "loading");
    setStatus(`Joining ${room} and loading its reaction ledger.`);
  }

  try {
    const stats = await requestJson(endpoint(room, "/stats"), { signal: controller.signal });
    if (state.room !== room || state.generation !== generation) return;
    state.stats = normaliseStats(stats);
    renderStats();
    lastSynced.textContent = `Last updated ${new Date().toLocaleTimeString()} · polling every second`;
    setConnection("Live", "live");
    if (initial) setStatus(`Joined ${room}. Reaction controls are ready.`);
  } catch (error) {
    if (error.name !== "AbortError" && state.room === room && state.generation === generation) {
      setConnection("Connection issue", "error");
      lastSynced.textContent = "Waiting to retry in the next poll.";
      setStatus(`Could not load ${room}: ${error.message}`);
    }
  } finally {
    if (state.statsController === controller) {
      state.statsController = null;
      state.polling = false;
    }
  }
}

async function joinRoom(event) {
  event.preventDefault();
  if (!roomForm.reportValidity()) return;

  const room = roomInput.value.trim();
  if (!roomPattern.test(room)) {
    setStatus("Room names use 1–64 letters, numbers, hyphens, or underscores.");
    return;
  }

  stopPolling();
  state.generation += 1;
  const generation = state.generation;
  state.room = room;
  state.stats = emptyStats();
  activeRoom.textContent = room;
  lastSynced.textContent = "Loading room statistics…";
  renderStats();
  setControlsDisabled(false);

  state.pollId = window.setInterval(() => {
    void loadStats(false, generation);
  }, pollIntervalMs);
  await loadStats(true, generation);
}

async function sendReaction(reaction, button) {
  const room = state.room;
  if (!room || !reactions.includes(reaction)) return;

  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  setConnection("Sending reaction…", "loading");

  try {
    const result = await requestJson(
      endpoint(room, `/reactions/${encodeURIComponent(reaction)}`),
      { method: "POST" },
    );
    if (state.room !== room) return;
    state.stats = {
      ...state.stats,
      totals: normaliseCounts(result.totals),
      pending: normaliseCounts(result.pending),
    };
    renderStats();
    setConnection("Live", "live");
    setStatus(`${reaction[0].toUpperCase()}${reaction.slice(1)} accepted in ${room}.`);
    void loadStats();
  } catch (error) {
    if (state.room === room) {
      setConnection("Connection issue", "error");
      setStatus(`Could not send ${reaction}: ${error.message}`);
    }
  } finally {
    button.removeAttribute("aria-busy");
    if (state.room === room) button.disabled = false;
  }
}

roomForm.addEventListener("submit", joinRoom);
reactionButtons.forEach((button) => {
  button.addEventListener("click", () => { void sendReaction(button.dataset.reaction, button); });
});
