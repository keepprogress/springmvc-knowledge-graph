# Slash Commands Reference

Phase 4.2 - CLI-style commands for SpringMVC Knowledge Graph MCP Server

## Overview

Slash commands provide a convenient CLI-style interface to access all analysis tools. Each command maps to a corresponding MCP tool and provides the same functionality with a more user-friendly syntax.

## Available Commands

### Command Aliases

For convenience, all commands support short aliases:

| Full Command | Aliases | Description |
|--------------|---------|-------------|
| `/analyze-jsp` | `/jsp` | JSP analysis |
| `/analyze-controller` | `/controller` | Controller analysis |
| `/analyze-service` | `/service` | Service analysis |
| `/analyze-mybatis` | `/mybatis`, `/mb` | MyBatis analysis |

**Example:**
```bash
/mb UserMapper.java UserMapper.xml  # Same as /analyze-mybatis
```

---

### `/analyze-jsp`

Analyze JSP file structure and extract UI components.

**Syntax:**
```bash
/analyze-jsp <jsp_file> [--output <file>] [--force-refresh]
```

**Arguments:**
- `jsp_file` - Path to JSP file (required)
- `--output`, `-o` - Output JSON file path (optional)
- `--force-refresh`, `-f` - Force refresh, ignore cache (optional)

**Examples:**
```bash
/analyze-jsp user_list.jsp
/analyze-jsp src/main/webapp/WEB-INF/views/user/list.jsp
/analyze-jsp user_list.jsp --output analysis/jsp.json
/analyze-jsp user_list.jsp --force-refresh
```

**Output:**
```json
{
  "success": true,
  "message": "✓ JSP analysis complete: user_list.jsp",
  "data": {
    "jsp_file": "user_list.jsp",
    "total_elements": 42,
    "forms": 1,
    "tables": 1,
    "scripts": 3,
    "output_file": "analysis/jsp.json"
  }
}
```

---

### `/analyze-controller`

Analyze Spring MVC Controller structure.

**Syntax:**
```bash
/analyze-controller <controller_file> [--output <file>] [--force-refresh]
```

**Arguments:**
- `controller_file` - Path to Controller Java file (required)
- `--output`, `-o` - Output JSON file path (optional)
- `--force-refresh`, `-f` - Force refresh, ignore cache (optional)

**Examples:**
```bash
/analyze-controller UserController.java
/analyze-controller src/main/java/com/example/controller/UserController.java
/analyze-controller UserController.java --output analysis/controller.json
/analyze-controller UserController.java --force-refresh
```

**Output:**
```json
{
  "success": true,
  "message": "✓ Controller analysis complete: UserController.java",
  "data": {
    "controller_name": "UserController",
    "total_endpoints": 8,
    "GET": 4,
    "POST": 2,
    "PUT": 1,
    "DELETE": 1,
    "output_file": "analysis/controller.json"
  }
}
```

---

### `/analyze-service`

Analyze Spring Service layer structure.

**Syntax:**
```bash
/analyze-service <service_file> [--output <file>] [--force-refresh]
```

**Arguments:**
- `service_file` - Path to Service Java file (required)
- `--output`, `-o` - Output JSON file path (optional)
- `--force-refresh`, `-f` - Force refresh, ignore cache (optional)

**Examples:**
```bash
/analyze-service UserService.java
/analyze-service src/main/java/com/example/service/UserService.java
/analyze-service UserService.java --output analysis/service.json
/analyze-service UserService.java --force-refresh
```

**Output:**
```json
{
  "success": true,
  "message": "✓ Service analysis complete: UserService.java",
  "data": {
    "service_name": "UserService",
    "total_methods": 12,
    "public_methods": 8,
    "transactional_methods": 6,
    "is_service": true,
    "output_file": "analysis/service.json"
  }
}
```

---

### `/analyze-mybatis`

Analyze MyBatis Mapper (interface + XML).

**Syntax:**
```bash
/analyze-mybatis <interface_file> [<xml_file>] [--xml <file>] [--output <file>] [--force-refresh]
```

**Arguments:**
- `interface_file` - Path to Mapper interface Java file (required)
- `xml_file` - Path to Mapper XML file (optional, positional)
- `--xml`, `-x` - Path to Mapper XML file (optional, alternative to positional)
- `--output`, `-o` - Output JSON file path (optional)
- `--force-refresh`, `-f` - Force refresh, ignore cache (optional)

