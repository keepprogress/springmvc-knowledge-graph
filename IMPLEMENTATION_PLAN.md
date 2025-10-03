# SpringMVC Knowledge Graph - 實作計畫

## 專案概述

使用 Claude Agent SDK 和 MCP Protocol 建立 SpringMVC + JSP + MyBatis 專案的自動化知識圖譜分析系統。

**追蹤路徑**: JSP (includes, AJAX) → Controller → Service → Mapper → SQL → Oracle Tables/Procedures

---

## Phase 0: 驗證策略 🧪 (新增 - 研究報告建議)

**目的**: 漸進式驗證，降低大規模部署風險

### 0.1 小規模驗證（10K LOC）
- [ ] **選擇代表性子集**
  - [ ] 選擇 1-2 個核心業務模組（User Management, Order Processing 等）
  - [ ] 包含完整的 JSP → Controller → Service → Mapper → DB 路徑
  - [ ] ~50 個 JSP, ~20 個 Controller, ~10 個 Service, ~15 個 Mapper
- [ ] **驗證圖譜準確性**
  - [ ] 人工檢查 20% 的關係（隨機抽樣）
  - [ ] 驗證 JSP static include namespace 正確性
  - [ ] 驗證 Controller @RequestMapping 與 URL 對應
  - [ ] 驗證 Service → Mapper 依賴注入正確性
- [ ] **調整 Parser 與 Prompt**
  - [ ] 識別 parser 遺漏的 pattern
  - [ ] 優化 tree-sitter-java query patterns
  - [ ] 調整 LLM prompt 提高準確度
- [ ] **預期結果**
  - [ ] Parser 覆蓋率 ≥ 70%
  - [ ] 關係準確率 ≥ 90%
  - [ ] 分析時間: ~2 分鐘
  - [ ] API 成本: ~$5

### 0.2 中規模測試（100K LOC）
- [ ] **擴展到多個模組**
  - [ ] 包含 5-10 個業務模組
  - [ ] ~500 個 JSP, ~200 個 Controller, ~150 個 Service
- [ ] **驗證效能與成本**
  - [ ] 測量分析時間是否線性擴展
  - [ ] 驗證 API 成本預測模型
  - [ ] 測試快取效果（semantic caching hit rate）
- [ ] **測試階層式模型**
  - [ ] 使用 Claude Haiku screening + Sonnet verification
  - [ ] 驗證成本降低 (預期 5-10x)
- [ ] **預期結果**
  - [ ] 分析時間: ~15 分鐘
  - [ ] API 成本: ~$30-40
  - [ ] Cache hit rate: 60-70%

### 0.3 全規模部署（500K+ LOC）
- [ ] **完整專案分析**
  - [ ] 所有 JSP, Controller, Service, Mapper
  - [ ] 完整知識圖譜建構
- [ ] **產生最終報告**
  - [ ] 互動式 HTML 圖譜（PyVis）
  - [ ] GraphML/GEXF 匯出（for Gephi）
  - [ ] 品質報告（覆蓋率、信心度分布）
- [ ] **預期結果** (based on research)
  - [ ] 分析時間: 15-25 分鐘
  - [ ] API 成本: $50-75
  - [ ] 圖譜節點: 2,000-3,000
  - [ ] 關係邊: 10,000-15,000

**驗證成功標準**:
- ✅ Parser 覆蓋率 ≥ 75%（Phase 0.1 優化後）
- ✅ 關係準確率 ≥ 85%（人工抽樣驗證）
- ✅ LLM 成本可控（<$100 for 500K LOC）
- ✅ 分析時間可接受（<30 分鐘 for 500K LOC）

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

## Phase 2: MCP Server 骨架 ✅

**狀態**: 已完成 (2025-10-03)

### 2.1 Base Tool 類別 ✅
- [x] mcp_server/tools/base_tool.py (399 lines)
  - [x] Claude Agent SDK 整合 (async/await pattern)
  - [x] 檔案讀寫管理 (JSON load/save)
  - [x] 錯誤處理 (comprehensive exception handling)
  - [x] 結果快取機制 (with expiration support, default 7 days)
  - [x] 批次分析支援 (batch_analyze method)
  - [x] JSON 解析增強 (json-repair integration, multiple code blocks)
  - [x] Windows UTF-8 支援 (console encoding fix)

### 2.2 MCP Server 主程式 ✅
- [x] mcp_server/springmvc_mcp_server.py (324 lines)
  - [x] Tool 註冊機制 (register_tool method)
  - [x] 已註冊 2 個工具:
    - [x] extract_oracle_schema (標準 JSON Schema 格式)
    - [x] analyze_stored_procedure (標準 JSON Schema 格式)
  - [x] 參數驗證 (connection_name enum validation)
  - [x] Slash Command 註冊機制 (register_command - Phase 4 實作)
  - [x] 錯誤處理 (comprehensive error messages)
  - [x] PEP 8 import 順序
  - [x] Windows UTF-8 支援

### 2.3 Phase 2 改進 (Code Review) ✅
- [x] 修正工具參數 Schema 為標準 JSON Schema 格式
- [x] 新增 connection_name 參數驗證 (enum: dev/test/prod)
- [x] 修正 import 順序符合 PEP 8 標準
- [x] 新增快取過期機制 (可配置天數)
- [x] 改進 JSON 解析:
  - [x] 支援多個 ```json``` code blocks (使用最後一個)
  - [x] 整合 json-repair 庫處理不完整 JSON
  - [x] Regex-based 提取提高穩健性
- [x] 新增依賴: json-repair>=0.30.0

**測試結果**:
- ✅ MCP Server 啟動正常
- ✅ 工具註冊成功 (2個工具)
- ✅ JSON 解析測試通過 (標準、多區塊、修復)
- ✅ 快取過期測試通過
- ✅ 參數驗證測試通過
- ✅ base_tool.py 測試套件全部通過

---

## Phase 3: 程式碼結構提取 📝

**策略**: 純結構化提取（Parsing），不使用 LLM
**目的**: 建立 100% 準確的程式碼結構資料，作為知識圖譜基礎

