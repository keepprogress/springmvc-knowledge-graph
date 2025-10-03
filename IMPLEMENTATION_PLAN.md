# SpringMVC Knowledge Graph - 實作計畫

## 專案概述

使用 Claude Agent SDK 和 MCP Protocol 建立 SpringMVC + JSP + MyBatis 專案的自動化知識圖譜分析系統。

**追蹤路徑**: JSP (includes, AJAX) → Controller → Service → Mapper → SQL → Oracle Tables/Procedures

---

## Phase 1: 基礎設施建設 ✅

### 1.1 專案結構 ✅
- [x] 建立專案目錄結構
- [x] 建立 requirements.txt
- [x] 建立 setup.py
- [x] 建立 .gitignore

### 1.2 快速啟動工具 ✅
- [x] QUICK_START.md（3步驟安裝指南）
- [x] scripts/setup_claude.py（自動配置 Claude Code）
- [x] scripts/test_mcp_server.py（測試工具）

### 1.3 Oracle 資料庫配置 ✅
- [x] config/oracle_config.example.yaml（連線配置範例）
- [x] 環境變數密碼管理（ORACLE_DEV_PASSWORD 等）

### 1.4 資料庫 Schema 提取器 ✅
- [x] mcp_server/tools/db_extractor.py
  - [x] 提取 Tables（欄位、型別、長度、非空、主鍵、索引、外鍵）
  - [x] 提取 Views
  - [x] 提取 Sequences
  - [x] 提取 Synonyms（本地/遠端同義詞）
  - [x] 提取 Procedures/Functions（含 Package 中的）
  - [x] 提取 Oracle Jobs（user_scheduler_jobs + user_jobs）
  - [x] 解析 Job Action 中的 Procedure 調用

### 1.5 Procedure 深度分析 ✅
- [x] mcp_server/prompts/procedure_analysis.txt（8維度分析 Prompt）
  - [x] 業務用途分析
  - [x] 操作類型分類
  - [x] 影響範圍分析
  - [x] 觸發方式分析（Oracle Trigger/Scheduler/Java BatchJob/Manual）
  - [x] 異常處理與事務評估
  - [x] 與 BatchJob 衝突分析
  - [x] BatchJob 整合建議（含難易度評估）
  - [x] 風險評估與優化建議
- [x] mcp_server/tools/procedure_analyzer.py

---

## Phase 2: MCP Server 骨架 🔄

### 2.1 Base Tool 類別 🔄
- [ ] mcp_server/tools/base_tool.py
  - [ ] Claude Agent SDK 整合
  - [ ] 檔案讀寫管理
  - [ ] 錯誤處理
  - [ ] 結果快取機制
  - [ ] 批次分析支援

### 2.2 MCP Server 主程式
- [ ] mcp_server/springmvc_mcp_server.py
  - [ ] MCP Protocol 實作
  - [ ] Tool 註冊機制
  - [ ] Slash Command 註冊機制
  - [ ] 錯誤處理與日誌
  - [ ] 狀態管理

---

## Phase 3: 程式碼分析工具 📝

### 3.1 JSP 分析器
- [ ] mcp_server/prompts/jsp_analysis.txt
  - [ ] JSP include 關係分析
  - [ ] AJAX 呼叫提取（$.ajax, fetch）
  - [ ] Form submit 目標分析
  - [ ] URL 路徑解析
  - [ ] EL 表達式分析
- [ ] mcp_server/tools/jsp_analyzer.py
  - [ ] 解析 JSP 檔案（lxml）
  - [ ] 提取靜態 include 與動態 include
  - [ ] 提取 JavaScript 中的 API 呼叫
  - [ ] 建立 JSP 依賴圖

### 3.2 Controller 分析器
- [ ] mcp_server/prompts/controller_analysis.txt
  - [ ] @RequestMapping 路徑分析
  - [ ] 請求方法（GET/POST/PUT/DELETE）
  - [ ] 參數綁定分析（@RequestParam, @PathVariable, @RequestBody）
  - [ ] @Autowired Service 依賴
  - [ ] 回傳類型分析（View name, JSON, Redirect）
