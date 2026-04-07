#!/usr/bin/env python3
"""
update_status.py
Updates status of ONE OR MORE posts in social/posts.csv in a single run.
"""

import argparse
import csv
import os
import sys
import codecs

CSV_PATH       = "social/posts.csv"
VALID_STATUSES = {"pending", "approved", "rejected", "posted"}

# Force UTF-8 output
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)

def update_statuses(changes: dict) -> None:
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
            del pending_changes[title]

    not_found = list(pending_changes.keys())

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

    # Write back with strict UTF-8
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV saved: {CSV_PATH} ({len(updated)} update(s))")


def parse_changes(changes_str: str) -> dict:
    changes = {}
    pairs = changes_str.split("||")
    for pair in pairs:
        pair = pair.strip()
        if "::" not in pair:
            print(f"WARNING: Skipping malformed pair: '{pair}'", file=sys.stderr)
            continue
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
    parser.add_argument("--changes", required=True,
        help='Format: "Title 1::approved||Title 2::rejected||Title 3::approved"')
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
