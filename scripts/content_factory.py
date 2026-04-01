#!/usr/bin/env python3
"""
Content Factory - Matches Your CSV Structure
"""

import os
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from ai_generator import AIContentGenerator

class ContentFactory:
    def __init__(self):
        self.generator = AIContentGenerator()
        self.csv_path = Path('social/posts.csv')
        
        # Read parameters from environment
        self.theme = os.getenv('THEME', 'general')
        self.count = int(os.getenv('COUNT', '5'))
        self.platforms = os.getenv('PLATFORMS', 'facebook,instagram').split(',')
        
    def generate_content(self):
        """Generate content and append to existing CSV"""
        
        print(f"🏭 Starting Content Factory")
        print(f"   Theme: {self.theme}")
        print(f"   Count: {self.count}")
        print(f"   Platforms: {self.platforms}")
        print("=" * 50)
        
        all_posts = []
        start_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Generate ideas
        print(f"\n🤖 Generating {self.count} ideas about '{self.theme}'...")
        ideas = self.generator.generate_ideas(self.theme, count=self.count)
        
        for i, idea in enumerate(ideas):
            print(f"\n📝 Processing idea {i+1}: {idea.get('title', 'Untitled')}")
            
            # Generate captions
            captions = self.generator.generate_captions(idea, self.platforms)
            
            # Generate hashtags
            hashtags = self.generator.generate_hashtags(idea.get('title', self.theme))
            
            # Create post time (spread throughout week)
            post_time = start_date + timedelta(days=i//3, hours=(i%3)*3)
            
            # Combine caption with hashtags for Instagram style
            main_caption = captions.get('instagram', captions.get('facebook', idea.get('core_message', '')))
            if hashtags:
                main_caption = f"{main_caption}\n\n{hashtags}"
            
            # Create post matching YOUR CSV structure
            post = {
                'title': idea.get('title', f"{self.theme} - Post {i+1}"),
                'post_date': post_time.strftime('%Y-%m-%d %H:%M'),
                'platform': ','.join(self.platforms).upper().replace('FACEBOOK', 'FB').replace('INSTAGRAM', 'IG'),
                'caption': main_caption[:500],  # Limit length
                'image_urls': '',  # Empty for now
                'link': '',  # Empty for now
                'status': 'pending'
            }
            
            all_posts.append(post)
            print(f"   ✅ Created: {post['title']} for {post['platform']}")
        
        # Append to existing CSV
        self.append_to_csv(all_posts)
        print(f"\n🎉 Generated {len(all_posts)} new posts!")
        
        return all_posts
    
    def append_to_csv(self, new_posts):
        """Append new posts to existing CSV file"""
        
        fieldnames = ['title', 'post_date', 'platform', 'caption', 'image_urls', 'link', 'status']
        
        # Read existing posts if file exists
        existing_posts = []
        if self.csv_path.exists():
            with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                existing_posts = list(reader)
            print(f"📖 Loaded {len(existing_posts)} existing posts")
        
        # Append new posts
        all_posts = existing_posts + new_posts
        
        # Write back
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_posts)
        
        print(f"💾 Saved {len(new_posts)} new posts to {self.csv_path}")
        print(f"📊 Total posts now: {len(all_posts)}")

if __name__ == "__main__":
    factory = ContentFactory()
    factory.generate_content()