- [ ] mcp_server/tools/controller_analyzer.py
  - [ ] 使用 javalang 解析 Java 檔案
  - [ ] 提取註解與參數
  - [ ] 分析方法呼叫鏈

### 3.3 Service 分析器
- [ ] mcp_server/prompts/service_analysis.txt
  - [ ] @Service 類別分析
  - [ ] @Autowired Mapper 依賴
  - [ ] 業務邏輯複雜度評估
  - [ ] 事務管理（@Transactional）
  - [ ] 異常處理分析
- [ ] mcp_server/tools/service_analyzer.py
  - [ ] 解析 Service 類別
  - [ ] 追蹤 Mapper 方法呼叫
  - [ ] 分析事務邊界

### 3.4 MyBatis Mapper 分析器
- [ ] mcp_server/prompts/mybatis_analysis.txt
  - [ ] Mapper 介面與 XML 對應
  - [ ] SQL 語句提取（select/insert/update/delete）
  - [ ] CALLABLE 類型（Stored Procedure 呼叫）
  - [ ] 動態 SQL 分析（if/choose/foreach）
  - [ ] ResultMap 映射分析
- [ ] mcp_server/tools/mybatis_analyzer.py
  - [ ] 解析 Mapper.xml（lxml）
  - [ ] 解析 Mapper Interface（javalang）
  - [ ] 提取 SQL 語句與參數
  - [ ] 輸出 mybatis_analysis.json

### 3.5 SQL 分析器
- [ ] mcp_server/prompts/sql_analysis.txt
  - [ ] SQL 語句解析（SELECT/INSERT/UPDATE/DELETE）
  - [ ] 表與欄位提取
  - [ ] JOIN 關係分析
  - [ ] WHERE 條件分析
  - [ ] 效能風險評估（全表掃描、缺少索引等）
- [ ] mcp_server/tools/sql_analyzer.py
  - [ ] 使用 sqlparse 或正則解析 SQL
  - [ ] 提取表名與欄位名
  - [ ] 與 db_schema.json 比對

---

## Phase 4: Slash Commands 設計 ⭐ (新增)

### 4.1 資料庫相關 Commands
```
/extract-oracle-schema [環境名稱]
  - 提取 Oracle Schema（dev/test/prod）
  - 輸出: output/db_schema.json

/analyze-procedure <procedure_name>
  - 深度分析單個 Procedure
  - 輸出: output/analysis/procedures/<name>.json

/analyze-all-procedures
  - 批次分析所有 Procedures
  - 輸出: output/analysis/procedures/

/list-oracle-jobs
  - 列出所有 Oracle Scheduler Jobs
  - 顯示調用的 Procedures
```

### 4.2 程式碼分析 Commands
```
/analyze-jsp <檔案路徑>
  - 分析單個 JSP 檔案
  - 提取 includes, AJAX 呼叫, Form 目標

/analyze-controller <類別名稱>
  - 分析 Controller 類別
  - 提取 RequestMapping 與 Service 依賴

/analyze-service <類別名稱>
  - 分析 Service 類別
  - 追蹤 Mapper 呼叫

/analyze-mapper <介面名稱>
  - 分析 MyBatis Mapper
  - 提取 SQL 語句與 Procedure 呼叫

/scan-project
  - 掃描整個專案
  - 批次分析所有 JSP, Controller, Service, Mapper
```

### 4.3 知識圖譜 Commands
```
/build-graph
  - 建立完整知識圖譜
  - 整合所有分析結果
  - 輸出: output/knowledge_graph.json

/query-path <起點> <終點>
  - 查詢兩個節點之間的路徑
  - 例如: /query-path userList.jsp UserService

/find-dependencies <節點名稱>
  - 查找節點的所有依賴（上游+下游）
  - 例如: /find-dependencies UserController

/find-procedure-callers <procedure_name>
  - 查找調用此 Procedure 的所有路徑
  - 包含: Triggers, Oracle Jobs, MyBatis Mappers

/visualize-graph [範圍]
  - 視覺化知識圖譜
  - 輸出 Mermaid/GraphViz 格式
```

