#!/usr/bin/env python3
"""
Content Factory - Clean Version
Creates validated posts directly to CSV
"""

import os
import csv
from datetime import datetime, timedelta
from pathlib import Path

def validate_post(post):
    """Check if post has all required fields"""
    required = ['title', 'post_date', 'platform', 'caption', 'status']
    for field in required:
        if not post.get(field):
            return False
    return True

def main():
    print("\n" + "="*50)
    print("🏭 CONTENT FACTORY")
    print("="*50)
    
    # Get inputs from GitHub Actions
    theme = os.getenv('THEME', 'fitness motivation')
    count = int(os.getenv('COUNT', '5'))
    
    print(f"\n📝 Creating {count} posts")
    print(f"   Theme: {theme}")
    print()
    
    # Create posts
    new_posts = []
    start_date = datetime.now().replace(hour=9, minute=0)
    
    for i in range(count):
        post_time = start_date + timedelta(hours=i*3, days=i//3)
        
        post = {
            'title': f"{theme.title()} - Post {i+1}",
            'post_date': post_time.strftime('%Y-%m-%d %H:%M'),
            'platform': 'FB,IG',
            'caption': f"""✨ {theme.title()} inspiration for you! ✨

Stay consistent and trust the process. Every small step counts toward your goal.

Ready to start? Let's go! 💪

#I-FlexThailand #FitnessJourney #{theme.replace(' ', '')}""",
            'image_urls': '',
            'link': '',  # ← EMPTY, you fill manually
            'status': 'pending'
        }
        
        if validate_post(post):
            new_posts.append(post)
            print(f"✅ Post {i+1}: {post['title']} - {post['post_date']}")
    
    if not new_posts:
        print("\n⚠️ No valid posts created")
        return
    
    # Load and save CSV
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
    print(f"✅ Added {len(new_posts)} new posts")
    print(f"📊 Total: {len(all_posts)} posts")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
