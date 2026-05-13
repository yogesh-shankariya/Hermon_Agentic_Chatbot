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
    def __init__(self, rows: list[dict] | None = None, drop_rows: list[dict] | None = None):
        self.rows = rows if rows is not None else [{"row_type": "total", "lead_count": 3}]
        self.drop_rows = drop_rows if drop_rows is not None else []
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
        if "drop_sets AS" in sql:
            return list(self.drop_rows[:max_rows])
        if max_rows is None:
            return list(self.rows)
        return list(self.rows[:max_rows])


def _sample_funnel_rows() -> list[dict]:
    return [
        {
            "row_type": "total",
            "lead_count": 5,
            "appointment_count": 4,
            "completed_call_count": 3,
            "no_show_count": 1,
            "signed_contract_count": 2,
            "paid_payment_count": 1,
        },
        {
            "row_type": "funnel_flow",
            "step_order": 1,
            "step_key": "total_leads",
            "leads_reached": 5,
            "dropped_from_previous": None,
            "drop_rate_from_previous": None,
            "conversion_rate_from_previous": None,
        },
        {
            "row_type": "funnel_flow",
            "step_order": 2,
            "step_key": "booked_call",
            "leads_reached": 4,
            "dropped_from_previous": 1,
            "drop_rate_from_previous": Decimal("20.00"),
            "conversion_rate_from_previous": Decimal("80.00"),
        },
        {
            "row_type": "funnel_flow",
            "step_order": 3,
            "step_key": "completed_call",
            "leads_reached": 3,
            "dropped_from_previous": 1,
            "drop_rate_from_previous": Decimal("25.00"),
            "conversion_rate_from_previous": Decimal("75.00"),
        },
        {
            "row_type": "funnel_flow",
            "step_order": 4,
            "step_key": "signed_contract",
            "leads_reached": 2,
            "dropped_from_previous": 1,
            "drop_rate_from_previous": Decimal("33.33"),
            "conversion_rate_from_previous": Decimal("66.67"),
        },
        {
            "row_type": "funnel_flow",
            "step_order": 5,
            "step_key": "paid_converted",
            "leads_reached": 1,
            "dropped_from_previous": 1,
            "drop_rate_from_previous": Decimal("50.00"),
            "conversion_rate_from_previous": Decimal("50.00"),
        },
        {
            "row_type": "stage",
            "funnel_stage": "lead_only",
            "conversion_outcome": "lead_not_booked",
            "lead_count": 1,
            "pct_of_total_leads": Decimal("20.00"),
            "net_collected_amount": Decimal("0.00"),
        },
        {
            "row_type": "stage",
            "funnel_stage": "booked_not_completed",
            "conversion_outcome": "booked_not_attended",
            "lead_count": 1,
            "pct_of_total_leads": Decimal("20.00"),
            "net_collected_amount": Decimal("0.00"),
        },
        {
            "row_type": "stage",
            "funnel_stage": "completed_not_signed",
            "conversion_outcome": "attended_not_signed",
            "lead_count": 1,
            "pct_of_total_leads": Decimal("20.00"),
            "net_collected_amount": Decimal("0.00"),
        },
        {
            "row_type": "stage",
            "funnel_stage": "signed_not_paid",
            "conversion_outcome": "signed_pending_payment",
            "lead_count": 1,
            "pct_of_total_leads": Decimal("20.00"),
            "net_collected_amount": Decimal("0.00"),
        },
        {
            "row_type": "stage",
            "funnel_stage": "paid",
            "conversion_outcome": "converted_paid",
            "lead_count": 1,
            "pct_of_total_leads": Decimal("20.00"),
            "net_collected_amount": Decimal("5000.00"),
        },
        {
            "row_type": "activity_counts",
            "appointment_records": 4,
            "completed_call_records": 3,
            "no_show_records": 1,
            "signed_contract_records": 2,
            "paid_payment_records": 1,
        },
    ]


