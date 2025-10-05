# MCP Tools Reference

**Version**: 0.4.4-alpha
**Last Updated**: 2025-10-05

This document provides a complete reference for all MCP (Model Context Protocol) tools available in the SpringMVC Knowledge Graph Analyzer.

---

## Table of Contents

1. [Overview](#overview)
2. [Database Tools](#database-tools)
3. [Code Analysis Tools](#code-analysis-tools)
4. [Query Tools](#query-tools)
5. [Tool Response Format](#tool-response-format)
6. [Error Handling](#error-handling)
7. [Usage Examples](#usage-examples)

---

## Overview

The SpringMVC MCP Server exposes **8 tools** for analyzing SpringMVC projects and Oracle databases. All tools follow a consistent interface and return structured JSON responses.

### Tool Categories

| Category | Tools | Description |
|----------|-------|-------------|
| **Database** | 2 tools | Oracle schema extraction and procedure analysis |
| **Code Analysis** | 4 tools | JSP, Controller, Service, MyBatis analysis |
| **Query** | 2 tools | Dependency graph queries and impact analysis |

### General Parameters

Most tools accept these common parameters:

- `force_refresh` (boolean, optional): Force re-analysis, ignore cache
- `output_file` (string, optional): Save results to specified file
- `project_path` (string, optional): Override project root directory

---

## Database Tools

### 1. extract_oracle_schema

Extract complete Oracle database schema including tables, views, procedures, and jobs.

**Parameters:**

```json
{
  "environment": {
    "type": "string",
    "required": true,
    "description": "Environment name (dev/test/prod)",
    "example": "dev"
  },
  "output_file": {
    "type": "string",
    "required": false,
    "description": "Output file path",
    "default": "output/db_schema.json"
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "✓ Oracle schema extracted successfully",
  "schema": {
    "database": "DEV_DB",
    "tables": 156,
    "views": 23,
    "procedures": 45,
    "functions": 12,
    "jobs": 8
  },
  "output_file": "output/db_schema.json"
}
```

**What Gets Extracted:**

- **Tables**: columns, data types, constraints, indexes, foreign keys, triggers
- **Views**: definition, columns, dependencies
- **Sequences**: current value, increment, min/max values, cycle
- **Synonyms**: local and remote, resolved target tables
- **Procedures/Functions**: parameters, source code, dependencies, package members
- **Oracle Jobs**: scheduler jobs and legacy jobs, procedure calls

**Security Note:**

Passwords are loaded from environment variables only:
- `ORACLE_DEV_PASSWORD`
- `ORACLE_TEST_PASSWORD`
- `ORACLE_PROD_PASSWORD`

Credentials **never** pass through the LLM.

---

### 2. analyze_stored_procedure

Deep analysis of Oracle stored procedures with business context and integration recommendations.

**Parameters:**

```json
{
  "procedure_name": {
    "type": "string",
    "required": true,
    "description": "Name of procedure to analyze",
    "example": "SYNC_USER_DATA"
  },
  "db_schema_file": {
    "type": "string",
    "required": false,
    "description": "Path to db_schema.json",
    "default": "output/db_schema.json"
  },
  "mybatis_analysis_file": {
    "type": "string",
    "required": false,
    "description": "Path to MyBatis analysis for caller detection",
    "default": "output/analysis/mybatis_analysis.json"
  },
  "output_file": {
    "type": "string",
    "required": false,
    "description": "Output file path",
    "default": "output/analysis/procedures/{procedure_name}.json"
  }
}
```

**Analysis Dimensions:**

1. **Business Purpose**: Main function, scenario, frequency, data volume
2. **Operation Type**: DATA_MAINTENANCE, BATCH_PROCESSING, DATA_SYNC, etc.
3. **Impact Analysis**: Tables affected (READ/INSERT/UPDATE/DELETE/TRUNCATE)
4. **Trigger Method**: How procedure is invoked (triggers, jobs, callable statements)
5. **Exception Handling**: Error handling quality, transaction scope, rollback logic
6. **Conflict Analysis**: Potential conflicts with existing batch jobs
7. **Integration Recommendation**: Merge, new job, keep as-is, or refactor options
8. **Risk Assessment**: Performance, data integrity, security, maintainability

**Response:**

```json
{
  "success": true,
  "message": "✓ Procedure analysis complete: SYNC_USER_DATA",
  "analysis": {
    "procedure_name": "SYNC_USER_DATA",
    "business_purpose": "Synchronizes user data from external system...",
    "operation_type": "DATA_SYNC",
    "impact": {
      "tables_read": ["USERS", "USER_PROFILE"],
      "tables_modified": ["USERS", "SYNC_LOG"]
    },
    "trigger_method": {
      "type": "ORACLE_SCHEDULER",
      "confidence": "high",
      "schedule": "Daily at 02:00"
    },
    "recommendation": {
      "option": "B",
      "description": "Create new batch job",
      "difficulty": "medium",
      "effort_days": 3
    }
  },
  "output_file": "output/analysis/procedures/SYNC_USER_DATA.json"
}
```

---

## Code Analysis Tools

### 3. analyze_jsp

Analyze JSP file structure, includes, AJAX calls, and form targets.

**Parameters:**

```json
{
  "jsp_file": {
    "type": "string",
    "required": true,
    "description": "Path to JSP file (relative or absolute)",
    "example": "src/main/webapp/WEB-INF/views/user/list.jsp"
  },
  "force_refresh": {
    "type": "boolean",
    "required": false,
    "default": false
  },
  "output_file": {
    "type": "string",
    "required": false
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "✓ JSP analysis complete: user/list.jsp",
  "result": {
    "jsp_file": "user/list.jsp",
    "includes": {
      "static": ["common/header.jsp", "common/footer.jsp"],
      "dynamic": ["${userType}/menu.jsp"]
    },
    "ajax_calls": [
      {"url": "/api/users", "method": "GET"},
      {"url": "/api/users/delete", "method": "POST"}
    ],
    "forms": [
      {"action": "/users/search", "method": "GET"},
      {"action": "/users/update", "method": "POST"}
    ],
    "statistics": {
      "total_elements": 145,
      "total_forms": 2,
      "total_tables": 1,
      "total_scripts": 3
    }
  },
  "output_file": "output/analysis/jsp/user_list.json"
}
```

**Extracted Information:**

- **Includes**: Static (`<%@ include %>`) and dynamic (`<jsp:include>`)
- **AJAX Calls**: All AJAX requests in `<script>` tags
- **Forms**: Action URLs and methods
- **UI Elements**: Tables, lists, inputs
- **Dependencies**: Taglib declarations, EL expressions

---

### 4. analyze_controller

Analyze Spring MVC Controller with request mappings and service dependencies.

**Parameters:**

```json
{
  "controller_file": {
    "type": "string",
    "required": true,
    "description": "Path to Controller Java file",
    "example": "src/main/java/com/example/controller/UserController.java"
  },
  "force_refresh": {
    "type": "boolean",
    "required": false,
    "default": false
  },
  "output_file": {
    "type": "string",
    "required": false
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "✓ Controller analysis complete: UserController",
  "result": {
    "class_name": "UserController",
    "base_path": "/users",
    "endpoints": [
      {
        "path": "/users/list",
        "method": "GET",
        "handler": "getUserList",
        "return_type": "String",
        "view": "user/list"
      },
      {
        "path": "/users/{id}",
        "method": "GET",
        "handler": "getUser",
        "params": ["id"],
        "return_type": "ModelAndView"
      }
    ],
    "dependencies": {
      "services": ["UserService", "AuthService"],
      "autowired_count": 2
    },
    "statistics": {
      "total_endpoints": 12,
      "get_methods": 8,
      "post_methods": 4
    }
  }
}
```

**Extracted Information:**

- **Request Mappings**: Class and method level paths, HTTP methods
- **Service Dependencies**: @Autowired services
- **Method Calls**: Service method invocations
- **Parameters**: @RequestParam, @PathVariable, @RequestBody
- **Return Types**: View names, ModelAndView, @ResponseBody

---

### 5. analyze_service

Analyze Spring Service layer with transaction boundaries and mapper dependencies.

**Parameters:**

```json
{
  "service_file": {
    "type": "string",
    "required": true,
    "description": "Path to Service Java file",
    "example": "src/main/java/com/example/service/UserService.java"
  },
  "force_refresh": {
    "type": "boolean",
    "required": false,
    "default": false
  },
  "output_file": {
    "type": "string",
    "required": false
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "✓ Service analysis complete: UserService",
  "result": {
    "class_name": "UserService",
    "annotations": ["@Service", "@Transactional"],
    "methods": [
      {
        "name": "getUserById",
        "parameters": ["Long id"],
        "return_type": "User",
        "transactional": true,
        "mapper_calls": ["UserMapper.selectById"]
      }
    ],
    "dependencies": {
      "mappers": ["UserMapper", "RoleMapper"],
      "services": ["LogService"],
      "autowired_count": 3
    },
    "transactions": {
      "class_level": true,
      "method_overrides": 2,
      "propagation_types": ["REQUIRED", "REQUIRES_NEW"]
    }
  }
}
```

**Extracted Information:**

- **Annotations**: @Service, @Component, @Transactional
- **Dependencies**: @Autowired mappers and services
- **Methods**: Signatures, transaction settings, mapper calls
- **Exception Handling**: Try-catch blocks, throws declarations
- **Transaction Boundaries**: Class and method level settings

---

### 6. analyze_mybatis

Analyze MyBatis Mapper interface and XML with SQL extraction.

**Parameters:**

```json
{
  "interface_file": {
    "type": "string",
    "required": true,
    "description": "Path to Mapper interface Java file",
    "example": "src/main/java/com/example/mapper/UserMapper.java"
  },
  "xml_file": {
    "type": "string",
    "required": false,
    "description": "Path to Mapper XML file (auto-detected if not provided)",
    "example": "src/main/resources/mapper/UserMapper.xml"
  },
  "force_refresh": {
    "type": "boolean",
    "required": false,
    "default": false
  },
  "output_file": {
    "type": "string",
    "required": false
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "✓ MyBatis analysis complete: UserMapper",
  "result": {
    "interface_name": "UserMapper",
    "xml_file": "mapper/UserMapper.xml",
    "methods": [
      {
        "name": "selectById",
        "params": ["@Param(\"id\") Long id"],
        "return_type": "User",
        "sql_type": "SELECT",
        "tables": ["USERS"],
        "callable": false
      },
      {
        "name": "syncUserData",
        "params": [],
        "return_type": "void",
        "sql_type": "CALLABLE",
        "procedure": "SYNC_USER_DATA",
        "callable": true
      }
    ],
    "statistics": {
      "total_methods": 15,
      "select_count": 10,
      "insert_count": 2,
      "update_count": 2,
      "delete_count": 1,
      "callable_count": 1
    }
  }
}
```

**Extracted Information:**

- **Interface Methods**: Method signatures with @Param annotations
- **XML Statements**: `<select>`, `<insert>`, `<update>`, `<delete>`
- **SQL Analysis**: Table names, operation types
- **CALLABLE Detection**: Stored procedure calls (`{call procedure(?, ?)}`)
- **Parameter Mapping**: Interface params to XML placeholders
- **Coverage**: Which methods have XML implementations

---

## Query Tools

### 7. find_chain

Find call chains (paths) from start node to end node in dependency graph.

**Parameters:**

```json
{
  "start_node": {
    "type": "string",
    "required": true,
    "description": "Starting node name",
    "example": "UserController"
  },
  "end_node": {
    "type": "string",
    "required": false,
    "description": "Ending node name (if omitted, returns direct dependencies)",
    "example": "UserMapper"
  },
  "max_depth": {
    "type": "integer",
    "required": false,
    "default": 10,
    "description": "Maximum search depth (max: 20)"
  },
  "max_paths": {
    "type": "integer",
    "required": false,
    "default": 100,
    "description": "Maximum number of paths to return"
  },
  "project_path": {
    "type": "string",
    "required": false,
    "default": "."
  },
  "cache_dir": {
    "type": "string",
    "required": false,
    "default": ".batch_cache"
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "✓ Found 3 call chain(s)",
  "data": {
    "start_node": "UserController",
    "end_node": "UserMapper",
    "total_chains": 3,
    "chains": [
      {
        "path": ["UserController", "UserService", "UserMapper"],
        "node_types": ["controller", "service", "mapper"],
        "edge_types": ["CALLS", "CALLS"],
        "depth": 2
      },
      {
        "path": ["UserController", "AdminService", "UserMapper"],
        "node_types": ["controller", "service", "mapper"],
        "edge_types": ["CALLS", "CALLS"],
        "depth": 2
      },
      {
        "path": ["UserController", "CacheService", "UserMapper"],
        "node_types": ["controller", "service", "mapper"],
        "edge_types": ["CALLS", "CALLS"],
        "depth": 2
      }
    ]
  }
}
```

**Use Cases:**

- Trace request flow from controller to database
- Find all paths between two components
- Identify redundant call chains
- Understand component dependencies

**Performance:**

- Uses optimized DFS with backtracking
- O(V + E) complexity with depth limit
- Edge lookup: O(1) with hash map cache
- Typical query time: < 100ms

---

### 8. impact_analysis

Analyze impact of changing a component (upstream and downstream dependencies).

**Parameters:**

```json
{
  "node": {
    "type": "string",
    "required": true,
    "description": "Node to analyze",
    "example": "UserService"
  },
  "direction": {
    "type": "string",
    "required": false,
    "enum": ["upstream", "downstream", "both"],
    "default": "both",
    "description": "Analysis direction"
  },
  "max_depth": {
    "type": "integer",
    "required": false,
    "default": 5,
    "description": "Maximum depth to analyze (max: 20)"
  },
  "project_path": {
    "type": "string",
    "required": false,
    "default": "."
  },
  "cache_dir": {
    "type": "string",
    "required": false,
    "default": ".batch_cache"
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "✓ Impact analysis complete: 12 affected component(s)",
  "data": {
    "target_node": "UserService",
    "upstream": {
      "level_1": [
        "[controller] UserController",
        "[controller] AdminController"
      ],
      "level_2": [
        "[jsp] user/list.jsp"
      ]
    },
    "downstream": {
      "level_1": [
        "[mapper] UserMapper",
        "[service] LogService"
      ],
      "level_2": [
        "[table] USERS",
        "[table] USER_LOG"
      ]
    },
    "total_upstream": 3,
    "total_downstream": 4
  }
}
```

**Directions Explained:**

- **upstream**: Who depends on this component? (needs testing if changed)
- **downstream**: What does this component depend on? (review for breaking changes)
- **both**: Complete bidirectional analysis

**Use Cases:**

- Refactoring impact assessment
- Change risk analysis
- Test scope determination
- Dependency auditing

---

## Tool Response Format

All tools follow a consistent response format:

### Success Response

```json
{
  "success": true,
  "message": "✓ Operation complete: <details>",
  "result": {
    // Tool-specific result data
  },
  "output_file": "path/to/output.json" // If file was saved
}
```

### Error Response

```json
{
  "success": false,
  "error": "Detailed error message explaining what went wrong",
  "error_type": "ValidationError|FileNotFound|AnalysisError|DatabaseError"
}
```

### Common Error Types

| Error Type | Description | Common Causes |
|------------|-------------|---------------|
| `ValidationError` | Invalid input parameters | Missing required fields, invalid values |
| `FileNotFound` | File or resource not found | Wrong path, file doesn't exist |
| `AnalysisError` | Analysis failed | Parsing errors, unsupported syntax |
| `DatabaseError` | Database operation failed | Connection issues, invalid credentials |
| `GraphError` | Graph query failed | Node not found, graph not built |

---

## Error Handling

### Graceful Degradation

Tools attempt to extract as much information as possible even when errors occur:

```json
{
  "success": true,
  "message": "✓ Analysis complete with warnings",
  "result": {
    // Partial results
  },
  "warnings": [
    "Failed to parse method signature at line 45",
    "Unknown annotation @CustomAnnotation ignored"
  ],
  "partial": true
}
```

### Validation

All tools validate inputs before execution:

- Required parameters checked
- File paths validated
- Numeric ranges enforced
- Enums verified

### Retry Logic

Database tools include automatic retry for transient errors:

- Connection timeouts: 3 retries with exponential backoff
- Network errors: Automatic reconnection
- Transaction conflicts: Retry with jitter

---

## Usage Examples

### Python

```python
from mcp_server.springmvc_mcp_server import SpringMVCMCPServer

# Initialize server
server = SpringMVCMCPServer(project_root="/path/to/project")

# Call tool
result = await server.handle_tool_call(
    tool_name="analyze_controller",
    arguments={
        "controller_file": "src/main/java/com/example/UserController.java",
        "force_refresh": True
    }
)

if result["success"]:
    print(f"Found {result['result']['statistics']['total_endpoints']} endpoints")
else:
    print(f"Error: {result['error']}")
```

### Via MCP Protocol

```json
{
  "method": "tools/call",
  "params": {
    "name": "find_chain",
    "arguments": {
      "start_node": "UserController",
      "end_node": "UserMapper",
      "max_depth": 5
    }
  }
}
```

### Batch Processing

```python
# Analyze all controllers
from pathlib import Path

controllers = Path("src/main/java").rglob("*Controller.java")

for controller in controllers:
    result = await server.handle_tool_call(
        tool_name="analyze_controller",
        arguments={"controller_file": str(controller)}
    )
    # Process result...
```

---

## Performance Considerations

### Caching

- All analysis results are cached by default
- Cache key: file path + modification time hash
- Use `force_refresh=true` to bypass cache
- Cache location: `.batch_cache/` (configurable)

### Parallelization

- Batch operations use parallel execution
- Default: 10 concurrent workers
- Configurable via `ANALYZER.DEFAULT_MAX_WORKERS`
- Automatic rate limiting for API calls

### Memory Management

- Streaming for large files
- Incremental graph building
- Bounded path finding (max 100 paths by default)
- Automatic cleanup of old cache files

---

## Configuration

Tools can be configured via `mcp_server/config.py`:

```python
from mcp_server.config import QUERY, CACHE, ANALYZER

# Query settings
QUERY.DEFAULT_MAX_DEPTH_CHAIN = 10
QUERY.MAX_PATHS_LIMIT = 100

# Cache settings
CACHE.DEFAULT_CACHE_DIR = ".batch_cache"
CACHE.CACHE_MAX_AGE_HOURS = 24

# Analyzer settings
ANALYZER.DEFAULT_MAX_WORKERS = 10
```

---

## See Also

- [Slash Commands Reference](SLASH_COMMANDS.md) - CLI-style command interface
- [Query Engine Documentation](QUERY_ENGINE.md) - Dependency graph queries
- [Phase 4 Progress](../PHASE_4_PROGRESS.md) - Implementation status
- [Implementation Plan](../IMPLEMENTATION_PLAN.md) - Full project roadmap

---

**Last Updated**: 2025-10-05
**Version**: 0.4.4-alpha
**Status**: Production Ready
