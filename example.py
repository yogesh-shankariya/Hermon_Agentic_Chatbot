from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# Edit values here, then run:
#   python example.py

RUNNER = Path("app/main/local_ai_runner.py")

INPUT_FILE = Path("app/main/local_input/input.txt")
SUBJECT = "Air Freight rate request from Roermond to Nairobi 1119 KG"
FROM_ADDR = "customer@example.com"
TO_ADDR = "sales@iqargo.nl"

ATTACHMENTS = [
    Path("app/main/local_input/ea65af273bf14ec985961a3078d43381_Pallet details.xlsx"),
]

# Add any other CLI parameters here.
# Example:
# EXTRA_ARGS = ["--cc-addr", "manager@example.com", "--dry-run"]
EXTRA_ARGS: list[str] = []


def build_command() -> list[str]:
    command = [
        sys.executable,
        str(RUNNER),
        "--input",
        str(INPUT_FILE),
        "--subject",
        SUBJECT,
        "--from-addr",
        FROM_ADDR,
        "--to-addr",
        TO_ADDR,
    ]

    for attachment in ATTACHMENTS:
        command.extend(["--attachment", str(attachment)])

    command.extend(EXTRA_ARGS)
    return command


def main() -> None:
    if not RUNNER.exists():
        raise SystemExit(
            f"Runner not found: {RUNNER}\n"
            "Update RUNNER in example.py if local_ai_runner.py lives somewhere else."
        )

    subprocess.run(build_command(), check=True)


if __name__ == "__main__":
    main()
