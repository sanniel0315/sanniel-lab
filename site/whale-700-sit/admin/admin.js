const REPO = "sanniel0315/sanniel-lab";
const ISSUE_URL = `https://github.com/${REPO}/issues/new`;
const state = { mode: "test", tests: [], questions: [], records: [], selected: null, meta: {} };

const $ = id => document.getElementById(id);
const text = value => value == null ? "" : String(value);

async function loadData() {
  const manifest = await fetch("../data-manifest.json", { cache: "no-store" }).then(r => {
    if (!r.ok) throw new Error(`manifest ${r.status}`);
    return r.json();
  });
  const testParts = await Promise.all(manifest.test_parts.map(file =>
    fetch(`../${file}`, { cache: "no-store" }).then(r => r.json())
  ));
  const questionParts = await Promise.all(manifest.question_parts.map(file =>
    fetch(`../${file}`, { cache: "no-store" }).then(r => r.json())
  ));
  state.meta = manifest.meta || {};
  state.tests = testParts.flat();
  state.questions = questionParts.flat();
  $("dataMeta").textContent =
    `資料來源：${state.meta.source || "GitHub JSON"}｜測項 ${state.tests.length}｜待釐清 ${state.questions.length}` +
    (state.meta.updated_at ? `｜更新：${state.meta.updated_at}` : "");
  setMode("test");
}

function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll(".mode-switch button").forEach(btn =>
    btn.classList.toggle("active", btn.dataset.mode === mode)
  );
  $("testFields").hidden = mode !== "test";
  $("questionFields").hidden = mode !== "question";
  $("search").value = "";
  state.records = mode === "test" ? state.tests : state.questions;
  renderOptions(state.records);
}

function recordLabel(item) {
  return state.mode === "test"
    ? `${item["編號"]}｜${item["判定"] || "未執行"}｜${item["測試項目"]}`
    : `${item["編號"]}｜${item["狀態"] || "Open"}｜${item["議題"]}`;
}

function renderOptions(records) {
  const select = $("recordSelect");
  select.innerHTML = "";
  records.forEach(item => {
    const option = document.createElement("option");
    option.value = item["編號"];
    option.textContent = recordLabel(item);
    select.appendChild(option);
  });
  if (records.length) {
    select.value = records[0]["編號"];
    selectRecord(records[0]["編號"]);
  } else {
    state.selected = null;
    $("recordTitle").textContent = "沒有符合項目";
  }
}

function filterRecords() {
  const keyword = $("search").value.trim().toLowerCase();
  const base = state.mode === "test" ? state.tests : state.questions;
  state.records = !keyword ? base : base.filter(item =>
    Object.values(item).map(text).join(" ").toLowerCase().includes(keyword)
  );
  renderOptions(state.records);
}

function selectRecord(id) {
  const base = state.mode === "test" ? state.tests : state.questions;
  const item = base.find(row => row["編號"] === id);
  if (!item) return;
  state.selected = item;
  $("recordType").textContent = state.mode === "test" ? "SIT TEST CASE" : "OPEN QUESTION";
  $("recordTitle").textContent = state.mode === "test"
    ? `${item["編號"]}｜${item["測試項目"]}`
    : `${item["編號"]}｜${item["議題"]}`;
  $("viewSource").href = state.mode === "test" ? `../?keyword=${encodeURIComponent(item["編號"])}` : "../#questions";
  if (state.mode === "test") fillTest(item); else fillQuestion(item);
  $("confirmAccuracy").checked = false;
  $("publishButton").disabled = true;
}

