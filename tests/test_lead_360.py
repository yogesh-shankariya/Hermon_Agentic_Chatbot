from __future__ import annotations

import importlib.util
import json
import re
import sys
import threading
import time
import types
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


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

        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)

        def invoke(self, args):
            return self.func(**args)

    def fake_tool(*args, **kwargs):
        if args and callable(args[0]):
            return FakeTool(args[0], kwargs.get("name"))

        name = args[0] if args else kwargs.get("name")

        def decorator(func):
            return FakeTool(func, name)

        return decorator

    langchain_module = types.ModuleType("langchain")
    tools_module = types.ModuleType("langchain.tools")
    tools_module.tool = fake_tool
    sys.modules.setdefault("langchain", langchain_module)
    sys.modules.setdefault("langchain.tools", tools_module)


def _load_lead_360_module():
    _install_fake_langchain_if_needed()
    module_path = Path(__file__).resolve().parents[1] / "app" / "tools" / "lead_360.py"
    module_name = "lead_360_under_test"

    fake_config = types.ModuleType("app.config")
    fake_config.get_sql_agent_settings = lambda: SimpleNamespace(default_org_id=None)
    fake_db = types.ModuleType("app.db")
    fake_db.get_db = lambda: None

    originals = {
        "app.config": sys.modules.get("app.config"),
        "app.db": sys.modules.get("app.db"),
    }
    sys.modules["app.config"] = fake_config
    sys.modules["app.db"] = fake_db

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


lead_360 = _load_lead_360_module()

LEAD_ID = "11111111-1111-1111-1111-111111111111"
OTHER_LEAD_ID = "22222222-2222-2222-2222-222222222222"


def dt(day: int, hour: int = 12) -> datetime:
    return datetime(2026, 4, day, hour, tzinfo=timezone.utc)


