const API_BASE = "http://localhost:8000";
const TOKEN_KEY = "rag_jwt_token";

const els = {
  authStatus: document.getElementById("authStatus"),
  authMessage: document.getElementById("authMessage"),
  uploadMessage: document.getElementById("uploadMessage"),
  chatLog: document.getElementById("chatLog"),
  logoutBtn: document.getElementById("logoutBtn"),
  streamToggle: document.getElementById("streamToggle"),
  queryInput: document.getElementById("queryInput"),
  documentFile: document.getElementById("documentFile"),
  loginEmail: document.getElementById("loginEmail"),
  loginPassword: document.getElementById("loginPassword"),
  signupEmail: document.getElementById("signupEmail"),
  signupPassword: document.getElementById("signupPassword"),
  authPage: document.getElementById("authPage"),
  mainApp: document.getElementById("mainApp"),
  userEmail: document.getElementById("userEmail"),
};

const state = {
  token: localStorage.getItem(TOKEN_KEY) || "",
  user: null,
};

function setMessage(el, text, kind = "") {
  el.textContent = text || "";
  el.className = `message ${kind}`.trim();
}

function setAuthStatus(text) {
  els.authStatus.textContent = text;
}

function setToken(token) {
  state.token = token || "";
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  return headers;
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const contentType = response.headers.get("content-type") || "";
  let data = null;

  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    const text = await response.text();
    data = text ? { detail: text } : null;
  }

  if (!response.ok) {
    const detail = data?.detail || data?.message || `Request failed (${response.status})`;
    throw new Error(detail);
  }

  return data;
}

function addBubble(role, text) {
  const template = document.getElementById("messageTemplate");
  const node = template.content.firstElementChild.cloneNode(true);
  node.classList.add(role);
  node.querySelector(".bubble-meta").textContent = role === "user" ? "You" : "Assistant";
  const textNode = node.querySelector(".bubble-text");
  textNode.textContent = text;
  els.chatLog.appendChild(node);
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
  return textNode;
}

function updateAuthUI() {
  const signedIn = Boolean(state.token);
  els.logoutBtn.classList.toggle("hidden", !signedIn);
  els.authPage.classList.toggle("hidden", signedIn);
  els.mainApp.classList.toggle("hidden", !signedIn);
  els.userEmail.textContent = state.user?.email || "-";
  setAuthStatus(signedIn ? `Signed in${state.user?.email ? ` as ${state.user.email}` : ""}` : "Not signed in");
}

async function refreshUser() {
  if (!state.token) {
    state.user = null;
    updateAuthUI();
    return;
  }

  try {
    const user = await apiRequest("/auth/me", {
      method: "GET",
      headers: authHeaders(),
    });
    state.user = user;
    updateAuthUI();
  } catch (error) {
    setToken("");
    state.user = null;
    updateAuthUI();
    setMessage(els.authMessage, error.message, "error");
  }
}

async function handleAuthSubmit(path, email, password) {
  const payload = { email, password };
  const data = await apiRequest(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  setToken(data.access_token);
  state.user = data.user;
  updateAuthUI();
  setMessage(els.authMessage, `Success: ${data.user.email}`, "success");
  setMessage(els.uploadMessage, "");
}

async function uploadDocument(file) {
  if (!state.token) {
    throw new Error("Please sign in first.");
  }
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest("/documents/upload", {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });
}

function buildQueryPayload(query) {
  return {
    query,
    top_k: 5,
  };
}

async function sendNonStreamingQuery(query) {
  if (!state.token) {
    throw new Error("Please sign in first.");
  }
  const data = await apiRequest("/query/ask", {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(buildQueryPayload(query)),
  });
  return data.answer;
}

async function sendStreamingQuery(query) {
  if (!state.token) {
    throw new Error("Please sign in first.");
  }
  const response = await fetch(`${API_BASE}/query/ask-stream`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(buildQueryPayload(query)),
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const errorData = await response.json();
      detail = errorData.detail || errorData.message || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let answerText = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.trim()) continue;
      const event = JSON.parse(line);

      if (event.type === "answer_chunk") {
        answerText += event.content;
        yieldUpdate(answerText);
      } else if (event.type === "error") {
        throw new Error(event.message || "Streaming failed");
      }
    }
  }

  if (buffer.trim()) {
    const event = JSON.parse(buffer);
    if (event.type === "answer_chunk") {
      answerText += event.content;
      yieldUpdate(answerText);
    }
  }

  return answerText;
}

let streamingBubbleText = null;
function yieldUpdate(text) {
  if (streamingBubbleText) {
    streamingBubbleText.textContent = text;
    els.chatLog.scrollTop = els.chatLog.scrollHeight;
  }
}

function wireTabs() {
  const tabs = document.querySelectorAll(".tab");
  const loginForm = document.getElementById("loginForm");
  const signupForm = document.getElementById("signupForm");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const target = tab.dataset.tab;
      loginForm.classList.toggle("hidden", target !== "login");
      signupForm.classList.toggle("hidden", target !== "signup");
      setMessage(els.authMessage, "");
    });
  });
}

function wireAuthForms() {
  document.getElementById("loginForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await handleAuthSubmit("/auth/login", els.loginEmail.value.trim(), els.loginPassword.value);
    } catch (error) {
      setMessage(els.authMessage, error.message, "error");
    }
  });

  document.getElementById("signupForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await handleAuthSubmit("/auth/signup", els.signupEmail.value.trim(), els.signupPassword.value);
    } catch (error) {
      setMessage(els.authMessage, error.message, "error");
    }
  });

  els.logoutBtn.addEventListener("click", () => {
    setToken("");
    state.user = null;
    els.chatLog.innerHTML = "";
    els.queryInput.value = "";
    els.documentFile.value = "";
    updateAuthUI();
    setMessage(els.authMessage, "Logged out.", "success");
  });
}

function wireUploadForm() {
  document.getElementById("uploadForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!state.token) {
      setMessage(els.uploadMessage, "Please sign in first.", "error");
      return;
    }
    const file = els.documentFile.files?.[0];
    if (!file) {
      setMessage(els.uploadMessage, "Choose a file first.", "error");
      return;
    }

    try {
      setMessage(els.uploadMessage, "Uploading...", "");
      const result = await uploadDocument(file);
      setMessage(els.uploadMessage, `${result.message} (${result.chunk_count} chunks)`, "success");
    } catch (error) {
      setMessage(els.uploadMessage, error.message, "error");
    }
  });
}

function wireQueryForm() {
  document.getElementById("queryForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!state.token) {
      addBubble("assistant", "Please sign in first.");
      return;
    }
    const query = els.queryInput.value.trim();
    if (!query) return;

    addBubble("user", query);
    els.queryInput.value = "";

    const assistantTextNode = addBubble("assistant", "Thinking...");
    streamingBubbleText = assistantTextNode;

    try {
      if (els.streamToggle.checked) {
        assistantTextNode.textContent = "";
        await sendStreamingQuery(query);
      } else {
        const answer = await sendNonStreamingQuery(query);
        assistantTextNode.textContent = answer;
      }
    } catch (error) {
      assistantTextNode.textContent = `Error: ${error.message}`;
    } finally {
      streamingBubbleText = null;
    }
  });
}

async function init() {
  wireTabs();
  wireAuthForms();
  wireUploadForm();
  wireQueryForm();
  updateAuthUI();
  await refreshUser();
}

init();
