from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.diagnostics import text_extraction_jsonl as extraction


class FakeResponse:
    def __init__(self, insights):
        self.insights = insights

    @classmethod
    def model_validate(cls, value):
        if not isinstance(value, dict):
            raise ValueError("response must be an object")
        insights = value.get("insights")
        if not isinstance(insights, list):
            raise ValueError("insights must be a list")
        for insight in insights:
            if insight.get("reason_category") == "not_a_valid_enum":
                raise ValueError("invalid enum")
        return cls(insights)

    def model_dump(self, mode="json"):
        return {"insights": self.insights}


class TextExtractionJsonlTests(unittest.TestCase):
    def test_clean_text_removes_contact_links_and_provider_ids(self):
        raw = (
            "Email lead@example.com or call +1 (555) 123-4567. "
            "Payment: https://buy.stripe.com/abc Meeting: https://calendly.com/demo "
            "Recording: https://fathom.video/share/abc Transcript: https://example.com/transcript "
            "[case study](https://example.com/case) fathom_call_id abcdefgh123456789"
        )

        cleaned = extraction.clean_text(raw)

        self.assertNotIn("lead@example.com", cleaned)
        self.assertNotIn("555", cleaned)
        self.assertNotIn("https://", cleaned)
        self.assertNotIn("abcdefgh123456789", cleaned)
        self.assertIn("case study", cleaned)

    def test_hash_text_is_stable(self):
        cleaned = "Needs partner approval before paying."

        self.assertEqual(extraction.hash_text(cleaned), extraction.hash_text(cleaned))

    def test_empty_text_returns_skipped_empty(self):
        result = self._process_candidate("   ")

        self.assertEqual(result.row["extraction_status"], "skipped_empty")
        self.assertEqual(result.row["llm_output_json"], {"insights": []})

    def test_duplicate_hash_returns_skipped_duplicate(self):
        candidate = self._candidate("Needs more time to decide.")
        base = extraction._build_base_row(
            candidate,
            cleaned_text=extraction.clean_text(candidate.source_text),
            prompt_path="prompt.yaml",
            schema_path="schema.py",
            extraction_model="test-model",
            extracted_at="2026-05-14T00:00:00Z",
        )
        existing = {extraction.dedupe_key_for_row(base)}

        result = self._process_candidate(candidate.source_text, existing_hashes=existing)

        self.assertEqual(result.row["extraction_status"], "skipped_duplicate")

    def test_valid_llm_output_passes_schema_validation(self):
        raw = {
            "insights": [
                {
                    "reason_category": "price_or_budget",
                    "reason_subcategory": "price_too_high",
                    "is_conversion_blocker": True,
                    "is_human_reason_supported": True,
                    "buying_intent_level": "medium",
                    "lead_quality_level": "medium_quality",
                    "profession_category": "unknown",
                    "employment_status": "unknown",
                }
            ]
        }

        validated = extraction.validate_llm_output(json.dumps(raw), FakeResponse)

        self.assertEqual(validated, raw)

    def test_invalid_enum_fails_validation(self):
        with self.assertRaises(extraction.ExtractionValidationError):
            extraction.validate_llm_output(
                {"insights": [{"reason_category": "not_a_valid_enum"}]},
                FakeResponse,
            )

    def test_empty_insights_are_stored_as_skipped_no_signal(self):
        result = self._process_candidate(
            "Lead is interested but did not share any blocker.",
            llm_callable=lambda _candidate, _cleaned: {"insights": []},
        )

        self.assertEqual(result.row["extraction_status"], "skipped_no_signal")

    def test_jsonl_row_contains_metadata_and_no_raw_text(self):
        result = self._process_candidate(
            "Budget is not available until next month.",
            llm_callable=lambda _candidate, _cleaned: {"insights": []},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "out.jsonl"
            extraction.write_jsonl_row(output_path, result.row)
            row = json.loads(output_path.read_text(encoding="utf-8"))

        for key in [
            "clerk_org_id",
            "lead_id",
            "source_table",
            "source_record_id",
            "source_text_type",
            "source_event_at",
            "source_text_hash",
            "source_text_length",
            "extraction_status",
            "llm_output_json",
            "extraction_model",
            "prompt_path",
            "schema_path",
            "extracted_at",
        ]:
            self.assertIn(key, row)
        self.assertNotIn("source_text", row)
        self.assertNotIn("cleaned_text", row)
        self.assertNotIn("Budget is not available", json.dumps(row))

    def test_dry_run_does_not_call_llm_or_write_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "out.jsonl"
            preview_path = Path(tmpdir) / "preview.md"
            with patch.object(
                extraction,
                "collect_text_candidates",
                return_value=[self._candidate("Needs finance approval before signing.")],
            ), patch.object(extraction, "load_schema_class", return_value=FakeResponse):
                summary = extraction.run_extraction(
                    org_id="org_1",
                    prompt_path="prompt.yaml",
                    schema_path="schema.py",
                    output_path=output_path,
                    preview_md_path=preview_path,
                    dry_run=True,
                    llm_callable=lambda _candidate, _cleaned: self.fail("LLM called"),
                )
            self.assertTrue(summary["dry_run"])
            self.assertEqual(summary["written_jsonl"], 0)
            self.assertFalse(output_path.exists())
            self.assertTrue(preview_path.exists())

    def _candidate(self, source_text: str | None) -> extraction.TextCandidate:
        return extraction.TextCandidate(
            clerk_org_id="org_1",
            lead_id="lead_1",
            source_table="lead_notes",
            source_record_id="note_1",
            source_text_type="lead_note",
            source_event_at="2026-05-14T00:00:00Z",
            source_text=source_text,
        )

    def _process_candidate(
        self,
        source_text: str | None,
        *,
        existing_hashes: set[str] | None = None,
        llm_callable=None,
    ) -> extraction.ExtractionResult:
        return extraction._process_candidate(
            self._candidate(source_text),
            prompt_path="prompt.yaml",
            schema_path="schema.py",
            schema_class=FakeResponse,
            existing_hashes=existing_hashes if existing_hashes is not None else set(),
            min_signal_chars=12,
            max_retries=0,
            extraction_model="test-model",
            llm_callable=llm_callable or (lambda _candidate, _cleaned: {"insights": []}),
            dry_run=False,
        )


if __name__ == "__main__":
    unittest.main()
