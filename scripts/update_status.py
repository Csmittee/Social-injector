#!/usr/bin/env python3
"""
update_status.py
Updates the 'status' field of a post in social/posts.csv by exact title match.

Usage:
    python scripts/update_status.py --title "My Post Title" --status approved
"""

import argparse
import csv
import os
import sys

CSV_PATH = "social/posts.csv"
VALID_STATUSES = {"pending", "approved", "rejected", "posted"}


def update_status(title: str, new_status: str) -> None:
    title      = title.strip()
    new_status = new_status.strip().lower()

    if new_status not in VALID_STATUSES:
        print(f"ERROR: invalid status '{new_status}'. Must be one of {VALID_STATUSES}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found.", file=sys.stderr)
        sys.exit(1)

    # Read all rows
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames or "title" not in fieldnames or "status" not in fieldnames:
            print(f"ERROR: CSV must have 'title' and 'status' columns. Found: {fieldnames}", file=sys.stderr)
            sys.exit(1)
        rows = list(reader)

    # Find and update
    matched = False
    for row in rows:
        if row.get("title", "").strip() == title:
            old_status = row["status"]
            row["status"] = new_status
            matched = True
            print(f"Updated: '{title}'  {old_status} → {new_status}")
            break   # update only the first exact match

    if not matched:
        print(f"ERROR: No post found with title: '{title}'", file=sys.stderr)
        print("Available titles:", file=sys.stderr)
        for r in rows:
            print(f"  - {r.get('title', '')}", file=sys.stderr)
        sys.exit(1)

    # Write back (preserve all columns, use same quoting)
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV saved: {CSV_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--title",  required=True, help="Exact post title")
    parser.add_argument("--status", required=True, help="New status")
    args = parser.parse_args()
    update_status(args.title, args.status)
