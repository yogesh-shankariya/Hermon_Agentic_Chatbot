from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from app import poc_chat_history


class PocChatHistoryTests(unittest.TestCase):
    def test_schema_and_wal_mode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.sqlite3"
            poc_chat_history.ensure_poc_chat_history_table(db_path)

            with sqlite3.connect(db_path) as connection:
                journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
                columns = connection.execute("PRAGMA table_info(poc_chat_history)").fetchall()

            self.assertEqual(journal_mode, "wal")
            self.assertEqual(
                [(column[1], column[2]) for column in columns],
                [
                    ("id", "INTEGER"),
                    ("organization_id", "TEXT"),
                    ("route", "TEXT"),
                    ("selected_skill", "TEXT"),
                    ("user_question", "TEXT"),
                    ("standalone_question", "TEXT"),
                    ("generated_sql", "TEXT"),
                    ("answer", "TEXT"),
                    ("created_at", "TEXT"),
                    ("elapsed_seconds", "REAL"),
                    ("execution_details_json", "TEXT"),
                    ("timing_json", "TEXT"),
                    ("lead_360_diagnostics_json", "TEXT"),
                ],
            )

    def test_insert_prunes_to_latest_five_per_organization(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.sqlite3"

            for index in range(7):
                poc_chat_history.insert_poc_chat_history(
                    organization_id="org_1",
                    route="sql_analytics",
                    selected_skill="lead_analytics",
                    user_question=f"q{index}",
                    standalone_question=f"sq{index}",
                    generated_sql=f"SELECT {index}",
                    answer=f"a{index}",
                    created_at=f"2026-05-09T00:00:0{index}+00:00",
                    db_path=db_path,
                )
            for index in range(2):
                poc_chat_history.insert_poc_chat_history(
                    organization_id="org_2",
                    route="lead_360",
                    user_question=f"other q{index}",
                    generated_sql="SELECT should_not_store",
                    answer=f"other a{index}",
                    created_at=f"2026-05-09T00:01:0{index}+00:00",
                    db_path=db_path,
                )

            org_1_rows = poc_chat_history.fetch_latest_poc_chat_history("org_1", db_path=db_path)
            org_2_rows = poc_chat_history.fetch_latest_poc_chat_history("org_2", db_path=db_path)

            self.assertEqual([row["user_question"] for row in org_1_rows], ["q6", "q5", "q4", "q3", "q2"])
            self.assertEqual([row["user_question"] for row in org_2_rows], ["other q1", "other q0"])

    def test_router_history_returns_latest_five_oldest_to_newest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.sqlite3"

            for index in range(6):
                poc_chat_history.insert_poc_chat_history(
                    organization_id="org_1",
                    route="sql_analytics",
                    user_question=f"q{index}",
                    answer=f"a{index}",
                    created_at=f"2026-05-09T00:00:0{index}+00:00",
                    db_path=db_path,
                )

            rows = poc_chat_history.fetch_router_poc_chat_history("org_1", db_path=db_path)
            self.assertEqual([row["user_question"] for row in rows], ["q1", "q2", "q3", "q4", "q5"])

    def test_non_sql_routes_do_not_store_generated_sql(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.sqlite3"

            poc_chat_history.insert_poc_chat_history(
                organization_id="org_1",
                route="lead_360",
                selected_skill="lead_analytics",
                user_question="What happened with Vedran?",
                standalone_question="What happened with Vedran?",
                generated_sql="SELECT should_not_store",
                answer="Lead answer",
                db_path=db_path,
            )

            row = poc_chat_history.fetch_latest_poc_chat_history("org_1", db_path=db_path)[0]
            self.assertIsNone(row["selected_skill"])
            self.assertIsNone(row["generated_sql"])

    def test_persists_display_diagnostics_for_recent_turns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "history.sqlite3"

            poc_chat_history.insert_poc_chat_history(
                organization_id="org_1",
                route="sql_analytics",
                selected_skill="lead_analytics",
                user_question="How many won?",
                standalone_question="How many won?",
                generated_sql="SELECT 1",
                answer="One row.",
                elapsed_seconds=1.25,
                execution_details={
                    "sql": "SELECT 1",
                    "rows": [{"won_count": 1}],
                    "row_count": 1,
                },
                timing={
                    "total_seconds": 1.25,
                    "events": [{"kind": "tool", "duration_seconds": 0.2}],
                },
                lead_360_diagnostics={"timings": {"events": []}},
                db_path=db_path,
            )

            row = poc_chat_history.fetch_latest_poc_chat_history("org_1", db_path=db_path)[0]

            self.assertEqual(row["elapsed_seconds"], 1.25)
            self.assertEqual(row["execution_details"]["rows"], [{"won_count": 1}])
            self.assertEqual(row["timing"]["total_seconds"], 1.25)
            self.assertEqual(row["lead_360_diagnostics"], {"timings": {"events": []}})


if __name__ == "__main__":
    unittest.main()
