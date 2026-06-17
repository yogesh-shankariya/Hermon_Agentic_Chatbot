"""File-backed versioned skill loading utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.config.settings import APP_DIR, load_app_config


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
    version: str
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


def _resolve_base_path(path_value: object) -> Path:
    base_path = str(path_value or "app/skills/modules").strip()
    if not base_path:
        raise SkillRegistryError("skills.base_path must be a non-empty string.")

    path = Path(base_path)
    return path if path.is_absolute() else APP_DIR.parent / path


def _get_skill_config(skill_name: str, version: str | None = None) -> tuple[str, str]:
    config = load_app_config()
    skills_config = config.get("skills", {})
    if not isinstance(skills_config, dict):
        raise SkillRegistryError("skills must be a YAML object.")

    skill_config = skills_config.get(skill_name, {})
    if not isinstance(skill_config, dict):
        raise SkillRegistryError(f"skills.{skill_name} must be a YAML object.")

    path = str(skill_config.get("path") or skill_name).strip()
    if not path:
        raise SkillRegistryError(f"skills.{skill_name}.path must be non-empty when provided.")

    clean_version = str(version or skill_config.get("version") or "").strip()
    if not clean_version:
        raise SkillRegistryError(f"Missing skills.{skill_name}.version in config.")

    return path, clean_version


def get_skill_path(skill_name: str, version: str | None = None) -> Path:
    """Return the configured Markdown skill path for a skill family."""

    clean_name = str(skill_name or "").strip()
    if not clean_name:
        raise SkillRegistryError("Skill name must be non-empty.")

    config = load_app_config()
    skills_config = config.get("skills", {})
    if not isinstance(skills_config, dict):
        raise SkillRegistryError("skills must be a YAML object.")

    folder, clean_version = _get_skill_config(clean_name, version)
    skills_root = _resolve_base_path(skills_config.get("base_path")).resolve()
    skill_path = (skills_root / folder / f"{clean_version}.md").resolve()

    if skills_root not in skill_path.parents and skill_path != skills_root:
        raise SkillRegistryError(f"Skill path escapes skills directory: {folder}/{clean_version}.md")

    return skill_path


def load_skill_body(skill_name: str, version: str | None = None) -> str:
    """Load one configured versioned Markdown skill body."""

    skill_path = get_skill_path(skill_name, version)
    if not skill_path.exists():
        raise SkillRegistryError(f"Skill file not found: {skill_path}")

    content = skill_path.read_text(encoding="utf-8")
    if not content.strip():
        raise SkillRegistryError(f"Skill file is empty: {skill_path}")
    return content


def load_skill_metadata(registry_path: Path = DEFAULT_REGISTRY_PATH) -> list[SkillMetadata]:
    """Load SQL skill metadata entries from ``registry.yaml`` and config versions."""

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
        except KeyError as exc:
            raise SkillRegistryError(
                f"Skill registry entry #{index + 1} is missing required key: {exc.args[0]}"
            ) from exc

        if not name or not description:
            raise SkillRegistryError(
                f"Skill registry entry #{index + 1} has an empty name or description."
            )

        if "path" in raw_skill or "version" in raw_skill:
            raise SkillRegistryError(
                f"Skill registry entry '{name}' must not define path or version; "
                "configure skills.<name>.path and skills.<name>.version in app/config/config.yaml."
            )

        path, version = _get_skill_config(name)

        primary_tables = raw_skill.get("primary_tables")
        if primary_tables is None:
            primary_tables = []
        if not isinstance(primary_tables, list):
            raise SkillRegistryError(
                f"Skill registry entry '{name}' must use a list for primary_tables."
            )

        skills.append(
            SkillMetadata(
                name=name,
                description=description,
                path=path,
                version=version,
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
            content = load_skill_body(metadata.name, metadata.version)
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
