#!/usr/bin/env python3
"""
image_generator.py
For each approved post title passed in, generates an image via Replicate (FLUX schnell),
uploads it to Cloudinary, writes the URL back to social/posts.csv,
and sets status -> "post_queue".

Called by .github/workflows/image-generator.yml
Requires secrets: REPLICATE_API_TOKEN, CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET

Usage:
  python scripts/image_generator.py --titles "Title A||Title B||Title C"
  or via env: TITLES="Title A||Title B"
"""

import argparse
import csv
import hashlib
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import base64
import codecs

CSV_PATH = "social/posts.csv"
FIELDNAMES = ["title", "post_date", "platform", "caption", "image_urls", "link", "status"]

# Force UTF-8 output (important for Thai text in logs)
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")


# ── REPLICATE ──────────────────────────────────────────────────────────────
def generate_image_replicate(prompt: str) -> str:
    """
    Calls Replicate synchronous predictions API for FLUX schnell.
    Returns the image URL (temporary Replicate CDN URL).
    """
    api_token = os.environ.get("REPLICATE_API_TOKEN", "").strip()
    if not api_token:
        raise RuntimeError("REPLICATE_API_TOKEN not set")

    # Use FLUX schnell — fast, free tier, great for social media visuals
    model_version = "black-forest-labs/flux-schnell"

    payload = json.dumps({
        "version": model_version,
        "input": {
            "prompt": prompt,
            "num_outputs": 1,
            "aspect_ratio": "1:1",         # square for Instagram/Facebook
            "output_format": "webp",
            "output_quality": 90,
            "num_inference_steps": 4,       # schnell default
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.replicate.com/v1/predictions",
        data=payload,
        headers={
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json",
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        prediction = json.loads(resp.read().decode("utf-8"))

    prediction_id = prediction["id"]
    poll_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"

    print(f"  Replicate prediction started: {prediction_id}")

    # Poll until complete (max 120s)
    for attempt in range(24):
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
            return output[0]  # first image URL

        if status == "failed":
            err = status_data.get("error", "unknown error")
            raise RuntimeError(f"Replicate prediction failed: {err}")

    raise RuntimeError("Replicate prediction timed out after 120s")


# ── CLOUDINARY ─────────────────────────────────────────────────────────────
def upload_to_cloudinary(image_url: str, public_id: str) -> str:
    """
    Uploads an image (by URL) to Cloudinary.
    Returns the permanent Cloudinary HTTPS URL.
    """
    cloud_name  = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
    api_key     = os.environ.get("CLOUDINARY_API_KEY", "").strip()
    api_secret  = os.environ.get("CLOUDINARY_API_SECRET", "").strip()

    if not all([cloud_name, api_key, api_secret]):
        raise RuntimeError("Cloudinary credentials not set (CLOUDINARY_CLOUD_NAME / API_KEY / API_SECRET)")

    # Build signed upload parameters
    timestamp = str(int(time.time()))
    folder    = "social_injector"

    # Signature: alphabetically sorted params (excluding api_key, resource_type, file)
    sign_params = {
        "folder":    folder,
        "public_id": public_id,
        "timestamp": timestamp,
    }
    sign_string = "&".join(f"{k}={v}" for k, v in sorted(sign_params.items())) + api_secret
    signature   = hashlib.sha1(sign_string.encode("utf-8")).hexdigest()

    post_data = {
        "file":        image_url,
        "api_key":     api_key,
        "timestamp":   timestamp,
        "signature":   signature,
        "folder":      folder,
        "public_id":   public_id,
    }

    encoded = urllib.parse.urlencode(post_data).encode("utf-8")
    upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"

    req = urllib.request.Request(upload_url, data=encoded, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise RuntimeError(f"Cloudinary upload failed {e.code}: {body}")

    secure_url = result.get("secure_url", "")
    if not secure_url:
        raise RuntimeError(f"Cloudinary returned no URL: {result}")

    # Append auto quality+format transformations for CDN efficiency
    # e.g. https://res.cloudinary.com/xxx/image/upload/q_auto/f_auto/v.../social_injector/xxx.webp
    secure_url = secure_url.replace("/upload/", "/upload/q_auto/f_auto/")
    return secure_url


# ── CSV HELPERS ────────────────────────────────────────────────────────────
def load_csv():
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found", file=sys.stderr)
        sys.exit(1)
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows   = list(reader)
        fieldnames = reader.fieldnames or FIELDNAMES
    return rows, fieldnames


def save_csv(rows, fieldnames):
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)


# ── PROMPT BUILDER ─────────────────────────────────────────────────────────
def build_image_prompt(post: dict) -> str:
    """
    Converts a social post's caption into a clean visual image prompt.
    Strips Thai text, hashtags, emoji — keeps the visual concept.
    """
    caption = post.get("caption", "")
    title   = post.get("title", "")
    platform= post.get("platform", "social media")

    # Use title as the primary concept (usually EN or bilingual)
    # Build a photography/graphic prompt
    prompt = (
        f"Professional social media marketing image for a Thai business. "
        f"Concept: {title}. "
        f"Style: clean, modern, vibrant, suitable for {platform}. "
        f"High quality commercial photography, no text overlays, no logos. "
        f"Bright natural lighting, appealing composition."
    )
    return prompt


# ── MAIN ────────────────────────────────────────────────────────────────────
def main():
    # Accept titles via --titles arg or TITLES env var
    parser = argparse.ArgumentParser()
    parser.add_argument("--titles", default="", help="||‑separated list of post titles")
    args   = parser.parse_args()

    titles_raw = args.titles.strip() or os.environ.get("TITLES", "").strip()
    if not titles_raw:
        print("ERROR: No titles provided. Use --titles 'A||B' or TITLES env var.", file=sys.stderr)
        sys.exit(1)

    titles = [t.strip() for t in titles_raw.split("||") if t.strip()]
    print(f"Processing {len(titles)} post(s):")
    for t in titles:
        print(f"  - {t}")
    print()

    rows, fieldnames = load_csv()

    # Ensure image_urls column exists
    if "image_urls" not in fieldnames:
        fieldnames = list(fieldnames) + ["image_urls"]
        for row in rows:
            row.setdefault("image_urls", "")

    updated = []
    errors  = []

    for title in titles:
        # Find row
        row = next((r for r in rows if r.get("title", "").strip() == title), None)
        if not row:
            print(f"  WARNING: '{title}' not found in CSV — skipping")
            errors.append(f"Not found: {title}")
            continue

        current_status = row.get("status", "").strip().lower()
        if current_status != "approved":
            print(f"  WARNING: '{title}' has status '{current_status}' (not approved) — skipping")
            errors.append(f"Wrong status ({current_status}): {title}")
            continue

        print(f"\n[{title}]")

        try:
            # 1. Build prompt
            img_prompt = build_image_prompt(row)
            print(f"  Prompt: {img_prompt[:120]}...")

            # 2. Generate via Replicate
            print("  Generating image via Replicate FLUX...")
            replicate_url = generate_image_replicate(img_prompt)
            print(f"  Replicate URL: {replicate_url[:80]}...")

            # 3. Upload to Cloudinary
            # public_id: safe filename from title
            safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)[:60]
            public_id = f"{safe_id}_{int(time.time())}"
            print(f"  Uploading to Cloudinary as '{public_id}'...")
            cloudinary_url = upload_to_cloudinary(replicate_url, public_id)
            print(f"  ✅ Cloudinary URL: {cloudinary_url}")

            # 4. Update row
            row["image_urls"] = cloudinary_url
            row["status"]     = "post_queue"
            updated.append(title)

        except Exception as e:
            print(f"  ❌ ERROR: {e}", file=sys.stderr)
            errors.append(f"Error ({title}): {e}")
            # Leave the post as "approved" so you can retry

    # Save CSV
    if updated:
        save_csv(rows, fieldnames)
        print(f"\n✅ CSV updated: {len(updated)} post(s) moved to post_queue")
        for t in updated:
            print(f"  - {t}")
    else:
        print("\nNo posts were updated.")

    if errors:
        print(f"\n⚠️  {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        if not updated:
            sys.exit(1)


if __name__ == "__main__":
    main()
