# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SpringMVC Knowledge Graph Analyzer - An automated knowledge graph builder for legacy SpringMVC + JSP + MyBatis + Oracle projects using Claude Agent SDK and MCP Protocol.

**Analysis Path**: JSP (includes, AJAX) → Spring Controller → Service → MyBatis Mapper → SQL → Oracle Tables/Stored Procedures

## Setup and Testing

### Initial Setup
```bash
# Install in development mode
pip install -e .

# Auto-configure Claude Code MCP Server
python scripts/setup_claude.py

# Test MCP Server and dependencies
python scripts/test_mcp_server.py
```

### Oracle Database Configuration
- Connection config: `config/oracle_config.yaml` (copy from `oracle_config.example.yaml`)
- Passwords via environment variables: `ORACLE_DEV_PASSWORD`, `ORACLE_TEST_PASSWORD`, `ORACLE_PROD_PASSWORD`
- **Critical**: Passwords NEVER pass through LLM - database extraction is local-only

### Running Database Extraction
```bash
# Extract Oracle schema (standalone)
python -c "from mcp_server.tools.db_extractor import extract_db_schema_by_config; extract_db_schema_by_config('dev', 'output/db_schema.json')"

# Analyze a specific procedure
python mcp_server/tools/procedure_analyzer.py SYNC_USER_DATA

# Analyze all procedures
python mcp_server/tools/procedure_analyzer.py --all
```

## Architecture

### Multi-Agent Design Philosophy

**Why Multiple Specialized Agents?**
1. **Context Management**: Each analyzer runs in isolated session to avoid 200k token limit
2. **Modularity**: Independent analysis tools for JSP, Controller, Service, Mapper, SQL, DB Schema
3. **Prompt Specialization**: Each agent has domain-specific prompts for higher accuracy
4. **Parallel Processing**: Multiple analyzers can run concurrently

### MCP Server Integration

This project uses **MCP (Model Context Protocol)** instead of packaged executables:
- Native integration with Claude Code CLI
- Future compatibility with GitHub Copilot CLI
- Slash commands for better UX (planned in Phase 4)
- Easy prompt modification without recompilation

### Data Flow

```
┌─────────────────┐
│  User Request   │
│  (Claude Code)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  MCP Server     │◄─────┤ Slash Commands   │ (Phase 4)
│  (Main Router)  │      │ /extract-oracle  │
└────────┬────────┘      │ /analyze-jsp     │
         │               │ /build-graph     │
         │               └──────────────────┘
         │
    ┌────┴────┬────────────┬───────────┬────────────┐
    ▼         ▼            ▼           ▼            ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐
│  JSP   │ │Control.│ │Service │ │MyBatis │ │  DB/Proc   │
│Analyzer│ │Analyzer│ │Analyzer│ │Analyzer│ │  Extractor │
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └─────┬──────┘
    │          │           │          │            │
    └──────────┴───────────┴──────────┴────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │ Graph Builder  │
                  │ (NetworkX)     │
                  └────────────────┘
```

### Critical Design Decisions

**Database Extraction (NOT via LLM)**
- Direct queries to Oracle system tables: `user_tables`, `user_procedures`, `user_scheduler_jobs`, `user_jobs`
- 100% accuracy, no hallucination risk
- Security: credentials never pass through Claude API
- Performance: faster, no API quota consumption

**Procedure Analysis (via Claude Agent SDK)**
- 8-dimension deep analysis (see `mcp_server/prompts/procedure_analysis.txt`)
- Business purpose inference from code patterns
- Trigger detection from multiple sources:
  1. Oracle Triggers (`user_triggers`)
  2. Oracle Scheduler Jobs (`user_scheduler_jobs`, `user_jobs`)
  3. Java Batch Jobs (MyBatis `statementType="CALLABLE"`)
- Conflict detection with existing batch jobs
- Integration difficulty assessment with concrete implementation steps

## Key Components

### Base Tool Pattern (mcp_server/tools/base_tool.py) - PENDING

All analysis tools inherit from `BaseTool`:
- Claude Agent SDK session management
- Result caching (avoid re-analysis)
- Batch analysis support
- JSON extraction from Claude responses (handles both markdown and raw JSON)

