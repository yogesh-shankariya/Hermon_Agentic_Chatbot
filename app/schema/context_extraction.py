from enum import Enum
from pydantic import BaseModel, ConfigDict


class ReasonCategory(str, Enum):
    price_or_budget = "price_or_budget"
    timing_issue = "timing_issue"
    not_decision_maker = "not_decision_maker"
    needs_partner_approval = "needs_partner_approval"
    trust_issue = "trust_issue"
    low_intent = "low_intent"
    unclear_need = "unclear_need"
    poor_fit = "poor_fit"
    competition = "competition"
    too_busy = "too_busy"
    needs_more_information = "needs_more_information"
    payment_friction = "payment_friction"
    contract_friction = "contract_friction"
    no_show = "no_show"
    ghosted = "ghosted"
    follow_up_pending = "follow_up_pending"
    operational_delay = "operational_delay"
    technical_issue = "technical_issue"
    language_or_communication_issue = "language_or_communication_issue"
    location_or_timezone_issue = "location_or_timezone_issue"
    already_solved = "already_solved"
    unknown = "unknown"


class ReasonSubcategory(str, Enum):
    price_too_high = "price_too_high"
    budget_not_available = "budget_not_available"
    wants_discount = "wants_discount"
    needs_payment_plan = "needs_payment_plan"
    not_ready_now = "not_ready_now"
    needs_more_time = "needs_more_time"
    waiting_for_partner = "waiting_for_partner"
    waiting_for_team = "waiting_for_team"
    waiting_for_finance = "waiting_for_finance"
    does_not_trust_offer = "does_not_trust_offer"
    needs_proof_or_case_study = "needs_proof_or_case_study"
    unclear_value = "unclear_value"
    comparing_competitor = "comparing_competitor"
    not_enough_need = "not_enough_need"
    wrong_customer_fit = "wrong_customer_fit"
    not_qualified = "not_qualified"
    missed_call = "missed_call"
    cancelled_call = "cancelled_call"
    stopped_responding = "stopped_responding"
    needs_more_information = "needs_more_information"
    contract_not_signed = "contract_not_signed"
    payment_not_completed = "payment_not_completed"
    payment_failed = "payment_failed"
    refund_requested = "refund_requested"
    internal_team_delay = "internal_team_delay"
    system_or_link_issue = "system_or_link_issue"
    language_barrier = "language_barrier"
    timezone_issue = "timezone_issue"
    issue_already_solved = "issue_already_solved"
    other = "other"
    unknown = "unknown"


class BuyingIntentLevel(str, Enum):
    very_high = "very_high"
    high = "high"
    medium = "medium"
    low = "low"
    very_low = "very_low"
    unknown = "unknown"


class LeadQualityLevel(str, Enum):
    high_quality = "high_quality"
    medium_quality = "medium_quality"
    low_quality = "low_quality"
    unqualified = "unqualified"
    unknown = "unknown"


class ProfessionCategory(str, Enum):
    student = "student"
    employee = "employee"
    self_employed = "self_employed"
    business_owner = "business_owner"
    entrepreneur = "entrepreneur"
    freelancer = "freelancer"
    trader_or_investor = "trader_or_investor"
    finance_or_accounting = "finance_or_accounting"
    sales_or_marketing = "sales_or_marketing"
    healthcare = "healthcare"
    education = "education"
    technology = "technology"
    engineering = "engineering"
    construction_or_trades = "construction_or_trades"
    hospitality = "hospitality"
    retail = "retail"
    real_estate = "real_estate"
    transport_or_logistics = "transport_or_logistics"
    creative_or_media = "creative_or_media"
    government_or_public_sector = "government_or_public_sector"
    unemployed = "unemployed"
    retired = "retired"
    other = "other"
    unknown = "unknown"


class EmploymentStatus(str, Enum):
    full_time = "full_time"
    part_time = "part_time"
    self_employed = "self_employed"
    student = "student"
    business_owner = "business_owner"
    unemployed = "unemployed"
    retired = "retired"
    unknown = "unknown"


class DiagnosticTextInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason_category: ReasonCategory = ReasonCategory.unknown
    reason_subcategory: ReasonSubcategory = ReasonSubcategory.unknown
    is_conversion_blocker: bool = False
    is_human_reason_supported: bool = False
    buying_intent_level: BuyingIntentLevel = BuyingIntentLevel.unknown
    lead_quality_level: LeadQualityLevel = LeadQualityLevel.unknown
    profession_category: ProfessionCategory = ProfessionCategory.unknown
    employment_status: EmploymentStatus = EmploymentStatus.unknown


class DiagnosticTextInsightResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    insights: list[DiagnosticTextInsight]