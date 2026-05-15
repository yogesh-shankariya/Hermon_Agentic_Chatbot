"""Diagnostic analytics admin utilities."""

__all__ = [
    "DiagnosticSnapshotBuildError",
    "build_diagnostic_lead_snapshot_once",
]


def __getattr__(name: str):
    if name in __all__:
        from app.diagnostics.lead_snapshot import (
            DiagnosticSnapshotBuildError,
            build_diagnostic_lead_snapshot_once,
        )

        exports = {
            "DiagnosticSnapshotBuildError": DiagnosticSnapshotBuildError,
            "build_diagnostic_lead_snapshot_once": build_diagnostic_lead_snapshot_once,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