### 3.1 JSP 結構提取器
- [ ] mcp_server/tools/jsp_analyzer.py
  - [ ] **Include 關係**（lxml + BeautifulSoup）
    - [ ] 靜態 include: `<%@ include file="..." %>`
    - [ ] 動態 include: `<jsp:include page="..." />`
    - [ ] JSTL import: `<c:import url="..." />`
  - [ ] **⭐ Compilation Unit 建模**（新增 - 基於研究報告）
    - [ ] 區分靜態 vs 動態 include:
      - [ ] 靜態: 建立 `shared_namespace` (translation-time merge)
      - [ ] 動態: 建立 `isolated_scope` (runtime execution)
    - [ ] 追蹤函數解析順序（parent → first include → subsequent includes）
    - [ ] 解析 `web.xml` 的 `jsp-property-group`:
      - [ ] `<include-prelude>`: 所有 JSP 前置隱式 include
      - [ ] `<include-coda>`: 所有 JSP 後置隱式 include
    - [ ] 輸出 `compilation_unit_id` 給每個 JSP 節點
  - [ ] **Form 提取**（lxml）
    - [ ] `<form action="..." method="...">` 解析
    - [ ] Input fields（name, type, required）
    - [ ] Submit target URL
  - [ ] **AJAX 呼叫提取**（Regex）
    - [ ] jQuery: `$.ajax()`, `$.get()`, `$.post()`
    - [ ] Fetch API: `fetch("...")`
    - [ ] XMLHttpRequest: `xhr.open()`
  - [ ] **URL 提取**（Regex）
    - [ ] href, src, location.href, window.open
    - [ ] 分類: Controller URL / Static / External / JSP
  - [ ] **EL 表達式提取**（Regex）
    - [ ] `${...}` 標準 EL
    - [ ] `#{...}` Spring EL
    - [ ] 提取變數名稱與屬性鏈
  - [ ] **Java Scriptlet 提取**（Regex + tree-sitter-java）
    - [ ] 提取 `<% ... %>` 程式碼區塊
    - [ ] 提取 `<%= ... %>` 表達式
    - [ ] 使用 tree-sitter-java 解析提取的 Java code
  - [ ] **Taglib 依賴**（lxml）
    - [ ] `<%@ taglib prefix="..." uri="..." %>`
  - [ ] **輸出**: `output/structure/jsp/<filename>.json`
    ```json
    {
      "file": "user/list.jsp",
      "compilation_unit_id": "cu_user_list_001",
      "static_includes": [...],
      "dynamic_includes": [...],
      "shared_namespace": ["header.jsp", "utils.jsp"],
      "web_xml_implicit_includes": {
        "prelude": ["config.jsp"],
        "coda": ["footer.jsp"]
      }
    }
    ```

### 3.2 Controller 結構提取器
- [ ] mcp_server/tools/controller_analyzer.py
  - [ ] **⭐ 使用 tree-sitter-java**（取代 javalang - 研究報告建議）
    - [ ] 優勢: 錯誤恢復能力、增量解析、C-based 效能、Spring MVC 生產驗證
    - [ ] 使用 tree-sitter query language 提取註解與結構
  - [ ] **註解提取**（tree-sitter-java queries）
    - [ ] `@Controller` / `@RestController`
    - [ ] `@RequestMapping` (類別與方法層級)
    - [ ] `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`
    - [ ] HTTP method, URL path, params, headers
    - [ ] Query pattern: `(annotation (identifier) @name (annotation_argument_list) @args)`
  - [ ] **依賴注入**（tree-sitter-java queries）
    - [ ] `@Autowired` Service 依賴
    - [ ] 建構子注入、欄位注入
    - [ ] Query pattern: `(field_declaration (modifiers (annotation)) (variable_declarator))`
  - [ ] **方法呼叫鏈**（tree-sitter-java CST）
    - [ ] 追蹤 Service method 呼叫
    - [ ] 提取方法名稱與參數
    - [ ] Query pattern: `(method_invocation (identifier) @method (argument_list) @args)`
  - [ ] **回傳類型分析**（tree-sitter-java）
    - [ ] View name (String)
    - [ ] ModelAndView
    - [ ] @ResponseBody (JSON)
    - [ ] RedirectView
  - [ ] **參數綁定**（tree-sitter-java）
    - [ ] `@RequestParam`, `@PathVariable`, `@RequestBody`
    - [ ] Model attributes
  - [ ] **錯誤恢復**（tree-sitter-java 特性）
    - [ ] 處理不完整的 Java 檔案（編譯中、錯誤程式碼）
    - [ ] 標記 parsing errors 但仍提取可用資訊
  - [ ] **輸出**: `output/structure/controllers/<classname>.json`

### 3.3 Service 結構提取器
- [ ] mcp_server/tools/service_analyzer.py
  - [ ] **⭐ 使用 tree-sitter-java**（取代 javalang）
  - [ ] **類別註解**（tree-sitter-java queries）
    - [ ] `@Service`, `@Component`
    - [ ] `@Transactional` (類別層級)
  - [ ] **依賴注入**（tree-sitter-java queries）
    - [ ] `@Autowired` Mapper 依賴
    - [ ] 其他 Service 依賴
  - [ ] **方法分析**（tree-sitter-java CST）
    - [ ] 方法簽名（名稱、參數、回傳型別）
    - [ ] `@Transactional` (方法層級)
    - [ ] Mapper method 呼叫追蹤
  - [ ] **異常處理**（tree-sitter-java CST）
    - [ ] try-catch blocks
    - [ ] throws declarations
    - [ ] Query pattern: `(try_statement (catch_clause (catch_formal_parameter)))`
  - [ ] **輸出**: `output/structure/services/<classname>.json`

### 3.4 MyBatis Mapper 結構提取器
- [ ] mcp_server/tools/mybatis_analyzer.py
  - [ ] **Mapper Interface 解析**（tree-sitter-java）
    - [ ] `@Mapper` 註解
    - [ ] 方法簽名（參數、回傳型別）
    - [ ] `@Param` 參數註解
    - [ ] Query pattern: `(interface_declaration (annotation) @mapper_ann (interface_body))`
  - [ ] **Mapper XML 解析**（lxml）
    - [ ] `<select>`, `<insert>`, `<update>`, `<delete>`
    - [ ] SQL 語句提取（包含動態 SQL）
    - [ ] `<include>` 引用（SQL fragments）
    - [ ] ResultMap 映射
  - [ ] **SQL 類型偵測**（sqlparse）
    - [ ] DML: SELECT, INSERT, UPDATE, DELETE
    - [ ] CALLABLE: `{call procedure_name(...)}`
    - [ ] 提取 Procedure 名稱
  - [ ] **參數映射**（lxml + Regex）
    - [ ] `#{paramName}` 參數佔位符
    - [ ] 動態 SQL: `<if>`, `<choose>`, `<foreach>`
  - [ ] **表名提取**（sqlparse + Regex fallback）
    - [ ] FROM, JOIN, INTO 後的表名
    - [ ] 與 db_schema.json 比對驗證
  - [ ] **輸出**: `output/structure/mappers/<interface_name>.json`

### 3.5 SQL 結構分析器
- [ ] mcp_server/tools/sql_analyzer.py
  - [ ] **SQL 解析**（sqlparse）
    - [ ] 語句類型: SELECT/INSERT/UPDATE/DELETE
    - [ ] 表名提取（FROM, JOIN, INTO）
    - [ ] 欄位提取（SELECT list, WHERE clause）
  - [ ] **JOIN 關係**（sqlparse AST）
    - [ ] INNER JOIN, LEFT JOIN, RIGHT JOIN
    - [ ] ON 條件分析
  - [ ] **WHERE 條件**（Regex）
    - [ ] 提取過濾欄位
    - [ ] 參數佔位符
  - [ ] **Schema 驗證**（比對 db_schema.json）
    - [ ] 表是否存在
    - [ ] 欄位是否存在
    - [ ] 型別是否匹配
  - [ ] **輸出**: 內嵌於 Mapper 分析結果

**Phase 3 核心原則**:
- ✅ 100% 準確（不依賴 LLM 推測）
- ✅ 快速（無 API 呼叫，秒級完成）
- ✅ 可測試（純 parsing 邏輯）
- ✅ 可重複（結果一致）
- ❌ 不做業務語意分析（留給 Phase 7）

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

