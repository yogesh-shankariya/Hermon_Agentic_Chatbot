"""Middleware that makes SQL skills discoverable to the LangChain agent."""

from __future__ import annotations

from typing import Callable

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.messages import SystemMessage

from app.config import get_sql_agent_settings
from app.tools import SQL_AGENT_TOOLS
from app.utils.skill_loader import build_skills_prompt


class SkillMiddleware(AgentMiddleware):
    """Inject lightweight skill metadata and register SQL tools."""

    tools = SQL_AGENT_TOOLS

    def __init__(self) -> None:
        settings = get_sql_agent_settings()
        self.skills_prompt = build_skills_prompt(
            allowed_skill_names=set(settings.enabled_skills),
        )

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Add available skill descriptions to the system prompt."""

        # The full skill markdown is loaded through a tool only when needed.
        # This addendum keeps the base system prompt small while still making
        # available skills discoverable to the model.
        skills_addendum = (
            "\n\n## Available SQL Skills\n\n"
            f"{self.skills_prompt}\n\n"
            "Use `load_skill` before writing SQL for a supported business question. "
            "Only use skills that are listed above as enabled."
        )

        system_message = request.system_message
        if hasattr(system_message, "content_blocks"):
            new_content = list(system_message.content_blocks) + [
                {"type": "text", "text": skills_addendum}
            ]
        elif isinstance(system_message.content, list):
            new_content = list(system_message.content) + [
                {"type": "text", "text": skills_addendum}
            ]
        else:
            new_content = f"{system_message.content}{skills_addendum}"

        modified_request = request.override(system_message=SystemMessage(content=new_content))
        return handler(modified_request)