**Examples:**
```bash
/analyze-mybatis UserMapper.java
/analyze-mybatis UserMapper.java UserMapper.xml
/analyze-mybatis UserMapper.java --xml UserMapper.xml
/analyze-mybatis UserMapper.java UserMapper.xml --output analysis/mapper.json
/analyze-mybatis UserMapper.java --force-refresh
```

**Output:**
```json
{
  "success": true,
  "message": "✓ MyBatis analysis complete: UserMapper.java",
  "data": {
    "mapper_name": "UserMapper",
    "interface_methods": 7,
    "xml_statements": 7,
    "mapped_methods": 7,
    "coverage": "7/7",
    "output_file": "analysis/mapper.json"
  }
}
```

---

## Advanced Features

### 1. Quoted Arguments

Command line arguments support shell-style quoting for paths with spaces:

```bash
/analyze-jsp "path/to/file with spaces.jsp" --output "output/result file.json"
```

The command parser uses Python's `shlex` module for proper quote handling.

### 2. Command Discovery

Use `list_commands()` method to discover available commands:

```python
from mcp_server.springmvc_mcp_server import SpringMVCMCPServer

server = SpringMVCMCPServer(project_root="/path/to/project")
commands = server.list_commands()

for cmd in commands:
    print(f"{cmd['name']}: {cmd['description']}")
    if cmd['aliases']:
        print(f"  Aliases: {', '.join(cmd['aliases'])}")
```

### 3. Logging

Enable logging for debugging and monitoring:

```python
# Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
server = SpringMVCMCPServer(project_root=".", log_level="DEBUG")

result = await server.handle_command("/analyze-jsp test.jsp")
```

**Log Output:**
```
2025-10-04 21:35:01,449 - springmvc_mcp_server - INFO - Command received: /analyze-jsp test.jsp
2025-10-04 21:35:01,449 - springmvc_mcp_server - INFO - Command succeeded: /analyze-jsp
```

### 4. Validation Decorator

All commands use `@validate_args` decorator for consistent error handling:

```python
from mcp_server.commands.base_command import BaseCommand, validate_args

class MyCommand(BaseCommand):
    @validate_args
    async def execute(self, args: List[str]) -> Dict[str, Any]:
        parsed_args = self.parse_args(args)
        # ... command logic
```

This decorator:
- Catches `SystemExit` from argparse
- Converts to standardized error response
- Provides helpful error messages

---

## Command Architecture

### Base Command Class

All commands inherit from `BaseCommand` which provides:

- **Argument parsing** - Using Python's `argparse`
- **Error handling** - Standardized error responses
- **Path resolution** - Relative to project root
- **Response formatting** - Success/error response structure

### Command Registration

Commands are automatically registered in `SpringMVCMCPServer`:

```python
# Initialize command instances
self._command_instances = {
    'analyze-jsp': AnalyzeJSPCommand(self),
    'analyze-controller': AnalyzeControllerCommand(self),
    'analyze-service': AnalyzeServiceCommand(self),
    'analyze-mybatis': AnalyzeMyBatisCommand(self)
}

# Register all commands
self._register_commands()
```

### Command Execution Flow

1. **Parse command line** - Extract command name and arguments
2. **Route to handler** - Find registered command instance
3. **Parse arguments** - Using command-specific argument parser
4. **Call MCP tool** - Invoke corresponding MCP tool
5. **Format response** - Return standardized response

### Example Usage (Python API)

```python
from mcp_server.springmvc_mcp_server import SpringMVCMCPServer

server = SpringMVCMCPServer(project_root="/path/to/project")

# Execute command
result = await server.handle_command(
    "/analyze-mybatis UserMapper.java UserMapper.xml --output out.json"
)

if result['success']:
    print(f"✓ {result['message']}")
    print(f"Data: {result['data']}")
else:
    print(f"✗ Error: {result['error']}")
```

---

## Error Handling

All commands return standardized error responses:

### Invalid Arguments

```bash
/analyze-jsp --invalid-flag
```

```json
{
  "success": false,
  "error": "Invalid arguments. Use --help for usage information."
}
```

### Unknown Command

```bash
/unknown-command test.jsp
```

```json
{
  "success": false,
  "error": "Unknown command: /unknown-command"
}
```

### File Not Found

```bash
/analyze-jsp nonexistent.jsp
```

```json
{
  "success": false,
  "error": "JSP analysis failed: File not found: nonexistent.jsp"
}
```

