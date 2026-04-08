#!/usr/bin/env python3
"""
image_generator.py
Pipeline per approved post:
  1. Claude (Haiku) reads caption + title → writes a clean English FLUX image prompt
  2. Replicate FLUX schnell generates the image
  3. Cloudinary stores it permanently
  4. CSV updated: image_urls = Cloudinary URL, status = post_queue

Called by .github/workflows/image-generator.yml
Secrets required: ANTHROPIC_API_KEY, REPLICATE_API_TOKEN,
                  CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
"""

import argparse
import csv
import codecs
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CSV_PATH   = "social/posts.csv"
FIELDNAMES = ["title", "post_date", "platform", "caption", "image_urls", "link", "status"]

# Force UTF-8 output so Thai text shows correctly in GitHub Actions logs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")


# ── STEP 1: CLAUDE PROMPT BUILDER ─────────────────────────────────────────
def build_image_prompt_via_claude(post: dict) -> str:
    """
    Sends the post title + caption to Claude Haiku.
    Claude returns a single clean English image prompt for FLUX.
    Thai text, emoji, hashtags, and CTAs are stripped — only the visual concept remains.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    title    = post.get("title", "")
    caption  = post.get("caption", "")
    platform = post.get("platform", "social media")

    system = (
        "You are an expert at writing image generation prompts for FLUX (a photorealistic AI image model). "
        "Your output must be a SINGLE paragraph of plain English — no bullet points, no Thai text, "
        "no emoji, no hashtags, no quotes, no explanation. "
        "Describe the ideal photograph or graphic for the post: subject, setting, mood, lighting, style. "
        "Make it specific and visual. Max 120 words."
    )

    user = (
        f"Create a FLUX image generation prompt for this social media post.\n\n"
        f"Platform: {platform}\n"
        f"Post title: {title}\n"
        f"Caption:\n{caption}\n\n"
        f"The image should visually represent the post concept and feel appropriate for {platform} marketing. "
        f"Professional commercial photography style. No text, no logos, no watermarks in the image."
    )

    payload = json.dumps({
        "model":      "claude-haiku-4-5-20251001",
        "max_tokens": 200,
        "system":     system,
        "messages":   [{"role": "user", "content": user}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
            "content-type":      "application/json",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise RuntimeError(f"Claude API error {e.code}: {body}")

    prompt = data["content"][0]["text"].strip()
    # Strip any accidental quotes or newlines
    prompt = prompt.replace('"', '').replace('\n', ' ').strip()
    return prompt


# ── STEP 2: REPLICATE IMAGE GENERATION ────────────────────────────────────
def generate_image_replicate(prompt: str) -> str:
    """
    Calls Replicate FLUX schnell with the Claude-built prompt.
    Returns the temporary Replicate CDN image URL.
    """
    api_token = os.environ.get("REPLICATE_API_TOKEN", "").strip()
    if not api_token:
        raise RuntimeError("REPLICATE_API_TOKEN not set")

    payload = json.dumps({
        "version": "black-forest-labs/flux-schnell",
        "input": {
            "prompt":              prompt,
            "num_outputs":         1,
            "aspect_ratio":        "1:1",
            "output_format":       "webp",
            "output_quality":      90,
            "num_inference_steps": 4,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.replicate.com/v1/predictions",
        data=payload,
        headers={
            "Authorization": f"Token {api_token}",
            "Content-Type":  "application/json",
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        prediction = json.loads(resp.read().decode("utf-8"))

    prediction_id = prediction["id"]
    poll_url      = f"https://api.replicate.com/v1/predictions/{prediction_id}"
    print(f"  Replicate prediction ID: {prediction_id}")

    for attempt in range(24):   # max ~120s
        time.sleep(5)
        req2 = urllib.request.Request(
            poll_url,
            headers={"Authorization": f"Token {api_token}"},
            method="GET"
        )
        with urllib.request.urlopen(req2, timeout=15) as resp2:
            status_data = json.loads(resp2.read().decode("utf-8"))

        status = status_data.get("status", "")
        print(f"  Poll {attempt+1}: {status}")

        if status == "succeeded":
            output = status_data.get("output", [])
            if not output:
                raise RuntimeError("Replicate returned no output URLs")
            return output[0]

        if status == "failed":
            raise RuntimeError(f"Replicate failed: {status_data.get('error','unknown')}")

    raise RuntimeError("Replicate timed out after 120s")


# ── STEP 3: CLOUDINARY UPLOAD ──────────────────────────────────────────────
def upload_to_cloudinary(image_url: str, public_id: str) -> str:
    """
    Uploads image (by URL) to Cloudinary social_injector/ folder.
    Returns permanent CDN URL with auto quality+format.
    """
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
    api_key    = os.environ.get("CLOUDINARY_API_KEY", "").strip()
    api_secret = os.environ.get("CLOUDINARY_API_SECRET", "").strip()

    if not all([cloud_name, api_key, api_secret]):
        raise RuntimeError("Cloudinary credentials incomplete")

    timestamp   = str(int(time.time()))
    folder      = "social_injector"
    sign_params = {"folder": folder, "public_id": public_id, "timestamp": timestamp}
    sign_string = "&".join(f"{k}={v}" for k, v in sorted(sign_params.items())) + api_secret
    signature   = hashlib.sha1(sign_string.encode("utf-8")).hexdigest()

    post_data = {
        "file": image_url, "api_key": api_key, "timestamp": timestamp,
        "signature": signature, "folder": folder, "public_id": public_id,
    }
    encoded    = urllib.parse.urlencode(post_data).encode("utf-8")
    upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"

    req = urllib.request.Request(upload_url, data=encoded, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Cloudinary upload failed {e.code}: {e.read().decode()}")

    url = result.get("secure_url", "")
    if not url:
        raise RuntimeError(f"Cloudinary returned no URL: {result}")

    return url.replace("/upload/", "/upload/q_auto/f_auto/")


# ── CSV HELPERS ────────────────────────────────────────────────────────────
def load_csv():
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found", file=sys.stderr)
        sys.exit(1)
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader     = csv.DictReader(f)
        rows       = list(reader)
        fieldnames = reader.fieldnames or FIELDNAMES
    return rows, list(fieldnames)


def save_csv(rows, fieldnames):
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)


# ── MAIN ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--titles", default="", help="||‑separated post titles")
    args = parser.parse_args()

    titles_raw = args.titles.strip() or os.environ.get("TITLES", "").strip()
    if not titles_raw:
        print("ERROR: No titles provided.", file=sys.stderr)
        sys.exit(1)

    titles = [t.strip() for t in titles_raw.split("||") if t.strip()]
    print(f"Processing {len(titles)} post(s):")
    for t in titles:
        print(f"  - {t}")
    print()

    rows, fieldnames = load_csv()

    if "image_urls" not in fieldnames:
        fieldnames.append("image_urls")
        for row in rows:
            row.setdefault("image_urls", "")

    updated = []
    errors  = []

    for title in titles:
        row = next((r for r in rows if r.get("title", "").strip() == title), None)
        if not row:
            print(f"WARNING: '{title}' not found in CSV — skipping")
            errors.append(f"Not found: {title}")
            continue

        if row.get("status", "").strip().lower() != "approved":
            print(f"WARNING: '{title}' is not approved — skipping")
            errors.append(f"Not approved: {title}")
            continue

        print(f"\n{'─'*60}")
        print(f"[{title}]")

        try:
            # Step 1 — Claude builds the image prompt
            print("  Step 1/3 → Claude building image prompt...")
            img_prompt = build_image_prompt_via_claude(row)
            print(f"  Image prompt: {img_prompt}")

            # Step 2 — Replicate generates the image
            print("  Step 2/3 → Replicate FLUX generating image...")
            replicate_url = generate_image_replicate(img_prompt)
            print(f"  Replicate URL: {replicate_url[:80]}...")

            # Step 3 — Upload to Cloudinary
            safe_id   = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:60]
            public_id = f"{safe_id}_{int(time.time())}"
            print(f"  Step 3/3 → Uploading to Cloudinary ({public_id})...")
            cdn_url = upload_to_cloudinary(replicate_url, public_id)
            print(f"  ✅ CDN URL: {cdn_url}")

            row["image_urls"] = cdn_url
            row["status"]     = "post_queue"
            updated.append(title)

        except Exception as e:
            print(f"  ❌ ERROR: {e}", file=sys.stderr)
            errors.append(f"{title}: {e}")
            # Post stays as 'approved' so you can retry

    print(f"\n{'═'*60}")
    if updated:
        save_csv(rows, fieldnames)
        print(f"✅ {len(updated)} post(s) moved to post_queue:")
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
