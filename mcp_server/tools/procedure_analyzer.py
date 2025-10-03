#!/usr/bin/env python3
"""
Stored Procedure 分析工具

使用 Claude Agent SDK 分析 Oracle Procedure 的業務用途、風險與優化建議
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from claude_agent_sdk import query, ClaudeAgentOptions


class ProcedureAnalyzer:
    """Procedure 分析器"""

    def __init__(self, db_schema_file: str = "output/db_schema.json"):
        """
        初始化

        Args:
            db_schema_file: 資料庫 Schema 檔案路徑
        """
        self.db_schema_file = Path(db_schema_file)
        self.db_schema = self._load_db_schema()
        self.prompt_template = self._load_prompt_template()

    def _load_db_schema(self) -> Dict[str, Any]:
        """載入資料庫 Schema"""
        if not self.db_schema_file.exists():
            raise FileNotFoundError(
                f"資料庫 Schema 檔案不存在: {self.db_schema_file}\n"
                f"請先執行: python scripts/extract_oracle_schema.py"
            )

        with open(self.db_schema_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_prompt_template(self) -> str:
        """載入 Prompt 模板"""
        prompt_file = Path(__file__).parent.parent / "prompts" / "procedure_analysis.txt"

        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt 模板不存在: {prompt_file}")

        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()

    def _get_procedure_info(self, procedure_name: str) -> Optional[Dict[str, Any]]:
        """取得 Procedure 資訊"""
        for proc in self.db_schema.get("procedures_and_functions", []):
            if proc["name"] == procedure_name or proc["full_name"] == procedure_name:
                return proc
        return None

    def _find_trigger_callers(self, procedure_name: str) -> List[Dict[str, Any]]:
        """查找調用此 Procedure 的 Trigger"""
        callers = []

        for table in self.db_schema.get("tables", []):
            for trigger in table.get("triggers", []):
                # 簡單檢查 Trigger 描述中是否包含 Procedure 名稱
                # 實際應該解析 Trigger 程式碼，但這裡簡化處理
                if procedure_name.upper() in trigger.get("description", "").upper():
                    callers.append({
                        "type": "TRIGGER",
                        "name": trigger["name"],
                        "table": table["name"],
                        "event": trigger["event"]
                    })

        return callers

    def _find_oracle_jobs(self, procedure_name: str) -> List[Dict[str, Any]]:
        """
        查找調用此 Procedure 的 Oracle Scheduler Jobs

        從 db_schema.json 的 oracle_jobs 欄位中查找
        """
        jobs = []

        for job in self.db_schema.get("oracle_jobs", []):
            # 檢查 Job 是否調用此 Procedure
            calls_procedure = job.get("calls_procedure")
            if calls_procedure and calls_procedure.upper() == procedure_name.upper():
                jobs.append({
                    "name": job["name"],
                    "type": job["type"],
                    "job_action": job.get("job_action", ""),
                    "enabled": job.get("enabled", job.get("broken") is not True),
                    "repeat_interval": job.get("repeat_interval") or job.get("interval")
                })

        return jobs

    def _find_mybatis_callers(self, procedure_name: str) -> List[Dict[str, Any]]:
        """
        查找調用此 Procedure 的 MyBatis Mapper

        需要讀取 mybatis_analysis.json（由 mybatis_analyzer 生成）
        """
        mybatis_file = Path("output/analysis/mybatis_analysis.json")

        if not mybatis_file.exists():
            return []

        with open(mybatis_file, 'r', encoding='utf-8') as f:
            mybatis_data = json.load(f)

        callers = []
        for mapper in mybatis_data.get("mappers", []):
            for statement in mapper.get("statements", []):
                # 檢查是否為 CALLABLE 且包含此 Procedure
                if statement.get("type") == "CALLABLE":
                    sql = statement.get("sql", "").upper()
                    if procedure_name.upper() in sql:
                        callers.append({
                            "type": "MYBATIS",
                            "mapper": mapper["interface"],
                            "method": statement["id"],
                            "sql": statement["sql"]
                        })

        return callers

    def _load_existing_batch_jobs(self) -> List[Dict[str, Any]]:
        """
        載入已知的 Batch Jobs

        可以從：
        1. Java 專案掃描結果（Phase 3 實作）
        2. 配置檔
        3. 文檔

        目前返回空列表，將在 Phase 3 實作 Java 專案掃描後完成
        """
        return []

    def analyze_procedure(
        self,
        procedure_name: str,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析單個 Procedure

        Args:
            procedure_name: Procedure 名稱
            output_file: 輸出檔案路徑（可選）

        Returns:
            分析結果 JSON
        """
        # 取得 Procedure 資訊
        proc_info = self._get_procedure_info(procedure_name)

        if not proc_info:
            return {
                "status": "error",
                "error": f"找不到 Procedure: {procedure_name}"
            }

        # 收集上下文資訊
        trigger_callers = self._find_trigger_callers(procedure_name)
        oracle_jobs = self._find_oracle_jobs(procedure_name)
        mybatis_callers = self._find_mybatis_callers(procedure_name)
        existing_batch_jobs = self._load_existing_batch_jobs()

        # 格式化參數
        params_str = "\n".join([
            f"  - {p['name']}: {p['data_type']} ({p['direction']})"
            for p in proc_info.get("parameters", [])
        ]) or "  無參數"

        # 組合 known_callers
        known_callers = []
        if trigger_callers:
            known_callers.append(f"Triggers: {[t['name'] for t in trigger_callers]}")
        if oracle_jobs:
            known_callers.append(f"Oracle Jobs: {[j['name'] for j in oracle_jobs]}")
        if mybatis_callers:
            known_callers.append(f"MyBatis Mappers: {[m['mapper'] for m in mybatis_callers]}")

        known_callers_str = "\n".join(known_callers) if known_callers else "尚未發現調用者"

        # 處理 source_code 長度
        source_code = proc_info.get("source_code", "")
        max_source_length = 10000
        if len(source_code) > max_source_length:
            print(f"⚠️  警告: {procedure_name} 程式碼過長 ({len(source_code)} 字元)，已截斷至 {max_source_length} 字元")
            source_code = source_code[:max_source_length] + "\n\n... (程式碼已截斷)"

        # 填充 Prompt 模板
        prompt = self.prompt_template.format(
            procedure_name=proc_info["name"],
            procedure_type=proc_info["type"],
            package_name=proc_info.get("package_name") or "獨立 Procedure",
            status=proc_info["status"],
            created=proc_info.get("created") or "未知",
            last_modified=proc_info.get("last_modified") or "未知",
            parameters=params_str,
            source_code=source_code,
            dependent_tables=", ".join(proc_info.get("dependencies", {}).get("tables", [])) or "無",
            dependent_views=", ".join(proc_info.get("dependencies", {}).get("views", [])) or "無",
            dependent_sequences=", ".join(proc_info.get("dependencies", {}).get("sequences", [])) or "無",
            dependent_procedures=", ".join(proc_info.get("dependencies", {}).get("procedures", [])) or "無",
            known_callers=known_callers_str,
            trigger_info=json.dumps(trigger_callers, indent=2, ensure_ascii=False) if trigger_callers else "無 Trigger 調用",
            oracle_jobs=json.dumps(oracle_jobs, indent=2, ensure_ascii=False) if oracle_jobs else "無 Oracle Job",
            mybatis_callers=json.dumps(mybatis_callers, indent=2, ensure_ascii=False) if mybatis_callers else "無 MyBatis 調用",
            existing_batch_jobs=json.dumps(existing_batch_jobs, indent=2, ensure_ascii=False) if existing_batch_jobs else "無已知 Batch Jobs"
        )

        # 使用 Claude Agent SDK 分析
        print(f"分析 Procedure: {procedure_name}...")

        try:
            options = ClaudeAgentOptions(
                system_prompt="你是 Oracle Stored Procedure 分析專家",
                max_turns=1,
                allowed_tools=[]  # 純分析，不需要工具
            )

            analysis_result = None

            async def run_analysis():
                nonlocal analysis_result
                try:
                    async for message in query(prompt=prompt, options=options):
                        if hasattr(message, 'content'):
                            for block in message.content:
                                if hasattr(block, 'text'):
                                    # 嘗試解析 JSON
                                    text = block.text
                                    # 提取 JSON（可能包含在 markdown 中）
                                    if "```json" in text:
                                        json_start = text.find("```json") + 7
                                        json_end = text.find("```", json_start)
                                        json_text = text[json_start:json_end].strip()
                                    else:
                                        json_text = text

                                    try:
                                        analysis_result = json.loads(json_text)
                                    except json.JSONDecodeError as e:
                                        print(f"⚠️  JSON 解析失敗: {e}")
                                        analysis_result = {
                                            "status": "partial_success",
                                            "error": f"JSON 解析失敗: {str(e)}",
                                            "raw_response": text[:1000]  # 只保留前 1000 字元
                                        }
                except Exception as e:
                    print(f"✗ Claude API 調用失敗: {e}")
                    analysis_result = {
                        "status": "error",
                        "error": f"Claude API 調用失敗: {str(e)}"
                    }

            import asyncio
            asyncio.run(run_analysis())

            if analysis_result is None:
                return {
                    "status": "error",
                    "error": "Claude 未返回任何回應"
                }

        except Exception as e:
            print(f"✗ 分析過程發生錯誤: {e}")
            return {
                "status": "error",
                "error": f"分析過程發生錯誤: {str(e)}"
            }

        # 儲存結果
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "procedure_name": procedure_name,
            "analysis": analysis_result,
            "output_file": str(output_path) if output_file else None
        }

    def analyze_all_procedures(
        self,
        output_dir: str = "output/analysis/procedures"
    ) -> Dict[str, Any]:
        """
        分析所有 Procedure

        Args:
            output_dir: 輸出目錄

        Returns:
            分析結果摘要
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        procedures = self.db_schema.get("procedures_and_functions", [])
        total = len(procedures)

        print(f"開始分析 {total} 個 Procedure/Function...")

        results = []

        for i, proc in enumerate(procedures, 1):
            proc_name = proc["name"]
            print(f"[{i}/{total}] 分析: {proc_name}")

            output_file = output_path / f"{proc_name}.json"

            result = self.analyze_procedure(proc_name, str(output_file))
            results.append({
                "name": proc_name,
                "status": result["status"],
                "output_file": result.get("output_file")
            })

        # 儲存摘要
        summary_file = output_path / "_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_analyzed": total,
                "results": results
            }, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "total_analyzed": total,
            "output_dir": str(output_path),
            "summary_file": str(summary_file)
        }


# MCP Tool 註冊（將在 MCP Server 中使用）
async def analyze_stored_procedures(
    procedure_name: Optional[str] = None,
    analyze_all: bool = False,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    分析 Stored Procedure（MCP Tool）

    Args:
        procedure_name: Procedure 名稱（分析單個）
        analyze_all: 是否分析所有 Procedure
        output_file: 輸出檔案路徑

    Returns:
        分析結果
    """
    try:
        analyzer = ProcedureAnalyzer()

        if analyze_all:
            return analyzer.analyze_all_procedures()
        elif procedure_name:
            return analyzer.analyze_procedure(procedure_name, output_file)
        else:
            return {
                "status": "error",
                "error": "請指定 procedure_name 或設定 analyze_all=True"
            }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("使用方式:")
        print("  python procedure_analyzer.py <procedure_name>")
        print("  python procedure_analyzer.py --all")
        sys.exit(1)

    if sys.argv[1] == "--all":
        analyzer = ProcedureAnalyzer()
        result = analyzer.analyze_all_procedures()
    else:
        procedure_name = sys.argv[1]
        analyzer = ProcedureAnalyzer()
        result = analyzer.analyze_procedure(procedure_name)

    if result["status"] == "success":
        print("\n✓ 分析完成！")
        if "output_file" in result and result["output_file"]:
            print(f"  輸出: {result['output_file']}")
    else:
        print(f"\n✗ 錯誤: {result['error']}")
