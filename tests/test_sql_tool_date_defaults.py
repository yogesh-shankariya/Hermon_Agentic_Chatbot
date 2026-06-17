from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"


def _install_fake_langchain_if_needed() -> None:
    try:
        import langchain.tools  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

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

    langchain_module = sys.modules.get("langchain") or types.ModuleType("langchain")
    langchain_module.__path__ = getattr(langchain_module, "__path__", [])
    tools_module = types.ModuleType("langchain.tools")
    tools_module.tool = fake_tool
    sys.modules["langchain"] = langchain_module
    sys.modules["langchain.tools"] = tools_module


def _load_sql_tools_module():
    _install_fake_langchain_if_needed()
    module_path = APP_DIR / "tools" / "sql_tools.py"
    module_name = "sql_tools_date_defaults_under_test"

    fake_config = types.ModuleType("app.config")
    fake_config.get_sql_agent_settings = lambda: SimpleNamespace(
        default_org_id="org_1",
        enabled_skills=("lead_analytics",),
        max_tool_rows=20,
    )
    fake_config.get_org_timezone = (
        lambda org_id: "Europe/Amsterdam" if org_id == "org_demo" else "UTC"
    )
    fake_db = types.ModuleType("app.db")
    fake_db.QueryValidationError = ValueError
    fake_db.get_db = lambda: None
    fake_skill_loader = types.ModuleType("app.utils.skill_loader")
    fake_skill_loader.SkillRegistryError = ValueError
    fake_skill_loader.load_skill = lambda *args, **kwargs: SimpleNamespace(
        name="lead_analytics",
        content="Skill content",
    )

    originals = {
        name: sys.modules.get(name)
        for name in ("app.config", "app.db", "app.utils.skill_loader")
    }
    sys.modules["app.config"] = fake_config
    sys.modules["app.db"] = fake_db
    sys.modules["app.utils.skill_loader"] = fake_skill_loader

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


