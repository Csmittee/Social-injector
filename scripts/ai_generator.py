#!/usr/bin/env python3
"""
ai_generator.py
Generates social media posts using Claude (Anthropic) and appends to social/posts.csv.

Called by .github/workflows/ai-generator.yml
Requires: ANTHROPIC_API_KEY secret in GitHub repo settings.

CSV columns (matches existing posts.csv):
  title, post_date, platform, caption, image_urls, link, status
"""

import anthropic
import csv
import json
import os
import sys
from datetime import datetime, timedelta

CSV_PATH   = "social/posts.csv"
FIELDNAMES = ["title", "post_date", "platform", "caption", "image_urls", "link", "status"]


def ensure_csv_exists():
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
        print(f"Created new CSV: {CSV_PATH}")


def generate_posts(prompt: str, count: int, platforms: list) -> list:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    today = datetime.utcnow()
    date_examples = [(today + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(7)]

    system = (
        "You are a professional social media content creator. "
        "Return ONLY a valid JSON array — no markdown, no code fences, no explanation."
    )

    user = f"""Generate exactly {count} social media posts.
Target platforms (distribute evenly): {', '.join(platforms)}
Brief: {prompt}

Rules:
- Each post must be unique in tone: mix motivational, educational, story-based, promotional, question-based.
- Vary emojis, hashtags, CTAs — never repeat the same ending.
- Thai + English mix is great for the audience.
- For "link": only include a real URL if there is a strong CTA (book, register, buy). Otherwise use empty string "".
- For "platform": use exactly one value per post, e.g. "Facebook" or "Instagram" or "Line".
- Spread post_date across the next 7 days. Use format: "YYYY-MM-DD HH:MM"
  Available dates: {', '.join(date_examples)}

Return ONLY this JSON array format:
[
  {{
    "title": "Short catchy title (max 60 chars)",
    "post_date": "2026-04-04 09:00",
    "platform": "Facebook",
    "caption": "Full engaging caption with emojis and hashtags...",
    "image_urls": "",
    "link": "",
    "status": "pending"
  }}
]"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    raw = message.content[0].text.strip()

    # Strip accidental markdown fences
    if "```" in raw:
        start = raw.find("[")
        end   = raw.rfind("]") + 1
        raw   = raw[start:end]

    try:
        posts = json.loads(raw)
        if not isinstance(posts, list):
            raise ValueError("Response is not a JSON array")
        return posts
    except (json.JSONDecodeError, ValueError) as e:
        print(f"ERROR parsing Claude response: {e}", file=sys.stderr)
        print(f"Raw:\n{raw}", file=sys.stderr)
        sys.exit(1)


def append_posts(posts: list):
    rows = []
    for post in posts:
        row = {
            "title":      str(post.get("title", "Untitled")).strip()[:120],
            "post_date":  str(post.get("post_date", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))).strip(),
            "platform":   str(post.get("platform", "Facebook")).strip(),
            "caption":    str(post.get("caption", "")).strip(),
            "image_urls": str(post.get("image_urls", "")).strip(),
            "link":       str(post.get("link", "")).strip(),
            "status":     "pending",  # always force pending on new posts
        }
        rows.append(row)

    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, quoting=csv.QUOTE_MINIMAL)
        writer.writerows(rows)

    print(f"Appended {len(rows)} post(s) to {CSV_PATH}")
    for r in rows:
        print(f"  [{r['platform']}] {r['title']}")


def main():
    # Read from env vars (set by the workflow)
    prompt        = os.getenv("PROMPT", "").strip()
    count_str     = os.getenv("COUNT", "5").strip()
    platforms_str = os.getenv("PLATFORMS", "Facebook,Instagram").strip()

    # Also support command-line args for local/codespace testing:
    # python scripts/ai_generator.py "my prompt" 5 "Facebook,Instagram"
    if len(sys.argv) >= 4:
        prompt        = sys.argv[1]
        count_str     = sys.argv[2]
        platforms_str = sys.argv[3]

    if not prompt:
        print("ERROR: No prompt provided. Set PROMPT env var or pass as first argument.", file=sys.stderr)
        sys.exit(1)

    try:
        count = max(1, min(20, int(count_str)))
    except ValueError:
        count = 5

    platforms = [p.strip() for p in platforms_str.split(",") if p.strip()]
    if not platforms:
        platforms = ["Facebook", "Instagram"]

    ensure_csv_exists()

    print(f"Generating {count} post(s) for: {platforms}")
    print(f"Prompt: {prompt}")

    posts = generate_posts(prompt, count, platforms)
    print(f"Claude returned {len(posts)} post(s)")

    append_posts(posts)


if __name__ == "__main__":
    main()
