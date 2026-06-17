"""Request and response schemas for the local chatbot API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ChatHistoryMessage(BaseModel):
    """One chat-history message supplied by the Node/frontend caller."""

    model_config = ConfigDict(extra="ignore")

    role: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    """Input accepted by both FastAPI and the reusable chatbot service."""

    model_config = ConfigDict(extra="ignore")

    question: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    org_id: str = Field(..., min_length=1)
    timezone: str = Field(..., min_length=1)
    chat_history: list[ChatHistoryMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Safe JSON response for Node or other HTTP clients."""

    status_code: int
    message: str
    answer: str | None
    route: str | None = None
    standalone_question: str | None = None
    trace_id: str | None = None
