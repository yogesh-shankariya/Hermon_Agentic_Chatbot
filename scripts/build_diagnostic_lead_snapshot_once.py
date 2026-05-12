#!/usr/bin/env python3
"""Build the static diagnostic lead snapshot once for a selected organization."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build diagnostic_lead_snapshot once for one organization.",
    )
    parser.add_argument(
        "--org-id",
        required=False,
        help="Clerk organization ID to build the snapshot for. Defaults to HERMON_DEFAULT_CLERK_ORG_ID from .env.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete and rebuild existing snapshot rows for this org. Use only for local/demo reruns.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    from app.diagnostics import (  # noqa: WPS433
        DiagnosticSnapshotBuildError,
        build_diagnostic_lead_snapshot_once,
    )

    try:
        org_id = args.org_id or os.getenv("HERMON_DEFAULT_CLERK_ORG_ID")
        summary = build_diagnostic_lead_snapshot_once(org_id or "", force=args.force)
    except DiagnosticSnapshotBuildError as exc:
        print(f"diagnostic snapshot build failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(_json_safe(summary), indent=2, sort_keys=True))
    return 0


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


if __name__ == "__main__":
    raise SystemExit(main())