### 4.4 報告生成 Commands
```
/generate-report <類型>
  - 類型: full/procedures/security/performance
  - 生成 Markdown 報告

/detect-conflicts
  - 檢測 Procedure 與 BatchJob 的潛在衝突
  - 輸出衝突清單與建議

/audit-transactions
  - 稽核事務管理
  - 檢查缺少 Rollback 的 Procedures
```

### 4.5 實用工具 Commands
```
/status
  - 顯示當前分析狀態
  - 已分析檔案數、快取狀態

/clear-cache [工具名稱]
  - 清除快取，強制重新分析

/config
  - 顯示當前配置（Oracle 連線、輸出目錄等）
```

### 4.6 Slash Commands 實作檔案
- [ ] mcp_server/commands/__init__.py
- [ ] mcp_server/commands/database_commands.py
  - [ ] extract_oracle_schema_command()
  - [ ] analyze_procedure_command()
  - [ ] analyze_all_procedures_command()
  - [ ] list_oracle_jobs_command()
- [ ] mcp_server/commands/analysis_commands.py
  - [ ] analyze_jsp_command()
  - [ ] analyze_controller_command()
  - [ ] analyze_service_command()
  - [ ] analyze_mapper_command()
  - [ ] scan_project_command()
- [ ] mcp_server/commands/graph_commands.py
  - [ ] build_graph_command()
  - [ ] query_path_command()
  - [ ] find_dependencies_command()
  - [ ] find_procedure_callers_command()
  - [ ] visualize_graph_command()
- [ ] mcp_server/commands/report_commands.py
  - [ ] generate_report_command()
  - [ ] detect_conflicts_command()
  - [ ] audit_transactions_command()
- [ ] mcp_server/commands/utility_commands.py
  - [ ] status_command()
  - [ ] clear_cache_command()
  - [ ] config_command()

---

## Phase 5: 知識圖譜構建 🕸️

### 5.1 Graph Builder
- [ ] mcp_server/tools/graph_builder.py
  - [ ] 載入所有分析結果（JSP, Controller, Service, Mapper, SQL, DB Schema）
  - [ ] 建立節點（JSP, AJAX_CALL, CONTROLLER, SERVICE, MAPPER, SQL, TABLE, PROCEDURE, VIEW, TRIGGER, ORACLE_JOB）
  - [ ] 建立邊（INCLUDES, CALLS, INVOKES, USES, EXECUTES, QUERIES, TRIGGERED_BY, SCHEDULED_BY）
  - [ ] 使用 NetworkX 建立有向圖
  - [ ] 輸出 JSON 與 GraphML 格式

### 5.2 Graph Query
- [ ] mcp_server/tools/graph_query.py
  - [ ] 路徑查詢（最短路徑、所有路徑）
  - [ ] 依賴分析（上游依賴、下游依賴）
  - [ ] 影響範圍分析（修改某個節點會影響哪些節點）
  - [ ] 孤立節點檢測（未被使用的程式碼）
  - [ ] 循環依賴檢測

### 5.3 Graph Visualization
- [ ] mcp_server/tools/graph_visualizer.py
  - [ ] Mermaid 格式輸出
  - [ ] GraphViz DOT 格式輸出
  - [ ] HTML 互動式圖表（使用 vis.js 或 cytoscape.js）

---

## Phase 6: 文檔與測試 📚

### 6.1 使用文檔
- [ ] README.md（完整版）
  - [ ] 專案簡介
  - [ ] 功能特色
  - [ ] 安裝指南
  - [ ] 快速開始
  - [ ] Slash Commands 完整列表
  - [ ] 常見問題
- [ ] PROMPTS_GUIDE.md
  - [ ] Prompt 模板說明
  - [ ] 自訂 Prompt 指南
  - [ ] 最佳實踐
- [ ] ARCHITECTURE.md
  - [ ] 系統架構圖（Mermaid）
  - [ ] 資料流程圖
  - [ ] 模組說明
  - [ ] 擴展指南

