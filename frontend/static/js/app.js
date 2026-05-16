/**
 * StudentRAG — Frontend
 * Full RAG via Llama 3.3 70B on OpenRouter.
 */

const API_BASE = "";
let isLoading  = false;

const chatWindow   = document.getElementById("chat-window");
const queryInput   = document.getElementById("query-input");
const sendBtn      = document.getElementById("send-btn");
const uploadZone   = document.getElementById("upload-zone");
const fileInput    = document.getElementById("file-input");
const uploadStatus = document.getElementById("upload-status");
const sourcesList  = document.getElementById("sources-list");

// ── Init ──────────────────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  checkHealth();
  setInterval(checkHealth, 30_000);

  uploadZone.addEventListener("dragover",  e => { e.preventDefault(); uploadZone.classList.add("dragover"); });
  uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("dragover"));
  uploadZone.addEventListener("drop",      e => { e.preventDefault(); uploadZone.classList.remove("dragover"); handleFiles(e.dataTransfer.files); });
  fileInput.addEventListener("change", () => handleFiles(fileInput.files));
});

// ── Health ────────────────────────────────────────────────────────────────────
async function checkHealth() {
  const el = id => document.getElementById(id);
  try {
    const data = await fetch(`${API_BASE}/api/health`).then(r => r.json());

    el("status-api").textContent = "online";
    el("status-api").className   = "status-badge ok";

    const llmOk = data.llm_configured;
    el("status-llm").textContent = llmOk ? "ready" : "no key";
    el("status-llm").className   = `status-badge ${llmOk ? "ok" : "error"}`;



    const colOk = data.collection_status === "ready";
    el("status-col").textContent = data.collection_status || "—";
    el("status-col").className   = `status-badge ${colOk ? "ok" : "error"}`;
    el("status-chunks").textContent = (data.total_chunks ?? 0).toLocaleString();

    if (colOk) updateSourcesList();
  } catch {
    ["status-api","status-llm","status-col"].forEach(k => {
      const e = document.getElementById(k);
      if (e) { e.textContent = "error"; e.className = "status-badge error"; }
    });
  }
}

async function updateSourcesList() {
  try {
    const { sources = [] } = await fetch(`${API_BASE}/api/stats`).then(r => r.json());
    sourcesList.innerHTML = sources.length
      ? sources.map(s => `<li class="has-source" title="${s}">${truncate(s, 28)}</li>`).join("")
      : '<li class="sources-empty">No sources indexed yet.</li>';
  } catch { /* silent */ }
}

// ── Chat ──────────────────────────────────────────────────────────────────────
function handleKeyDown(e) {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendQuery(); }
}

async function sendQuery() {
  const question = queryInput.value.trim();
  if (!question || isLoading) return;

  appendUserMessage(question);
  queryInput.value = "";
  updateCharCount(queryInput);
  autoResize(queryInput);

  const loadingId = appendLoading();
  setLoading(true);

  const payload = { question, top_k: 5, min_score: 0.1 };

  try {
    const res  = await fetch(`${API_BASE}/api/query`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "API error");
    removeMessage(loadingId);
    appendBotAnswer(data);
  } catch (err) {
    removeMessage(loadingId);
    appendError(err.message);
  } finally {
    setLoading(false);
  }
}

async function summarizeNotes() {
  if (isLoading) return;
  appendUserMessage("Summarizing the indexed notes comprehensively...");
  const loadingId = appendLoading();
  setLoading(true);

  try {
    const res  = await fetch(`${API_BASE}/api/summarize`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: null }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "API error");
    removeMessage(loadingId);
    appendBotAnswer(data);
  } catch (err) {
    removeMessage(loadingId);
    appendError(err.message);
  } finally {
    setLoading(false);
  }
}

function appendUserMessage(text) {
  const div = document.createElement("div");
  div.className = "message user-message";
  div.innerHTML = `
    <div class="message-icon">U</div>
    <div class="message-body"><p>${escapeHtml(text)}</p></div>`;
  chatWindow.appendChild(div);
  scrollToBottom();
}

function appendLoading() {
  const id  = `l-${Date.now()}`;
  const div = document.createElement("div");
  div.id        = id;
  div.className = "message bot-message loading-message";
  div.innerHTML = `
    <div class="message-icon">⬡</div>
    <div class="message-body">
      <p><span>Model is thinking</span>
        <span class="dot"></span><span class="dot"></span><span class="dot"></span>
      </p>
    </div>`;
  chatWindow.appendChild(div);
  scrollToBottom();
  return id;
}