### Database Extractor (mcp_server/tools/db_extractor.py) - COMPLETE

**Class**: `OracleSchemaExtractor`

**Key Methods**:
- `extract_tables()`: Tables with columns, PKs, indexes, FKs, triggers
- `extract_views()`: View definitions and columns
- `extract_sequences()`: Sequences with min/max/increment/cycle
- `extract_synonyms()`: Local and remote synonyms with resolved table names
- `extract_procedures_and_functions()`: Procedures/Functions with:
  - Parameters from `user_arguments`
  - Source code from `user_source`
  - Dependencies from `user_dependencies`
  - **Separate extraction for package members** (each procedure/function as independent item)
- `extract_oracle_jobs()`: Both modern (`user_scheduler_jobs`) and legacy (`user_jobs`)
- `_extract_procedure_from_job_action()`: Regex-based procedure name extraction from PL/SQL job actions

**Output**: `output/db_schema.json` with complete Oracle metadata

### Procedure Analyzer (mcp_server/tools/procedure_analyzer.py) - COMPLETE

**Class**: `ProcedureAnalyzer`

**Analysis Dimensions** (see prompt template):
1. **Business Purpose**: Infer main function, scenario, frequency, data volume
2. **Operation Type**: DATA_MAINTENANCE, BATCH_PROCESSING, DATA_SYNC, REPORT_GENERATION, etc.
3. **Impact Analysis**: Which tables affected (READ/INSERT/UPDATE/DELETE/TRUNCATE)
4. **Trigger Method Detection** (CRITICAL):
   - Source A: Trigger info from db_schema
   - Source B: Oracle Job info from db_schema
   - Source C: MyBatis Mapper CALLABLE statements
   - Output: trigger type + confidence level (high/medium/low) + reasoning
5. **Exception & Transaction Handling**: Error handling quality, transaction scope, rollback logic
6. **Conflict Analysis**: Potential conflicts with existing batch jobs (data race, lock, resource, logic)
7. **Batch Job Integration Recommendation**:
   - Options: A (merge into existing), B (new batch job), C (keep as-is), D (refactor to Java)
   - Difficulty assessment, effort estimation, pros/cons, prerequisites, implementation steps
8. **Risk Assessment & Optimization**: Performance, data integrity, security, maintainability

**Context Injection**:
- Loads `output/db_schema.json` for procedure metadata
- Loads `output/analysis/mybatis_analysis.json` for Java caller detection (if exists)
- Future: Load existing batch job info (TODO in `_load_existing_batch_jobs()`)

## Prompt Templates

### Location
`mcp_server/prompts/*.txt`

### Currently Implemented
- `procedure_analysis.txt`: 8-dimension Stored Procedure analysis (323 lines, comprehensive)

### Planned (Phase 3)
- `jsp_analysis.txt`: JSP includes, AJAX calls, form targets
- `controller_analysis.txt`: @RequestMapping, Service dependencies
- `service_analysis.txt`: @Autowired Mappers, transaction boundaries
- `mybatis_analysis.txt`: Mapper XML parsing, SQL extraction, CALLABLE detection
- `sql_analysis.txt`: Table/column extraction, JOIN analysis, performance risks

### Customization Strategy
Prompts are **plain text templates** using Python `.format()`:
- Easy modification without code changes
- Restart Claude Code after modification to reload
- Use concrete examples in prompts for better LLM performance
- Request JSON output with explicit schema definitions

## Implementation Status (See IMPLEMENTATION_PLAN.md)

**Phase 1: Foundation** ✅ COMPLETE
- Project structure, setup scripts, Oracle config
- Database extractor with full Oracle support (Tables, Views, Sequences, Synonyms, Procedures, Jobs)
- Procedure analyzer with 8-dimension analysis

**Phase 2: MCP Server Skeleton** 🔄 IN PROGRESS (10%)
- [ ] base_tool.py - Base class for all analyzers
- [ ] springmvc_mcp_server.py - MCP Protocol implementation

