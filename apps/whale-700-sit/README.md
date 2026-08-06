# Whale-700 SIT Dashboard

Whale-700 視覺化雷達軟體的資料驅動 SIT 會議介面。

## 成果

- `data/Whale-700_SIT_Dashboard.xlsx`：獨立下載包內附的完整 Excel；GitHub 版可使用 JSON 快照或上傳最新版 Excel。
- `streamlit_app.py`：直接讀取 Excel 的互動式 Streamlit 網頁。
- `site/whale-700-sit/`：GitHub Pages 可直接發布的靜態會議頁面（位於 Repo 根目錄）。
- `scripts/export_data.py`：Excel 更新後，重新輸出靜態頁面需要的 JSON。

## 本機執行

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 更新資料

日常只需更新 Excel 的：

- `1_SIT主表`：K～N 欄
- `3_待釐清事項`：期限與狀態

Streamlit 可直接上傳最新版 Excel。若要同步更新 GitHub Pages 的靜態快照：

```bash
python apps/whale-700-sit/scripts/export_data.py <最新版SIT.xlsx> site/whale-700-sit/data.json
```

## Streamlit Community Cloud

建立 App 時設定：

- Repository：`sanniel0315/sanniel-lab`
- Branch：包含本專案的分支或合併後的 `main`
- Main file path：`apps/whale-700-sit/streamlit_app.py`

> GitHub Pages 執行的是 `site/whale-700-sit/` 靜態版本；完整 Streamlit 互動版需由 Streamlit 執行環境啟動。
