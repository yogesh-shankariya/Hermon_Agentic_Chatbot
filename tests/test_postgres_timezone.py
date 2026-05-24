from __future__ import annotations

import unittest

from app.db.postgres import QueryValidationError, ReadOnlyPostgres, ReadOnlyQueryConfig


class FakeTransaction:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class FakeResult:
    def mappings(self):
        return [{"answer": 1}]


class FakeConnection:
    def __init__(self) -> None:
        self.commands: list[str] = []
        self.executed: list[dict[str, object]] = []
        self.transaction = FakeTransaction()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def begin(self) -> FakeTransaction:
        return self.transaction

    def exec_driver_sql(self, sql: str) -> None:
        self.commands.append(sql)

    def execute(self, statement, params):
        self.executed.append({"statement": str(statement), "params": dict(params)})
        return FakeResult()


class FakeEngine:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    def connect(self) -> FakeConnection:
        return self.connection


class ReadOnlyPostgresTimezoneTests(unittest.TestCase):
    def _runner_with_connection(self, connection: FakeConnection) -> ReadOnlyPostgres:
        runner = ReadOnlyPostgres(
            config=ReadOnlyQueryConfig(
                database_url="postgresql://example",
                max_rows=5,
                statement_timeout_ms=4321,
                require_org_scope=False,
            )
        )
        runner._get_engine = lambda: FakeEngine(connection)  # type: ignore[method-assign]
        return runner

    def test_query_records_sets_readonly_timezone_and_timeout(self):
        connection = FakeConnection()
        runner = self._runner_with_connection(connection)

        rows = runner.query_records(
            "SELECT 1 AS answer",
            params={"org_id": "org_demo"},
            timezone_name="Europe/Amsterdam",
        )

        self.assertEqual(rows, [{"answer": 1}])
        self.assertEqual(
            connection.commands,
            [
                "SET TRANSACTION READ ONLY",
                "SET LOCAL TIME ZONE 'Europe/Amsterdam'",
                "SET LOCAL statement_timeout = 4321",
            ],
        )
        self.assertTrue(connection.transaction.committed)
        self.assertFalse(connection.transaction.rolled_back)
        self.assertIn("LIMIT 5", connection.executed[0]["statement"])

    def test_query_records_rejects_invalid_timezone(self):
        connection = FakeConnection()
        runner = self._runner_with_connection(connection)

        with self.assertRaisesRegex(QueryValidationError, "Invalid IANA timezone"):
            runner.query_records("SELECT 1 AS answer", timezone_name="Amsterdam")

        self.assertTrue(connection.transaction.rolled_back)


if __name__ == "__main__":
    unittest.main()
