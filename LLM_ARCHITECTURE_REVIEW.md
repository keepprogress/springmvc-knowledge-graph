# 解放LLM思維 - 架構設計審視

**Date**: 2025-10-05
**Philosophy**: LLM-First vs Code-First Balance

---

## 核心問題陳述

當前專案面臨兩個極端：

❌ **極端1: 完全Prompt驅動**
- 無方法論，浪費token
- 成本不可控
- 精度無保證

❌ **極端2: 完全Code驅動（當前狀態）**
- 過度工程化
- 無法隨LLM進化
- 維護成本高

✅ **理想狀態: 智能平衡**
- LLM處理複雜語意，Code處理確定邏輯
- 可隨模型能力提升而提升
- 成本可控，精度可保證

---

## 當前架構的「反LLM」傾向分析

### Phase 3: 程式碼結構提取 ⚠️ 過度工程化

**當前設計（Code-First）**:
```python
# JSP Analyzer - lxml parsing
- 用lxml解析HTML
- 用regex提取AJAX calls
- hardcoded所有可能的patterns

# Controller Analyzer - tree-sitter-java
- 寫複雜的tree-sitter queries
- 提取@RequestMapping
- 手動追蹤method calls

# Service Analyzer - tree-sitter-java
- 類似的tree-sitter邏輯
- 手動追蹤@Autowired

# MyBatis Analyzer - lxml + sqlparse
- XML parsing
- SQL parsing
- Table extraction
```

**問題**:
1. ❌ **大量維護成本** - 每個新annotation都要改code
2. ❌ **無法處理edge cases** - regex/parser無法理解語意
3. ❌ **不隨LLM進化** - Claude Opus 4出來，我們的工具不會變強
4. ❌ **過度精確但不靈活** - 100%準確但只能處理已知patterns

**LLM-First替代方案**:
```python
class LLMDrivenAnalyzer:
    """Let LLM do the heavy lifting"""

    async def analyze_any_file(self, file_path: str, file_type: str) -> Dict:
        """Universal analyzer - LLM figures out what to extract"""

        # 1. Read file (simple)
        code = Path(file_path).read_text()

        # 2. Ask LLM what's in this file (adaptive)
        prompt = f"""
        Analyze this {file_type} file and extract ALL relevant information.

        File: {file_path}

        Code:
        ```{file_type}
        {code[:5000]}  # Smart truncation, not hardcoded ±15 lines
        ```

        Extract (let LLM decide what's relevant):
        - For Controllers: endpoints, dependencies, method calls
        - For Services: transactional boundaries, dependencies
        - For JSP: includes, AJAX, forms, any UI interactions
        - For MyBatis: SQL, tables, procedures, parameters

        If you're unsure about something, ask for more context.
        Output structured JSON with confidence scores.
        """

        result = await self.llm.query(prompt)

        # 3. Validate critical parts only (not everything)
        if result.confidence < 0.7:
            # Use code parsing as fallback/validation
            code_result = await self.code_parser.parse(file_path, file_type)
            return self.merge_results(result, code_result)

        return result
```

**優勢**:
1. ✅ **一個analyzer處理所有文件類型**
2. ✅ **自動適應新框架**（SpringBoot 3.x新註解自動識別）
3. ✅ **隨LLM能力提升** - 模型變強，分析就變強
4. ✅ **處理edge cases** - LLM理解語意，不只是pattern matching

---

### Phase 5.1 vs 5.2: 主次顛倒 ⚠️

**當前設計**:
```
Phase 5.1 (主): Code-based Graph (100% certain)
Phase 5.2 (輔): LLM-based Graph (gap filling)
```

**問題分析**:

| Aspect | Code-First (5.1主) | LLM-First (5.2主) |
|--------|-------------------|-------------------|
| **靈活性** | ❌ 只能處理已知patterns | ✅ 適應任何code style |
| **完整性** | ⚠️ 會漏掉edge cases | ✅ 語意理解，很難漏 |
| **維護成本** | ❌ 每個新feature都要改code | ✅ 改prompt即可 |
| **進化能力** | ❌ 固定能力 | ✅ 隨模型提升 |
| **成本** | ✅ 免費 | ⚠️ 需要控制 |

