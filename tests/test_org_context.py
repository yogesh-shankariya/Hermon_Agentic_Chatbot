from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.config import get_sql_agent_settings
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


if __name__ == "__main__":
    unittest.main()