function appendBotAnswer(data) {
  const div = document.createElement("div");
  div.className = "message bot-message";

  const sourcesHtml = (data.sources || [])
    .map(s => `<span class="source-tag">${escapeHtml(s)}</span>`)
    .join("");

  const chunksHtml = (data.chunks || []).map(c => `
    <div class="chunk-item">
      <div class="chunk-meta">
        <span>${escapeHtml(c.source)}</span>
        <span>p.${c.page}</span>
        <span class="score">score: ${c.score.toFixed(3)}</span>
        <span>${escapeHtml(c.chunk_id)}</span>
      </div>
      <div class="chunk-text">${escapeHtml(c.text)}</div>
    </div>`).join("");

  const toggleId = `t-${Date.now()}`;
  const listId   = `cl-${Date.now()}`;

  // Format model name for display
  const modelDisplay = data.model_used
    ? data.model_used.split("/").pop().replace(":free", " (free)")
    : "";

  div.innerHTML = `
    <div class="message-icon">⬡</div>
    <div class="message-body">
      <div class="answer-block ${data.answer_found ? "" : "answer-not-found"}">${escapeHtml(data.answer)}</div>
      ${sourcesHtml ? `<div class="sources-row">${sourcesHtml}</div>` : ""}
      ${chunksHtml ? `
        <button class="chunks-toggle" id="${toggleId}"
          onclick="toggleChunks('${toggleId}','${listId}')">
          ▸ Show ${data.chunks.length} retrieved chunk(s)
        </button>
        <div class="chunks-list" id="${listId}" style="display:none">${chunksHtml}</div>
      ` : ""}
      <div class="query-meta">⏱ ${data.query_time_ms}ms · ${data.retrieved_count} chunk(s) retrieved</div>
    </div>`;
  chatWindow.appendChild(div);
  scrollToBottom();
}

function appendError(msg) {
  const div = document.createElement("div");
  div.className = "message bot-message";
  div.innerHTML = `
    <div class="message-icon" style="background:rgba(240,106,106,.15);color:var(--error)">!</div>
    <div class="message-body">
      <div class="answer-block answer-not-found">${escapeHtml(msg)}</div>
    </div>`;
  chatWindow.appendChild(div);
  scrollToBottom();
}

function removeMessage(id)  { document.getElementById(id)?.remove(); }
function clearChat()        { chatWindow.innerHTML = ""; }
function fillQuery(text)    { queryInput.value = text; updateCharCount(queryInput); queryInput.focus(); }

function toggleChunks(toggleId, listId) {
  const list  = document.getElementById(listId);
  const btn   = document.getElementById(toggleId);
  const open  = list.style.display !== "none";
  list.style.display = open ? "none" : "flex";
  btn.textContent = open
    ? `▸ Show ${list.children.length} retrieved chunk(s)`
    : `▾ Hide retrieved chunk(s)`;
}

// ── Upload ────────────────────────────────────────────────────────────────────
async function handleFiles(files) {
  if (!files?.length) return;
  const file = files[0];
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    showUploadStatus("Only PDF files are supported.", "error"); return;
  }
  showUploadStatus(`Uploading ${file.name}…`, "");
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res  = await fetch(`${API_BASE}/api/upload-and-index`, { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail);
    showUploadStatus(`✓ ${file.name} uploaded. Indexing in background…`, "success");
    setTimeout(checkHealth, 5000);
    setTimeout(checkHealth, 15000);
  } catch (err) {
    showUploadStatus(`✗ ${err.message}`, "error");
  }
  fileInput.value = "";
}

function showUploadStatus(msg, type) {
  uploadStatus.textContent = msg;
  uploadStatus.className   = `upload-status ${type}`;
}

// ── Utils ─────────────────────────────────────────────────────────────────────
function setLoading(v)    { isLoading = v; sendBtn.disabled = v; document.getElementById("send-icon").textContent = v ? "…" : "→"; }
function scrollToBottom() { chatWindow.scrollTop = chatWindow.scrollHeight; }
function autoResize(el)   { el.style.height = "auto"; el.style.height = Math.min(el.scrollHeight, 140) + "px"; }
function updateCharCount(el) { const c = document.getElementById("char-count"); if (c) c.textContent = `${el.value.length} / 1000`; }
function truncate(s, n)   { return s.length > n ? "…" + s.slice(-(n-1)) : s; }
function escapeHtml(s)    { return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
