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


class _FakeLangSmithRun:
    def __init__(self, run_id: str) -> None:
        self.id = run_id
        self.metadata = {}
        self.outputs = None
        self.error = None

    def end(self, *, outputs=None, error=None) -> None:
        self.outputs = outputs
        self.error = error


class _FakeLangSmithTraceContext:
    def __init__(self, run: _FakeLangSmithRun) -> None:
        self.run = run

    def __enter__(self) -> _FakeLangSmithRun:
        return self.run

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None


class _FakeLangSmithTrace:
    def __init__(self) -> None:
        self.calls = []

    def __call__(self, name, **kwargs):
        run_id = "trace_123" if kwargs.get("parent") is None else f"child_{len(self.calls)}"
        run = _FakeLangSmithRun(run_id)
        self.calls.append((name, kwargs, run))
        return _FakeLangSmithTraceContext(run)


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

    def _successful_turn(self) -> dict:
        return {
            "question": self.payload["question"],
            "organization_id": self.payload["org_id"],
            "timezone": self.payload["timezone"],
            "chat_history_count": 2,
            "route": "unsupported",
            "selected_skill": None,
            "standalone_question": self.payload["question"],
            "router_response": {"route": "unsupported"},
            "answer": "Final answer",
            "elapsed_seconds": 0.01,
            "timing": {},
            "trace_messages": [],
            "execution_details": {},
        }

    def test_root_returns_api_info_for_cloud_browser_checks(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["health"], "/health")
        self.assertEqual(data["chat"], "/chat")
        self.assertEqual(data["stream"], "/chat/stream")

    def test_favicon_is_quiet_no_content(self) -> None:
        response = self.client.get("/favicon.ico")

        self.assertEqual(response.status_code, 204)

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

    def test_service_returns_langsmith_trace_id_when_tracing_can_persist(self) -> None:
        request = ChatRequest(**self.payload)
        fake_trace = _FakeLangSmithTrace()

        with (
            patch("app.services.chatbot_service._langsmith_tracing_can_persist", return_value=True),
            patch("app.services.chatbot_service.langsmith_trace", fake_trace),
            patch(
                "app.services.chatbot_service.run_chatbot_turn",
                return_value=self._successful_turn(),
            ),
        ):
            response = chatbot_service.run_chatbot(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.trace_id, "trace_123")
        self.assertEqual(fake_trace.calls[0][0], "/chat request")

    def test_service_omits_trace_id_when_langsmith_cannot_persist(self) -> None:
        request = ChatRequest(**self.payload)
        fake_trace = _FakeLangSmithTrace()

        with (
            patch("app.services.chatbot_service._langsmith_tracing_can_persist", return_value=False),
            patch("app.services.chatbot_service.langsmith_trace", fake_trace),
            patch(
                "app.services.chatbot_service.run_chatbot_turn",
                return_value=self._successful_turn(),
            ),
        ):
            response = chatbot_service.run_chatbot(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.trace_id)
        self.assertEqual(fake_trace.calls, [])

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
