# Phase 4: Slash Commands & MCP Integration

## 📋 Overview

Integrate Phase 3 analyzers (JSP, Controller, Service, MyBatis) into the MCP server with slash commands for CLI access.

## 🎯 Objectives

1. Register Phase 3 analyzers as MCP tools
2. Create slash commands for easy access
3. Implement command handlers with proper error handling
4. Add comprehensive tests
5. Document usage and examples

## 🔧 Phase 3 Analyzers to Integrate

| Analyzer | Status | LOC | Test Coverage |
|----------|--------|-----|---------------|
| JSP Analyzer | ✅ Complete | 617 | 15 tests |
| Controller Analyzer | ✅ Complete | 613 | Validated |
| Service Analyzer | ✅ Complete | 630 | Validated |
| MyBatis Analyzer | ✅ Complete | 655 | 12 tests (100%) |

**Total:** ~2,515 LOC with comprehensive test coverage

## 📦 MCP Tools to Register

### Tool 1: analyze_jsp
**Description:** Analyze JSP file structure and extract UI components

**Parameters:**
```json
{
  "jsp_file": {
    "type": "string",
    "description": "Path to JSP file",
    "required": true
  },
  "output_file": {
    "type": "string",
    "description": "Output JSON file path"
  },
  "force_refresh": {
    "type": "boolean",
    "description": "Force refresh (ignore cache)",
    "default": false
  }
}
```

**Handler:** `JSPAnalyzer.analyze_async()`

---

### Tool 2: analyze_controller
**Description:** Analyze Spring MVC Controller structure

**Parameters:**
```json
{
  "controller_file": {
    "type": "string",
    "description": "Path to Controller Java file",
    "required": true
  },
  "output_file": {
    "type": "string",
    "description": "Output JSON file path"
  },
  "force_refresh": {
    "type": "boolean",
    "description": "Force refresh (ignore cache)",
    "default": false
  }
}
```

**Handler:** `ControllerAnalyzer.analyze_async()`

---

### Tool 3: analyze_service
**Description:** Analyze Spring Service layer structure

**Parameters:**
```json
{
  "service_file": {
    "type": "string",
    "description": "Path to Service Java file",
    "required": true
  },
  "output_file": {
    "type": "string",
    "description": "Output JSON file path"
  },
  "force_refresh": {
    "type": "boolean",
    "description": "Force refresh (ignore cache)",
    "default": false
  }
}
```

**Handler:** `ServiceAnalyzer.analyze_async()`

---

### Tool 4: analyze_mybatis
**Description:** Analyze MyBatis Mapper (interface + XML)

**Parameters:**
```json
{
  "interface_file": {
    "type": "string",
    "description": "Path to Mapper interface Java file",
    "required": true
  },
  "xml_file": {
    "type": "string",
    "description": "Path to Mapper XML file"
  },
  "output_file": {
    "type": "string",
    "description": "Output JSON file path"
  },
  "force_refresh": {
    "type": "boolean",
    "description": "Force refresh (ignore cache)",
    "default": false
  }
}
```

**Handler:** `MyBatisAnalyzer.analyze_async()`

---

## 🔪 Slash Commands

### Command 1: /analyze-jsp
**Usage:** `/analyze-jsp <jsp_file> [options]`

**Example:**
```bash
/analyze-jsp src/main/webapp/WEB-INF/views/user/list.jsp
/analyze-jsp user/list.jsp --output analysis/jsp_result.json
```

---

### Command 2: /analyze-controller
**Usage:** `/analyze-controller <controller_file> [options]`

**Example:**
```bash
/analyze-controller src/main/java/com/example/controller/UserController.java
/analyze-controller UserController.java --force-refresh
```

---

### Command 3: /analyze-service
**Usage:** `/analyze-service <service_file> [options]`

**Example:**
```bash
/analyze-service src/main/java/com/example/service/UserService.java
/analyze-service UserService.java --output analysis/service_result.json
```

---

### Command 4: /analyze-mybatis
**Usage:** `/analyze-mybatis <interface_file> [xml_file] [options]`

**Example:**
```bash
/analyze-mybatis UserMapper.java UserMapper.xml
/analyze-mybatis src/main/java/com/example/mapper/UserMapper.java --xml src/main/resources/mapper/UserMapper.xml
```

---

### Command 5: /analyze-all
**Usage:** `/analyze-all <project_root> [options]`