**LLM-First替代設計**:
```python
# Phase 5 Redesign: LLM主導，Code驗證

class LLMFirstGraphBuilder:

    async def build_graph(self, project_dir: str) -> nx.DiGraph:
        """LLM主導建圖，Code輔助驗證"""

        # Step 1: 讓LLM理解整個專案結構（Adaptive Context）
        project_structure = await self.understand_project(project_dir)

        # Step 2: LLM自己決定分析策略
        analysis_plan = await self.llm.plan_analysis(project_structure)

        # Step 3: LLM執行分析（帶cache）
        for task in analysis_plan.tasks:
            llm_result = await self.llm.analyze(task)

            # Step 4: Code驗證關鍵部分（不是全部）
            if task.is_critical:
                code_validation = await self.validate_with_code(llm_result)
                if code_validation.conflicts:
                    # LLM重新分析，帶上衝突資訊
                    llm_result = await self.llm.reanalyze(
                        task,
                        validation_feedback=code_validation
                    )

            # Step 5: 建圖
            self.add_to_graph(llm_result)

        return self.graph
```

**核心轉變**:
- ❌ 舊: Code建圖 → LLM補洞
- ✅ 新: LLM建圖 → Code驗證關鍵部分

---

## 解放LLM的新架構設計

### 1. Prompt-First Pipeline ⭐

**設計理念**: 能用Prompt解決的，不寫Code

```python
class PromptFirstPipeline:
    """
    Pipeline: Prompt → (optional) Code Validation → Result
    """

    def __init__(self):
        self.llm = AdaptiveLLM()  # 自適應model selection
        self.code_validator = LightweightValidator()  # 輕量驗證

    async def analyze(self, input_data: Any) -> Result:
        # 1. Prompt嘗試（主力）
        llm_result = await self.prompt_analysis(input_data)

        # 2. 評估是否需要code validation（而不是預設都驗證）
        if self.needs_validation(llm_result):
            validation = await self.code_validator.validate(llm_result)

            if validation.failed:
                # 3. Prompt重試，帶validation feedback
                llm_result = await self.prompt_analysis(
                    input_data,
                    previous_attempt=llm_result,
                    validation_errors=validation.errors
                )

        return llm_result

    def needs_validation(self, result: Result) -> bool:
        """智能判斷是否需要code驗證"""
        return (
            result.confidence < 0.8 or  # 信心不足
            result.involves_critical_logic or  # 關鍵邏輯
            result.has_security_implications  # 安全相關
        )
```

**優勢**:
- ✅ Prompt為主，Code為輔
- ✅ 只在必要時用Code
- ✅ 自動平衡成本與精度

---

### 2. Adaptive Context Window ⭐

**問題**: 當前hardcoded ±15行context

**更好的方式**: 讓LLM自己決定需要多少context

```python
class AdaptiveContextExtractor:
    """LLM自適應決定context大小"""

    async def get_context_for_analysis(
        self,
        file_path: str,
        target_line: int,
        analysis_type: str
    ) -> str:
        """動態決定context window"""

        # Step 1: 先用小context問LLM
        initial_context = self.get_lines(file_path, target_line, window=5)

        initial_prompt = f"""
        分析這段代碼（第{target_line}行）。

        Context:
        {initial_context}

        請告訴我：
        1. 這段代碼的功能是什麼？
        2. 你需要更多context嗎？如果需要，需要看哪些部分？
           - 上下文行數？
           - 相關類別/方法？
           - Import statements？
        """

        initial_response = await self.llm.query(initial_prompt)

        # Step 2: 根據LLM要求擴展context
        if initial_response.needs_more_context:
            expanded_context = self.expand_context(
                file_path,
                initial_response.requested_context
            )

            final_prompt = f"""
            之前的分析：
            {initial_response.analysis}

            額外context：
            {expanded_context}

            現在完成分析。
            """

            return await self.llm.query(final_prompt)

        return initial_response
```