### 6.2 範例與教學
- [ ] examples/sample_project/（示範專案）
  - [ ] 簡單的 SpringMVC + MyBatis 專案
  - [ ] 包含 JSP, Controller, Service, Mapper, Oracle Procedures
- [ ] examples/analysis_walkthrough.md（分析流程教學）

### 6.3 測試
- [ ] tests/test_db_extractor.py
- [ ] tests/test_procedure_analyzer.py
- [ ] tests/test_jsp_analyzer.py
- [ ] tests/test_controller_analyzer.py
- [ ] tests/test_service_analyzer.py
- [ ] tests/test_mybatis_analyzer.py
- [ ] tests/test_graph_builder.py
- [ ] tests/test_graph_query.py

### 6.4 CLI 工具（可選）
- [ ] cli/springmvc_cli.py
  - [ ] 獨立 CLI 工具（不需要 Claude Code）
  - [ ] 直接執行分析與圖譜構建
  - [ ] 使用 Click 實作

---

## Phase 7: 優化與擴展 🚀

### 7.1 效能優化
- [ ] 並行分析支援（asyncio）
- [ ] 增量分析（只分析變更的檔案）
- [ ] 快取策略優化

### 7.2 進階功能
- [ ] 安全性分析（SQL Injection 風險、XSS 風險）
- [ ] 效能瓶頸偵測
- [ ] 程式碼品質評分
- [ ] 技術債務評估

### 7.3 整合功能
- [ ] Git 整合（分析變更影響範圍）
- [ ] JIRA 整合（追蹤需求與程式碼關聯）
- [ ] CI/CD 整合（自動化分析）

---

## 實作優先順序建議

### Sprint 1（核心功能）
1. ✅ 完成 Phase 1（基礎設施）
2. 🔄 完成 Phase 2（MCP Server 骨架）
3. 實作 Phase 4.1-4.2（基本 Slash Commands）
4. 實作 Phase 3.1-3.4（程式碼分析工具）

### Sprint 2（知識圖譜）
5. 實作 Phase 5.1-5.2（Graph Builder & Query）
6. 實作 Phase 4.3（知識圖譜 Commands）
7. 實作 Phase 5.3（Graph Visualization）

### Sprint 3（完善與優化）
8. 實作 Phase 4.4-4.5（報告與工具 Commands）
9. 完成 Phase 6（文檔與測試）
10. 實作 Phase 7（優化與擴展）

---

## 關鍵設計決策記錄

### 1. 為何使用多 Agent 架構？
- **模組化**: 每個分析器獨立，易於維護與擴展
- **Context 管理**: 避免單一 Agent 超過 200k token 限制
- **並行處理**: 多個分析器可並行執行
- **Prompt 專精**: 每個 Agent 有專門的 Prompt，提高分析準確度

### 2. 為何 DB 提取不使用 LLM？
- **安全性**: 密碼不經過 LLM
- **準確性**: 直接查詢系統表，100% 準確
- **效能**: 本地提取快速，不消耗 API Quota
- **可靠性**: 不受 LLM 幻覺影響

### 3. 為何使用 MCP Protocol？
- **Claude Code 原生支援**: 無縫整合
- **Slash Commands**: 提供更好的 UX
- **未來擴展**: 可整合其他 AI IDE（Copilot CLI 等）

### 4. Procedure 分析的觸發方式偵測
- **多來源檢測**: Triggers + Oracle Jobs + MyBatis CALLABLE
- **信心程度**: 明確標註推測的信心（high/medium/low）
- **上下文豐富**: 提供充足資訊給 LLM 推理

---

## 當前進度

- [x] Phase 1: 基礎設施建設（100%）
- [ ] Phase 2: MCP Server 骨架（10%）
- [ ] Phase 3: 程式碼分析工具（0%）
- [ ] Phase 4: Slash Commands（0%）
- [ ] Phase 5: 知識圖譜構建（0%）
- [ ] Phase 6: 文檔與測試（5%）
- [ ] Phase 7: 優化與擴展（0%）

**下一步**: 完成 base_tool.py，然後建立 MCP Server 主程式與 Slash Commands 架構。
