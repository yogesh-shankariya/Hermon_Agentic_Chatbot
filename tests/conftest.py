"""Pytest bootstrap for deterministic local tests."""

from __future__ import annotations

import os


if os.getenv("HERMON_TEST_ENABLE_LANGSMITH", "").lower() != "true":
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
