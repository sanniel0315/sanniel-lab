from __future__ import annotations

import io
import json
from pathlib import Path
from typing import BinaryIO

import altair as alt
import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DEFAULT_WORKBOOK_CANDIDATES = [
    APP_DIR / "data" / "Whale-700_SIT_Dashboard.xlsx",
    APP_DIR.parent.parent / "site" / "files" / "Whale-700_SIT_互動會議儀表板_20260806.xlsx",
]
DEFAULT_WORKBOOK = next(
    (path for path in DEFAULT_WORKBOOK_CANDIDATES if path.exists()),
    None,
)
DEFAULT_JSON_CANDIDATES = [
    APP_DIR / "static" / "data.json",
    APP_DIR.parent.parent / "site" / "whale-700-sit" / "data.json",
]
DEFAULT_JSON = next(
    (path for path in DEFAULT_JSON_CANDIDATES if path.exists()),
    DEFAULT_JSON_CANDIDATES[0],
)

SIT_SHEET = "1_SIT主表"
QUESTION_SHEET = "3_待釐清事項"
INFO_SHEET = "0_SIT說明"

NAVY = "#1F3864"
TEXT = "#1A1A1A"
MUTED = "#666666"
RULE = "#E5E5E5"
PASS = "#548235"
FAIL = "#C00000"
PENDING = "#ED7D31"
UNEXECUTED = "#8C8C8C"


