#!/usr/bin/env python3
"""
Content Factory - Fixed Version
Every post gets a VALID status
"""

import os
import csv
from datetime import datetime, timedelta
from pathlib import Path

def main():
    print("\n" + "="*50)
    print("CONTENT FACTORY - FIXED")
    print("="*50)
    
    theme = os.getenv('THEME', 'fitness motivation')
    count = int(os.getenv('COUNT', '3'))
    
    print(f"Theme: {theme}")
    print(f"Posts to create: {count}")
    print()
    
    # Create posts with VALID status
    new_posts = []
    start_date = datetime.now().replace(hour=9, minute=0)
    
    for i in range(count):
        post_time = start_date + timedelta(hours=i*3)
        
        # EVERY post gets a VALID status
        post = {
            'title': f"{theme.title()} - Post {i+1}",
            'post_date': post_time.strftime('%Y-%m-%d %H:%M'),
            'platform': 'FB,IG',
            'caption': f"✨ {theme.title()} inspiration! Stay consistent. Every step counts. #I-FlexThailand",
            'image_urls': '',
            'link': '',
            'status': 'pending'  # ← ALWAYS pending, never empty
        }
        
        new_posts.append(post)
        print(f"Created: {post['title']} | Status: {post['status']}")
    
    # Read existing CSV
    csv_path = Path('social/posts.csv')
    existing = []
    
    if csv_path.exists():
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing = list(reader)
        print(f"\nExisting posts: {len(existing)}")
    
    # Combine
    all_posts = existing + new_posts
    
    # Write back with ALL fields
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'post_date', 'platform', 'caption', 'image_urls', 'link', 'status'])
        writer.writeheader()
        writer.writerows(all_posts)
    
    print(f"\nTotal posts now: {len(all_posts)}")
    print(f"New posts added: {len(new_posts)}")
    print("="*50)

if __name__ == "__main__":
    main()
