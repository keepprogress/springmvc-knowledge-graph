#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Tool - MCP 工具基礎類別

提供所有分析工具的共用功能：
- Claude Agent SDK 整合
- 檔案讀寫管理
- 錯誤處理
- 結果快取
"""

import asyncio
import io
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from claude_agent_sdk import ClaudeAgentOptions, query

try:
    from json_repair import repair_json
    JSON_REPAIR_AVAILABLE = True
except ImportError:
    JSON_REPAIR_AVAILABLE = False

# Windows console encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except AttributeError:
        pass  # Already wrapped or not needed


class BaseTool:
    """MCP 工具基礎類別"""

    def __init__(
        self,
        tool_name: str,
        output_dir: str = "output/analysis",
        prompt_template_file: Optional[str] = None,
        cache_expiration_days: int = 7
    ):
        """
        初始化

        Args:
            tool_name: 工具名稱（用於輸出目錄）
            output_dir: 輸出根目錄
            prompt_template_file: Prompt 模板檔案名稱（在 prompts/ 目錄下）
            cache_expiration_days: 快取過期天數（預設 7 天）
        """
        self.tool_name = tool_name
        self.output_dir = Path(output_dir) / tool_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_expiration_days = cache_expiration_days

        # 載入 Prompt 模板
        self.prompt_template = None
        if prompt_template_file:
            self.prompt_template = self._load_prompt_template(prompt_template_file)

    def _load_prompt_template(self, template_name: str) -> str:
        """載入 Prompt 模板"""
        prompt_file = Path(__file__).parent.parent / "prompts" / template_name

        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt 模板不存在: {prompt_file}")

        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()

    def _get_cache_path(self, identifier: str) -> Path:
        """取得快取檔案路徑"""
        # 清理檔案名稱（移除不合法字元）
        safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in identifier)
        return self.output_dir / f"{safe_name}.json"

    def _load_cache(self, identifier: str) -> Optional[Dict[str, Any]]:
        """載入快取結果"""
        cache_path = self._get_cache_path(identifier)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # 檢查快取是否過期
                if "cached_at" in data:
                    try:
                        cached_time = datetime.fromisoformat(data["cached_at"])
                        expiration_time = cached_time + timedelta(days=self.cache_expiration_days)

                        if datetime.now() > expiration_time:
                            print(f"⚠️  快取已過期: {identifier} (已存在 {(datetime.now() - cached_time).days} 天)")
                            return None
                    except (ValueError, TypeError) as e:
                        print(f"⚠️  無法解析快取時間: {e}")
                        # 繼續使用快取，但不進行過期檢查

                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  無法載入快取 {cache_path}: {e}")
            return None

    def _save_cache(self, identifier: str, data: Dict[str, Any]) -> Path:
        """儲存快取結果"""
        cache_path = self._get_cache_path(identifier)

        # 加入時間戳
        if isinstance(data, dict) and "cached_at" not in data:
            data["cached_at"] = datetime.now().isoformat()

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return cache_path

    def _save_result(self, filename: str, data: Dict[str, Any]) -> Path:
        """儲存分析結果"""
        output_path = self.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_path

    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """載入 JSON 檔案"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"檔案不存在: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def _query_claude(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_turns: int = 1,
        allowed_tools: Optional[List[str]] = None
    ) -> str:
        """
        查詢 Claude Agent SDK

        Args:
            prompt: 使用者提示
            system_prompt: 系統提示
            max_turns: 最大輪次
            allowed_tools: 允許使用的工具列表

        Returns:
            Claude 的回應文字
        """
        if system_prompt is None:
            system_prompt = f"你是 {self.tool_name} 分析專家"

        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            max_turns=max_turns,
            allowed_tools=allowed_tools or []
        )

        response_text = ""

        try:
            async for message in query(prompt=prompt, options=options):
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            response_text += block.text
        except Exception as e:
            raise RuntimeError(f"Claude API 調用失敗: {e}")

        if not response_text:
            raise RuntimeError("Claude 未返回任何回應")

        return response_text

    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        從 Claude 回應中提取 JSON

        支援多種格式：
        1. Markdown code block: ```json ... ```
        2. 多個 JSON code blocks（取最後一個）
        3. 純 JSON
        4. 使用 json-repair 修復不完整的 JSON
        """
        json_text = None

        # 1. 嘗試提取所有 Markdown code blocks
        json_blocks = re.findall(r'```json\s*(.*?)```', response, re.DOTALL)

        if json_blocks:
            # 使用最後一個 JSON block（通常最完整）
            json_text = json_blocks[-1].strip()
        else:
            # 2. 嘗試直接解析整個回應
            json_text = response.strip()

        if not json_text:
            print("⚠️  無法從回應中提取 JSON")
            return None

        # 3. 嘗試標準 JSON 解析
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            # 4. 使用 json-repair 嘗試修復
            if JSON_REPAIR_AVAILABLE:
                try:
                    print(f"⚠️  標準 JSON 解析失敗，嘗試使用 json-repair 修復...")
                    repaired = repair_json(json_text, return_objects=True)
                    if isinstance(repaired, dict):
                        print("✓ JSON 修復成功")
                        return repaired
                    else:
                        print(f"⚠️  json-repair 返回非字典類型: {type(repaired)}")
                        return None
                except Exception as repair_error:
                    print(f"⚠️  json-repair 修復失敗: {repair_error}")
            else:
                print("⚠️  json-repair 未安裝，無法修復 JSON")

            print(f"⚠️  JSON 解析失敗: {e}")
            print(f"   原始 JSON 前 200 字元: {json_text[:200]}...")
            return None

    async def analyze_async(
        self,
        identifier: str,
        context: Dict[str, Any],
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        執行非同步分析（子類別應覆寫此方法）

        Args:
            identifier: 分析對象識別碼
            context: 分析所需的上下文資料
            force_refresh: 是否強制重新分析（忽略快取）

        Returns:
            分析結果
        """
        raise NotImplementedError("子類別必須實作 analyze_async 方法")

    def analyze(
        self,
        identifier: str,
        context: Dict[str, Any],
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        執行同步分析（包裝 analyze_async）

        Args:
            identifier: 分析對象識別碼
            context: 分析所需的上下文資料
            force_refresh: 是否強制重新分析（忽略快取）

        Returns:
            分析結果
        """
        return asyncio.run(self.analyze_async(identifier, context, force_refresh))

    def batch_analyze(
        self,
        targets: List[Dict[str, Any]],
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        批次分析（子類別可選擇性覆寫）

        Args:
            targets: 分析對象列表 [{"identifier": "...", "context": {...}}, ...]
            force_refresh: 是否強制重新分析

        Returns:
            批次分析結果摘要
        """
        total = len(targets)
        results = []

        print(f"開始批次分析 {total} 個目標...")

        for i, target in enumerate(targets, 1):
            identifier = target["identifier"]
            context = target.get("context", {})

            print(f"[{i}/{total}] 分析: {identifier}")

            try:
                result = self.analyze(identifier, context, force_refresh)
                results.append({
                    "identifier": identifier,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                print(f"  ✗ 錯誤: {e}")
                results.append({
                    "identifier": identifier,
                    "status": "error",
                    "error": str(e)
                })

        # 儲存批次分析摘要
        summary_file = self._save_result("_batch_summary.json", {
            "tool_name": self.tool_name,
            "total": total,
            "successful": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "error"),
            "timestamp": datetime.now().isoformat(),
            "results": results
        })

        print(f"\n✓ 批次分析完成！摘要: {summary_file}")

        return {
            "status": "success",
            "total": total,
            "summary_file": str(summary_file),
            "results": results
        }

    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        取得所有已分析結果的摘要

        Returns:
            摘要資訊
        """
        json_files = list(self.output_dir.glob("*.json"))
        json_files = [f for f in json_files if not f.name.startswith("_")]

        return {
            "tool_name": self.tool_name,
            "output_dir": str(self.output_dir),
            "total_analyses": len(json_files),
            "files": [f.name for f in sorted(json_files)]
        }


# 測試用範例工具
class ExampleTool(BaseTool):
    """範例工具（僅供測試 BaseTool 功能）"""

    def __init__(self):
        super().__init__(
            tool_name="example",
            prompt_template_file=None  # 可以指定 prompt 檔案
        )

    async def analyze_async(
        self,
        identifier: str,
        context: Dict[str, Any],
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """範例分析方法"""

        # 檢查快取
        if not force_refresh:
            cached = self._load_cache(identifier)
            if cached:
                print(f"✓ 使用快取結果: {identifier}")
                return cached

        # 模擬分析
        print(f"🔍 分析: {identifier}")

        # 如果有 Prompt 模板，使用 Claude 分析
        if self.prompt_template and context:
            try:
                prompt = self.prompt_template.format(**context)
                response = await self._query_claude(
                    prompt=prompt,
                    system_prompt="你是程式碼分析專家"
                )
                analysis = self._extract_json_from_response(response)

                if not analysis:
                    # 回退到簡單分析
                    analysis = {
                        "identifier": identifier,
                        "context_keys": list(context.keys()),
                        "note": "JSON 解析失敗，返回基本資訊"
                    }
            except Exception as e:
                print(f"⚠️  Claude 分析失敗: {e}")
                analysis = {
                    "identifier": identifier,
                    "error": str(e),
                    "context_keys": list(context.keys())
                }
        else:
            # 無 Prompt 模板時的簡單分析
            analysis = {
                "identifier": identifier,
                "context_keys": list(context.keys()),
                "timestamp": datetime.now().isoformat()
            }

        # 儲存快取
        self._save_cache(identifier, analysis)

        return analysis


if __name__ == "__main__":
    # 測試範例
    print("=== BaseTool 測試 ===\n")

    tool = ExampleTool()

    # 單個分析
    print("1. 測試單個分析:")
    result = tool.analyze(
        identifier="test_item",
        context={"key": "value", "data": "test"}
    )
    print(f"   結果: {result}\n")

    # 再次分析（測試快取）
    print("2. 測試快取機制:")
    result2 = tool.analyze(
        identifier="test_item",
        context={"key": "value"}
    )
    print(f"   結果: {result2}\n")

    # 批次分析
    print("3. 測試批次分析:")
    batch_result = tool.batch_analyze([
        {"identifier": "item1", "context": {"data": "a"}},
        {"identifier": "item2", "context": {"data": "b"}},
        {"identifier": "item3", "context": {"data": "c"}},
    ])
    print(f"   成功: {batch_result['total']} 個\n")

    # 取得摘要
    print("4. 測試分析摘要:")
    summary = tool.get_analysis_summary()
    print(f"   總數: {summary['total_analyses']}")
    print(f"   檔案: {summary['files']}")
