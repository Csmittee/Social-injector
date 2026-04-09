#!/usr/bin/env python3
"""
buffer_poster.py
Sends post_queue posts to Buffer, posting to Facebook AND Instagram simultaneously.
Uses Buffer's GraphQL API with Bearer token auth.

Pipeline per post:
  1. Read post from CSV (must be status=post_queue)
  2. Find matching Buffer channels for Facebook + Instagram
  3. Create one Buffer post per channel (FB and IG linked, so both get same content+image)
  4. Mark CSV status → posted

Called by .github/workflows/buffer-poster.yml
Secret required: BUFFER_API_KEY  (from publish.buffer.com → Settings → API)
"""

import argparse
import codecs
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta

CSV_PATH   = "social/posts.csv"
BUFFER_API = "https://api.buffer.com"

# Thailand is UTC+7 — adjust if your post_date times are in a different zone
LOCAL_TZ_OFFSET = timedelta(hours=7)

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")


# ── BUFFER GRAPHQL HELPER ─────────────────────────────────────────────────
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
        body = e.read().decode("utf-8")
        raise RuntimeError(f"Buffer API HTTP {e.code}: {body}")


# ── FETCH ALL CONNECTED CHANNELS ──────────────────────────────────────────
def get_channels(api_key: str) -> list:
    query = """
    query GetChannels {
      channels {
        id
        service
        name
        serviceUsername
      }
    }
    """
    data = graphql(query, {}, api_key)
    errors = data.get("errors")
    if errors:
        raise RuntimeError(f"Buffer channels error: {errors}")
    channels = data.get("data", {}).get("channels", [])
    return channels


# ── MATCH CHANNELS FOR A POST ─────────────────────────────────────────────
def find_channels_for_post(channels: list, csv_platform: str) -> list:
    """
    Given the platform field from CSV (e.g. "Facebook", "Instagram", "Facebook,Instagram"),
    returns ALL matching Buffer channel IDs.
    Since FB and IG are always linked, we always send to BOTH facebook + instagram.
    """
    # Always send to both regardless of what's in the CSV platform field
    target_services = {"facebook", "instagram"}

    matched = []
    for ch in channels:
        svc = ch.get("service", "").lower()
        if svc in target_services:
            matched.append(ch)
    return matched


# ── CONVERT POST DATE TO UTC ISO ──────────────────────────────────────────
def to_utc_iso(post_date: str) -> str | None:
    """
    Converts "YYYY-MM-DD HH:MM" (local Thai time UTC+7) to UTC ISO 8601.
    Returns None if parsing fails (Buffer will add to queue instead).
    """
    if not post_date or not post_date.strip():
        return None
    try:
        local_dt = datetime.strptime(post_date.strip(), "%Y-%m-%d %H:%M")
        utc_dt   = local_dt - LOCAL_TZ_OFFSET
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except ValueError:
        return None


# ── CREATE ONE BUFFER POST ────────────────────────────────────────────────
def create_buffer_post(caption: str, image_url: str, post_date: str,
                       channel_id: str, api_key: str) -> dict:
    due_at  = to_utc_iso(post_date)
    mode    = "customScheduled" if due_at else "addToQueue"

    # Build assets block only if we have an image
    assets_block = ""
    assets_var   = {}
    if image_url:
        assets_block = "assets: $assets"
        assets_var   = {"images": [{"url": image_url}]}

    mutation = f"""
    mutation CreatePost($input: CreatePostInput!) {{
      createPost(input: $input) {{
        ... on PostActionSuccess {{
          post {{
            id
            text
            dueAt
            status
          }}
        }}
        ... on MutationError {{
          message
        }}
      }}
    }}
    """

    input_data = {
        "text":           caption,
        "channelId":      channel_id,
        "schedulingType": "automatic",
        "mode":           mode,
    }
    if due_at:
        input_data["dueAt"] = due_at
    if image_url:
        input_data["assets"] = {"images": [{"url": image_url}]}

    return graphql(mutation, {"input": input_data}, api_key)


# ── CSV HELPERS ────────────────────────────────────────────────────────────
def load_csv():
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found", file=sys.stderr)
        sys.exit(1)
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader     = csv.DictReader(f)
        rows       = list(reader)
        fieldnames = list(reader.fieldnames or [])
    return rows, fieldnames


def save_csv(rows, fieldnames):
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)