**策略**: 混合雙層方案 = 程式碼建立確定關係 + LLM 完整性掃描補強
**目的**: 兼顧準確性與完整性

### 5.1 Graph Builder - Layer 1（程式碼建立確定關係）

- [ ] mcp_server/tools/graph_builder_code.py
  - [ ] **資料載入**
    - [ ] 載入 `output/structure/jsp/*.json`
    - [ ] 載入 `output/structure/controllers/*.json`
    - [ ] 載入 `output/structure/services/*.json`
    - [ ] 載入 `output/structure/mappers/*.json`
    - [ ] 載入 `output/db_schema.json`
    - [ ] 載入 `output/analysis/procedures/*.json`（Phase 1）
  - [ ] **節點建立**（NetworkX）
    - [ ] JSP: `{type: "JSP", path: "...", name: "..."}`
    - [ ] AJAX_CALL: `{type: "AJAX", url: "...", method: "GET/POST"}`
    - [ ] CONTROLLER: `{type: "CONTROLLER", class: "...", method: "..."}`
    - [ ] SERVICE: `{type: "SERVICE", class: "...", method: "..."}`
    - [ ] MAPPER: `{type: "MAPPER", interface: "...", method: "..."}`
    - [ ] SQL: `{type: "SQL", statement_type: "SELECT/INSERT/...", tables: [...]}`
    - [ ] TABLE: `{type: "TABLE", name: "...", schema: "..."}`
    - [ ] PROCEDURE: `{type: "PROCEDURE", name: "...", package: "..."}`
    - [ ] VIEW: `{type: "VIEW", name: "..."}`
    - [ ] TRIGGER: `{type: "TRIGGER", name: "...", table: "..."}`
    - [ ] ORACLE_JOB: `{type: "ORACLE_JOB", name: "...", procedure: "..."}`
  - [ ] **邊建立（高信心關係）**
    - [ ] ✅ JSP → JSP: `INCLUDES` (明確路徑，confidence=1.0)
    - [ ] ⚠️ JSP → CONTROLLER: `CALLS` (URL pattern matching，confidence=0.6-0.9)
    - [ ] ✅ CONTROLLER → SERVICE: `INVOKES` (@Autowired 明確，confidence=1.0)
    - [ ] ✅ SERVICE → MAPPER: `USES` (依賴注入明確，confidence=1.0)
    - [ ] ✅ MAPPER → SQL: `EXECUTES` (XML 明確，confidence=1.0)
    - [ ] ✅ SQL → TABLE: `QUERIES/MODIFIES` (sqlparse，confidence=0.8-1.0)
    - [ ] ✅ SQL → PROCEDURE: `CALLS` (CALLABLE 明確，confidence=1.0)
    - [ ] ✅ TRIGGER → PROCEDURE: `TRIGGERED_BY` (db_schema，confidence=1.0)
    - [ ] ✅ ORACLE_JOB → PROCEDURE: `SCHEDULED_BY` (db_schema，confidence=1.0)
  - [ ] **輸出**
    - [ ] `output/graph/code_based_graph.json` (程式碼建立的關係)
    - [ ] `output/graph/low_confidence_edges.json` (需 LLM 驗證的關係)

### 5.2 Graph Builder - Layer 2（LLM 完整性掃描 + Parser 改進建議）

- [ ] mcp_server/tools/graph_builder_llm.py
  - [ ] **⭐ RAG (Retrieval-Augmented Generation) 實作**（研究報告驗證）
    - [ ] 架構: Static analysis results → inject into LLM prompts → contextual reasoning
    - [ ] 優勢: 70% top-2 accuracy (研究報告數據)
    - [ ] vs Data-Augmented Training (需 fine-tuning，成本高)
  - [ ] **⭐ Prompt Engineering 最佳實踐**（研究報告建議）
    - [ ] **Context Window**: ±15 行程式碼（sweet spot）
      - [ ] 太少: 準確度下降
      - [ ] 太多: noise 增加但無益
    - [ ] **XML-Structured Prompts**: 15-20% 準確度提升
      ```xml
      <task>找出 AJAX URL 對應的 Controller</task>
      <context>
        <ajax_call>
          <file>user/list.jsp:45</file>
          <code>$.post('${ctx}/user/save', data)</code>
        </ajax_call>
        <candidate_controllers>
          <controller>
            <class>UserController</class>
            <method>saveUser</method>
            <mapping>@PostMapping("/user/save")</mapping>
          </controller>
        </candidate_controllers>
      </context>
      <requirements>
        - 輸出 JSON 格式
        - 包含 confidence (0.0-1.0)
        - 提供 reasoning
      </requirements>
      ```
    - [ ] **Few-Shot Examples**: 3-5 個涵蓋 positive/negative/edge cases
    - [ ] **Step-by-Step Reasoning**: 要求 LLM 先推理再結論（提升 15-20%）
  - [ ] **⭐ Semantic Caching 策略**（研究報告: 3-5x 成本降低）
    - [ ] **Normalization**:
      ```python
      def semantic_hash(code, query_type):
          # Remove whitespace, comments, formatting
          normalized = normalize_code(code)
          # Hash normalized code + query type
          return hash(normalized + query_type)
      ```
    - [ ] **Cache Structure**:
      ```json
      {
        "cache_key": "hash_abc123_url_mapping",
        "input": {"code": "...", "query": "..."},
        "output": {"target": "UserController.save", "confidence": 0.9},
        "timestamp": "2025-10-03T10:00:00",
        "hit_count": 15
      }
      ```
    - [ ] **Expected Performance**:
      - [ ] Cache hit rate: 60-80% (研究數據)
      - [ ] Cost reduction: 3-5x
      - [ ] 應用於增量分析時效果更顯著
  - [ ] **完整性掃描**
    - [ ] 輸入: Phase 3 所有結構化資料 + Layer 1 圖譜
    - [ ] LLM 任務: 掃描所有檔案，識別 Layer 1 可能遺漏的關係
    - [ ] 重點關注:
      - [ ] 動態 URL（EL 表達式、Context Path）
      - [ ] 複雜 Form action（JavaScript 動態設定）
      - [ ] 反射呼叫、動態代理
      - [ ] 間接依賴（透過 Factory、Builder）
  - [ ] **模糊關係推測**
    - [ ] AJAX URL → Controller mapping
      ```
      輸入: {
        "ajax_url": "${ctx}/user/detail/${userId}",
        "controllers": [
          {"path": "/user/detail/{id}", "method": "UserController.detail"},
          {"path": "/admin/user/detail/{id}", "method": "AdminController.detail"}
        ]
      }
      輸出: {
        "most_likely": "UserController.detail",
        "confidence": 0.85,
        "reasoning": "URL pattern 與 context 匹配"
      }
      ```
    - [ ] Form action 解析
    - [ ] 間接方法呼叫鏈
  - [ ] **遺漏偵測**
    - [ ] 孤立節點檢查（應該有關係但沒有的節點）
    - [ ] 對稱性檢查（A→B 存在，B→A 應該也存在？）
    - [ ] 業務邏輯合理性（Controller 沒有 Service？）
  - [ ] **⭐ Parser 問題偵測與改進建議**
    - [ ] 發現 Parser 遺漏的 Pattern
      ```python
      # LLM 發現遺漏案例
      {
        "issue_type": "ajax_pattern_missed",
        "file": "user/list.jsp",
        "line": 45,
        "missed_code": "$.post('${pageContext.request.contextPath}/user/save', data)",
        "reason": "Parser regex 未處理 pageContext.request.contextPath",
        "current_regex": r"\$\.post\(['\"]([^'\"]+)['\"]",
        "suggested_regex": r"\$\.post\(['\"](?:\$\{[^}]+\})?([^'\"]+)['\"]",
        "improvement": "支援 ${...} EL 表達式前綴",
        "test_cases": [
          "$.post('/user/save', data)",
          "$.post('${ctx}/user/save', data)",
          "$.post('${pageContext.request.contextPath}/user/save', data)"
        ]
      }
      ```
    - [ ] 分類問題類型
      - [ ] `regex_too_strict`: Regex 過於嚴格，遺漏合法 pattern
      - [ ] `encoding_issue`: 編碼問題（如 HTML entities）
      - [ ] `multi_line_pattern`: 跨行 pattern 未處理
      - [ ] `nested_structure`: 巢狀結構未解析
      - [ ] `new_framework_syntax`: 新語法（如 Vue.js、React）
    - [ ] 累積改進知識庫
      ```
      output/parser_improvements/
        ├── ajax_patterns.json (AJAX 相關改進)
        ├── el_expression_patterns.json (EL 表達式)
        ├── form_patterns.json (Form action)
        └── summary.md (改進總覽)
      ```
  - [ ] **輸出**
    - [ ] `output/graph/llm_discovered_edges.json` (LLM 發現的關係)
    - [ ] `output/graph/missing_relationships.json` (可能遺漏的關係)
    - [ ] `output/parser_improvements/issues_found.json` (Parser 問題清單)
    - [ ] `output/parser_improvements/regex_suggestions.json` (Regex 改進建議)

