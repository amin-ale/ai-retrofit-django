const tenantField = document.getElementById("tenant");
const statusField = document.getElementById("status");

function tenant() {
  return tenantField.value.trim();
}

async function refreshStatus() {
  const response = await fetch(`/copilot/status?tenant=${encodeURIComponent(tenant())}`);
  if (!response.ok) {
    statusField.value = "unavailable";
    return;
  }
  const data = await response.json();
  statusField.value = data.enabled ? `enabled · ${data.remaining_tokens} tokens left` : "disabled";
}

async function postJson(path, payload) {
  return fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

async function streamSse(path, payload, onEvent) {
  const response = await postJson(path, payload);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: response.statusText }));
    onEvent({ event: "error", detail: error });
    return;
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop();
    for (const chunk of chunks) {
      const line = chunk.replace(/^data: /, "").trim();
      if (line) onEvent(JSON.parse(line));
    }
  }
}

async function runSearch() {
  const out = document.getElementById("search-out");
  out.textContent = "…";
  const response = await postJson("/copilot/search", {
    tenant: tenant(),
    query: document.getElementById("search-q").value,
  });
  const data = await response.json();
  out.textContent = response.ok
    ? data.results.map((r) => `${r.score.toFixed(3)}  #${r.source_pk}  ${r.content.slice(0, 90)}`).join("\n")
    : `Error: ${data.error}`;
}

async function runAsk() {
  const sql = document.getElementById("ask-sql");
  const rows = document.getElementById("ask-rows");
  const answer = document.getElementById("ask-answer");
  sql.textContent = rows.textContent = answer.textContent = "";
  await streamSse("/copilot/ask", { tenant: tenant(), question: document.getElementById("ask-q").value }, (event) => {
    if (event.event === "sql") sql.textContent = event.sql;
    else if (event.event === "rows") rows.textContent = `${event.columns.join(" | ")}\n` + event.rows.map((r) => r.join(" | ")).join("\n");
    else if (event.event === "token") answer.textContent += event.text;
    else if (event.event === "error") sql.textContent = `Blocked: ${event.detail.reason || event.detail.error}`;
  });
  refreshStatus();
}

async function runSummarize() {
  const out = document.getElementById("sum-out");
  out.textContent = "";
  await streamSse("/copilot/summarize", { tenant: tenant(), ticket_id: document.getElementById("sum-id").value }, (event) => {
    if (event.event === "token") out.textContent += event.text;
    else if (event.event === "error") out.textContent = `Error: ${event.detail.error}`;
  });
  refreshStatus();
}

const actions = { search: runSearch, ask: runAsk, summarize: runSummarize };

document.querySelectorAll("button[data-action]").forEach((button) => {
  button.addEventListener("click", () => actions[button.dataset.action]());
});

tenantField.addEventListener("change", refreshStatus);
refreshStatus();
