from __future__ import annotations

import importlib.util
import json
import re
import sys
import types
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"


class FakeTool:
    def __init__(self, func, name: str | None = None):
        self.func = func
        self.name = name or func.__name__

    def invoke(self, args):
        return self.func(**args)


def fake_tool(*args, **kwargs):
    if args and callable(args[0]):
        return FakeTool(args[0], kwargs.get("name"))

    name = args[0] if args else kwargs.get("name")

    def decorator(func):
        return FakeTool(func, name)

    return decorator


class FakeDb:
    def __init__(self, rows: list[dict] | None = None):
        self.rows = rows if rows is not None else [{"row_type": "total", "lead_count": 3}]
        self.calls: list[dict] = []

    def query_records(self, sql: str, params: dict | None = None, *, max_rows: int | None = None):
        self.calls.append({"sql": sql, "params": params or {}, "max_rows": max_rows})
        if "MIN(dls.lead_created_at)::date" in sql:
            return [
                {
                    "min_lead_created_date": "2026-01-15",
                    "max_lead_created_date": "2026-05-09",
                }
            ]
        if max_rows is None:
            return list(self.rows)
        return list(self.rows[:max_rows])


def _load_diagnostic_tools_module():
    module_path = APP_DIR / "tools" / "diagnostic_tools.py"
    module_name = "diagnostic_tools_under_test"

    langchain_module = types.ModuleType("langchain")
    langchain_module.__path__ = []
    tools_module = types.ModuleType("langchain.tools")
    tools_module.tool = fake_tool

    fake_config = types.ModuleType("app.config")
    fake_config.get_sql_agent_settings = lambda: SimpleNamespace(default_org_id="org_default")

    fake_db = types.ModuleType("app.db")
    fake_db.get_db = lambda: FakeDb()

    originals = {
        name: sys.modules.get(name)
        for name in ("langchain", "langchain.tools", "app.config", "app.db")
    }
    sys.modules["langchain"] = langchain_module
    sys.modules["langchain.tools"] = tools_module
    sys.modules["app.config"] = fake_config
    sys.modules["app.db"] = fake_db

    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(module_name, None)
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


diagnostic_tools = _load_diagnostic_tools_module()