### 5.3 Graph Merger（合併與驗證）

- [ ] mcp_server/tools/graph_merger.py
  - [ ] **關係合併**
    - [ ] 合併 Layer 1 (code-based) + Layer 2 (LLM-discovered)
    - [ ] 衝突解決策略:
      - [ ] 程式碼 confidence=1.0 優先
      - [ ] LLM 僅補充，不覆蓋明確關係
      - [ ] 雙方都發現的關係 → 提高 confidence
  - [ ] **雙向驗證**
    - [ ] 程式碼發現但 LLM 認為不合理 → 標記為 `needs_review`
    - [ ] LLM 發現但程式碼未找到 → 標記為 `llm_inferred`
  - [ ] **信心評分**
    ```json
    {
      "source": "user/list.jsp",
      "target": "UserController.list",
      "type": "CALLS",
      "confidence": 0.95,
      "source_methods": ["code_regex", "llm_verification"],
      "evidence": {
        "code": "$.ajax({url: '/user/list'})",
        "llm_reasoning": "明確的 URL 匹配"
      }
    }
    ```
  - [ ] **圖譜輸出**（多種格式）
    - [ ] `output/knowledge_graph.json` (完整圖譜，自訂格式)
    - [ ] `output/knowledge_graph.graphml` (NetworkX 標準格式)
    - [ ] `output/knowledge_graph_stats.json` (統計資訊)
    - [ ] `output/neo4j_import.cypher` (Neo4j 匯入腳本)
    - [ ] `output/graph_quality_report.md` (品質報告)

### 5.4 Graph Query（查詢 API）
- [ ] mcp_server/tools/graph_query.py
  - [ ] **路徑查詢**（NetworkX algorithms）
    - [ ] `find_path(source, target)` - 最短路徑
    - [ ] `find_all_paths(source, target, max_depth=10)` - 所有路徑
    - [ ] `trace_request_flow(jsp_or_url)` - 追蹤完整請求流程
  - [ ] **依賴分析**
    - [ ] `get_upstream_dependencies(node)` - 上游依賴（誰依賴我）
    - [ ] `get_downstream_dependencies(node)` - 下游依賴（我依賴誰）
    - [ ] `get_all_dependencies(node, depth=5)` - 遞迴依賴
  - [ ] **影響範圍分析**
    - [ ] `impact_analysis(node)` - 修改此節點會影響哪些節點
    - [ ] `find_affected_jsps(table_name)` - 修改表會影響哪些 JSP
  - [ ] **程式碼品質分析**
    - [ ] `find_orphaned_nodes()` - 孤立節點（未被使用）
    - [ ] `detect_circular_dependencies()` - 循環依賴
    - [ ] `find_dead_code()` - 死程式碼
  - [ ] **Procedure 相關查詢**
    - [ ] `find_procedure_callers(proc_name)` - 誰調用此 Procedure
    - [ ] `find_procedure_call_paths(proc_name)` - 所有調用路徑
  - [ ] **信心度查詢**
    - [ ] `get_low_confidence_edges(threshold=0.7)` - 低信心關係
    - [ ] `get_llm_inferred_edges()` - LLM 推測的關係
    - [ ] `get_needs_review_edges()` - 需人工檢視的關係

### 5.5 Graph Visualization
- [ ] mcp_server/tools/graph_visualizer.py
  - [ ] **⭐ PyVis 互動式視覺化**（研究報告推薦 - CLI 工具最佳選擇）
    - [ ] **優勢**（來自研究）:
      - [ ] Wraps vis.js (physics-based layouts)
      - [ ] Zero JavaScript knowledge required
      - [ ] Generates shareable HTML for stakeholders
      - [ ] 適合 CLI 工具（不需額外 server）
    - [ ] **功能實作**:
      ```python
      from pyvis.network import Network

      def generate_pyvis(graph):
          net = Network(height="800px", width="100%", directed=True)
          net.from_nx(graph)  # Load from NetworkX

          # Physics layout (spring-based)
          net.show_buttons(filter_=['physics'])

          # Node customization
          for node in graph.nodes():
              net.get_node(node)['color'] = get_color_by_type(node)
              net.get_node(node)['title'] = get_node_details(node)

          # Generate interactive HTML
          net.show('output/graph_interactive.html')
      ```
    - [ ] **節點著色**（by type）:
      - [ ] JSP: 藍色
      - [ ] CONTROLLER: 綠色
      - [ ] SERVICE: 黃色
      - [ ] MAPPER: 橙色
      - [ ] TABLE/PROCEDURE: 紅色
    - [ ] **互動功能**:
      - [ ] 拖曳節點（physics engine）
      - [ ] 點擊節點顯示詳細資訊（hover tooltip）
      - [ ] 篩選器（by type, by confidence）
      - [ ] 搜尋功能（highlight matching nodes）
      - [ ] 縮放與平移
    - [ ] **輸出**: `output/graph_interactive.html` (可直接開啟分享)
  - [ ] **Mermaid 輸出**
    - [ ] Flowchart 格式（適合文件嵌入）
    - [ ] 支援節點著色（by type）
    - [ ] 支援邊標籤（關係類型）
    - [ ] 輸出: `output/graph_mermaid.md`
  - [ ] **GraphViz DOT 輸出**
    - [ ] 適合大型圖譜（專業佈局演算法）
    - [ ] 自動佈局演算法（dot, neato, fdp, circo）
    - [ ] 輸出: `output/graph.dot`
  - [ ] **⭐ GEXF Export**（研究報告: Gephi 最佳支援）
    - [ ] GEXF format for Gephi visualization
    - [ ] 保留所有節點屬性（confidence, evidence）
    - [ ] 輸出: `output/knowledge_graph.gexf`
  - [ ] **子圖提取**
    - [ ] `extract_subgraph(center_node, radius=2)` - 局部圖譜
    - [ ] `extract_flow_diagram(jsp_file)` - 單一 JSP 的完整流程圖
    - [ ] 使用 PyVis 渲染子圖

