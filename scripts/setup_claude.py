#!/usr/bin/env python3
"""自動配置 Claude Code 的 MCP Server"""

import json
from pathlib import Path
import shutil
import sys
import subprocess

def setup_claude_code():
    """配置 Claude Code settings.json"""

    print("=== SpringMVC Analyzer - Claude Code 設定 ===\n")

    # 找到 settings.json
    settings_path = Path.home() / ".claude_code" / "settings.json"

    if not settings_path.exists():
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings = {}
        print(f"建立新的 settings.json")
    else:
        with open(settings_path, 'r', encoding='utf-8') as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                print("⚠️  settings.json 格式錯誤，建立新的設定")
                settings = {}

    # 加入 MCP Server 配置
    if "mcpServers" not in settings:
        settings["mcpServers"] = {}

    project_root = Path(__file__).parent.parent.absolute()
    server_path = project_root / "mcp_server" / "springmvc_mcp_server.py"

    settings["mcpServers"]["springmvc-analyzer"] = {
        "type": "stdio",
        "command": sys.executable,  # 使用當前 Python 解釋器
        "args": [str(server_path)]
    }

    # 備份原始設定
    if settings_path.exists():
        backup = settings_path.with_suffix('.json.backup')
        shutil.copy(settings_path, backup)
        print(f"✓ 已備份原始設定到: {backup}")

    # 寫入新設定
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    print(f"✓ Claude Code 已配置")
    print(f"  MCP Server: {server_path}")
    print(f"  Settings: {settings_path}")
    print(f"  Python: {sys.executable}")

    # 測試連線
    print("\n測試 MCP Server 連線...")
    test_connection(server_path)

def test_connection(server_path):
    """測試 MCP Server 是否正常運行"""

    try:
        # 簡單測試：檢查檔案是否存在且可讀取
        if not server_path.exists():
            print(f"✗ MCP Server 檔案不存在: {server_path}")
            return False

        # 測試 Python 語法
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(server_path)],
            capture_output=True,
            timeout=5
        )

        if result.returncode == 0:
            print("✓ MCP Server 檔案語法正確")
        else:
            print("✗ MCP Server 檔案有語法錯誤")
            print(result.stderr.decode())
            return False

        # 檢查依賴
        print("\n檢查依賴套件...")
        required_packages = [
            "claude_agent_sdk",
            "mcp",
            "oracledb",
            "networkx",
        ]

        missing = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"  ✓ {package}")
            except ImportError:
                print(f"  ✗ {package} (缺少)")
                missing.append(package)

        if missing:
            print(f"\n⚠️  缺少以下套件，請執行: pip install {' '.join(missing)}")
            return False

        print("\n✓ 所有檢查通過")
        return True

    except Exception as e:
        print(f"✗ 測試錯誤: {e}")
        return False

def main():
    """主函數"""
    setup_claude_code()

    print("\n" + "="*50)
    print("完成！請在 Claude Code 中測試：")
    print("  輸入: 請使用 springmvc-analyzer 工具")
    print("="*50)

if __name__ == "__main__":
    main()
