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
    print("⚠️  MCP SDK not fully available, running in stub mode", file=sys.stderr)
    MCP_AVAILABLE = False

# Import analysis tools
from mcp_server.tools.db_extractor import extract_db_schema_by_config, extract_oracle_schema
from mcp_server.tools.procedure_analyzer import analyze_stored_procedures


class SpringMVCMCPServer:
    """SpringMVC Knowledge Graph MCP Server"""

    def __init__(self):
        self.name = "springmvc-analyzer"
        self.version = "0.2.0-alpha"  # Phase 2
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.commands: Dict[str, Dict[str, Any]] = {}

        # Initialize tool registry
        self._register_tools()

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

        print(f"✓ 已註冊 {len(self.tools)} 個 MCP Tools", file=sys.stderr)

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
