"""Generic SQL agent entry points."""

from app.agents.sql_agent.builder import create_sql_agent

__all__ = ["create_sql_agent"]
