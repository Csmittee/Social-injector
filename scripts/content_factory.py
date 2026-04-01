#!/usr/bin/env python3
"""
AI Content Factory - With Validation and Protection
"""

import os
import csv
import re
from datetime import datetime, timedelta
from pathlib import Path

class ProtectedContentFactory:
    def __init__(self):
        self.csv_path = Path('social/posts.csv')
        self.theme = os.getenv('THEME', 'fitness motivation')
        self.count = min(int(os.getenv('COUNT', '5')), 14)  # Max 14 posts per run
        
    def validate_post(self, post):
        """Validate post before adding"""
        
        # Required fields
        required = ['title', 'post_date', 'platform', 'caption', 'status']
        for field in required:
            if not post.get(field):
                print(f"   ❌ Missing {field}")
                return False
        
        # Title length (min 3, max 100)
        if len(post['title']) < 3 or len(post['title']) > 100:
            print(f"   ❌ Title length invalid: {len(post['title'])}")
            return False
        
        # Caption length (min 20, max 2000)
        if len(post['caption']) < 20 or len(post['caption']) > 2000:
            print(f"   ❌ Caption length invalid: {len(post['caption'])}")
            return False
        
        # Platform format (should contain FB, IG, or LINE)
        valid_platforms = ['FB', 'IG', 'LINE', 'FACEBOOK', 'INSTAGRAM']
        platform_upper = post['platform'].upper()
        if not any(p in platform_upper for p in valid_platforms):
            print(f"   ❌ Invalid platform: {post['platform']}")
            return False
        
        # Date format validation
        try:
            datetime.strptime(post['post_date'], '%Y-%m-%d %H:%M')
        except:
            print(f"   ❌ Invalid date: {post['post_date']}")
            return False
        
        # Status validation
        if post['status'] not in ['pending', 'approved', 'posted', 'rejected']:
            print(f"   ❌ Invalid status: {post['status']}")
            return False
        
        return True
    
    def check_duplicate(self, new_post, existing_posts):
        """Check if post already exists"""
        for existing in existing_posts:
            if existing.get('title') == new_post.get('title'):
                # Check if same or similar date
                if existing.get('post_date') == new_post.get('post_date'):
                    return True
        return False
    
    def run(self):
        print(f"\n{'='*50}")
        print(f"🛡️ Protected Content Factory")
        print(f"   Theme: {self.theme}")
        print(f"   Max Posts: {self.count}")
        print(f"{'='*50}\n")
        
        # Load existing posts
        existing_posts = []
        if self.csv_path.exists():
            with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                existing_posts = list(reader)
            print(f"📖 Loaded {len(existing_posts)} existing posts")
        
        # Create new posts
        new_posts = []
        start_date = datetime.now().replace(hour=9, minute=0)
        
        # Clean, validated post templates
        post_templates = [
            {
                'title': f"Start Your {self.theme.title()} Journey Today",
                'caption': f"""Ready to transform your life? {self.theme.title()} is your first step to a healthier you! 🌟

✓ Simple daily habits that stick
✓ Expert tips from certified trainers
✓ Real results from real people

Start today and see the difference! 💪

What's your fitness goal? Comment below! 👇

#{self.theme.replace(' ', '')} #I-FlexThailand #FitnessJourney #ThaiFitness"""
            },
            {
                'title': f"Daily {self.theme.title()} Motivation",
                'caption': f"""Need motivation today? Here's your daily dose of {self.theme.title()} inspiration! 🔥

Remember: Every expert was once a beginner. Every champion started as a contender.

💡 Pro Tip: Consistency beats intensity. Show up, do the work, trust the process.

What keeps you motivated? Share below! 👇

#{self.theme.replace(' ', '')} #Motivation #I-FlexThailand #FitnessMindset"""
            },
            {
                'title': f"3 {self.theme.title()} Tips That Work",
                'caption': f"""Want faster results? Here are 3 proven {self.theme.title()} strategies: 🔑

1️⃣ Set specific, measurable goals
2️⃣ Track your progress daily
3️⃣ Celebrate small wins

These simple shifts helped our clients achieve amazing transformations. They can work for you too!

Try these today! 👇

#{self.theme.replace(' ', '')} #SuccessTips #I-FlexThailand #FitnessHacks"""
            }
        ]
        
        added = 0
        for i in range(min(self.count, len(post_templates) * 3)):
            template = post_templates[i % len(post_templates)]
            post_time = start_date + timedelta(hours=i*3, days=i//3)
            
            # Create link based on theme
            link = f"https://i-flexthailand.com/{self.theme.lower().replace(' ', '-')}"
            
            post = {
                'title': template['title'],
                'post_date': post_time.strftime('%Y-%m-%d %H:%M'),
                'platform': 'FB,IG',
                'caption': template['caption'],
                'image_urls': '',
                'link': link,
                'status': 'pending'
            }
            
            # Validate
            if not self.validate_post(post):
                print(f"❌ Invalid post skipped: {post['title']}")
                continue
            
            # Check duplicate
            if self.check_duplicate(post, existing_posts):
                print(f"⚠️ Duplicate skipped: {post['title']}")
                continue
            
            new_posts.append(post)
            added += 1
            print(f"✅ Added: {post['title']}")
        
        if new_posts:
            # Save to CSV
            all_posts = existing_posts + new_posts
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['title', 'post_date', 'platform', 'caption', 'image_urls', 'link', 'status'])
                writer.writeheader()
                writer.writerows(all_posts)
            
            print(f"\n{'='*50}")
            print(f"🎉 SUCCESS! Added {added} new posts")
            print(f"📊 Total posts now: {len(all_posts)}")
        else:
            print(f"\n⚠️ No new posts added (all were invalid or duplicates)")

if __name__ == "__main__":
    factory = ProtectedContentFactory()
    factory.run()
