#!/usr/bin/env python3
"""
buffer_poster.py
Sends approved post_queue posts to Buffer for scheduling.
Uses Buffer's GraphQL API (new 2024+ API, not the old REST API).

Called by .github/workflows/buffer-poster.yml
Secrets required: BUFFER_API_KEY

Buffer API endpoint: https://api.buffer.com (GraphQL)
"""

import argparse
import csv
import codecs
import json
import os
import sys
import urllib.error
import urllib.request

CSV_PATH   = "social/posts.csv"
BUFFER_API = "https://api.buffer.com"

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")


def graphql(query: str, variables: dict, api_key: str) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        BUFFER_API,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Buffer API error {e.code}: {e.read().decode()}")


def get_channels(api_key: str) -> list:
    """Returns list of {id, service, name} for all connected channels."""
    query = """
    query {
      channels {
        id
        service
        name
        serviceUsername
      }
    }
    """
    data = graphql(query, {}, api_key)
    return data.get("data", {}).get("channels", [])


def match_channel(channels: list, platform: str) -> str | None:
    """Finds the best channel ID for a given platform name."""
    platform_map = {
        "facebook":  ["facebook"],
        "instagram": ["instagram"],
        "line":      [],   # Buffer doesn't support Line OA
        "twitter":   ["twitter", "x"],
        "linkedin":  ["linkedin"],
    }
    target = platform_map.get(platform.lower(), [platform.lower()])
    for ch in channels:
        if ch.get("service", "").lower() in target:
            return ch["id"]
    return None


def create_buffer_post(title: str, caption: str, image_url: str,
                       post_date: str, channel_id: str, api_key: str) -> dict:
    """Creates a scheduled post in Buffer with image."""

    # Convert post_date "YYYY-MM-DD HH:MM" -> ISO 8601 UTC
    # Assumes times stored in CSV are in local Thai time (UTC+7)
    # Adjust offset as needed
    due_at = None
    if post_date:
        try:
            from datetime import datetime, timezone, timedelta
            tz_offset = timedelta(hours=7)  # Thailand UTC+7
            local_dt  = datetime.strptime(post_date.strip(), "%Y-%m-%d %H:%M")
            utc_dt    = local_dt - tz_offset
            due_at    = utc_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except Exception:
            due_at = None

    # Build mutation
    if due_at:
        mutation = """
        mutation CreatePost($input: CreatePostInput!) {
          createPost(input: $input) {
            ... on PostActionSuccess {
              post { id text dueAt }
            }
            ... on MutationError { message }
          }
        }
        """
        variables = {
            "input": {
                "text":           caption,
                "channelId":      channel_id,
                "schedulingType": "automatic",
                "mode":           "customScheduled",
                "dueAt":          due_at,
                "assets":         {"images": [{"url": image_url}]} if image_url else None,
            }
        }
    else:
        mutation = """
        mutation CreatePost($input: CreatePostInput!) {
          createPost(input: $input) {
            ... on PostActionSuccess {
              post { id text dueAt }
            }
            ... on MutationError { message }
          }
        }
        """
        variables = {
            "input": {
                "text":           caption,
                "channelId":      channel_id,
                "schedulingType": "automatic",
                "mode":           "addToQueue",
                "assets":         {"images": [{"url": image_url}]} if image_url else None,
            }
        }

    # Remove None assets
    if variables["input"]["assets"] is None:
        del variables["input"]["assets"]

    return graphql(mutation, variables, api_key)


def load_csv():
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows   = list(reader)
        fieldnames = list(reader.fieldnames or [])
    return rows, fieldnames


def save_csv(rows, fieldnames):
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--titles", default="", help="||‑separated post titles to send to Buffer")
    args = parser.parse_args()

    api_key    = os.environ.get("BUFFER_API_KEY", "").strip()
    titles_raw = args.titles.strip() or os.environ.get("TITLES", "").strip()

    if not api_key:
        print("ERROR: BUFFER_API_KEY not set.", file=sys.stderr)
        sys.exit(1)
    if not titles_raw:
        print("ERROR: No titles provided.", file=sys.stderr)
        sys.exit(1)

    titles = [t.strip() for t in titles_raw.split("||") if t.strip()]
    print(f"Sending {len(titles)} post(s) to Buffer...")

    # Fetch connected channels once
    print("Fetching Buffer channels...")
    channels = get_channels(api_key)
    print(f"Found {len(channels)} channel(s):")
    for ch in channels:
        print(f"  [{ch.get('service')}] {ch.get('serviceUsername','')} — id: {ch.get('id')}")

    rows, fieldnames = load_csv()
    updated = []
    errors  = []

    for title in titles:
        row = next((r for r in rows if r.get("title","").strip() == title), None)
        if not row:
            errors.append(f"Not found: {title}"); continue

        if row.get("status","").strip().lower() != "post_queue":
            errors.append(f"Not in post_queue: {title}"); continue

        platform   = row.get("platform","").strip()
        caption    = row.get("caption","").strip()
        image_url  = row.get("image_urls","").strip()
        post_date  = row.get("post_date","").strip()

        channel_id = match_channel(channels, platform)
        if not channel_id:
            errors.append(f"No Buffer channel for platform '{platform}': {title}")
            print(f"  ⚠️  No channel matched for '{platform}' — skipping '{title}'")
            continue

        print(f"\n[{title}]")
        print(f"  Platform: {platform} → channel {channel_id}")
        print(f"  Scheduled: {post_date or 'add to queue'}")

        try:
            result = create_buffer_post(title, caption, image_url, post_date, channel_id, api_key)
            success = result.get("data",{}).get("createPost",{})

            if "post" in success:
                buffer_post_id = success["post"]["id"]
                due_at         = success["post"].get("dueAt","")
                print(f"  ✅ Buffer post created: {buffer_post_id} (due: {due_at})")
                row["status"] = "posted"
                updated.append(title)
            else:
                err_msg = success.get("message","unknown error")
                print(f"  ❌ Buffer rejected: {err_msg}")
                errors.append(f"{title}: {err_msg}")
        except Exception as e:
            print(f"  ❌ ERROR: {e}", file=sys.stderr)
            errors.append(f"{title}: {e}")

    if updated:
        save_csv(rows, fieldnames)
        print(f"\n✅ {len(updated)} post(s) sent to Buffer and marked 'posted':")
        for t in updated:
            print(f"  - {t}")

    if errors:
        print(f"\n⚠️  {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        if not updated:
            sys.exit(1)


if __name__ == "__main__":
    main()
