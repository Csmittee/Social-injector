import os
import json
import sys
from datetime import datetime, timedelta
from content_factory import append_to_csv

# ========================= CONFIG =========================
# Change this to your preferred model
MODEL = "gpt-4o-mini"                    # or "deepseek-chat", "grok-beta", etc.

# Niche / Business (you can change this)
NICHE = "Yoga for Pregnant Women & General Fitness"  

# =========================================================

def generate_posts_with_ai(custom_prompt, num_posts=5):
    """Call AI with your custom prompt and generate varied posts."""
    
    platforms = "Facebook, Instagram"
    
    full_prompt = f"""
You are a professional social media content creator specializing in {NICHE}.

{ custom_prompt }

Generate exactly {num_posts} **different and varied** posts.

Important rules:
- Make each post unique in tone, structure, length, and message.
- Vary the emojis, calls to action, and hashtags. Do not repeat the same phrase or ending.
- One post can be motivational, one educational, one personal/story-based, one promotional, one question-based, etc.
- For "link" field: Put a real URL only if it's a strong CTA (book class, register, buy, etc.). Otherwise leave it empty "".
- Captions should be natural, warm, and suitable for pregnant women / fitness audience (Thai + English mix is good).

Return ONLY a valid JSON array like this:
[
  {{
    "title": "Short catchy title",
    "post_date": "2026-04-XX HH:MM",
    "platform": "{platforms}",
    "caption": "Full engaging caption with emojis...",
    "image_urls": "",
    "link": "" or "https://...",
    "status": "pending"
  }}
]

Spread the post_date over the next 7 days.
"""

    try:
        print(f"🤖 Sending prompt to AI ({MODEL})...")

        # === Real AI Call Section ===
        # Uncomment and configure the one you use:

        # Example with OpenAI / compatible API:
        from openai import OpenAI
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),   # or GITHUB_TOKEN for GitHub Models
            base_url="https://models.inference.ai.azure.com" if "github" in MODEL.lower() else None
        )

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.85,
            max_tokens=2000
        )

        content = response.choices[0].message.content.strip()
        
        # Clean JSON if needed
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].strip()

        posts = json.loads(content)
        
        if not isinstance(posts, list):
            posts = [posts]

        print(f"✅ AI successfully generated {len(posts)} varied posts.")
        return posts

    except Exception as e:
        print(f"❌ AI generation error: {e}")
        # Fallback: return empty so we don't add bad data
        return []


def main():
    print("🚀 AI Generator Started")

    # Get prompt and count from command line (called from ai-control later)
    custom_prompt = sys.argv[1] if len(sys.argv) > 1 else "Generate motivational yoga and fitness posts for pregnant women and general audience."
    try:
        num_posts = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    except:
        num_posts = 5

    new_posts = generate_posts_with_ai(custom_prompt, num_posts)

    if new_posts:
        append_to_csv(new_posts)
        print(f"🎉 {len(new_posts)} new posts added to social/posts.csv with status 'pending'.")
        print("Go back to Dashboard and click Refresh to see them.")
    else:
        print("⚠️ No posts were generated.")


if __name__ == "__main__":
    main()
