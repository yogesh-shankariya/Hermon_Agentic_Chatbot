from __future__ import annotations

import importlib
import importlib.util
import sys
import types
import unittest
from enum import Enum
from pathlib import Path
from types import SimpleNamespace

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"


def _install_fake_pydantic_if_needed() -> None:
    try:
        import pydantic  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    def field(default=..., **kwargs):
        return default

    class BaseModel:
        model_config = {}

        def __init__(self, **kwargs):
            annotations = getattr(self.__class__, "__annotations__", {})
            for name, annotation in annotations.items():
                if name not in kwargs:
                    raise ValueError(f"Missing required field: {name}")
                value = kwargs[name]
                if isinstance(annotation, type) and issubclass(annotation, Enum):
                    value = annotation(value)
                setattr(self, name, value)

        @classmethod
        def model_validate(cls, value):
            if isinstance(value, cls):
                return value
            return cls(**value)

        @classmethod
        def parse_obj(cls, value):
            return cls(**value)

        def model_dump(self):
            return dict(self.__dict__)

        def dict(self):
            return self.model_dump()

    pydantic_module = types.ModuleType("pydantic")
    pydantic_module.BaseModel = BaseModel
    pydantic_module.Field = field
    sys.modules.setdefault("pydantic", pydantic_module)


def _install_fake_langchain_if_needed() -> None:
    class FakeTool:
        def __init__(self, func=None, name: str | None = None):
            self.func = func
            self.name = name or getattr(func, "__name__", "fake_tool")

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

    def fake_create_agent(model, tools=None, system_prompt=None, middleware=None):
        return SimpleNamespace(
            model=model,
            tools=list(tools or []),
            system_prompt=system_prompt,
            middleware=list(middleware or []),
        )

    def fake_init_chat_model(model_name, **kwargs):
        return SimpleNamespace(model_name=model_name, kwargs=kwargs)

    try:
        import langchain  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["langchain"] = types.ModuleType("langchain")

    langchain_module = sys.modules["langchain"]
    if not hasattr(langchain_module, "__path__"):
        langchain_module.__path__ = []

    tools_module = sys.modules.get("langchain.tools") or types.ModuleType("langchain.tools")
    tools_module.tool = fake_tool
    agents_module = sys.modules.get("langchain.agents") or types.ModuleType("langchain.agents")
    agents_module.create_agent = fake_create_agent
    chat_models_module = sys.modules.get("langchain.chat_models") or types.ModuleType(
        "langchain.chat_models"
    )
    chat_models_module.init_chat_model = fake_init_chat_model

    sys.modules["langchain.tools"] = tools_module
    sys.modules["langchain.agents"] = agents_module
    sys.modules["langchain.chat_models"] = chat_models_module


class FakeRouter:
    def __init__(self, response):
        self.response = response
        self.payloads = []

    def invoke(self, payload, config=None):
        self.payloads.append(payload)
        return self.response


class FakeAgent:
    def __init__(self, answer: str):
        self.answer = answer
        self.payloads = []

    def invoke(self, payload, config=None):
        self.payloads.append(payload)
        return {
            "messages": [
                *payload["messages"],
                {"role": "assistant", "content": self.answer},
            ]
        }


class FailingAgent:
    def invoke(self, payload, config=None):
        raise AssertionError("This flow should not have been called")


def _message_content(message) -> str:
    if isinstance(message, dict):
        return str(message.get("content", ""))
    return str(getattr(message, "content", ""))


class RoutingAndToolSeparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _install_fake_pydantic_if_needed()
        _install_fake_langchain_if_needed()

    def test_sql_skill_registry_contains_only_analytics_skills(self):
        registry_text = (APP_DIR / "skills" / "registry.yaml").read_text(encoding="utf-8")
        config_text = (APP_DIR / "config" / "config.yaml").read_text(encoding="utf-8")
        registry = yaml.safe_load(registry_text)
        config = yaml.safe_load(config_text)
        skills = registry["skills"]
        names = [skill["name"] for skill in skills]
        self.assertEqual(
            names,
            [
                "lead_analytics",
                "appointment_analytics",
                "acquisition_analytics",
                "lead_profile_analytics",
                "revenue_analytics",
            ],
        )
        self.assertNotIn("lead_360", names)
        for skill in skills:
            self.assertNotIn("path", skill)
            self.assertNotIn("version", skill)
            self.assertEqual(config["skills"][skill["name"]]["path"], skill["name"])
            self.assertEqual(config["skills"][skill["name"]]["version"], "1_0_0")

        self.assertEqual(config["skills"]["lead_360"]["path"], "lead_360")
        self.assertEqual(config["skills"]["lead_360"]["version"], "1_0_0")
        self.assertEqual(
            config["skills"]["diagnostic_analytics"]["path"],
            "diagnostic_analytics",
        )
        self.assertEqual(config["skills"]["diagnostic_analytics"]["version"], "1_0_0")

    def test_lead_profile_sql_skill_contains_profile_question_rules(self):
        registry_text = (APP_DIR / "skills" / "registry.yaml").read_text(encoding="utf-8")
        skill_text = (
            APP_DIR / "skills" / "modules" / "lead_profile_analytics" / "1_0_0.md"
        ).read_text(encoding="utf-8")
        sql_prompt = (
            APP_DIR / "prompts" / "sql_agent" / "1_0_0.md"
        ).read_text(encoding="utf-8")

        self.assertIn("lead_profile_analytics", registry_text)
        self.assertIn("Which profession generated the most leads?", skill_text)
        self.assertIn("Which profession submitted the most opt-ins?", skill_text)
        self.assertIn("What do you do for work?", skill_text)
        self.assertIn("What is your employment status?", skill_text)
        self.assertIn("COUNT(DISTINCT l.id)::int AS lead_count", skill_text)
        self.assertIn("COUNT(*)::int AS opt_in_count", skill_text)
        self.assertIn("DATE_TRUNC('month', l.created_at)", skill_text)
        self.assertIn("l.clerk_org_id = :org_id", skill_text)
        self.assertIn("l.is_deleted = false", skill_text)
        self.assertIn("q.question", skill_text)
        self.assertIn("q.answer", skill_text)
        self.assertIn("load `lead_profile_analytics`", sql_prompt)

    def test_sql_agent_tools_include_only_sql_analytics_tools(self):
        module = self._load_sql_tools_with_fakes()
        tool_names = [tool.name for tool in module.SQL_AGENT_TOOLS]
        self.assertEqual(tool_names, ["load_skill", "run_readonly_sql"])
        self.assertNotIn("get_lead_360", tool_names)
        self.assertNotIn("get_diagnostic_funnel_snapshot", tool_names)
        self.assertNotIn("get_diagnostic_source_snapshot", tool_names)
        self.assertNotIn("get_diagnostic_profile_snapshot", tool_names)
        self.assertNotIn("get_diagnostic_source_quality_snapshot", tool_names)
        self.assertNotIn("get_diagnostic_business_change_snapshot", tool_names)
        self.assertNotIn("get_diagnostic_text_reason_snapshot", tool_names)
        self.assertNotIn("get_diagnostic_monthly_trend_overview_snapshot", tool_names)

    def test_lead_360_agent_has_only_lead_360_tool_and_safe_prompt_rules(self):
        module = self._load_lead_360_builder_with_fakes()
        agent = module.create_lead_360_agent()

        self.assertEqual([tool.name for tool in module.LEAD_360_TOOLS], ["get_lead_360"])
        self.assertEqual([tool.name for tool in agent.tools], ["get_lead_360"])

        prompt = module.load_lead_360_prompt()
        self.assertIn("Do not generate SQL.", prompt)
        self.assertIn("Do not call `run_readonly_sql`.", prompt)
        self.assertIn("If status is `multiple_matches`", prompt)
        self.assertIn("If status is `not_found`", prompt)
        self.assertIn("If status is `error`", prompt)
        self.assertIn("If status is `success`", prompt)

    def test_diagnostic_agent_has_only_diagnostic_tools_and_safe_prompt_rules(self):
        module = self._load_diagnostic_builder_with_fakes()
        agent = module.create_diagnostic_agent()

        expected_tool_names = [
            "get_diagnostic_monthly_trend_overview_snapshot",
            "get_diagnostic_funnel_snapshot",
            "get_diagnostic_source_snapshot",
            "get_diagnostic_profile_snapshot",
            "get_diagnostic_source_quality_snapshot",
            "get_diagnostic_business_change_snapshot",
            "get_diagnostic_text_reason_snapshot",
        ]
        self.assertEqual([tool.name for tool in module.DIAGNOSTIC_TOOLS], expected_tool_names)
        self.assertEqual([tool.name for tool in agent.tools], expected_tool_names)
        self.assertNotIn("load_skill", expected_tool_names)
        self.assertNotIn("run_readonly_sql", expected_tool_names)
        self.assertNotIn("get_lead_360", expected_tool_names)

        prompt = module.load_diagnostic_prompt()
        self.assertIn("Do not generate SQL.", prompt)
        self.assertIn("Do not call `run_readonly_sql`.", prompt)
        self.assertIn("Do not call `load_skill`.", prompt)
        self.assertIn("Use only the evidence returned by the diagnostic tools.", prompt)

    def test_orchestrator_routes_sql_examples_to_sql_flow(self):
        orchestrator = self._import_orchestrator()
        sql_agent = FakeAgent("sql answer")
        lead_agent = FailingAgent()
        diagnostic_agent = FailingAgent()

        questions = [
            "How many leads came last month?",
            "Show revenue by program.",
            "Which source generated the most revenue?",
            "Show revenue by source.",
            "Show appointment count by source.",
            "Show no-show rate by source.",
            "Show funnel by source.",
            "Lead trend by source.",
        ]

        for question in questions:
            with self.subTest(question=question):
                sql_agent.payloads.clear()
                router = FakeRouter(
                    {
                        "route": "sql_analytics",
                        "history_count": 0,
                        "standalone_question": question,
                    }
                )
                turn = orchestrator.answer_user_question(
                    question,
                    [],
                    router=router,
                    sql_agent=sql_agent,
                    lead_360_agent=lead_agent,
                    diagnostic_agent=diagnostic_agent,
                )
                self.assertEqual(turn["route"], "sql_analytics")
                self.assertEqual(turn["answer"], "sql answer")
                self.assertEqual(len(sql_agent.payloads), 1)

    def test_router_prompt_contains_required_route_examples(self):
        prompt = (APP_DIR / "prompts" / "router" / "1_0_0.md").read_text(
            encoding="utf-8"
        )
        expected_examples = [
            ("How many leads came last month?", "sql_analytics"),
            ("Show revenue by program.", "sql_analytics"),
            ("What happened with Vedran?", "lead_360"),
            ("Give me the 360 view of John Smith.", "lead_360"),
            ("Which source should we scale?", "diagnostic_analytics"),
            ("How are we doing in April compared to March?", "diagnostic_analytics"),
            ("How are we doing in April compared the March?", "diagnostic_analytics"),
            ("Compare lead count in April vs March.", "sql_analytics"),
            ("What is the lead trend?", "sql_analytics"),
            ("What should I pay attention to for my business?", "diagnostic_analytics"),
            ("What trends are you noticing?", "diagnostic_analytics"),
            ("What are the current trends?", "diagnostic_analytics"),
            ("What business trends do you see?", "diagnostic_analytics"),
            ("What is changing in the business?", "diagnostic_analytics"),
            ("What looks different recently?", "diagnostic_analytics"),
            ("What should I pay attention to from recent trends?", "diagnostic_analytics"),
            ("Show lead trend.", "sql_analytics"),
            ("Show revenue trend by month.", "sql_analytics"),
            ("Show appointment trend.", "sql_analytics"),
            ("Lead trend by source.", "sql_analytics"),
            ("Which source generated the most revenue?", "sql_analytics"),
            ("Show revenue by source.", "sql_analytics"),
            ("Show appointment count by source.", "sql_analytics"),
            ("Show no-show rate by source.", "sql_analytics"),
            ("Show funnel by source.", "sql_analytics"),
            ("Show won leads by UTM campaign.", "sql_analytics"),
            ("Which UTM campaign produced the most won leads?", "sql_analytics"),
            ("What is the won lead rate by UTM campaign?", "sql_analytics"),
            ("Which source has the weakest funnel performance?", "diagnostic_analytics"),
            ("Which source has the worst funnel performance?", "diagnostic_analytics"),
            ("Which source is weakest across the funnel?", "diagnostic_analytics"),
            ("Which source has weak conversion through the funnel?", "diagnostic_analytics"),
            ("Which source is leaking the most in the funnel?", "diagnostic_analytics"),
            ("Which source has high leads but weak conversion?", "diagnostic_analytics"),
            ("Which source books calls but does not convert?", "diagnostic_analytics"),
            ("Which source completes calls but does not sign?", "diagnostic_analytics"),
            ("Which source signs but does not pay?", "diagnostic_analytics"),
            ("what caused revenue drop?", "sql_analytics"),
            (
                "Explain why gross paid revenue by payment date dropped from €72,500 in Mar 2026 to €63,000 in Apr 2026",
                "sql_analytics",
            ),
            ("Why are completed calls not converting to signed leads?", "diagnostic_analytics"),
            ("After calls, why are people not paying?", "diagnostic_analytics"),
            ("Where are we losing people in the funnel and why?", "diagnostic_analytics"),
            ("Where are we losing people on funnel?", "diagnostic_analytics"),
            ("Which profession generated the most leads?", "sql_analytics"),
            ("Which profession converts best?", "diagnostic_analytics"),
            ("Which employment status is most common?", "sql_analytics"),
            ("Which profession submitted the most opt-ins?", "sql_analytics"),
            ("Monthly leads trend by profession.", "sql_analytics"),
            ("Which professions joined mostly recently?", "sql_analytics"),
            ("Which professions are increasing recently?", "sql_analytics"),
            ("Monthly leads trend by employment status.", "sql_analytics"),
            ("Which employment status has the highest paid conversion?", "diagnostic_analytics"),
            ("Which profession should we focus on?", "diagnostic_analytics"),
            ("Why are Business Owner leads not converting?", "diagnostic_analytics"),
            ("Why did Vedran not pay?", "lead_360"),
            ("Delete these leads.", "unsupported"),
        ]

        for question, route in expected_examples:
            with self.subTest(question=question):
                self.assertIn(question, prompt)
                self.assertIn(route, prompt)

    def test_orchestrator_routes_lead_360_examples_to_lead_flow(self):
        orchestrator = self._import_orchestrator()
        sql_agent = FailingAgent()
        lead_agent = FakeAgent("lead answer")
        diagnostic_agent = FailingAgent()

        for question in ["What happened with Vedran?", "Give me the 360 view of john@example.com."]:
            with self.subTest(question=question):
                lead_agent.payloads.clear()
                router = FakeRouter(
                    {
                        "route": "lead_360",
                        "history_count": 0,
                        "standalone_question": question,
                    }
                )
                turn = orchestrator.answer_user_question(
                    question,
                    [],
                    router=router,
                    sql_agent=sql_agent,
                    lead_360_agent=lead_agent,
                    diagnostic_agent=diagnostic_agent,
                )
                self.assertEqual(turn["route"], "lead_360")
                self.assertEqual(turn["answer"], "lead answer")
                self.assertEqual(len(lead_agent.payloads), 1)

    def test_orchestrator_routes_diagnostic_examples_to_diagnostic_flow(self):
        orchestrator = self._import_orchestrator()
        diagnostic_agent = FakeAgent("diagnostic answer")

        questions = [
            "Why are leads increasing but revenue is not?",
            "Where are we losing people in the funnel?",
            "Which source looks good but may be misleading?",
            "Can we trust source performance?",
            "What changed this month?",
            "How are we doing in April compared the March?",
            "Are we doing better or worse in April than March?",
            "What should I pay attention to for my business?",
            "What should sales focus on this week?",
            "What should marketing investigate this week?",
            "Which source has signed contracts but low collected cash?",
            "Why are completed calls not converting to signed leads?",
            "After calls, why are people not paying?",
            "Where are we losing people in the funnel and why?",
            "What trends are you noticing?",
            "What are the current trends?",
            "What business trends do you see?",
            "What is changing in the business?",
            "What looks different recently?",
            "What should I pay attention to from recent trends?",
            "Which source has the weakest funnel performance?",
            "Which source has the worst funnel performance?",
            "Which source is leaking the most in the funnel?",
            "Which source has high leads but weak conversion?",
            "Which source books calls but does not convert?",
            "Which source completes calls but does not sign?",
            "Which source signs but does not pay?",
        ]

        for question in questions:
            with self.subTest(question=question):
                diagnostic_agent.payloads.clear()
                router = FakeRouter(
                    {
                        "route": "diagnostic_analytics",
                        "history_count": 0,
                        "standalone_question": question,
                    }
                )
                turn = orchestrator.answer_user_question(
                    question,
                    [],
                    router=router,
                    sql_agent=FailingAgent(),
                    lead_360_agent=FailingAgent(),
                    diagnostic_agent=diagnostic_agent,
                )
                self.assertEqual(turn["route"], "diagnostic_analytics")
                self.assertEqual(turn["answer"], "diagnostic answer")
                self.assertEqual(len(diagnostic_agent.payloads), 1)

    def test_orchestrator_forces_generic_trend_discovery_to_diagnostic_when_router_says_sql(self):
        orchestrator = self._import_orchestrator()
        diagnostic_agent = FakeAgent("monthly trend diagnostic answer")

        questions = [
            "What trends are you noticing?",
            "What are the current trends?",
            "What business trends do you see?",
            "What is changing in the business?",
            "What looks different recently?",
            "What should I pay attention to from recent trends?",
        ]

        for question in questions:
            with self.subTest(question=question):
                diagnostic_agent.payloads.clear()
                turn = orchestrator.answer_user_question(
                    question,
                    [],
                    router=FakeRouter(
                        {
                            "route": "sql_analytics",
                            "history_count": 0,
                            "standalone_question": question,
                        }
                    ),
                    sql_agent=FailingAgent(),
                    lead_360_agent=FailingAgent(),
                    diagnostic_agent=diagnostic_agent,
                )

                self.assertEqual(turn["route"], "diagnostic_analytics")
                self.assertEqual(turn["answer"], "monthly trend diagnostic answer")
                self.assertEqual(turn["standalone_question"], question)
                self.assertEqual(len(diagnostic_agent.payloads), 1)

    def test_orchestrator_keeps_direct_metric_trends_in_sql(self):
        orchestrator = self._import_orchestrator()
        sql_agent = FakeAgent("direct trend sql answer")

        questions = [
            "Show lead trend.",
            "Show revenue trend by month.",
            "Show appointment trend.",
            "Lead trend by source.",
            "Monthly leads trend by profession.",
        ]

        for question in questions:
            with self.subTest(question=question):
                sql_agent.payloads.clear()
                turn = orchestrator.answer_user_question(
                    question,
                    [],
                    router=FakeRouter(
                        {
                            "route": "sql_analytics",
                            "history_count": 0,
                            "standalone_question": question,
                        }
                    ),
                    sql_agent=sql_agent,
                    lead_360_agent=FailingAgent(),
                    diagnostic_agent=FailingAgent(),
                )

                self.assertEqual(turn["route"], "sql_analytics")
                self.assertEqual(turn["answer"], "direct trend sql answer")
                self.assertEqual(len(sql_agent.payloads), 1)

    def test_orchestrator_preserves_sql_revenue_metric_for_causal_follow_up(self):
        orchestrator = self._import_orchestrator()
        sql_agent = FakeAgent("payment-period revenue explanation")
        history = [
            {
                "route": "sql_analytics",
                "selected_skill": "revenue_analytics",
                "question": "show me revenue trend",
                "answer": (
                    "Trend period: Feb 2026 through Apr 2026. Gross paid revenue "
                    "fell from €72,500 in Mar 2026 to €63,000 in Apr 2026."
                ),
            }
        ]

        turn = orchestrator.answer_user_question(
            "what caused revenue drop?",
            history,
            router=FakeRouter(
                {
                    "route": "diagnostic_analytics",
                    "history_count": 0,
                    "standalone_question": "What caused revenue to drop?",
                }
            ),
            sql_agent=sql_agent,
            lead_360_agent=FailingAgent(),
            diagnostic_agent=FailingAgent(),
        )

        self.assertEqual(turn["route"], "sql_analytics")
        self.assertEqual(turn["context_turn_count"], 1)
        self.assertEqual(turn["answer"], "payment-period revenue explanation")
        self.assertIn("gross paid revenue by payment date", turn["standalone_question"])
        self.assertIn("€72,500 in Mar 2026", turn["standalone_question"])
        self.assertIn("€63,000 in Apr 2026", turn["standalone_question"])
        self.assertIn("same revenue basis", turn["standalone_question"])
        self.assertEqual(len(sql_agent.payloads), 1)

    def test_orchestrator_preserves_sql_lead_metric_for_causal_follow_up(self):
        orchestrator = self._import_orchestrator()
        sql_agent = FakeAgent("lead trend explanation")
        history = [
            {
                "route": "sql_analytics",
                "selected_skill": "lead_analytics",
                "question": "show me lead trend",
                "answer": "Leads increased from 90 in Mar 2026 to 108 in Apr 2026.",
            }
        ]

        turn = orchestrator.answer_user_question(
            "why did it increase?",
            history,
            router=FakeRouter(
                {
                    "route": "diagnostic_analytics",
                    "history_count": 0,
                    "standalone_question": "Why did it increase?",
                }
            ),
            sql_agent=sql_agent,
            lead_360_agent=FailingAgent(),
            diagnostic_agent=FailingAgent(),
        )

        self.assertEqual(turn["route"], "sql_analytics")
        self.assertIn(
            "lead count increased from 90 in Mar 2026 to 108 in Apr 2026",
            turn["standalone_question"],
        )
        self.assertIn("same lead-created date basis", turn["standalone_question"])
        self.assertEqual(len(sql_agent.payloads), 1)

    def test_orchestrator_allows_explicit_lead_cohort_switch_after_sql_revenue_trend(self):
        orchestrator = self._import_orchestrator()
        diagnostic_agent = FakeAgent("lead cohort diagnostic answer")
        history = [
            {
                "route": "sql_analytics",
                "selected_skill": "revenue_analytics",
                "question": "show me revenue trend",
                "answer": "Gross paid revenue by payment date dropped in April.",
            }
        ]

        turn = orchestrator.answer_user_question(
            "what about lead cohort performance, why did April leads monetize weaker?",
            history,
            router=FakeRouter(
                {
                    "route": "diagnostic_analytics",
                    "history_count": 1,
                    "standalone_question": (
                        "Explain lead-created cohort performance for April leads compared "
                        "with the previous period, focusing on why April leads monetized weaker."
                    ),
                }
            ),
            sql_agent=FailingAgent(),
            lead_360_agent=FailingAgent(),
            diagnostic_agent=diagnostic_agent,
        )

        self.assertEqual(turn["route"], "diagnostic_analytics")
        self.assertEqual(turn["answer"], "lead cohort diagnostic answer")
        self.assertEqual(len(diagnostic_agent.payloads), 1)

    def test_orchestrator_forces_generic_profile_questions_to_sql_when_router_says_diagnostic(self):
        orchestrator = self._import_orchestrator()
        sql_agent = FakeAgent("profile sql answer")
        questions = [
            "Which profession submitted the most opt-ins?",
            "which profession generated the most leads",
            "Which employment status is most common?",
            "Monthly leads trend by profession.",
            "Which professions joined mostly recently?",
            "Which professions are increasing recently?",
            "Monthly leads trend by employment status.",
        ]

        for question in questions:
            with self.subTest(question=question):
                sql_agent.payloads.clear()
                turn = orchestrator.answer_user_question(
                    question,
                    [],
                    router=FakeRouter(
                        {
                            "route": "diagnostic_analytics",
                            "history_count": 0,
                            "standalone_question": question,
                        }
                    ),
                    sql_agent=sql_agent,
                    lead_360_agent=FailingAgent(),
                    diagnostic_agent=FailingAgent(),
                )

                self.assertEqual(turn["route"], "sql_analytics")
                self.assertEqual(turn["answer"], "profile sql answer")
                self.assertEqual(turn["standalone_question"], question)
                self.assertEqual(len(sql_agent.payloads), 1)

    def test_orchestrator_forces_profile_conversion_questions_to_diagnostic_when_router_says_sql(self):
        orchestrator = self._import_orchestrator()
        diagnostic_agent = FakeAgent("profile diagnostic answer")
        questions = [
            "Which profession converts best?",
            "Which employment status has the highest paid conversion?",
            "Which profession should we focus on?",
            "Why are Business Owner leads not converting?",
        ]

        for question in questions:
            with self.subTest(question=question):
                diagnostic_agent.payloads.clear()
                turn = orchestrator.answer_user_question(
                    question,
                    [],
                    router=FakeRouter(
                        {
                            "route": "sql_analytics",
                            "history_count": 0,
                            "standalone_question": question,
                        }
                    ),
                    sql_agent=FailingAgent(),
                    lead_360_agent=FailingAgent(),
                    diagnostic_agent=diagnostic_agent,
                )

                self.assertEqual(turn["route"], "diagnostic_analytics")
                self.assertEqual(turn["answer"], "profile diagnostic answer")
                self.assertEqual(turn["standalone_question"], question)
                self.assertEqual(len(diagnostic_agent.payloads), 1)

    def test_orchestrator_forces_acquisition_status_conversion_to_sql_when_router_says_unsupported(self):
        orchestrator = self._import_orchestrator()
        sql_agent = FakeAgent("acquisition sql answer")
        question = "Show won leads by UTM campaign."

        turn = orchestrator.answer_user_question(
            question,
            [],
            router=FakeRouter(
                {
                    "route": "unsupported",
                    "history_count": 0,
                    "standalone_question": question,
                }
            ),
            sql_agent=sql_agent,
            lead_360_agent=FailingAgent(),
            diagnostic_agent=FailingAgent(),
        )

        self.assertEqual(turn["route"], "sql_analytics")
        self.assertEqual(turn["answer"], "acquisition sql answer")
        self.assertEqual(turn["standalone_question"], question)
        self.assertEqual(len(sql_agent.payloads), 1)

    def test_orchestrator_forces_acquisition_status_conversion_to_sql_when_router_says_diagnostic(self):
        orchestrator = self._import_orchestrator()
        sql_agent = FakeAgent("acquisition sql answer")
        question = "What is the won lead rate by UTM campaign?"

        turn = orchestrator.answer_user_question(
            question,
            [],
            router=FakeRouter(
                {
                    "route": "diagnostic_analytics",
                    "history_count": 0,
                    "standalone_question": question,
                }
            ),
            sql_agent=sql_agent,
            lead_360_agent=FailingAgent(),
            diagnostic_agent=FailingAgent(),
        )

        self.assertEqual(turn["route"], "sql_analytics")
        self.assertEqual(turn["answer"], "acquisition sql answer")
        self.assertEqual(turn["standalone_question"], question)
        self.assertEqual(len(sql_agent.payloads), 1)

    def test_orchestrator_keeps_revenue_by_utm_campaign_unsupported(self):
        orchestrator = self._import_orchestrator()
        question = "Show revenue by UTM campaign."

        turn = orchestrator.answer_user_question(
            question,
            [],
            router=FakeRouter(
                {
                    "route": "unsupported",
                    "history_count": 0,
                    "standalone_question": question,
                }
            ),
            sql_agent=FailingAgent(),
            lead_360_agent=FailingAgent(),
            diagnostic_agent=FailingAgent(),
        )

        self.assertEqual(turn["route"], "unsupported")
        self.assertEqual(turn["trace_messages"], [])

    def test_orchestrator_uses_router_history_count_for_single_lead_follow_up(self):
        orchestrator = self._import_orchestrator()
        lead_agent = FakeAgent("lead follow-up answer")
        history = [
            {"question": "Show me Vedran's 360 view.", "answer": "Vedran is in follow-up."}
        ]
        router = FakeRouter(
            {
                "route": "lead_360",
                "history_count": 1,
                "standalone_question": "Why did Vedran not pay?",
            }
        )

        turn = orchestrator.answer_user_question(
            "Why did this lead not pay?",
            history,
            router=router,
            sql_agent=FailingAgent(),
            lead_360_agent=lead_agent,
            diagnostic_agent=FailingAgent(),
        )

        messages = lead_agent.payloads[0]["messages"]
        self.assertEqual(turn["route"], "lead_360")
        self.assertEqual(turn["context_turn_count"], 1)
        self.assertEqual(messages[-1]["content"], "Why did Vedran not pay?")
        self.assertEqual(messages[:-1], [
            {"role": "user", "content": "Show me Vedran's 360 view."},
            {"role": "assistant", "content": "Vedran is in follow-up."},
        ])

    def test_orchestrator_uses_router_history_count_for_diagnostic_follow_up(self):
        orchestrator = self._import_orchestrator()
        diagnostic_agent = FakeAgent("diagnostic follow-up answer")
        history = [
            {
                "question": "Why are leads increasing but revenue is not?",
                "answer": "Revenue per lead dropped.",
            }
        ]
        router = FakeRouter(
            {
                "route": "diagnostic_analytics",
                "history_count": 1,
                "standalone_question": "Which funnel stage changed most?",
            }
        )

        turn = orchestrator.answer_user_question(
            "Which stage changed most?",
            history,
            router=router,
            sql_agent=FailingAgent(),
            lead_360_agent=FailingAgent(),
            diagnostic_agent=diagnostic_agent,
        )

        messages = diagnostic_agent.payloads[0]["messages"]
        self.assertEqual(turn["route"], "diagnostic_analytics")
        self.assertEqual(turn["context_turn_count"], 1)
        self.assertEqual(messages[-1]["content"], "Which funnel stage changed most?")
        self.assertEqual(messages[:-1], [
            {"role": "user", "content": "Why are leads increasing but revenue is not?"},
            {"role": "assistant", "content": "Revenue per lead dropped."},
        ])

    def test_orchestrator_does_not_call_downstream_for_unsupported(self):
        orchestrator = self._import_orchestrator()

        turn = orchestrator.answer_user_question(
            "Delete these leads.",
            [],
            router=FakeRouter(
                {
                    "route": "unsupported",
                    "history_count": 0,
                    "standalone_question": "Delete these leads.",
                }
            ),
            sql_agent=FailingAgent(),
            lead_360_agent=FailingAgent(),
            diagnostic_agent=FailingAgent(),
        )
        self.assertEqual(turn["route"], "unsupported")
        self.assertEqual(turn["trace_messages"], [])

    def test_router_receives_only_latest_five_history_turns(self):
        orchestrator = self._import_orchestrator()
        history = [
            {"question": f"q{index}", "answer": f"a{index}"}
            for index in range(7)
        ]
        router = FakeRouter(
            {
                "route": "sql_analytics",
                "history_count": 0,
                "standalone_question": "How many leads?",
            }
        )

        orchestrator.answer_user_question(
            "How many leads?",
            history,
            router=router,
            sql_agent=FakeAgent("sql answer"),
            lead_360_agent=FailingAgent(),
            diagnostic_agent=FailingAgent(),
        )

        router_user_content = _message_content(router.payloads[0][-1])
        self.assertNotIn("q0", router_user_content)
        self.assertNotIn("q1", router_user_content)
        for index in range(2, 7):
            self.assertIn(f"q{index}", router_user_content)
            self.assertIn(f"a{index}", router_user_content)

    def _import_orchestrator(self):
        _install_fake_pydantic_if_needed()
        return importlib.import_module("app.orchestrator")

    def _load_sql_tools_with_fakes(self):
        _install_fake_langchain_if_needed()
        module_name = "sql_tools_under_test"
        module_path = APP_DIR / "tools" / "sql_tools.py"

        fake_config = types.ModuleType("app.config")
        fake_config.get_sql_agent_settings = lambda: SimpleNamespace(
            default_org_id="org_1",
            enabled_skills=("lead_analytics",),
            max_tool_rows=20,
        )
        fake_config.get_org_timezone = lambda org_id: "UTC"
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

    def _load_lead_360_builder_with_fakes(self):
        _install_fake_langchain_if_needed()
        module_name = "lead_360_builder_under_test"
        module_path = APP_DIR / "agents" / "lead_360" / "builder.py"

        fake_tool = SimpleNamespace(name="get_lead_360")
        fake_tools = types.ModuleType("app.tools")
        fake_tools.get_lead_360_tool = fake_tool
        fake_config = types.ModuleType("app.config")
        fake_config.ensure_openai_key = lambda: None
        fake_config.get_sql_agent_settings = lambda: SimpleNamespace(
            model="test-model",
            reasoning=None,
            service_tier=None,
        )
        fake_settings = types.ModuleType("app.config.settings")
        fake_settings.APP_DIR = APP_DIR
        fake_settings.load_app_config = lambda: {
            "skills": {
                "base_path": str(APP_DIR / "skills" / "modules"),
                "lead_360": {"path": "lead_360", "version": "1_0_0"},
            }
        }

        originals = {
            name: sys.modules.get(name)
            for name in (
                "app.tools",
                "app.config",
                "app.config.settings",
                "app.utils.skill_loader",
            )
        }
        sys.modules.pop("app.utils.skill_loader", None)
        sys.modules["app.tools"] = fake_tools
        sys.modules["app.config"] = fake_config
        sys.modules["app.config.settings"] = fake_settings

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

    def _load_diagnostic_builder_with_fakes(self):
        _install_fake_langchain_if_needed()
        module_name = "diagnostic_builder_under_test"
        module_path = APP_DIR / "agents" / "diagnostic_agent" / "builder.py"

        fake_diagnostic_tools = types.ModuleType("app.tools.diagnostic_tools")
        fake_diagnostic_tools.DIAGNOSTIC_TOOLS = [
            SimpleNamespace(name="get_diagnostic_monthly_trend_overview_snapshot"),
            SimpleNamespace(name="get_diagnostic_funnel_snapshot"),
            SimpleNamespace(name="get_diagnostic_source_snapshot"),
            SimpleNamespace(name="get_diagnostic_profile_snapshot"),
            SimpleNamespace(name="get_diagnostic_source_quality_snapshot"),
            SimpleNamespace(name="get_diagnostic_business_change_snapshot"),
            SimpleNamespace(name="get_diagnostic_text_reason_snapshot"),
        ]
        fake_tools = types.ModuleType("app.tools")
        fake_tools.__path__ = []
        fake_config = types.ModuleType("app.config")
        fake_config.ensure_openai_key = lambda: None
        fake_config.get_sql_agent_settings = lambda: SimpleNamespace(
            model="test-model",
            reasoning=None,
            service_tier=None,
        )
        fake_settings = types.ModuleType("app.config.settings")
        fake_settings.APP_DIR = APP_DIR
        fake_settings.load_app_config = lambda: {
            "skills": {
                "base_path": str(APP_DIR / "skills" / "modules"),
                "diagnostic_analytics": {
                    "path": "diagnostic_analytics",
                    "version": "1_0_0",
                },
            }
        }

        originals = {
            name: sys.modules.get(name)
            for name in (
                "app.tools",
                "app.tools.diagnostic_tools",
                "app.config",
                "app.config.settings",
                "app.utils.skill_loader",
            )
        }
        sys.modules.pop("app.utils.skill_loader", None)
        sys.modules["app.tools"] = fake_tools
        sys.modules["app.tools.diagnostic_tools"] = fake_diagnostic_tools
        sys.modules["app.config"] = fake_config
        sys.modules["app.config.settings"] = fake_settings

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


if __name__ == "__main__":
    unittest.main()