class DiagnosticToolLayerTests(unittest.TestCase):
    def test_exports_four_diagnostic_tools(self):
        self.assertEqual(
            [tool.name for tool in diagnostic_tools.DIAGNOSTIC_TOOLS],
            [
                "get_diagnostic_funnel_snapshot",
                "get_diagnostic_source_snapshot",
                "get_diagnostic_source_quality_snapshot",
                "get_diagnostic_business_change_snapshot",
            ],
        )
        self.assertTrue(callable(diagnostic_tools.get_diagnostic_funnel_snapshot))
        self.assertTrue(callable(diagnostic_tools.get_diagnostic_source_snapshot))
        self.assertTrue(callable(diagnostic_tools.get_diagnostic_source_quality_snapshot))
        self.assertTrue(callable(diagnostic_tools.get_diagnostic_business_change_snapshot))

        init_text = (APP_DIR / "tools" / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("DIAGNOSTIC_TOOLS", init_text)
        self.assertIn("get_diagnostic_business_change_snapshot_tool", init_text)

    def test_business_table_scope_includes_snapshot(self):
        postgres_text = (APP_DIR / "db" / "postgres.py").read_text(encoding="utf-8")
        self.assertIn('"diagnostic_lead_snapshot"', postgres_text)

    def test_funnel_snapshot_uses_default_period_from_snapshot_anchor(self):
        fake_db = FakeDb()

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_funnel_snapshot(org_id="org_1")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["row_count"], 1)
        self.assertIn("lead_created_at cohort logic", result["scope_note"])
        self.assertEqual(
            result["period"],
            {
                "start_date": "2026-05-01",
                "end_date": "2026-05-10",
                "anchor_date": "2026-05-09",
                "date_field": "lead_created_at",
            },
        )
        self.assertIsInstance(result["rows"], list)
        self.assertEqual(fake_db.calls[1]["params"]["org_id"], "org_1")
        self.assertEqual(fake_db.calls[1]["params"]["start_date"], "2026-05-01")
        self.assertEqual(fake_db.calls[1]["params"]["end_date"], "2026-05-10")

    def test_business_change_uses_default_org_and_previous_month(self):
        fake_db = FakeDb()

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_business_change_snapshot()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["periods"]["current"]["start_date"], "2026-05-01")
        self.assertEqual(result["periods"]["current"]["end_date"], "2026-05-10")
        self.assertEqual(result["periods"]["previous"]["start_date"], "2026-04-01")
        self.assertEqual(result["periods"]["previous"]["end_date"], "2026-05-01")
        self.assertEqual(fake_db.calls[1]["params"]["org_id"], "org_default")

    def test_invalid_source_basis_wrapper_returns_error_json(self):
        fake_db = FakeDb()

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            raw = diagnostic_tools.get_diagnostic_source_snapshot_tool.invoke(
                {"org_id": "org_1", "source_basis": "utm_campaign"}
            )

        payload = json.loads(raw)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["tool"], "get_diagnostic_source_snapshot")
        self.assertIn("scope_note", payload)
        self.assertEqual(payload["row_count"], 0)
        self.assertIn("source_basis must be one of: first, last", payload["error"])

    def test_plain_function_returns_error_payload_for_empty_snapshot(self):
        class EmptySnapshotDb(FakeDb):
            def query_records(
                self,
                sql: str,
                params: dict | None = None,
                *,
                max_rows: int | None = None,
            ):
                self.calls.append({"sql": sql, "params": params or {}, "max_rows": max_rows})
                return []

        fake_db = EmptySnapshotDb()

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_funnel_snapshot(org_id="org_1")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["tool"], "get_diagnostic_funnel_snapshot")
        self.assertIn("scope_note", result)
        self.assertEqual(result["row_count"], 0)
        self.assertIn("no rows for this org", result["error"])

    def test_plain_function_payload_is_json_serializable(self):
        fake_db = FakeDb(rows=[{"net_collected_amount": Decimal("123.45")}])

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_source_snapshot(org_id="org_1")

        self.assertEqual(result["rows"][0]["net_collected_amount"], 123.45)
        self.assertEqual(result["row_count"], 1)
        json.dumps(result)

    def test_source_limits_are_clamped(self):
        fake_db = FakeDb()

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            diagnostic_tools.get_diagnostic_source_snapshot(
                org_id="org_1",
                source_basis="last",
                limit=999,
            )

        query_call = fake_db.calls[1]
        self.assertEqual(query_call["params"]["limit"], 50)
        self.assertEqual(query_call["max_rows"], 50)
        self.assertIn("dls.last_source", query_call["sql"])
        self.assertNotIn("utm_campaign", query_call["sql"])

    def test_source_quality_keeps_overall_row_outside_source_limit(self):
        rows = [
            {"row_type": "overall"},
            {"row_type": "source", "source_name": "A"},
            {"row_type": "source", "source_name": "B"},
        ]
        fake_db = FakeDb(rows=rows)

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_source_quality_snapshot(
                org_id="org_1",
                limit=2,
            )

        query_call = fake_db.calls[1]
        self.assertEqual(query_call["params"]["limit"], 2)
        self.assertEqual(query_call["max_rows"], 3)
        self.assertEqual(result["row_count"], 3)
        self.assertEqual(result["overall"], rows[0])
        self.assertEqual(result["sources"], rows[1:])
        self.assertEqual([row["row_type"] for row in result["rows"]], ["overall", "source", "source"])

    def test_diagnostic_sql_is_read_only_scoped_and_sanitized(self):
        sql_texts = [
            diagnostic_tools.SNAPSHOT_DATE_BOUNDS_SQL,
            diagnostic_tools.FUNNEL_SQL,
            diagnostic_tools.SOURCE_SNAPSHOT_SQL_TEMPLATE.format(source_column="first_source"),
            diagnostic_tools.SOURCE_SNAPSHOT_SQL_TEMPLATE.format(source_column="last_source"),
            diagnostic_tools.SOURCE_QUALITY_SQL_TEMPLATE.format(source_column="first_source"),
            diagnostic_tools.SOURCE_QUALITY_SQL_TEMPLATE.format(source_column="last_source"),
            diagnostic_tools.BUSINESS_CHANGE_SQL,
        ]
        dangerous_sql_re = re.compile(
            r"\b(alter|call|copy|create|delete|drop|execute|grant|insert|"
            r"lock|merge|refresh|reindex|revoke|truncate|update|vacuum)\b",
            re.IGNORECASE,
        )
        wildcard_re = re.compile(
            r"(\bselect\s+\*\s+\bfrom\b|\b[a-zA-Z_][a-zA-Z0-9_]*\.\*)",
            re.IGNORECASE | re.DOTALL,
        )
        blocked_terms = (
            "email",
            "phone",
            "raw_payload",
            "meeting_url",
            "recording_url",
            "transcript_url",
            "external_provider",
            "provider_id",
            "webhook",
        )

        for sql in sql_texts:
            with self.subTest(sql=sql[:40]):
                self.assertRegex(sql.strip(), re.compile(r"^(select|with)\b", re.IGNORECASE))
                self.assertIn("diagnostic_lead_snapshot dls", sql)
                self.assertIn("dls.clerk_org_id = :org_id", sql)
                self.assertIsNone(wildcard_re.search(sql))
                self.assertIsNone(dangerous_sql_re.search(sql))
                for blocked_term in blocked_terms:
                    self.assertNotIn(blocked_term, sql.lower())


if __name__ == "__main__":
    unittest.main()