**優勢**:
- ✅ 不浪費token（不需要時不給多餘context）
- ✅ 不遺漏資訊（需要時主動要求）
- ✅ 適應不同複雜度的代碼

---

### 3. Agent-Based Analysis ⭐⭐⭐

**核心思想**: 讓LLM作為Agent，自己規劃分析策略

```python
class AnalysisAgent:
    """LLM Agent - 自主規劃和執行分析"""

    async def analyze_project(self, project_dir: str) -> KnowledgeGraph:
        """Agent自主分析專案"""

        # 1. Agent理解專案結構
        understanding = await self.understand_project_structure(project_dir)

        # 2. Agent自己制定分析計畫
        plan = await self.create_analysis_plan(understanding)
        # plan = {
        #   "strategy": "bottom-up",  # Agent自己決定策略
        #   "steps": [
        #       "先分析DB schema（基礎）",
        #       "再分析Mapper（數據層）",
        #       "然後Service（業務層）",
        #       "最後Controller和JSP（展示層）"
        #   ],
        #   "tools_needed": ["db_query", "file_read", "ast_parse"]
        # }

        # 3. Agent執行計畫（可調整）
        for step in plan.steps:
            result = await self.execute_step(step, plan.tools_needed)

            # Agent自我評估
            if not result.is_satisfactory:
                # Agent調整計畫
                plan = await self.adjust_plan(plan, result.issues)

        # 4. Agent建構知識圖譜
        graph = await self.build_knowledge_graph(
            self.analysis_results,
            strategy=plan.graph_building_strategy  # Agent決定建圖策略
        )

        return graph

    async def execute_step(self, step: str, tools: List[str]) -> Result:
        """Agent使用工具執行步驟"""

        # Agent自己決定用什麼工具
        tool_choice = await self.choose_tool(step, tools)

        if tool_choice == "llm_only":
            return await self.llm_analysis(step)
        elif tool_choice == "code_parser":
            return await self.code_parsing(step)
        elif tool_choice == "hybrid":
            # Agent自己決定混合策略
            return await self.hybrid_analysis(step)
```

**優勢**:
- ✅ **完全自主** - 不需要預先定義所有步驟
- ✅ **自我調整** - 遇到問題自動調整策略
- ✅ **工具選擇** - 自己決定用LLM還是Code Parser
- ✅ **隨模型進化** - 更強的模型 = 更好的策略

---

### 4. Hierarchical Model Strategy ⭐

**問題**: 當前沒有model selection策略

**改進**: 智能路由，用對的model做對的事

```python
class HierarchicalModelRouter:
    """分層模型策略 - 便宜model screening，貴model深度分析"""

    MODELS = {
        "haiku": {
            "cost": 0.25,  # per 1M tokens input
            "speed": "fast",
            "use_for": ["screening", "simple_extraction", "classification"]
        },
        "sonnet": {
            "cost": 3.0,
            "speed": "medium",
            "use_for": ["reasoning", "complex_analysis", "verification"]
        },
        "opus": {
            "cost": 15.0,
            "speed": "slow",
            "use_for": ["critical_decisions", "complex_reasoning", "edge_cases"]
        }
    }

    async def analyze_with_optimal_model(
        self,
        task: AnalysisTask
    ) -> Result:
        """智能選擇model"""

        # Step 1: Haiku screening
        haiku_result = await self.query_haiku(f"""
        Quick analysis: {task.description}

        Questions:
        1. Is this task simple or complex?
        2. Confidence level (0-1)?
        3. Do you need a more powerful model?
        """)

        # Step 2: 根據Haiku判斷，決定是否升級
        if haiku_result.is_simple and haiku_result.confidence > 0.9:
            return haiku_result  # Haiku就夠了，省錢

        # Step 3: Sonnet深度分析
        sonnet_result = await self.query_sonnet(f"""
        Haiku的初步分析：
        {haiku_result.analysis}

        請深度分析：
        {task.description}

        Haiku認為需要注意：{haiku_result.concerns}
        """)

        if sonnet_result.confidence > 0.85:
            return sonnet_result

        # Step 4: 極端情況用Opus
        if task.is_critical or sonnet_result.has_edge_cases:
            opus_result = await self.query_opus(f"""
            之前的分析：
            - Haiku: {haiku_result.summary}
            - Sonnet: {sonnet_result.summary}

            關鍵問題：
            {sonnet_result.critical_issues}

            請最終判斷。
            """)
            return opus_result

        return sonnet_result
```

