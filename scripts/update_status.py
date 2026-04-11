#!/usr/bin/env python3
"""
update_status.py
Updates status OR permanently deletes posts in social/posts.csv.

Accepts --changes in format:
  "Title 1::approved||Title 2::rejected||Title 3::delete"

Special action "delete" removes the row entirely from the CSV.
All other values are treated as status updates.
"""

import argparse
import csv
import os
import sys
import codecs

CSV_PATH       = "social/posts.csv"
VALID_STATUSES = {"pending", "approved", "rejected", "posted", "post_queue"}
DELETE_ACTION  = "delete"

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")


def process_changes(changes: dict) -> None:
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
        print("ERROR: CSV must have 'title' and 'status' columns.", file=sys.stderr)
        sys.exit(1)

    to_delete   = {title for title, action in changes.items() if action == DELETE_ACTION}
    to_update   = {title: action for title, action in changes.items() if action != DELETE_ACTION}

    kept_rows   = []
    updated     = []
    deleted     = []
    not_found   = set(changes.keys())

    for row in rows:
        title = row.get("title", "").strip()

        if title in to_delete:
            deleted.append(title)
            not_found.discard(title)
            # Row is NOT appended to kept_rows → permanently removed
            continue

        if title in to_update:
            new_status = to_update[title]
            old_status = row.get("status", "").strip()
            if old_status != new_status:
                row["status"] = new_status
                updated.append(f"  '{title}'  {old_status} → {new_status}")
            else:
                updated.append(f"  '{title}'  already {new_status} (no change)")
            not_found.discard(title)

        kept_rows.append(row)

    # Summary
    print(f"Processing {len(changes)} change(s):")
    if updated:
        print("  Status updates:")
        for u in updated:
            print(u)
    if deleted:
        print(f"  Permanently deleted {len(deleted)} row(s):")
        for d in deleted:
            print(f"    - '{d}'")
    if not_found:
        print(f"\nWARNING: {len(not_found)} title(s) not found in CSV:")
        for t in not_found:
            print(f"  - '{t}'")

    if not updated and not deleted:
        print("WARNING: No posts were changed.", file=sys.stderr)
        # Don't exit 1 — not_found shouldn't crash the workflow

    # Write back
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(kept_rows)

    print(f"\nCSV saved: {len(updated)} update(s), {len(deleted)} deletion(s). "
          f"{len(kept_rows)} rows remaining.")


def parse_changes(changes_str: str) -> dict:
    changes = {}
    for pair in changes_str.split("||"):
        pair = pair.strip()
        if "::" not in pair:
            print(f"WARNING: Skipping malformed pair: '{pair}'", file=sys.stderr)
            continue
        idx    = pair.rfind("::")
        title  = pair[:idx].strip()
        action = pair[idx+2:].strip().lower()
        if not title:
            continue
        if action != DELETE_ACTION and action not in VALID_STATUSES:
            print(f"WARNING: Invalid action '{action}' for '{title}' — skipping.", file=sys.stderr)
            continue
        changes[title] = action
    return changes


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--changes", required=True,
        help='Format: "Title 1::approved||Title 2::delete||Title 3::rejected"')
    args    = parser.parse_args()
    changes = parse_changes(args.changes)

    if not changes:
        print("ERROR: No valid changes to process.", file=sys.stderr)
        sys.exit(1)

    print(f"Parsed {len(changes)} change(s):")
    for t, a in changes.items():
        print(f"  '{t}' → {a}")
    print()

    process_changes(changes)
