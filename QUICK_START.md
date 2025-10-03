# 快速開始

3 步驟開始使用 SpringMVC Knowledge Graph Analyzer

## 前置需求

- Python 3.10+
- Node.js + Claude Code CLI: `npm install -g @anthropic-ai/claude-code`

## 步驟 1: 安裝專案

```bash
# Clone 或解壓縮專案
cd C:\Developer\springmvc-knowledge-graph

# 開發模式安裝（可編輯）
pip install -e .
```

這會安裝所有依賴並讓您可以直接修改程式碼。

## 步驟 2: 配置 Claude Code

```bash
python scripts/setup_claude.py
```

這個腳本會自動：
- ✅ 修改 `~/.claude_code/settings.json`
- ✅ 加入 MCP Server 配置
- ✅ 備份原始設定
- ✅ 測試連線

**輸出範例**：
```
=== SpringMVC Analyzer - Claude Code 設定 ===

✓ 已備份原始設定到: C:\Users\你\.claude_code\settings.json.backup
✓ Claude Code 已配置
  MCP Server: C:\Developer\springmvc-knowledge-graph\mcp_server\springmvc_mcp_server.py
  Settings: C:\Users\你\.claude_code\settings.json

測試 MCP Server 連線...
✓ MCP Server 測試通過

完成！請在 Claude Code 中測試。
```

## 步驟 3: 在 Claude Code 測試

打開 Claude Code，在對話中輸入：

```
請使用 springmvc-analyzer 分析我的專案
```

Claude 會自動調用 MCP tools 進行分析！

---

## 📌 常用操作

### 分析整個專案

```
User: 請分析 C:\myproject 這個 SpringMVC 專案

Claude: 我會使用 springmvc-analyzer 的工具來分析...
[自動調用 analyze_jsp_files, analyze_spring_controllers 等]
```

### 只分析特定層級

```
User: 只分析 Controller 層就好

Claude: [調用 mcp__springmvc-analyzer__analyze_spring_controllers]
```

### 查詢知識圖譜

```
User: 哪些 API 會操作 users 表？

Claude: [調用 mcp__springmvc-analyzer__query_knowledge_graph]
```

### 提取資料庫結構（不經過 LLM）

```
User: 提取 localhost 的 mydb 資料庫結構

Claude: [調用 mcp__springmvc-analyzer__extract_db_schema]
需要您提供資料庫密碼...
```

---

## 🔧 調整 Prompts

Prompts 位於 `mcp_server/prompts/`：

```bash
mcp_server/prompts/
├── procedure_analysis.txt  ✅ 已實作
├── jsp_analysis.txt        (Phase 3)
├── controller_analysis.txt (Phase 3)
├── service_analysis.txt    (Phase 3)
├── mybatis_analysis.txt    (Phase 3)
└── sql_analysis.txt        (Phase 3)
```

**修改後**：
1. 儲存檔案
2. 重啟 Claude Code（會自動重新載入 MCP Server）
3. 測試修改效果

詳見 [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) 了解開發進度

---

## 🚀 分享給其他人

### 方式 1: Git（推薦）

```bash
# 其他人執行
git clone [repo-url]
cd springmvc-knowledge-graph
pip install -e .
python scripts/setup_claude.py
```

### 方式 2: ZIP 檔案

1. 將整個專案打包成 zip
2. 對方解壓縮後執行：
   ```bash
   pip install -e .
   python scripts/setup_claude.py
   ```

---

## 🐛 疑難排解

### 問題 1: Claude Code 找不到 MCP Server

**解決方案**：
```bash
# 測試 MCP Server 是否正常
python scripts/test_mcp_server.py

# 重新配置
python scripts/setup_claude.py
```

### 問題 2: 工具調用失敗

**檢查**：
1. MCP Server 是否在運行
2. 查看 Claude Code 的錯誤訊息
3. 檢查 `~/.claude_code/settings.json` 中的路徑是否正確

### 問題 3: 修改 Prompt 後沒有生效

**解決方案**：
- 重啟 Claude Code
- 或重新載入 settings

---

## 📚 下一步

- 閱讀 [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) 了解完整開發計畫
- 閱讀 [CLAUDE.md](CLAUDE.md) 了解架構設計與開發指引
- 查看 `mcp_server/prompts/procedure_analysis.txt` 了解 Prompt 設計
- 查看 `mcp_server/tools/` 中的已實作工具

---

## ⏱️ 預計時間

- 安裝: 5 分鐘
- 配置: 1 分鐘
- 測試: 2 分鐘

**總計：10 分鐘內開始使用！**