**成本對比**:
```
情境：分析100個Controller

方案1（當前 - 全用Sonnet）:
- 100 files × 2000 tokens × $3/1M = $0.60

方案2（智能路由）:
- 80 files → Haiku screening → simple → $0.04
- 15 files → Sonnet深度分析 → $0.09
- 5 files → Opus關鍵決策 → $0.15
- Total: $0.28 (省了53%)

且精度更高（關鍵部分用Opus）
```

---

### 5. Self-Improving Prompt Library ⭐

**問題**: 當前prompts是static的

**改進**: Prompts從經驗中學習

```python
class SelfImprovingPromptLibrary:
    """自我改進的Prompt庫"""

    def __init__(self):
        self.prompt_templates = {}
        self.success_examples = {}  # 成功案例
        self.failure_patterns = {}   # 失敗模式

    async def get_prompt_for_task(
        self,
        task_type: str,
        context: Dict
    ) -> str:
        """取得優化過的prompt"""

        # 1. 基礎template
        base_template = self.prompt_templates[task_type]

        # 2. 加入成功案例（few-shot learning）
        few_shot = self.get_relevant_examples(task_type, context)

        # 3. 加入失敗教訓
        warnings = self.get_failure_warnings(task_type, context)

        # 4. 組合最優prompt
        optimized_prompt = f"""
        {base_template}

        參考這些成功案例：
        {few_shot}

        注意避免這些錯誤：
        {warnings}

        現在分析：
        {context}
        """

        return optimized_prompt

    def learn_from_result(
        self,
        task_type: str,
        prompt: str,
        result: Result,
        validation: Validation
    ):
        """從結果中學習"""

        if validation.is_success:
            # 成功 - 加入成功案例庫
            self.success_examples[task_type].append({
                "prompt": prompt,
                "result": result,
                "context": result.context,
                "confidence": result.confidence
            })
        else:
            # 失敗 - 記錄失敗模式
            self.failure_patterns[task_type].append({
                "prompt": prompt,
                "error": validation.error,
                "what_went_wrong": validation.analysis
            })

            # 自動改進prompt template
            self.improve_template(task_type, validation)

    def improve_template(self, task_type: str, validation: Validation):
        """自動改進prompt template"""

        improvement_prompt = f"""
        這個prompt template效果不好：
        {self.prompt_templates[task_type]}

        失敗原因：
        {validation.analysis}

        請改進這個template，使其避免這類錯誤。
        """

        improved = await self.llm.query(improvement_prompt)
        self.prompt_templates[task_type] = improved.new_template
```

**效果**:
- ✅ Prompts越用越好
- ✅ 自動學習edge cases
- ✅ 建立領域知識庫

---

## 新架構完整設計

### 整體架構圖

```
┌─────────────────────────────────────────────────┐
│           Analysis Agent (LLM-Driven)            │
│                                                   │
│  1. 理解專案 → 2. 制定計畫 → 3. 執行分析 → 4. 建圖  │
└────────────────────┬────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│  Prompt Engine    │      │  Tool Arsenal    │
│                   │      │                  │
│ • Adaptive Context│      │ • Code Parser    │
│ • Self-Improving  │      │ • DB Query       │
│ • Model Router    │      │ • AST Tools      │
└────────┬──────────┘      └────────┬─────────┘
         │                          │
         └──────────┬───────────────┘
                    ▼
         ┌──────────────────────┐
         │  Validation Layer     │
         │                       │
         │ • Critical checks     │
         │ • Confidence scoring  │
         │ • Conflict resolution │
         └──────────┬────────────┘
                    ▼
         ┌──────────────────────┐
         │  Knowledge Graph      │
         └──────────────────────┘
```

### 核心轉變