**Phase 3: Code Analysis Tools** 📝 PLANNED (0%)
- [ ] JSP Analyzer (lxml parsing, AJAX extraction)
- [ ] Controller Analyzer (javalang parsing, @RequestMapping extraction)
- [ ] Service Analyzer (javalang parsing, @Transactional detection)
- [ ] MyBatis Analyzer (XML parsing, SQL + CALLABLE extraction)
- [ ] SQL Analyzer (sqlparse, table/column extraction)

**Phase 4: Slash Commands** ⭐ PLANNED (0%)
- Database commands: `/extract-oracle-schema`, `/analyze-procedure`, `/list-oracle-jobs`
- Analysis commands: `/analyze-jsp`, `/analyze-controller`, `/scan-project`
- Graph commands: `/build-graph`, `/query-path`, `/find-procedure-callers`
- Report commands: `/generate-report`, `/detect-conflicts`, `/audit-transactions`
- Utility commands: `/status`, `/clear-cache`, `/config`

**Phase 5: Knowledge Graph** 🕸️ PLANNED (0%)
- Graph Builder (NetworkX): Nodes (JSP, CONTROLLER, SERVICE, MAPPER, TABLE, PROCEDURE, ORACLE_JOB)
- Graph Query: Path finding, dependency analysis, impact analysis, orphan detection
- Visualization: Mermaid, GraphViz, HTML interactive

## Development Guidelines

### Adding New Analysis Tool

1. **Create Prompt Template** in `mcp_server/prompts/<tool_name>_analysis.txt`:
   - Define clear analysis dimensions
   - Request JSON output with explicit schema
   - Include concrete examples

2. **Create Analyzer** in `mcp_server/tools/<tool_name>_analyzer.py`:
   ```python
   from mcp_server.tools.base_tool import BaseTool

   class MyAnalyzer(BaseTool):
       def __init__(self):
           super().__init__(
               tool_name="my_analyzer",
               prompt_template="my_analysis.txt"
           )

       async def analyze_async(self, identifier, context, force_refresh=False):
           # Check cache
           if not force_refresh:
               cached = self._load_cache(identifier)
               if cached:
                   return cached

           # Build prompt with context
           prompt = self.prompt_template.format(**context)

           # Query Claude
           response = await self._query_claude(prompt)

           # Extract JSON
           analysis = self._extract_json_from_response(response)

           # Save cache
           self._save_cache(identifier, analysis)

           return analysis
   ```

3. **Register MCP Tool** in `mcp_server/springmvc_mcp_server.py`:
   - Add tool registration
   - Define input schema
   - Implement tool handler

### Adding Slash Command

1. **Create Command Handler** in `mcp_server/commands/<category>_commands.py`:
   ```python
   async def my_command(arg1: str, arg2: Optional[str] = None) -> Dict[str, Any]:
       """
       Command description

       Args:
           arg1: First argument
           arg2: Optional second argument

       Returns:
           Command result
       """
       # Implementation
       return {"status": "success", "result": ...}
   ```

2. **Register in MCP Server** with proper argument schema

### Working with Oracle Database

**Connection Pattern**:
```python
import oracledb

# Get password from environment
password = os.getenv("ORACLE_DEV_PASSWORD")
if not password:
    password = getpass.getpass(f"Password for {user}@{dsn}: ")

# Connect (thin mode, no Oracle Client needed)
connection = oracledb.connect(user=user, password=password, dsn=dsn)
cursor = connection.cursor()

# Query system tables
cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
```

**Never hardcode credentials** - always use environment variables or interactive input.

### Analyzing Procedures

**Key Patterns to Detect**:
- Exception handling: Look for `EXCEPTION WHEN ... THEN`
- Transaction management: `COMMIT`, `ROLLBACK`, `AUTONOMOUS_TRANSACTION`
- Trigger calls: Check `user_triggers` for procedure name in trigger body
- Job scheduling: Parse `job_action` field from `user_scheduler_jobs`
- Batch job calls: Search MyBatis mappers for `statementType="CALLABLE"`

**Confidence Levels**:
- **High**: Direct evidence (e.g., found in `user_scheduler_jobs`)
- **Medium**: Indirect evidence (e.g., procedure name pattern suggests batch processing)
- **Low**: Pure inference from code structure

## Output Structure