### 5.6 Parser 持續改進循環 🔄

- [ ] mcp_server/tools/parser_improver.py
  - [ ] **自動應用建議**（可選）
    - [ ] 讀取 `output/parser_improvements/regex_suggestions.json`
    - [ ] 人工審核後，自動更新 Phase 3 parser 的 regex
    - [ ] 回歸測試（確保舊 pattern 仍可用）
  - [ ] **改進效果追蹤**
    ```json
    {
      "iteration": 1,
      "date": "2025-10-03",
      "improvements_applied": 5,
      "before": {
        "total_edges": 1250,
        "low_confidence_edges": 180,
        "parser_coverage": 0.72
      },
      "after": {
        "total_edges": 1320,
        "low_confidence_edges": 95,
        "parser_coverage": 0.89
      },
      "improvement_rate": "5.6% more edges, 47% fewer low-confidence",
      "parser_improvements": {
        "ajax_patterns": {
          "before_coverage": 0.72,
          "after_coverage": 0.89,
          "improvement": "+23.6%"
        }
      }
    }
    ```
  - [ ] **Parser 品質報告**
    - [ ] 覆蓋率統計（多少 % 的關係被 parser 直接抓到）
    - [ ] 信心度分布（high/medium/low 的比例）
    - [ ] 常見遺漏 pattern 排行榜
  - [ ] **Slash Command 支援**
    ```
    /improve-parsers
      - 檢視 LLM 建議的 parser 改進
      - 人工選擇要應用的改進
      - 自動更新 regex 並測試

    /parser-quality-report
      - 產生 Parser 品質報告
      - 顯示覆蓋率、信心度分布
      - 列出待改進項目
    ```

### 5.6.1 安全機制與風險緩解 🛡️

**Risk 1: LLM Regex Suggestions May Be Wrong**

- [ ] **必要安全閘門（Mandatory Gates）**
  - [ ] **人工審核必要性**
    - [ ] 所有 regex 建議必須經過人工審核（no auto-apply without review）
    - [ ] 審核介面顯示:
      - [ ] 原始 regex vs 建議 regex（diff view）
      - [ ] Test cases（before/after 比對）
      - [ ] 遺漏案例（missed code examples）
      - [ ] LLM reasoning
    - [ ] 審核者可以:
      - [ ] ✅ Accept（應用建議）
      - [ ] ✏️ Edit（修改後應用）
      - [ ] ❌ Reject（拒絕建議）
      - [ ] 🔖 Defer（稍後處理）
  - [ ] **回歸測試套件**
    - [ ] 每個 parser 模組維護測試案例庫
    - [ ] 應用 regex 改進前:
      - [ ] 執行所有現有 test cases
      - [ ] 新 regex 必須通過所有舊測試
      - [ ] 新 test cases（LLM 建議）也要通過
    - [ ] 失敗處理:
      - [ ] 任何測試失敗 → 自動拒絕建議
      - [ ] 記錄失敗原因到 `rejected_suggestions.json`
  - [ ] **Rollback 機制**
    - [ ] Git 自動 commit 每次 regex 更新
    - [ ] 若發現問題，提供快速 rollback:
      ```
      /rollback-parser-change <parser_name> <iteration>
        - 回滾到指定版本
        - 自動執行測試確保穩定性
        - 記錄 rollback 原因供 LLM 學習
      ```
    - [ ] Rollback 觸發條件:
      - [ ] 新 regex 導致分析錯誤
      - [ ] Coverage 下降超過 5%
      - [ ] 產生大量誤報（false positives）
  - [ ] **改進建議品質檢查**
    - [ ] LLM 建議必須包含:
      - [ ] ✅ `current_regex`（目前版本）
      - [ ] ✅ `suggested_regex`（建議版本）
      - [ ] ✅ `test_cases`（至少 3 個，包含 edge cases）
      - [ ] ✅ `reasoning`（為何需要改進）
      - [ ] ✅ `improvement`（預期改善）
    - [ ] 缺少任何必要欄位 → 自動拒絕

**Risk 2: Conflict Resolution Complexity**

- [ ] **明確的衝突解決政策**
  - [ ] **基本原則**（Code-First Policy）
    - [ ] 程式碼 confidence=1.0 → **永遠優先**（不可覆蓋）
    - [ ] 程式碼 confidence ≥ 0.8 → 除非 LLM 提供明確反證
    - [ ] LLM 僅可:
      - [ ] ✅ 補充新關係（程式碼未發現）
      - [ ] ✅ 提高既有關係的 confidence（雙方都發現）
      - [ ] ❌ 覆蓋程式碼已建立的明確關係
  - [ ] **Confidence 閾值政策**
    ```python
    # 定義於 mcp_server/tools/graph_merger.py
    CONFIDENCE_THRESHOLDS = {
        "auto_include": 0.85,      # 自動加入圖譜
        "human_review": 0.60,      # 標記為需人工檢視
        "auto_reject": 0.40,       # 自動排除（太不確定）
        "conflict_threshold": 0.30 # confidence 差異超過此值 → 人工審核
    }
    ```
  - [ ] **衝突處理流程**
    - [ ] **Type 1: 同一關係，不同 confidence**
      ```python
      code_edge = {"source": "A", "target": "B", "confidence": 1.0, "method": "code"}
      llm_edge = {"source": "A", "target": "B", "confidence": 0.7, "method": "llm"}

      # 結果: 取高 confidence（1.0），標註雙方都發現
      merged = {"source": "A", "target": "B", "confidence": 1.0,
                "methods": ["code", "llm_verified"]}
      ```
    - [ ] **Type 2: Code 發現但 LLM 認為錯誤**（罕見但需處理）
      ```python
      code_edge = {"source": "A", "target": "B", "confidence": 0.65}
      llm_edge = {"source": "A", "target": "C", "confidence": 0.85,
                  "note": "B 是錯誤 mapping，應為 C"}

      # 策略: 標記為 needs_human_review
      # confidence 差異 = 0.85 - 0.65 = 0.20 < 0.30 → 保留 code_edge
      # 但記錄 LLM 異議到 review_queue
      ```
    - [ ] **Type 3: LLM 發現新關係**（最常見）
      ```python
      llm_edge = {"source": "X", "target": "Y", "confidence": 0.75}
      # code 未發現此關係

      # 0.75 >= 0.60 → 標記為 "llm_inferred"，加入圖譜
      # 輸出時附帶 "needs_verification: true"
      ```
  - [ ] **人工審核佇列（Review Queue）**
    - [ ] 自動收集需審核案例:
      - [ ] Confidence 差異 > 0.30
      - [ ] LLM 認為 code 錯誤
      - [ ] 孤立節點（應該有關係但沒有）
    - [ ] 審核介面:
      ```
      /review-conflicts
        - 顯示所有衝突案例
        - 提供 Evidence（code snippet + LLM reasoning）
        - 人工決策: Accept Code / Accept LLM / Custom
      ```
    - [ ] 決策記錄:
      - [ ] 所有人工決策記錄到 `conflict_resolutions.json`
      - [ ] 作為 LLM future learning 的參考
  - [ ] **衝突稽核記錄（Audit Trail）**
    - [ ] 所有衝突與解決方案記錄到 `output/graph/conflict_log.json`
    ```json
    {
      "conflict_id": "c001",
      "timestamp": "2025-10-03T14:30:00",
      "type": "confidence_mismatch",
      "code_edge": {...},
      "llm_edge": {...},
      "resolution": "code_wins",
      "reason": "code confidence=1.0 policy",
      "reviewer": "auto|human_name"
    }
    ```
    - [ ] 統計報告:
      - [ ] 衝突總數 / 解決數 / 待審核數
      - [ ] Code wins / LLM wins / Custom resolution 比例
      - [ ] 最常見衝突類型