| Aspect | 舊設計 (Code-First) | 新設計 (LLM-First) |
|--------|--------------------|--------------------|
| **主導者** | Code parsers | LLM Agent |
| **Code角色** | 主力分析 | 驗證工具 |
| **Context** | 固定±15行 | 自適應 |
| **策略** | 預定義pipeline | Agent自主決定 |
| **Model** | 單一Sonnet | 分層路由(Haiku→Sonnet→Opus) |
| **Prompts** | Static | Self-improving |
| **進化能力** | ❌ 固定 | ✅ 隨模型提升 |
| **成本** | 中等 | 更低（智能路由） |
| **精度** | 高但有限 | 更高（關鍵處用Opus） |

---

## 具體實施建議

### Phase 3 重構建議

**Option 1: 漸進式（推薦）**
```python
# 保留現有parsers作為fallback，加入LLM層

class HybridAnalyzer:
    def __init__(self):
        self.llm_analyzer = LLMDrivenAnalyzer()
        self.code_parser = TreeSitterParser()  # 現有的

    async def analyze(self, file_path: str) -> Result:
        # 1. 先用LLM（快速，語意理解）
        llm_result = await self.llm_analyzer.analyze(file_path)

        # 2. 只在confidence低時用code parser驗證
        if llm_result.confidence < 0.8:
            code_result = self.code_parser.parse(file_path)
            return self.merge(llm_result, code_result)

        return llm_result
```

**Option 2: 激進式**
```python
# 完全用Agent，code parser變成tool

class AgentDrivenAnalyzer:
    async def analyze(self, file_path: str) -> Result:
        return await self.agent.analyze(
            task=f"分析{file_path}",
            tools=["llm", "tree_sitter", "regex", "ast"],
            let_agent_decide=True  # Agent自己決定用什麼工具
        )
```

### Phase 5 重構建議

**關鍵改變**:
1. **5.1和5.2合併** → 單一Agent-driven pipeline
2. **LLM主導** → Code驗證關鍵節點
3. **自適應策略** → Agent決定建圖順序

```python
class AgentGraphBuilder:
    async def build_graph(self, project_dir: str) -> nx.DiGraph:
        # Agent自主分析專案
        plan = await self.agent.understand_and_plan(project_dir)

        # Agent執行（混合LLM和Code）
        for step in plan.adaptive_steps:
            result = await self.agent.execute(
                step,
                prefer="llm",  # 優先用LLM
                fallback="code"  # 低信心時用code
            )
            self.graph.add(result)

        return self.graph
```

---

## 成本與效益分析

### 成本對比（中型專案500K LOC）

**當前設計（Code-First）**:
```
Phase 3: $0（code parsing）
Phase 5.1: $0（code parsing）
Phase 5.2: $40（LLM gap filling）
Total: $40
Time: 需要寫大量parsers，維護成本高
```

**新設計（LLM-First with智能路由）**:
```
Phase 3 (Agent-driven):
- Haiku screening: 500 files × $0.25/1M = $0.13
- Sonnet分析: 100 files × $3/1M = $0.30
- Opus關鍵: 20 files × $15/1M = $0.30
Subtotal: $0.73

Phase 5 (Agent建圖):
- Haiku關係推斷: $0.50
- Sonnet複雜關係: $2.00
- Opus關鍵決策: $1.00
Subtotal: $3.50

Total: $4.23

但是：
- ✅ 維護成本大幅降低（不用維護複雜parsers）
- ✅ 精度更高（Opus處理關鍵部分）
- ✅ 適應性更強（新框架自動支援）
- ✅ 隨模型進化（Claude 4出來自動變強）
```

### ROI分析

**Code-First維護成本（年）**:
- Parser更新: 40小時 × $100/小時 = $4,000
- Bug fixes: 20小時 × $100/小時 = $2,000
- 新feature: 60小時 × $100/小時 = $6,000
- **Total: $12,000/年**

**LLM-First維護成本（年）**:
- Prompt優化: 10小時 × $100/小時 = $1,000
- Model升級: 5小時 × $100/小時 = $500
- 監控調整: 5小時 × $100/小時 = $500
- **Total: $2,000/年**

