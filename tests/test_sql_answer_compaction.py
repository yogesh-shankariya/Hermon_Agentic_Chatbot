from __future__ import annotations

import json
import unittest
from types import SimpleNamespace

from app.agents.sql_agent.builder import (
    CompactSqlAnswerAgent,
    build_sql_answer_messages,
    build_sql_answer_payload,
)


FULL_SKILL_MARKDOWN = "FULL SQL AGENT SKILL MARKDOWN THAT MUST NOT LEAK"
FULL_SQL_TEXT = "SELECT full_sql_prompt_leak FROM private_context"


class _FakeExecutionAgent:
    def __init__(self, first_messages, second_messages):
        self._results = [
            {"messages": first_messages},
            {"messages": second_messages},
        ]
        self.payloads = []

    def invoke(self, payload, config=None):
        self.payloads.append(payload)
        index = min(len(self.payloads) - 1, len(self._results) - 1)
        return self._results[index]


class _FakeAnswerModel:
    def __init__(self):
        self.payloads = []

    def invoke(self, payload, config=None):
        self.payloads.append(payload)
        return SimpleNamespace(content="There are 11 leads created today.")


class SqlAnswerCompactionTests(unittest.TestCase):
    def _messages(self):
        initial_messages = [
            {"role": "user", "content": "Previous question that must not leak"},
            {"role": "assistant", "content": "Previous answer that must not leak"},
            {"role": "system", "content": "Runtime context for relative dates"},
            {"role": "user", "content": "Give number of leads created today"},
        ]
        loaded_skill_messages = [
            *initial_messages,
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "name": "load_skill",
                        "args": {"skill_name": "lead_analytics"},
                        "id": "call_1",
                    }
                ],
            },
            {
                "role": "tool",
                "name": "load_skill",
                "content": f"Loaded skill: lead_analytics\n\n{FULL_SKILL_MARKDOWN}",
            },
        ]
        sql_result_messages = [
            *loaded_skill_messages,
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "name": "run_readonly_sql",
                        "args": {
                            "query": FULL_SQL_TEXT,
                            "params_json": "{}",
                        },
                        "id": "call_2",
                    }
                ],
            },
            {
                "role": "tool",
                "name": "run_readonly_sql",
                "content": json.dumps(
                    {
                        "ok": True,
                        "rows": [{"leads_created_today": 11}],
                        "effective_params": {
                            "org_id": "org_internal",
                            "start_date": "2026-06-11",
                            "end_date": "2026-06-12",
                            "timezone": "Asia/Kolkata",
                            "limit": 20,
                        },
                        "row_count": 1,
                        "sql": FULL_SQL_TEXT,
                    }
                ),
            },
        ]
        return initial_messages, loaded_skill_messages, sql_result_messages

    def test_sql_answer_payload_contains_only_compact_context(self):
        _, _, sql_result_messages = self._messages()

        payload = build_sql_answer_payload(sql_result_messages)
        payload_text = json.dumps(payload, sort_keys=True)

        self.assertEqual(
            set(payload),
            {"standalone_question", "rows", "effective_params", "display_metadata"},
        )
        self.assertEqual(
            payload["standalone_question"],
            "Give number of leads created today",
        )
        self.assertEqual(payload["rows"], [{"leads_created_today": 11}])
        self.assertEqual(
            payload["effective_params"],
            {
                "start_date": "2026-06-11",
                "end_date": "2026-06-12",
                "timezone": "Asia/Kolkata",
                "limit": 20,
            },
        )
        self.assertEqual(payload["display_metadata"]["route"], "sql_analytics")
        self.assertEqual(payload["display_metadata"]["skill_name"], "lead_analytics")
        self.assertEqual(payload["display_metadata"]["metric_type"], "count")
        self.assertEqual(payload["display_metadata"]["date_range_label"], "2026-06-11")
        self.assertNotIn(FULL_SKILL_MARKDOWN, payload_text)
        self.assertNotIn(FULL_SQL_TEXT, payload_text)
        self.assertNotIn("Previous answer that must not leak", payload_text)
        self.assertNotIn("org_internal", payload_text)

    def test_compact_agent_answers_from_payload_after_sql_execution(self):
        initial_messages, loaded_skill_messages, sql_result_messages = self._messages()
        execution_agent = _FakeExecutionAgent(loaded_skill_messages, sql_result_messages)
        answer_model = _FakeAnswerModel()
        agent = CompactSqlAnswerAgent(
            execution_agent=execution_agent,
            answer_model=answer_model,
            answer_prompt="ANSWER FROM COMPACT JSON ONLY",
        )

        result = agent.invoke({"messages": initial_messages})

        self.assertEqual(len(execution_agent.payloads), 2)
        self.assertEqual(len(answer_model.payloads), 1)
        answer_messages = answer_model.payloads[0]
        self.assertEqual(answer_messages[0]["content"], "ANSWER FROM COMPACT JSON ONLY")
        answer_payload = json.loads(answer_messages[1]["content"])
        answer_payload_text = answer_messages[1]["content"]

        self.assertEqual(
            set(answer_payload),
            {"standalone_question", "rows", "effective_params", "display_metadata"},
        )
        self.assertNotIn(FULL_SKILL_MARKDOWN, answer_payload_text)
        self.assertNotIn(FULL_SQL_TEXT, answer_payload_text)
        self.assertNotIn("Previous question that must not leak", answer_payload_text)
        self.assertEqual(
            result["messages"][-1],
            {"role": "assistant", "content": "There are 11 leads created today."},
        )
        self.assertEqual(result["sql_answer_payload"], answer_payload)

    def test_sql_answer_messages_put_compact_payload_in_user_message(self):
        answer_payload = {
            "standalone_question": "Give number of leads created today",
            "rows": [{"leads_created_today": 11}],
            "effective_params": {"timezone": "Asia/Kolkata"},
            "display_metadata": {"route": "sql_analytics", "metric_type": "count"},
        }

        messages = build_sql_answer_messages("answer prompt", answer_payload)

        self.assertEqual(messages[0], {"role": "system", "content": "answer prompt"})
        self.assertEqual(json.loads(messages[1]["content"]), answer_payload)


if __name__ == "__main__":
    unittest.main()