class SqlToolDateDefaultTests(unittest.TestCase):
    def test_prompts_default_generic_lead_trend_to_monthly_previous_three_months(self):
        sql_prompt = (APP_DIR / "prompts" / "sql_agent" / "1_0_0.md").read_text(
            encoding="utf-8"
        )
        lead_skill = (
            APP_DIR / "skills" / "modules" / "lead_analytics" / "1_0_0.md"
        ).read_text(encoding="utf-8")

        self.assertIn("If the user asks for a generic trend", sql_prompt)
        self.assertIn("use a monthly lead creation trend over the previous 3 completed months", sql_prompt)
        self.assertIn("Do not use the daily last-10-days default for generic lead trend", sql_prompt)
        self.assertIn(
            "Do not rely on the application fallback for current-month or month-to-date questions",
            sql_prompt,
        )
        self.assertIn("Lead Creation Trend Defaults", lead_skill)
        self.assertIn("use a monthly lead creation trend by default", lead_skill)
        self.assertIn("previous 3 completed months", lead_skill)

    def test_new_leads_with_date_means_created_leads_not_status(self):
        lead_skill = (
            APP_DIR / "skills" / "modules" / "lead_analytics" / "1_0_0.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'When the user asks for "new leads" with a date or date range',
            lead_skill,
        )
        self.assertIn("This matches the dashboard \"New Leads\" metric.", lead_skill)
        self.assertIn("Use `l.created_at` and do not filter by current pipeline status.", lead_skill)
        self.assertIn("Europe/Amsterdam local dates", lead_skill)
        self.assertIn("pass the runtime context current month window as concrete tool params", lead_skill)
        self.assertNotIn(
            'When the user asks for "new leads today", "new leads this week", or "new leads this month", combine',
            lead_skill,
        )

    def test_appointment_dashboard_kpi_rules_use_latest_appointment_per_lead(self):
        appointment_skill = (
            APP_DIR / "skills" / "modules" / "appointment_analytics" / "1_0_0.md"
        ).read_text(encoding="utf-8")
        sql_prompt = (
            APP_DIR / "prompts" / "sql_agent" / "1_0_0.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Dashboard-Aligned KPI Metrics", appointment_skill)
        self.assertIn("docs/dashboard_metrics_reference.md", appointment_skill)
        self.assertIn("Asia/Kolkata", appointment_skill)
        self.assertIn("displayed end date as inclusive", sql_prompt)
        self.assertIn('"end_date":"2026-05-17"', sql_prompt)
        self.assertIn("not the displayed final day", appointment_skill)
        self.assertIn("Deduplicate to the latest appointment per `lead_id`", appointment_skill)
        self.assertIn("latest_appointment_per_lead AS", appointment_skill)
        self.assertIn("SELECT DISTINCT ON (lead_id)", appointment_skill)
        self.assertIn("regardless of outcome", appointment_skill)
        self.assertIn("COUNT(*)::int AS calls_booked", appointment_skill)
        self.assertIn("COUNT(*)::int AS calls_scheduled", appointment_skill)
        self.assertIn("COUNT(*)::int AS calls_taken", appointment_skill)
        self.assertIn("COUNT(*)::int AS no_show", appointment_skill)
        self.assertIn("COUNT(*)::int AS cancelled", appointment_skill)
        self.assertIn("COUNT(*)::int AS rescheduled", appointment_skill)
        self.assertIn("COUNT(*)::int AS follow_up", appointment_skill)
        self.assertIn("COUNT(*)::int AS upcoming", appointment_skill)
        self.assertIn("COUNT(*)::int AS deposit_by_status", appointment_skill)
        self.assertIn("outcome_role NOT IN ('CANCELED', 'RESCHEDULED')", appointment_skill)
        self.assertIn(
            "outcome_role IN ('WON', 'PARTIAL_PAYMENT', 'FOLLOW_UP', 'LOST', 'UNQUALIFIED')",
            appointment_skill,
        )
        self.assertIn("(no_show = true OR outcome_role = 'NO_SHOW')", appointment_skill)
        self.assertIn("outcome_role = 'CANCELED'", appointment_skill)
        self.assertIn("outcome_role = 'RESCHEDULED'", appointment_skill)
        self.assertIn("lead_status_role = 'FOLLOW_UP'", appointment_skill)
        self.assertIn("outcome_role = 'PARTIAL_PAYMENT'", appointment_skill)
        self.assertIn("Raw appointment row counts are still valid only", appointment_skill)

    def test_appointment_calls_taken_rejects_no_show_false_only_logic(self):
        appointment_skill = (
            APP_DIR / "skills" / "modules" / "appointment_analytics" / "1_0_0.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Do not use `a.no_show = false` alone", appointment_skill)
        self.assertIn("require one of the completed outcome roles", appointment_skill)
        self.assertNotIn(
            "a.schedule_time < NOW()\nAND a.no_show = false\n```",
            appointment_skill,
        )
        self.assertNotIn("AND a.no_show = false;", appointment_skill)
        self.assertNotIn("COUNT(*) AS completed_attended_calls", appointment_skill)

    def test_appointment_dashboard_bundle_covers_may_kpi_wording(self):
        appointment_skill = (
            APP_DIR / "skills" / "modules" / "appointment_analytics" / "1_0_0.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            '"new leads, booking rate, booked call, scheduled calls, calls taken, no shows in 1st may to may 15"',
            appointment_skill,
        )
        self.assertIn("WITH new_leads AS", appointment_skill)
        self.assertIn("l.created_at >= :start_date", appointment_skill)
        self.assertIn("a.schedule_time >= :start_date", appointment_skill)
        self.assertIn(
            "ROUND(100.0 * am.calls_booked / NULLIF(nl.new_leads, 0), 2)",
            appointment_skill,
        )
        self.assertIn("COUNT(*)::int AS calls_booked", appointment_skill)
        self.assertIn("am.calls_booked", appointment_skill)
        self.assertIn("am.calls_scheduled", appointment_skill)
        self.assertIn("am.calls_taken", appointment_skill)
        self.assertIn("am.no_show", appointment_skill)

    def test_plain_show_rate_defaults_to_dashboard_booked_show_rate(self):
        appointment_skill = (
            APP_DIR / "skills" / "modules" / "appointment_analytics" / "1_0_0.md"
        ).read_text(encoding="utf-8")
        dashboard_reference = (
            PROJECT_ROOT / "docs" / "dashboard_metrics_reference.md"
        ).read_text(encoding="utf-8")

        self.assertIn("plain \"show rate\"", appointment_skill)
        self.assertIn("Show Rate (Booked)", appointment_skill)
        self.assertIn("show_rate_booked_percent", appointment_skill)
        self.assertIn("show_rate_scheduled_percent", appointment_skill)
        self.assertIn(
            "/ NULLIF(COUNT(*), 0)",
            appointment_skill,
        )
        self.assertIn(
            'plain "show rate" -> `adjusted_show_rate_percent` / Show Rate (Booked)',
            dashboard_reference,
        )

    def test_cancelled_and_cancel_rate_use_latest_per_lead_dashboard_logic(self):
        appointment_skill = (
            APP_DIR / "skills" / "modules" / "appointment_analytics" / "1_0_0.md"
        ).read_text(encoding="utf-8")
        dashboard_reference = (
            PROJECT_ROOT / "docs" / "dashboard_metrics_reference.md"
        ).read_text(encoding="utf-8")

        self.assertIn("`cancelled`: count latest-per-lead rows", appointment_skill)
        self.assertIn("unique leads whose latest appointment outcome is canceled", appointment_skill)
        self.assertIn("not raw canceled appointment rows", appointment_skill)
        self.assertIn("Dashboard-style cancelled calls", appointment_skill)
        self.assertIn("Dashboard-style cancel rate", appointment_skill)
        self.assertIn(
            "* COUNT(*) FILTER (WHERE outcome_role = 'CANCELED')",
            appointment_skill,
        )
        self.assertIn(
            "/ NULLIF(COUNT(*), 0)",
            appointment_skill,
        )
        self.assertIn(
            "Do not count raw cancellation rows unless the user explicitly asks",
            appointment_skill,
        )
        self.assertIn(
            "| `cancelled` | Cancelled | number | Unique leads whose latest appointment outcome is 'canceled'.",
            dashboard_reference,
        )
        self.assertIn(
            "| `cancel_rate_percent` | Cancel Rate | percent | cancelled / calls_booked * 100.",
            dashboard_reference,
        )

    def test_secondary_dashboard_appointment_kpis_use_latest_per_lead_logic(self):
        appointment_skill = (
            APP_DIR / "skills" / "modules" / "appointment_analytics" / "1_0_0.md"
        ).read_text(encoding="utf-8")
        dashboard_reference = (
            PROJECT_ROOT / "docs" / "dashboard_metrics_reference.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Dashboard-style rescheduled calls", appointment_skill)
        self.assertIn("Dashboard-style follow-up", appointment_skill)
        self.assertIn("Dashboard-style upcoming calls", appointment_skill)
        self.assertIn("Dashboard-style deposit status", appointment_skill)
        self.assertIn("l.next_touch_point_at", appointment_skill)
        self.assertIn("lead_status.role", appointment_skill)
        self.assertIn("next_touch_point_at IS NOT NULL", appointment_skill)
        self.assertIn("lead_status_role = 'FOLLOW_UP'", appointment_skill)
        self.assertIn("schedule_time > NOW()", appointment_skill)
        self.assertIn(
            "use the dashboard-aligned latest-per-lead definitions above",
            appointment_skill,
        )
        self.assertIn(
            "| `rescheduled` | Rescheduled | number | Unique leads whose latest past appointment outcome is 'rescheduled'.",
            dashboard_reference,
        )
        self.assertIn(
            "| `follow_up` | Follow Up | number | Unique leads whose latest appointment outcome is 'no-sale-follow-up'",
            dashboard_reference,
        )
        self.assertIn(
            "| `deposit_by_status` | Deposit | number | Unique leads whose latest past appointment outcome is 'deposit'.",
            dashboard_reference,
        )

    def test_revenue_new_cash_collected_uses_first_payment_and_deposit_gross(self):
        revenue_skill = (
            APP_DIR / "skills" / "modules" / "revenue_analytics" / "1_0_0.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Dashboard New Cash Collected", revenue_skill)
        self.assertIn("p.type IN ('FIRST_PAYMENT', 'DEPOSIT')", revenue_skill)
        self.assertIn("do not subtract refunds", revenue_skill)
        self.assertIn("not first payments only", revenue_skill)
        self.assertIn(
            "COALESCE(SUM(p.amount), 0) / 100.0 AS new_cash_collected",
            revenue_skill,
        )
        self.assertIn("p.paid_at >= :start_date", revenue_skill)
        self.assertIn("p.paid_at < :end_date", revenue_skill)

    def test_revenue_cash_collected_subtracts_only_associated_refunds(self):
        revenue_skill = (
            APP_DIR / "skills" / "modules" / "revenue_analytics" / "1_0_0.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "subtract associated succeeded refunds attached to those included paid payments",
            revenue_skill,
        )
        self.assertIn(
            "do not subtract refunds for payments outside the included paid base",
            revenue_skill,
        )
        self.assertIn("paid_payment_rows AS", revenue_skill)
        self.assertIn("JOIN paid_payment_rows pp", revenue_skill)
        self.assertIn("pp.payment_id = r.payment_id", revenue_skill)
        self.assertIn(
            "pp.gross_paid_amount - sr.refunded_amount AS cash_collected",
            revenue_skill,
        )

    def test_plain_close_rate_defaults_to_dashboard_taken_close_rate(self):
        revenue_skill = (
            APP_DIR / "skills" / "modules" / "revenue_analytics" / "1_0_0.md"
        ).read_text(encoding="utf-8")
        dashboard_reference = (
            PROJECT_ROOT / "docs" / "dashboard_metrics_reference.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Dashboard Close Rate Metrics", revenue_skill)
        self.assertIn("plain \"close rate\"", revenue_skill)
        self.assertIn("contract_signed / calls_taken * 100", revenue_skill)
        self.assertIn("Do not use generic contract signed rate", revenue_skill)
        self.assertIn("Dashboard Close Rate Taken in a Date Range", revenue_skill)
        self.assertIn(
            "ROUND(100.0 * sc.contract_signed / NULLIF(am.calls_taken, 0), 2)",
            revenue_skill,
        )
        self.assertIn("close_rate_taken_percent", revenue_skill)
        self.assertIn("Dashboard Revenue KPI Bundle in a Date Range", revenue_skill)
        self.assertIn("show_rate_booked_percent", revenue_skill)
        self.assertIn(
            'plain "close rate" -> `closing_rate_taken_percent` / Close Rate (Taken)',
            dashboard_reference,
        )

    def test_revenue_closed_without_call_uses_signed_contracts_missing_period_appointments(self):
        revenue_skill = (
            APP_DIR / "skills" / "modules" / "revenue_analytics" / "1_0_0.md"
        ).read_text(encoding="utf-8")
        dashboard_reference = (
            PROJECT_ROOT / "docs" / "dashboard_metrics_reference.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Dashboard Closed Without Call", revenue_skill)
        self.assertIn("signed contracts in the selected period using `c.signed_at`", revenue_skill)
        self.assertIn("Deduplicate appointments to the latest appointment per lead", revenue_skill)
        self.assertIn("latest_appointment_per_lead AS", revenue_skill)
        self.assertIn("SELECT DISTINCT ON (lead_id)", revenue_skill)
        self.assertIn("COUNT(*) FILTER (WHERE lapl.lead_id IS NULL)::int AS closed_without_call", revenue_skill)
        self.assertIn("LEFT JOIN latest_appointment_per_lead lapl", revenue_skill)
        self.assertIn(
            "| `closed_without_call` | Closed Without Call | number | Signed contracts whose lead had no appointment in the period.",
            dashboard_reference,
        )

    def test_non_trend_start_end_defaults_to_previous_completed_month(self):
        module = _load_sql_tools_module()

        class FakeDate(date):
            @classmethod
            def today(cls):
                return cls(2026, 5, 9)

        module.date = FakeDate
        params = {}
        module._apply_default_date_window(
            "SELECT COUNT(*) FROM leads WHERE created_at >= :start_date AND created_at < :end_date",
            params,
        )

        self.assertEqual(
            params,
            {
                "start_date": "2026-04-01",
                "end_date": "2026-05-01",
            },
        )

    def test_trend_start_end_keeps_existing_trend_defaults(self):
        module = _load_sql_tools_module()

        class FakeDate(date):
            @classmethod
            def today(cls):
                return cls(2026, 5, 9)

        module.date = FakeDate
        params = {}
        module._apply_default_date_window(
            """
            SELECT date_trunc('month', l.created_at) AS month
            FROM leads l
            WHERE l.created_at >= :start_date AND l.created_at < :end_date
            """,
            params,
        )

        self.assertEqual(
            params,
            {
                "start_date": "2026-02-01",
                "end_date": "2026-05-01",
            },
        )

    def test_existing_date_params_are_not_overwritten(self):
        module = _load_sql_tools_module()
        params = {"start_date": "2026-03-01", "end_date": "2026-04-01"}
        module._apply_default_date_window(
            "SELECT COUNT(*) FROM leads WHERE created_at >= :start_date AND created_at < :end_date",
            params,
        )

        self.assertEqual(
            params,
            {
                "start_date": "2026-03-01",
                "end_date": "2026-04-01",
            },
        )

    def test_run_readonly_sql_uses_active_org_context_over_default_and_params(self):
        module = _load_sql_tools_module()
        from app.org_context import active_org_context, get_active_org_id

        calls = []

        class FakeDb:
            def query_records(self, sql, params, *, max_rows, timezone_name=None):
                calls.append(
                    {
                        "sql": sql,
                        "params": dict(params),
                        "max_rows": max_rows,
                        "timezone_name": timezone_name,
                    }
                )
                return [{"seen_org_id": params["org_id"]}]

        module.get_db = lambda: FakeDb()
        module.get_sql_agent_settings = lambda: SimpleNamespace(
            default_org_id=get_active_org_id() or "org_live",
            enabled_skills=("lead_analytics",),
            max_tool_rows=20,
        )

        with active_org_context("org_demo"):
            response = module.run_readonly_sql.invoke(
                {
                    "query": "SELECT COUNT(*) FROM leads WHERE clerk_org_id = :org_id",
                    "params_json": '{"org_id": "org_bad"}',
                }
            )

        payload = json.loads(response)
        self.assertTrue(payload["ok"])
        self.assertEqual(calls[0]["params"]["org_id"], "org_demo")
        self.assertEqual(payload["effective_params"]["org_id"], "org_demo")
        self.assertEqual(payload["rows"], [{"seen_org_id": "org_demo"}])
        self.assertEqual(calls[0]["timezone_name"], "Europe/Amsterdam")
        self.assertEqual(payload["effective_params"]["timezone"], "Europe/Amsterdam")

    def test_run_readonly_sql_defaults_dates_from_org_local_today(self):
        module = _load_sql_tools_module()
        calls = []

        class FakeDb:
            def query_records(self, sql, params, *, max_rows, timezone_name=None):
                calls.append(
                    {
                        "sql": sql,
                        "params": dict(params),
                        "max_rows": max_rows,
                        "timezone_name": timezone_name,
                    }
                )
                return [{"lead_count": 12}]

        module.get_db = lambda: FakeDb()
        module.get_sql_agent_settings = lambda: SimpleNamespace(
            default_org_id="org_demo",
            enabled_skills=("lead_analytics",),
            max_tool_rows=20,
        )
        module._today_in_timezone = lambda timezone_name: date(2026, 5, 9)

        response = module.run_readonly_sql.invoke(
            {
                "query": (
                    "SELECT COUNT(*) AS lead_count FROM leads "
                    "WHERE clerk_org_id = :org_id "
                    "AND created_at >= :start_date "
                    "AND created_at < :end_date"
                ),
            }
        )

        payload = json.loads(response)
        self.assertTrue(payload["ok"])
        self.assertEqual(calls[0]["timezone_name"], "Europe/Amsterdam")
        self.assertEqual(
            calls[0]["params"],
            {
                "org_id": "org_demo",
                "limit": 20,
                "start_date": "2026-04-01",
                "end_date": "2026-05-01",
            },
        )
        self.assertEqual(payload["effective_params"]["timezone"], "Europe/Amsterdam")
        self.assertEqual(payload["effective_params"]["start_date"], "2026-04-01")
        self.assertEqual(payload["effective_params"]["end_date"], "2026-05-01")

    def test_run_readonly_sql_uses_active_request_timezone_over_org_config(self):
        module = _load_sql_tools_module()
        from app.org_context import active_org_context

        calls = []

        class FakeDb:
            def query_records(self, sql, params, *, max_rows, timezone_name=None):
                calls.append(
                    {
                        "params": dict(params),
                        "timezone_name": timezone_name,
                    }
                )
                return [{"lead_count": 96}]

        module.get_db = lambda: FakeDb()
        module.get_sql_agent_settings = lambda: SimpleNamespace(
            default_org_id="org_new",
            enabled_skills=("lead_analytics",),
            max_tool_rows=20,
        )
        module.get_org_timezone = lambda org_id: "UTC"
        module._today_in_timezone = lambda timezone_name: date(2026, 6, 9)

        with active_org_context("org_new", timezone_name="Europe/Amsterdam"):
            response = module.run_readonly_sql.invoke(
                {
                    "query": (
                        "SELECT COUNT(*) AS lead_count FROM leads "
                        "WHERE clerk_org_id = :org_id "
                        "AND created_at >= :start_date "
                        "AND created_at < :end_date"
                    ),
                    "params_json": '{"start_date":"2026-06-01","end_date":"2026-07-01"}',
                }
            )

        payload = json.loads(response)
        self.assertTrue(payload["ok"])
        self.assertEqual(calls[0]["timezone_name"], "Europe/Amsterdam")
        self.assertEqual(payload["effective_params"]["timezone"], "Europe/Amsterdam")
        self.assertEqual(payload["rows"], [{"lead_count": 96}])


if __name__ == "__main__":
    unittest.main()
