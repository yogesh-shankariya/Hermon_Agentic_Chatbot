from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.utils import prompt_loader, skill_loader
from app.utils.skill_loader import (
    SkillRegistryError,
    load_skill,
    load_skill_body,
    load_skill_metadata,
)


class PromptLoaderTests(unittest.TestCase):
    def test_load_prompt_uses_configured_markdown_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "prompts"
            prompt_path = base_path / "router" / "1_0_0.md"
            prompt_path.parent.mkdir(parents=True)
            prompt_path.write_text("Router prompt body\n", encoding="utf-8")

            with patch.object(
                prompt_loader,
                "load_app_config",
                return_value={
                    "prompts": {
                        "base_path": str(base_path),
                        "router_path": "router",
                        "router": {"version": "1_0_0"},
                    }
                },
            ):
                prompt = prompt_loader.load_prompt("router")

        self.assertEqual(prompt.name, "router")
        self.assertEqual(prompt.prompt_id, "router")
        self.assertEqual(prompt.version, "1_0_0")
        self.assertEqual(prompt.system, "Router prompt body")
        self.assertEqual(prompt.path, prompt_path)

    def test_load_prompt_requires_configured_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(
                prompt_loader,
                "load_app_config",
                return_value={
                    "prompts": {
                        "base_path": str(Path(temp_dir) / "prompts"),
                        "router_path": "router",
                        "router": {},
                    }
                },
            ):
                with self.assertRaisesRegex(RuntimeError, "Missing prompts.router.version"):
                    prompt_loader.load_prompt("router")

    def test_load_prompt_requires_existing_markdown_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(
                prompt_loader,
                "load_app_config",
                return_value={
                    "prompts": {
                        "base_path": str(Path(temp_dir) / "prompts"),
                        "sql_agent_path": "sql_agent",
                        "sql_agent": {"version": "1_0_0"},
                    }
                },
            ):
                with self.assertRaisesRegex(FileNotFoundError, "Prompt file not found"):
                    prompt_loader.load_prompt("sql_agent")

    def test_load_prompt_rejects_empty_markdown_body(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "prompts"
            prompt_path = base_path / "sql_agent" / "1_0_0.md"
            prompt_path.parent.mkdir(parents=True)
            prompt_path.write_text(" \n", encoding="utf-8")

            with patch.object(
                prompt_loader,
                "load_app_config",
                return_value={
                    "prompts": {
                        "base_path": str(base_path),
                        "sql_agent_path": "sql_agent",
                        "sql_agent": {"version": "1_0_0"},
                    }
                },
            ):
                with self.assertRaisesRegex(ValueError, "Prompt Markdown is empty"):
                    prompt_loader.load_prompt("sql_agent")


class SkillLoaderTests(unittest.TestCase):
    def test_load_skill_uses_configured_path_and_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "skills" / "registry.yaml"
            base_path = registry_path.parent / "modules"
            skill_path = base_path / "test_skill" / "1_0_0.md"
            skill_path.parent.mkdir(parents=True)
            skill_path.write_text("Skill body\n", encoding="utf-8")
            registry_path.write_text(
                """
skills:
  - name: test_skill
    description: Test skill.
    primary_tables:
      - leads
""".lstrip(),
                encoding="utf-8",
            )

            with patch.object(
                skill_loader,
                "load_app_config",
                return_value={
                    "skills": {
                        "base_path": str(base_path),
                        "test_skill": {"path": "test_skill", "version": "1_0_0"},
                    }
                },
            ):
                skill = load_skill("test_skill", registry_path=registry_path)

        self.assertEqual(skill.name, "test_skill")
        self.assertEqual(skill.metadata.version, "1_0_0")
        self.assertEqual(skill.metadata.path, "test_skill")
        self.assertEqual(skill.metadata.primary_tables, ("leads",))
        self.assertEqual(skill.content, "Skill body\n")

    def test_load_skill_body_uses_config_for_non_sql_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "skills" / "modules"
            skill_path = base_path / "lead_360" / "1_0_0.md"
            skill_path.parent.mkdir(parents=True)
            skill_path.write_text("Lead 360 body\n", encoding="utf-8")

            with patch.object(
                skill_loader,
                "load_app_config",
                return_value={
                    "skills": {
                        "base_path": str(base_path),
                        "lead_360": {"path": "lead_360", "version": "1_0_0"},
                    }
                },
            ):
                content = load_skill_body("lead_360")

        self.assertEqual(content, "Lead 360 body\n")

    def test_load_skill_metadata_requires_configured_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "skills" / "registry.yaml"
            registry_path.parent.mkdir(parents=True)
            registry_path.write_text(
                """
skills:
  - name: test_skill
    description: Test skill.
""".lstrip(),
                encoding="utf-8",
            )

            with patch.object(
                skill_loader,
                "load_app_config",
                return_value={
                    "skills": {
                        "base_path": str(registry_path.parent / "modules"),
                        "test_skill": {"path": "test_skill"},
                    }
                },
            ):
                with self.assertRaisesRegex(SkillRegistryError, "Missing skills.test_skill.version"):
                    load_skill_metadata(registry_path=registry_path)

    def test_load_skill_metadata_requires_config_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "skills" / "registry.yaml"
            registry_path.parent.mkdir(parents=True)
            registry_path.write_text(
                """
skills:
  - name: test_skill
    description: Test skill.
""".lstrip(),
                encoding="utf-8",
            )

            with patch.object(
                skill_loader,
                "load_app_config",
                return_value={"skills": {"base_path": str(registry_path.parent / "modules")}},
            ):
                with self.assertRaisesRegex(SkillRegistryError, "Missing skills.test_skill.version"):
                    load_skill_metadata(registry_path=registry_path)

    def test_load_skill_metadata_rejects_registry_path_or_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "skills" / "registry.yaml"
            registry_path.parent.mkdir(parents=True)
            registry_path.write_text(
                """
skills:
  - name: test_skill
    description: Test skill.
    path: old/location
    version: "0_9_0"
""".lstrip(),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(SkillRegistryError, "must not define path or version"):
                load_skill_metadata(registry_path=registry_path)

    def test_load_skill_requires_existing_markdown_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "skills" / "registry.yaml"
            base_path = registry_path.parent / "modules"
            registry_path.parent.mkdir(parents=True)
            registry_path.write_text(
                """
skills:
  - name: test_skill
    description: Test skill.
""".lstrip(),
                encoding="utf-8",
            )

            with patch.object(
                skill_loader,
                "load_app_config",
                return_value={
                    "skills": {
                        "base_path": str(base_path),
                        "test_skill": {"path": "test_skill", "version": "1_0_0"},
                    }
                },
            ):
                with self.assertRaisesRegex(SkillRegistryError, "Skill file not found"):
                    load_skill("test_skill", registry_path=registry_path)

    def test_load_skill_rejects_empty_markdown_body(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "skills" / "registry.yaml"
            base_path = registry_path.parent / "modules"
            skill_path = base_path / "test_skill" / "1_0_0.md"
            skill_path.parent.mkdir(parents=True)
            skill_path.write_text("\n", encoding="utf-8")
            registry_path.write_text(
                """
skills:
  - name: test_skill
    description: Test skill.
""".lstrip(),
                encoding="utf-8",
            )

            with patch.object(
                skill_loader,
                "load_app_config",
                return_value={
                    "skills": {
                        "base_path": str(base_path),
                        "test_skill": {"path": "test_skill", "version": "1_0_0"},
                    }
                },
            ):
                with self.assertRaisesRegex(SkillRegistryError, "Skill file is empty"):
                    load_skill("test_skill", registry_path=registry_path)
