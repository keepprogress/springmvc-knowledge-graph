#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SpringMVC Knowledge Graph - MCP Server

MCP (Model Context Protocol) Server for Claude Code integration

Phase 2: Basic skeleton with tool registration infrastructure
"""

import asyncio
import io
import json
import logging
import shlex
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List

# Windows console encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except AttributeError:
        pass  # Already wrapped or not needed

# Import MCP SDK (will be fully integrated in future phases)
try:
    from mcp import Server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    # Only show warning if not in test mode
    if 'pytest' not in sys.modules and 'unittest' not in sys.modules:
        print("⚠️  MCP SDK not fully available, running in stub mode", file=sys.stderr)
    MCP_AVAILABLE = False

# Import analysis tools (Phase 1 & 2)
from mcp_server.tools.db_extractor import extract_db_schema_by_config, extract_oracle_schema
from mcp_server.tools.procedure_analyzer import analyze_stored_procedures

# Import Phase 3 analyzers
from mcp_server.tools.jsp_analyzer import JSPAnalyzer
from mcp_server.tools.controller_analyzer import ControllerAnalyzer
from mcp_server.tools.service_analyzer import ServiceAnalyzer
from mcp_server.tools.mybatis_analyzer import MyBatisAnalyzer

# Import configuration
from mcp_server.config import QUERY, CACHE, ANALYZER

# Import Phase 4 slash commands
from mcp_server.commands import (
    AnalyzeJSPCommand,
    AnalyzeControllerCommand,
    AnalyzeServiceCommand,
    AnalyzeMyBatisCommand,
    AnalyzeAllCommand,
    FindChainCommand,
    ImpactAnalysisCommand,
    BuildGraphCommand,
    GraphStatsCommand
)


class SpringMVCMCPServer:
    """SpringMVC Knowledge Graph MCP Server"""

    def __init__(self, project_root: str = ".", log_level: str = "INFO"):
        self.name = "springmvc-analyzer"
        self.version = "0.4.4-alpha"  # Phase 4.4 - Query Engine
        self.project_root = Path(project_root)
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.commands: Dict[str, Dict[str, Any]] = {}

        # Initialize logging
        self.logger = logging.getLogger('springmvc_mcp_server')
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)

        # Initialize Phase 3 analyzers
        self.jsp_analyzer = JSPAnalyzer(project_root=str(self.project_root))
        self.controller_analyzer = ControllerAnalyzer(project_root=str(self.project_root))
        self.service_analyzer = ServiceAnalyzer(project_root=str(self.project_root))
        self.mybatis_analyzer = MyBatisAnalyzer(project_root=str(self.project_root))

        # Initialize Phase 4 slash commands
        self._command_instances = {
            'analyze-jsp': AnalyzeJSPCommand(self),
            'jsp': AnalyzeJSPCommand(self),  # Alias
            'analyze-controller': AnalyzeControllerCommand(self),
            'controller': AnalyzeControllerCommand(self),  # Alias
            'analyze-service': AnalyzeServiceCommand(self),
            'service': AnalyzeServiceCommand(self),  # Alias
            'analyze-mybatis': AnalyzeMyBatisCommand(self),
            'mybatis': AnalyzeMyBatisCommand(self),  # Alias
            'mb': AnalyzeMyBatisCommand(self),  # Short alias
            'analyze-all': AnalyzeAllCommand(self),
            'batch': AnalyzeAllCommand(self),  # Alias
            'find-chain': FindChainCommand(self),
            'chain': FindChainCommand(self),  # Alias
            'impact-analysis': ImpactAnalysisCommand(self),
            'impact': ImpactAnalysisCommand(self),  # Alias
            # Phase 6.1 - Graph Building Commands
            'build-graph': BuildGraphCommand(self),
            'graph': BuildGraphCommand(self),  # Alias
            'graph-stats': GraphStatsCommand(self),
            'stats': GraphStatsCommand(self),  # Alias
        }

        # Initialize tool and command registry
        self._register_tools()
        self._register_commands()

    def _register_tools(self):
        """
        註冊所有 MCP Tools

        Phase 2: 註冊 Phase 1 完成的工具
        Phase 3+: 將加入更多工具
        """

        # Tool 1: Extract Oracle Schema
        self.register_tool(
            name="extract_oracle_schema",
            description="提取 Oracle 資料庫 Schema（Tables, Views, Sequences, Synonyms, Procedures, Oracle Jobs）",
            parameters={
                "type": "object",
                "properties": {
                    "connection_name": {
                        "type": "string",
                        "description": "連線名稱（dev/test/prod），需要在 config/oracle_config.yaml 中定義",
                        "enum": ["dev", "test", "prod"]
                    },
                    "output_file": {
                        "type": "string",
                        "description": "輸出檔案路徑",
                        "default": "output/db_schema.json"
                    }
                },
                "required": ["connection_name"]
            },
            handler=self._handle_extract_oracle_schema
        )

        # Tool 2: Analyze Stored Procedure
        self.register_tool(
            name="analyze_stored_procedure",
            description="深度分析 Oracle Stored Procedure（8 維度分析：業務用途、觸發方式、風險評估等）",
            parameters={
                "type": "object",
                "properties": {
                    "procedure_name": {
                        "type": "string",
                        "description": "Procedure 名稱"
                    },
                    "analyze_all": {
                        "type": "boolean",
                        "description": "是否分析所有 Procedure",
                        "default": False
                    },
                    "output_file": {
                        "type": "string",
                        "description": "輸出檔案路徑（分析單個 Procedure 時使用）"
                    }
                },
                "required": []
            },
            handler=self._handle_analyze_procedure
        )

        # Tool 3: Analyze JSP (Phase 3.1)
        self.register_tool(
            name="analyze_jsp",
            description="Analyze JSP file structure and extract UI components",
            parameters={
                "type": "object",
                "properties": {
                    "jsp_file": {
                        "type": "string",
                        "description": "Path to JSP file"
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Output JSON file path"
                    },
                    "force_refresh": {
                        "type": "boolean",
                        "description": "Force refresh (ignore cache)",
                        "default": False
                    }
                },
                "required": ["jsp_file"]
            },
            handler=self._handle_analyze_jsp
        )

        # Tool 4: Analyze Controller (Phase 3.2)
        self.register_tool(
            name="analyze_controller",
            description="Analyze Spring MVC Controller structure",
            parameters={
                "type": "object",
                "properties": {
                    "controller_file": {
                        "type": "string",
                        "description": "Path to Controller Java file"
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Output JSON file path"
                    },
                    "force_refresh": {
                        "type": "boolean",
                        "description": "Force refresh (ignore cache)",
                        "default": False
                    }
                },
                "required": ["controller_file"]
            },
            handler=self._handle_analyze_controller
        )

        # Tool 5: Analyze Service (Phase 3.3)
        self.register_tool(
            name="analyze_service",
            description="Analyze Spring Service layer structure",
            parameters={
                "type": "object",
                "properties": {
                    "service_file": {
                        "type": "string",
                        "description": "Path to Service Java file"
                    },
                    "output_file": {
                        "type": "string",
                        "description": "Output JSON file path"
                    },
                    "force_refresh": {
                        "type": "boolean",
                        "description": "Force refresh (ignore cache)",
                        "default": False
                    }
                },
                "required": ["service_file"]
            },
            handler=self._handle_analyze_service
        )

        # Tool 6: Analyze MyBatis Mapper (Phase 3.4)
        self.register_tool(
            name="analyze_mybatis",
            description="Analyze MyBatis Mapper (interface + XML)",
            parameters={
                "type": "object",
                "properties": {
                    "interface_file": {
                        "type": "string",
                        "description": "Path to Mapper interface Java file"
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
                        "default": False
                    }
                },
                "required": ["interface_file"]
            },
            handler=self._handle_analyze_mybatis
        )

        # Tool 7: Find Call Chain (Phase 4.4)
        self.register_tool(
            name="find_chain",
            description="Find call chains from start node to end node in dependency graph",
            parameters={
                "type": "object",
                "properties": {
                    "start_node": {
                        "type": "string",
                        "description": "Starting node name (e.g., UserController)"
                    },
                    "end_node": {
                        "type": "string",
                        "description": "Ending node name (optional, shows direct dependencies if not provided)"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth to search",
                        "default": 10
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Project root directory (default: current project)"
                    },
                    "cache_dir": {
                        "type": "string",
                        "description": "Cache directory for loading previous analysis",
                        "default": ".batch_cache"
                    }
                },
                "required": ["start_node"]
            },
            handler=self._handle_find_chain
        )

        # Tool 8: Impact Analysis (Phase 4.4)
        self.register_tool(
            name="impact_analysis",
            description="Analyze impact of changing a component (shows upstream and downstream dependencies)",
            parameters={
                "type": "object",
                "properties": {
                    "node": {
                        "type": "string",
                        "description": "Node to analyze (e.g., UserService)"
                    },
                    "direction": {
                        "type": "string",
                        "description": "Analysis direction",
                        "enum": ["upstream", "downstream", "both"],
                        "default": "both"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth to analyze",
                        "default": 5
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Project root directory (default: current project)"
                    },
                    "cache_dir": {
                        "type": "string",
                        "description": "Cache directory for loading previous analysis",
                        "default": ".batch_cache"
                    }
                },
                "required": ["node"]
            },
            handler=self._handle_impact_analysis
        )

        print(f"✓ Registered {len(self.tools)} MCP Tools", file=sys.stderr)

    def _register_commands(self):
        """Register all slash commands (Phase 4.2)"""
        for cmd_name, cmd_instance in self._command_instances.items():
            self.register_command(
                name=cmd_name,
                description=cmd_instance.get_description(),
                handler=cmd_instance
            )
        print(f"✓ Registered {len(self.commands)} Slash Commands", file=sys.stderr)

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable
    ):
        """
        註冊 MCP Tool

        Args:
            name: 工具名稱
            description: 工具描述
            parameters: 參數定義
            handler: 處理函數
        """
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler
        }

    def register_command(
        self,
        name: str,
        description: str,
        handler: Callable
    ):
        """註冊 Slash Command（Phase 4 實作）"""
        self.commands[name] = {
            "name": name,
            "description": description,
            "handler": handler
        }

    async def _handle_extract_oracle_schema(self, **kwargs) -> Dict[str, Any]:
        """
        處理 extract_oracle_schema 工具調用

        Args:
            connection_name: 連線名稱
            output_file: 輸出檔案路徑

        Returns:
            執行結果
        """
        connection_name = kwargs.get("connection_name", "dev")
        output_file = kwargs.get("output_file", "output/db_schema.json")

        # 參數驗證
        valid_connections = ["dev", "test", "prod"]
        if connection_name not in valid_connections:
            return {
                "success": False,
                "error": f"無效的連線名稱: {connection_name}，必須是 {valid_connections} 之一"
            }

        try:
            print(f"提取 Oracle Schema (連線: {connection_name})...", file=sys.stderr)

            result = extract_db_schema_by_config(
                connection_name=connection_name,
                output_file=output_file,
                interactive=True  # 允許互動式輸入密碼
            )

            if result.get("status") == "success":
                return {
                    "success": True,
                    "message": f"✓ Schema 提取完成",
                    "output_file": result.get("output_file"),
                    "statistics": result.get("statistics", {})
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "未知錯誤")
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"提取失敗: {str(e)}"
            }

    async def _handle_analyze_procedure(self, **kwargs) -> Dict[str, Any]:
        """
        處理 analyze_stored_procedure 工具調用

        Args:
            procedure_name: Procedure 名稱（可選）
            analyze_all: 是否分析所有
            output_file: 輸出檔案路徑（可選）

        Returns:
            執行結果
        """
        procedure_name = kwargs.get("procedure_name")
        analyze_all = kwargs.get("analyze_all", False)
        output_file = kwargs.get("output_file")

        try:
            # 使用 asyncio 包裝同步函數
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                analyze_stored_procedures,
                procedure_name,
                analyze_all,
                output_file
            )

            if result.get("status") == "success":
                return {
                    "success": True,
                    "message": "✓ 分析完成",
                    "result": result
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "未知錯誤")
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"分析失敗: {str(e)}"
            }

    async def _handle_analyze_jsp(self, **kwargs) -> Dict[str, Any]:
        """Handle analyze_jsp tool call (Phase 3.1)"""
        jsp_file = kwargs.get("jsp_file")
        output_file = kwargs.get("output_file")
        force_refresh = kwargs.get("force_refresh", False)

        if not jsp_file:
            return {"success": False, "error": "jsp_file is required"}

        try:
            jsp_path = self.project_root / jsp_file
            identifier = jsp_path.stem  # filename without extension

            context = {"file_path": str(jsp_path)}

            result = await self.jsp_analyzer.analyze_async(
                identifier=identifier,
                context=context,
                force_refresh=force_refresh
            )

            # Save to output file if specified
            if output_file:
                output_path = self.project_root / output_file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

            return {
                "success": True,
                "message": f"✓ JSP analysis complete: {jsp_file}",
                "result": result,
                "output_file": output_file
            }

        except Exception as e:
            return {"success": False, "error": f"JSP analysis failed: {str(e)}"}

    async def _handle_analyze_controller(self, **kwargs) -> Dict[str, Any]:
        """Handle analyze_controller tool call (Phase 3.2)"""
        controller_file = kwargs.get("controller_file")
        output_file = kwargs.get("output_file")
        force_refresh = kwargs.get("force_refresh", False)

        if not controller_file:
            return {"success": False, "error": "controller_file is required"}

        try:
            controller_path = self.project_root / controller_file
            identifier = controller_path.stem

            context = {"file_path": str(controller_path)}

            result = await self.controller_analyzer.analyze_async(
                identifier=identifier,
                context=context,
                force_refresh=force_refresh
            )

            if output_file:
                output_path = self.project_root / output_file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

            return {
                "success": True,
                "message": f"✓ Controller analysis complete: {controller_file}",
                "result": result,
                "output_file": output_file
            }

        except Exception as e:
            return {"success": False, "error": f"Controller analysis failed: {str(e)}"}

    async def _handle_analyze_service(self, **kwargs) -> Dict[str, Any]:
        """Handle analyze_service tool call (Phase 3.3)"""
        service_file = kwargs.get("service_file")
        output_file = kwargs.get("output_file")
        force_refresh = kwargs.get("force_refresh", False)

        if not service_file:
            return {"success": False, "error": "service_file is required"}

        try:
            service_path = self.project_root / service_file
            identifier = service_path.stem

            context = {"file_path": str(service_path)}

            result = await self.service_analyzer.analyze_async(
                identifier=identifier,
                context=context,
                force_refresh=force_refresh
            )

            if output_file:
                output_path = self.project_root / output_file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

            return {
                "success": True,
                "message": f"✓ Service analysis complete: {service_file}",
                "result": result,
                "output_file": output_file
            }

        except Exception as e:
            return {"success": False, "error": f"Service analysis failed: {str(e)}"}

    async def _handle_analyze_mybatis(self, **kwargs) -> Dict[str, Any]:
        """Handle analyze_mybatis tool call (Phase 3.4)"""
        interface_file = kwargs.get("interface_file")
        xml_file = kwargs.get("xml_file")
        output_file = kwargs.get("output_file")
        force_refresh = kwargs.get("force_refresh", False)

        if not interface_file:
            return {"success": False, "error": "interface_file is required"}

        try:
            interface_path = self.project_root / interface_file
            identifier = interface_path.stem

            context = {"interface_path": str(interface_path)}
            if xml_file:
                xml_path = self.project_root / xml_file
                context["xml_path"] = str(xml_path)

            result = await self.mybatis_analyzer.analyze_async(
                identifier=identifier,
                context=context,
                force_refresh=force_refresh
            )

            if output_file:
                output_path = self.project_root / output_file
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

            return {
                "success": True,
                "message": f"✓ MyBatis analysis complete: {interface_file}",
                "result": result,
                "output_file": output_file
            }

        except Exception as e:
            return {"success": False, "error": f"MyBatis analysis failed: {str(e)}"}

    async def _handle_find_chain(self, **kwargs) -> Dict[str, Any]:
        """Handle find_chain tool call (Phase 4.4)"""
        start_node = kwargs.get("start_node")
        end_node = kwargs.get("end_node")
        max_depth = kwargs.get("max_depth", QUERY.DEFAULT_MAX_DEPTH_CHAIN)
        project_path = kwargs.get("project_path", str(self.project_root))
        cache_dir = kwargs.get("cache_dir", CACHE.DEFAULT_CACHE_DIR)

        if not start_node:
            return {"success": False, "error": "start_node is required"}

        try:
            from mcp_server.tools.graph_utils import load_or_build_graph
            from mcp_server.tools.query_engine import QueryEngine

            # Load dependency graph
            graph = await load_or_build_graph(project_path, cache_dir)

            # Execute query
            query_engine = QueryEngine(graph)
            chains = query_engine.find_call_chains(
                start_node=start_node,
                end_node=end_node,
                max_depth=max_depth
            )

            # Format result
            if not chains:
                if end_node:
                    message = f"No call chains found from {start_node} to {end_node}"
                else:
                    message = f"No dependencies found for {start_node}"

                return {
                    "success": True,
                    "message": message,
                    "chains": [],
                    "count": 0
                }

            return {
                "success": True,
                "message": f"✓ Found {len(chains)} call chain(s)",
                "chains": [chain.to_dict() for chain in chains],
                "count": len(chains),
                "start_node": start_node,
                "end_node": end_node
            }

        except Exception as e:
            return {"success": False, "error": f"Find chain failed: {str(e)}"}

    async def _handle_impact_analysis(self, **kwargs) -> Dict[str, Any]:
        """Handle impact_analysis tool call (Phase 4.4)"""
        node = kwargs.get("node")
        direction = kwargs.get("direction", "both")
        max_depth = kwargs.get("max_depth", QUERY.DEFAULT_MAX_DEPTH_IMPACT)
        project_path = kwargs.get("project_path", str(self.project_root))
        cache_dir = kwargs.get("cache_dir", CACHE.DEFAULT_CACHE_DIR)

        if not node:
            return {"success": False, "error": "node is required"}

        try:
            from mcp_server.tools.graph_utils import load_or_build_graph
            from mcp_server.tools.query_engine import QueryEngine

            # Load dependency graph
            graph = await load_or_build_graph(project_path, cache_dir)

            # Execute query
            query_engine = QueryEngine(graph)
            result = query_engine.impact_analysis(
                node_id=node,
                direction=direction,
                max_depth=max_depth
            )

            # Handle None result (node not found)
            if result is None:
                return {
                    "success": False,
                    "error": f"Node '{node}' not found in dependency graph"
                }

            # Filter by direction if specified
            if direction == "upstream":
                total = result.total_upstream
            elif direction == "downstream":
                total = result.total_downstream
            else:
                total = result.total_upstream + result.total_downstream

            return {
                "success": True,
                "message": f"✓ Impact analysis complete: {total} affected component(s)",
                "result": result.to_dict(),
                "direction": direction,
                "total_affected": total
            }

        except Exception as e:
            return {"success": False, "error": f"Impact analysis failed: {str(e)}"}

    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理工具調用

        Args:
            tool_name: 工具名稱
            arguments: 參數

        Returns:
            執行結果
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"工具不存在: {tool_name}"
            }

        tool = self.tools[tool_name]
        handler = tool["handler"]

        try:
            result = await handler(**arguments)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"工具執行錯誤: {str(e)}"
            }

    async def handle_command(self, command_line: str) -> Dict[str, Any]:
        """
        Handle slash command execution (Phase 4.2)

        Args:
            command_line: Full command line (e.g., "/analyze-jsp user.jsp --output out.json")

        Returns:
            Command execution result
        """
        self.logger.info(f"Command received: {command_line}")

        # Parse command line with proper quote handling
        try:
            parts = shlex.split(command_line.strip())
        except ValueError as e:
            error_msg = f"Invalid command syntax: {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

        if not parts or not parts[0].startswith('/'):
            error_msg = "Invalid command format. Commands must start with '/'"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

        command_name = parts[0][1:]  # Remove leading '/'
        args = parts[1:]  # Remaining arguments

        if command_name not in self.commands:
            error_msg = f"Unknown command: /{command_name}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

        command = self.commands[command_name]
        handler = command["handler"]

        try:
            result = await handler.execute(args)

            if result.get('success'):
                self.logger.info(f"Command succeeded: /{command_name}")
            else:
                self.logger.error(f"Command failed: {result.get('error')}")

            return result
        except Exception as e:
            error_msg = f"Command execution error: {str(e)}"
            self.logger.exception(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
            for tool in self.tools.values()
        ]

    def list_commands(self) -> List[Dict[str, Any]]:
        """
        List all available slash commands

        Returns:
            List of command definitions with name and description
        """
        # Deduplicate commands (remove aliases)
        seen = set()
        commands = []

        for cmd_name, cmd in self.commands.items():
            handler = cmd["handler"]
            # Use handler object id to detect duplicates (aliases)
            handler_id = id(handler)

            if handler_id not in seen:
                seen.add(handler_id)
                # Find all aliases for this command
                aliases = [name for name, c in self.commands.items() if id(c["handler"]) == handler_id]

                commands.append({
                    "name": f"/{cmd['name']}",
                    "description": cmd["description"],
                    "aliases": [f"/{alias}" for alias in aliases if alias != cmd_name]
                })

        return sorted(commands, key=lambda x: x['name'])

    def run(self):
        """
        啟動 MCP Server

        Phase 2: 基本骨架
        Phase 3+: 完整 MCP Protocol 實作
        """
        print(f"{self.name} v{self.version} - MCP Server", file=sys.stderr)
        print(f"✓ 已註冊工具: {len(self.tools)}", file=sys.stderr)
        print(f"✓ 已註冊命令: {len(self.commands)}", file=sys.stderr)

        if MCP_AVAILABLE:
            print("✓ MCP SDK 可用", file=sys.stderr)
        else:
            print("⚠️  MCP SDK 部分功能不可用（開發模式）", file=sys.stderr)

        # Phase 2: 輸出工具列表供測試
        print("\n可用工具:", file=sys.stderr)
        for tool in self.list_tools():
            print(f"  - {tool['name']}: {tool['description']}", file=sys.stderr)

        # Phase 3 將實作完整的 MCP Protocol stdio 通訊
        # 目前返回成功狀態
        return 0


def main():
    """主入口"""
    server = SpringMVCMCPServer()

    # 未來 Phase 3 將在此加入更多工具:
    # - analyze_jsp
    # - analyze_controller
    # - analyze_service
    # - analyze_mybatis
    # - build_knowledge_graph
    # - query_knowledge_graph

    # 未來 Phase 4 將在此註冊所有 slash commands:
    # - /extract-oracle-schema
    # - /analyze-procedure
    # - /build-graph
    # - /query-path
    # etc.

    return server.run()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n中斷執行", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n錯誤: {e}", file=sys.stderr)
        sys.exit(1)