**Safety Metrics Dashboard**

- [ ] **監控指標** (`/parser-safety-metrics`)
  ```json
  {
    "parser_improvements": {
      "total_suggestions": 50,
      "accepted": 30,
      "rejected": 15,
      "deferred": 5,
      "rejection_rate": "30%"
    },
    "test_coverage": {
      "total_test_cases": 250,
      "passing": 248,
      "failing": 2,
      "coverage": "99.2%"
    },
    "conflict_resolution": {
      "total_conflicts": 85,
      "auto_resolved": 70,
      "human_reviewed": 15,
      "code_wins": 60,
      "llm_wins": 10,
      "custom": 15
    },
    "rollbacks": {
      "total": 3,
      "reasons": ["coverage_drop", "false_positives", "test_failures"]
    }
  }
  ```

### 5.7 成本與效能模型 📊 (新增 - 研究報告驗證)

**目的**: 基於研究數據提供可預測的成本與時間估算

- [ ] **效能基準**（500K LOC Spring MVC 專案）
  ```yaml
  分析時間: 15-25 分鐘
  API 成本: $50-75
  圖譜規模:
    節點數: 2,000-3,000
    關係邊: 10,000-15,000
    信心度分布:
      high (>0.85): 70%
      medium (0.60-0.85): 20%
      low (<0.60): 10%
  ```

- [ ] **⭐ 階層式模型使用**（研究報告: 10x 成本降低）
  - [ ] **Claude Haiku** (Screening Layer):
    - [ ] 成本: $0.25/M input tokens, $1.25/M output tokens
    - [ ] 用途: 初步篩選、簡單 URL mapping、明顯 false positives
    - [ ] 涵蓋: 90% 的 LLM 呼叫
  - [ ] **Claude Sonnet** (Verification Layer):
    - [ ] 成本: $3/M input tokens, $15/M output tokens
    - [ ] 用途: 複雜推理、高風險決策、最終驗證
    - [ ] 涵蓋: 10% 的 LLM 呼叫
  - [ ] **成本對比**:
    ```
    全部使用 Sonnet: $300 (500K LOC)
    階層式模型: $50-75 (10x 降低)
    ```

- [ ] **成本控制策略**（研究報告驗證）
  - [ ] **Progressive Disclosure**:
    ```
    1. Static analysis (free): Filter 90% of code
    2. Heuristic pre-filtering (free): Eliminate 90% of remaining
    3. Haiku screening (cheap): Process 90% of ambiguous cases
    4. Sonnet verification (expensive): Final 0.1% high-priority
    ```
  - [ ] **Semantic Caching**: 60-80% hit rate
    - [ ] 首次分析: $75
    - [ ] 增量分析 (20% changed): $15-20 (5x 降低)
  - [ ] **Batch Processing**: Group similar queries
    - [ ] 單獨查詢 100 cases: 100 API calls
    - [ ] Batch 查詢: 10 API calls (10x 降低)

- [ ] **效能優化**
  - [ ] **並行處理**: asyncio multi-threading
    ```python
    # Phase 3 parsing: 全並行（無 API 限制）
    # Phase 5 LLM: Rate-limited 並行（Claude API limits）
    async with asyncio.Semaphore(10):  # 10 concurrent LLM calls
        tasks = [analyze_ambiguous_case(case) for case in cases]
        results = await asyncio.gather(*tasks)
    ```
  - [ ] **Incremental Analysis**: Git diff-based
    ```
    全量分析: 25 分鐘, $75
    增量分析 (10% changed): 3 分鐘, $10
    ```

- [ ] **成本預測公式**（基於研究）
  ```python
  def estimate_cost(loc, changed_ratio=1.0):
      # Static analysis: free
      static_time = loc / 50000  # minutes (1M LOC = 20 min)

      # LLM analysis
      ambiguous_cases = loc * 0.05 * changed_ratio  # 5% needs LLM
      haiku_calls = ambiguous_cases * 0.9  # 90% Haiku
      sonnet_calls = ambiguous_cases * 0.1  # 10% Sonnet

      cache_hit_rate = 0.7 if changed_ratio < 1.0 else 0.0
      effective_calls = (haiku_calls + sonnet_calls) * (1 - cache_hit_rate)

      haiku_cost = (effective_calls * 0.9) * 0.001  # $1/1K calls
      sonnet_cost = (effective_calls * 0.1) * 0.01  # $10/1K calls

      total_cost = haiku_cost + sonnet_cost
      total_time = static_time + (effective_calls / 100)  # 100 calls/min

      return {
          "total_time_minutes": total_time,
          "total_cost_usd": total_cost,
          "breakdown": {
              "static_analysis": {"time": static_time, "cost": 0},
              "llm_analysis": {
                  "haiku_calls": effective_calls * 0.9,
                  "sonnet_calls": effective_calls * 0.1,
                  "cost": total_cost
              }
          }
      }
  ```

- [ ] **Slash Command**: `/estimate-cost <loc> [--changed-ratio 0.1]`
  - [ ] 輸出成本與時間預估
  - [ ] 建議使用階層式模型 or 純 parsing（based on budget）

**Phase 5 核心原則（混合雙層 + 持續改進）**:
- ✅ **Layer 1（程式碼）**: 建立高信心關係（@Autowired, include, SQL）
- ✅ **Layer 2（LLM）**: 完整性掃描，補充遺漏關係（動態 URL, EL 表達式）
- ✅ **信心評分**: 每個關係附帶 confidence 與 evidence
- ✅ **雙向驗證**: 程式碼 vs LLM 結果交叉驗證
- 🔄 **持續改進**: LLM 發現 parser 問題 → 提供 regex 建議 → 人工審核 → 自動應用
- ✅ **多格式輸出**: JSON, GraphML, GEXF, Neo4j Cypher, PyVis HTML
- ⚠️ **完整性優先**: 寧可低信心關係保留，也不要遺漏
- 💰 **成本可控**: 階層式模型 + Semantic caching = $50-75 for 500K LOC

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

