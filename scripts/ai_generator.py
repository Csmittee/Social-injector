#!/usr/bin/env python3
"""
ai_generator.py
Generates social media posts using Claude (Anthropic) and appends to social/posts.csv.
Reads business config from scripts/businesses.json to inject correct context.

Called by .github/workflows/ai-generator.yml
Requires: ANTHROPIC_API_KEY secret in GitHub repo settings.

CSV columns: title, post_date, platform, caption, image_urls, link, status
"""

import anthropic
import csv
import json
import os
import re
import sys
from datetime import datetime, timedelta

CSV_PATH        = "social/posts.csv"
BUSINESSES_PATH = "scripts/businesses.json"
FIELDNAMES      = ["title", "post_date", "platform", "caption", "image_urls", "link", "status"]


def ensure_csv_exists():
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
        print(f"Created new CSV: {CSV_PATH}")


def load_business(business_id: str) -> dict:
    if not os.path.exists(BUSINESSES_PATH):
        print(f"WARNING: {BUSINESSES_PATH} not found — running without business context.")
        return None
    with open(BUSINESSES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for biz in data.get("businesses", []):
        if biz["id"] == business_id:
            return biz
    print(f"WARNING: Business '{business_id}' not found in businesses.json")
    return None


def build_business_context(biz: dict) -> str:
    if not biz:
        return ""
    lines = [
        f"Business name: {biz['name']}",
        f"Niche: {biz['niche']}",
        f"Language style: {biz['language']}",
        f"Default hashtags to include: {biz['hashtags']}",
        f"Main URL for CTAs: {biz['booking_url']}",
    ]
    social = biz.get("social", {})
    if social.get("facebook_page"):
        lines.append(f"Facebook page: {social['facebook_page']}")
    if social.get("instagram"):
        lines.append(f"Instagram: {social['instagram']} ({social.get('instagram_handle', '')})")
    return "\n".join(lines)


def clean_json_string(raw: str) -> str:
    """
    Robustly extract and clean JSON from Claude's response.
    Handles:
      - Markdown code fences (```json ... ```)
      - Broken/replacement unicode chars (the ??? boxes)
      - Literal newlines inside JSON string values
    """
    # Strip markdown fences
    raw = raw.strip()
    if "```" in raw:
        raw = re.sub(r"```(?:json)?", "", raw).strip()

    # Find the JSON array boundaries
    start = raw.find("[")
    end   = raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return raw
    raw = raw[start:end+1]

    # Remove unicode replacement characters (U+FFFD and similar broken sequences)
    raw = raw.replace("\ufffd", "")
    # Remove other common broken unicode escape sequences that appear as literal \u + garbled chars
    raw = re.sub(r'\\u[0-9a-fA-F]{0,3}[^0-9a-fA-F"\\,\]\}]', '', raw)

    # Fix literal (unescaped) newlines INSIDE JSON string values.
    # Strategy: walk char by char, track if we're inside a string,
    # and replace bare \n/\r inside strings with \\n
    result    = []
    in_string = False
    i         = 0
    while i < len(raw):
        ch = raw[i]
        if ch == '\\' and in_string:
            # Escaped sequence — pass both chars through unchanged
            result.append(ch)
            i += 1
            if i < len(raw):
                result.append(raw[i])
            i += 1
            continue
        if ch == '"':
            in_string = not in_string
            result.append(ch)
            i += 1
            continue
        if in_string and ch == '\n':
            result.append('\\n')
            i += 1
            continue
        if in_string and ch == '\r':
            i += 1
            continue
        result.append(ch)
        i += 1

    return "".join(result)


def generate_posts(prompt: str, count: int, platforms: list, biz: dict) -> list:
    client = anthropic.Anthropic()

    today         = datetime.utcnow()
    date_examples = [(today + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(7)]
    biz_context   = build_business_context(biz)

    system = (
        "You are a professional social media content creator for Thai businesses. "
        "Return ONLY a valid JSON array — no markdown, no code fences, no explanation. "
        "CRITICAL: All string values must use \\n for line breaks (escaped), never raw newlines. "
        "Do not include any broken unicode or replacement characters. "
        "Every double-quote inside a string value must be escaped as \\\"."
    )

    biz_block = f"--- Business Context ---\n{biz_context}\n---" if biz_context else ""

    user = f"""Generate exactly {count} social media posts.
Target platforms (distribute evenly): {', '.join(platforms)}
User brief: {prompt}

{biz_block}

Rules:
- Each post must be unique in tone: mix motivational, educational, story-based, promotional, question-based.
- Vary emojis, hashtags, CTAs — never repeat the same ending.
- Use the business language style and include the default hashtags naturally.
- For "link": use the business main URL only when there is a strong CTA. Otherwise use "".
- For "platform": use exactly one value per post matching the target platforms.
- Spread post_date across the next 7 days. Format: "YYYY-MM-DD HH:MM"
  Available dates: {', '.join(date_examples)}
- Title should be short and catchy (max 60 chars). No double-quotes in titles.
- In caption, use \\n for line breaks — never raw newlines.

Return ONLY this JSON array (no text before or after):
[
  {{
    "title": "Short catchy title",
    "post_date": "2026-04-04 09:00",
    "platform": "Facebook",
    "caption": "Line 1\\nLine 2\\nLine 3",
    "image_urls": "",
    "link": "",
    "status": "pending"
  }}
]"""

    MAX_RETRIES = 3
    last_error  = None

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"  Claude attempt {attempt}/{MAX_RETRIES}...")
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )

        raw     = message.content[0].text.strip()
        cleaned = clean_json_string(raw)

        try:
            posts = json.loads(cleaned)
            if not isinstance(posts, list):
                raise ValueError("Response is not a JSON array")
            if len(posts) == 0:
                raise ValueError("Empty posts array returned")
            print(f"  ✅ Parsed {len(posts)} post(s) successfully.")
            return posts
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  ⚠️  Parse attempt {attempt} failed: {e}", file=sys.stderr)
            if attempt < MAX_RETRIES:
                print("  Retrying with stricter instructions...", file=sys.stderr)
                # On retry, add the failed output as context to help Claude self-correct
                user += f"\n\nIMPORTANT: Your previous response caused a JSON parse error: {e}. Please fix it and return only clean valid JSON."

    print(f"ERROR: All {MAX_RETRIES} parse attempts failed. Last error: {last_error}", file=sys.stderr)
    print(f"Last raw response:\n{raw}", file=sys.stderr)
    sys.exit(1)