**節省: $10,000/年** 💰

---

## 實施路線圖

### Week 1-2: Agent框架建設
```python
# 1. 建立Agent基礎設施
- AnalysisAgent基類
- Tool registry (LLM, Code parsers, etc.)
- Adaptive context system
- Model router

# 2. 重構一個analyzer作為POC
- 選擇Controller Analyzer（最複雜的）
- 實作Agent-driven版本
- 對比舊版效果
```

### Week 3-4: Prompt Engineering
```python
# 3. Self-improving prompt library
- 建立prompt templates
- Few-shot learning機制
- 失敗模式學習

# 4. Hierarchical model strategy
- Haiku/Sonnet/Opus路由
- 成本監控
- 效果評估
```

### Week 5-6: 全面應用
```python
# 5. Phase 3 全面Agent化
- 所有analyzers用Agent重寫
- Code parsers降級為tools

# 6. Phase 5 Agent建圖
- 統一的Agent-driven graph building
- 移除5.1/5.2分離
```

---

## 風險與對策

### Risk 1: LLM不穩定
**對策**:
- Code parsers作為fallback永遠保留
- Critical paths強制用code驗證

### Risk 2: 成本超支
**對策**:
- 嚴格的成本監控
- 每日budget限制
- Haiku screening強制執行

### Risk 3: 精度下降
**對策**:
- 建立gold-standard test set
- 每次變更都regression test
- Confidence threshold強制執行（<0.7必須code驗證）

---

## 結論與建議

### ✅ 強烈建議採用的改進

1. **Agent-Based架構** ⭐⭐⭐
   - 最符合「解放LLM」理念
   - 長期維護成本最低
   - 隨模型進化

2. **Hierarchical Model Strategy** ⭐⭐⭐
   - 立即降低成本50%+
   - 精度不降反升
   - 容易實施

3. **Self-Improving Prompts** ⭐⭐
   - 越用越好
   - 建立領域知識
   - 中期受益

4. **Adaptive Context** ⭐⭐
   - 不浪費token
   - 不遺漏資訊
   - 容易實施

### ⚠️ 需要謹慎評估

1. **完全移除Code Parsers**
   - 太激進，不建議
   - 保留作為fallback/validation

2. **完全依賴LLM**
   - 成本風險
   - 穩定性問題
   - 需要強力監控

### 📋 Action Items

**Immediate (本週)**:
1. ✅ 建立Agent基礎框架
2. ✅ 實作Model Router（Haiku→Sonnet→Opus）
3. ✅ POC: 用Agent重寫一個analyzer

**Short-term (2-4週)**:
1. Self-improving prompt library
2. Adaptive context system
3. Phase 3 漸進式重構

**Long-term (1-2月)**:
1. 全面Agent化
2. 建立知識庫
3. 持續優化

---

## 哲學總結

**平衡之道**:

```python
# ❌ 不要這樣（極端Code-First）
if problem:
    write_complex_parser()
    maintain_forever()
    cant_evolve()

# ❌ 也不要這樣（極端Prompt-First）
if problem:
    throw_money_at_llm()
    waste_tokens()
    no_control()

# ✅ 要這樣（智能平衡）
if problem:
    # 1. LLM先嘗試（主力）
    result = await llm.solve(problem)

    # 2. 評估需不需要code
    if result.needs_validation:
        validation = code.verify(result)

        if validation.failed:
            # 3. LLM重試，帶feedback
            result = await llm.solve(
                problem,
                learned_from=validation
            )

    # 4. 學習改進
    system.learn(result)

    return result
```

**核心原則**:
1. 🤖 **LLM為主**，Code為輔
2. 💰 **成本可控**，智能路由
3. 🎯 **精度保證**，關鍵驗證
4. 📈 **持續進化**，自我學習
5. 🛡️ **風險可控**，多重保險

---

**Status**: Architectural Philosophy Document
**Next**: Implement Agent Framework POC
**Goal**: Balance LLM capability with practical constraints

🤖 Generated with Claude Code
