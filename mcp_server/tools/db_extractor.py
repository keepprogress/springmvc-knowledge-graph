#!/usr/bin/env python3
"""Oracle 資料庫 Schema 提取工具（純 Python，不經過 LLM）"""

import oracledb
import json
import os
import yaml
import getpass
from pathlib import Path
from typing import Dict, List, Any, Optional


class OracleSchemaExtractor:
    """Oracle Schema 提取器"""

    def __init__(self, user: str, password: str, dsn: str):
        """
        初始化

        Args:
            user: 資料庫使用者
            password: 密碼
            dsn: 連線字串，格式: "host:port/service_name"
        """
        self.user = user
        self.password = password
        self.dsn = dsn
        self.connection = None

    def connect(self):
        """建立資料庫連線"""
        try:
            self.connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            )
            return True
        except Exception as e:
            raise ConnectionError(f"無法連線到 Oracle: {e}")

    def disconnect(self):
        """關閉連線"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def extract_tables(self) -> List[Dict[str, Any]]:
        """提取所有表資訊"""
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT table_name, tablespace_name, num_rows
            FROM user_tables
            ORDER BY table_name
        """)

        tables = []
        for row in cursor.fetchall():
            table_name = row[0]

            table_info = {
                "name": table_name,
                "type": "TABLE",
                "tablespace": row[1],
                "num_rows": row[2],
                "columns": self._extract_columns(table_name),
                "primary_key": self._extract_primary_key(table_name),
                "indexes": self._extract_indexes(table_name),
                "foreign_keys": self._extract_foreign_keys(table_name),
                "triggers": self._extract_triggers(table_name),
            }

            tables.append(table_info)

        cursor.close()
        return tables

    def _extract_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """提取表的欄位資訊"""
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                column_name,
                data_type,
                data_length,
                data_precision,
                data_scale,
                nullable,
                data_default,
                column_id
            FROM user_tab_columns
            WHERE table_name = :table_name
            ORDER BY column_id
        """, {"table_name": table_name})

        columns = []
        for row in cursor.fetchall():
            data_type = row[1]
            if data_type in ('VARCHAR2', 'CHAR', 'NVARCHAR2', 'NCHAR'):
                full_type = f"{data_type}({row[2]})"
            elif data_type == 'NUMBER':
                if row[3] is not None:
                    if row[4] is not None and row[4] > 0:
                        full_type = f"NUMBER({row[3]},{row[4]})"
                    else:
                        full_type = f"NUMBER({row[3]})"
                else:
                    full_type = "NUMBER"
            else:
                full_type = data_type

            columns.append({
                "name": row[0],
                "data_type": row[1],
                "full_type": full_type,
                "max_length": row[2],
                "precision": row[3],
                "scale": row[4],
                "nullable": row[5] == 'Y',
                "default_value": row[6].strip() if row[6] else None,
                "position": row[7],
            })

        cursor.close()
        return columns

    def _extract_primary_key(self, table_name: str) -> Optional[Dict[str, Any]]:
        """提取主鍵資訊"""
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT constraint_name
            FROM user_constraints
            WHERE table_name = :table_name
              AND constraint_type = 'P'
        """, {"table_name": table_name})

        row = cursor.fetchone()
        if not row:
            cursor.close()
            return None

        constraint_name = row[0]

        cursor.execute("""
            SELECT column_name, position
            FROM user_cons_columns
            WHERE constraint_name = :constraint_name
            ORDER BY position
        """, {"constraint_name": constraint_name})

        columns = [row[0] for row in cursor.fetchall()]

        cursor.close()
        return {
            "constraint_name": constraint_name,
            "columns": columns
        }

    def _extract_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """提取索引資訊"""
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                index_name,
                index_type,
                uniqueness,
                tablespace_name
            FROM user_indexes
            WHERE table_name = :table_name
            ORDER BY index_name
        """, {"table_name": table_name})

        indexes = []
        for row in cursor.fetchall():
            index_name = row[0]

            cursor2 = self.connection.cursor()
            cursor2.execute("""
                SELECT column_name, column_position, descend
                FROM user_ind_columns
                WHERE index_name = :index_name
                ORDER BY column_position
            """, {"index_name": index_name})

            columns = [
                {
                    "name": col_row[0],
                    "position": col_row[1],
                    "descend": col_row[2] == 'DESC'
                }
                for col_row in cursor2.fetchall()
            ]
            cursor2.close()

            indexes.append({
                "name": index_name,
                "type": row[1],
                "unique": row[2] == 'UNIQUE',
                "tablespace": row[3],
                "columns": columns
            })

        cursor.close()
        return indexes

    def _extract_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        """提取外鍵關係"""
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                c.constraint_name,
                c.r_constraint_name,
                c.delete_rule,
                (SELECT table_name FROM user_constraints WHERE constraint_name = c.r_constraint_name) AS ref_table
            FROM user_constraints c
            WHERE c.table_name = :table_name
              AND c.constraint_type = 'R'
        """, {"table_name": table_name})

        foreign_keys = []
        for row in cursor.fetchall():
            constraint_name = row[0]
            ref_constraint_name = row[1]
            delete_rule = row[2]
            ref_table = row[3]

            cursor2 = self.connection.cursor()
            cursor2.execute("""
                SELECT column_name, position
                FROM user_cons_columns
                WHERE constraint_name = :constraint_name
                ORDER BY position
            """, {"constraint_name": constraint_name})

            columns = [col_row[0] for col_row in cursor2.fetchall()]

            cursor2.execute("""
                SELECT column_name, position
                FROM user_cons_columns
                WHERE constraint_name = :ref_constraint_name
                ORDER BY position
            """, {"ref_constraint_name": ref_constraint_name})

            ref_columns = [col_row[0] for col_row in cursor2.fetchall()]
            cursor2.close()

            foreign_keys.append({
                "constraint_name": constraint_name,
                "columns": columns,
                "referenced_table": ref_table,
                "referenced_columns": ref_columns,
                "delete_rule": delete_rule
            })

        cursor.close()
        return foreign_keys

    def _extract_triggers(self, table_name: str) -> List[Dict[str, Any]]:
        """提取觸發器資訊"""
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                trigger_name,
                trigger_type,
                triggering_event,
                status,
                description
            FROM user_triggers
            WHERE table_name = :table_name
            ORDER BY trigger_name
        """, {"table_name": table_name})

        triggers = []
        for row in cursor.fetchall():
            triggers.append({
                "name": row[0],
                "type": row[1],
                "event": row[2],
                "status": row[3],
                "description": row[4]
            })

        cursor.close()
        return triggers

    def extract_views(self) -> List[Dict[str, Any]]:
        """提取視圖資訊"""
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT view_name, text
            FROM user_views
            ORDER BY view_name
        """)

        views = []
        for row in cursor.fetchall():
            view_name = row[0]
            views.append({
                "name": view_name,
                "type": "VIEW",
                "sql": row[1],
                "columns": self._extract_columns(view_name)
            })

        cursor.close()
        return views

    def extract_sequences(self) -> List[Dict[str, Any]]:
        """提取序列資訊"""
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                sequence_name,
                min_value,
                max_value,
                increment_by,
                cycle_flag,
                cache_size,
                last_number
            FROM user_sequences
            ORDER BY sequence_name
        """)

        sequences = []
        for row in cursor.fetchall():
            sequences.append({
                "name": row[0],
                "type": "SEQUENCE",
                "min_value": row[1],
                "max_value": row[2],
                "increment_by": row[3],
                "cycle": row[4] == 'Y',
                "cache_size": row[5],
                "last_number": row[6]
            })

        cursor.close()
        return sequences

    def extract_synonyms(self) -> List[Dict[str, Any]]:
        """提取同義詞資訊"""
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                synonym_name,
                table_owner,
                table_name,
                db_link
            FROM user_synonyms
            ORDER BY synonym_name
        """)

        synonyms = []
        for row in cursor.fetchall():
            synonym_info = {
                "name": row[0],
                "type": "SYNONYM",
                "table_owner": row[1],
                "table_name": row[2],
                "db_link": row[3],
                "is_remote": row[3] is not None
            }

            if not synonym_info["is_remote"] and row[1]:
                synonym_info["resolved_table"] = f"{row[1]}.{row[2]}"
            else:
                synonym_info["resolved_table"] = row[2]

            synonyms.append(synonym_info)

        cursor.close()
        return synonyms

    def extract_procedures_and_functions(self) -> List[Dict[str, Any]]:
        """提取 Procedures 和 Functions（從 Package 中分離）"""
        cursor = self.connection.cursor()

        # 取得所有 Procedure 和 Function（包含獨立和 Package 內的）
        cursor.execute("""
            SELECT
                object_name,
                procedure_name,
                object_type,
                status,
                created,
                last_ddl_time
            FROM user_procedures
            WHERE object_type IN ('PROCEDURE', 'FUNCTION')
               OR (object_type = 'PACKAGE' AND procedure_name IS NOT NULL)
            ORDER BY object_name, procedure_name
        """)

        procedures = []
        for row in cursor.fetchall():
            object_name = row[0]
            procedure_name = row[1] if row[1] else object_name
            object_type = row[2]

            # 判斷是否在 Package 中
            is_in_package = object_type == 'PACKAGE'
            full_name = f"{object_name}.{procedure_name}" if is_in_package else procedure_name

            proc_info = {
                "name": procedure_name,
                "full_name": full_name,
                "type": "FUNCTION" if "FUNCTION" in object_type else "PROCEDURE",
                "package_name": object_name if is_in_package else None,
                "is_in_package": is_in_package,
                "status": row[3],
                "created": row[4].isoformat() if row[4] else None,
                "last_modified": row[5].isoformat() if row[5] else None,
                "parameters": self._extract_procedure_parameters(object_name, procedure_name),
                "source_code": self._extract_procedure_source(object_name, is_in_package),
                "dependencies": self._extract_procedure_dependencies(object_name, procedure_name),
            }

            procedures.append(proc_info)

        cursor.close()
        return procedures

    def _extract_procedure_parameters(self, object_name: str, procedure_name: str) -> List[Dict[str, Any]]:
        """提取 Procedure/Function 參數"""
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                argument_name,
                data_type,
                in_out,
                position,
                data_length,
                data_precision,
                data_scale
            FROM user_arguments
            WHERE object_name = :object_name
              AND (NVL(:procedure_name, object_name) = object_name
                   OR NVL(:procedure_name, object_name) = NVL(overload, :procedure_name))
            ORDER BY position NULLS FIRST
        """, {
            "object_name": object_name,
            "procedure_name": procedure_name
        })

        parameters = []
        for row in cursor.fetchall():
            # argument_name 為 NULL 表示是 Function 的返回值
            param = {
                "name": row[0] if row[0] else "RETURN_VALUE",
                "data_type": row[1],
                "direction": row[2],  # IN, OUT, IN/OUT
                "position": row[3] if row[3] is not None else 0,
                "length": row[4],
                "precision": row[5],
                "scale": row[6]
            }
            parameters.append(param)

        cursor.close()
        return parameters

    def _extract_procedure_source(self, object_name: str, is_package: bool) -> str:
        """提取 Procedure/Function 原始碼"""
        cursor = self.connection.cursor()

        if is_package:
            # Package 的 body
            cursor.execute("""
                SELECT text
                FROM user_source
                WHERE name = :object_name
                  AND type = 'PACKAGE BODY'
                ORDER BY line
            """, {"object_name": object_name})
        else:
            # 獨立的 Procedure/Function
            cursor.execute("""
                SELECT text
                FROM user_source
                WHERE name = :object_name
                ORDER BY line
            """, {"object_name": object_name})

        source_lines = [row[0] for row in cursor.fetchall()]
        source_code = ''.join(source_lines)

        cursor.close()
        return source_code

    def _extract_procedure_dependencies(self, object_name: str, procedure_name: str) -> Dict[str, List[str]]:
        """提取 Procedure/Function 的依賴關係"""
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                referenced_name,
                referenced_type,
                referenced_owner
            FROM user_dependencies
            WHERE name = :object_name
              AND type IN ('PROCEDURE', 'FUNCTION', 'PACKAGE', 'PACKAGE BODY')
            ORDER BY referenced_type, referenced_name
        """, {"object_name": object_name})

        dependencies = {
            "tables": [],
            "views": [],
            "sequences": [],
            "procedures": [],
            "functions": [],
            "packages": [],
            "synonyms": [],
            "others": []
        }

        for row in cursor.fetchall():
            ref_name = row[0]
            ref_type = row[1]
            ref_owner = row[2]

            # 跳過系統物件
            if ref_owner and ref_owner != self.user.upper():
                continue

            if ref_type == 'TABLE':
                dependencies["tables"].append(ref_name)
            elif ref_type == 'VIEW':
                dependencies["views"].append(ref_name)
            elif ref_type == 'SEQUENCE':
                dependencies["sequences"].append(ref_name)
            elif ref_type == 'PROCEDURE':
                dependencies["procedures"].append(ref_name)
            elif ref_type == 'FUNCTION':
                dependencies["functions"].append(ref_name)
            elif ref_type in ('PACKAGE', 'PACKAGE BODY'):
                dependencies["packages"].append(ref_name)
            elif ref_type == 'SYNONYM':
                dependencies["synonyms"].append(ref_name)
            else:
                dependencies["others"].append(f"{ref_name} ({ref_type})")

        cursor.close()
        return dependencies

    def extract_oracle_jobs(self) -> List[Dict[str, Any]]:
        """提取 Oracle Scheduler Jobs 和 Legacy DBMS_JOBS"""
        cursor = self.connection.cursor()
        jobs = []

        # 1. 提取 Oracle Scheduler Jobs（11g+）
        try:
            cursor.execute("""
                SELECT
                    job_name,
                    job_type,
                    job_action,
                    schedule_name,
                    schedule_type,
                    repeat_interval,
                    start_date,
                    next_run_date,
                    last_start_date,
                    enabled,
                    state,
                    run_count,
                    failure_count,
                    comments
                FROM user_scheduler_jobs
                ORDER BY job_name
            """)

            for row in cursor.fetchall():
                job_info = {
                    "name": row[0],
                    "type": "SCHEDULER_JOB",
                    "job_type": row[1],  # PLSQL_BLOCK, STORED_PROCEDURE, EXECUTABLE 等
                    "job_action": row[2],  # Procedure 名稱或 PL/SQL 程式碼
                    "schedule_name": row[3],
                    "schedule_type": row[4],  # CALENDAR, NAMED, IMMEDIATE 等
                    "repeat_interval": row[5],  # CRON 表達式
                    "start_date": row[6].isoformat() if row[6] else None,
                    "next_run_date": row[7].isoformat() if row[7] else None,
                    "last_start_date": row[8].isoformat() if row[8] else None,
                    "enabled": row[9] == 'TRUE',
                    "state": row[10],  # RUNNING, SCHEDULED, DISABLED 等
                    "run_count": row[11],
                    "failure_count": row[12],
                    "comments": row[13],
                    "calls_procedure": self._extract_procedure_from_job_action(row[1], row[2])
                }
                jobs.append(job_info)
        except Exception as e:
            # 可能沒有權限或是舊版本 Oracle
            print(f"Warning: 無法提取 Scheduler Jobs: {e}")

        # 2. 提取 Legacy DBMS_JOB (Oracle 10g 及更早版本)
        try:
            cursor.execute("""
                SELECT
                    job,
                    what,
                    next_date,
                    interval,
                    broken,
                    failures,
                    this_date,
                    total_time
                FROM user_jobs
                ORDER BY job
            """)

            for row in cursor.fetchall():
                job_info = {
                    "name": f"DBMS_JOB_{row[0]}",
                    "type": "DBMS_JOB",
                    "job_id": row[0],
                    "job_action": row[1],  # PL/SQL 程式碼
                    "next_run_date": row[2].isoformat() if row[2] else None,
                    "interval": row[3],  # PL/SQL 表達式
                    "broken": row[4] == 'Y',
                    "failures": row[5],
                    "last_start_date": row[6].isoformat() if row[6] else None,
                    "total_execution_time": row[7],
                    "calls_procedure": self._extract_procedure_from_job_action("PLSQL_BLOCK", row[1])
                }
                jobs.append(job_info)
        except Exception as e:
            # 可能沒有權限
            print(f"Warning: 無法提取 DBMS_JOBS: {e}")

        cursor.close()
        return jobs

    def _extract_procedure_from_job_action(self, job_type: str, job_action: str) -> Optional[str]:
        """從 Job Action 中提取調用的 Procedure 名稱"""
        if not job_action:
            return None

        # 如果是 STORED_PROCEDURE 類型，直接返回
        if job_type == 'STORED_PROCEDURE':
            return job_action.strip()

        # 如果是 PL/SQL 程式碼，嘗試提取 Procedure 調用
        # 簡單的 pattern matching（可以更精確）
        import re

        # 尋找 EXECUTE、BEGIN、CALL 等關鍵字後的 Procedure 名稱
        patterns = [
            r'EXECUTE\s+([A-Z_][A-Z0-9_\.]*)',
            r'BEGIN\s+([A-Z_][A-Z0-9_\.]*)\s*[\(;]',
            r'CALL\s+([A-Z_][A-Z0-9_\.]*)',
            r'^\s*([A-Z_][A-Z0-9_\.]*)\s*\(',  # 直接調用
        ]

        for pattern in patterns:
            match = re.search(pattern, job_action.upper())
            if match:
                return match.group(1)

        return None

    def extract_all(self) -> Dict[str, Any]:
        """提取所有 Schema 資訊"""
        return {
            "database_type": "Oracle",
            "user": self.user,
            "dsn": self.dsn,
            "tables": self.extract_tables(),
            "views": self.extract_views(),
            "sequences": self.extract_sequences(),
            "synonyms": self.extract_synonyms(),
            "procedures_and_functions": self.extract_procedures_and_functions(),
            "oracle_jobs": self.extract_oracle_jobs(),
        }


