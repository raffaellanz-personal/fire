#!/usr/bin/env python3
"""
Safe Duplicate EMLX Remover

IMPORTANT:
    This script NEVER permanently deletes files.

It reads:
    duplicate_groups.csv

from the duplicate audit script and:
    - keeps the recommended canonical email
    - moves duplicate copies into a quarantine folder

This is MUCH safer than deleting immediately.

Recommended workflow:

1. Run duplicate audit:

    python3 scripts/audit_emlx_duplicates.py FireClaimEmail_Claude duplicate_audit

2. Review:

    duplicate_audit/duplicate_groups.csv

3. Move duplicates to quarantine:

    python3 scripts/safe_remove_duplicate_emlx.py

4. Manually inspect quarantine before permanent deletion.

Default folders:
    duplicate_audit/
    duplicate_quarantine/

Nothing is permanently deleted.
"""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

DEFAULT_AUDIT_DIR = Path("duplicate_audit")
DEFAULT_QUARANTINE_DIR = Path("duplicate_quarantine")


def safe_name(path: Path) -> str:
    return str(path).replace("/", "__")


def main() -> int:
    parser = argparse.ArgumentParser(description="Move duplicate .emlx files into quarantine.")
    parser.add_argument("--audit-dir", default=str(DEFAULT_AUDIT_DIR))
    parser.add_argument("--quarantine-dir", default=str(DEFAULT_QUARANTINE_DIR))
    parser.add_argument("--apply", action="store_true", help="Actually move files. Without this flag, performs dry-run only.")
    args = parser.parse_args()

    audit_dir = Path(args.audit_dir)
    quarantine_dir = Path(args.quarantine_dir)
    duplicates_csv = audit_dir / "duplicate_groups.csv"

    if not duplicates_csv.exists():
        print(f"ERROR: missing {duplicates_csv}")
        return 2

    quarantine_dir.mkdir(parents=True, exist_ok=True)

    moves = []

    with duplicates_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row.get("recommended_keep") == "YES":
                continue

            src = Path(row["file"])

            # Skip missing files.
            if not src.exists():
                continue

            dst = quarantine_dir / safe_name(src)

            moves.append((src, dst, row.get("group_type", "unknown")))

    print(f"Duplicate files identified for quarantine: {len(moves)}")

    if not args.apply:
        print("\nDRY RUN ONLY. No files moved.\n")
        for src, dst, gtype in moves[:50]:
            print(f"[{gtype}] MOVE:")
            print(f"  FROM: {src}")
            print(f"  TO:   {dst}")
            print()

        if len(moves) > 50:
            print(f"... plus {len(moves)-50} more")

        print("\nTo actually move duplicates into quarantine:")
        print("python3 scripts/safe_remove_duplicate_emlx.py --apply")
        return 0

    moved = 0

    for src, dst, _gtype in moves:
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved += 1
        except Exception as exc:
            print(f"FAILED: {src} -> {exc}")

    print(f"\nMoved {moved} duplicate files into quarantine:")
    print(quarantine_dir)
    print("\nNothing permanently deleted.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