st.set_page_config(
    page_title="Whale-700 SIT Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
      :root {{
        --navy: {NAVY};
        --text: {TEXT};
        --muted: {MUTED};
        --rule: {RULE};
      }}

      html, body, [class*="css"] {{
        font-family: "Noto Sans TC", "Microsoft JhengHei", -apple-system,
          BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      }}

      .stApp {{
        background: #ffffff;
        color: var(--text);
      }}

      [data-testid="stHeader"] {{
        background: rgba(255, 255, 255, 0.96);
        border-bottom: 1px solid #dddddd;
      }}

      [data-testid="stSidebar"] {{
        background: #ffffff;
        border-right: 1px solid #dddddd;
      }}

      .block-container {{
        max-width: 1500px;
        padding-top: 2.2rem;
        padding-bottom: 3rem;
      }}

      h1 {{
        color: var(--navy);
        font-size: 2rem !important;
        font-weight: 650 !important;
        letter-spacing: 0.01em;
        margin-bottom: 0.15rem !important;
      }}

      h2 {{
        color: var(--text);
        font-size: 1.2rem !important;
        font-weight: 650 !important;
        padding-top: 1.4rem;
        border-top: 1px solid var(--rule);
      }}

      h3 {{
        color: var(--text);
        font-size: 1rem !important;
        font-weight: 650 !important;
      }}

      .subtitle {{
        color: var(--muted);
        font-size: 0.94rem;
        line-height: 1.7;
        margin-bottom: 1.4rem;
      }}

      [data-testid="stMetric"] {{
        background: #ffffff;
        border-top: 2px solid var(--navy);
        border-bottom: 1px solid var(--rule);
        border-radius: 0;
        padding: 0.75rem 0.85rem;
      }}

      [data-testid="stMetricLabel"] {{
        color: var(--muted);
        font-size: 0.85rem;
      }}

      [data-testid="stMetricValue"] {{
        color: var(--navy);
        font-weight: 650;
      }}

      .stButton > button,
      .stDownloadButton > button {{
        border: 1px solid var(--navy);
        border-radius: 0;
        background: #ffffff;
        color: var(--navy);
      }}

      .stButton > button:hover,
      .stDownloadButton > button:hover {{
        background: #f6f8fb;
        border-color: var(--navy);
        color: var(--navy);
      }}

      div[data-baseweb="select"] > div,
      div[data-baseweb="input"] > div {{
        border-radius: 0 !important;
      }}

      [data-testid="stDataFrame"] {{
        border: 1px solid var(--rule);
      }}

      .status-line {{
        padding-left: 0.9rem;
        border-left: 2px solid var(--navy);
        color: var(--text);
        line-height: 1.75;
        margin: 0.5rem 0 1rem;
      }}

      .muted {{
        color: var(--muted);
        font-size: 0.88rem;
      }}

      .detail-label {{
        color: var(--muted);
        font-size: 0.82rem;
        margin-bottom: 0.15rem;
      }}

      .detail-value {{
        color: var(--text);
        line-height: 1.75;
        white-space: pre-wrap;
        border-bottom: 1px solid var(--rule);
        padding-bottom: 0.7rem;
        margin-bottom: 0.85rem;
      }}

      .gate {{
        border-left: 2px solid var(--navy);
        padding: 0.7rem 0 0.7rem 1rem;
        margin-bottom: 0.8rem;
      }}

      footer {{ visibility: hidden; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def _read_bytes(source: Path | BinaryIO) -> bytes:
    if isinstance(source, Path):
        return source.read_bytes()
    source.seek(0)
    return source.read()


@st.cache_data(show_spinner=False)
def load_sit_workbook(raw_bytes: bytes) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    book = io.BytesIO(raw_bytes)

    sit = pd.read_excel(book, sheet_name=SIT_SHEET, dtype=object, engine="openpyxl")
    sit = sit[sit["編號"].astype(str).str.match(r"^SIT-", na=False)].copy()
    sit["判定"] = sit["判定"].fillna("未執行").replace("", "未執行")
    sit["優先級"] = sit["優先級"].fillna("")
    sit["分類"] = sit["分類"].fillna("")
    sit["V2 實測值"] = sit["V2 實測值"].fillna("")
    sit["缺失單號"] = sit["缺失單號"].fillna("")
    sit["備註 / 待釐清"] = sit["備註 / 待釐清"].fillna("")

    book.seek(0)
    questions = pd.read_excel(
        book, sheet_name=QUESTION_SHEET, dtype=object, engine="openpyxl"
    )
    questions = questions[questions["編號"].astype(str).str.match(r"^Q-", na=False)].copy()
    questions["狀態"] = questions["狀態"].fillna("Open").replace("", "Open")
    questions["期限"] = pd.to_datetime(questions["期限"], errors="coerce")

    book.seek(0)
    info = pd.read_excel(
        book, sheet_name=INFO_SHEET, header=None, dtype=object, engine="openpyxl"
    )
    return sit, questions, info



@st.cache_data(show_spinner=False)
def load_snapshot_json(path: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    sit = pd.DataFrame(payload["tests"])
    questions = pd.DataFrame(payload["questions"])
    sit["判定"] = sit["判定"].fillna("未執行").replace("", "未執行")
    for column in ["優先級", "分類", "V2 實測值", "缺失單號", "備註 / 待釐清"]:
        sit[column] = sit[column].fillna("")
    questions["狀態"] = questions["狀態"].fillna("Open").replace("", "Open")
    questions["期限"] = pd.to_datetime(questions["期限"], errors="coerce")
    info = pd.DataFrame(
        [
            ["資料模式", "GitHub 內建 JSON 快照"],
            ["更新方式", "上傳最新版 SIT Excel 即時覆蓋目前畫面"],
            ["完整 Excel", "請使用本專案交付之 Excel 儀表板檔案"],
        ],
        columns=["項目", "內容"],
    )
    return sit, questions, info


def filtered_tests(
    source: pd.DataFrame,
    categories: list[str],
    priorities: list[str],
    statuses: list[str],
    keyword: str,
) -> pd.DataFrame:
    result = source.copy()
    if categories:
        result = result[result["分類"].isin(categories)]
    if priorities:
        result = result[result["優先級"].isin(priorities)]
    if statuses:
        result = result[result["判定"].isin(statuses)]
    if keyword.strip():
        needle = keyword.strip()
        searchable = result.fillna("").astype(str).agg(" ".join, axis=1)
        result = result[searchable.str.contains(needle, case=False, regex=False)]
    return result


def metric_counts(df: pd.DataFrame) -> dict[str, float | int]:
    total = len(df)
    counts = df["判定"].value_counts().to_dict()
    completed = total - int(counts.get("未執行", 0))
    return {
        "total": total,
        "p0": int((df["優先級"] == "P0").sum()),
        "pass": int(counts.get("Pass", 0)),
        "fail": int(counts.get("Fail", 0)),
        "pending": int(counts.get("Pending", 0)),
        "unexecuted": int(counts.get("未執行", 0)),
        "completion": completed / total if total else 0,
    }


def value_html(label: str, value: object) -> str:
    display = "" if pd.isna(value) else str(value)
    return (
        f'<div class="detail-label">{label}</div>'
        f'<div class="detail-value">{display}</div>'
    )


uploaded = st.sidebar.file_uploader(
    "上傳最新版 SIT Excel",
    type=["xlsx"],
    help="未上傳時使用 GitHub 專案內建的資料快照。",
)
if uploaded is not None:
    raw = _read_bytes(uploaded)
    sit, questions, info = load_sit_workbook(raw)
    workbook_bytes: bytes | None = raw
elif DEFAULT_WORKBOOK is not None:
    raw = _read_bytes(DEFAULT_WORKBOOK)
    sit, questions, info = load_sit_workbook(raw)
    workbook_bytes = raw
else:
    sit, questions, info = load_snapshot_json(str(DEFAULT_JSON))
    workbook_bytes = None

st.sidebar.markdown("### 篩選條件")
selected_categories = st.sidebar.multiselect(
    "分類",
    options=sit["分類"].dropna().drop_duplicates().tolist(),
)
selected_priorities = st.sidebar.multiselect(
    "優先級",
    options=["P0", "P1", "P2"],
)
selected_statuses = st.sidebar.multiselect(
    "判定",
    options=["未執行", "Pass", "Fail", "Pending", "N/A", "Doc"],
)
keyword = st.sidebar.text_input("全文搜尋", placeholder="編號、項目、規格或備註")

view = filtered_tests(
    sit,
    selected_categories,
    selected_priorities,
    selected_statuses,
    keyword,
)
metrics = metric_counts(view)

st.title("Whale-700 視覺化雷達軟體 SIT")
st.markdown(
    '<div class="subtitle">'
    "系統整合測試會議儀表板｜Excel 為單一資料來源，"
    "更新主表後重新載入即可同步呈現。"
    "</div>",
    unsafe_allow_html=True,
)

tabs = st.tabs(["執行總覽", "測試項目", "待釐清事項", "驗收判定", "SIT 說明"])

with tabs[0]:
    cols = st.columns(6)
    cols[0].metric("篩選後測項", f"{metrics['total']}")
    cols[1].metric("P0 必過", f"{metrics['p0']}")
    cols[2].metric("Pass", f"{metrics['pass']}")
    cols[3].metric("Fail", f"{metrics['fail']}")
    cols[4].metric("Pending", f"{metrics['pending']}")
    cols[5].metric("完成率", f"{metrics['completion']:.1%}")

    left, right = st.columns([1.35, 1])

    with left:
        st.subheader("各分類測項與 P0")
        category = (
            view.groupby("分類", dropna=False)
            .agg(
                項目數=("編號", "count"),
                P0=("優先級", lambda x: int((x == "P0").sum())),
            )
            .reset_index()
        )
        long_category = category.melt(
            id_vars="分類",
            value_vars=["項目數", "P0"],
            var_name="指標",
            value_name="數量",
        )
        chart = (
            alt.Chart(long_category)
            .mark_bar()
            .encode(
                x=alt.X("分類:N", sort=None, axis=alt.Axis(labelAngle=-25)),
                y=alt.Y("數量:Q", title="數量"),
                color=alt.Color(
                    "指標:N",
                    scale=alt.Scale(
                        domain=["項目數", "P0"],
                        range=[NAVY, "#9AA9BE"],
                    ),
                    legend=alt.Legend(orient="bottom"),
                ),
                xOffset="指標:N",
                tooltip=["分類", "指標", "數量"],
            )
            .properties(height=360)
        )
        st.altair_chart(chart, use_container_width=True)

    with right:
        st.subheader("執行狀態分布")
        status_order = ["Pass", "Fail", "Pending", "N/A", "Doc", "未執行"]
        status_counts = (
            view["判定"]
            .value_counts()
            .reindex(status_order, fill_value=0)
            .rename_axis("狀態")
            .reset_index(name="數量")
        )
        status_chart = (
            alt.Chart(status_counts)
            .mark_bar()
            .encode(
                x=alt.X("數量:Q", title="數量"),
                y=alt.Y("狀態:N", sort=status_order, title=None),
                color=alt.Color(
                    "狀態:N",
                    scale=alt.Scale(
                        domain=status_order,
                        range=[
                            PASS,
                            FAIL,
                            PENDING,
                            "#A5A5A5",
                            "#5B9BD5",
                            UNEXECUTED,
                        ],
                    ),
                    legend=None,
                ),
                tooltip=["狀態", "數量"],
            )
            .properties(height=360)
        )
        st.altair_chart(status_chart, use_container_width=True)

    st.subheader("會議用測項清單")
    overview_columns = [
        "編號",
        "分類",
        "測試項目",
        "優先級",
        "判定",
        "V2 實測值",
        "缺失單號",
        "備註 / 待釐清",
    ]
    st.dataframe(
        view[overview_columns],
        use_container_width=True,
        hide_index=True,
        height=430,
    )
    st.download_button(
        "下載目前篩選結果（CSV）",
        data=view[overview_columns].to_csv(index=False).encode("utf-8-sig"),
        file_name="Whale-700_SIT_filtered.csv",
        mime="text/csv",
    )

with tabs[1]:
    st.subheader("單項測試完整內容")
    if view.empty:
        st.warning("目前篩選條件沒有符合的測項。")
    else:
        item_id = st.selectbox("選擇 SIT 編號", view["編號"].tolist())
        item = sit.loc[sit["編號"] == item_id].iloc[0]

        headline = st.columns([1.3, 1, 1, 1])
        headline[0].metric("編號", item["編號"])
        headline[1].metric("分類", item["分類"])
        headline[2].metric("優先級", item["優先級"])
        headline[3].metric("判定", item["判定"])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(value_html("測試項目", item["測試項目"]), unsafe_allow_html=True)
            st.markdown(value_html("規格依據", item["規格依據"]), unsafe_allow_html=True)
            st.markdown(value_html("前置條件", item["前置條件"]), unsafe_allow_html=True)
            st.markdown(
                value_html("測試方法 / 步驟", item["測試方法 / 步驟"]),
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                value_html("判定基準（Pass）", item["判定基準 (Pass)"]),
                unsafe_allow_html=True,
            )
            st.markdown(
                value_html("量測工具 / 佐證", item["量測工具 / 佐證"]),
                unsafe_allow_html=True,
            )
            st.markdown(value_html("V1 對應", item["V1(0707)對應"]), unsafe_allow_html=True)
            st.markdown(value_html("V2 實測值", item["V2 實測值"]), unsafe_allow_html=True)
            st.markdown(value_html("缺失單號", item["缺失單號"]), unsafe_allow_html=True)
            st.markdown(
                value_html("備註 / 待釐清", item["備註 / 待釐清"]),
                unsafe_allow_html=True,
            )

with tabs[2]:
    open_count = int((questions["狀態"] == "Open").sum())
    no_due = int(
        ((questions["狀態"] != "Closed") & questions["期限"].isna()).sum()
    )
    qcols = st.columns(4)
    qcols[0].metric("議題總數", len(questions))
    qcols[1].metric("Open", open_count)
    qcols[2].metric("未填期限", no_due)
    qcols[3].metric("Closed", int((questions["狀態"] == "Closed").sum()))

    q_status = st.multiselect(
        "議題狀態",
        options=["Open", "In Progress", "Blocked", "Closed"],
        default=["Open", "In Progress", "Blocked"],
    )
    q_view = questions[questions["狀態"].isin(q_status)] if q_status else questions

    st.dataframe(
        q_view[
            ["編號", "類別", "議題", "需求對象", "需提供項目", "期限", "狀態"]
        ],
        use_container_width=True,
        hide_index=True,
        height=420,
        column_config={
            "期限": st.column_config.DateColumn("期限", format="YYYY/MM/DD"),
        },
    )

    if not q_view.empty:
        q_id = st.selectbox("查看議題明細", q_view["編號"].tolist())
        question = questions.loc[questions["編號"] == q_id].iloc[0]
        st.markdown(
            '<div class="status-line">'
            f"<strong>{question['編號']}｜{question['議題']}</strong><br>"
            f"需求對象：{question['需求對象']}｜狀態：{question['狀態']}"
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            value_html("說明 / 為何影響 SIT", question["說明 / 為何影響 SIT"]),
            unsafe_allow_html=True,
        )
        st.markdown(
            value_html("需提供項目", question["需提供項目"]),
            unsafe_allow_html=True,
        )

with tabs[3]:
    p0 = sit[sit["優先級"] == "P0"]
    p0_pass = int((p0["判定"] == "Pass").sum())
    p0_fail = int((p0["判定"] == "Fail").sum())
    p0_pending = int((p0["判定"] == "Pending").sum())
    p0_unexecuted = int((p0["判定"] == "未執行").sum())
    open_questions = int((questions["狀態"] != "Closed").sum())

    if p0_fail > 0:
        decision = "目前不符合驗收條件：存在 P0 Fail。"
    elif p0_pass == len(p0) and len(p0) > 0:
        decision = "P0 已全數通過；仍應確認 P1 改善事項與文件交付。"
    else:
        decision = "尚未具備最終驗收判定條件：P0 尚未全數執行並通過。"

    st.markdown(f'<div class="status-line"><strong>{decision}</strong></div>', unsafe_allow_html=True)

    gate1 = "完成" if open_questions == 0 else f"未完成（尚有 {open_questions} 項未關閉）"
    gate2 = (
        "完成"
        if p0_pass == len(p0) and len(p0) > 0
        else f"未完成（Pass {p0_pass}/{len(p0)}，Fail {p0_fail}，Pending {p0_pending}，未執行 {p0_unexecuted}）"
    )
    p1_fail = int(((sit["優先級"] == "P1") & (sit["判定"] == "Fail")).sum())
    gate3 = "完成" if p1_fail == 0 else f"需改善計畫（P1 Fail：{p1_fail}）"

    st.markdown(
        f"""
        <div class="gate"><strong>Gate 1｜前置條件與待釐清事項</strong><br>{gate1}</div>
        <div class="gate"><strong>Gate 2｜P0 驗收必過項</strong><br>{gate2}</div>
        <div class="gate"><strong>Gate 3｜P1 改善與期限</strong><br>{gate3}</div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("P0 驗收清單")
    st.dataframe(
        p0[["編號", "分類", "測試項目", "判定", "缺失單號"]],
        use_container_width=True,
        hide_index=True,
        height=480,
    )

with tabs[4]:
    st.subheader("SIT 文件說明")
    info_display = info.iloc[:, :2].copy()
    if list(info_display.columns) != ["項目", "內容"]:
        info_display.columns = ["項目", "內容"]
    info_display = info_display.dropna(how="all")
    st.dataframe(info_display, use_container_width=True, hide_index=True, height=600)

st.sidebar.divider()
if workbook_bytes is not None:
    st.sidebar.download_button(
        "下載目前 Excel",
        data=workbook_bytes,
        file_name="Whale-700_SIT_Dashboard.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.sidebar.caption("目前使用 GitHub 資料快照；上傳 Excel 後即可在此下載目前版本。")
st.sidebar.caption("資料解析只在目前 App 執行環境中進行。")
