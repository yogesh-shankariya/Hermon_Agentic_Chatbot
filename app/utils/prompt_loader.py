"""Versioned Markdown prompt loading helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config.settings import APP_DIR, load_app_config


@dataclass(frozen=True)
class PromptTemplate:
    """A loaded Markdown prompt file."""

    name: str
    prompt_id: str
    version: str
    system: str
    path: Path


def _resolve_base_path(path_value: object) -> Path:
    base_path = str(path_value or "app/prompts").strip()
    if not base_path:
        raise RuntimeError("prompts.base_path must be a non-empty string.")

    path = Path(base_path)
    return path if path.is_absolute() else APP_DIR.parent / path


def get_prompt_path(prompt_name: str, version: str | None = None) -> Path:
    """Return the configured Markdown prompt path for a prompt family."""

    clean_name = str(prompt_name or "").strip()
    if not clean_name:
        raise RuntimeError("Prompt name must be non-empty.")

    config = load_app_config()
    prompts_config = config.get("prompts", {})
    if not isinstance(prompts_config, dict):
        raise RuntimeError("prompts must be a YAML object.")

    prompt_config = prompts_config.get(clean_name, {})
    if not isinstance(prompt_config, dict):
        raise RuntimeError(f"prompts.{clean_name} must be a YAML object.")

    clean_version = str(version or prompt_config.get("version") or "").strip()
    if not clean_version:
        raise RuntimeError(f"Missing prompts.{clean_name}.version in config.")

    folder = str(prompts_config.get(f"{clean_name}_path") or clean_name).strip()
    if not folder:
        raise RuntimeError(f"prompts.{clean_name}_path must be non-empty when provided.")

    return _resolve_base_path(prompts_config.get("base_path")) / folder / f"{clean_version}.md"


def load_prompt(prompt_name: str, version: str | None = None) -> PromptTemplate:
    """Load a configured versioned Markdown prompt."""

    prompt_path = get_prompt_path(prompt_name, version)
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    system_prompt = prompt_path.read_text(encoding="utf-8").strip()
    if not system_prompt:
        raise ValueError(f"Prompt Markdown is empty: {prompt_path}")

    config = load_app_config()
    prompts_config = config.get("prompts", {})
    prompt_config = prompts_config.get(str(prompt_name), {}) if isinstance(prompts_config, dict) else {}
    prompt_config = prompt_config if isinstance(prompt_config, dict) else {}

    clean_version = str(version or prompt_config.get("version") or prompt_path.stem)

    return PromptTemplate(
        name=str(prompt_config.get("name", prompt_name)),
        prompt_id=str(prompt_config.get("id", prompt_name)),
        version=clean_version,
        system=system_prompt,
        path=prompt_path,
    )