def load_oracle_config(config_file: str = "config/oracle_config.yaml") -> Dict[str, Any]:
    """載入 Oracle 配置檔"""
    config_path = Path(config_file)

    if not config_path.exists():
        raise FileNotFoundError(
            f"配置檔不存在: {config_path}\n"
            f"請複製 config/oracle_config.example.yaml 為 config/oracle_config.yaml"
        )

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_password_for_connection(connection_name: str, interactive: bool = True) -> str:
    """
    取得連線密碼（從環境變數或互動式輸入）

    Args:
        connection_name: 連線名稱（如 dev, test, prod）
        interactive: 是否允許互動式輸入

    Returns:
        密碼字串
    """
    env_var_name = f"ORACLE_{connection_name.upper()}_PASSWORD"
    password = os.getenv(env_var_name)

    if password:
        return password

    if not interactive:
        raise ValueError(
            f"未設定環境變數: {env_var_name}\n"
            f"請執行: export {env_var_name}='your_password'"
        )

    password = getpass.getpass(f"請輸入 {connection_name} 的密碼: ")
    return password


def extract_db_schema_by_config(
    connection_name: str = "dev",
    output_file: str = "output/db_schema.json",
    interactive: bool = True
) -> Dict[str, Any]:
    """使用配置檔提取 Oracle Schema（方案 A：安全方式）"""
    try:
        config = load_oracle_config()

        if connection_name not in config["connections"]:
            available = ", ".join(config["connections"].keys())
            raise ValueError(
                f"連線 '{connection_name}' 不存在\n"
                f"可用的連線: {available}"
            )

        conn_config = config["connections"][connection_name]
        password = get_password_for_connection(connection_name, interactive)

        return extract_oracle_schema(
            user=conn_config["user"],
            password=password,
            dsn=conn_config["dsn"],
            output_file=output_file
        )

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def extract_oracle_schema(
    user: str,
    password: str,
    dsn: str,
    output_file: str = "output/db_schema.json"
) -> Dict[str, Any]:
    """提取 Oracle Schema（內部函數）"""
    try:
        extractor = OracleSchemaExtractor(user, password, dsn)
        extractor.connect()

        schema = extractor.extract_all()
        extractor.disconnect()

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "summary": {
                "total_tables": len(schema["tables"]),
                "total_views": len(schema["views"]),
                "total_sequences": len(schema["sequences"]),
                "total_synonyms": len(schema["synonyms"]),
                "total_procedures_functions": len(schema["procedures_and_functions"]),
                "total_oracle_jobs": len(schema["oracle_jobs"]),
            },
            "output_file": str(output_path.absolute())
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    import sys

    print("Oracle Schema 提取工具")
    print("=" * 50)

    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        connection_name = sys.argv[2] if len(sys.argv) > 2 else "dev"
        print(f"使用配置檔模式，連線: {connection_name}")
        result = extract_db_schema_by_config(connection_name)
    else:
        print("手動輸入模式（測試用）")
        user = input("使用者名稱: ")
        password = getpass.getpass("密碼: ")
        host = input("主機 (預設 localhost): ") or "localhost"
        port = input("埠號 (預設 1521): ") or "1521"
        service = input("Service Name: ")

        dsn = f"{host}:{port}/{service}"
        print(f"\n連線到: {user}@{dsn}")
        print("提取中...")

        result = extract_oracle_schema(user, password, dsn)

    if result["status"] == "success":
        print("\n✓ 提取成功！")
        print(f"  表:                 {result['summary']['total_tables']}")
        print(f"  視圖:               {result['summary']['total_views']}")
        print(f"  序列:               {result['summary']['total_sequences']}")
        print(f"  同義詞:             {result['summary']['total_synonyms']}")
        print(f"  Procedure/Function: {result['summary']['total_procedures_functions']}")
        print(f"  Oracle Jobs:        {result['summary']['total_oracle_jobs']}")
        print(f"  輸出: {result['output_file']}")
    else:
        print(f"\n✗ 錯誤: {result['error']}")
