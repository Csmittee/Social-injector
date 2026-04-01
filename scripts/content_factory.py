#!/usr/bin/env python3
"""
Content Factory - With Real AI (GitHub Models)
"""

import os
import csv
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

def generate_ai_content(theme, count):
    """Call GitHub Models API for real AI content"""
    
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("⚠️ No GitHub token, using fallback")
        return None
    
    prompt = f"""Generate {count} social media posts for a fitness brand about "{theme}".

For each post, provide:
- title: catchy headline (max 8 words)
- caption: engaging post (100-150 words) with emojis and hashtags
- link_suggestion: what type of link would fit (e.g., "shop", "blog", "free guide")

Return as JSON array with fields: title, caption, link_suggestion

Example:
[{{"title": "Start Your Journey", "caption": "Ready to transform... #fitness", "link_suggestion": "free-guide"}}]"""

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Clean and parse JSON
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            return json.loads(content)
        else:
            print(f"⚠️ AI API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"⚠️ AI error: {e}")
        return None

def main():
    print("\n" + "="*50)
    print("🤖 CONTENT FACTORY (with AI)")
    print("="*50)
    
    theme = os.getenv('THEME', 'fitness motivation')
    count = int(os.getenv('COUNT', '5'))
    
    print(f"\n📝 Generating {count} AI posts")
    print(f"   Theme: {theme}")
    print()
    
    # Get AI-generated content
    ai_posts = generate_ai_content(theme, count)
    
    if not ai_posts:
        print("⚠️ AI failed, using fallback")
        ai_posts = []
        for i in range(count):
            ai_posts.append({
                'title': f"{theme.title()} - Post {i+1}",
                'caption': f"✨ {theme.title()} inspiration! Stay consistent and trust the process. #FitnessJourney",
                'link_suggestion': ''
            })
    
    # Create posts with dates
    new_posts = []
    start_date = datetime.now().replace(hour=9, minute=0)
    
    for i, ai_post in enumerate(ai_posts[:count]):
        post_time = start_date + timedelta(hours=i*3, days=i//3)
        
        post = {
            'title': ai_post.get('title', f"{theme.title()} - Post {i+1}"),
            'post_date': post_time.strftime('%Y-%m-%d %H:%M'),
            'platform': 'FB,IG',
            'caption': ai_post.get('caption', f"✨ {theme.title()} inspiration!"),
            'image_urls': '',
            'link': '',  # You can add logic here based on link_suggestion
            'status': 'pending'
        }
        
        new_posts.append(post)
        print(f"✅ AI Post {i+1}: {post['title']}")
    
    # Save to CSV
    csv_path = Path('social/posts.csv')
    existing = []
    
    if csv_path.exists():
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            existing = list(reader)
        print(f"\n📖 Loaded {len(existing)} existing posts")
    
    all_posts = existing + new_posts
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'post_date', 'platform', 'caption', 'image_urls', 'link', 'status'])
        writer.writeheader()
        writer.writerows(all_posts)
    
    print(f"\n{'='*50}")
    print(f"✅ Added {len(new_posts)} AI-generated posts")
    print(f"📊 Total: {len(all_posts)} posts")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
