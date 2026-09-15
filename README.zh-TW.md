# 檔案證據清單 CLI
這是一個離線優先的小型命令列工具，用來替本機資料夾建立及驗證 SHA-256 完整性清單。
它不會上傳檔案，也不會把檔案內容寫進清單；輸出只包含相對路徑（或雜湊後的路徑識別碼）、檔案大小、UTC 修改時間及 SHA-256。若檔名本身敏感，可以使用 `--path-mode hashed`。
```powershell
python -m evidence_manifest create C:\資料夾 --output manifest.json
python -m evidence_manifest verify C:\資料夾 --manifest manifest.json
```
請注意：雜湊只能證明檔案自建立清單後是否改變，不能證明檔案由誰建立、事件何時發生，或內容是否真實。
本專案仍在早期階段，歡迎針對可重現問題提出範圍明確的 issue 或 pull request。
