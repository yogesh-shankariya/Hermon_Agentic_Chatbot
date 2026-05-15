"""Read-only diagnostic tools over diagnostic_lead_snapshot.

These tools provide controlled evidence for the future diagnostic analytics
agent. They intentionally use fixed SQL templates instead of LLM-generated SQL.

Money fields in diagnostic_lead_snapshot are already major-unit EUR values.
Do not divide diagnostic money fields by 100 in these tools or in the
diagnostic agent prompt.
"""

from __future__ import annotations

import json
from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from langchain.tools import tool

from app.config import get_sql_agent_settings
from app.db import get_db


SCOPE_NOTE = (
    "This diagnostic snapshot uses lead_created_at cohort logic. "
    "Revenue and payment fields are lifetime outcomes for leads created in the selected period, "
    "not true payment-period revenue. "
    "Monetary fields returned by this tool are already major-unit EUR values, "
    "not raw minor-unit source values."
)

SUPPORTED_SOURCE_BASIS = {
    "first": "first_source",
    "last": "last_source",
}
DEFAULT_LOOKBACK_MONTHS = 6
MONTH_ABBREVIATIONS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)

FUNNEL_STEP_LABELS = {
    "total_leads": "Total leads",
    "booked_call": "Booked a call",
    "completed_call": "Completed a call",
    "signed_contract": "Signed contract",
    "paid_converted": "Paid / converted",
}

FUNNEL_STAGE_LABELS = {
    "never_booked": "Never booked a call",
    "lead_only": "Never booked a call",
    "booked_not_completed": "Booked but did not complete call",
    "completed_not_signed": "Completed call but did not sign",
    "signed_not_paid": "Signed but not paid",
    "paid": "Paid / converted",
    "lost": "Lost",
    "unqualified": "Unqualified",
    "refunded": "Refunded",
}

FUNNEL_STAGE_HINTS = {
    "never_booked": "Leads did not reach the appointment stage",
    "lead_only": "Leads did not reach the call stage",
    "booked_not_completed": "Attendance or confirmation process needs review",
    "completed_not_signed": "Post-call conversion needs review",
    "signed_not_paid": "Payment collection after signing needs review",
    "paid": "Converted group",
    "lost": "Marked lost",
    "unqualified": "Marked unqualified",
    "refunded": "Paid then refunded",
}

DROP_POINT_METADATA = {
    "lead_to_booked": {
        "drop_point_label": "No booked-call record",
        "from_step_label": "Total leads",
        "to_step_label": "Booked a call",
    },
    "booked_to_completed": {
        "drop_point_label": "Booked but no completed-call record",
        "from_step_label": "Booked a call",
        "to_step_label": "Completed a call",
    },
    "completed_to_signed": {
        "drop_point_label": "Completed call but no signed-contract record",
        "from_step_label": "Completed a call",
        "to_step_label": "Signed contract",
    },
    "signed_to_paid": {
        "drop_point_label": "Signed but no paid-payment record",
        "from_step_label": "Signed contract",
        "to_step_label": "Paid / converted",
    },
}

REASON_CATEGORY_LABELS = {
    "price_or_budget": "Price or budget concern",
    "timing_issue": "Not ready yet / needs more time",
    "not_decision_maker": "Not the decision-maker",
    "needs_partner_approval": "Waiting for partner or decision-maker approval",
    "trust_issue": "Needs more trust or proof",
    "low_intent": "Low buying intent",
    "unclear_need": "Need or goal is unclear",
    "poor_fit": "Not a strong fit",
    "competition": "Comparing with another option",
    "too_busy": "Too busy right now",
    "needs_more_information": "Needs clearer information",
    "payment_friction": "Payment issue or payment not completed",
    "contract_friction": "Contract signing issue",
    "no_show": "Missed or cancelled call",
    "ghosted": "Stopped responding",
    "follow_up_pending": "Follow-up still pending",
    "operational_delay": "Internal or operational delay",
    "technical_issue": "Link or technical issue",
    "language_or_communication_issue": "Communication issue",
    "location_or_timezone_issue": "Location or timezone issue",
    "already_solved": "Problem already solved",
    "unknown": "Reason not clear",
}

REASON_SUBCATEGORY_LABELS = {
    "price_too_high": "Price felt too high",
    "budget_not_available": "Budget not available right now",
    "wants_discount": "Asked for discount",
    "needs_payment_plan": "Needs a payment plan",
    "not_ready_now": "Not ready right now",
    "needs_more_time": "Needs more time before deciding",
    "waiting_for_partner": "Waiting for partner approval",
    "waiting_for_team": "Waiting for team input",
    "waiting_for_finance": "Waiting for finance approval",
    "does_not_trust_offer": "Does not fully trust the offer yet",
    "needs_proof_or_case_study": "Needs proof or case studies",
    "unclear_value": "Value is not clear enough",
    "comparing_competitor": "Comparing with another option",
    "not_enough_need": "Need is not strong enough",
    "wrong_customer_fit": "Not the right customer fit",
    "not_qualified": "Not qualified",
    "missed_call": "Missed the call",
    "cancelled_call": "Cancelled the call",
    "stopped_responding": "Stopped responding",
    "needs_more_information": "Needs more information",
    "contract_not_signed": "Contract not signed",
    "payment_not_completed": "Payment not completed",
    "payment_failed": "Payment failed",
    "refund_requested": "Refund requested",
    "internal_team_delay": "Internal team delay",
    "system_or_link_issue": "System or link issue",
    "language_barrier": "Language barrier",
    "timezone_issue": "Timezone issue",
    "issue_already_solved": "Issue already solved",
    "other": "Other reason",
    "unknown": "Reason not clear",
}

BUYING_INTENT_LABELS = {
    "very_high": "Very high intent",
    "high": "High intent",
    "medium": "Medium intent",
    "low": "Low intent",
    "very_low": "Very low intent",
    "unknown": "Intent not clear",
}

FINAL_FUNNEL_STAGE_CASE_SQL = """
CASE
  WHEN dls.paid_payment_count > 0 THEN 'paid_converted'
  WHEN dls.signed_contract_count > 0 THEN 'signed_not_paid'
  WHEN dls.completed_call_count > 0 THEN 'completed_not_signed'
  WHEN dls.appointment_count > 0 THEN 'booked_not_completed'
  ELSE 'never_booked'
END
""".strip()

TEXT_REASON_COHORTS = {
    "never_booked": {
        "label": "Never booked a call",
        "definition": "final_funnel_stage = never_booked",
        "condition": f"({FINAL_FUNNEL_STAGE_CASE_SQL}) = 'never_booked'",
    },
    "booked_not_completed": {
        "label": "Booked but did not complete call",
        "definition": "final_funnel_stage = booked_not_completed",
        "condition": f"({FINAL_FUNNEL_STAGE_CASE_SQL}) = 'booked_not_completed'",
    },
    "completed_not_signed": {
        "label": "Completed call but did not sign",
        "definition": "final_funnel_stage = completed_not_signed",
        "condition": f"({FINAL_FUNNEL_STAGE_CASE_SQL}) = 'completed_not_signed'",
    },
    "signed_not_paid": {
        "label": "Signed but not paid",
        "definition": "final_funnel_stage = signed_not_paid",
        "condition": f"({FINAL_FUNNEL_STAGE_CASE_SQL}) = 'signed_not_paid'",
    },
    "completed_not_paid": {
        "label": "Completed call but not paid",
        "definition": "completed_call_count > 0 AND paid_payment_count = 0",
        "condition": "dls.completed_call_count > 0 AND dls.paid_payment_count = 0",
    },
}

TEXT_REASON_COHORT_ALIASES = {
    "lead_not_booked": "never_booked",
}

FUNNEL_STUCK_GROUPS = {
    "total_leads": {
        "stage_order": 6,
        "stage_label": "Total",
        "what_this_means": "Must equal the sum of all rows above",
        "cohort_name": None,
    },
    "never_booked": {
        "stage_order": 1,
        "stage_label": "Never booked a call",
        "what_this_means": "Leads did not reach the appointment stage",
        "cohort_name": "never_booked",
    },
    "booked_not_completed": {
        "stage_order": 2,
        "stage_label": "Booked but did not complete call",
        "what_this_means": "Leads booked a call but did not attend/complete it",
        "cohort_name": "booked_not_completed",
    },
    "completed_not_signed": {
        "stage_order": 3,
        "stage_label": "Completed call but did not sign",
        "what_this_means": "Leads attended the call but did not move to signed contract",
        "cohort_name": "completed_not_signed",
    },
    "signed_not_paid": {
        "stage_order": 4,
        "stage_label": "Signed but not paid",
        "what_this_means": "Leads signed but payment was not completed",
        "cohort_name": "signed_not_paid",
    },
    "paid_converted": {
        "stage_order": 5,
        "stage_label": "Paid / converted",
        "what_this_means": "Leads completed the paid conversion path",
        "cohort_name": None,
    },
}

STUCK_TEXT_COHORTS = (
    "never_booked",
    "booked_not_completed",
    "completed_not_signed",
    "signed_not_paid",
)

TEXT_COHORT_SELECTION_PRIORITY = {
    "completed_not_signed": 1,
    "booked_not_completed": 2,
    "signed_not_paid": 3,
    "never_booked": 4,
}

TEXT_COHORT_REASONS = {
    "never_booked": "Top-of-funnel booking leakage",
    "booked_not_completed": "Booked-call attendance leakage",
    "completed_not_signed": "Post-call signing leakage",
    "signed_not_paid": "Payment-stage leakage",
}

SECONDARY_TEXT_COHORT_ORDER = (
    "completed_not_signed",
    "booked_not_completed",
    "signed_not_paid",
    "never_booked",
)

SPECIAL_COMBINATION_LABELS = {
    "unknown_reason": "Reason not clear",
    "no_text_insight_available": "No usable text insight available",
    "other_lower_volume_combinations": "Other lower-volume combinations",
}

SNAPSHOT_DATE_BOUNDS_SQL = """
SELECT
  MIN(dls.lead_created_at)::date AS min_lead_created_date,
  MAX(dls.lead_created_at)::date AS max_lead_created_date
FROM diagnostic_lead_snapshot dls
WHERE dls.clerk_org_id = :org_id
"""


def _default_org_id(org_id: str | None) -> str:
    clean_org_id = str(org_id or "").strip()
    if clean_org_id:
        return clean_org_id

    settings = get_sql_agent_settings()
    clean_default = str(settings.default_org_id or "").strip()
    if not clean_default:
        raise ValueError("org_id is required because HERMON_DEFAULT_CLERK_ORG_ID is not set.")
    return clean_default


def _parse_date(value: str | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    clean_value = str(value).strip()
    if not clean_value:
        return None
    return datetime.strptime(clean_value, "%Y-%m-%d").date()


def _add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    target_year = month_index // 12
    target_month = month_index % 12 + 1
    target_day = min(value.day, monthrange(target_year, target_month)[1])
    return date(target_year, target_month, target_day)


def _query_records(
    sql: str,
    params: dict[str, Any],
    *,
    max_rows: int = 200,
) -> list[dict[str, Any]]:
    return get_db().query_records(sql, params=params, max_rows=max_rows)


def _snapshot_date_bounds(org_id: str) -> dict[str, date]:
    rows = _query_records(SNAPSHOT_DATE_BOUNDS_SQL, {"org_id": org_id}, max_rows=1)
    if not rows or rows[0].get("max_lead_created_date") is None:
        raise ValueError(
            "diagnostic_lead_snapshot has no rows for this org, so default periods cannot be derived."
        )

    min_lead_created_date = _parse_date(rows[0].get("min_lead_created_date"))
    max_lead_created_date = _parse_date(rows[0].get("max_lead_created_date"))
    if min_lead_created_date is None or max_lead_created_date is None:
        raise ValueError("diagnostic_lead_snapshot date bounds could not be parsed.")

    return {
        "min_lead_created_date": min_lead_created_date,
        "max_lead_created_date": max_lead_created_date,
    }


def _default_periods(
    org_id: str,
    current_start_date: str | None,
    current_end_date: str | None,
    previous_start_date: str | None,
    previous_end_date: str | None,
) -> dict[str, str]:
    bounds = _snapshot_date_bounds(org_id)
    anchor_date = bounds["max_lead_created_date"]

    current_start = _parse_date(current_start_date)
    current_end = _parse_date(current_end_date)
    previous_start = _parse_date(previous_start_date)
    previous_end = _parse_date(previous_end_date)

    current_start_was_defaulted = current_start is None
    current_end_was_defaulted = current_end is None

    if current_end is None:
        current_end = anchor_date + timedelta(days=1)
    if current_start is None:
        current_start = _add_months(current_end, -DEFAULT_LOOKBACK_MONTHS)

    if previous_start is None or previous_end is None:
        previous_end_default = current_start
        if current_start_was_defaulted and current_end_was_defaulted:
            previous_start_default = _add_months(
                previous_end_default,
                -DEFAULT_LOOKBACK_MONTHS,
            )
        else:
            previous_start_default = previous_end_default - (current_end - current_start)
        previous_start = previous_start or previous_start_default
        previous_end = previous_end or previous_end_default

    if current_start >= current_end:
        raise ValueError("current_start_date must be earlier than current_end_date.")
    if previous_start >= previous_end:
        raise ValueError("previous_start_date must be earlier than previous_end_date.")

    return {
        "current_start_date": current_start.isoformat(),
        "current_end_date": current_end.isoformat(),
        "previous_start_date": previous_start.isoformat(),
        "previous_end_date": previous_end.isoformat(),
        "period_anchor_date": anchor_date.isoformat(),
    }


def _safe_limit(limit: int | None, *, default: int = 10, maximum: int = 50) -> int:
    try:
        parsed = int(limit if limit is not None else default)
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, maximum))