class FakeDb:
    def __init__(self, resolver_rows: list[dict] | None = None):
        self.resolver_rows = resolver_rows if resolver_rows is not None else [self.resolver_row()]
        self.calls: list[dict] = []

    @staticmethod
    def resolver_row(**overrides) -> dict:
        row = {
            "lead_id": LEAD_ID,
            "display_name": "Vedran",
            "status_name": "No Sale - Follow Up",
            "status_role": "FOLLOW_UP",
            "lead_source": "CALENDLY",
            "created_at": dt(1),
        }
        row.update(overrides)
        return row

    def query_records(self, sql: str, params: dict | None = None, *, max_rows: int | None = None):
        self.calls.append({"sql": sql, "params": params or {}, "max_rows": max_rows})

        if "FROM leads l" in sql and "assigned_to" in sql:
            contact_allowed = "l.email AS email" in sql
            return [
                {
                    "lead_id": LEAD_ID,
                    "display_name": "Vedran",
                    "email": "vedran@example.com" if contact_allowed else None,
                    "phone_e164": "+15551234567" if contact_allowed else None,
                    "status_name": "No Sale - Follow Up",
                    "status_role": "FOLLOW_UP",
                    "lead_source": "CALENDLY",
                    "assigned_to": "user_internal_1",
                    "setter_id": None,
                    "next_touch_point_at": None,
                    "next_touch_point_type": None,
                    "created_at": dt(1),
                    "updated_at": dt(7),
                }
            ]

        if "FROM leads l" in sql and "first_ms" in sql:
            return [
                {
                    "lead_source": "CALENDLY",
                    "first_source": "Unknown",
                    "first_source_name_raw": None,
                    "last_source": "Unknown",
                    "last_source_name_raw": None,
                    "ai_source_summary": None,
                }
            ]

        if "FROM leads l" in sql:
            return self.resolver_rows

        if "FROM opt_ins o" in sql and "traffic_attributions" in sql:
            return [
                {
                    "opt_in_id": "opt_1",
                    "created_at": dt(1),
                    "opt_in_source": "CALENDLY",
                    "provider_form_name": "Qualification Call Freedom Academy (TF)",
                    "utm_source": None,
                    "utm_medium": None,
                    "utm_campaign": None,
                    "utm_content": None,
                    "utm_term": None,
                    "landing_page": None,
                    "referrer": None,
                }
            ]

        if "JOIN opt_in_question_answers q" in sql:
            return [
                {
                    "opt_in_created_at": dt(1),
                    "provider_form_name": "Qualification Call Freedom Academy (TF)",
                    "position": 1,
                    "question": "What problem are you trying to solve?",
                    "answer": "I need predictable income. See https://example.com/private",
                }
            ]

        if "FROM appointments a" in sql and "JOIN fathom_call_records f" not in sql:
            return [
                {
                    "appointment_id": "appt_canceled",
                    "_created_at": dt(2),
                    "schedule_time": dt(3),
                    "event_name": "Strategy Call - Freedom - FU",
                    "call_category": "SALES_CALL",
                    "outcome_name": "Canceled",
                    "outcome_role": "CANCELED",
                    "no_show": False,
                    "appointment_source": "CALENDLY",
                    "host_id": "host_internal",
                    "setter_id": None,
                    "has_fathom_record": False,
                    "meeting_url": None,
                    "recording_url": None,
                },
                {
                    "appointment_id": "appt_call",
                    "_created_at": dt(3),
                    "schedule_time": dt(4),
                    "event_name": "Qualification Call Freedom Academy (TF)",
                    "call_category": "SALES_CALL",
                    "outcome_name": "No Sale - Follow Up",
                    "outcome_role": "FOLLOW_UP",
                    "no_show": False,
                    "appointment_source": "CALENDLY",
                    "host_id": "host_internal",
                    "setter_id": None,
                    "has_fathom_record": True,
                    "meeting_url": None,
                    "recording_url": None,
                },
                {
                    "appointment_id": "appt_no_show",
                    "_created_at": dt(5),
                    "schedule_time": dt(6),
                    "event_name": "Strategy Call - Freedom - NS",
                    "call_category": "SALES_CALL",
                    "outcome_name": "No Show",
                    "outcome_role": "NO_SHOW",
                    "no_show": True,
                    "appointment_source": "CALENDLY",
                    "host_id": "host_internal",
                    "setter_id": None,
                    "has_fathom_record": False,
                    "meeting_url": "https://meet.example/private",
                    "recording_url": "https://recording.example/private",
                },
            ]

        if "JOIN fathom_call_records f" in sql:
            links_allowed = "f.recording_url AS recording_url" in sql
            return [
                {
                    "fathom_record_id": "fathom_1",
                    "appointment_id": "appt_call",
                    "schedule_time": dt(4),
                    "event_name": "Qualification Call Freedom Academy (TF)",
                    "call_started_at": dt(4, 13),
                    "call_ended_at": dt(4, 14),
                    "call_duration_seconds": 1440,
                    "summary": (
                        "## Summary\n"
                        "[**Goal:** Jan wants passive income]"
                        "(https://fathom.video/share/abc?tab=summary&timestamp=94.0)\n"
                        "### Next steps\n"
                        "- Follow up through WhatsApp."
                    ),
                    "key_points": ["[Goal: wants freedom](https://fathom.video/share/def)"],
                    "action_items": ["Send payment reminder https://example.com/pay"],
                    "objections": ["Price"],
                    "ai_rationale": "Warm but stalled.",
                    "ai_confidence_score": Decimal("0.85"),
                    "outcome_applied": False,
                    "has_recording_url": True,
                    "has_transcript_url": False,
                    "recording_url": "https://fathom.video/share/recording" if links_allowed else None,
                    "transcript_url": None,
                },
                {
                    "fathom_record_id": "fathom_2",
                    "appointment_id": "appt_earlier",
                    "schedule_time": dt(2),
                    "event_name": "Earlier Strategy Call",
                    "call_started_at": dt(2, 13),
                    "call_ended_at": dt(2, 13),
                    "call_duration_seconds": 900,
                    "summary": "Discussed initial goals. https://fathom.video/share/older",
                    "key_points": ["Needs clarity"],
                    "action_items": ["Book next call"],
                    "objections": [],
                    "ai_rationale": "Early discovery call.",
                    "ai_confidence_score": Decimal("0.72"),
                    "outcome_applied": True,
                    "has_recording_url": False,
                    "has_transcript_url": True,
                    "recording_url": None,
                    "transcript_url": "https://fathom.video/share/transcript" if links_allowed else None,
                }
            ]

        if "FROM lead_notes ln" in sql:
            return [
                {
                    "note_id": "note_1",
                    "appointment_id": "appt_call",
                    "created_at": dt(7),
                    "note": "Asked to follow up on payment plan. https://example.com/note",
                }
            ]

        if "FROM contracts c" in sql and "JOIN contract_subscriptions cs" not in sql:
            return [
                {
                    "contract_id": "contract_1",
                    "created_at": dt(5),
                    "program_name": "Freedom Academy",
                    "contract_type": "PIF",
                    "contract_status": "DRAFT",
                    "total_value": Decimal("500000"),
                    "currency": "eur",
                    "closer_id": "closer_internal",
                    "setter_id": None,
                    "sent_at": None,
                    "signed_at": None,
                    "voided_at": None,
                    "voided_reason": None,
                }
            ]

        if "FROM payments p" in sql and "GROUP BY p.currency" in sql:
            return [
                {
                    "currency": "eur",
                    "payment_count": 1,
                    "paid_payment_count": 0,
                    "outstanding_payment_count": 1,
                    "overdue_payment_count": 1,
                    "paid_amount": Decimal("0"),
                    "outstanding_amount": Decimal("500000"),
                    "overdue_amount": Decimal("500000"),
                }
            ]

        if "FROM payments p" in sql and "JOIN payment_links pl" not in sql and "JOIN payment_proofs pp" not in sql:
            return [
                {
                    "payment_id": "payment_1",
                    "contract_id": "contract_1",
                    "subscription_id": None,
                    "created_at": dt(5),
                    "_updated_at": dt(5),
                    "payment_type": "FIRST_PAYMENT",
                    "payment_status": "PENDING",
                    "payment_provider": "WHOP",
                    "amount": Decimal("500000"),
                    "currency": "eur",
                    "due_date": dt(3, 8),
                    "paid_at": None,
                    "note": None,
                    "failure_reason": None,
                }
            ]

        if "JOIN payment_links pl" in sql:
            return [
                {
                    "payment_link_id": "plink_1",
                    "payment_id": "payment_1",
                    "created_at": dt(5),
                    "payment_link_status": "ACTIVE",
                    "provider_invalidation_status": None,
                    "note": None,
                    "url": None,
                }
            ]

        if "JOIN payment_proofs pp" in sql:
            return []

        if "FROM refunds r" in sql:
            return []

        if "FROM invoices i" in sql:
            return []

        if "JOIN contract_subscriptions cs" in sql:
            return []

        if "subscription_checkout_links scl" in sql:
            return []

        return []


