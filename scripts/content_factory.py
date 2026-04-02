#!/usr/bin/env python3
"""
Content Factory - REAL AI using GitHub Models
"""

import os
import csv
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

def call_ai(prompt):
    """Call GitHub's free AI model"""
    
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        return None
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a creative social media strategist. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 1500
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
            
            # Clean JSON
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            return json.loads(content)
        else:
            print(f"AI Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"AI Exception: {e}")
        return None

def main():
    print("\n" + "="*50)
    print("🤖 REAL AI CONTENT FACTORY")
    print("="*50)
    
    theme = os.getenv('THEME', 'fitness motivation')
    count = int(os.getenv('COUNT', '3'))
    
    print(f"Theme: {theme}")
    print(f"Posts: {count}")
    print()
    
    # Call AI to generate content
    prompt = f"""Generate {count} social media posts for a fitness brand about "{theme}".

Return JSON array with objects containing:
- title: catchy headline (max 8 words)
- caption: engaging post (80-150 words) with emojis and hashtags

Example:
[{{"title": "Start Your Journey", "caption": "Ready to transform? Start today! 💪 #fitness"}}]"""

    ai_result = call_ai(prompt)
    
    if ai_result and len(ai_result) >= count:
        print("✅ AI generated successfully!")
        ai_posts = ai_result[:count]
    else:
        print("⚠️ AI failed, using fallback")
        ai_posts = []
        for i in range(count):
            ai_posts.append({
                'title': f"{theme.title()} - Post {i+1}",
                'caption': f"✨ {theme.title()} inspiration! Stay consistent. Every step counts. #I-FlexThailand"
            })
    
    # Create posts with dates
    new_posts = []
    start_date = datetime.now().replace(hour=9, minute=0)
    
    for i, ai_post in enumerate(ai_posts):
        post_time = start_date + timedelta(hours=i*3)
        
        post = {
            'title': ai_post.get('title', f"{theme.title()} Post {i+1}"),
            'post_date': post_time.strftime('%Y-%m-%d %H:%M'),
            'platform': 'FB,IG',
            'caption': ai_post.get('caption', ''),
            'image_urls': '',
            'link': '',
            'status': 'pending'
        }
        
        new_posts.append(post)
        print(f"✅ {post['title']}")
        print(f"   Caption: {post['caption'][:80]}...")
        print()
    
    # Save to CSV
    csv_path = Path('social/posts.csv')
    existing = []
    
    if csv_path.exists():
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing = list(reader)
        print(f"Existing posts: {len(existing)}")
    
    all_posts = existing + new_posts
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'post_date', 'platform', 'caption', 'image_urls', 'link', 'status'])
        writer.writeheader()
        writer.writerows(all_posts)
    
    print(f"\n✅ Added {len(new_posts)} AI posts")
    print(f"📊 Total: {len(all_posts)} posts")
    print("="*50)

if __name__ == "__main__":
    main()