def _safe_top_limit(limit: int | None, *, default: int = 10, maximum: int = 20) -> int:
    return _safe_limit(limit, default=default, maximum=maximum)


def _friendly_enum_label(value: str | None, labels: dict[str, str], default_key: str) -> str:
    clean_value = str(value or "").strip()
    if not clean_value:
        clean_value = default_key
    if clean_value in labels:
        return labels[clean_value]
    return clean_value.replace("_", " ").title()


def _reason_category_label(value: str | None) -> str:
    return _friendly_enum_label(value, REASON_CATEGORY_LABELS, "unknown")


def _reason_subcategory_label(value: str | None) -> str:
    return _friendly_enum_label(value, REASON_SUBCATEGORY_LABELS, "unknown")


def _buying_intent_label(value: str | None) -> str:
    return _friendly_enum_label(value, BUYING_INTENT_LABELS, "unknown")


def _display_issue_combination(raw_combination: str | None) -> str:
    clean_combination = str(raw_combination or "unknown_reason").strip()
    if clean_combination in SPECIAL_COMBINATION_LABELS:
        return SPECIAL_COMBINATION_LABELS[clean_combination]
    return " + ".join(
        _reason_category_label(part.strip())
        for part in clean_combination.split(" + ")
        if part.strip()
    )


def _percentage(numerator: int | float | None, denominator: int | float | None) -> float:
    if not denominator:
        return 0.0
    return round(100.0 * float(numerator or 0) / float(denominator), 2)


def _source_column(source_basis: str) -> str:
    basis = str(source_basis or "first").strip().lower()
    if basis not in SUPPORTED_SOURCE_BASIS:
        raise ValueError("source_basis must be one of: first, last.")
    return SUPPORTED_SOURCE_BASIS[basis]


def _json_response(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=str)


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _number_or_none(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _business_date_display(value: date) -> str:
    return f"{value.day} {MONTH_ABBREVIATIONS[value.month - 1]} {value.year}"


def _period_metadata(start_date: str, end_date: str, anchor_date: str) -> dict[str, str]:
    parsed_start = _parse_date(start_date)
    parsed_end = _parse_date(end_date)
    if parsed_start is None or parsed_end is None:
        raise ValueError("Tool period dates could not be parsed.")

    display_end = parsed_end - timedelta(days=1)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "display_start_date": parsed_start.isoformat(),
        "display_end_date": display_end.isoformat(),
        "date_field": "lead_created_at",
        "date_range_display": (
            f"{_business_date_display(parsed_start)} to {_business_date_display(display_end)}"
        ),
        "anchor_date": anchor_date,
    }


def _funnel_stage_label(funnel_stage: Any) -> str:
    clean_stage = str(funnel_stage or "").strip()
    if clean_stage in FUNNEL_STAGE_LABELS:
        return FUNNEL_STAGE_LABELS[clean_stage]
    return "Unknown"


def _funnel_stage_hint(funnel_stage: Any) -> str:
    clean_stage = str(funnel_stage or "").strip()
    return FUNNEL_STAGE_HINTS.get(clean_stage, "Review this final funnel position")


def _final_funnel_stage_key(
    *,
    appointment_count: int = 0,
    completed_call_count: int = 0,
    signed_contract_count: int = 0,
    paid_payment_count: int = 0,
) -> str:
    if paid_payment_count > 0:
        return "paid_converted"
    if signed_contract_count > 0:
        return "signed_not_paid"
    if completed_call_count > 0:
        return "completed_not_signed"
    if appointment_count > 0:
        return "booked_not_completed"
    return "never_booked"


def _funnel_sections(rows: list[dict[str, Any]]) -> dict[str, Any]:
    funnel_flow: list[dict[str, Any]] = []
    final_position_breakdown: list[dict[str, Any]] = []
    activity_counts: dict[str, int] = {
        "appointment_records": 0,
        "completed_call_records": 0,
        "no_show_records": 0,
        "signed_contract_records": 0,
        "paid_payment_records": 0,
    }
    total_row: dict[str, Any] | None = None

    for row in rows:
        row_type = row.get("row_type")
        if row_type == "total":
            total_row = row
            continue

        if row_type == "funnel_flow":
            step_key = str(row.get("step_key") or "").strip()
            funnel_flow.append(
                {
                    "step_order": _int_or_none(row.get("step_order")),
                    "step_key": step_key,
                    "step_label": FUNNEL_STEP_LABELS.get(step_key, step_key.replace("_", " ").title()),
                    "leads_reached": _int_or_none(row.get("leads_reached")) or 0,
                    "dropped_from_previous": _int_or_none(row.get("dropped_from_previous")),
                    "drop_rate_from_previous": _number_or_none(row.get("drop_rate_from_previous")),
                    "conversion_rate_from_previous": _number_or_none(
                        row.get("conversion_rate_from_previous")
                    ),
                }
            )
            continue

        if row_type == "stage":
            pct_of_total_leads = row.get("pct_of_total_leads")
            if pct_of_total_leads is None:
                pct_of_total_leads = row.get("pct_of_leads")
            funnel_stage = row.get("funnel_stage")
            final_position_breakdown.append(
                {
                    "funnel_stage": funnel_stage,
                    "display_label": row.get("display_label") or _funnel_stage_label(funnel_stage),
                    "lead_count": _int_or_none(row.get("lead_count")) or 0,
                    "pct_of_total_leads": _number_or_none(pct_of_total_leads),
                    "net_collected_amount": _number_or_none(row.get("net_collected_amount")),
                    "interpretation_hint": row.get("interpretation_hint")
                    or _funnel_stage_hint(funnel_stage),
                }
            )
            continue

        if row_type == "activity_counts":
            activity_counts = {
                "appointment_records": _int_or_none(row.get("appointment_records")) or 0,
                "completed_call_records": _int_or_none(row.get("completed_call_records")) or 0,
                "no_show_records": _int_or_none(row.get("no_show_records")) or 0,
                "signed_contract_records": _int_or_none(row.get("signed_contract_records")) or 0,
                "paid_payment_records": _int_or_none(row.get("paid_payment_records")) or 0,
            }

    if total_row is not None and not any(activity_counts.values()):
        activity_counts = {
            "appointment_records": _int_or_none(total_row.get("appointment_count")) or 0,
            "completed_call_records": _int_or_none(total_row.get("completed_call_count")) or 0,
            "no_show_records": _int_or_none(total_row.get("no_show_count")) or 0,
            "signed_contract_records": _int_or_none(total_row.get("signed_contract_count")) or 0,
            "paid_payment_records": _int_or_none(total_row.get("paid_payment_count")) or 0,
        }

    funnel_flow.sort(key=lambda item: item["step_order"] or 0)
    final_position_breakdown.sort(
        key=lambda item: (
            -(item["lead_count"] or 0),
            str(item.get("funnel_stage") or ""),
        )
    )

    stuck_positions = [
        item
        for item in final_position_breakdown
        if item.get("funnel_stage") not in {"paid"} and (item.get("lead_count") or 0) > 0
    ]
    if stuck_positions:
        stuck_positions[0]["interpretation_hint"] = "Largest visible stuck group"

    total_leads = next(
        (
            item["leads_reached"]
            for item in funnel_flow
            if item.get("step_key") == "total_leads"
        ),
        None,
    )
    if total_leads is None and total_row is not None:
        total_leads = _int_or_none(total_row.get("lead_count"))
    if total_leads is None and final_position_breakdown:
        total_leads = sum(item["lead_count"] for item in final_position_breakdown)

    return {
        "funnel_flow": funnel_flow,
        "final_position_breakdown": final_position_breakdown,
        "activity_counts": activity_counts,
        "total_leads": total_leads or 0,
    }


