const state = { data: null, filtered: [] };

const esc = (value) => {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
};

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function addOptions(id, values) {
  const select = document.getElementById(id);
  unique(values).forEach(value => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
}

function applyFilters() {
  const category = document.getElementById("category").value;
  const priority = document.getElementById("priority").value;
  const status = document.getElementById("status").value;
  const keyword = document.getElementById("keyword").value.trim().toLowerCase();

  state.filtered = state.data.tests.filter(item => {
    const text = Object.values(item).join(" ").toLowerCase();
    return (!category || item["分類"] === category)
      && (!priority || item["優先級"] === priority)
      && (!status || item["判定"] === status)
      && (!keyword || text.includes(keyword));
  });
  render();
}

function renderKpis() {
  const tests = state.filtered;
  const count = key => tests.filter(x => x["判定"] === key).length;
  const total = tests.length;
  const unexecuted = count("未執行");
  const completion = total ? ((total - unexecuted) / total * 100).toFixed(1) + "%" : "0.0%";
  const values = [
    ["測項數", total],
    ["P0", tests.filter(x => x["優先級"] === "P0").length],
    ["Pass", count("Pass")],
    ["Fail", count("Fail")],
    ["Pending", count("Pending")],
    ["N/A", count("N/A")],
    ["未執行", unexecuted],
    ["完成率", completion],
  ];
  document.getElementById("kpis").innerHTML = values
    .map(([label, value]) => `<div class="kpi"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
}

function renderBars() {
  const tests = state.filtered;
  const byCategory = {};
  tests.forEach(item => {
    const key = item["分類"];
    byCategory[key] ||= { total: 0, p0: 0 };
    byCategory[key].total += 1;
    byCategory[key].p0 += item["優先級"] === "P0" ? 1 : 0;
  });
  const maxCategory = Math.max(1, ...Object.values(byCategory).map(x => x.total));
  document.getElementById("categoryBars").innerHTML = Object.entries(byCategory)
    .map(([name, value]) => `
      <div class="bar-row">
        <span>${esc(name)}</span>
        <div>
          <div class="bar-track"><div class="bar" style="width:${value.total / maxCategory * 100}%"></div></div>
          <div class="bar-track" style="margin-top:.18rem"><div class="bar p0" style="width:${value.p0 / maxCategory * 100}%"></div></div>
        </div>
        <strong>${value.total}</strong>
      </div>`)
    .join("");

  const order = ["Pass", "Fail", "Pending", "N/A", "Doc", "未執行"];
  const counts = Object.fromEntries(order.map(key => [key, tests.filter(x => x["判定"] === key).length]));
  const maxStatus = Math.max(1, ...Object.values(counts));
  document.getElementById("statusBars").innerHTML = order
    .map(name => `
      <div class="bar-row">
        <span>${name}</span>
        <div class="bar-track"><div class="bar" style="width:${counts[name] / maxStatus * 100}%"></div></div>
        <strong>${counts[name]}</strong>
      </div>`)
    .join("");
}

function showTestDetail(id) {
  const item = state.data.tests.find(x => x["編號"] === id);
  if (!item) return;
  const fields = [
    ["測試項目", item["測試項目"]],
    ["規格依據", item["規格依據"]],
    ["前置條件", item["前置條件"]],
    ["測試方法 / 步驟", item["測試方法 / 步驟"]],
    ["判定基準", item["判定基準 (Pass)"]],
    ["量測工具 / 佐證", item["量測工具 / 佐證"]],
    ["V2 實測值", item["V2 實測值"]],
    ["備註 / 待釐清", item["備註 / 待釐清"]],
  ];
  document.getElementById("testDetail").innerHTML =
    `<h3>${esc(item["編號"])}｜${esc(item["測試項目"])}</h3><dl>` +
    fields.map(([label, value]) => `<dt>${label}</dt><dd>${esc(value)}</dd>`).join("") +
    `</dl>`;
}

function renderTests() {
  document.getElementById("testRows").innerHTML = state.filtered.map(item => `
    <tr data-id="${esc(item["編號"])}">
      <td>${esc(item["編號"])}</td>
      <td>${esc(item["分類"])}</td>
      <td>${esc(item["測試項目"])}</td>
      <td>${esc(item["優先級"])}</td>
      <td class="status ${esc(item["判定"])}">${esc(item["判定"])}</td>
      <td>${esc(item["V2 實測值"])}</td>
      <td>${esc(item["缺失單號"])}</td>
    </tr>`).join("");

  document.querySelectorAll("#testRows tr").forEach(row => {
    row.addEventListener("click", () => showTestDetail(row.dataset.id));
  });
  if (state.filtered[0]) showTestDetail(state.filtered[0]["編號"]);
  else document.getElementById("testDetail").innerHTML = "<p>目前沒有符合的測項。</p>";
}

function renderQuestions() {
  document.getElementById("questionRows").innerHTML = state.data.questions.map(item => `
    <tr>
      <td>${esc(item["編號"])}</td>
      <td>${esc(item["類別"])}</td>
      <td>${esc(item["議題"])}</td>
      <td>${esc(item["需求對象"])}</td>
      <td>${esc(item["期限"])}</td>
      <td class="status ${esc(item["狀態"])}">${esc(item["狀態"])}</td>
    </tr>`).join("");
}

function render() {
  renderKpis();
  renderBars();
  renderTests();
  renderQuestions();
}

fetch("data.json")
  .then(response => response.json())
  .then(data => {
    state.data = data;
    state.filtered = data.tests;
    addOptions("category", data.tests.map(x => x["分類"]));
    addOptions("priority", data.tests.map(x => x["優先級"]));
    addOptions("status", ["未執行", "Pass", "Fail", "Pending", "N/A", "Doc"]);
    ["category", "priority", "status"].forEach(id =>
      document.getElementById(id).addEventListener("change", applyFilters)
    );
    document.getElementById("keyword").addEventListener("input", applyFilters);
    render();
  })
  .catch(error => {
    document.querySelector("main").innerHTML =
      `<p>資料載入失敗：${esc(error.message)}</p>`;
  });