### Analysis Error

```json
{
  "success": false,
  "error": "MyBatis analysis failed: Failed to parse XML: Unexpected token"
}
```

---

## Command Help

Each command supports `--help` flag for detailed usage information:

```bash
/analyze-mybatis --help
```

**Output:**
```
usage: analyze-mybatis [-h] [--xml XML] [--output OUTPUT] [--force-refresh]
                       interface_file [xml_file]

Analyze MyBatis Mapper (interface + XML)

positional arguments:
  interface_file        Path to Mapper interface Java file
  xml_file              Path to Mapper XML file (optional, positional)

optional arguments:
  -h, --help            show this help message and exit
  --xml XML, -x XML     Path to Mapper XML file (alternative to positional)
  --output OUTPUT, -o OUTPUT
                        Output JSON file path
  --force-refresh, -f   Force refresh (ignore cache)

Examples:
  /analyze-mybatis UserMapper.java
  /analyze-mybatis UserMapper.java UserMapper.xml
  /analyze-mybatis UserMapper.java --xml UserMapper.xml
  /analyze-mybatis UserMapper.java UserMapper.xml --output analysis/mapper.json
  /analyze-mybatis UserMapper.java --force-refresh
```

---

## Testing

Run the slash commands test suite:

```bash
python tests/test_slash_commands.py
```

**Expected Output:**
```
============================================================
Testing Phase 4.2 Slash Commands (Enhanced)
============================================================

[Test 1/4] /analyze-jsp command
------------------------------------------------------------
✓ PASS: ✓ JSP analysis complete: test_samples/jsp/user_list.jsp

[Test 2/4] /analyze-controller command
------------------------------------------------------------
✓ PASS: ✓ Controller analysis complete: test_samples/controllers/UserController.java

[Test 3/4] /analyze-service command
------------------------------------------------------------
✓ PASS: ✓ Service analysis complete: test_samples/services/UserService.java

[Test 4/4] /analyze-mybatis command
------------------------------------------------------------
✓ PASS: ✓ MyBatis analysis complete: test_samples/mappers/UserMapper.java

[Bonus Test] Command with flags
------------------------------------------------------------
✓ PASS: Command with flags works

[Error Test] Invalid command
------------------------------------------------------------
✓ PASS: Invalid command rejected

[New Test 1] Quoted arguments with spaces
------------------------------------------------------------
✓ PASS: Quoted arguments parsed correctly
  Output file: output/test/path with spaces.json

[New Test 2] Command aliases
------------------------------------------------------------
✓ PASS: Command alias 'mb' works
  Mapper: UserMapper

[New Test 3] List commands discovery
------------------------------------------------------------
✓ PASS: Found 4 commands
  /analyze-controller: Analyze Spring MVC Controller structure (aliases: /controller)
  /analyze-jsp: Analyze JSP file structure (aliases: /jsp)
  /analyze-mybatis: Analyze MyBatis Mapper (aliases: /mybatis, /mb)
  /analyze-service: Analyze Spring Service layer (aliases: /service)

============================================================
Results: 9/9 tests passed
============================================================
```

---

## Implementation Files

- **`mcp_server/commands/base_command.py`** - Base command class
- **`mcp_server/commands/analyze_jsp_cmd.py`** - JSP analysis command
- **`mcp_server/commands/analyze_controller_cmd.py`** - Controller analysis command
- **`mcp_server/commands/analyze_service_cmd.py`** - Service analysis command
- **`mcp_server/commands/analyze_mybatis_cmd.py`** - MyBatis analysis command
- **`mcp_server/springmvc_mcp_server.py`** - Command registration and routing
- **`tests/test_slash_commands.py`** - Integration tests

---

## Future Commands (Planned)

- `/analyze-all` - Batch analyze all components in project
- `/build-graph` - Build complete knowledge graph
- `/query-path` - Query execution paths through layers
- `/extract-oracle-schema` - Extract database schema
- `/analyze-procedure` - Analyze stored procedures
- `/generate-docs` - Generate documentation from analysis

---

## See Also

- [Phase 4 Progress](../PHASE_4_PROGRESS.md) - Phase 4 implementation status
- [MCP Tools Reference](MCP_TOOLS.md) - Underlying MCP tools documentation
- [Phase 3 Analyzers](../PHASE_3_PROGRESS.md) - Analysis tool documentation
