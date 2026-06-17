"""FastAPI entrypoint for the local Hermon chatbot service."""

from __future__ import annotations

import json
import queue
import threading
from collections.abc import Iterator
from typing import Any

from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse

from app.schema.chat import ChatRequest, ChatResponse
from app.services.chatbot_service import response_to_dict, run_chatbot


app = FastAPI(title="Hermon Chatbot Service")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "Hermon Chatbot Service",
        "status": "ok",
        "health": "/health",
        "chat": "/chat",
        "stream": "/chat/stream",
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


def _validation_message(exc: RequestValidationError) -> str:
    field_messages = {
        "question": "Question is required.",
        "user_id": "User ID is required.",
        "org_id": "Organization ID is required.",
        "timezone": "Timezone is required.",
    }
    for error in exc.errors():
        loc = [str(part) for part in error.get("loc", [])]
        for field, message in field_messages.items():
            if field in loc:
                return message
    return "Invalid request."


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Any,
    exc: RequestValidationError,
) -> JSONResponse:
    _ = request
    response = ChatResponse(
        status_code=400,
        message=_validation_message(exc),
        answer=None,
        route=None,
        standalone_question=None,
        trace_id=None,
    )
    return JSONResponse(status_code=400, content=response_to_dict(response))


def _json_response_for_chat(response: ChatResponse) -> ChatResponse | JSONResponse:
    if response.status_code == 200:
        return response
    return JSONResponse(
        status_code=response.status_code,
        content=response_to_dict(response),
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse | JSONResponse:
    return _json_response_for_chat(run_chatbot(request))


def _sse(event_name: str, payload: dict[str, Any]) -> str:
    data = json.dumps(payload, default=str, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event_name}\ndata: {data}\n\n"


def _progress_events(message_or_event: str | dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    if isinstance(message_or_event, dict):
        message = str(message_or_event.get("message") or "").strip()
        route = str(message_or_event.get("route") or "").strip()
        stage = str(message_or_event.get("stage") or "").strip()
        events: list[tuple[str, dict[str, Any]]] = []
        if message:
            events.append(("status", {"message": message}))
        if route and stage == "route_selected":
            events.append(("route", {"route": route}))
        return events

    message = str(message_or_event or "").strip()
    return [("status", {"message": message})] if message else []


def _stream_chat_events(request: ChatRequest) -> Iterator[str]:
    events: queue.Queue[tuple[str, dict[str, Any]] | None] = queue.Queue()

    def emit_progress(message_or_event: str | dict[str, Any]) -> None:
        for event_name, payload in _progress_events(message_or_event):
            events.put((event_name, payload))

    def worker() -> None:
        try:
            response = run_chatbot(request, progress_callback=emit_progress)
            event_name = "done" if response.status_code == 200 else "error"
            events.put((event_name, response_to_dict(response)))
        except Exception:  # noqa: BLE001 - streaming errors must stay user-safe.
            response = ChatResponse(
                status_code=500,
                message="Unable to complete this request.",
                answer=None,
                route=None,
                standalone_question=None,
                trace_id=None,
            )
            events.put(("error", response_to_dict(response)))
        finally:
            events.put(None)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    while True:
        item = events.get()
        if item is None:
            break
        event_name, payload = item
        yield _sse(event_name, payload)


@app.post("/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _stream_chat_events(request),
        media_type="text/event-stream",
    )
