# SANNIEL-LAB 線上修改流程

## 使用入口

- 公開儀表板：`https://sanniel0315.github.io/sanniel-lab/whale-700-sit/`
- 管理後台：`https://sanniel0315.github.io/sanniel-lab/whale-700-sit/admin/`

## 修改測試結果

1. 在管理後台選擇 **SIT 測試結果**。
2. 搜尋並選擇 SIT 編號。
3. 填寫判定、V2 實測值、缺失單號與備註。
4. 勾選確認，按 **送出 GitHub 更新單**。
5. GitHub 頁面開啟後，登入 `sanniel0315`，確認內容並按 **Submit new issue**。
6. `Apply Whale-700 SIT update` Workflow 驗證操作者、更新 JSON、Commit 至 `main`、關閉 Issue。
7. 原有 GitHub Pages Workflow 自動重新發布公開儀表板。

## 驗證規則

- 只有 Repository 擁有者建立的 `[SIT-UPDATE]` Issue 會生效。
- `Pass` 必須填寫 V2 實測值或佐證摘要。
- `Fail` 必須填寫缺失單號。
- 支援狀態：`未執行`、`Pass`、`Fail`、`Pending`、`N/A`、`Doc`。
- 待釐清事項支援：`Open`、`In Progress`、`Blocked`、`Closed`。

## 稽核紀錄

每次更新均保留：

- GitHub 操作者
- Issue 編號與內容
- Commit SHA 與差異
- GitHub Actions 執行紀錄
- GitHub Pages 發布紀錄

公開網站維持唯讀，避免未授權修改驗收資料。
