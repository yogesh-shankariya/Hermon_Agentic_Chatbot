from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.schema.chat import ChatRequest, ChatResponse
from app.services import chatbot_service


EXPECTED_RESPONSE_KEYS = {
    "status_code",
    "message",
    "answer",
    "route",
    "standalone_question",
    "trace_id",
}


class FastApiResponseContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.payload = {
            "question": "Show me revenue trend",
            "user_id": "user_123",
            "org_id": "org_123",
            "timezone": "Europe/Amsterdam",
            "chat_history": [
                {"role": "user", "content": "Previous question"},
                {"role": "assistant", "content": "Previous answer"},
            ],
        }

    def test_chat_success_returns_minimal_schema(self) -> None:
        service_response = ChatResponse(
            status_code=200,
            message="success",
            answer="Final answer",
            route="sql_analytics",
            standalone_question="Show me revenue trend",
            trace_id="trace_123",
        )

        with patch("app.main.run_chatbot", return_value=service_response) as run_mock:
            response = self.client.post("/chat", json=self.payload)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(set(data), EXPECTED_RESPONSE_KEYS)
        self.assertEqual(data["message"], "success")
        self.assertNotIn("success", data)
        self.assertNotIn("error", data)
        self.assertNotIn("timezone", data)
        self.assertNotIn("root_run_id", data)
        request = run_mock.call_args.args[0]
        self.assertFalse(hasattr(request, "session_id"))

    def test_chat_error_uses_response_status_code(self) -> None:
        service_response = ChatResponse(
            status_code=500,
            message="Unable to complete this request.",
            answer=None,
            route="sql_analytics",
            standalone_question="Show me revenue trend",
            trace_id="trace_error_123",
        )

        with patch("app.main.run_chatbot", return_value=service_response):
            response = self.client.post("/chat", json=self.payload)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(set(response.json()), EXPECTED_RESPONSE_KEYS)
        self.assertIsNone(response.json()["answer"])

    def test_validation_error_is_400_contract_response(self) -> None:
        payload = dict(self.payload)
        payload.pop("question")

        response = self.client.post("/chat", json=payload)

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(set(data), EXPECTED_RESPONSE_KEYS)
        self.assertEqual(data["message"], "Question is required.")
        self.assertIsNone(data["trace_id"])

    def test_service_rejects_blank_required_field(self) -> None:
        request = ChatRequest(
            question="Show me revenue trend",
            user_id=" ",
            org_id="org_123",
            timezone="Europe/Amsterdam",
        )

        with (
            patch("app.services.chatbot_service.langsmith_trace", None),
            patch("app.services.chatbot_service.run_chatbot_turn") as run_turn_mock,
        ):
            response = chatbot_service.run_chatbot(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.message, "User ID is required.")
        self.assertIsNone(response.answer)
        run_turn_mock.assert_not_called()

    def test_stream_sends_status_route_and_done_events(self) -> None:
        def fake_run_chatbot(request, *, progress_callback=None):
            if progress_callback is not None:
                progress_callback("Understanding your question...")
                progress_callback(
                    {
                        "stage": "route_selected",
                        "message": "Route selected: sql analytics.",
                        "route": "sql_analytics",
                    }
                )
            return ChatResponse(
                status_code=200,
                message="success",
                answer="Final answer",
                route="sql_analytics",
                standalone_question="Show me revenue trend",
                trace_id="trace_123",
            )

        with patch("app.main.run_chatbot", side_effect=fake_run_chatbot):
            response = self.client.post("/chat/stream", json=self.payload)

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers["content-type"])
        self.assertIn("event: status", response.text)
        self.assertIn('data: {"message":"Understanding your question..."}', response.text)
        self.assertIn("event: route", response.text)
        self.assertIn('data: {"route":"sql_analytics"}', response.text)
        self.assertIn("event: done", response.text)
        self.assertIn('"trace_id":"trace_123"', response.text)

    def test_stream_sends_error_event_for_service_error(self) -> None:
        service_response = ChatResponse(
            status_code=500,
            message="Unable to complete this request.",
            answer=None,
            route=None,
            standalone_question=None,
            trace_id="trace_error_123",
        )

        with patch("app.main.run_chatbot", return_value=service_response):
            response = self.client.post("/chat/stream", json=self.payload)

        self.assertEqual(response.status_code, 200)
        self.assertIn("event: error", response.text)
        self.assertIn('"status_code":500', response.text)
        self.assertIn('"trace_id":"trace_error_123"', response.text)


if __name__ == "__main__":
    unittest.main()
