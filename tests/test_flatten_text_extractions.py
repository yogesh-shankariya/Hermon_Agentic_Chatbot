from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.diagnostics import flatten_text_extractions as flatten


ORG_ID = "org_1"
OTHER_ORG_ID = "org_2"
LEAD_ID = "11111111-1111-4111-8111-111111111111"
SOURCE_RECORD_ID = "22222222-2222-4222-8222-222222222222"


class FakeResult:
    def __init__(self, rowcount: int):
        self.rowcount = rowcount


class FakeConnection:
    def __init__(self, insert_rowcounts: list[int] | None = None):
        self.insert_rowcounts = list(insert_rowcounts or [])
        self.statements: list[tuple[str, dict | None]] = []
        self.inserted_rows: list[dict] = []

    def execute(self, statement, params=None):
        sql = str(statement)
        self.statements.append((sql, params))
        if "DELETE FROM diagnostic_text_insights" in sql:
            return FakeResult(3)
        if "INSERT INTO diagnostic_text_insights" in sql:
            self.inserted_rows.append(dict(params or {}))
            rowcount = self.insert_rowcounts.pop(0) if self.insert_rowcounts else 1
            return FakeResult(rowcount)
        return FakeResult(0)


class FakeBegin:
    def __init__(self, connection: FakeConnection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeEngine:
    def __init__(self, connection: FakeConnection):
        self.connection = connection

    def begin(self):
        return FakeBegin(self.connection)


class FlattenTextExtractionsTests(unittest.TestCase):
    def test_one_insight_creates_one_table_row(self):
        with self._jsonl_file([self._jsonl_row([self._insight()])]) as path:
            rows, summary = flatten.collect_insert_rows(path, org_id=ORG_ID)

        self.assertEqual(len(rows), 1)
        self.assertEqual(summary.insights_seen, 1)
        self.assertEqual(rows[0]["reason_category"], "price_or_budget")

    def test_multiple_insights_create_multiple_table_rows(self):
        with self._jsonl_file(
            [
                self._jsonl_row(
                    [
                        self._insight(reason_category="price_or_budget"),
                        self._insight(reason_category="timing_issue"),
                    ]
                )
            ]
        ) as path:
            rows, summary = flatten.collect_insert_rows(path, org_id=ORG_ID)

        self.assertEqual(len(rows), 2)
        self.assertEqual(summary.insights_seen, 2)

    def test_empty_insights_and_non_success_create_zero_rows(self):
        with self._jsonl_file(
            [
                self._jsonl_row([], extraction_status="success"),
                self._jsonl_row([self._insight()], extraction_status="skipped_no_signal"),
            ]
        ) as path:
            rows, summary = flatten.collect_insert_rows(path, org_id=ORG_ID)

        self.assertEqual(rows, [])
        self.assertEqual(summary.success_jsonl_rows, 1)
        self.assertEqual(summary.non_success_jsonl_rows_skipped, 1)

    def test_is_human_reason_supported_is_ignored(self):
        with self._jsonl_file(
            [self._jsonl_row([self._insight(is_human_reason_supported=False)])]
        ) as path:
            rows, _summary = flatten.collect_insert_rows(path, org_id=ORG_ID)

        self.assertNotIn("is_human_reason_supported", rows[0])
        self.assertEqual(rows[0]["reason_category"], "price_or_budget")
        self.assertTrue(rows[0]["is_conversion_blocker"])

    def test_missing_optional_insight_fields_use_defaults(self):
        with self._jsonl_file([self._jsonl_row([{}])]) as path:
            rows, summary = flatten.collect_insert_rows(path, org_id=ORG_ID)

        self.assertEqual(summary.validation_errors, 0)
        self.assertEqual(rows[0]["reason_category"], "unknown")
        self.assertEqual(rows[0]["reason_subcategory"], "unknown")
        self.assertFalse(rows[0]["is_conversion_blocker"])
        self.assertEqual(rows[0]["buying_intent_level"], "unknown")
        self.assertEqual(rows[0]["lead_quality_level"], "unknown")
        self.assertEqual(rows[0]["profession_category"], "unknown")
        self.assertEqual(rows[0]["employment_status"], "unknown")

    def test_invalid_enum_is_validation_error_and_skipped(self):
        with self._jsonl_file(
            [self._jsonl_row([self._insight(reason_category="made_up")])]
        ) as path:
            rows, summary = flatten.collect_insert_rows(path, org_id=ORG_ID)

        self.assertEqual(rows, [])
        self.assertEqual(summary.validation_errors, 1)

    def test_duplicate_rows_are_skipped(self):
        duplicate = self._insight()
        with self._jsonl_file([self._jsonl_row([duplicate, duplicate])]) as path:
            rows, summary = flatten.collect_insert_rows(path, org_id=ORG_ID)

        self.assertEqual(len(rows), 1)
        self.assertEqual(summary.duplicates_skipped, 1)

    def test_dry_run_does_not_insert(self):
        with self._jsonl_file([self._jsonl_row([self._insight()])]) as path:
            summary = flatten.run_flatten(
                input_path=path,
                org_id=ORG_ID,
                dry_run=True,
                engine=self._failing_engine(),
            )

        self.assertTrue(summary["dry_run"])
        self.assertEqual(summary["insights_inserted"], 1)

    def test_force_deletes_only_selected_org(self):
        connection = FakeConnection()
        engine = FakeEngine(connection)
        with self._jsonl_file([self._jsonl_row([self._insight()])]) as path:
            summary = flatten.run_flatten(
                input_path=path,
                org_id=ORG_ID,
                force=True,
                engine=engine,
            )

        delete_calls = [
            params
            for sql, params in connection.statements
            if "DELETE FROM diagnostic_text_insights" in sql
        ]
        self.assertEqual(delete_calls, [{"org_id": ORG_ID}])
        self.assertEqual(summary["rows_deleted"], 3)
        self.assertEqual(summary["insights_inserted"], 1)

    def test_insert_payload_contains_no_raw_or_path_fields(self):
        raw_row = self._jsonl_row([self._insight()])
        raw_row["source_text"] = "Raw text must not be inserted"
        raw_row["cleaned_text"] = "Cleaned text must not be inserted"
        raw_row["llm_output_json"]["extra"] = "raw payload"
        raw_row["prompt_path"] = "/Users/example/prompt.yaml"
        raw_row["schema_path"] = "/Users/example/schema.py"
        raw_row["extraction_error"] = "unsafe detail"

        with self._jsonl_file([raw_row]) as path:
            rows, _summary = flatten.collect_insert_rows(path, org_id=ORG_ID)

        serialized = json.dumps(rows[0], sort_keys=True)
        self.assertNotIn("Raw text must not be inserted", serialized)
        self.assertNotIn("Cleaned text must not be inserted", serialized)
        self.assertNotIn("raw payload", serialized)
        self.assertNotIn("/Users/example", serialized)
        self.assertNotIn("unsafe detail", serialized)
        self.assertNotIn("llm_output_json", rows[0])
        self.assertNotIn("prompt_path", rows[0])
        self.assertNotIn("schema_path", rows[0])

    def test_rows_are_tenant_scoped_by_org_id(self):
        with self._jsonl_file(
            [
                self._jsonl_row([self._insight()], clerk_org_id=OTHER_ORG_ID),
                self._jsonl_row([self._insight()], clerk_org_id=ORG_ID),
            ]
        ) as path:
            rows, summary = flatten.collect_insert_rows(path, org_id=ORG_ID)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["clerk_org_id"], ORG_ID)
        self.assertEqual(summary.jsonl_rows_read, 2)
        self.assertEqual(summary.jsonl_rows_for_org, 1)

    def _jsonl_file(self, rows: list[dict]):
        tempdir = tempfile.TemporaryDirectory()
        path = Path(tempdir.name) / "input.jsonl"
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )

        class _ManagedPath:
            def __enter__(self_nonlocal):
                return path

            def __exit__(self_nonlocal, exc_type, exc, traceback):
                tempdir.cleanup()
                return False

        return _ManagedPath()

    def _jsonl_row(
        self,
        insights: list[dict],
        *,
        clerk_org_id: str = ORG_ID,
        extraction_status: str = "success",
    ) -> dict:
        return {
            "clerk_org_id": clerk_org_id,
            "lead_id": LEAD_ID,
            "source_table": "lead_notes",
            "source_record_id": SOURCE_RECORD_ID,
            "source_text_type": "lead_note",
            "source_event_at": "2026-05-14T00:00:00Z",
            "source_text_hash": "abc123",
            "source_text_length": 42,
            "extraction_status": extraction_status,
            "llm_output_json": {"insights": insights},
            "extracted_at": "2026-05-14T01:00:00Z",
        }

    def _insight(self, **overrides) -> dict:
        insight = {
            "reason_category": "price_or_budget",
            "reason_subcategory": "price_too_high",
            "is_conversion_blocker": True,
            "is_human_reason_supported": False,
            "buying_intent_level": "medium",
            "lead_quality_level": "medium_quality",
            "profession_category": "unknown",
            "employment_status": "unknown",
        }
        insight.update(overrides)
        return insight

    def _failing_engine(self):
        class FailingEngine:
            def begin(self):
                raise AssertionError("dry-run should not open a database connection")

        return FailingEngine()


if __name__ == "__main__":
    unittest.main()
