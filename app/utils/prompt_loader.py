"""Prompt loading helpers.

Prompts are versioned YAML files so prompt edits do not require code changes.
The config file chooses which version each agent uses.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml

from app.config.settings import APP_DIR


PROMPTS_DIR = APP_DIR / "prompts"


@dataclass(frozen=True)
class PromptTemplate:
    """A loaded prompt YAML file."""

    name: str
    prompt_id: str
    version: str
    system: str


def load_prompt(agent_name: str, version: str) -> PromptTemplate:
    """Load a prompt by agent name and version."""

    prompt_path = PROMPTS_DIR / agent_name / f"{version}.yaml"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with prompt_path.open("r", encoding="utf-8") as prompt_file:
        raw_prompt: dict[str, Any] = yaml.safe_load(prompt_file) or {}

    system_prompt = str(raw_prompt.get("System", "")).strip()
    if not system_prompt:
        raise ValueError(f"Prompt file is missing a non-empty System block: {prompt_path}")

    return PromptTemplate(
        name=str(raw_prompt.get("name", agent_name)),
        prompt_id=str(raw_prompt.get("id", agent_name)),
        version=str(raw_prompt.get("version", version)),
        system=system_prompt,
    )