def _sample_drop_reconciliation_rows() -> list[dict]:
    return [
        {
            "drop_point_key": "lead_to_booked",
            "movement_dropped_leads": 1,
            "drop_set_leads": 1,
            "offsetting_later_step_leads": 0,
            "funnel_stage": "lead_only",
            "conversion_outcome": "lead_not_booked",
            "lead_count": 1,
            "pct_of_drop_set_leads": Decimal("100.00"),
        },
        {
            "drop_point_key": "booked_to_completed",
            "movement_dropped_leads": 1,
            "drop_set_leads": 1,
            "offsetting_later_step_leads": 0,
            "funnel_stage": "booked_not_completed",
            "conversion_outcome": "booked_not_attended",
            "lead_count": 1,
            "pct_of_drop_set_leads": Decimal("100.00"),
        },
        {
            "drop_point_key": "completed_to_signed",
            "movement_dropped_leads": 1,
            "drop_set_leads": 2,
            "offsetting_later_step_leads": 1,
            "funnel_stage": "completed_not_signed",
            "conversion_outcome": "attended_not_signed",
            "lead_count": 1,
            "pct_of_drop_set_leads": Decimal("50.00"),
        },
        {
            "drop_point_key": "completed_to_signed",
            "movement_dropped_leads": 1,
            "drop_set_leads": 2,
            "offsetting_later_step_leads": 1,
            "funnel_stage": "lost",
            "conversion_outcome": "lost",
            "lead_count": 1,
            "pct_of_drop_set_leads": Decimal("50.00"),
        },
        {
            "drop_point_key": "signed_to_paid",
            "movement_dropped_leads": 1,
            "drop_set_leads": 1,
            "offsetting_later_step_leads": 0,
            "funnel_stage": "signed_not_paid",
            "conversion_outcome": "signed_pending_payment",
            "lead_count": 1,
            "pct_of_drop_set_leads": Decimal("100.00"),
        },
    ]


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

    def test_funnel_snapshot_uses_default_six_month_period_from_snapshot_anchor(self):
        fake_db = FakeDb(rows=_sample_funnel_rows(), drop_rows=_sample_drop_reconciliation_rows())

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_funnel_snapshot(org_id="org_1")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["row_count"], 5)
        self.assertIn("lead_created_at cohort logic", result["scope_note"])
        self.assertIn("already major-unit EUR values", result["scope_note"])
        self.assertEqual(
            result["period"],
            {
                "start_date": "2025-11-10",
                "end_date": "2026-05-10",
                "display_start_date": "2025-11-10",
                "display_end_date": "2026-05-09",
                "date_field": "lead_created_at",
                "date_range_display": "10 Nov 2025 to 9 May 2026",
                "anchor_date": "2026-05-09",
            },
        )
        self.assertIsInstance(result["rows"], list)
        self.assertEqual(len(result["rows"]), len(_sample_funnel_rows()))
        self.assertEqual(fake_db.calls[1]["params"]["org_id"], "org_1")
        self.assertEqual(fake_db.calls[1]["params"]["start_date"], "2025-11-10")
        self.assertEqual(fake_db.calls[1]["params"]["end_date"], "2026-05-10")

    def test_funnel_snapshot_preserves_explicit_period(self):
        fake_db = FakeDb(rows=_sample_funnel_rows(), drop_rows=_sample_drop_reconciliation_rows())

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_funnel_snapshot(
                org_id="org_1",
                current_start_date="2026-03-01",
                current_end_date="2026-04-01",
            )

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["period"],
            {
                "start_date": "2026-03-01",
                "end_date": "2026-04-01",
                "display_start_date": "2026-03-01",
                "display_end_date": "2026-03-31",
                "date_field": "lead_created_at",
                "date_range_display": "1 Mar 2026 to 31 Mar 2026",
                "anchor_date": "2026-05-09",
            },
        )
        self.assertEqual(fake_db.calls[1]["params"]["start_date"], "2026-03-01")
        self.assertEqual(fake_db.calls[1]["params"]["end_date"], "2026-04-01")

    def test_funnel_snapshot_returns_separate_business_sections(self):
        fake_db = FakeDb(rows=_sample_funnel_rows(), drop_rows=_sample_drop_reconciliation_rows())

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_funnel_snapshot(org_id="org_1")

        self.assertIn("funnel_flow", result)
        self.assertIn("drop_reconciliation", result)
        self.assertIn("final_position_breakdown", result)
        self.assertIn("activity_counts", result)
        self.assertIsInstance(result["drop_reconciliation"], list)
        self.assertIn("display_start_date", result["period"])
        self.assertIn("display_end_date", result["period"])
        self.assertIn("date_range_display", result["period"])
        self.assertEqual(
            result["activity_counts"],
            {
                "appointment_records": 4,
                "completed_call_records": 3,
                "no_show_records": 1,
                "signed_contract_records": 2,
                "paid_payment_records": 1,
            },
        )
        labels_by_stage = {
            row["funnel_stage"]: row["display_label"] for row in result["final_position_breakdown"]
        }
        self.assertEqual(labels_by_stage["paid"], "Paid / converted")
        self.assertEqual(
            labels_by_stage["booked_not_completed"],
            "Booked but did not complete call",
        )

    def test_funnel_flow_uses_unique_lead_step_keys_and_drop_metrics(self):
        fake_db = FakeDb(rows=_sample_funnel_rows(), drop_rows=_sample_drop_reconciliation_rows())

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_funnel_snapshot(org_id="org_1")

        self.assertEqual(
            [row["step_key"] for row in result["funnel_flow"]],
            [
                "total_leads",
                "booked_call",
                "completed_call",
                "signed_contract",
                "paid_converted",
            ],
        )
        self.assertEqual(
            [row["step_label"] for row in result["funnel_flow"]],
            [
                "Total leads",
                "Booked a call",
                "Completed a call",
                "Signed contract",
                "Paid / converted",
            ],
        )
        for row in result["funnel_flow"][1:]:
            self.assertIn("dropped_from_previous", row)
            self.assertIn("drop_rate_from_previous", row)
            self.assertIn("conversion_rate_from_previous", row)

    def test_drop_reconciliation_has_required_fields_and_valid_keys(self):
        fake_db = FakeDb(rows=_sample_funnel_rows(), drop_rows=_sample_drop_reconciliation_rows())

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_funnel_snapshot(org_id="org_1")

        required_fields = {
            "drop_point_key",
            "drop_point_label",
            "from_step_label",
            "to_step_label",
            "dropped_leads",
            "movement_dropped_leads",
            "drop_set_leads",
            "offsetting_later_step_leads",
            "matches_funnel_flow_drop",
            "funnel_stage",
            "conversion_outcome",
            "final_position_label",
            "lead_count",
            "pct_of_dropped_leads",
            "pct_of_drop_set_leads",
            "reconciliation_note",
        }
        allowed_keys = {
            "lead_to_booked",
            "booked_to_completed",
            "completed_to_signed",
            "signed_to_paid",
        }

        for row in result["drop_reconciliation"]:
            self.assertTrue(required_fields.issubset(row))
            self.assertIn(row["drop_point_key"], allowed_keys)

    def test_drop_reconciliation_explains_flow_drops_and_offsets(self):
        fake_db = FakeDb(rows=_sample_funnel_rows(), drop_rows=_sample_drop_reconciliation_rows())

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_funnel_snapshot(org_id="org_1")

        drop_set_totals_by_key = {}
        drop_set_by_key = {}
        movement_by_key = {}
        offset_by_key = {}
        for row in result["drop_reconciliation"]:
            key = row["drop_point_key"]
            drop_set_totals_by_key[key] = drop_set_totals_by_key.get(key, 0) + row["lead_count"]
            drop_set_by_key[key] = row["drop_set_leads"]
            movement_by_key[key] = row["movement_dropped_leads"]
            offset_by_key[key] = row["offsetting_later_step_leads"]

        self.assertEqual(drop_set_totals_by_key, drop_set_by_key)

        flow_drops = {
            row["step_key"]: row["dropped_from_previous"] for row in result["funnel_flow"]
        }
        expected_movement_by_key = {
            "lead_to_booked": flow_drops["booked_call"],
            "booked_to_completed": flow_drops["completed_call"],
            "completed_to_signed": flow_drops["signed_contract"],
            "signed_to_paid": flow_drops["paid_converted"],
        }
        self.assertEqual(movement_by_key, expected_movement_by_key)
        self.assertEqual(drop_set_by_key["completed_to_signed"], 2)
        self.assertEqual(movement_by_key["completed_to_signed"], 1)
        self.assertEqual(offset_by_key["completed_to_signed"], 1)

        offset_row = next(
            row
            for row in result["drop_reconciliation"]
            if row["drop_point_key"] == "completed_to_signed"
        )
        self.assertFalse(offset_row["matches_funnel_flow_drop"])
        self.assertIn("without a tracked Completed a call record", offset_row["reconciliation_note"])

    def test_diagnostic_prompt_contains_funnel_answer_rules(self):
        prompt_text = (APP_DIR / "skills" / "modules" / "diagnostic_analytics.md").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "For funnel leakage questions, always show the step-by-step funnel movement first.",
            prompt_text,
        )
        self.assertIn("Do not mix activity record counts into the main funnel flow.", prompt_text)
        self.assertIn('Do not say "up to but not including".', prompt_text)
        self.assertIn("Drop Reconciliation Usage", prompt_text)
        self.assertIn("Do not say vague phrases", prompt_text)
        self.assertIn("Do not display a drop reconciliation table in the default answer.", prompt_text)
        self.assertIn("The main visible stuck groups are:", prompt_text)
        self.assertIn("format them with the `€` symbol", prompt_text)
        self.assertIn("€1,234.56", prompt_text)
        self.assertIn("For business-change or period-comparison questions, prefer a table", prompt_text)
        self.assertIn("Business Attention Answer Format", prompt_text)
        self.assertIn("| Priority | Focus area | Evidence | Why it matters | Recommended action |", prompt_text)
        self.assertIn("Do not force every returned metric into the table.", prompt_text)
        self.assertIn("If there is only one clear focus area, a short answer without a table is fine.", prompt_text)
        self.assertIn("Do not add separate confidence or data-quality sections", prompt_text)
        self.assertNotIn("Confidence:", prompt_text)
        self.assertNotIn("Data quality note:", prompt_text)
        self.assertNotIn("| Drop point | Net movement drop", prompt_text)
        self.assertNotIn("Where prior-step non-converters are now:", prompt_text)
        funnel_format = prompt_text.split("For funnel questions, use this structure:", 1)[1].split(
            "## Required Answer Format",
            1,
        )[0]
        non_funnel_format = prompt_text.split("For non-funnel diagnostic questions, use this structure:", 1)[
            1
        ].split("Rules:", 1)[0]
        self.assertIn("Recommended next action:", non_funnel_format)

    def test_business_change_uses_default_org_and_previous_six_month_period(self):
        fake_db = FakeDb()

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_business_change_snapshot()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["periods"]["current"]["start_date"], "2025-11-10")
        self.assertEqual(result["periods"]["current"]["end_date"], "2026-05-10")
        self.assertEqual(result["periods"]["previous"]["start_date"], "2025-05-10")
        self.assertEqual(result["periods"]["previous"]["end_date"], "2025-11-10")
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
            diagnostic_tools.DROP_RECONCILIATION_SQL,
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
