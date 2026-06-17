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
    def __init__(
        self,
        rows: list[dict] | None = None,
        drop_rows: list[dict] | None = None,
        stuck_group_rows: list[dict] | None = None,
    ):
        self.rows = rows if rows is not None else [{"row_type": "total", "lead_count": 3}]
        self.drop_rows = drop_rows if drop_rows is not None else []
        self.stuck_group_rows = (
            stuck_group_rows if stuck_group_rows is not None else _sample_stuck_group_rows()
        )
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
        if "stage_counts AS" in sql:
            return list(self.stuck_group_rows[:max_rows])
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


def _sample_stuck_group_rows() -> list[dict]:
    return [
        {
            "stage_order": 1,
            "stage_key": "never_booked",
            "cohort_name": "never_booked",
            "lead_count": 1,
            "pct_of_total_leads": Decimal("20.00"),
        },
        {
            "stage_order": 2,
            "stage_key": "booked_not_completed",
            "cohort_name": "booked_not_completed",
            "lead_count": 1,
            "pct_of_total_leads": Decimal("20.00"),
        },
        {
            "stage_order": 3,
            "stage_key": "completed_not_signed",
            "cohort_name": "completed_not_signed",
            "lead_count": 1,
            "pct_of_total_leads": Decimal("20.00"),
        },
        {
            "stage_order": 4,
            "stage_key": "signed_not_paid",
            "cohort_name": "signed_not_paid",
            "lead_count": 1,
            "pct_of_total_leads": Decimal("20.00"),
        },
        {
            "stage_order": 5,
            "stage_key": "paid_converted",
            "cohort_name": None,
            "lead_count": 1,
            "pct_of_total_leads": Decimal("20.00"),
        },
        {
            "stage_order": 6,
            "stage_key": "total_leads",
            "cohort_name": None,
            "lead_count": 5,
            "pct_of_total_leads": Decimal("100.00"),
        },
    ]


