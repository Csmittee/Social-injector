#!/usr/bin/env python3
"""
buffer_poster.py
Sends post_queue posts to Buffer using the correct GraphQL API schema.

Correct flow (per Buffer docs):
  1. account { organizations { id } }  → get org ID
  2. channels(input: { organizationId }) { id, name, service } → get channels
  3. createPost(input: { ... }) for each FB channel

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

CSV_PATH   = "social/posts.csv"
BUFFER_API = "https://api.buffer.com"

# Channels to skip permanently (disconnected/low-priority)
# Remove a name from this list once you've disconnected it in Buffer
SKIP_CHANNELS = {"Outride Thailand"}

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent":   "social-injector/1.0 (github-actions; python-urllib)",
}


# ── GRAPHQL HELPER ────────────────────────────────────────────────────────
def graphql(query: str, variables: dict, api_key: str) -> dict:
    body = {"query": query}
    if variables:
        body["variables"] = variables
    payload = json.dumps(body).encode("utf-8")
    headers = {**HEADERS, "Authorization": f"Bearer {api_key}"}
    req = urllib.request.Request(BUFFER_API, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise RuntimeError(f"Buffer API HTTP {e.code}: {body}")


# ── STEP 1: GET ORGANIZATION ID ───────────────────────────────────────────
def get_organization_id(api_key: str) -> str:
    """Fetches the first organization ID for the authenticated account."""
    query = """
    query GetOrganizations {
      account {
        organizations {
          id
          name
        }
      }
    }
    """
    data   = graphql(query, {}, api_key)
    errors = data.get("errors")
    if errors:
        raise RuntimeError(f"Buffer org query error: {errors}")

    orgs = data.get("data", {}).get("account", {}).get("organizations", [])
    if not orgs:
        raise RuntimeError("No organizations found in Buffer account.")

    org_id = orgs[0]["id"]
    org_name = orgs[0].get("name", "?")
    print(f"  Organization: {org_name} (id: {org_id})")
    return org_id


# ── STEP 2: GET CHANNELS ──────────────────────────────────────────────────
def get_channels(org_id: str, api_key: str) -> list:
    """Fetches all channels for the given organization."""
    query = """
    query GetChannels($input: ChannelsInput!) {
      channels(input: $input) {
        id
        name
        displayName
        service
        avatar
        isQueuePaused
      }
    }
    """
    variables = {"input": {"organizationId": org_id}}
    data   = graphql(query, variables, api_key)
    errors = data.get("errors")
    if errors:
        raise RuntimeError(f"Buffer channels query error: {errors}")

    return data.get("data", {}).get("channels", [])


# ── STEP 3: CREATE A BUFFER POST ──────────────────────────────────────────


def create_buffer_post(caption: str, image_url: str,
                       channel_id: str, api_key: str) -> dict:
    """
    Always uses addToQueue. Image URL must be a direct Cloudinary URL
    without q_auto/f_auto transformations so Buffer/Facebook can process it.
    """
    input_data = {
        "text":           caption,
        "channelId":      channel_id,
        "schedulingType": "automatic",
        "mode":           "addToQueue",
    }
    if image_url:
        input_data["assets"] = {"images": [{"url": image_url}]}

    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post { id text dueAt status }
        }
        ... on MutationError {
          message
        }
      }
    }
    """
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
    print(f"Sending {len(titles)} post(s) to Buffer...")
    print()

    # Step 1: get org ID
    print("Step 1 — Fetching Buffer organization...")
    try:
        org_id = get_organization_id(api_key)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 2: get channels
    print("Step 2 — Fetching connected channels...")
    try:
        channels = get_channels(org_id, api_key)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not channels:
        print("ERROR: No channels found. Connect FB/IG at publish.buffer.com first.", file=sys.stderr)
        sys.exit(1)

    print(f"  Found {len(channels)} channel(s):")
    for ch in channels:
        paused = " [PAUSED]" if ch.get("isQueuePaused") else ""
        print(f"    [{ch.get('service','?'):12}] {ch.get('displayName') or ch.get('name','?')}{paused}  id={ch.get('id')}")

    fb_channels = [
        ch for ch in channels
        if ch.get("service","").lower() == "facebook"
        and (ch.get("displayName") or ch.get("name","")) not in SKIP_CHANNELS
    ]
    ig_channels = [
        ch for ch in channels
        if ch.get("service","").lower() == "instagram"
        and (ch.get("displayName") or ch.get("name","")) not in SKIP_CHANNELS
    ]

    skipped = [
        ch.get("displayName") or ch.get("name","")
        for ch in channels
        if (ch.get("displayName") or ch.get("name","")) in SKIP_CHANNELS
    ]
    if skipped:
        print(f"  Skipping {len(skipped)} channel(s) in SKIP_CHANNELS: {', '.join(skipped)}")
    if not fb_channels:
        print("  WARNING: No active Facebook channels.")
    if not ig_channels:
        print("  NOTE: No Instagram channels — posting to Facebook only.")
    print(f"  Active channels: {len(fb_channels)} FB + {len(ig_channels)} IG")
    print()

    # Step 3: post each title
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
            errors.append(f"Status '{status}' not post_queue: {title}")
            print(f"  SKIP '{title}' — not in post_queue")
            continue

        caption   = row.get("caption","").strip()
        raw_url   = row.get("image_urls","").strip()
        # Strip Cloudinary transformations for clean URL
        image_url = raw_url.replace("/q_auto/f_auto/", "/").replace("/q_auto,f_auto/", "/")

        print(f"{'─'*60}")
        print(f"[{title}]")
        print(f"  Mode: addToQueue (respects your Buffer 3/day schedule)")
        if image_url:
            print(f"  📎 Image URL (attach manually in Buffer):")
            print(f"     {image_url}")
        print(f"  NOTE: Posting text only — attach image manually in Buffer dashboard")

        post_success = False
        post_errors  = []

        for ch in fb_channels:
            label = f"Facebook / {ch.get('displayName') or ch.get('name','?')}"
            try:
                result  = create_buffer_post(caption, "", ch["id"], api_key)  # text only
                outcome = result.get("data", {}).get("createPost", {})
                if "post" in outcome:
                    buf_id = outcome["post"]["id"]
                    sched  = outcome["post"].get("dueAt") or "added to queue"
                    print(f"  ✅ {label} → {buf_id} ({sched})")
                    post_success = True
                else:
                    msg = outcome.get("message", str(result))
                    print(f"  ❌ {label} → {msg}")
                    post_errors.append(f"{label}: {msg}")
            except Exception as e:
                print(f"  ❌ {label} → {e}")
                post_errors.append(f"{label}: {e}")

        for ch in ig_channels:
            label = f"Instagram / {ch.get('displayName') or ch.get('name','?')}"
            try:
                result  = create_buffer_post(caption, "", ch["id"], api_key)  # text only
                outcome = result.get("data", {}).get("createPost", {})
                if "post" in outcome:
                    buf_id = outcome["post"]["id"]
                    sched  = outcome["post"].get("dueAt") or "added to queue"
                    print(f"  ✅ {label} → {buf_id} ({sched})")
                    post_success = True
                else:
                    msg = outcome.get("message", str(result))
                    print(f"  ❌ {label} → {msg}")
                    post_errors.append(f"{label}: {msg}")
            except Exception as e:
                print(f"  ❌ {label} → {e}")
                post_errors.append(f"{label}: {e}")

        if post_success:
            row["status"] = "posted"
            updated.append(title)
            if post_errors:
                print(f"  ⚠️  Posted to some channels but {len(post_errors)} channel(s) failed:")
                for pe in post_errors:
                    print(f"    - {pe}")
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
