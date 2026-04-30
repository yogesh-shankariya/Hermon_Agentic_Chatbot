"""File-backed skill loading utilities for the SQL assistant.

The LangChain tutorial keeps skills in memory. Hermon stores lightweight skill
metadata in ``app/skills/registry.yaml`` and detailed skill instructions in
``app/skills/modules/*.md``. This module keeps that data layout separate from
the Python agent/tool packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


APP_DIR = Path(__file__).resolve().parents[1]
SKILLS_DIR = APP_DIR / "skills"
DEFAULT_REGISTRY_PATH = SKILLS_DIR / "registry.yaml"


class SkillRegistryError(ValueError):
    """Raised when a skill registry entry is invalid or missing."""


@dataclass(frozen=True)
class SkillMetadata:
    """Lightweight skill metadata shown to the agent upfront."""

    name: str
    description: str
    path: str
    primary_tables: tuple[str, ...] = ()


@dataclass(frozen=True)
class Skill:
    """A full skill loaded on demand."""

    metadata: SkillMetadata
    content: str

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def description(self) -> str:
        return self.metadata.description


def load_skill_metadata(registry_path: Path = DEFAULT_REGISTRY_PATH) -> list[SkillMetadata]:
    """Load all skill metadata entries from ``registry.yaml``."""

    if not registry_path.exists():
        raise SkillRegistryError(f"Skill registry not found: {registry_path}")

    with registry_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    raw_skills = data.get("skills")
    if not isinstance(raw_skills, list):
        raise SkillRegistryError("Skill registry must contain a top-level 'skills' list.")

    skills: list[SkillMetadata] = []
    for index, raw_skill in enumerate(raw_skills):
        if not isinstance(raw_skill, dict):
            raise SkillRegistryError(f"Skill registry entry #{index + 1} must be a mapping.")

        try:
            name = str(raw_skill["name"]).strip()
            description = str(raw_skill["description"]).strip()
            path = str(raw_skill["path"]).strip()
        except KeyError as exc:
            raise SkillRegistryError(
                f"Skill registry entry #{index + 1} is missing required key: {exc.args[0]}"
            ) from exc

        if not name or not description or not path:
            raise SkillRegistryError(
                f"Skill registry entry #{index + 1} has an empty name, description, or path."
            )

        primary_tables = raw_skill.get("primary_tables", ())
        if primary_tables is None:
            primary_tables = ()
        if not isinstance(primary_tables, list):
            raise SkillRegistryError(
                f"Skill registry entry '{name}' must use a list for primary_tables."
            )

        skills.append(
            SkillMetadata(
                name=name,
                description=description,
                path=path,
                primary_tables=tuple(str(table).strip() for table in primary_tables),
            )
        )

    return skills


def list_skill_metadata(
    *,
    allowed_skill_names: set[str] | None = None,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
) -> list[SkillMetadata]:
    """Return metadata for skills, optionally scoped to a set of names."""

    skills = load_skill_metadata(registry_path)
    if allowed_skill_names is None:
        return skills

    allowed = {name.strip() for name in allowed_skill_names}
    return [skill for skill in skills if skill.name in allowed]


def load_skill(
    skill_name: str,
    *,
    allowed_skill_names: set[str] | None = None,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
) -> Skill:
    """Load one skill's metadata and Markdown content."""

    normalized_name = skill_name.strip()
    available = list_skill_metadata(
        allowed_skill_names=allowed_skill_names,
        registry_path=registry_path,
    )

    for metadata in available:
        if metadata.name == normalized_name:
            skill_path = (registry_path.parent / metadata.path).resolve()
            skills_root = registry_path.parent.resolve()
            if skills_root not in skill_path.parents and skill_path != skills_root:
                raise SkillRegistryError(f"Skill path escapes skills directory: {metadata.path}")
            if not skill_path.exists():
                raise SkillRegistryError(f"Skill file not found: {skill_path}")

            content = skill_path.read_text(encoding="utf-8")
            return Skill(metadata=metadata, content=content)

    names = ", ".join(skill.name for skill in available) or "none"
    raise SkillRegistryError(f"Skill '{skill_name}' not found. Available skills: {names}")


def build_skills_prompt(
    *,
    allowed_skill_names: set[str] | None = None,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
) -> str:
    """Build the lightweight skill list injected into the system prompt."""

    skills = list_skill_metadata(
        allowed_skill_names=allowed_skill_names,
        registry_path=registry_path,
    )
    if not skills:
        return "No SQL skills are currently enabled."

    lines = []
    for skill in skills:
        tables = ", ".join(skill.primary_tables)
        table_suffix = f" Primary tables: {tables}." if tables else ""
        lines.append(f"- **{skill.name}**: {skill.description}{table_suffix}")

    return "\n".join(lines)


def skill_names(registry_path: Path = DEFAULT_REGISTRY_PATH) -> set[str]:
    """Return all known skill names from the registry."""

    return {skill.name for skill in load_skill_metadata(registry_path)}