**Description:** Batch analyze entire Spring MVC project

**Example:**
```bash
/analyze-all /path/to/springmvc-project
/analyze-all . --output-dir analysis/full-scan
```

**Process:**
1. Scan project directory structure
2. Detect JSP files, Controllers, Services, MyBatis mappers
3. Run all analyzers in parallel
4. Generate comprehensive analysis report
5. Create dependency graph

---

## 🏗️ Implementation Architecture

```
mcp_server/
├── springmvc_mcp_server.py        # Main MCP server (update)
├── tools/
│   ├── base_tool.py               # Base class (existing)
│   ├── jsp_analyzer.py            # Phase 3.1 ✅
│   ├── controller_analyzer.py     # Phase 3.2 ✅
│   ├── service_analyzer.py        # Phase 3.3 ✅
│   ├── mybatis_analyzer.py        # Phase 3.4 ✅
│   └── batch_analyzer.py          # NEW: /analyze-all
├── commands/                       # NEW: Slash command handlers
│   ├── __init__.py
│   ├── analyze_jsp_cmd.py
│   ├── analyze_controller_cmd.py
│   ├── analyze_service_cmd.py
│   ├── analyze_mybatis_cmd.py
│   └── analyze_all_cmd.py
└── tests/                         # NEW: Integration tests
    ├── test_mcp_tools.py
    ├── test_slash_commands.py
    └── test_batch_analyzer.py
```

---

## 🔄 Implementation Steps

### Step 1: Update MCP Server (springmvc_mcp_server.py)
- [ ] Import Phase 3 analyzers
- [ ] Register 4 new MCP tools
- [ ] Implement tool handlers (async wrappers)
- [ ] Add error handling and validation

### Step 2: Create Slash Commands (commands/)
- [ ] Create `commands/__init__.py`
- [ ] Implement `/analyze-jsp` command
- [ ] Implement `/analyze-controller` command
- [ ] Implement `/analyze-service` command
- [ ] Implement `/analyze-mybatis` command
- [ ] Implement `/analyze-all` command (batch)

### Step 3: Create Batch Analyzer (tools/batch_analyzer.py)
- [ ] Project structure scanner
- [ ] File pattern detection
- [ ] Parallel analysis executor
- [ ] Dependency graph builder
- [ ] Report generator

### Step 4: Add Integration Tests
- [ ] Test MCP tool registration
- [ ] Test tool invocation
- [ ] Test slash command parsing
- [ ] Test batch analyzer
- [ ] Test error handling

### Step 5: Documentation & Examples
- [ ] Update README with Phase 4 usage
- [ ] Create SLASH_COMMANDS.md
- [ ] Add example outputs
- [ ] Create video demo (optional)

---

## ✅ Acceptance Criteria

1. **Tool Registration:** All 4 Phase 3 analyzers registered as MCP tools
2. **Slash Commands:** All 5 commands functional with proper argument parsing
3. **Error Handling:** Comprehensive error handling with user-friendly messages
4. **Test Coverage:** >90% coverage for new code
5. **Documentation:** Complete usage documentation
6. **Performance:** Batch analyzer processes project in <5 minutes
7. **Backward Compatibility:** No breaking changes to Phase 1-3 code

---

## 📊 Expected Deliverables

| Deliverable | LOC Estimate | Status |
|-------------|--------------|--------|
| MCP Server Update | ~200 | Pending |
| Slash Commands | ~400 | Pending |
| Batch Analyzer | ~500 | Pending |
| Integration Tests | ~300 | Pending |
| Documentation | ~500 | Pending |
| **Total** | **~1,900** | **Pending** |

---

## 🔗 Dependencies

- Phase 1: Database Extraction ✅
- Phase 2: MCP Server Skeleton ✅
- Phase 3.1: JSP Analyzer ✅
- Phase 3.2: Controller Analyzer ✅
- Phase 3.3: Service Analyzer ✅
- Phase 3.4: MyBatis Analyzer ✅

---

## 🚀 Next Phase Preview

**Phase 5: Knowledge Graph Construction**
- Build Neo4j knowledge graph from analysis results
- Semantic relationship extraction using LLM
- Query interface for dependency tracing
- Visualization dashboard

---

*Phase 4 Plan - Version 1.0*
*Author: keepprogress*
*Date: 2025-10-04*