## Phase 7: 語意豐富化 🤖

**策略**: 基於 Phase 5 知識圖譜，使用 LLM 進行業務語意分析
**前提**: Phase 3-5 已建立完整且準確的結構化知識圖譜

### 7.1 Trace-Based 語意分析
- [ ] mcp_server/tools/semantic_analyzer.py
  - [ ] **完整路徑追蹤**
    - [ ] 輸入: 知識圖譜 + 特定路徑（JSP → Controller → Service → Mapper → SQL → Table）
    - [ ] 輸出: LLM 分析此路徑的業務用途、安全性、效能風險
  - [ ] **業務流程理解**
    ```python
    trace = graph_query.trace_request_flow("user/list.jsp")
    # trace = [
    #   JSP(user/list.jsp)
    #   → AJAX(/api/users)
    #   → Controller(UserController.getUsers)
    #   → Service(UserService.listUsers)
    #   → Mapper(UserMapper.selectUsers)
    #   → SQL(SELECT * FROM users WHERE status = 1)
    #   → Table(USERS)
    # ]

    semantic_analysis = semantic_analyzer.analyze_trace(trace)
    # 輸出: {
    #   "business_purpose": "使用者列表查詢功能",
    #   "security_concerns": ["缺少權限檢查", "可能的 SQL injection"],
    #   "performance_risks": ["全表掃描", "缺少分頁"],
    #   "recommendations": [...]
    # }
    ```
  - [ ] **Procedure 業務語意增強**
    - [ ] 基於 Phase 1 的 Procedure 分析
    - [ ] 結合知識圖譜中的調用路徑
    - [ ] LLM 深度理解業務邏輯與潛在問題

### 7.2 Prompt 模板（Phase 7 專用）
- [ ] mcp_server/prompts/semantic_enrichment.txt
  - [ ] 輸入: 完整 trace path + 程式碼片段
  - [ ] 分析維度:
    - [ ] 業務用途推測
    - [ ] 安全性風險（XSS, SQL Injection, CSRF）
    - [ ] 效能瓶頸（N+1 query, 全表掃描）
    - [ ] 程式碼異味（過長方法、循環依賴）
    - [ ] 重構建議
- [ ] mcp_server/prompts/flow_analysis.txt
  - [ ] 分析完整業務流程
  - [ ] 識別關鍵業務邏輯
  - [ ] 提供優化建議
- [ ] mcp_server/prompts/security_audit.txt
  - [ ] 安全性專項稽核
  - [ ] 識別常見漏洞模式
  - [ ] OWASP Top 10 檢查

### 7.3 語意豐富化工具
- [ ] **/enrich-semantic** Command
  ```
  /enrich-semantic <node_or_path>
    - 對特定節點或路徑進行語意分析
    - 例如: /enrich-semantic user/list.jsp
    - 輸出: 業務理解 + 安全分析 + 效能建議
  ```
- [ ] **/audit-security** Command
  ```
  /audit-security [範圍]
    - 全面安全性稽核
    - 掃描 XSS, SQL Injection, CSRF 風險
    - 輸出: 風險報告與修復建議
  ```
- [ ] **/suggest-refactoring** Command
  ```
  /suggest-refactoring <component>
    - 基於語意分析提供重構建議
    - 識別程式碼異味
    - 提供具體重構步驟
  ```
- [ ] **/explain-flow** Command
  ```
  /explain-flow <start_point>
    - 解釋完整業務流程
    - 使用 LLM 生成自然語言說明
    - 適合新人 onboarding
  ```

### 7.4 批次語意豐富化
- [ ] mcp_server/tools/batch_semantic_enrichment.py
  - [ ] 掃描整個知識圖譜
  - [ ] 識別關鍵路徑（高頻使用、高風險）
  - [ ] 批次進行語意分析
  - [ ] 產生完整的語意豐富化報告
  - [ ] 成本控制（僅分析關鍵路徑）

### 7.5 效能優化（基於語意分析）
- [ ] N+1 Query 偵測
  - [ ] 分析 Service → Mapper 呼叫模式
  - [ ] 識別迴圈中的重複查詢
  - [ ] LLM 提供 JOIN 優化建議
- [ ] 全表掃描偵測
  - [ ] 分析 SQL WHERE 條件
  - [ ] 比對 db_schema 的索引資訊
  - [ ] LLM 建議索引策略
- [ ] 事務邊界分析
  - [ ] 分析 @Transactional 使用
  - [ ] 識別過長事務
  - [ ] LLM 建議拆分策略

**Phase 7 核心原則**:
- ✅ 建立在準確的知識圖譜之上
- ✅ LLM 僅用於語意理解與建議
- ✅ 結構化資訊（Phase 3-5）不被 LLM 修改
- ✅ 可選功能（不影響核心分析）
- ✅ 成本可控（僅分析關鍵路徑）

### 7.6 增量分析（Incremental Analysis）⚡ (新增 - 研究報告建議)

**目的**: 只處理變更檔案，提升日常使用效率 95%

- [ ] **Git 整合**
  - [ ] **檔案變更偵測**:
    ```python
    def detect_changes(base_commit="HEAD~1"):
        # Get changed files from git diff
        changed_files = git.diff(base_commit, name_only=True)

        return {
            "modified": [f for f in changed_files if f.endswith(('.java', '.jsp', '.xml'))],
            "added": git.diff(base_commit, diff_filter='A'),
            "deleted": git.diff(base_commit, diff_filter='D')
        }
    ```
  - [ ] **影響範圍分析**:
    - [ ] 變更 JSP → 重新分析該 JSP + 更新圖譜
    - [ ] 變更 Controller → 重新分析 Controller + 更新關聯 Service
    - [ ] 變更 Service → 更新下游 Mapper 關係
    - [ ] 變更 Mapper XML → 重新解析 SQL + 更新 Table 關係

- [ ] **增量圖譜更新**
  - [ ] **節點更新策略**:
    ```python
    def incremental_update(graph, changed_files):
        for file in changed_files['modified']:
            # Remove old nodes from this file
            old_nodes = graph.nodes_from_file(file)
            graph.remove_nodes(old_nodes)

            # Re-analyze file
            new_structure = parse_file(file)
            new_nodes = create_nodes(new_structure)
            graph.add_nodes(new_nodes)

            # Update edges
            affected_edges = graph.edges_involving(old_nodes)
            graph.remove_edges(affected_edges)
            rebuild_edges(graph, new_nodes)
    ```
  - [ ] **快取重用**:
    - [ ] Semantic cache hits: 70-80% (未變更檔案的 LLM 分析結果)
    - [ ] Parser results cache: 100% (未變更檔案跳過 parsing)

- [ ] **效能對比**（研究報告數據）
  ```yaml
  全量分析（500K LOC）:
    時間: 25 分鐘
    成本: $75
    涵蓋: 100% 檔案

  增量分析（10% 變更）:
    時間: 3 分鐘 (95% faster)
    成本: $10 (87% cheaper)
    涵蓋: 10% 檔案 + 受影響節點
  ```

