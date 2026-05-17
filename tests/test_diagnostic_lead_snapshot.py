from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace


def _load_lead_snapshot_module():
    module_path = Path(__file__).resolve().parents[1] / "app" / "diagnostics" / "lead_snapshot.py"
    module_name = "diagnostic_lead_snapshot_under_test"

    fake_sqlalchemy = types.ModuleType("sqlalchemy")
    fake_sqlalchemy.create_engine = lambda *args, **kwargs: object()
    fake_sqlalchemy.text = lambda sql: sql

    fake_sqlalchemy_engine = types.ModuleType("sqlalchemy.engine")
    fake_sqlalchemy_engine.Connection = object
    fake_sqlalchemy_engine.Engine = object

    fake_config = types.ModuleType("app.config")
    fake_config.get_database_settings = lambda: SimpleNamespace(database_url="postgresql://example")

    originals = {
        "sqlalchemy": sys.modules.get("sqlalchemy"),
        "sqlalchemy.engine": sys.modules.get("sqlalchemy.engine"),
        "app.config": sys.modules.get("app.config"),
    }
    sys.modules["sqlalchemy"] = fake_sqlalchemy
    sys.modules["sqlalchemy.engine"] = fake_sqlalchemy_engine
    sys.modules["app.config"] = fake_config

    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


lead_snapshot = _load_lead_snapshot_module()


class DiagnosticLeadSnapshotSqlTests(unittest.TestCase):
    def test_static_builder_uses_force_guardrails(self):
        self.assertIn("build_diagnostic_lead_snapshot_once", dir(lead_snapshot))
        self.assertNotIn("refresh_diagnostic_lead_snapshot", dir(lead_snapshot))

        source = lead_snapshot.build_diagnostic_lead_snapshot_once.__doc__ or ""
        self.assertIn("Without ``force``", source)
        self.assertIn("With ``force``", source)

    def test_table_schema_contains_expected_constraints_and_columns(self):
        ddl = lead_snapshot.CREATE_TABLE_SQL

        self.assertIn("snapshot_built_at", ddl)
        self.assertIn("past_non_no_show_appointment_count", ddl)
        self.assertIn("completed_calls_missing_fathom_count", ddl)
        self.assertIn("completed_call_fathom_coverage_rate", ddl)
        self.assertIn("contract_sent_lifecycle_count", ddl)
        self.assertIn("latest_profession text", ddl)
        self.assertIn("latest_employment_status text", ddl)
        alter_sql = "\n".join(lead_snapshot.ALTER_TABLE_SQL)
        self.assertIn("ADD COLUMN IF NOT EXISTS latest_profession TEXT", alter_sql)
        self.assertIn("ADD COLUMN IF NOT EXISTS latest_employment_status TEXT", alter_sql)
        self.assertIn("CONSTRAINT uq_dls_org_lead", ddl)
        self.assertIn("CONSTRAINT chk_dls_source_confidence", ddl)
        self.assertIn("CONSTRAINT chk_dls_funnel_stage", ddl)
        self.assertIn("CONSTRAINT chk_dls_conversion_outcome", ddl)
        self.assertIn("CONSTRAINT chk_dls_contract_currency_eur", ddl)
        self.assertIn("CONSTRAINT chk_dls_payment_currency_eur", ddl)

    def test_insert_sql_matches_diagnostic_metric_rules(self):
        sql = lead_snapshot.INSERT_SNAPSHOT_SQL

        self.assertIn("NOT IN ('CANCELED', 'RESCHEDULED')", sql)
        self.assertIn("past_non_no_show_appointment_count", sql)
        self.assertIn("completed_calls_missing_fathom_count", sql)
        self.assertIn("completed_call_fathom_coverage_rate", sql)
        self.assertIn("contract_sent_lifecycle_count", sql)
        self.assertIn("NULLIF(BTRIM(a.snapshot_event_name), '')", sql)
        self.assertIn("aet.event_type_name", sql)
        self.assertIn("Unknown Event Type", sql)
        self.assertIn("SUM(COALESCE(pr.amount, 0)) FILTER (WHERE pr.status::text = 'PAID') / 100.0", sql)
        self.assertIn("SUM(COALESCE(r.amount, 0)) FILTER (WHERE r.status::text = 'SUCCEEDED') / 100.0", sql)
        self.assertIn("latest_profession AS", sql)
        self.assertIn("latest_employment_status AS", sql)
        self.assertIn("LOWER(BTRIM(q.question)) = LOWER('What do you do for work?')", sql)
        self.assertIn(
            "LOWER(BTRIM(q.question)) = LOWER('What is your employment status?')",
            sql,
        )
        self.assertIn("COALESCE(q.created_at, o.created_at) DESC", sql)
        self.assertIn("fs.latest_profession", sql)
        self.assertIn("fs.latest_employment_status", sql)
        self.assertNotIn("contract_viewed_lifecycle_count", sql)

    def test_validation_checks_exact_one_row_and_json_flags(self):
        sql = lead_snapshot.VALIDATION_SQL

        self.assertIn("missing_active_lead_snapshot", sql)
        self.assertIn("extra_snapshot_without_active_lead", sql)
        self.assertIn("duplicate_org_lead_rows", sql)
        self.assertIn("json_flag_array_contains_null", sql)
        self.assertIn("blank_latest_profession", sql)
        self.assertIn("blank_latest_employment_status", sql)

    def test_plain_postgres_urls_use_installed_psycopg_driver(self):
        self.assertEqual(
            lead_snapshot._sqlalchemy_psycopg_url("postgresql://user:pass@example/db"),
            "postgresql+psycopg://user:pass@example/db",
        )
        self.assertEqual(
            lead_snapshot._sqlalchemy_psycopg_url("postgres://user:pass@example/db"),
            "postgresql+psycopg://user:pass@example/db",
        )
        self.assertEqual(
            lead_snapshot._sqlalchemy_psycopg_url("postgresql+psycopg://user:pass@example/db"),
            "postgresql+psycopg://user:pass@example/db",
        )


if __name__ == "__main__":
    unittest.main()
