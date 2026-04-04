#!/usr/bin/env python3
"""
update_status.py
Updates status of ONE OR MORE posts in social/posts.csv in a single run.

Called by .github/workflows/update-status.yml
Usage:
    python scripts/update_status.py --changes "Title 1:approved,Title 2:rejected,Title 3:approved"
"""

import argparse
import csv
import os
import sys

CSV_PATH       = "social/posts.csv"
VALID_STATUSES = {"pending", "approved", "rejected", "posted"}


def update_statuses(changes: dict) -> None:
    """
    changes = { "Post Title": "approved", "Other Title": "rejected", ... }
    """
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found.", file=sys.stderr)
        sys.exit(1)

    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader     = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            print("ERROR: CSV is empty.", file=sys.stderr)
            sys.exit(1)
        rows = list(reader)

    if "title" not in fieldnames or "status" not in fieldnames:
        print(f"ERROR: CSV must have 'title' and 'status' columns.", file=sys.stderr)
        sys.exit(1)

    updated   = []
    not_found = []

    # Track which titles we still need to match
    pending_changes = dict(changes)

    for row in rows:
        title = row.get("title", "").strip()
        if title in pending_changes:
            new_status = pending_changes[title]
            old_status = row["status"].strip()
            if old_status != new_status:
                row["status"] = new_status
                updated.append(f"  '{title}'  {old_status} -> {new_status}")
            else:
                updated.append(f"  '{title}'  already {new_status} (no change)")
            del pending_changes[title]  # mark as matched

    # Anything left in pending_changes was not found
    not_found = list(pending_changes.keys())

    # Report
    print(f"Processing {len(changes)} status change(s):")
    for u in updated:
        print(u)
    if not_found:
        print(f"\nWARNING: {len(not_found)} title(s) not found in CSV:")
        for t in not_found:
            print(f"  - '{t}'")

    if not updated and not_found:
        print("ERROR: No posts were updated.", file=sys.stderr)
        sys.exit(1)

    # Write back
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV saved: {CSV_PATH} ({len(updated)} update(s))")


def parse_changes(changes_str: str) -> dict:
    """
    Parse "Title 1:approved,Title 2:rejected" into a dict.
    Handles titles that contain commas by using | as separator between pairs.
    Format: "title1::status1||title2::status2"
    """
    changes = {}
    # Use || as pair separator and :: as title:status separator
    pairs = changes_str.split("||")
    for pair in pairs:
        pair = pair.strip()
        if "::" not in pair:
            print(f"WARNING: Skipping malformed pair: '{pair}'", file=sys.stderr)
            continue
        # Split on LAST :: to handle titles with :: in them
        idx    = pair.rfind("::")
        title  = pair[:idx].strip()
        status = pair[idx+2:].strip().lower()
        if not title:
            continue
        if status not in VALID_STATUSES:
            print(f"WARNING: Invalid status '{status}' for '{title}' — skipping.", file=sys.stderr)
            continue
        changes[title] = status

    return changes


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--changes", required=True,
        help='Format: "Title 1::approved||Title 2::rejected||Title 3::approved"'
    )
    args    = parser.parse_args()
    changes = parse_changes(args.changes)

    if not changes:
        print("ERROR: No valid changes to process.", file=sys.stderr)
        sys.exit(1)

    print(f"Parsed {len(changes)} change(s):")
    for t, s in changes.items():
        print(f"  '{t}' -> {s}")
    print()

    update_statuses(changes)
