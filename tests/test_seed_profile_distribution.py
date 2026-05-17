from __future__ import annotations

import importlib.util
import random
import sys
import unittest
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEED_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "seed_demo_data.py"


def _load_seed_script():
    module_name = "seed_demo_data_under_test"
    spec = importlib.util.spec_from_file_location(module_name, SEED_SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class SeedProfileDistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.seed = _load_seed_script()

    def test_monthly_profession_distribution_is_weighted_and_reconciles_to_leads(self):
        monthly_distribution = self.seed.MONTHLY_PROFESSION_DISTRIBUTION
        monthly_leads = self.seed.MONTHLY_LEAD_DISTRIBUTION

        self.assertEqual(set(monthly_distribution), set(monthly_leads))
        for month_key, distribution in monthly_distribution.items():
            with self.subTest(month_key=month_key):
                self.assertEqual(sum(distribution.values()), monthly_leads[month_key])
                self.assertGreater(len(set(distribution.values())), 1)

        totals = Counter()
        for distribution in monthly_distribution.values():
            totals.update(distribution)
        self.assertEqual(dict(totals), self.seed.PROFESSION_DISTRIBUTION)
        self.assertEqual(self.seed.PROFESSION_DISTRIBUTION["Business Owner"], 101)
        self.assertEqual(self.seed.PROFESSION_DISTRIBUTION["Employee"], 85)
        self.assertEqual(self.seed.PROFESSION_DISTRIBUTION["Self-employed"], 65)
        self.assertEqual(sum(self.seed.PROFESSION_DISTRIBUTION.values()), 500)
        self.assertGreater(len(set(self.seed.PROFESSION_DISTRIBUTION.values())), 1)

    def test_generated_profile_plans_match_expected_distribution(self):
        random.seed(self.seed.RANDOM_SEED)

        profession_plan = self.seed.generate_monthly_profession_plan()
        profession_totals = Counter()
        for month_key, values in profession_plan.items():
            with self.subTest(month_key=month_key):
                self.assertEqual(Counter(values), self.seed.MONTHLY_PROFESSION_DISTRIBUTION[month_key])
            profession_totals.update(values)
        self.assertEqual(dict(profession_totals), self.seed.PROFESSION_DISTRIBUTION)

        employment_plan = self.seed.generate_employment_status_plan()
        self.assertEqual(Counter(employment_plan), self.seed.EMPLOYMENT_STATUS_DISTRIBUTION)
        self.assertEqual(len(employment_plan), 500)
        self.assertGreater(len(set(self.seed.EMPLOYMENT_STATUS_DISTRIBUTION.values())), 1)


if __name__ == "__main__":
    unittest.main()
