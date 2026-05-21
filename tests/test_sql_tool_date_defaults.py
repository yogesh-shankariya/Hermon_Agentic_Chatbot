from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace


APP_DIR = Path(__file__).resolve().parents[1] / "app"


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
        sql_prompt = (APP_DIR / "prompts" / "sql_agent" / "1_0_0.yaml").read_text(
            encoding="utf-8"
        )
        lead_skill = (APP_DIR / "skills" / "modules" / "lead_analytics.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("If the user asks for a generic trend", sql_prompt)
        self.assertIn("use a monthly lead creation trend over the previous 3 completed months", sql_prompt)
        self.assertIn("Do not use the daily last-10-days default for generic lead trend", sql_prompt)
        self.assertIn("Lead Creation Trend Defaults", lead_skill)
        self.assertIn("use a monthly lead creation trend by default", lead_skill)
        self.assertIn("previous 3 completed months", lead_skill)

    def test_new_leads_with_date_means_created_leads_not_status(self):
        lead_skill = (APP_DIR / "skills" / "modules" / "lead_analytics.md").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            'When the user asks for "new leads" with a date or date range',
            lead_skill,
        )
        self.assertIn("This matches the dashboard \"New Leads\" metric.", lead_skill)
        self.assertIn("Use `l.created_at` and do not filter by current pipeline status.", lead_skill)
        self.assertIn("Europe/Amsterdam local dates", lead_skill)
        self.assertNotIn(
            'When the user asks for "new leads today", "new leads this week", or "new leads this month", combine',
            lead_skill,
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
            def query_records(self, sql, params, *, max_rows):
                calls.append({"sql": sql, "params": dict(params), "max_rows": max_rows})
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


if __name__ == "__main__":
    unittest.main()