# ── MAIN ──────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--titles", default="", help="||‑separated post titles")
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
    print(f"Sending {len(titles)} post(s) to Buffer (FB + IG simultaneously)...")
    print()

    # Fetch all connected Buffer channels once
    print("Fetching Buffer channels...")
    try:
        channels = get_channels(api_key)
    except Exception as e:
        print(f"ERROR fetching channels: {e}", file=sys.stderr)
        sys.exit(1)

    if not channels:
        print("ERROR: No channels connected in Buffer. Connect FB/IG at publish.buffer.com first.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(channels)} connected channel(s):")
    for ch in channels:
        print(f"  [{ch.get('service','?'):12}] {ch.get('serviceUsername','?')}  id={ch.get('id')}")
    print()

    # Separate FB and IG channels
    fb_channels = [ch for ch in channels if ch.get("service","").lower() == "facebook"]
    ig_channels = [ch for ch in channels if ch.get("service","").lower() == "instagram"]

    if not fb_channels:
        print("WARNING: No Facebook channels found in Buffer.")
    if not ig_channels:
        print("WARNING: No Instagram channels found in Buffer.")

    rows, fieldnames = load_csv()
    updated = []
    errors  = []

    for title in titles:
        row = next((r for r in rows if r.get("title","").strip() == title), None)
        if not row:
            errors.append(f"Not found in CSV: {title}")
            continue

        status = row.get("status","").strip().lower()
        if status != "post_queue":
            errors.append(f"Status is '{status}' not post_queue: {title}")
            print(f"  SKIP '{title}' — status is '{status}', expected post_queue")
            continue

        caption   = row.get("caption","").strip()
        image_url = row.get("image_urls","").strip()
        post_date = row.get("post_date","").strip()
        due_at    = to_utc_iso(post_date)

        print(f"{'─'*60}")
        print(f"[{title}]")
        print(f"  Schedule: {post_date} → UTC: {due_at or 'add to queue'}")
        print(f"  Image:    {image_url[:60] + '...' if len(image_url) > 60 else image_url or '(none)'}")

        post_success = False
        post_errors  = []

        # Post to every connected FB channel
        for ch in fb_channels:
            ch_label = f"Facebook/{ch.get('serviceUsername','?')}"
            try:
                result  = create_buffer_post(caption, image_url, post_date, ch["id"], api_key)
                outcome = result.get("data", {}).get("createPost", {})
                if "post" in outcome:
                    buf_id = outcome["post"]["id"]
                    sched  = outcome["post"].get("dueAt", "queued")
                    print(f"  ✅ {ch_label} → Buffer ID {buf_id} (due: {sched})")
                    post_success = True
                else:
                    msg = outcome.get("message", str(result))
                    print(f"  ❌ {ch_label} → {msg}")
                    post_errors.append(f"{ch_label}: {msg}")
            except Exception as e:
                print(f"  ❌ {ch_label} → {e}")
                post_errors.append(f"{ch_label}: {e}")

        # Post to every connected IG channel
        for ch in ig_channels:
            ch_label = f"Instagram/{ch.get('serviceUsername','?')}"
            try:
                result  = create_buffer_post(caption, image_url, post_date, ch["id"], api_key)
                outcome = result.get("data", {}).get("createPost", {})
                if "post" in outcome:
                    buf_id = outcome["post"]["id"]
                    sched  = outcome["post"].get("dueAt", "queued")
                    print(f"  ✅ {ch_label} → Buffer ID {buf_id} (due: {sched})")
                    post_success = True
                else:
                    msg = outcome.get("message", str(result))
                    print(f"  ❌ {ch_label} → {msg}")
                    post_errors.append(f"{ch_label}: {msg}")
            except Exception as e:
                print(f"  ❌ {ch_label} → {e}")
                post_errors.append(f"{ch_label}: {e}")

        if post_success:
            row["status"] = "posted"
            updated.append(title)
        else:
            errors.extend(post_errors)

    print(f"\n{'═'*60}")
    if updated:
        save_csv(rows, fieldnames)
        print(f"✅ {len(updated)} post(s) sent to Buffer and marked 'posted':")
        for t in updated:
            print(f"  - {t}")
    else:
        print("No posts were updated.")

    if errors:
        print(f"\n⚠️  {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        if not updated:
            sys.exit(1)


if __name__ == "__main__":
    main()