def _sample_text_reason_rows() -> list[dict]:
    return [
        {
            "row_type": "coverage",
            "total_cohort_leads": 4,
            "leads_with_text_insights": 3,
            "known_reason_leads": 2,
            "unknown_only_reason_leads": 1,
        },
        {
            "row_type": "combination",
            "item_key": "price_or_budget + timing_issue",
            "lead_count": 1,
        },
        {
            "row_type": "combination",
            "item_key": "needs_partner_approval",
            "lead_count": 1,
        },
        {
            "row_type": "combination",
            "item_key": "unknown_reason",
            "lead_count": 1,
        },
        {
            "row_type": "combination",
            "item_key": "no_text_insight_available",
            "lead_count": 1,
        },
        {
            "row_type": "issue",
            "item_key": "price_or_budget",
            "lead_count": 2,
        },
        {
            "row_type": "issue",
            "item_key": "timing_issue",
            "lead_count": 2,
        },
        {
            "row_type": "issue",
            "item_key": "needs_partner_approval",
            "lead_count": 1,
        },
        {
            "row_type": "subcategory",
            "item_key": "needs_more_time",
            "lead_count": 2,
        },
        {
            "row_type": "buying_intent",
            "item_key": "medium",
            "lead_count": 3,
        },
        {
            "row_type": "source_text_type",
            "item_key": "call_summary",
            "lead_count": 3,
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
    def test_exports_seven_diagnostic_tools(self):
        self.assertEqual(
            [tool.name for tool in diagnostic_tools.DIAGNOSTIC_TOOLS],
            [
                "get_diagnostic_monthly_trend_overview_snapshot",
                "get_diagnostic_funnel_snapshot",
                "get_diagnostic_source_snapshot",
                "get_diagnostic_profile_snapshot",
                "get_diagnostic_source_quality_snapshot",
                "get_diagnostic_business_change_snapshot",
                "get_diagnostic_text_reason_snapshot",
            ],
        )
        self.assertTrue(callable(diagnostic_tools.get_diagnostic_monthly_trend_overview_snapshot))
        self.assertTrue(callable(diagnostic_tools.get_diagnostic_funnel_snapshot))
        self.assertTrue(callable(diagnostic_tools.get_diagnostic_source_snapshot))
        self.assertTrue(callable(diagnostic_tools.get_diagnostic_profile_snapshot))
        self.assertTrue(callable(diagnostic_tools.get_diagnostic_source_quality_snapshot))
        self.assertTrue(callable(diagnostic_tools.get_diagnostic_business_change_snapshot))
        self.assertTrue(callable(diagnostic_tools.get_diagnostic_text_reason_snapshot))
        tool_names = [tool.name for tool in diagnostic_tools.DIAGNOSTIC_TOOLS]
        self.assertNotIn("load_skill", tool_names)
        self.assertNotIn("run_readonly_sql", tool_names)
        self.assertNotIn("get_lead_360", tool_names)

        init_text = (APP_DIR / "tools" / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("DIAGNOSTIC_TOOLS", init_text)
        self.assertIn("get_diagnostic_monthly_trend_overview_snapshot_tool", init_text)
        self.assertIn("get_diagnostic_profile_snapshot_tool", init_text)
        self.assertIn("get_diagnostic_business_change_snapshot_tool", init_text)
        self.assertIn("get_diagnostic_text_reason_snapshot_tool", init_text)

    def test_business_table_scope_includes_snapshot(self):
        postgres_text = (APP_DIR / "db" / "postgres.py").read_text(encoding="utf-8")
        self.assertIn('"diagnostic_lead_snapshot"', postgres_text)

    def test_monthly_trend_overview_uses_default_completed_months_and_parallel_sections(self):
        class MonthlyTrendDb(FakeDb):
            def query_records(
                self,
                sql: str,
                params: dict | None = None,
                *,
                max_rows: int | None = None,
            ):
                self.calls.append({"sql": sql, "params": params or {}, "max_rows": max_rows})
                if "previous_month_lead_count" in sql:
                    return [
                        {
                            "month_start": "2026-02-01",
                            "month_label": "Feb 2026",
                            "lead_count": 82,
                            "previous_month_lead_count": None,
                            "lead_count_change": None,
                            "percentage_change": None,
                            "total_matching_leads": 280,
                        },
                        {
                            "month_start": "2026-03-01",
                            "month_label": "Mar 2026",
                            "lead_count": 90,
                            "previous_month_lead_count": 82,
                            "lead_count_change": 8,
                            "percentage_change": Decimal("9.76"),
                            "total_matching_leads": 280,
                        },
                    ]
                if "previous_month_net_collected_amount" in sql:
                    return [
                        {
                            "month_start": "2026-03-01",
                            "month_label": "Mar 2026",
                            "paid_payment_count": 22,
                            "net_collected_amount": Decimal("72500.00"),
                            "previous_month_net_collected_amount": Decimal("68500.00"),
                            "revenue_change": Decimal("4000.00"),
                            "percentage_change": Decimal("5.84"),
                        }
                    ]
                if "completed_call_rate" in sql:
                    return [
                        {
                            "month_start": "2026-03-01",
                            "month_label": "Mar 2026",
                            "booked_lead_count": 76,
                            "appointment_count": 82,
                            "completed_call_count": 55,
                            "no_show_count": 21,
                            "completed_call_rate": Decimal("67.07"),
                            "no_show_rate": Decimal("25.61"),
                        }
                    ]
                if "top_sources AS" in sql:
                    return [
                        {
                            "month_start": "2026-03-01",
                            "month_label": "Mar 2026",
                            "source_name": "Facebook",
                            "lead_count": 17,
                            "previous_period_lead_count": 13,
                            "percentage_change": Decimal("30.77"),
                            "total_matching_leads": 30,
                        }
                    ]
                if "top_profiles AS" in sql:
                    return [
                        {
                            "month_start": "2026-03-01",
                            "month_label": "Mar 2026",
                            "profile_value": "Student",
                            "lead_count": 20,
                            "previous_period_lead_count": 14,
                            "percentage_change": Decimal("42.86"),
                            "total_matching_leads": 34,
                        }
                    ]
                raise AssertionError("Unexpected monthly trend SQL")

        fake_db = MonthlyTrendDb()
        expected_end = diagnostic_tools.date.today().replace(day=1)
        expected_start = diagnostic_tools._add_months(expected_end, -3)

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_monthly_trend_overview_snapshot(
                org_id="org_1"
            )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["tool"], "get_diagnostic_monthly_trend_overview_snapshot")
        self.assertEqual(result["period"]["start_date"], expected_start.isoformat())
        self.assertEqual(result["period"]["end_date"], expected_end.isoformat())
        self.assertEqual(result["period"]["date_note"], "default previous 3 completed months")
        self.assertTrue(result["period"]["end_date_is_exclusive"])
        self.assertEqual(result["source_basis"], "first")
        self.assertEqual(result["profile_field"], "latest_profession")
        self.assertEqual(result["source_lead_trend"], result["source_trend"])
        self.assertEqual(result["profile_lead_trend"], result["profession_trend"])
        self.assertEqual(result["summary_metrics"]["latest_lead_count"], 90)
        self.assertEqual(result["summary_metrics"]["latest_revenue"], 72500.0)
        self.assertEqual(result["_diagnostics"]["parallel_execution"], True)
        self.assertEqual(result["_diagnostics"]["max_workers"], 4)
        self.assertEqual(result["_diagnostics"]["section_errors"], {})
        self.assertEqual(
            result["_diagnostics"]["successful_sections"],
            [
                "overall_lead_trend",
                "revenue_trend",
                "appointment_trend",
                "source_lead_trend",
                "profile_lead_trend",
            ],
        )
        self.assertEqual(len(fake_db.calls), 5)
        for call in fake_db.calls:
            self.assertEqual(call["params"]["org_id"], "org_1")
            self.assertEqual(call["params"]["start_date"], expected_start.isoformat())
            self.assertEqual(call["params"]["end_date"], expected_end.isoformat())
            self.assertNotIn("/ 100", call["sql"])
        self.assertTrue(any("dls.first_source" in call["sql"] for call in fake_db.calls))
        self.assertTrue(any("dls.latest_profession" in call["sql"] for call in fake_db.calls))

    def test_monthly_trend_overview_returns_partial_success_for_section_failure(self):
        class PartialMonthlyTrendDb(FakeDb):
            def query_records(
                self,
                sql: str,
                params: dict | None = None,
                *,
                max_rows: int | None = None,
            ):
                self.calls.append({"sql": sql, "params": params or {}, "max_rows": max_rows})
                if "top_profiles AS" in sql:
                    raise RuntimeError("profile section unavailable")
                return [{"month_start": "2026-03-01", "month_label": "Mar 2026"}]

        fake_db = PartialMonthlyTrendDb()

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_monthly_trend_overview_snapshot(
                org_id="org_1",
                start_date="2026-02-01",
                end_date="2026-05-01",
            )

        self.assertEqual(result["status"], "partial_success")
        self.assertEqual(result["profile_lead_trend"], [])
        self.assertIn("profile_lead_trend", result["_diagnostics"]["section_errors"])
        self.assertIn("One or more monthly trend sections", result["warnings"][0])

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
        self.assertIn("stuck_group_funnel", result)
        self.assertIn("largest_stuck_group", result)
        self.assertIn("selected_text_reason_cohort", result)
        self.assertIn("drop_reconciliation", result)
        self.assertIn("final_position_breakdown", result)
        self.assertIn("activity_counts", result)
        self.assertIsInstance(result["drop_reconciliation"], list)
        self.assertEqual(
            [row["stage_key"] for row in result["stuck_group_funnel"]],
            [
                "never_booked",
                "booked_not_completed",
                "completed_not_signed",
                "signed_not_paid",
                "paid_converted",
                "total_leads",
            ],
        )
        self.assertEqual(
            result["funnel_stage_validation"],
            {
                "total_leads": 5,
                "stage_total": 5,
                "stage_counts_reconcile": True,
            },
        )
        self.assertEqual(result["largest_stuck_group"]["cohort_name"], "completed_not_signed")
        self.assertEqual(
            result["selected_text_reason_cohort"],
            {
                "cohort_name": "completed_not_signed",
                "cohort_label": "Completed call but did not sign",
                "lead_count": 1,
                "reason": "Largest mutually exclusive final-stage stuck group",
            },
        )
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
        prompt_text = (
            APP_DIR / "skills" / "modules" / "diagnostic_analytics" / "1_0_0.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "For broad funnel leakage questions, always show the mutually exclusive final-stage funnel table first.",
            prompt_text,
        )
        self.assertIn("get_diagnostic_monthly_trend_overview_snapshot", prompt_text)
        self.assertIn("Generic Monthly Trend Overview", prompt_text)
        self.assertIn("Trend period:", prompt_text)
        self.assertIn("| Month | Lead count | Previous month | % change |", prompt_text)
        self.assertIn("| Month | Paid payments | Revenue | Previous month | % change |", prompt_text)
        self.assertIn(
            "| Month | Booked leads | Appointments | Completed calls | No-shows | Completed-call rate |",
            prompt_text,
        )
        self.assertIn("| Source | <Month 1> | <Month 2> | <Month 3> |", prompt_text)
        self.assertIn("| Profession | <Month 1> | <Month 2> | <Month 3> |", prompt_text)
        self.assertIn("Do not show full funnel stage tables", prompt_text)
        self.assertIn("Do not mix activity record counts into the main stuck-group table.", prompt_text)
        self.assertIn("The `Total` row must equal the sum of the five mutually exclusive stage rows", prompt_text)
        self.assertIn("If `get_diagnostic_funnel_snapshot.status` is `validation_failed`", prompt_text)
        self.assertIn("stuck_group_funnel", prompt_text)
        self.assertIn("selected_text_reason_cohort", prompt_text)
        self.assertIn("Never use a different cohort condition or a net movement drop count", prompt_text)
        self.assertIn('Do not say "up to but not including".', prompt_text)
        self.assertIn("Drop Reconciliation Usage", prompt_text)
        self.assertIn("Do not say vague phrases", prompt_text)
        self.assertIn("Do not display a drop reconciliation table in the default answer.", prompt_text)
        self.assertIn("| Funnel stage | Leads | What this means |", prompt_text)
        self.assertIn("Do not show the issue-pattern / reason-combination table in normal diagnostic answers.", prompt_text)
        self.assertIn("include_issue_combinations = true", prompt_text)
        self.assertIn("One lead can have multiple issues, so this table does not sum to", prompt_text)
        self.assertIn("| Individual issue | Leads with this issue | % of stuck leads |", prompt_text)
        self.assertNotIn("coverage note", prompt_text.lower())
        self.assertIn("Do not add a standalone coverage section by default", prompt_text)
        self.assertIn("Prefer concise bullet points over paragraph blocks", prompt_text)
        self.assertIn("format them with the `€` symbol", prompt_text)
        self.assertIn("€1,234.56", prompt_text)
        self.assertIn("For business-change or period-comparison questions, prefer a table", prompt_text)
        self.assertIn("Broad Overview Answer Format", prompt_text)
        self.assertIn("Use this table-led structure only for broad overview questions", prompt_text)
        self.assertIn("Do not use this broad-overview format for funnel-loss questions", prompt_text)
        self.assertIn('get_diagnostic_source_snapshot with source_basis = "first" and limit = 10', prompt_text)
        self.assertIn("get_diagnostic_profile_snapshot", prompt_text)
        self.assertIn("Profile Conversion Diagnostics", prompt_text)
        self.assertIn("Which profession converts best?", prompt_text)
        self.assertIn("Which profession should we focus on?", prompt_text)
        self.assertIn("Why are Business Owner leads not converting?", prompt_text)
        self.assertIn("Monthly leads trend by profession.", prompt_text)
        self.assertIn('profile_field = "latest_profession"', prompt_text)
        self.assertIn('profile_field = "latest_employment_status"', prompt_text)
        self.assertIn('sort_by = "paid_lead_rate"', prompt_text)
        self.assertNotIn(
            'get_diagnostic_profile_snapshot with profile_field = "latest_profession" and sort_by = "lead_count"',
            prompt_text,
        )
        self.assertIn("Based on the latest lead-level opt-in profile answer", prompt_text)
        self.assertIn("Do not describe these as exact opt-in submission counts", prompt_text)
        self.assertIn("Funnel view:", prompt_text)
        self.assertIn("Step conversion view:", prompt_text)
        self.assertIn("Source view: top 10 first sources, sorted by lifetime net collected", prompt_text)
        self.assertIn(
            "| Step | Leads reached | Dropped from previous | Drop rate from previous | Conversion from previous |",
            prompt_text,
        )
        self.assertIn(
            "| Source | Leads | Booked leads | Completed-call leads | Signed-contract leads | Paid leads | Lifetime net collected | What it suggests |",
            prompt_text,
        )
        self.assertIn("| Source | Leads | Completed-call records | Signed-contract records | Paid payment records | Lifetime net collected | What it suggests |", prompt_text)
        self.assertIn("use `drop_rate_from_previous` and `conversion_rate_from_previous`", prompt_text)
        self.assertIn("the lead-to-booked-call rate is 81.0%", prompt_text)
        self.assertIn("appointment records per lead", prompt_text)
        self.assertIn("If `is_truncated = true`", prompt_text)
        self.assertIn("Do not say \"all sources\" if the source rows are limited", prompt_text)
        self.assertIn("total_distinct_sources <= returned_source_count", prompt_text)
        self.assertIn("Do not call multiple-source leads source-quality failures.", prompt_text)
        self.assertIn("CRM-side first-source reporting rather than ad attribution", prompt_text)
        self.assertIn("do not describe them as \"top sources\"", prompt_text)
        self.assertIn("Do not call it paid leads", prompt_text)
        self.assertIn("Source interpretation text must be supported by metrics returned by the tool", prompt_text)
        self.assertIn(
            "Revenue figures here are cohort-based: they show lifetime net collected revenue for leads created in the selected period, not true payment-period revenue.",
            prompt_text,
        )
        self.assertIn("Business Attention Answer Format", prompt_text)
        self.assertIn("| Priority | Focus area | Evidence | Why it matters | Recommended action |", prompt_text)
        self.assertIn("For general business attention questions without a department", prompt_text)
        self.assertIn("Keep this priority-table format for narrower action questions", prompt_text)
        self.assertIn("Do not force every returned metric into the table.", prompt_text)
        self.assertIn("If there is only one clear focus area, a short answer without a table is fine.", prompt_text)
        self.assertIn("Do not add separate confidence or data-quality sections", prompt_text)
        self.assertIn("get_diagnostic_text_reason_snapshot", prompt_text)
        self.assertIn("Optional Issue-Pattern Table", prompt_text)
        self.assertIn("Individual Issue Distribution", prompt_text)
        self.assertIn("Never show raw diagnostic text enum values", prompt_text)
        self.assertIn("If combinations were explicitly requested, the reason combination table total equals selected_cohort_leads.", prompt_text)
        self.assertIn("Normal answers do not show issue-pattern / reason-combination tables.", prompt_text)
        self.assertIn("Default limits", prompt_text)
        self.assertNotIn("Confidence:", prompt_text)
        self.assertNotIn("Data quality note:", prompt_text)
        self.assertNotIn("| Drop point | Net movement drop", prompt_text)
        self.assertNotIn("Where prior-step non-converters are now:", prompt_text)
        funnel_format = prompt_text.split("For funnel questions, use this structure:", 1)[1].split(
            "## Broad Overview Answer Format",
            1,
        )[0]
        self.assertIn("One lead can have multiple issues", funnel_format)
        self.assertNotIn("reason combination distribution table", funnel_format.lower())
        self.assertNotIn("Issue combination", funnel_format)
        self.assertNotIn("Funnel view / Step conversion view / Source view", funnel_format)
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

    def test_source_snapshot_returns_limit_and_truncation_metadata(self):
        rows = [
            {"source_name": "A", "total_distinct_sources": 3},
            {"source_name": "B", "total_distinct_sources": 3},
            {"source_name": "C", "total_distinct_sources": 3},
        ]
        fake_db = FakeDb(rows=rows)

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_source_snapshot(org_id="org_1", limit=2)

        self.assertEqual(result["requested_limit"], 2)
        self.assertEqual(result["returned_source_count"], 2)
        self.assertEqual(result["total_distinct_sources"], 3)
        self.assertTrue(result["is_truncated"])
        self.assertEqual(
            result["source_sort"],
            "net_collected_amount DESC, signed_contract_count DESC, "
            "completed_call_count DESC, lead_count DESC, source_name ASC",
        )
        self.assertEqual(
            result["source_selection_note"],
            "Rows are limited by the requested limit and sorted by lifetime net collected.",
        )

    def test_profile_snapshot_returns_lead_level_profile_payload(self):
        rows = [
            {
                "profile_value": "Founder",
                "lead_count": 12,
                "paid_lead_rate": Decimal("25.00"),
            }
        ]
        fake_db = FakeDb(rows=rows)

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_profile_snapshot(
                org_id="org_1",
                profile_field="latest_profession",
                sort_by="paid_lead_rate",
            )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["tool"], "get_diagnostic_profile_snapshot")
        self.assertEqual(result["profile_field"], "latest_profession")
        self.assertEqual(result["profile_label"], "Profession")
        self.assertEqual(result["sort_by"], "paid_lead_rate")
        self.assertIn("latest lead-level opt-in profile answers", result["profile_basis_note"])
        self.assertIn("fewer than 10 leads", result["minimum_sample_caveat"])
        self.assertEqual(result["rows"][0]["profile_value"], "Founder")
        query_call = fake_db.calls[-1]
        self.assertIn("dls.latest_profession", query_call["sql"])
        self.assertIn("paid_lead_rate DESC NULLS LAST", query_call["sql"])
        self.assertNotIn("opt_in_question_answers", query_call["sql"])

    def test_profile_snapshot_rejects_unknown_profile_field(self):
        result = diagnostic_tools.get_diagnostic_profile_snapshot(
            org_id="org_1",
            profile_field="profession",
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["tool"], "get_diagnostic_profile_snapshot")
        self.assertIn("profile_field must be one of", result["error"])

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

    def test_diagnostic_sql_uses_distinct_booked_lead_metrics(self):
        source_sql = diagnostic_tools.SOURCE_SNAPSHOT_SQL_TEMPLATE.format(
            source_column="first_source"
        )

        self.assertIn("booked_lead_count", source_sql)
        self.assertIn("completed_call_lead_count", source_sql)
        self.assertIn("signed_lead_count", source_sql)
        self.assertIn("paid_lead_count", source_sql)
        self.assertIn("lead_to_booked_call_rate", source_sql)
        self.assertIn("lead_to_completed_call_rate", source_sql)
        self.assertIn("completed_lead_to_signed_lead_rate", source_sql)
        self.assertIn("signed_lead_to_paid_lead_rate", source_sql)
        self.assertIn("paid_lead_rate", source_sql)
        self.assertIn("appointment_records_per_lead", source_sql)
        self.assertIn("COUNT(*) OVER()::int AS total_distinct_sources", source_sql)
        self.assertNotIn("lead_to_appointment_rate", source_sql)

        self.assertIn("booked_lead_count", diagnostic_tools.BUSINESS_CHANGE_SQL)
        self.assertIn("lead_to_booked_call_rate", diagnostic_tools.BUSINESS_CHANGE_SQL)
        self.assertIn("appointment_records_per_lead", diagnostic_tools.BUSINESS_CHANGE_SQL)
        self.assertNotIn("lead_to_appointment_rate", diagnostic_tools.BUSINESS_CHANGE_SQL)

        profile_sql = diagnostic_tools.PROFILE_SNAPSHOT_SQL_TEMPLATE.format(
            profile_column="latest_employment_status",
            order_clause=diagnostic_tools.PROFILE_SNAPSHOT_SORTS["paid_lead_rate"],
        )
        self.assertIn("dls.latest_employment_status", profile_sql)
        self.assertIn("COUNT(*)::int AS lead_count", profile_sql)
        self.assertIn("booked_lead_count", profile_sql)
        self.assertIn("completed_call_lead_count", profile_sql)
        self.assertIn("signed_lead_count", profile_sql)
        self.assertIn("paid_lead_count", profile_sql)
        self.assertIn("paid_lead_rate DESC NULLS LAST", profile_sql)
        self.assertNotIn("opt_in_question_answers", profile_sql)

    def test_source_quality_issue_count_excludes_multiple_source_leads(self):
        source_quality_sql = diagnostic_tools.SOURCE_QUALITY_SQL_TEMPLATE.format(
            source_column="first_source"
        )

        self.assertIn("has_multiple_sources)::int AS multiple_source_leads", source_quality_sql)
        self.assertNotIn(
            "OR has_multiple_sources\n    )::int AS issue_leads",
            source_quality_sql,
        )

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

    def test_funnel_snapshot_includes_recommended_text_cohorts(self):
        fake_db = FakeDb(
            rows=_sample_funnel_rows(),
            drop_rows=_sample_drop_reconciliation_rows(),
            stuck_group_rows=[
                {
                    "stage_order": 1,
                    "stage_key": "never_booked",
                    "cohort_name": "never_booked",
                    "lead_count": 2,
                },
                {
                    "stage_order": 2,
                    "stage_key": "booked_not_completed",
                    "cohort_name": "booked_not_completed",
                    "lead_count": 5,
                },
                {
                    "stage_order": 3,
                    "stage_key": "completed_not_signed",
                    "cohort_name": "completed_not_signed",
                    "lead_count": 8,
                },
                {
                    "stage_order": 4,
                    "stage_key": "signed_not_paid",
                    "cohort_name": "signed_not_paid",
                    "lead_count": 3,
                },
                {"stage_order": 5, "stage_key": "paid_converted", "lead_count": 4},
                {"stage_order": 6, "stage_key": "total_leads", "lead_count": 22},
            ],
        )

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_funnel_snapshot(org_id="org_1")

        self.assertEqual(
            result["recommended_text_cohorts"],
            [
                {
                    "cohort_name": "completed_not_signed",
                    "cohort_label": "Completed call but did not sign",
                    "lead_count": 8,
                    "reason": "Largest mutually exclusive final-stage stuck group",
                },
                {
                    "cohort_name": "booked_not_completed",
                    "cohort_label": "Booked but did not complete call",
                    "lead_count": 5,
                    "reason": "Booked-call attendance leakage",
                },
            ],
        )
        self.assertEqual(result["selected_text_reason_cohort"], result["recommended_text_cohorts"][0])

    def test_funnel_stage_validation_fails_when_stage_rows_overcount_total(self):
        fake_db = FakeDb(
            rows=_sample_funnel_rows(),
            drop_rows=_sample_drop_reconciliation_rows(),
            stuck_group_rows=[
                {
                    "stage_order": 1,
                    "stage_key": "never_booked",
                    "cohort_name": "never_booked",
                    "lead_count": 108,
                },
                {
                    "stage_order": 2,
                    "stage_key": "booked_not_completed",
                    "cohort_name": "booked_not_completed",
                    "lead_count": 126,
                },
                {
                    "stage_order": 3,
                    "stage_key": "completed_not_signed",
                    "cohort_name": "completed_not_signed",
                    "lead_count": 159,
                },
                {
                    "stage_order": 4,
                    "stage_key": "signed_not_paid",
                    "cohort_name": "signed_not_paid",
                    "lead_count": 2,
                },
                {"stage_order": 5, "stage_key": "paid_converted", "lead_count": 135},
                {"stage_order": 6, "stage_key": "total_leads", "lead_count": 515},
            ],
        )

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_funnel_snapshot(org_id="org_1")

        self.assertEqual(result["status"], "validation_failed")
        self.assertEqual(result["stuck_group_funnel"], [])
        self.assertEqual(result["funnel_stage_validation"]["stage_total"], 530)
        self.assertEqual(result["funnel_stage_validation"]["total_leads"], 515)
        self.assertFalse(result["funnel_stage_validation"]["stage_counts_reconcile"])
        self.assertEqual(
            result["safe_message"],
            (
                "Funnel stage counts could not be reconciled because final stage rows "
                "do not sum to total leads."
            ),
        )

    def test_final_funnel_stage_priority_assigns_terminal_stages_first(self):
        self.assertEqual(
            diagnostic_tools._final_funnel_stage_key(
                appointment_count=0,
                completed_call_count=0,
                signed_contract_count=0,
                paid_payment_count=1,
            ),
            "paid_converted",
        )
        self.assertEqual(
            diagnostic_tools._final_funnel_stage_key(
                appointment_count=1,
                completed_call_count=0,
                signed_contract_count=1,
                paid_payment_count=0,
            ),
            "signed_not_paid",
        )

    def test_text_reason_tool_rejects_invalid_cohort_without_sql_trace(self):
        result = diagnostic_tools.get_diagnostic_text_reason_snapshot(
            org_id="org_1",
            cohort_name="bad_cohort",
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["tool"], "get_diagnostic_text_reason_snapshot")
        self.assertEqual(result["row_count"], 0)
        self.assertIn("cohort_name must be one of", result["error"])
        self.assertNotIn("SELECT", result["error"].upper())

    def test_funnel_selected_cohort_matches_text_reason_totals(self):
        stuck_group_rows = [
            {
                "stage_order": 1,
                "stage_key": "never_booked",
                "cohort_name": "never_booked",
                "lead_count": 4,
            },
            {
                "stage_order": 2,
                "stage_key": "booked_not_completed",
                "cohort_name": "booked_not_completed",
                "lead_count": 6,
            },
            {
                "stage_order": 3,
                "stage_key": "completed_not_signed",
                "cohort_name": "completed_not_signed",
                "lead_count": 8,
            },
            {
                "stage_order": 4,
                "stage_key": "signed_not_paid",
                "cohort_name": "signed_not_paid",
                "lead_count": 2,
            },
            {"stage_order": 5, "stage_key": "paid_converted", "lead_count": 5},
            {"stage_order": 6, "stage_key": "total_leads", "lead_count": 25},
        ]
        funnel_db = FakeDb(
            rows=_sample_funnel_rows(),
            drop_rows=_sample_drop_reconciliation_rows(),
            stuck_group_rows=stuck_group_rows,
        )
        with patch.object(diagnostic_tools, "get_db", return_value=funnel_db):
            funnel_result = diagnostic_tools.get_diagnostic_funnel_snapshot(org_id="org_1")

        selected = funnel_result["selected_text_reason_cohort"]
        text_rows = [
            {
                "row_type": "coverage",
                "total_cohort_leads": selected["lead_count"],
                "leads_with_text_insights": 7,
                "known_reason_leads": 6,
                "unknown_only_reason_leads": 1,
            },
            {"row_type": "combination", "item_key": "timing_issue", "lead_count": 3},
            {"row_type": "combination", "item_key": "price_or_budget", "lead_count": 3},
            {"row_type": "combination", "item_key": "unknown_reason", "lead_count": 1},
            {
                "row_type": "combination",
                "item_key": "no_text_insight_available",
                "lead_count": 1,
            },
            {"row_type": "issue", "item_key": "timing_issue", "lead_count": 3},
            {"row_type": "issue", "item_key": "price_or_budget", "lead_count": 3},
        ]
        with patch.object(diagnostic_tools, "get_db", return_value=FakeDb(rows=text_rows)):
            text_result = diagnostic_tools.get_diagnostic_text_reason_snapshot(
                org_id="org_1",
                cohort_name=selected["cohort_name"],
            )

        self.assertEqual(selected["cohort_name"], "completed_not_signed")
        self.assertEqual(selected["lead_count"], text_result["cohort"]["total_leads"])
        self.assertEqual(
            selected["lead_count"],
            text_result["reconciliation"]["reason_combination_total"],
        )
        self.assertEqual(
            selected["lead_count"],
            text_result["text_insight_coverage"]["total_cohort_leads"],
        )

    def test_text_reason_limits_are_clamped(self):
        fake_db = FakeDb(rows=_sample_text_reason_rows())

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_text_reason_snapshot(
                org_id="org_1",
                reason_limit=999,
                combination_limit=999,
                subcategory_limit=999,
            )

        self.assertEqual(
            result["display_limits"],
            {
                "reason_limit": 20,
                "combination_limit": 20,
                "subcategory_limit": 20,
            },
        )

        with patch.object(diagnostic_tools, "get_db", return_value=FakeDb(rows=_sample_text_reason_rows())):
            result = diagnostic_tools.get_diagnostic_text_reason_snapshot(
                org_id="org_1",
                reason_limit=0,
                combination_limit=0,
                subcategory_limit=0,
            )

        self.assertEqual(
            result["display_limits"],
            {
                "reason_limit": 1,
                "combination_limit": 1,
                "subcategory_limit": 1,
            },
        )

    def test_text_reason_tool_aggregates_distinct_lead_safe_labels_and_coverage(self):
        fake_db = FakeDb(rows=_sample_text_reason_rows())

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_text_reason_snapshot(
                org_id="org_1",
                cohort_name="completed_not_paid",
            )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["cohort"]["total_leads"], 4)
        self.assertEqual(result["cohort"]["cohort_label"], "Completed call but not paid")
        self.assertEqual(
            result["text_insight_coverage"],
            {
                "total_cohort_leads": 4,
                "leads_with_text_insights": 3,
                "leads_without_text_insights": 1,
                "text_insight_coverage_rate": 75.0,
                "known_reason_leads": 2,
                "unknown_only_reason_leads": 1,
                "known_reason_coverage_rate": 50.0,
                "unknown_or_missing_reason_leads": 2,
                "unknown_or_missing_reason_rate": 50.0,
                "coverage_reconciles": True,
            },
        )

        self.assertEqual(result["reason_combination_distribution"], [])
        self.assertIsNone(result["combination_fragmentation_note"])
        self.assertEqual(
            result["default_answer_guidance"],
            {
                "show_issue_combinations_by_default": False,
                "issue_combination_table_returned": False,
                "individual_issue_note": (
                    "One lead can have multiple issues, so the individual issue table "
                    "does not sum to 4."
                ),
            },
        )
        self.assertEqual(
            result["reconciliation"],
            {
                "selected_cohort_leads": 4,
                "reason_combination_total": 4,
                "coverage_total": 4,
                "tables_reconcile": True,
            },
        )
        issue_total = sum(
            row["leads_with_issue"] for row in result["individual_issue_distribution"]
        )
        self.assertGreater(issue_total, result["cohort"]["total_leads"])
        self.assertEqual(
            result["recommended_focus"][0],
            {
                "focus_area": "Price or budget concern",
                "leads_with_issue": 2,
                "share_of_cohort_leads": 50.0,
            },
        )

        issue_labels = {
            row["reason_category_raw"]: row["reason_category"]
            for row in result["individual_issue_distribution"]
        }
        self.assertEqual(issue_labels["timing_issue"], "Not ready yet / needs more time")
        self.assertEqual(issue_labels["price_or_budget"], "Price or budget concern")
        self.assertEqual(
            issue_labels["needs_partner_approval"],
            "Waiting for partner or decision-maker approval",
        )
        self.assertNotIn("unknown", {row["reason_category_raw"] for row in result["individual_issue_distribution"]})

    def test_text_reason_combination_table_is_opt_in_and_stays_at_bottom(self):
        rows = [
            {
                "row_type": "coverage",
                "total_cohort_leads": 20,
                "leads_with_text_insights": 19,
                "known_reason_leads": 17,
                "unknown_only_reason_leads": 2,
            },
            {
                "row_type": "combination",
                "item_key": "unknown_reason",
                "lead_count": 2,
            },
            {
                "row_type": "combination",
                "item_key": "no_text_insight_available",
                "lead_count": 1,
            },
        ]
        rows.extend(
            {
                "row_type": "combination",
                "item_key": f"known_combo_{index}",
                "lead_count": 1,
            }
            for index in range(17)
        )
        fake_db = FakeDb(rows=rows)

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_text_reason_snapshot(
                org_id="org_1",
                cohort_name="completed_not_signed",
                combination_limit=10,
                include_issue_combinations=True,
            )

        combinations = result["reason_combination_distribution"]
        self.assertEqual(result["status"], "success")
        self.assertTrue(
            result["default_answer_guidance"]["issue_combination_table_returned"]
        )
        self.assertEqual(len(combinations), 10)
        self.assertEqual(
            combinations[-1]["issue_combination"],
            "Other lower-volume combinations",
        )
        self.assertEqual(sum(row["lead_count"] for row in combinations), 20)
        self.assertEqual(
            result["combination_fragmentation_note"],
            (
                "Reason combinations are fragmented, so the individual issue view is more "
                "useful than the combination view."
            ),
        )

    def test_text_reason_output_contains_no_raw_or_sensitive_fields(self):
        fake_db = FakeDb(rows=_sample_text_reason_rows())

        with patch.object(diagnostic_tools, "get_db", return_value=fake_db):
            result = diagnostic_tools.get_diagnostic_text_reason_snapshot(org_id="org_1")

        serialized = json.dumps(result, sort_keys=True)
        blocked_terms = (
            "email",
            "phone",
            "raw_payload",
            "meeting_url",
            "recording_url",
            "transcript_url",
            "source_record_id",
            "raw_text",
            "summary_clean",
            "objection_text",
        )
        for blocked_term in blocked_terms:
            with self.subTest(blocked_term=blocked_term):
                self.assertNotIn(blocked_term, serialized)

    def test_diagnostic_sql_is_read_only_scoped_and_sanitized(self):
        sql_texts = [
            diagnostic_tools.SNAPSHOT_DATE_BOUNDS_SQL,
            diagnostic_tools.FUNNEL_SQL,
            diagnostic_tools.DROP_RECONCILIATION_SQL,
            diagnostic_tools.STUCK_GROUP_FUNNEL_SQL,
            diagnostic_tools.MONTHLY_LEAD_TREND_SQL,
            diagnostic_tools.MONTHLY_REVENUE_TREND_SQL,
            diagnostic_tools.MONTHLY_APPOINTMENT_TREND_SQL,
            diagnostic_tools.MONTHLY_SOURCE_LEAD_TREND_SQL_TEMPLATE.format(
                source_column="first_source"
            ),
            diagnostic_tools.MONTHLY_SOURCE_LEAD_TREND_SQL_TEMPLATE.format(
                source_column="last_source"
            ),
            diagnostic_tools.MONTHLY_PROFILE_LEAD_TREND_SQL_TEMPLATE.format(
                profile_column="latest_profession"
            ),
            diagnostic_tools.MONTHLY_PROFILE_LEAD_TREND_SQL_TEMPLATE.format(
                profile_column="latest_employment_status"
            ),
            diagnostic_tools.SOURCE_SNAPSHOT_SQL_TEMPLATE.format(source_column="first_source"),
            diagnostic_tools.SOURCE_SNAPSHOT_SQL_TEMPLATE.format(source_column="last_source"),
            diagnostic_tools.PROFILE_SNAPSHOT_SQL_TEMPLATE.format(
                profile_column="latest_profession",
                order_clause=diagnostic_tools.PROFILE_SNAPSHOT_SORTS["lead_count"],
            ),
            diagnostic_tools.PROFILE_SNAPSHOT_SQL_TEMPLATE.format(
                profile_column="latest_employment_status",
                order_clause=diagnostic_tools.PROFILE_SNAPSHOT_SORTS["paid_lead_rate"],
            ),
            diagnostic_tools.SOURCE_QUALITY_SQL_TEMPLATE.format(source_column="first_source"),
            diagnostic_tools.SOURCE_QUALITY_SQL_TEMPLATE.format(source_column="last_source"),
            diagnostic_tools.BUSINESS_CHANGE_SQL,
            diagnostic_tools.RECOMMENDED_TEXT_COHORTS_SQL,
            diagnostic_tools.TEXT_REASON_SQL_TEMPLATE.format(
                cohort_condition=diagnostic_tools.TEXT_REASON_COHORTS[
                    "completed_not_paid"
                ]["condition"],
            ),
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

        text_sql = diagnostic_tools.TEXT_REASON_SQL_TEMPLATE.format(
            cohort_condition=diagnostic_tools.TEXT_REASON_COHORTS[
                "completed_not_paid"
            ]["condition"],
        )
        self.assertIn("dti.clerk_org_id = sl.clerk_org_id", text_sql)
        self.assertIn("dti.lead_id = sl.lead_id", text_sql)
        self.assertIn("COUNT(DISTINCT lead_id)::int", text_sql)

    def test_explicit_stuck_cohort_definitions_are_shared_by_funnel_and_text_reason(self):
        self.assertIn(
            "WHEN dls.paid_payment_count > 0 THEN 'paid_converted'",
            diagnostic_tools.STUCK_GROUP_FUNNEL_SQL,
        )
        self.assertIn(
            "WHEN dls.signed_contract_count > 0 THEN 'signed_not_paid'",
            diagnostic_tools.STUCK_GROUP_FUNNEL_SQL,
        )
        self.assertIn(
            "WHEN dls.completed_call_count > 0 THEN 'completed_not_signed'",
            diagnostic_tools.STUCK_GROUP_FUNNEL_SQL,
        )
        self.assertIn("COUNT(DISTINCT lead_id)::int AS lead_count", diagnostic_tools.STUCK_GROUP_FUNNEL_SQL)
        self.assertEqual(
            diagnostic_tools.TEXT_REASON_COHORTS["never_booked"]["condition"],
            f"({diagnostic_tools.FINAL_FUNNEL_STAGE_CASE_SQL}) = 'never_booked'",
        )
        self.assertEqual(
            diagnostic_tools.TEXT_REASON_COHORTS["booked_not_completed"]["condition"],
            f"({diagnostic_tools.FINAL_FUNNEL_STAGE_CASE_SQL}) = 'booked_not_completed'",
        )
        self.assertEqual(
            diagnostic_tools.TEXT_REASON_COHORTS["completed_not_signed"]["condition"],
            f"({diagnostic_tools.FINAL_FUNNEL_STAGE_CASE_SQL}) = 'completed_not_signed'",
        )
        self.assertNotIn(
            "dls.completed_call_count > 0 AND dls.signed_contract_count = 0",
            diagnostic_tools.TEXT_REASON_COHORTS["completed_not_signed"]["condition"],
        )


if __name__ == "__main__":
    unittest.main()