def _drop_reconciliation(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reconciled: list[dict[str, Any]] = []
    for row in rows:
        drop_point_key = str(row.get("drop_point_key") or "").strip()
        metadata = DROP_POINT_METADATA.get(drop_point_key, {})
        movement_dropped_leads = _int_or_none(row.get("movement_dropped_leads")) or 0
        drop_set_leads = _int_or_none(row.get("drop_set_leads")) or 0
        offsetting_later_step_leads = (
            _int_or_none(row.get("offsetting_later_step_leads")) or 0
        )
        from_step_label = metadata.get("from_step_label", "Unknown")
        to_step_label = metadata.get("to_step_label", "Unknown")
        if offsetting_later_step_leads:
            reconciliation_note = (
                f"{drop_set_leads} leads reached {from_step_label} but not {to_step_label}. "
                f"{offsetting_later_step_leads} leads reached {to_step_label} without a tracked "
                f"{from_step_label} record, so the movement table shows a net drop of "
                f"{movement_dropped_leads}."
            )
        else:
            reconciliation_note = (
                f"{drop_set_leads} leads reached {from_step_label} but not {to_step_label}, "
                f"matching the movement table drop of {movement_dropped_leads}."
            )
        reconciled.append(
            {
                "drop_point_key": drop_point_key,
                "drop_point_label": metadata.get("drop_point_label", "Unknown"),
                "from_step_label": from_step_label,
                "to_step_label": to_step_label,
                "dropped_leads": drop_set_leads,
                "movement_dropped_leads": movement_dropped_leads,
                "drop_set_leads": drop_set_leads,
                "offsetting_later_step_leads": offsetting_later_step_leads,
                "matches_funnel_flow_drop": offsetting_later_step_leads == 0,
                "funnel_stage": row.get("funnel_stage"),
                "conversion_outcome": row.get("conversion_outcome"),
                "final_position_label": _funnel_stage_label(row.get("funnel_stage")),
                "lead_count": _int_or_none(row.get("lead_count")) or 0,
                "pct_of_dropped_leads": _number_or_none(row.get("pct_of_drop_set_leads")),
                "pct_of_drop_set_leads": _number_or_none(row.get("pct_of_drop_set_leads")),
                "reconciliation_note": reconciliation_note,
            }
        )
    return reconciled


def _text_cohort_metadata(cohort_name: str) -> dict[str, str]:
    clean_name = str(cohort_name or "").strip().lower()
    canonical_name = TEXT_REASON_COHORT_ALIASES.get(clean_name, clean_name)
    if canonical_name not in TEXT_REASON_COHORTS:
        allowed = ", ".join(sorted(TEXT_REASON_COHORTS))
        raise ValueError(f"cohort_name must be one of: {allowed}.")
    metadata = TEXT_REASON_COHORTS[canonical_name]
    return {
        "cohort_name": canonical_name,
        "cohort_label": metadata["label"],
        "cohort_definition": metadata["definition"],
        "condition": metadata["condition"],
    }


def _stuck_group_funnel(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total_leads = next(
        (
            _int_or_none(row.get("lead_count")) or 0
            for row in rows
            if str(row.get("stage_key") or "").strip() == "total_leads"
        ),
        0,
    )
    result: list[dict[str, Any]] = []
    for row in rows:
        stage_key = str(row.get("stage_key") or row.get("cohort_name") or "").strip()
        if stage_key == "lead_not_booked":
            stage_key = "never_booked"
        if stage_key not in FUNNEL_STUCK_GROUPS:
            continue
        metadata = FUNNEL_STUCK_GROUPS[stage_key]
        lead_count = _int_or_none(row.get("lead_count")) or 0
        result.append(
            {
                "stage_order": metadata["stage_order"],
                "stage_key": stage_key,
                "cohort_name": metadata["cohort_name"],
                "stage_label": metadata["stage_label"],
                "lead_count": lead_count,
                "pct_of_total_leads": _number_or_none(row.get("pct_of_total_leads"))
                if row.get("pct_of_total_leads") is not None
                else _percentage(lead_count, total_leads),
                "what_this_means": row.get("what_this_means")
                or metadata["what_this_means"],
                "is_text_reason_cohort": metadata["cohort_name"] is not None,
            }
        )
    result.sort(key=lambda item: item["stage_order"])
    return result


def _stuck_group_validation(stuck_group_funnel: list[dict[str, Any]]) -> dict[str, Any]:
    total_leads = next(
        (
            _int_or_none(row.get("lead_count")) or 0
            for row in stuck_group_funnel
            if row.get("stage_key") == "total_leads"
        ),
        0,
    )
    stage_total = sum(
        _int_or_none(row.get("lead_count")) or 0
        for row in stuck_group_funnel
        if row.get("stage_key") in {
            "never_booked",
            "booked_not_completed",
            "completed_not_signed",
            "signed_not_paid",
            "paid_converted",
        }
    )
    stage_counts_reconcile = stage_total == total_leads
    validation: dict[str, Any] = {
        "total_leads": total_leads,
        "stage_total": stage_total,
        "stage_counts_reconcile": stage_counts_reconcile,
    }
    if not stage_counts_reconcile:
        validation["safe_message"] = (
            "Funnel stage counts could not be reconciled because final stage rows "
            "do not sum to total leads."
        )
    return validation


def _stuck_group_candidates(stuck_group_funnel: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item
        for item in stuck_group_funnel
        if item.get("cohort_name") in STUCK_TEXT_COHORTS
        and (item.get("lead_count") or 0) > 0
    ]


def _largest_stuck_group(stuck_group_funnel: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = _stuck_group_candidates(stuck_group_funnel)
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda item: (
            item.get("lead_count") or 0,
            -TEXT_COHORT_SELECTION_PRIORITY.get(str(item.get("cohort_name")), 99),
        ),
    )


def _recommended_text_cohorts(stuck_group_funnel: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts_by_name = {
        str(row.get("cohort_name") or "").strip(): _int_or_none(row.get("lead_count")) or 0
        for row in stuck_group_funnel
        if row.get("cohort_name")
    }
    selected = _largest_stuck_group(stuck_group_funnel)
    selected_name = str((selected or {}).get("cohort_name") or "").strip()
    recommended: list[dict[str, Any]] = []

    ordered_names: list[str] = []
    if selected_name:
        ordered_names.append(selected_name)
    for cohort_name in SECONDARY_TEXT_COHORT_ORDER:
        if cohort_name not in ordered_names:
            ordered_names.append(cohort_name)

    for cohort_name in ordered_names:
        lead_count = counts_by_name.get(cohort_name, 0)
        if lead_count <= 0:
            continue
        metadata = TEXT_REASON_COHORTS[cohort_name]
        reason = (
            "Largest mutually exclusive final-stage stuck group"
            if cohort_name == selected_name
            else TEXT_COHORT_REASONS[cohort_name]
        )
        recommended.append(
            {
                "cohort_name": cohort_name,
                "cohort_label": metadata["label"],
                "lead_count": lead_count,
                "reason": reason,
            }
        )
        if len(recommended) >= 2:
            break
    return recommended


def _split_text_reason_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {
        "coverage": [],
        "combination": [],
        "issue": [],
        "subcategory": [],
        "buying_intent": [],
        "source_text_type": [],
    }
    for row in rows:
        row_type = str(row.get("row_type") or "").strip()
        if row_type in grouped:
            grouped[row_type].append(row)
    return grouped


def _text_reason_coverage(row: dict[str, Any] | None) -> dict[str, int | float | bool]:
    total_leads = _int_or_none((row or {}).get("total_cohort_leads")) or 0
    leads_with_text = _int_or_none((row or {}).get("leads_with_text_insights")) or 0
    known_reason_leads = _int_or_none((row or {}).get("known_reason_leads")) or 0
    unknown_only_reason_leads = _int_or_none((row or {}).get("unknown_only_reason_leads")) or 0
    leads_without_text = max(total_leads - leads_with_text, 0)
    unknown_or_missing_reason_leads = max(total_leads - known_reason_leads, 0)
    coverage_reconciles = (
        total_leads == leads_with_text + leads_without_text
        and leads_with_text == known_reason_leads + unknown_only_reason_leads
    )
    return {
        "total_cohort_leads": total_leads,
        "leads_with_text_insights": leads_with_text,
        "leads_without_text_insights": leads_without_text,
        "text_insight_coverage_rate": _percentage(leads_with_text, total_leads),
        "known_reason_leads": known_reason_leads,
        "unknown_only_reason_leads": unknown_only_reason_leads,
        "known_reason_coverage_rate": _percentage(known_reason_leads, total_leads),
        "unknown_or_missing_reason_leads": unknown_or_missing_reason_leads,
        "unknown_or_missing_reason_rate": _percentage(unknown_or_missing_reason_leads, total_leads),
        "coverage_reconciles": coverage_reconciles,
    }


def _limited_combination_distribution(
    rows: list[dict[str, Any]],
    *,
    total_leads: int,
    limit: int,
) -> list[dict[str, Any]]:
    combination_counts = [
        {
            "issue_combination_raw": str(row.get("item_key") or "").strip(),
            "lead_count": _int_or_none(row.get("lead_count")) or 0,
        }
        for row in rows
        if _int_or_none(row.get("lead_count"))
    ]
    special_raws = {"unknown_reason", "no_text_insight_available"}
    special_rows = [
        row for row in combination_counts if row["issue_combination_raw"] in special_raws
    ]
    known_rows = [
        row for row in combination_counts if row["issue_combination_raw"] not in special_raws
    ]
    known_rows.sort(
        key=lambda row: (
            -row["lead_count"],
            row["issue_combination_raw"],
        )
    )

    special_rows.sort(
        key=lambda row: (
            -row["lead_count"],
            row["issue_combination_raw"],
        )
    )

    known_slots = max(limit - len(special_rows), 0)
    if len(known_rows) > known_slots:
        known_slots = max(limit - len(special_rows) - 1, 0)
    selected_known = known_rows[:known_slots]
    omitted_known = known_rows[known_slots:]

    selected = list(selected_known) + list(special_rows)
    selected.sort(
        key=lambda row: (
            -row["lead_count"],
            row["issue_combination_raw"],
        )
    )
    if omitted_known:
        selected.append(
            {
                "issue_combination_raw": "other_lower_volume_combinations",
                "lead_count": sum(row["lead_count"] for row in omitted_known),
            }
        )

    return [
        {
            "issue_combination": _display_issue_combination(row["issue_combination_raw"]),
            "issue_combination_raw": row["issue_combination_raw"],
            "lead_count": row["lead_count"],
            "share_of_cohort_leads": _percentage(row["lead_count"], total_leads),
        }
        for row in selected
    ]


def _combination_fragmentation_note(
    rows: list[dict[str, Any]],
    *,
    total_leads: int,
) -> str | None:
    other_row = next(
        (
            row
            for row in rows
            if row.get("issue_combination_raw") == "other_lower_volume_combinations"
        ),
        None,
    )
    if not other_row:
        return None
    if _percentage(other_row.get("lead_count"), total_leads) <= 40:
        return None
    return (
        "Reason combinations are fragmented, so the individual issue view is more "
        "useful than the combination view."
    )


def _individual_issue_distribution(
    rows: list[dict[str, Any]],
    *,
    total_leads: int,
    limit: int,
) -> list[dict[str, Any]]:
    issue_rows = [
        {
            "reason_category_raw": str(row.get("item_key") or "").strip(),
            "leads_with_issue": _int_or_none(row.get("lead_count")) or 0,
        }
        for row in rows
        if str(row.get("item_key") or "").strip()
    ]
    issue_rows.sort(
        key=lambda row: (
            -row["leads_with_issue"],
            row["reason_category_raw"],
        )
    )
    total_known_mentions = sum(row["leads_with_issue"] for row in issue_rows)
    return [
        {
            "reason_category": _reason_category_label(row["reason_category_raw"]),
            "reason_category_raw": row["reason_category_raw"],
            "leads_with_issue": row["leads_with_issue"],
            "share_of_cohort_leads": _percentage(row["leads_with_issue"], total_leads),
            "share_of_all_known_issue_mentions": _percentage(
                row["leads_with_issue"],
                total_known_mentions,
            ),
        }
        for row in issue_rows[:limit]
    ]


def _subcategory_distribution(
    rows: list[dict[str, Any]],
    *,
    total_leads: int,
    limit: int,
) -> list[dict[str, Any]]:
    subcategory_rows = [
        {
            "reason_subcategory_raw": str(row.get("item_key") or "").strip(),
            "leads_with_subcategory": _int_or_none(row.get("lead_count")) or 0,
        }
        for row in rows
        if str(row.get("item_key") or "").strip()
    ]
    subcategory_rows.sort(
        key=lambda row: (
            -row["leads_with_subcategory"],
            row["reason_subcategory_raw"],
        )
    )
    return [
        {
            "reason_subcategory": _reason_subcategory_label(row["reason_subcategory_raw"]),
            "reason_subcategory_raw": row["reason_subcategory_raw"],
            "leads_with_subcategory": row["leads_with_subcategory"],
            "share_of_cohort_leads": _percentage(
                row["leads_with_subcategory"],
                total_leads,
            ),
        }
        for row in subcategory_rows[:limit]
    ]


def _buying_intent_breakdown(
    rows: list[dict[str, Any]],
    *,
    total_leads: int,
) -> list[dict[str, Any]]:
    intent_rows = [
        {
            "buying_intent_level_raw": str(row.get("item_key") or "unknown").strip(),
            "lead_count": _int_or_none(row.get("lead_count")) or 0,
        }
        for row in rows
    ]
    intent_rows.sort(
        key=lambda row: (
            -row["lead_count"],
            row["buying_intent_level_raw"],
        )
    )
    return [
        {
            "buying_intent_level": _buying_intent_label(row["buying_intent_level_raw"]),
            "buying_intent_level_raw": row["buying_intent_level_raw"],
            "lead_count": row["lead_count"],
            "share_of_cohort_leads": _percentage(row["lead_count"], total_leads),
        }
        for row in intent_rows
    ]


def _recommended_focus_from_issues(
    individual_issue_distribution: list[dict[str, Any]],
    *,
    limit: int = 3,
) -> list[dict[str, Any]]:
    return [
        {
            "focus_area": row["reason_category"],
            "leads_with_issue": row["leads_with_issue"],
            "share_of_cohort_leads": row["share_of_cohort_leads"],
        }
        for row in individual_issue_distribution[:limit]
    ]


def _source_text_type_breakdown(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_rows = [
        {
            "source_text_type": str(row.get("item_key") or "unknown").strip(),
            "lead_count": _int_or_none(row.get("lead_count")) or 0,
        }
        for row in rows
    ]
    source_rows.sort(
        key=lambda row: (
            -row["lead_count"],
            row["source_text_type"],
        )
    )
    return source_rows


def _error_response(tool_name: str, error: Exception) -> str:
    return _json_response(
        {
            "status": "error",
            "tool": tool_name,
            "scope_note": SCOPE_NOTE,
            "row_count": 0,
            "error": str(error),
        }
    )


def _error_payload(tool_name: str, error: Exception) -> dict[str, Any]:
    return {
        "status": "error",
        "tool": tool_name,
        "scope_note": SCOPE_NOTE,
        "row_count": 0,
        "error": str(error),
    }


FUNNEL_SQL = """
WITH scoped AS (
  SELECT
    dls.lead_id AS lead_id,
    dls.funnel_stage AS funnel_stage,
    dls.conversion_outcome AS conversion_outcome,
    dls.appointment_count AS appointment_count,
    dls.completed_call_count AS completed_call_count,
    dls.no_show_count AS no_show_count,
    dls.signed_contract_count AS signed_contract_count,
    dls.paid_payment_count AS paid_payment_count,
    dls.gross_paid_amount AS gross_paid_amount,
    dls.refund_amount AS refund_amount,
    dls.net_collected_amount AS net_collected_amount,
    dls.outstanding_amount AS outstanding_amount
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
),
totals AS (
  SELECT
    COUNT(*)::int AS total_leads,
    COUNT(*) FILTER (WHERE appointment_count > 0)::int AS booked_leads,
    COUNT(*) FILTER (WHERE completed_call_count > 0)::int AS completed_call_leads,
    COUNT(*) FILTER (WHERE signed_contract_count > 0)::int AS signed_leads,
    COUNT(*) FILTER (WHERE paid_payment_count > 0)::int AS paid_leads,
    COALESCE(SUM(appointment_count), 0)::int AS appointment_count,
    COALESCE(SUM(completed_call_count), 0)::int AS completed_call_count,
    COALESCE(SUM(no_show_count), 0)::int AS no_show_count,
    COALESCE(SUM(signed_contract_count), 0)::int AS signed_contract_count,
    COALESCE(SUM(paid_payment_count), 0)::int AS paid_payment_count,
    COALESCE(SUM(gross_paid_amount), 0)::numeric(12,2) AS gross_paid_amount,
    COALESCE(SUM(refund_amount), 0)::numeric(12,2) AS refund_amount,
    COALESCE(SUM(net_collected_amount), 0)::numeric(12,2) AS net_collected_amount,
    COALESCE(SUM(outstanding_amount), 0)::numeric(12,2) AS outstanding_amount
  FROM scoped
),
funnel_steps AS (
  SELECT
    1 AS step_order,
    'total_leads' AS step_key,
    total_leads AS leads_reached,
    NULL::int AS previous_step_leads
  FROM totals
  UNION ALL
  SELECT
    2 AS step_order,
    'booked_call' AS step_key,
    booked_leads AS leads_reached,
    total_leads AS previous_step_leads
  FROM totals
  UNION ALL
  SELECT
    3 AS step_order,
    'completed_call' AS step_key,
    completed_call_leads AS leads_reached,
    booked_leads AS previous_step_leads
  FROM totals
  UNION ALL
  SELECT
    4 AS step_order,
    'signed_contract' AS step_key,
    signed_leads AS leads_reached,
    completed_call_leads AS previous_step_leads
  FROM totals
  UNION ALL
  SELECT
    5 AS step_order,
    'paid_converted' AS step_key,
    paid_leads AS leads_reached,
    signed_leads AS previous_step_leads
  FROM totals
),
stage_breakdown AS (
  SELECT
    funnel_stage,
    conversion_outcome,
    COUNT(*)::int AS lead_count,
    ROUND(100.0 * COUNT(*) / NULLIF((SELECT total_leads FROM totals), 0), 2) AS pct_of_leads,
    COALESCE(SUM(appointment_count), 0)::int AS appointment_count,
    COALESCE(SUM(completed_call_count), 0)::int AS completed_call_count,
    COALESCE(SUM(signed_contract_count), 0)::int AS signed_contract_count,
    COALESCE(SUM(paid_payment_count), 0)::int AS paid_payment_count,
    COALESCE(SUM(net_collected_amount), 0)::numeric(12,2) AS net_collected_amount
  FROM scoped
  GROUP BY funnel_stage, conversion_outcome
),
unioned AS (
  SELECT
    'total' AS row_type,
    NULL::int AS step_order,
    NULL::text AS step_key,
    NULL::text AS step_label,
    NULL::int AS leads_reached,
    NULL::int AS dropped_from_previous,
    NULL::numeric AS drop_rate_from_previous,
    NULL::numeric AS conversion_rate_from_previous,
    NULL::text AS funnel_stage,
    NULL::text AS display_label,
    NULL::text AS conversion_outcome,
    total_leads AS lead_count,
    NULL::numeric AS pct_of_leads,
    NULL::numeric AS pct_of_total_leads,
    NULL::text AS interpretation_hint,
    appointment_count,
    completed_call_count,
    no_show_count,
    signed_contract_count,
    paid_payment_count,
    NULL::int AS appointment_records,
    NULL::int AS completed_call_records,
    NULL::int AS no_show_records,
    NULL::int AS signed_contract_records,
    NULL::int AS paid_payment_records,
    gross_paid_amount,
    refund_amount,
    net_collected_amount,
    outstanding_amount
  FROM totals
  UNION ALL
  SELECT
    'funnel_flow' AS row_type,
    step_order,
    step_key,
    NULL::text AS step_label,
    leads_reached,
    CASE
      WHEN previous_step_leads IS NULL THEN NULL
      ELSE GREATEST(previous_step_leads - leads_reached, 0)
    END AS dropped_from_previous,
    CASE
      WHEN previous_step_leads IS NULL OR previous_step_leads = 0 THEN NULL
      ELSE ROUND(
        100.0 * GREATEST(previous_step_leads - leads_reached, 0) / previous_step_leads,
        2
      )
    END AS drop_rate_from_previous,
    CASE
      WHEN previous_step_leads IS NULL OR previous_step_leads = 0 THEN NULL
      ELSE ROUND(100.0 * leads_reached / previous_step_leads, 2)
    END AS conversion_rate_from_previous,
    NULL::text AS funnel_stage,
    NULL::text AS display_label,
    NULL::text AS conversion_outcome,
    NULL::int AS lead_count,
    NULL::numeric AS pct_of_leads,
    NULL::numeric AS pct_of_total_leads,
    NULL::text AS interpretation_hint,
    NULL::int AS appointment_count,
    NULL::int AS completed_call_count,
    NULL::int AS no_show_count,
    NULL::int AS signed_contract_count,
    NULL::int AS paid_payment_count,
    NULL::int AS appointment_records,
    NULL::int AS completed_call_records,
    NULL::int AS no_show_records,
    NULL::int AS signed_contract_records,
    NULL::int AS paid_payment_records,
    NULL::numeric AS gross_paid_amount,
    NULL::numeric AS refund_amount,
    NULL::numeric AS net_collected_amount,
    NULL::numeric AS outstanding_amount
  FROM funnel_steps
  UNION ALL
  SELECT
    'stage' AS row_type,
    NULL::int AS step_order,
    NULL::text AS step_key,
    NULL::text AS step_label,
    NULL::int AS leads_reached,
    NULL::int AS dropped_from_previous,
    NULL::numeric AS drop_rate_from_previous,
    NULL::numeric AS conversion_rate_from_previous,
    funnel_stage,
    NULL::text AS display_label,
    conversion_outcome,
    lead_count,
    pct_of_leads,
    pct_of_leads AS pct_of_total_leads,
    NULL::text AS interpretation_hint,
    appointment_count,
    completed_call_count,
    NULL::int AS no_show_count,
    signed_contract_count,
    paid_payment_count,
    NULL::int AS appointment_records,
    NULL::int AS completed_call_records,
    NULL::int AS no_show_records,
    NULL::int AS signed_contract_records,
    NULL::int AS paid_payment_records,
    NULL::numeric AS gross_paid_amount,
    NULL::numeric AS refund_amount,
    net_collected_amount,
    NULL::numeric AS outstanding_amount
  FROM stage_breakdown
  UNION ALL
  SELECT
    'activity_counts' AS row_type,
    NULL::int AS step_order,
    NULL::text AS step_key,
    NULL::text AS step_label,
    NULL::int AS leads_reached,
    NULL::int AS dropped_from_previous,
    NULL::numeric AS drop_rate_from_previous,
    NULL::numeric AS conversion_rate_from_previous,
    NULL::text AS funnel_stage,
    NULL::text AS display_label,
    NULL::text AS conversion_outcome,
    NULL::int AS lead_count,
    NULL::numeric AS pct_of_leads,
    NULL::numeric AS pct_of_total_leads,
    NULL::text AS interpretation_hint,
    appointment_count,
    completed_call_count,
    no_show_count,
    signed_contract_count,
    paid_payment_count,
    appointment_count AS appointment_records,
    completed_call_count AS completed_call_records,
    no_show_count AS no_show_records,
    signed_contract_count AS signed_contract_records,
    paid_payment_count AS paid_payment_records,
    NULL::numeric AS gross_paid_amount,
    NULL::numeric AS refund_amount,
    NULL::numeric AS net_collected_amount,
    NULL::numeric AS outstanding_amount
  FROM totals
)
SELECT
  row_type,
  step_order,
  step_key,
  step_label,
  leads_reached,
  dropped_from_previous,
  drop_rate_from_previous,
  conversion_rate_from_previous,
  funnel_stage,
  display_label,
  conversion_outcome,
  lead_count,
  pct_of_leads,
  pct_of_total_leads,
  interpretation_hint,
  appointment_count,
  completed_call_count,
  no_show_count,
  signed_contract_count,
  paid_payment_count,
  appointment_records,
  completed_call_records,
  no_show_records,
  signed_contract_records,
  paid_payment_records,
  gross_paid_amount,
  refund_amount,
  net_collected_amount,
  outstanding_amount
FROM unioned
ORDER BY
  CASE row_type
    WHEN 'total' THEN 1
    WHEN 'funnel_flow' THEN 2
    WHEN 'stage' THEN 3
    WHEN 'activity_counts' THEN 4
    ELSE 5
  END,
  step_order ASC,
  lead_count DESC,
  funnel_stage ASC,
  conversion_outcome ASC
"""

DROP_RECONCILIATION_SQL = """
WITH scoped AS (
  SELECT
    dls.lead_id AS lead_id,
    dls.appointment_count AS appointment_count,
    dls.completed_call_count AS completed_call_count,
    dls.signed_contract_count AS signed_contract_count,
    dls.paid_payment_count AS paid_payment_count,
    dls.net_collected_amount AS net_collected_amount,
    dls.funnel_stage AS funnel_stage,
    dls.conversion_outcome AS conversion_outcome
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
),
step_counts AS (
  SELECT
    COUNT(*)::int AS total_leads,
    COUNT(*) FILTER (WHERE appointment_count > 0)::int AS booked_leads,
    COUNT(*) FILTER (WHERE completed_call_count > 0)::int AS completed_call_leads,
    COUNT(*) FILTER (WHERE signed_contract_count > 0)::int AS signed_leads,
    COUNT(*) FILTER (WHERE paid_payment_count > 0)::int AS paid_leads
  FROM scoped
),
movement_drops AS (
  SELECT
    'lead_to_booked' AS drop_point_key,
    GREATEST(total_leads - booked_leads, 0)::int AS movement_dropped_leads
  FROM step_counts
  UNION ALL
  SELECT
    'booked_to_completed' AS drop_point_key,
    GREATEST(booked_leads - completed_call_leads, 0)::int AS movement_dropped_leads
  FROM step_counts
  UNION ALL
  SELECT
    'completed_to_signed' AS drop_point_key,
    GREATEST(completed_call_leads - signed_leads, 0)::int AS movement_dropped_leads
  FROM step_counts
  UNION ALL
  SELECT
    'signed_to_paid' AS drop_point_key,
    GREATEST(signed_leads - paid_leads, 0)::int AS movement_dropped_leads
  FROM step_counts
),
drop_sets AS (
  SELECT
    1 AS drop_point_order,
    'lead_to_booked' AS drop_point_key,
    lead_id,
    funnel_stage,
    conversion_outcome
  FROM scoped
  WHERE appointment_count = 0
  UNION ALL
  SELECT
    2 AS drop_point_order,
    'booked_to_completed' AS drop_point_key,
    lead_id,
    funnel_stage,
    conversion_outcome
  FROM scoped
  WHERE appointment_count > 0
    AND completed_call_count = 0
  UNION ALL
  SELECT
    3 AS drop_point_order,
    'completed_to_signed' AS drop_point_key,
    lead_id,
    funnel_stage,
    conversion_outcome
  FROM scoped
  WHERE completed_call_count > 0
    AND signed_contract_count = 0
  UNION ALL
  SELECT
    4 AS drop_point_order,
    'signed_to_paid' AS drop_point_key,
    lead_id,
    funnel_stage,
    conversion_outcome
  FROM scoped
  WHERE signed_contract_count > 0
    AND paid_payment_count = 0
),
later_without_previous AS (
  SELECT
    'lead_to_booked' AS drop_point_key,
    0::int AS offsetting_later_step_leads
  UNION ALL
  SELECT
    'booked_to_completed' AS drop_point_key,
    COUNT(*)::int AS offsetting_later_step_leads
  FROM scoped
  WHERE appointment_count = 0
    AND completed_call_count > 0
  UNION ALL
  SELECT
    'completed_to_signed' AS drop_point_key,
    COUNT(*)::int AS offsetting_later_step_leads
  FROM scoped
  WHERE completed_call_count = 0
    AND signed_contract_count > 0
  UNION ALL
  SELECT
    'signed_to_paid' AS drop_point_key,
    COUNT(*)::int AS offsetting_later_step_leads
  FROM scoped
  WHERE signed_contract_count = 0
    AND paid_payment_count > 0
),
reconciled AS (
  SELECT
    drop_point_order,
    drop_point_key,
    funnel_stage,
    conversion_outcome,
    COUNT(*)::int AS lead_count
  FROM drop_sets
  GROUP BY
    drop_point_order,
    drop_point_key,
    funnel_stage,
    conversion_outcome
),
drop_totals AS (
  SELECT
    drop_point_key,
    SUM(lead_count)::int AS drop_set_leads
  FROM reconciled
  GROUP BY drop_point_key
)
SELECT
  r.drop_point_key,
  m.movement_dropped_leads,
  t.drop_set_leads,
  o.offsetting_later_step_leads,
  r.funnel_stage,
  r.conversion_outcome,
  r.lead_count,
  CASE
    WHEN t.drop_set_leads = 0 THEN NULL
    ELSE ROUND(100.0 * r.lead_count / t.drop_set_leads, 2)
  END AS pct_of_drop_set_leads
FROM reconciled r
JOIN drop_totals t
  ON t.drop_point_key = r.drop_point_key
JOIN movement_drops m
  ON m.drop_point_key = r.drop_point_key
JOIN later_without_previous o
  ON o.drop_point_key = r.drop_point_key
ORDER BY
  r.drop_point_order ASC,
  r.lead_count DESC,
  r.funnel_stage ASC,
  r.conversion_outcome ASC
"""

STUCK_GROUP_FUNNEL_SQL = f"""
WITH lead_cohort AS (
  SELECT
    dls.lead_id AS lead_id,
    {FINAL_FUNNEL_STAGE_CASE_SQL} AS final_funnel_stage
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
),
totals AS (
  SELECT
    COUNT(DISTINCT lead_id)::int AS total_leads
  FROM lead_cohort
),
stage_order AS (
  SELECT
    1 AS stage_order,
    'never_booked' AS stage_key,
    'never_booked' AS cohort_name
  UNION ALL
  SELECT
    2 AS stage_order,
    'booked_not_completed' AS stage_key,
    'booked_not_completed' AS cohort_name
  UNION ALL
  SELECT
    3 AS stage_order,
    'completed_not_signed' AS stage_key,
    'completed_not_signed' AS cohort_name
  UNION ALL
  SELECT
    4 AS stage_order,
    'signed_not_paid' AS stage_key,
    'signed_not_paid' AS cohort_name
  UNION ALL
  SELECT
    5 AS stage_order,
    'paid_converted' AS stage_key,
    NULL::text AS cohort_name
),
stage_counts AS (
  SELECT
    final_funnel_stage AS stage_key,
    COUNT(DISTINCT lead_id)::int AS lead_count
  FROM lead_cohort
  GROUP BY final_funnel_stage
),
stage_rows AS (
  SELECT
    so.stage_order,
    so.stage_key,
    so.cohort_name,
    COALESCE(sc.lead_count, 0)::int AS lead_count
  FROM stage_order so
  LEFT JOIN stage_counts sc
    ON sc.stage_key = so.stage_key
),
unioned AS (
  SELECT
    stage_order,
    stage_key,
    cohort_name,
    lead_count
  FROM stage_rows
  UNION ALL
  SELECT
    6 AS stage_order,
    'total_leads' AS stage_key,
    NULL::text AS cohort_name,
    total_leads AS lead_count
  FROM totals
)
SELECT
  u.stage_order,
  u.stage_key,
  u.cohort_name,
  u.lead_count,
  t.total_leads,
  CASE
    WHEN t.total_leads = 0 THEN NULL
    ELSE ROUND(100.0 * u.lead_count / t.total_leads, 2)
  END AS pct_of_total_leads
FROM unioned u
CROSS JOIN totals t
ORDER BY u.stage_order ASC
"""

SOURCE_SNAPSHOT_SQL_TEMPLATE = """
WITH scoped AS (
  SELECT
    COALESCE(NULLIF(BTRIM(dls.{source_column}), ''), 'Unknown') AS source_name,
    dls.source_confidence AS source_confidence,
    dls.appointment_count AS appointment_count,
    dls.completed_call_count AS completed_call_count,
    dls.no_show_count AS no_show_count,
    dls.signed_contract_count AS signed_contract_count,
    dls.paid_payment_count AS paid_payment_count,
    dls.gross_paid_amount AS gross_paid_amount,
    dls.refund_amount AS refund_amount,
    dls.net_collected_amount AS net_collected_amount,
    dls.outstanding_amount AS outstanding_amount,
    dls.has_unknown_source AS has_unknown_source,
    dls.has_multiple_sources AS has_multiple_sources,
    dls.has_revenue_without_source AS has_revenue_without_source
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
),
source_rollup AS (
  SELECT
    source_name,
    COUNT(*)::int AS lead_count,
    COALESCE(SUM(appointment_count), 0)::int AS appointment_count,
    COALESCE(SUM(completed_call_count), 0)::int AS completed_call_count,
    COALESCE(SUM(no_show_count), 0)::int AS no_show_count,
    COALESCE(SUM(signed_contract_count), 0)::int AS signed_contract_count,
    COALESCE(SUM(paid_payment_count), 0)::int AS paid_payment_count,
    COALESCE(SUM(gross_paid_amount), 0)::numeric(12,2) AS gross_paid_amount,
    COALESCE(SUM(refund_amount), 0)::numeric(12,2) AS refund_amount,
    COALESCE(SUM(net_collected_amount), 0)::numeric(12,2) AS net_collected_amount,
    COALESCE(SUM(outstanding_amount), 0)::numeric(12,2) AS outstanding_amount,
    COUNT(*) FILTER (WHERE source_confidence = 'high')::int AS high_confidence_leads,
    COUNT(*) FILTER (WHERE source_confidence = 'medium')::int AS medium_confidence_leads,
    COUNT(*) FILTER (WHERE source_confidence = 'low')::int AS low_confidence_leads,
    COUNT(*) FILTER (WHERE has_unknown_source)::int AS unknown_source_leads,
    COUNT(*) FILTER (WHERE has_multiple_sources)::int AS multiple_source_leads,
    COUNT(*) FILTER (WHERE has_revenue_without_source)::int AS revenue_without_source_leads
  FROM scoped
  GROUP BY source_name
),
scored AS (
  SELECT
    source_name,
    lead_count,
    appointment_count,
    completed_call_count,
    no_show_count,
    signed_contract_count,
    paid_payment_count,
    gross_paid_amount,
    refund_amount,
    net_collected_amount,
    outstanding_amount,
    high_confidence_leads,
    medium_confidence_leads,
    low_confidence_leads,
    unknown_source_leads,
    multiple_source_leads,
    revenue_without_source_leads,
    ROUND(100.0 * appointment_count / NULLIF(lead_count, 0), 2) AS lead_to_appointment_rate,
    ROUND(100.0 * completed_call_count / NULLIF(appointment_count, 0), 2) AS appointment_to_completed_rate,
    ROUND(100.0 * signed_contract_count / NULLIF(completed_call_count, 0), 2) AS completed_to_signed_rate,
    ROUND(100.0 * paid_payment_count / NULLIF(signed_contract_count, 0), 2) AS signed_to_paid_rate,
    ROUND(net_collected_amount / NULLIF(lead_count, 0), 2) AS net_collected_per_lead,
    ROUND(net_collected_amount / NULLIF(completed_call_count, 0), 2)
      AS net_collected_per_completed_call
  FROM source_rollup
)
SELECT
  source_name,
  lead_count,
  appointment_count,
  completed_call_count,
  no_show_count,
  signed_contract_count,
  paid_payment_count,
  gross_paid_amount,
  refund_amount,
  net_collected_amount,
  outstanding_amount,
  lead_to_appointment_rate,
  appointment_to_completed_rate,
  completed_to_signed_rate,
  signed_to_paid_rate,
  net_collected_per_lead,
  net_collected_per_completed_call,
  high_confidence_leads,
  medium_confidence_leads,
  low_confidence_leads,
  unknown_source_leads,
  multiple_source_leads,
  revenue_without_source_leads
FROM scored
ORDER BY
  net_collected_amount DESC,
  signed_contract_count DESC,
  completed_call_count DESC,
  lead_count DESC,
  source_name ASC
LIMIT :limit
"""

SOURCE_QUALITY_SQL_TEMPLATE = """
WITH scoped AS (
  SELECT
    COALESCE(NULLIF(BTRIM(dls.{source_column}), ''), 'Unknown') AS source_name,
    dls.source_confidence AS source_confidence,
    dls.has_missing_first_source AS has_missing_first_source,
    dls.has_missing_last_source AS has_missing_last_source,
    dls.has_orphaned_first_source_id AS has_orphaned_first_source_id,
    dls.has_orphaned_last_source_id AS has_orphaned_last_source_id,
    dls.has_unknown_source AS has_unknown_source,
    dls.has_multiple_sources AS has_multiple_sources,
    dls.has_revenue_without_source AS has_revenue_without_source,
    dls.missing_utm_source AS missing_utm_source,
    dls.missing_utm_campaign AS missing_utm_campaign,
    dls.missing_landing_page AS missing_landing_page,
    dls.missing_referrer AS missing_referrer,
    dls.completed_calls_missing_fathom_count AS completed_calls_missing_fathom_count,
    dls.net_collected_amount AS net_collected_amount
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
),
totals AS (
  SELECT
    COUNT(*)::int AS total_leads,
    COALESCE(SUM(net_collected_amount), 0)::numeric(12,2) AS total_net_collected_amount,
    COUNT(*) FILTER (WHERE source_confidence = 'high')::int AS high_confidence_leads,
    COUNT(*) FILTER (WHERE source_confidence = 'medium')::int AS medium_confidence_leads,
    COUNT(*) FILTER (WHERE source_confidence = 'low')::int AS low_confidence_leads,
    COUNT(*) FILTER (WHERE has_unknown_source)::int AS unknown_source_leads,
    COUNT(*) FILTER (WHERE has_missing_first_source)::int AS missing_first_source_leads,
    COUNT(*) FILTER (WHERE has_missing_last_source)::int AS missing_last_source_leads,
    COUNT(*) FILTER (WHERE has_orphaned_first_source_id)::int AS orphaned_first_source_leads,
    COUNT(*) FILTER (WHERE has_orphaned_last_source_id)::int AS orphaned_last_source_leads,
    COUNT(*) FILTER (WHERE has_multiple_sources)::int AS multiple_source_leads,
    COUNT(*) FILTER (WHERE has_revenue_without_source)::int AS revenue_without_source_leads,
    COUNT(*) FILTER (WHERE missing_utm_source)::int AS missing_utm_source_leads,
    COUNT(*) FILTER (WHERE missing_utm_campaign)::int AS missing_utm_campaign_leads,
    COUNT(*) FILTER (WHERE missing_landing_page)::int AS missing_landing_page_leads,
    COUNT(*) FILTER (WHERE missing_referrer)::int AS missing_referrer_leads,
    COUNT(*) FILTER (WHERE completed_calls_missing_fathom_count > 0)::int
      AS leads_with_completed_calls_missing_fathom,
    COUNT(*) FILTER (
      WHERE source_confidence = 'low'
         OR has_unknown_source
         OR has_orphaned_first_source_id
         OR has_orphaned_last_source_id
         OR has_multiple_sources
    )::int AS issue_leads
  FROM scoped
),
overall AS (
  SELECT
    'overall' AS row_type,
    NULL::text AS source_name,
    total_leads AS lead_count,
    total_net_collected_amount AS net_collected_amount,
    high_confidence_leads,
    medium_confidence_leads,
    low_confidence_leads,
    unknown_source_leads,
    missing_first_source_leads,
    missing_last_source_leads,
    orphaned_first_source_leads,
    orphaned_last_source_leads,
    multiple_source_leads,
    revenue_without_source_leads,
    missing_utm_source_leads,
    missing_utm_campaign_leads,
    missing_landing_page_leads,
    missing_referrer_leads,
    leads_with_completed_calls_missing_fathom,
    issue_leads,
    ROUND(100.0 * issue_leads / NULLIF(total_leads, 0), 2) AS issue_lead_rate
  FROM totals
),
source_quality AS (
  SELECT
    'source' AS row_type,
    source_name,
    COUNT(*)::int AS lead_count,
    COALESCE(SUM(net_collected_amount), 0)::numeric(12,2) AS net_collected_amount,
    COUNT(*) FILTER (WHERE source_confidence = 'high')::int AS high_confidence_leads,
    COUNT(*) FILTER (WHERE source_confidence = 'medium')::int AS medium_confidence_leads,
    COUNT(*) FILTER (WHERE source_confidence = 'low')::int AS low_confidence_leads,
    COUNT(*) FILTER (WHERE has_unknown_source)::int AS unknown_source_leads,
    COUNT(*) FILTER (WHERE has_missing_first_source)::int AS missing_first_source_leads,
    COUNT(*) FILTER (WHERE has_missing_last_source)::int AS missing_last_source_leads,
    COUNT(*) FILTER (WHERE has_orphaned_first_source_id)::int AS orphaned_first_source_leads,
    COUNT(*) FILTER (WHERE has_orphaned_last_source_id)::int AS orphaned_last_source_leads,
    COUNT(*) FILTER (WHERE has_multiple_sources)::int AS multiple_source_leads,
    COUNT(*) FILTER (WHERE has_revenue_without_source)::int AS revenue_without_source_leads,
    COUNT(*) FILTER (WHERE missing_utm_source)::int AS missing_utm_source_leads,
    COUNT(*) FILTER (WHERE missing_utm_campaign)::int AS missing_utm_campaign_leads,
    COUNT(*) FILTER (WHERE missing_landing_page)::int AS missing_landing_page_leads,
    COUNT(*) FILTER (WHERE missing_referrer)::int AS missing_referrer_leads,
    COUNT(*) FILTER (WHERE completed_calls_missing_fathom_count > 0)::int
      AS leads_with_completed_calls_missing_fathom,
    COUNT(*) FILTER (
      WHERE source_confidence = 'low'
         OR has_unknown_source
         OR has_orphaned_first_source_id
         OR has_orphaned_last_source_id
         OR has_multiple_sources
    )::int AS issue_leads
  FROM scoped
  GROUP BY source_name
),
ranked_sources AS (
  SELECT
    row_type,
    source_name,
    lead_count,
    net_collected_amount,
    high_confidence_leads,
    medium_confidence_leads,
    low_confidence_leads,
    unknown_source_leads,
    missing_first_source_leads,
    missing_last_source_leads,
    orphaned_first_source_leads,
    orphaned_last_source_leads,
    multiple_source_leads,
    revenue_without_source_leads,
    missing_utm_source_leads,
    missing_utm_campaign_leads,
    missing_landing_page_leads,
    missing_referrer_leads,
    leads_with_completed_calls_missing_fathom,
    issue_leads,
    ROUND(100.0 * issue_leads / NULLIF(lead_count, 0), 2) AS issue_lead_rate
  FROM source_quality
  ORDER BY
    issue_leads DESC,
    low_confidence_leads DESC,
    unknown_source_leads DESC,
    lead_count DESC,
    source_name ASC
  LIMIT :limit
)
SELECT
  row_type,
  source_name,
  lead_count,
  net_collected_amount,
  high_confidence_leads,
  medium_confidence_leads,
  low_confidence_leads,
  unknown_source_leads,
  missing_first_source_leads,
  missing_last_source_leads,
  orphaned_first_source_leads,
  orphaned_last_source_leads,
  multiple_source_leads,
  revenue_without_source_leads,
  missing_utm_source_leads,
  missing_utm_campaign_leads,
  missing_landing_page_leads,
  missing_referrer_leads,
  leads_with_completed_calls_missing_fathom,
  issue_leads,
  issue_lead_rate
FROM overall
UNION ALL
SELECT
  row_type,
  source_name,
  lead_count,
  net_collected_amount,
  high_confidence_leads,
  medium_confidence_leads,
  low_confidence_leads,
  unknown_source_leads,
  missing_first_source_leads,
  missing_last_source_leads,
  orphaned_first_source_leads,
  orphaned_last_source_leads,
  multiple_source_leads,
  revenue_without_source_leads,
  missing_utm_source_leads,
  missing_utm_campaign_leads,
  missing_landing_page_leads,
  missing_referrer_leads,
  leads_with_completed_calls_missing_fathom,
  issue_leads,
  issue_lead_rate
FROM ranked_sources
ORDER BY
  row_type ASC,
  issue_leads DESC,
  source_name ASC
"""

BUSINESS_CHANGE_SQL = """
WITH period_rows AS (
  SELECT
    'current' AS period_name,
    dls.appointment_count AS appointment_count,
    dls.completed_call_count AS completed_call_count,
    dls.no_show_count AS no_show_count,
    dls.signed_contract_count AS signed_contract_count,
    dls.paid_payment_count AS paid_payment_count,
    dls.gross_paid_amount AS gross_paid_amount,
    dls.refund_amount AS refund_amount,
    dls.net_collected_amount AS net_collected_amount,
    dls.outstanding_amount AS outstanding_amount
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:current_start_date AS date)
    AND dls.lead_created_at < CAST(:current_end_date AS date)
  UNION ALL
  SELECT
    'previous' AS period_name,
    dls.appointment_count AS appointment_count,
    dls.completed_call_count AS completed_call_count,
    dls.no_show_count AS no_show_count,
    dls.signed_contract_count AS signed_contract_count,
    dls.paid_payment_count AS paid_payment_count,
    dls.gross_paid_amount AS gross_paid_amount,
    dls.refund_amount AS refund_amount,
    dls.net_collected_amount AS net_collected_amount,
    dls.outstanding_amount AS outstanding_amount
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:previous_start_date AS date)
    AND dls.lead_created_at < CAST(:previous_end_date AS date)
),
period_totals AS (
  SELECT
    period_name,
    COUNT(*)::int AS lead_count,
    COALESCE(SUM(appointment_count), 0)::int AS appointment_count,
    COALESCE(SUM(completed_call_count), 0)::int AS completed_call_count,
    COALESCE(SUM(no_show_count), 0)::int AS no_show_count,
    COALESCE(SUM(signed_contract_count), 0)::int AS signed_contract_count,
    COALESCE(SUM(paid_payment_count), 0)::int AS paid_payment_count,
    COALESCE(SUM(gross_paid_amount), 0)::numeric(12,2) AS gross_paid_amount,
    COALESCE(SUM(refund_amount), 0)::numeric(12,2) AS refund_amount,
    COALESCE(SUM(net_collected_amount), 0)::numeric(12,2) AS net_collected_amount,
    COALESCE(SUM(outstanding_amount), 0)::numeric(12,2) AS outstanding_amount,
    ROUND(100.0 * COALESCE(SUM(appointment_count), 0) / NULLIF(COUNT(*), 0), 2)
      AS lead_to_appointment_rate,
    ROUND(100.0 * COALESCE(SUM(completed_call_count), 0)
      / NULLIF(SUM(appointment_count), 0), 2) AS appointment_to_completed_rate,
    ROUND(100.0 * COALESCE(SUM(signed_contract_count), 0)
      / NULLIF(SUM(completed_call_count), 0), 2) AS completed_to_signed_rate,
    ROUND(100.0 * COALESCE(SUM(paid_payment_count), 0)
      / NULLIF(SUM(signed_contract_count), 0), 2) AS signed_to_paid_rate,
    ROUND(COALESCE(SUM(net_collected_amount), 0) / NULLIF(COUNT(*), 0), 2)
      AS net_collected_per_lead
  FROM period_rows
  GROUP BY period_name
),
pivoted AS (
  SELECT
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN lead_count END), 0) AS current_lead_count,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN lead_count END), 0) AS previous_lead_count,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN appointment_count END), 0)
      AS current_appointment_count,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN appointment_count END), 0)
      AS previous_appointment_count,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN completed_call_count END), 0)
      AS current_completed_call_count,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN completed_call_count END), 0)
      AS previous_completed_call_count,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN no_show_count END), 0)
      AS current_no_show_count,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN no_show_count END), 0)
      AS previous_no_show_count,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN signed_contract_count END), 0)
      AS current_signed_contract_count,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN signed_contract_count END), 0)
      AS previous_signed_contract_count,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN paid_payment_count END), 0)
      AS current_paid_payment_count,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN paid_payment_count END), 0)
      AS previous_paid_payment_count,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN gross_paid_amount END), 0)
      AS current_gross_paid_amount,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN gross_paid_amount END), 0)
      AS previous_gross_paid_amount,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN refund_amount END), 0)
      AS current_refund_amount,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN refund_amount END), 0)
      AS previous_refund_amount,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN net_collected_amount END), 0)
      AS current_net_collected_amount,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN net_collected_amount END), 0)
      AS previous_net_collected_amount,
    COALESCE(MAX(CASE WHEN period_name = 'current' THEN outstanding_amount END), 0)
      AS current_outstanding_amount,
    COALESCE(MAX(CASE WHEN period_name = 'previous' THEN outstanding_amount END), 0)
      AS previous_outstanding_amount,
    MAX(CASE WHEN period_name = 'current' THEN lead_to_appointment_rate END)
      AS current_lead_to_appointment_rate,
    MAX(CASE WHEN period_name = 'previous' THEN lead_to_appointment_rate END)
      AS previous_lead_to_appointment_rate,
    MAX(CASE WHEN period_name = 'current' THEN appointment_to_completed_rate END)
      AS current_appointment_to_completed_rate,
    MAX(CASE WHEN period_name = 'previous' THEN appointment_to_completed_rate END)
      AS previous_appointment_to_completed_rate,
    MAX(CASE WHEN period_name = 'current' THEN completed_to_signed_rate END)
      AS current_completed_to_signed_rate,
    MAX(CASE WHEN period_name = 'previous' THEN completed_to_signed_rate END)
      AS previous_completed_to_signed_rate,
    MAX(CASE WHEN period_name = 'current' THEN signed_to_paid_rate END)
      AS current_signed_to_paid_rate,
    MAX(CASE WHEN period_name = 'previous' THEN signed_to_paid_rate END)
      AS previous_signed_to_paid_rate,
    MAX(CASE WHEN period_name = 'current' THEN net_collected_per_lead END)
      AS current_net_collected_per_lead,
    MAX(CASE WHEN period_name = 'previous' THEN net_collected_per_lead END)
      AS previous_net_collected_per_lead
  FROM period_totals
)
SELECT
  metric_name,
  current_value,
  previous_value,
  current_value - previous_value AS absolute_change,
  CASE
    WHEN previous_value = 0 THEN NULL
    ELSE ROUND(100.0 * (current_value - previous_value) / previous_value, 2)
  END AS percentage_change
FROM pivoted,
LATERAL (
  VALUES
    ('lead_count', current_lead_count::numeric, previous_lead_count::numeric),
    ('appointment_count', current_appointment_count::numeric, previous_appointment_count::numeric),
    (
      'completed_call_count',
      current_completed_call_count::numeric,
      previous_completed_call_count::numeric
    ),
    ('no_show_count', current_no_show_count::numeric, previous_no_show_count::numeric),
    (
      'signed_contract_count',
      current_signed_contract_count::numeric,
      previous_signed_contract_count::numeric
    ),
    (
      'paid_payment_count',
      current_paid_payment_count::numeric,
      previous_paid_payment_count::numeric
    ),
    ('gross_paid_amount', current_gross_paid_amount::numeric, previous_gross_paid_amount::numeric),
    ('refund_amount', current_refund_amount::numeric, previous_refund_amount::numeric),
    (
      'net_collected_amount',
      current_net_collected_amount::numeric,
      previous_net_collected_amount::numeric
    ),
    (
      'outstanding_amount',
      current_outstanding_amount::numeric,
      previous_outstanding_amount::numeric
    ),
    (
      'lead_to_appointment_rate',
      current_lead_to_appointment_rate::numeric,
      previous_lead_to_appointment_rate::numeric
    ),
    (
      'appointment_to_completed_rate',
      current_appointment_to_completed_rate::numeric,
      previous_appointment_to_completed_rate::numeric
    ),
    (
      'completed_to_signed_rate',
      current_completed_to_signed_rate::numeric,
      previous_completed_to_signed_rate::numeric
    ),
    (
      'signed_to_paid_rate',
      current_signed_to_paid_rate::numeric,
      previous_signed_to_paid_rate::numeric
    ),
    (
      'net_collected_per_lead',
      current_net_collected_per_lead::numeric,
      previous_net_collected_per_lead::numeric
    )
) AS metrics(metric_name, current_value, previous_value)
ORDER BY
  ABS(current_value - previous_value) DESC NULLS LAST,
  metric_name ASC
"""

RECOMMENDED_TEXT_COHORTS_SQL = STUCK_GROUP_FUNNEL_SQL

TEXT_REASON_SQL_TEMPLATE = """
WITH period_leads AS (
  SELECT
    dls.clerk_org_id AS clerk_org_id,
    dls.lead_id AS lead_id,
    dls.appointment_count AS appointment_count,
    dls.completed_call_count AS completed_call_count,
    dls.signed_contract_count AS signed_contract_count,
    dls.paid_payment_count AS paid_payment_count
  FROM diagnostic_lead_snapshot dls
  WHERE dls.clerk_org_id = :org_id
    AND dls.lead_created_at >= CAST(:start_date AS date)
    AND dls.lead_created_at < CAST(:end_date AS date)
),
scoped_leads AS (
  SELECT
    dls.clerk_org_id AS clerk_org_id,
    dls.lead_id AS lead_id
  FROM period_leads dls
  WHERE dls.clerk_org_id = :org_id
    AND {cohort_condition}
),
text_rows AS (
  SELECT
    sl.lead_id AS lead_id,
    dti.reason_category AS reason_category,
    dti.reason_subcategory AS reason_subcategory,
    dti.is_conversion_blocker AS is_conversion_blocker,
    dti.buying_intent_level AS buying_intent_level,
    dti.lead_quality_level AS lead_quality_level,
    dti.profession_category AS profession_category,
    dti.employment_status AS employment_status,
    dti.source_text_type AS source_text_type
  FROM scoped_leads sl
  LEFT JOIN diagnostic_text_insights dti
    ON dti.clerk_org_id = sl.clerk_org_id
   AND dti.lead_id = sl.lead_id
  WHERE dti.extraction_status = 'success'
    AND (:blockers_only = false OR dti.is_conversion_blocker = true)
),
known_reasons_per_lead AS (
  SELECT DISTINCT
    lead_id,
    reason_category
  FROM text_rows
  WHERE reason_category IS NOT NULL
    AND reason_category <> 'unknown'
),
known_subcategories_per_lead AS (
  SELECT DISTINCT
    lead_id,
    reason_subcategory
  FROM text_rows
  WHERE reason_subcategory IS NOT NULL
    AND reason_subcategory <> 'unknown'
),
buying_intent_per_lead AS (
  SELECT DISTINCT
    lead_id,
    COALESCE(NULLIF(BTRIM(buying_intent_level), ''), 'unknown') AS buying_intent_level
  FROM text_rows
),
source_text_type_per_lead AS (
  SELECT DISTINCT
    lead_id,
    COALESCE(NULLIF(BTRIM(source_text_type), ''), 'unknown') AS source_text_type
  FROM text_rows
),
text_coverage_per_lead AS (
  SELECT
    sl.lead_id AS lead_id,
    COUNT(tr.lead_id)::int AS text_insight_count,
    COUNT(DISTINCT kr.reason_category)::int AS known_reason_count
  FROM scoped_leads sl
  LEFT JOIN text_rows tr
    ON tr.lead_id = sl.lead_id
  LEFT JOIN known_reasons_per_lead kr
    ON kr.lead_id = sl.lead_id
  GROUP BY sl.lead_id
),
lead_reason_combinations AS (
  SELECT
    sl.lead_id AS lead_id,
    CASE
      WHEN COUNT(kr.reason_category) > 0
      THEN STRING_AGG(kr.reason_category, ' + ' ORDER BY kr.reason_category)
      WHEN MAX(tc.text_insight_count) > 0
      THEN 'unknown_reason'
      ELSE 'no_text_insight_available'
    END AS issue_combination_raw
  FROM scoped_leads sl
  LEFT JOIN known_reasons_per_lead kr
    ON kr.lead_id = sl.lead_id
  LEFT JOIN text_coverage_per_lead tc
    ON tc.lead_id = sl.lead_id
  GROUP BY sl.lead_id
),
coverage AS (
  SELECT
    'coverage' AS row_type,
    NULL::text AS item_key,
    NULL::int AS lead_count,
    COUNT(sl.lead_id)::int AS total_cohort_leads,
    COUNT(*) FILTER (WHERE tc.text_insight_count > 0)::int AS leads_with_text_insights,
    COUNT(*) FILTER (WHERE tc.known_reason_count > 0)::int AS known_reason_leads,
    COUNT(*) FILTER (
      WHERE tc.text_insight_count > 0
        AND tc.known_reason_count = 0
    )::int AS unknown_only_reason_leads
  FROM scoped_leads sl
  LEFT JOIN text_coverage_per_lead tc
    ON tc.lead_id = sl.lead_id
),
combination_rollup AS (
  SELECT
    'combination' AS row_type,
    issue_combination_raw AS item_key,
    COUNT(*)::int AS lead_count,
    NULL::int AS total_cohort_leads,
    NULL::int AS leads_with_text_insights,
    NULL::int AS known_reason_leads,
    NULL::int AS unknown_only_reason_leads
  FROM lead_reason_combinations
  GROUP BY issue_combination_raw
),
issue_rollup AS (
  SELECT
    'issue' AS row_type,
    reason_category AS item_key,
    COUNT(DISTINCT lead_id)::int AS lead_count,
    NULL::int AS total_cohort_leads,
    NULL::int AS leads_with_text_insights,
    NULL::int AS known_reason_leads,
    NULL::int AS unknown_only_reason_leads
  FROM known_reasons_per_lead
  GROUP BY reason_category
),
subcategory_rollup AS (
  SELECT
    'subcategory' AS row_type,
    reason_subcategory AS item_key,
    COUNT(DISTINCT lead_id)::int AS lead_count,
    NULL::int AS total_cohort_leads,
    NULL::int AS leads_with_text_insights,
    NULL::int AS known_reason_leads,
    NULL::int AS unknown_only_reason_leads
  FROM known_subcategories_per_lead
  GROUP BY reason_subcategory
),
buying_intent_rollup AS (
  SELECT
    'buying_intent' AS row_type,
    buying_intent_level AS item_key,
    COUNT(DISTINCT lead_id)::int AS lead_count,
    NULL::int AS total_cohort_leads,
    NULL::int AS leads_with_text_insights,
    NULL::int AS known_reason_leads,
    NULL::int AS unknown_only_reason_leads
  FROM buying_intent_per_lead
  GROUP BY buying_intent_level
),
source_text_type_rollup AS (
  SELECT
    'source_text_type' AS row_type,
    source_text_type AS item_key,
    COUNT(DISTINCT lead_id)::int AS lead_count,
    NULL::int AS total_cohort_leads,
    NULL::int AS leads_with_text_insights,
    NULL::int AS known_reason_leads,
    NULL::int AS unknown_only_reason_leads
  FROM source_text_type_per_lead
  GROUP BY source_text_type
),
unioned AS (
  SELECT
    row_type,
    item_key,
    lead_count,
    total_cohort_leads,
    leads_with_text_insights,
    known_reason_leads,
    unknown_only_reason_leads
  FROM coverage
  UNION ALL
  SELECT
    row_type,
    item_key,
    lead_count,
    total_cohort_leads,
    leads_with_text_insights,
    known_reason_leads,
    unknown_only_reason_leads
  FROM combination_rollup
  UNION ALL
  SELECT
    row_type,
    item_key,
    lead_count,
    total_cohort_leads,
    leads_with_text_insights,
    known_reason_leads,
    unknown_only_reason_leads
  FROM issue_rollup
  UNION ALL
  SELECT
    row_type,
    item_key,
    lead_count,
    total_cohort_leads,
    leads_with_text_insights,
    known_reason_leads,
    unknown_only_reason_leads
  FROM subcategory_rollup
  UNION ALL
  SELECT
    row_type,
    item_key,
    lead_count,
    total_cohort_leads,
    leads_with_text_insights,
    known_reason_leads,
    unknown_only_reason_leads
  FROM buying_intent_rollup
  UNION ALL
  SELECT
    row_type,
    item_key,
    lead_count,
    total_cohort_leads,
    leads_with_text_insights,
    known_reason_leads,
    unknown_only_reason_leads
  FROM source_text_type_rollup
)
SELECT
  row_type,
  item_key,
  lead_count,
  total_cohort_leads,
  leads_with_text_insights,
  known_reason_leads,
  unknown_only_reason_leads
FROM unioned
ORDER BY
  CASE row_type
    WHEN 'coverage' THEN 1
    WHEN 'combination' THEN 2
    WHEN 'issue' THEN 3
    WHEN 'subcategory' THEN 4
    WHEN 'buying_intent' THEN 5
    WHEN 'source_text_type' THEN 6
    ELSE 7
  END,
  lead_count DESC NULLS LAST,
  item_key ASC
"""


def get_diagnostic_funnel_snapshot(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
) -> dict[str, Any]:
    try:
        clean_org_id = _default_org_id(org_id)
        periods = _default_periods(clean_org_id, current_start_date, current_end_date, None, None)
        params = {
            "org_id": clean_org_id,
            "start_date": periods["current_start_date"],
            "end_date": periods["current_end_date"],
        }
        rows = _query_records(FUNNEL_SQL, params, max_rows=100)
        drop_rows = _query_records(DROP_RECONCILIATION_SQL, params, max_rows=100)
        stuck_group_rows = _query_records(STUCK_GROUP_FUNNEL_SQL, params, max_rows=10)
        sections = _funnel_sections(rows)
        stuck_group_funnel = _stuck_group_funnel(stuck_group_rows)
        stage_validation = _stuck_group_validation(stuck_group_funnel)
        period_metadata = _period_metadata(
            periods["current_start_date"],
            periods["current_end_date"],
            periods["period_anchor_date"],
        )
        if not stage_validation["stage_counts_reconcile"]:
            return _json_ready(
                {
                    "status": "validation_failed",
                    "tool": "get_diagnostic_funnel_snapshot",
                    "scope_note": SCOPE_NOTE,
                    "row_count": stage_validation["total_leads"],
                    "period": period_metadata,
                    "safe_message": stage_validation["safe_message"],
                    "funnel_stage_validation": stage_validation,
                    "stuck_group_funnel": [],
                    "largest_stuck_group": None,
                    "selected_text_reason_cohort": None,
                    "recommended_text_cohorts": [],
                }
            )
        recommended_text_cohorts = _recommended_text_cohorts(stuck_group_funnel)
        return _json_ready(
            {
                "status": "success",
                "tool": "get_diagnostic_funnel_snapshot",
                "scope_note": SCOPE_NOTE,
                "row_count": sections["total_leads"],
                "period": period_metadata,
                "stuck_group_funnel": stuck_group_funnel,
                "funnel_stage_validation": stage_validation,
                "largest_stuck_group": _largest_stuck_group(stuck_group_funnel),
                "selected_text_reason_cohort": (
                    recommended_text_cohorts[0] if recommended_text_cohorts else None
                ),
                "funnel_flow": sections["funnel_flow"],
                "drop_reconciliation": _drop_reconciliation(drop_rows),
                "final_position_breakdown": sections["final_position_breakdown"],
                "recommended_text_cohorts": recommended_text_cohorts,
                "activity_counts": sections["activity_counts"],
                "rows": rows,
            }
        )
    except Exception as exc:  # noqa: BLE001 - public tool payloads should stay structured.
        return _error_payload("get_diagnostic_funnel_snapshot", exc)


def get_diagnostic_source_snapshot(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    source_basis: str = "first",
    limit: int = 10,
) -> dict[str, Any]:
    try:
        clean_org_id = _default_org_id(org_id)
        periods = _default_periods(clean_org_id, current_start_date, current_end_date, None, None)
        safe_limit = _safe_limit(limit)
        source_column = _source_column(source_basis)
        sql = SOURCE_SNAPSHOT_SQL_TEMPLATE.format(source_column=source_column)
        params = {
            "org_id": clean_org_id,
            "start_date": periods["current_start_date"],
            "end_date": periods["current_end_date"],
            "limit": safe_limit,
        }
        rows = _query_records(sql, params, max_rows=safe_limit)
        return _json_ready(
            {
                "status": "success",
                "tool": "get_diagnostic_source_snapshot",
                "scope_note": SCOPE_NOTE,
                "row_count": len(rows),
                "source_basis": str(source_basis or "first").strip().lower(),
                "period": _period_metadata(
                    periods["current_start_date"],
                    periods["current_end_date"],
                    periods["period_anchor_date"],
                ),
                "rows": rows,
            }
        )
    except Exception as exc:  # noqa: BLE001 - public tool payloads should stay structured.
        return _error_payload("get_diagnostic_source_snapshot", exc)


def get_diagnostic_source_quality_snapshot(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    source_basis: str = "first",
    limit: int = 20,
) -> dict[str, Any]:
    try:
        clean_org_id = _default_org_id(org_id)
        periods = _default_periods(clean_org_id, current_start_date, current_end_date, None, None)
        safe_limit = _safe_limit(limit, default=20)
        source_column = _source_column(source_basis)
        sql = SOURCE_QUALITY_SQL_TEMPLATE.format(source_column=source_column)
        params = {
            "org_id": clean_org_id,
            "start_date": periods["current_start_date"],
            "end_date": periods["current_end_date"],
            "limit": safe_limit,
        }
        rows = _query_records(sql, params, max_rows=safe_limit + 1)
        overall = next((row for row in rows if row.get("row_type") == "overall"), None)
        sources = [row for row in rows if row.get("row_type") == "source"]
        return _json_ready(
            {
                "status": "success",
                "tool": "get_diagnostic_source_quality_snapshot",
                "scope_note": SCOPE_NOTE,
                "row_count": len(rows),
                "source_basis": str(source_basis or "first").strip().lower(),
                "period": _period_metadata(
                    periods["current_start_date"],
                    periods["current_end_date"],
                    periods["period_anchor_date"],
                ),
                "overall": overall,
                "sources": sources,
                "rows": rows,
            }
        )
    except Exception as exc:  # noqa: BLE001 - public tool payloads should stay structured.
        return _error_payload("get_diagnostic_source_quality_snapshot", exc)


def get_diagnostic_business_change_snapshot(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    previous_start_date: str | None = None,
    previous_end_date: str | None = None,
) -> dict[str, Any]:
    try:
        clean_org_id = _default_org_id(org_id)
        periods = _default_periods(
            clean_org_id,
            current_start_date,
            current_end_date,
            previous_start_date,
            previous_end_date,
        )
        params = {
            "org_id": clean_org_id,
            "current_start_date": periods["current_start_date"],
            "current_end_date": periods["current_end_date"],
            "previous_start_date": periods["previous_start_date"],
            "previous_end_date": periods["previous_end_date"],
        }
        rows = _query_records(BUSINESS_CHANGE_SQL, params, max_rows=100)
        return _json_ready(
            {
                "status": "success",
                "tool": "get_diagnostic_business_change_snapshot",
                "scope_note": SCOPE_NOTE,
                "row_count": len(rows),
                "periods": {
                    "current": _period_metadata(
                        periods["current_start_date"],
                        periods["current_end_date"],
                        periods["period_anchor_date"],
                    ),
                    "previous": _period_metadata(
                        periods["previous_start_date"],
                        periods["previous_end_date"],
                        periods["period_anchor_date"],
                    ),
                },
                "rows": rows,
            }
        )
    except Exception as exc:  # noqa: BLE001 - public tool payloads should stay structured.
        return _error_payload("get_diagnostic_business_change_snapshot", exc)


def get_diagnostic_text_reason_snapshot(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    cohort_name: str = "completed_not_signed",
    reason_limit: int = 10,
    combination_limit: int = 10,
    subcategory_limit: int = 10,
    blockers_only: bool = False,
    include_issue_combinations: bool = False,
) -> dict[str, Any]:
    try:
        cohort_metadata = _text_cohort_metadata(cohort_name)
        clean_org_id = _default_org_id(org_id)
        periods = _default_periods(clean_org_id, current_start_date, current_end_date, None, None)
        safe_reason_limit = _safe_top_limit(reason_limit)
        safe_combination_limit = _safe_top_limit(combination_limit)
        safe_subcategory_limit = _safe_top_limit(subcategory_limit)
        sql = TEXT_REASON_SQL_TEMPLATE.format(
            cohort_condition=cohort_metadata["condition"],
        )
        params = {
            "org_id": clean_org_id,
            "start_date": periods["current_start_date"],
            "end_date": periods["current_end_date"],
            "blockers_only": bool(blockers_only),
        }
        rows = _query_records(sql, params, max_rows=5000)
        grouped_rows = _split_text_reason_rows(rows)
        coverage_row = grouped_rows["coverage"][0] if grouped_rows["coverage"] else {}
        total_leads = _int_or_none(coverage_row.get("total_cohort_leads")) or 0
        text_insight_coverage = _text_reason_coverage(coverage_row)
        reason_combination_distribution = _limited_combination_distribution(
            grouped_rows["combination"],
            total_leads=total_leads,
            limit=safe_combination_limit,
        )
        combination_total = sum(
            row["lead_count"] for row in reason_combination_distribution
        )
        tables_reconcile = (
            combination_total == total_leads
            and bool(text_insight_coverage["coverage_reconciles"])
        )
        common_payload = {
            "tool": "get_diagnostic_text_reason_snapshot",
            "scope_note": SCOPE_NOTE,
            "period": _period_metadata(
                periods["current_start_date"],
                periods["current_end_date"],
                periods["period_anchor_date"],
            ),
            "cohort": {
                "cohort_name": cohort_metadata["cohort_name"],
                "cohort_label": cohort_metadata["cohort_label"],
                "cohort_definition": cohort_metadata["cohort_definition"],
                "total_leads": total_leads,
            },
            "text_insight_coverage": text_insight_coverage,
            "display_limits": {
                "reason_limit": safe_reason_limit,
                "combination_limit": safe_combination_limit,
                "subcategory_limit": safe_subcategory_limit,
            },
            "default_answer_guidance": {
                "show_issue_combinations_by_default": False,
                "issue_combination_table_returned": bool(include_issue_combinations),
                "individual_issue_note": (
                    "One lead can have multiple issues, so the individual issue table "
                    f"does not sum to {total_leads}."
                ),
            },
            "reconciliation": {
                "selected_cohort_leads": total_leads,
                "reason_combination_total": combination_total,
                "coverage_total": text_insight_coverage["total_cohort_leads"],
                "tables_reconcile": tables_reconcile,
            },
            "row_count": total_leads,
        }
        if not tables_reconcile:
            return _json_ready(
                {
                    **common_payload,
                    "status": "limited",
                    "reason_combination_distribution": [],
                    "individual_issue_distribution": [],
                    "recommended_focus": [],
                    "top_reason_subcategories": [],
                    "buying_intent_breakdown": [],
                    "source_text_type_breakdown": [],
                    "limitations": [
                        (
                            "The text reason breakdown could not be safely reconciled "
                            "with the selected funnel cohort, so reason tables should "
                            "not be shown for this answer."
                        ),
                    ],
                }
            )

        fragmentation_note = _combination_fragmentation_note(
            reason_combination_distribution,
            total_leads=total_leads,
        )
        individual_issue_distribution = _individual_issue_distribution(
            grouped_rows["issue"],
            total_leads=total_leads,
            limit=safe_reason_limit,
        )

        return _json_ready(
            {
                **common_payload,
                "status": "success",
                "reason_combination_distribution": (
                    reason_combination_distribution if include_issue_combinations else []
                ),
                "combination_fragmentation_note": (
                    fragmentation_note if include_issue_combinations else None
                ),
                "individual_issue_distribution": individual_issue_distribution,
                "recommended_focus": _recommended_focus_from_issues(
                    individual_issue_distribution,
                ),
                "top_reason_subcategories": _subcategory_distribution(
                    grouped_rows["subcategory"],
                    total_leads=total_leads,
                    limit=safe_subcategory_limit,
                ),
                "buying_intent_breakdown": _buying_intent_breakdown(
                    grouped_rows["buying_intent"],
                    total_leads=total_leads,
                ),
                "source_text_type_breakdown": _source_text_type_breakdown(
                    grouped_rows["source_text_type"],
                ),
                "limitations": [
                    (
                        "Text reasons are extracted from available structured text "
                        "insight enums, not raw transcripts."
                    ),
                    (
                        "One lead may have multiple issues, so individual issue counts "
                        "do not sum to the cohort total."
                    ),
                    (
                        "The combination distribution assigns each lead to exactly one "
                        "combination row and must sum to the cohort total, but it is "
                        "returned only when include_issue_combinations is true."
                    ),
                ],
            }
        )
    except Exception as exc:  # noqa: BLE001 - public tool payloads should stay structured.
        return _error_payload("get_diagnostic_text_reason_snapshot", exc)


def _get_diagnostic_funnel_snapshot_tool(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
) -> str:
    """Return funnel-stage evidence from diagnostic_lead_snapshot.

    Dates use lead_created_at cohort logic. If org_id is omitted, the tool uses
    HERMON_DEFAULT_CLERK_ORG_ID.
    """

    try:
        return _json_response(
            get_diagnostic_funnel_snapshot(
                org_id=org_id,
                current_start_date=current_start_date,
                current_end_date=current_end_date,
            )
        )
    except Exception as exc:  # noqa: BLE001 - tool output should stay JSON.
        return _error_response("get_diagnostic_funnel_snapshot", exc)


def _get_diagnostic_source_snapshot_tool(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    source_basis: str = "first",
    limit: int = 10,
) -> str:
    """Return source performance evidence from diagnostic_lead_snapshot.

    source_basis must be first or last. Dates use lead_created_at cohort logic.
    """

    try:
        return _json_response(
            get_diagnostic_source_snapshot(
                org_id=org_id,
                current_start_date=current_start_date,
                current_end_date=current_end_date,
                source_basis=source_basis,
                limit=limit,
            )
        )
    except Exception as exc:  # noqa: BLE001 - tool output should stay JSON.
        return _error_response("get_diagnostic_source_snapshot", exc)


def _get_diagnostic_source_quality_snapshot_tool(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    source_basis: str = "first",
    limit: int = 20,
) -> str:
    """Return source trust and data-quality evidence from diagnostic_lead_snapshot.

    source_basis must be first or last. Dates use lead_created_at cohort logic.
    """

    try:
        return _json_response(
            get_diagnostic_source_quality_snapshot(
                org_id=org_id,
                current_start_date=current_start_date,
                current_end_date=current_end_date,
                source_basis=source_basis,
                limit=limit,
            )
        )
    except Exception as exc:  # noqa: BLE001 - tool output should stay JSON.
        return _error_response("get_diagnostic_source_quality_snapshot", exc)


def _get_diagnostic_business_change_snapshot_tool(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    previous_start_date: str | None = None,
    previous_end_date: str | None = None,
) -> str:
    """Return current-vs-previous business change evidence from the snapshot.

    Dates use lead_created_at cohort logic.
    """

    try:
        return _json_response(
            get_diagnostic_business_change_snapshot(
                org_id=org_id,
                current_start_date=current_start_date,
                current_end_date=current_end_date,
                previous_start_date=previous_start_date,
                previous_end_date=previous_end_date,
            )
        )
    except Exception as exc:  # noqa: BLE001 - tool output should stay JSON.
        return _error_response("get_diagnostic_business_change_snapshot", exc)


def _get_diagnostic_text_reason_snapshot_tool(
    org_id: str | None = None,
    current_start_date: str | None = None,
    current_end_date: str | None = None,
    cohort_name: str = "completed_not_signed",
    reason_limit: int = 10,
    combination_limit: int = 10,
    subcategory_limit: int = 10,
    blockers_only: bool = False,
    include_issue_combinations: bool = False,
) -> str:
    """Return safe text-reason evidence for a diagnostic dropped/stuck cohort.

    Dates use lead_created_at cohort logic. Text evidence is aggregated to
    distinct leads and does not expose raw text or source records. Set
    include_issue_combinations only when the user explicitly asks for issue
    combinations or patterns.
    """

    try:
        return _json_response(
            get_diagnostic_text_reason_snapshot(
                org_id=org_id,
                current_start_date=current_start_date,
                current_end_date=current_end_date,
                cohort_name=cohort_name,
                reason_limit=reason_limit,
                combination_limit=combination_limit,
                subcategory_limit=subcategory_limit,
                blockers_only=blockers_only,
                include_issue_combinations=include_issue_combinations,
            )
        )
    except Exception as exc:  # noqa: BLE001 - tool output should stay JSON.
        return _error_response("get_diagnostic_text_reason_snapshot", exc)


get_diagnostic_funnel_snapshot_tool = tool("get_diagnostic_funnel_snapshot")(
    _get_diagnostic_funnel_snapshot_tool
)
get_diagnostic_source_snapshot_tool = tool("get_diagnostic_source_snapshot")(
    _get_diagnostic_source_snapshot_tool
)
get_diagnostic_source_quality_snapshot_tool = tool("get_diagnostic_source_quality_snapshot")(
    _get_diagnostic_source_quality_snapshot_tool
)
get_diagnostic_business_change_snapshot_tool = tool("get_diagnostic_business_change_snapshot")(
    _get_diagnostic_business_change_snapshot_tool
)
get_diagnostic_text_reason_snapshot_tool = tool("get_diagnostic_text_reason_snapshot")(
    _get_diagnostic_text_reason_snapshot_tool
)

DIAGNOSTIC_TOOLS = [
    get_diagnostic_funnel_snapshot_tool,
    get_diagnostic_source_snapshot_tool,
    get_diagnostic_source_quality_snapshot_tool,
    get_diagnostic_business_change_snapshot_tool,
    get_diagnostic_text_reason_snapshot_tool,
]
