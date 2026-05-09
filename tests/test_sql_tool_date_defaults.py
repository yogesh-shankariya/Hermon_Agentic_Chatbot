from __future__ import annotations

import importlib.util
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


if __name__ == "__main__":
    unittest.main()