function fillTest(item) {
  $("testStatus").value = item["判定"] || "未執行";
  $("defectNo").value = text(item["缺失單號"]);
  $("measuredValue").value = text(item["V2 實測值"]);
  $("testNote").value = text(item["備註 / 待釐清"]);
  $("testReference").innerHTML = `<dl>
    <dt>分類／優先級</dt><dd>${escapeHtml(item["分類"])}／${escapeHtml(item["優先級"])}</dd>
    <dt>V1 對應</dt><dd>${escapeHtml(item["V1(0707)對應"])}</dd>
    <dt>規格依據</dt><dd>${escapeHtml(item["規格依據"])}</dd>
    <dt>前置條件</dt><dd>${escapeHtml(item["前置條件"])}</dd>
    <dt>測試步驟</dt><dd>${escapeHtml(item["測試方法 / 步驟"])}</dd>
    <dt>Pass 基準</dt><dd>${escapeHtml(item["判定基準 (Pass)"])}</dd>
    <dt>量測佐證</dt><dd>${escapeHtml(item["量測工具 / 佐證"])}</dd>
  </dl>`;
}

function fillQuestion(item) {
  $("questionStatus").value = item["狀態"] || "Open";
  $("dueDate").value = normalizeDate(item["期限"]);
  $("vendorReply").value = text(item["廠商回復"]);
  $("requiredItems").value = text(item["需提供專案"] ?? item["需提供項目"]);
  $("questionReference").innerHTML = `<dl>
    <dt>類別</dt><dd>${escapeHtml(item["類別"])}</dd>
    <dt>需求對象</dt><dd>${escapeHtml(item["需求對象"])}</dd>
    <dt>影響說明</dt><dd>${escapeHtml(item["說明 / 為何影響 SIT"])}</dd>
  </dl>`;
}

function normalizeDate(value) {
  if (!value) return "";
  const match = String(value).match(/^\d{4}-\d{2}-\d{2}/);
  return match ? match[0] : "";
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = text(value);
  return div.innerHTML.replace(/\n/g, "<br>");
}

function payloadForSelected() {
  if (!state.selected) throw new Error("未選擇項目");
  if (state.mode === "test") {
    return { schema: 1, type: "test", id: state.selected["編號"], changes: {
      "判定": $("testStatus").value,
      "V2 實測值": $("measuredValue").value.trim(),
      "缺失單號": $("defectNo").value.trim(),
      "備註 / 待釐清": $("testNote").value.trim()
    }};
  }
  return { schema: 1, type: "question", id: state.selected["編號"], changes: {
    "狀態": $("questionStatus").value,
    "期限": $("dueDate").value,
    "廠商回復": $("vendorReply").value.trim(),
    "需提供專案": $("requiredItems").value.trim()
  }};
}

function createIssueUrl(payload) {
  const summary = payload.type === "test"
    ? `${payload.changes["判定"]}｜${state.selected["測試項目"]}`
    : `${payload.changes["狀態"]}｜${state.selected["議題"]}`;
  const title = `[SIT-UPDATE] ${payload.id} ${summary}`.slice(0, 240);
  const body = [
    "## SANNIEL-LAB 線上更新", "", `- 類型：${payload.type === "test" ? "SIT 測試結果" : "待釐清事項"}`,
    `- 編號：${payload.id}`, "", "此 Issue 由 Whale-700 SIT 管理後台產生。請確認下方內容後送出；",
    "GitHub Actions 僅接受 Repository 擁有者建立的更新單。", "", "<!-- SANNIEL_SIT_UPDATE",
    JSON.stringify(payload, null, 2), "SANNIEL_SIT_UPDATE -->"
  ].join("\n");
  return `${ISSUE_URL}?${new URLSearchParams({ title, body }).toString()}`;
}

$("editForm").addEventListener("submit", event => {
  event.preventDefault();
  if (!$("confirmAccuracy").checked) return;
  window.open(createIssueUrl(payloadForSelected()), "_blank", "noopener,noreferrer");
});
$("confirmAccuracy").addEventListener("change", event => { $("publishButton").disabled = !event.target.checked; });
$("recordSelect").addEventListener("change", event => selectRecord(event.target.value));
$("search").addEventListener("input", filterRecords);
document.querySelectorAll(".mode-switch button").forEach(btn => btn.addEventListener("click", () => setMode(btn.dataset.mode)));
loadData().catch(error => { document.querySelector("main").innerHTML = `<p>資料載入失敗：${escapeHtml(error.message)}</p>`; });
