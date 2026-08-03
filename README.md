# sanniel-lab

史哲政 Zhe-Zheng Shi 的學術個人頁。

**https://sanniel0315.github.io/sanniel-lab/**

## 結構

```
site/
  index.html      單頁內容
  style.css       全部樣式
  files/          CV、研究摘要（PDF）與論文圖表
.github/workflows/deploy.yaml
```

沒有建置步驟。`site/` 就是實際部署的內容，改完 push 即可。

## 部署

push 到 `main` 觸發 GitHub Actions，直接把 `site/` 發佈到 Pages。

workflow 有一道必要檔案檢查：純靜態站缺檔不會有任何錯誤訊息，
會安靜地部署一個壞掉的網站，所以那一步是唯一的把關。

## 本機預覽

```sh
python -m http.server 8000 --directory site
```

## 內容來源

論文圖表出自碩士論文與 CACS 2026 投稿稿件。
CV 與研究摘要由私有 vault 的 markdown 以 pandoc 產生，不在本 repo 內編輯。
