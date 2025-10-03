#!/usr/bin/env python3
"""測試 MCP Server 連線與工具可用性"""

import sys
from pathlib import Path
import subprocess

def test_mcp_server():
    """測試 MCP Server"""

    print("=== MCP Server 測試 ===\n")

    project_root = Path(__file__).parent.parent
    server_path = project_root / "mcp_server" / "springmvc_mcp_server.py"

    # 1. 檢查檔案存在
    print("1. 檢查 MCP Server 檔案...")
    if not server_path.exists():
        print(f"   ✗ 檔案不存在: {server_path}")
        return False
    print(f"   ✓ 檔案存在: {server_path}")

    # 2. 檢查 Python 語法
    print("\n2. 檢查 Python 語法...")
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(server_path)],
        capture_output=True
    )
    if result.returncode != 0:
        print("   ✗ 語法錯誤:")
        print(result.stderr.decode())
        return False
    print("   ✓ 語法正確")

    # 3. 檢查依賴套件
    print("\n3. 檢查依賴套件...")
    packages = {
        "claude_agent_sdk": "Claude Agent SDK",
        "mcp": "MCP Protocol",
        "oracledb": "Oracle Database Driver",
        "networkx": "NetworkX (圖譜處理)",
        "yaml": "PyYAML",
        "click": "Click (CLI)",
        "rich": "Rich (CLI 美化)",
    }

    all_ok = True
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"   ✓ {name}")
        except ImportError:
            print(f"   ✗ {name} - 請執行: pip install {package}")
            all_ok = False

    if not all_ok:
        print("\n請先安裝缺少的套件: pip install -r requirements.txt")
        return False

    # 4. 檢查工具檔案
    print("\n4. 檢查 MCP 工具檔案...")
    tools_dir = project_root / "mcp_server" / "tools"
    expected_tools = [
        "base_tool.py",
        "jsp_analyzer.py",
        "controller_analyzer.py",
        "service_analyzer.py",
        "mybatis_analyzer.py",
        "sql_analyzer.py",
        "graph_builder.py",
        "graph_query.py",
        "db_extractor.py",
    ]

    for tool in expected_tools:
        tool_path = tools_dir / tool
        if tool_path.exists():
            print(f"   ✓ {tool}")
        else:
            print(f"   - {tool} (尚未實作)")

    # 5. 檢查 Prompt 模板
    print("\n5. 檢查 Prompt 模板...")
    prompts_dir = project_root / "mcp_server" / "prompts"
    expected_prompts = [
        "jsp_analysis.txt",
        "controller_analysis.txt",
        "service_analysis.txt",
        "mybatis_analysis.txt",
        "sql_analysis.txt",
    ]

    for prompt in expected_prompts:
        prompt_path = prompts_dir / prompt
        if prompt_path.exists():
            print(f"   ✓ {prompt}")
        else:
            print(f"   - {prompt} (尚未建立)")

    # 6. 檢查輸出目錄
    print("\n6. 檢查輸出目錄...")
    output_dir = project_root / "output"
    if output_dir.exists():
        print(f"   ✓ 輸出目錄: {output_dir}")
    else:
        print(f"   ! 輸出目錄不存在，將自動建立")
        output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*50)
    print("✓ 測試完成！")
    print("="*50)

    return True

def main():
    """主函數"""
    success = test_mcp_server()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