def append_posts(posts: list):
    rows = []
    for post in posts:
        # Restore \\n back to real newlines for CSV storage (display correctly in dashboard)
        caption = str(post.get("caption", "")).strip()
        caption = caption.replace("\\n", "\n")

        row = {
            "title":      str(post.get("title", "Untitled")).strip()[:120],
            "post_date":  str(post.get("post_date", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))).strip(),
            "platform":   str(post.get("platform", "Facebook")).strip(),
            "caption":    caption,
            "image_urls": str(post.get("image_urls", "")).strip(),
            "link":       str(post.get("link", "")).strip(),
            "status":     "pending",
        }
        rows.append(row)

    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, quoting=csv.QUOTE_ALL)
        writer.writerows(rows)

    print(f"Appended {len(rows)} post(s) to {CSV_PATH}")
    for r in rows:
        print(f"  [{r['platform']}] {r['title']}")


def main():
    prompt        = os.getenv("PROMPT", "").strip()
    count_str     = os.getenv("COUNT", "5").strip()
    platforms_str = os.getenv("PLATFORMS", "Facebook,Instagram").strip()
    business_id   = os.getenv("BUSINESS_ID", "").strip()

    if len(sys.argv) >= 2: prompt        = sys.argv[1]
    if len(sys.argv) >= 3: count_str     = sys.argv[2]
    if len(sys.argv) >= 4: platforms_str = sys.argv[3]
    if len(sys.argv) >= 5: business_id   = sys.argv[4]

    if not prompt:
        print("ERROR: No prompt provided.", file=sys.stderr)
        sys.exit(1)

    try:
        count = max(1, min(20, int(count_str)))
    except ValueError:
        count = 5

    platforms = [p.strip() for p in platforms_str.split(",") if p.strip()]
    if not platforms:
        platforms = ["Facebook", "Instagram"]

    biz = load_business(business_id) if business_id else None
    if biz:
        print(f"Business context loaded: {biz['name']}")
    else:
        print("No business selected — generating without business context")

    ensure_csv_exists()
    print(f"Generating {count} post(s) for: {platforms}")
    print(f"Prompt: {prompt}")

    posts = generate_posts(prompt, count, platforms, biz)
    print(f"Claude returned {len(posts)} post(s)")
    append_posts(posts)


if __name__ == "__main__":
    main()
