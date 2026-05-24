from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.config import get_org_timezone, get_sql_agent_settings
from app.org_context import active_org_context, get_active_org_id


class OrgContextTests(unittest.TestCase):
    def test_sql_settings_prefer_active_org_context_over_env_default(self):
        with patch.dict(os.environ, {"HERMON_DEFAULT_CLERK_ORG_ID": "org_live"}):
            self.assertEqual(get_sql_agent_settings().default_org_id, "org_live")

            with active_org_context("org_demo"):
                self.assertEqual(get_active_org_id(), "org_demo")
                self.assertEqual(get_sql_agent_settings().default_org_id, "org_demo")

            self.assertIsNone(get_active_org_id())
            self.assertEqual(get_sql_agent_settings().default_org_id, "org_live")

    def test_configured_org_timezone_is_used(self):
        config = {
            "organization_timezones": {
                "default_timezone": "UTC",
                "by_org_id": {
                    "org_3ARuGHeqbbEu5FNexlpC7ElaiyW": "Europe/Amsterdam",
                },
            }
        }

        with patch("app.config.settings.load_app_config", return_value=config):
            self.assertEqual(
                get_org_timezone("org_3ARuGHeqbbEu5FNexlpC7ElaiyW"),
                "Europe/Amsterdam",
            )

    def test_unknown_org_timezone_defaults_to_utc(self):
        config = {
            "organization_timezones": {
                "default_timezone": "UTC",
                "by_org_id": {
                    "org_3ARuGHeqbbEu5FNexlpC7ElaiyW": "Europe/Amsterdam",
                },
            }
        }

        with patch("app.config.settings.load_app_config", return_value=config):
            self.assertEqual(get_org_timezone("org_unknown"), "UTC")
            self.assertEqual(get_org_timezone(None), "UTC")

    def test_invalid_configured_timezone_raises_clear_error(self):
        config = {
            "organization_timezones": {
                "default_timezone": "UTC",
                "by_org_id": {
                    "org_bad": "Amsterdam",
                },
            }
        }

        with patch("app.config.settings.load_app_config", return_value=config):
            with self.assertRaisesRegex(RuntimeError, "invalid IANA timezone"):
                get_org_timezone("org_bad")


if __name__ == "__main__":
    unittest.main()