```
output/
├── db_schema.json                 # Complete Oracle metadata
├── analysis/
│   ├── procedures/
│   │   ├── SYNC_USER_DATA.json   # Individual procedure analysis
│   │   ├── CALC_MONTHLY_REPORT.json
│   │   └── _summary.json         # Batch analysis summary
│   ├── mybatis_analysis.json     # MyBatis mapper analysis (future)
│   ├── jsp_analysis/             # JSP analysis results (future)
│   ├── controller_analysis/      # Controller analysis results (future)
│   └── service_analysis/         # Service analysis results (future)
└── knowledge_graph.json           # Final knowledge graph (future)
```

## Common Tasks for Future Development

### Implementing JSP Analyzer (Phase 3.1)
- Use `lxml.html` to parse JSP as HTML
- Extract `<jsp:include>` and `<%@ include %>` directives
- Use regex to find AJAX calls in `<script>` tags: `$.ajax`, `fetch()`, `XMLHttpRequest`
- Parse `<form action="...">` to find controller endpoints
- Handle EL expressions: `${...}` for data flow

### Implementing Controller Analyzer (Phase 3.2)
- Use `javalang` to parse Java source code
- Extract class-level and method-level `@RequestMapping` annotations
- Combine paths: `@RequestMapping("/users")` + `@RequestMapping("/list")` = `/users/list`
- Find `@Autowired` fields to detect Service dependencies
- Parse method calls to trace Service method invocations

### Implementing MyBatis Analyzer (Phase 3.4)
- Parse Mapper.xml with `lxml.etree`
- Extract `<select>`, `<insert>`, `<update>`, `<delete>` statements
- **Critical for Procedure detection**: Find `statementType="CALLABLE"` statements
- Parse `<call>` tags or embedded `{call procedure_name(?, ?)}`
- Match Mapper interface methods with XML statements by `id`

### Building Knowledge Graph (Phase 5.1)
```python
import networkx as nx

G = nx.DiGraph()

# Add nodes
G.add_node("userList.jsp", type="JSP", path="/WEB-INF/views/user/list.jsp")
G.add_node("UserController.getUsers", type="CONTROLLER", method="GET", path="/users/list")
G.add_node("UserService.listUsers", type="SERVICE")
G.add_node("UserMapper.selectAllUsers", type="MAPPER")
G.add_node("USERS", type="TABLE")
G.add_node("SYNC_USER_DATA", type="PROCEDURE")

# Add edges
G.add_edge("userList.jsp", "UserController.getUsers", relation="AJAX_CALL", url="/users/list")
G.add_edge("UserController.getUsers", "UserService.listUsers", relation="INVOKES")
G.add_edge("UserService.listUsers", "UserMapper.selectAllUsers", relation="CALLS")
G.add_edge("UserMapper.selectAllUsers", "USERS", relation="QUERIES", operation="SELECT")
G.add_edge("SYNC_USER_DATA", "USERS", relation="MODIFIES", operation="UPDATE")

# Query examples
paths = nx.all_simple_paths(G, "userList.jsp", "USERS")
upstream = nx.ancestors(G, "USERS")  # What depends on USERS table
downstream = nx.descendants(G, "UserService.listUsers")  # What does this service affect
```

## Testing Strategy

**Unit Tests** (Phase 6.3):
- Test each analyzer independently with sample inputs
- Mock Claude API responses for deterministic testing
- Test Oracle queries with in-memory SQLite when possible

**Integration Tests**:
- Use `examples/sample_project/` as test fixture
- Full end-to-end analysis pipeline
- Verify knowledge graph construction

**Manual Testing**:
```bash
# Test database extraction
python scripts/test_mcp_server.py

# Test procedure analysis on real Oracle DB
python mcp_server/tools/procedure_analyzer.py <procedure_name>
```

## Critical Notes

- **Security**: Never commit `config/oracle_config.yaml` (in `.gitignore`)
- **Performance**: Cache analysis results to avoid re-analyzing unchanged code
- **Context Window**: Each analyzer should output intermediate JSON, not raw code, to avoid token overflow
- **Prompt Engineering**: Use explicit JSON schemas in prompts, include examples, request confidence levels for inferences
- **Oracle Specifics**: This tool is Oracle-specific, not generic SQL - leverage Oracle system tables fully
