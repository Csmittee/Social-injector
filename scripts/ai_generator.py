import os
import json
from datetime import datetime, timedelta
from content_factory import append_to_csv

# ========================= CONFIG =========================
# Choose your model (GitHub Models, Grok, OpenAI, etc.)
MODEL = "gpt-4o-mini"          # Change to your preferred model
# If using GitHub Models via API, you can set the base URL and token here

# How many posts to generate per run
NUM_POSTS = 5

# Target platforms
PLATFORMS = "Facebook, Instagram"

# Business / Niche (change this to your content theme)
NICHE = "Fitness & Yoga Motivation"   # Example: "Fitness & Yoga Motivation"

# Optional: GitHub token (if needed for other calls)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")   # Set this in your environment or GitHub Secrets
# =========================================================

def generate_posts_with_ai():
    """Generate social media posts using AI (GitHub Models or other LLM)."""
    
    # Simple prompt template - you can make it more advanced later
   prompt = f"""
    You are a professional social media content creator for a {NICHE} business.
    
    Generate {NUM_POSTS} engaging posts.
    
    Rules for the "link" field:
    - If the post is a strong Call-To-Action (CTA) such as "Book now", "Register", "Buy", "Join class", "Limited offer", etc. → put the actual URL (example: https://yourwebsite.com/book).
    - For normal motivational / awareness / inspirational posts → leave link as empty string "".
    
    Return ONLY a valid JSON array. Each object must have exactly these fields:
    - title
    - post_date (YYYY-MM-DD HH:MM, spread over next 7 days)
    - platform
    - caption (long, engaging, with emojis + hashtags, Thai + English ok)
    - image_urls (leave empty "")
    - link (URL or "")
    - status: "pending"
    
    Example of CTA post:
    {{"title": "Yoga Class This Weekend", ..., "link": "https://yourwebsite.com/book-yoga"}}
    
    Example of normal post:
    {{"title": "Morning Motivation", ..., "link": ""}}
    
    Make captions natural and suitable for Facebook & Instagram.
    """

    try:
        # === Replace this section with your actual LLM call ===
        # Example using OpenAI / Grok / GitHub Models client:
        
        # from openai import OpenAI
        # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))   # or GITHUB token
        
        # response = client.chat.completions.create(
        #     model=MODEL,
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=0.8
        # )
        
        # content = response.choices[0].message.content.strip()
        # posts = json.loads(content)
        
        # === For now: Placeholder (replace with real AI call) ===
        print("🤖 Generating posts using AI...")
        
        # Temporary mock data (remove after you connect real AI)
        posts = []
        today = datetime.now()
        
        for i in range(NUM_POSTS):
            post_date = (today + timedelta(days=i+1)).strftime("%Y-%m-%d 09:00")
            posts.append({
                "title": f"Motivation Day {i+1} - {NICHE}",
                "post_date": post_date,
                "platform": PLATFORMS,
                "caption": f"✨ Start your day with positive energy! Day {i+1} of fitness journey. "
                           f"Consistency is the key to success 💪 #Fitness #Yoga #Motivation",
                "image_urls": "",
                "link": "",
                "status": "pending"
            })
        
        # ========================================================
        
        print(f"✅ Generated {len(posts)} posts successfully.")
        return posts

    except Exception as e:
        print(f"❌ Error generating posts: {e}")
        return []


def main():
    print("🚀 Starting Social Injector AI Generator...")
    
    new_posts = generate_posts_with_ai()
    
    if new_posts:
        append_to_csv(new_posts)
        print("🎉 All posts have been saved to social/posts.csv with status 'pending'.")
        print(f"Total posts in CSV now ready for review in the dashboard.")
    else:
        print("⚠️ No posts were generated.")


if __name__ == "__main__":
    main()