- [ ] **CI/CD 整合**
  - [ ] **Pre-commit Hook**:
    ```bash
    # .git/hooks/pre-commit
    python -m springmvc_analyzer --incremental --changed-only

    # 檢查新增的安全風險
    if [ $? -ne 0 ]; then
        echo "❌ 發現新的安全風險，請修復"
        exit 1
    fi
    ```
  - [ ] **Pull Request 分析**:
    ```yaml
    # .github/workflows/analyze-pr.yml
    name: Code Analysis
    on: [pull_request]
    jobs:
      analyze:
        runs-on: ubuntu-latest
        steps:
          - name: Incremental Analysis
            run: |
              python -m springmvc_analyzer \
                --incremental \
                --base-commit ${{ github.event.pull_request.base.sha }} \
                --output pr_analysis.html

          - name: Comment PR
            uses: actions/github-script@v6
            with:
              script: |
                // Post analysis results as PR comment
    ```

- [ ] **Slash Commands**
  ```
  /analyze-changes [--since HEAD~1]
    - 分析 git diff 中的變更
    - 增量更新知識圖譜
    - 輸出變更影響範圍報告

  /impact-analysis <file_path>
    - 顯示修改此檔案會影響哪些節點
    - 列出所有上游與下游依賴
  ```

- [ ] **並行分析支援**（asyncio）
  ```python
  async def analyze_incremental(changed_files):
      # Phase 3: Parallel parsing (no API limits)
      parse_tasks = [parse_file_async(f) for f in changed_files]
      structures = await asyncio.gather(*parse_tasks)

      # Phase 5: Rate-limited LLM calls
      async with asyncio.Semaphore(10):
          llm_tasks = [analyze_ambiguous_async(s) for s in structures]
          results = await asyncio.gather(*llm_tasks)

      return merge_results(structures, results)
  ```

**增量分析核心原則**:
- ✅ **快速回饋**: 3 分鐘內完成（vs 25 分鐘全量）
- ✅ **成本可控**: $10 vs $75（87% 降低）
- ✅ **準確性**: 與全量分析相同（基於同樣的 parser + LLM）
- ✅ **CI/CD 友好**: 自動化整合，每次 commit/PR 都分析

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

### 1. ⭐ 為何採用 Parsing-First 策略？（Phase 3）

**決策**: Phase 3 專注於結構化提取（Pure Parsing）

**理由**:
1. **可靠性**: 結構化資訊（URL、類別名、方法名）100% 準確，不受 LLM 幻覺影響
2. **速度**: 解析 1000+ 檔案秒級完成，無需等待 API
3. **成本**: 不消耗 Claude API quota
4. **可測試性**: 純 parsing 邏輯易於單元測試
5. **知識圖譜基礎**: 準確的結構化資料是圖譜的基石

**實作原則**:
- Phase 3: 使用 lxml, BeautifulSoup, javalang, sqlparse（純 parsing）
- 輸出: 100% 準確的結構化 JSON

### 2. ⭐ 為何採用混合雙層圖譜構建？（Phase 5）

**決策**: Layer 1 (程式碼) + Layer 2 (LLM 完整性掃描) + 持續改進循環

**問題**: 純程式碼建立圖譜的困境
```python
# Parser 難以處理的案例
$.ajax({url: '${pageContext.request.contextPath}/user/save'})
@RequestMapping("${api.base.path}/user")  # 配置檔路徑
location.href = ctx + '/user/detail/' + userId  # 動態拼接
```

**解決方案**:
```
Layer 1 (程式碼): 建立明確關係
  ├─ @Autowired 依賴 (confidence=1.0)
  ├─ include 路徑 (confidence=1.0)
  └─ 簡單 URL (confidence=0.8-1.0)

Layer 2 (LLM): 完整性掃描
  ├─ 模糊 URL mapping (confidence=0.6-0.9)
  ├─ 發現遺漏關係
  └─ ⭐ 提供 Parser 改進建議

持續改進循環:
  └─ LLM 建議 → 人工審核 → 更新 regex → 下次更準確
```

**優勢**:
1. **完整性**: 不遺漏邊界情況（動態 URL、EL 表達式）
2. **準確性**: 明確關係由程式碼保證
3. **可追蹤**: 每個關係有 confidence 與 evidence
4. **自我優化**: Parser 持續改進，越用越準

**對比**:
| 項目 | 純 Parsing | 純 LLM | 混合雙層 |
|------|-----------|--------|----------|
| 明確關係準確度 | 100% | ~90% | 100% |
| 模糊關係完整度 | 60% | 95% | 95% |
| 處理速度 | 秒級 | 分鐘級 | 分鐘級 |
| API 成本 | $0 | $高 | $中 (僅掃描) |
| 持續改進 | 難 | 無 | ✅ |

### 3. 為何使用多 Agent 架構？
- **模組化**: 每個分析器獨立，易於維護與擴展
- **Context 管理**: 避免單一 Agent 超過 200k token 限制
- **並行處理**: 多個分析器可並行執行
- **專精分析**: Phase 7 每個 trace path 獨立分析

### 4. 為何 DB 提取不使用 LLM？
- **安全性**: 密碼不經過 LLM
- **準確性**: 直接查詢系統表，100% 準確
- **效能**: 本地提取快速，不消耗 API Quota
- **可靠性**: 不受 LLM 幻覺影響
- **一致性**: 與 Parsing-First 策略一致

### 5. 為何使用 MCP Protocol？
- **Claude Code 原生支援**: 無縫整合
- **Slash Commands**: 提供更好的 UX
- **未來擴展**: 可整合其他 AI IDE（Copilot CLI 等）

### 6. Phase 1 Procedure 分析的特殊性
**為何 Phase 1 使用 LLM？**
- Procedure 程式碼複雜（PL/SQL），難以純 parsing 理解業務用途
- 需要推測觸發方式（非結構化資訊）
- 風險評估需要語意理解
- 數量較少（通常數十個），成本可控

**但仍保持安全性**:
- Procedure source code 本地提取（不經過 LLM）
- 僅分析結果經過 LLM
- 密碼安全（環境變數）

---

## 當前進度

- [x] Phase 1: 基礎設施建設（100%） ✅ 2025-10-02
- [x] Phase 2: MCP Server 骨架（100%） ✅ 2025-10-03
- [ ] Phase 3: 程式碼結構提取（0%） - **Pure Parsing**
- [ ] Phase 4: Slash Commands（0%）
- [ ] Phase 5: 知識圖譜構建（0%） - **Hybrid Dual-Layer + 持續改進**
- [ ] Phase 6: 文檔與測試（5%）
- [ ] Phase 7: 語意豐富化（0%） - **Trace-Based LLM Analysis**

**最新完成**: Phase 2 - MCP Server 骨架 + Code Review 改進

**策略調整** (2025-10-03):
- ✅ 採用 **Parsing-First** 策略（Phase 3）
- ✅ 採用 **混合雙層** 圖譜構建（Phase 5）
  - Layer 1: 程式碼建立明確關係（confidence=1.0）
  - Layer 2: LLM 完整性掃描 + Parser 改進建議
  - 🔄 持續改進循環（LLM 發現問題 → 提供 regex 建議 → 自動應用）
- Phase 7: 基於 trace path 的語意豐富化

**下一步**: Phase 3.1 - JSP 結構提取器（lxml + Regex parsing）