class SlowSectionDb(FakeDb):
    def __init__(self):
        super().__init__()
        self.active_queries = 0
        self.max_active_queries = 0
        self._lock = threading.Lock()

    def query_records(self, sql: str, params: dict | None = None, *, max_rows: int | None = None):
        with self._lock:
            self.active_queries += 1
            self.max_active_queries = max(self.max_active_queries, self.active_queries)
        try:
            time.sleep(0.01)
            return super().query_records(sql, params=params, max_rows=max_rows)
        finally:
            with self._lock:
                self.active_queries -= 1


class Lead360CleanupTests(unittest.TestCase):
    def run_tool(self, fake_db: FakeDb, **kwargs):
        with patch.object(lead_360, "get_db", return_value=fake_db):
            return lead_360.get_lead_360(org_id="org_1", **kwargs)

    def test_fathom_markdown_cleanup_removes_links(self):
        cleaned = lead_360.clean_fathom_markdown_summary(
            "[**Goal:** Jan wants passive income](https://fathom.video/share/abc?tab=summary&timestamp=94.0)"
        )

        self.assertIn("Goal: Jan wants passive income", cleaned["summary_text"])
        self.assertNotIn("http", json.dumps(cleaned))
        self.assertNotIn("fathom.video", json.dumps(cleaned))

    def test_money_normalization_uses_minor_units(self):
        money = lead_360.format_money_minor(Decimal("500000"), "eur")

        self.assertEqual(money["amount_minor"], 500000)
        self.assertEqual(money["amount_major"], 5000.0)
        self.assertEqual(money["amount_display"], "€5,000.00")
        self.assertEqual(money["currency"], "EUR")

    def test_default_output_is_compact_and_business_ready(self):
        result = self.run_tool(FakeDb(), lead_id=LEAD_ID)
        context = result["lead_360"]

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            set(context),
            {
                "profile",
                "current_state",
                "acquisition_summary",
                "form_answer_summary",
                "notes_summary",
                "appointment_summary",
                "appointments",
                "latest_call_summary",
                "call_summaries",
                "contract_payment_summary",
                "timeline_clean",
                "data_quality_summary",
                "journey_evidence",
            },
        )
        self.assertNotIn("lead_profile", context)
        self.assertNotIn("fathom_calls", context)
        self.assertNotIn("payments_summary", context)

    def test_lead_360_section_queries_run_concurrently(self):
        fake_db = SlowSectionDb()
        result = self.run_tool(fake_db, lead_id=LEAD_ID)

        self.assertEqual(result["status"], "success")
        self.assertGreater(fake_db.max_active_queries, 1)

    def test_lead_360_filters_cast_parameter_not_uuid_columns(self):
        fake_db = FakeDb()
        self.run_tool(fake_db, lead_id=LEAD_ID)

        sql_text = "\n".join(call["sql"] for call in fake_db.calls)
        self.assertIn("CAST(:lead_id AS uuid)", sql_text)
        self.assertNotIn("lead_id::text = :lead_id", sql_text)
        self.assertNotIn("to_client_id::text = :lead_id", sql_text)

    def test_lead_360_result_includes_tool_timing_diagnostics(self):
        result = self.run_tool(SlowSectionDb(), lead_id=LEAD_ID)
        timings = result["_diagnostics"]["timings"]
        events = timings["events"]

        self.assertIn("total_seconds", timings)
        self.assertTrue(timings["slowest_query"])
        self.assertTrue(
            any(
                event["section"] == "section_queries"
                and event["subsection"] == "parallel_wall_time"
                for event in events
            )
        )

    def test_fathom_query_limits_full_summaries_to_latest_two_by_default(self):
        fake_db = FakeDb()
        self.run_tool(fake_db, lead_id=LEAD_ID)
        fathom_call = next(
            call for call in fake_db.calls if "JOIN fathom_call_records f" in call["sql"]
        )

        self.assertIn(":full_summary_limit", fathom_call["sql"])
        self.assertEqual(fathom_call["params"]["full_summary_limit"], 2)

    def test_default_output_hides_contact_links_urls_and_internal_ids(self):
        result = self.run_tool(FakeDb(), lead_id=LEAD_ID)
        payload = json.dumps(result, default=str)

        self.assertNotIn("vedran@example.com", payload)
        self.assertNotIn("phone_e164", payload)
        self.assertNotIn("http://", payload)
        self.assertNotIn("https://", payload)
        self.assertNotIn("fathom.video", payload)
        self.assertNotIn("lead_id", payload)
        self.assertNotIn("appointment_id", payload)
        self.assertNotIn("payment_id", payload)
        self.assertNotRegex(payload, re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-", re.IGNORECASE))
        self.assertNotIn("user_internal_1", payload)
        self.assertNotIn("host_internal", payload)
        self.assertNotIn("closer_internal", payload)

    def test_contact_details_are_only_included_when_requested(self):
        result = self.run_tool(FakeDb(), lead_id=LEAD_ID, include_contact_details=True)

        self.assertEqual(result["lead_360"]["profile"]["email"], "vedran@example.com")
        self.assertEqual(result["lead_360"]["profile"]["phone_e164"], "+15551234567")

    def test_links_are_only_included_when_requested(self):
        default_result = self.run_tool(FakeDb(), lead_id=LEAD_ID)
        linked_result = self.run_tool(FakeDb(), lead_id=LEAD_ID, include_links=True)

        self.assertNotIn("recording_url", default_result["lead_360"]["latest_call_summary"])
        self.assertEqual(
            linked_result["lead_360"]["latest_call_summary"]["recording_url"],
            "https://fathom.video/share/recording",
        )

    def test_form_answer_summary_contains_cleaned_details_without_ids(self):
        result = self.run_tool(FakeDb(), lead_id=LEAD_ID)
        answers = result["lead_360"]["form_answer_summary"]
        payload = json.dumps(answers)

        self.assertEqual(answers[0]["provider_form_name"], "Qualification Call Freedom Academy (TF)")
        self.assertEqual(answers[0]["question"], "What problem are you trying to solve?")
        self.assertIn("I need predictable income", answers[0]["answer"])
        self.assertNotIn("https://", payload)
        self.assertNotIn("opt_in_id", payload)
        self.assertNotIn("question_answer_id", payload)

    def test_notes_summary_contains_cleaned_notes_without_ids(self):
        result = self.run_tool(FakeDb(), lead_id=LEAD_ID)
        notes = result["lead_360"]["notes_summary"]
        payload = json.dumps(notes)

        self.assertIn("follow up on payment plan", notes[0]["note"])
        self.assertIn("created_at", notes[0])
        self.assertNotIn("https://", payload)
        self.assertNotIn("note_id", payload)
        self.assertNotIn("appointment_id", payload)

    def test_compact_appointments_include_status_labels_without_internal_fields(self):
        result = self.run_tool(FakeDb(), lead_id=LEAD_ID)
        appointments = result["lead_360"]["appointments"]
        payload = json.dumps(appointments)
        labels = {appointment["event_name"]: appointment["status_label"] for appointment in appointments}

        self.assertEqual(labels["Strategy Call - Freedom - FU"], "canceled")
        self.assertEqual(labels["Qualification Call Freedom Academy (TF)"], "completed")
        self.assertEqual(labels["Strategy Call - Freedom - NS"], "no_show")
        self.assertNotIn("appointment_id", payload)
        self.assertNotIn("host_id", payload)
        self.assertNotIn("setter_id", payload)
        self.assertNotIn("meeting_url", payload)
        self.assertNotIn("recording_url", payload)

    def test_call_summaries_include_all_cleaned_calls(self):
        result = self.run_tool(FakeDb(), lead_id=LEAD_ID)
        calls = result["lead_360"]["call_summaries"]
        payload = json.dumps(calls)

        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["event_name"], "Qualification Call Freedom Academy (TF)")
        self.assertEqual(calls[1]["event_name"], "Earlier Strategy Call")
        self.assertIn("Goal: Jan wants passive income", calls[0]["summary_clean"])
        self.assertIn("Follow up through WhatsApp", calls[0]["summary_clean"])
        self.assertIn("latest_call_summary", result["lead_360"])
        self.assertNotIn("https://", payload)
        self.assertNotIn("fathom.video", payload)
        self.assertNotIn("fathom_record_id", payload)
        self.assertNotIn("appointment_id", payload)
        self.assertNotIn("key_takeaways", payload)
        self.assertNotIn("action_items", payload)
        self.assertNotIn("objections", payload)
        self.assertNotIn("ai_rationale", payload)

    def test_call_summary_keeps_complete_summary_without_meeting_purpose(self):
        long_detail = " ".join(["detail"] * 350)
        calls = lead_360.compact_call_summaries(
            [
                {
                    "call_started_at": dt(4, 13),
                    "event_name": "Qualification Call",
                    "summary": (
                        "## Meeting Purpose\n"
                        "Understand the lead context.\n\n"
                        "## Key Takeaways\n"
                        f"{long_detail} COMPLETE_SUMMARY_TAIL"
                    ),
                }
            ],
            include_links=False,
        )

        self.assertIn("Understand the lead context", calls[0]["summary_clean"])
        self.assertIn("COMPLETE_SUMMARY_TAIL", calls[0]["summary_clean"])
        self.assertNotIn("meeting_purpose", calls[0])

    def test_call_summaries_only_include_full_summary_for_first_two_calls_by_default(self):
        calls = lead_360.compact_call_summaries(
            [
                {"call_started_at": dt(4, 13), "event_name": "Call 1", "summary": "Summary 1"},
                {"call_started_at": dt(3, 13), "event_name": "Call 2", "summary": "Summary 2"},
                {"call_started_at": dt(2, 13), "event_name": "Call 3", "summary": "Summary 3"},
            ],
            include_links=False,
        )

        self.assertEqual(calls[0]["summary_clean"], "Summary 1")
        self.assertEqual(calls[1]["summary_clean"], "Summary 2")
        self.assertNotIn("summary_clean", calls[2])

    def test_timeline_canceled_appointment_is_not_marked_completed(self):
        result = self.run_tool(FakeDb(), lead_id=LEAD_ID)
        timeline_text = json.dumps(result["lead_360"]["timeline_clean"], ensure_ascii=False)

        self.assertIn("Appointment canceled", timeline_text)
        self.assertIn("was marked Canceled", timeline_text)
        self.assertNotIn("Strategy Call - Freedom - FU took place", timeline_text)

    def test_timeline_overdue_payment_uses_money_display(self):
        result = self.run_tool(FakeDb(), lead_id=LEAD_ID)
        timeline_text = json.dumps(result["lead_360"]["timeline_clean"], ensure_ascii=False)

        self.assertIn("Payment overdue", timeline_text)
        self.assertIn("€5,000.00", timeline_text)
        self.assertNotIn("€500,000.00", timeline_text)

    def test_null_and_empty_raw_sections_are_cleaned(self):
        result = self.run_tool(FakeDb(), lead_id=LEAD_ID)
        context = result["lead_360"]
        payload = json.dumps(context)

        self.assertNotIn('"form_answers": []', payload)
        self.assertNotIn('"refunds": []', payload)
        self.assertNotIn('"landing_page": null', payload)
        self.assertIn("First source", context["data_quality_summary"]["missing"])
        self.assertIn("Last source", context["data_quality_summary"]["missing"])
        self.assertIn("Next touch point", context["data_quality_summary"]["missing"])
        self.assertTrue(context["data_quality_summary"]["flags"]["has_payment_link"])
        self.assertFalse(context["data_quality_summary"]["flags"]["has_payment_proof"])

    def test_contract_payment_summary_normalizes_money(self):
        result = self.run_tool(FakeDb(), lead_id=LEAD_ID)
        summary = result["lead_360"]["contract_payment_summary"]

        contract = summary["contracts"][0]
        payment = summary["payments"][0]
        by_currency = summary["payment_summary_by_currency"][0]

        self.assertEqual(contract["value"]["amount_display"], "€5,000.00")
        self.assertEqual(payment["amount"]["amount_display"], "€5,000.00")
        self.assertTrue(payment["is_overdue"])
        self.assertEqual(by_currency["outstanding_amount"]["amount_display"], "€5,000.00")
        self.assertEqual(summary["outstanding_amount_display"], "€5,000.00")

    def test_multiple_matches_do_not_expose_lead_ids(self):
        fake_db = FakeDb(
            resolver_rows=[
                FakeDb.resolver_row(lead_id=LEAD_ID),
                FakeDb.resolver_row(lead_id=OTHER_LEAD_ID, display_name="Vedran Other"),
            ]
        )
        result = self.run_tool(fake_db, lead_name="Vedran")
        payload = json.dumps(result, default=str)

        self.assertEqual(result["status"], "multiple_matches")
        self.assertNotIn("lead_id", payload)
        self.assertNotIn(LEAD_ID, payload)
        self.assertNotIn(OTHER_LEAD_ID, payload)

    def test_tool_wrapper_returns_clean_json_string(self):
        with patch.object(lead_360, "get_db", return_value=FakeDb()):
            raw = lead_360.get_lead_360_tool.invoke({"org_id": "org_1", "lead_id": LEAD_ID})

        parsed = json.loads(raw)
        self.assertEqual(parsed["status"], "success")
        self.assertIn("profile", parsed["lead_360"])
        self.assertNotIn("https://", raw)

    def test_final_output_has_no_keys_ending_with_id(self):
        result = self.run_tool(FakeDb(), lead_id=LEAD_ID)

        def walk(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    self.assertFalse(key.endswith("_id"), key)
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)

        walk(result["lead_360"])

    def test_subscription_query_uses_started_at_or_contract_created_at(self):
        fake_db = FakeDb()
        self.run_tool(fake_db, lead_id=LEAD_ID)
        subscription_sql = next(
            call["sql"]
            for call in fake_db.calls
            if "JOIN contract_subscriptions cs" in call["sql"]
            and "subscription_checkout_links" not in call["sql"]
        )

        self.assertIn("COALESCE(cs.started_at, c.created_at) AS created_at", subscription_sql)
        self.assertIn(
            "ORDER BY COALESCE(cs.started_at, c.created_at) DESC",
            subscription_sql,
        )
        self.assertNotIn("ORDER BY cs.created_at DESC", subscription_sql)


if __name__ == "__main__":
    unittest.main()
