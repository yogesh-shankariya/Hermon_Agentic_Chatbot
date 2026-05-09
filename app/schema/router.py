from enum import Enum
from pydantic import BaseModel, Field


class RouterRoute(str, Enum):
    SQL_ANALYTICS = "sql_analytics"
    LEAD_360 = "lead_360"
    DIAGNOSTIC_ANALYTICS = "diagnostic_analytics"
    UNSUPPORTED = "unsupported"


class RouterResponse(BaseModel):
    model_config = {"extra": "forbid"}

    route: RouterRoute = Field(
        ...,
        description="The selected route for the current user question."
    )

    history_count: int = Field(
        ...,
        ge=0,
        le=5,
        description="Number of most recent previous Q&A turns required by the next flow. Use 0 when no previous history is needed."
    )

    standalone_question: str = Field(
        ...,
        min_length=1,
        description="Standalone rewritten version of the current user question. If history_count is 0, keep it the same as the current question."
    )