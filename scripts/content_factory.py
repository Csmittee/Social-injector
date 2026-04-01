#!/usr/bin/env python3
"""
Content Factory - Accepts parameters from GitHub Actions
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
        self.ideas_dir = Path('social/ai_generated')
        self.ideas_dir.mkdir(parents=True, exist_ok=True)
        
        # Read parameters from environment
        self.theme = os.getenv('THEME', 'general')
        self.count = int(os.getenv('COUNT', '5'))
        self.platforms = os.getenv('PLATFORMS', 'facebook,instagram').split(',')
        
    def generate_content(self):
        """Generate content based on parameters"""
        
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
            
            # Generate captions for each platform
            captions = self.generator.generate_captions(idea, self.platforms)
            
            # Generate hashtags
            hashtags = self.generator.generate_hashtags(idea.get('title', self.theme))
            
            # Create post time
            post_time = start_date + timedelta(hours=i*3)
            
            # For multiple platforms, combine or create separate?
            platform_str = ','.join(self.platforms)
            
            # Combine caption with hashtags for Instagram
            ig_caption = captions.get('instagram', '')
            if ig_caption and hashtags:
                ig_caption = f"{ig_caption}\n\n{hashtags}"
            
            post = {
                'title': idea.get('title', f"Idea {i+1}"),
                'post_date': post_time.strftime('%Y-%m-%d %H:%M'),
                'platform': platform_str,
                'caption': ig_caption or captions.get('facebook', idea.get('core_message', '')),
                'image_urls': '',
                'link': '',
                'status': 'pending'
            }
            
            all_posts.append(post)
            print(f"   ✅ Created: {post['title']}")
        
        # Save to CSV
        self.save_to_csv(all_posts)
        print(f"\n🎉 Generated {len(all_posts)} posts!")
        
        return all_posts
    
    def save_to_csv(self, posts):
        """Save posts to CSV file"""
        
        fieldnames = ['title', 'post_date', 'platform', 'caption', 'image_urls', 'link', 'status']
        
        existing_posts = []
        if self.csv_path.exists():
            with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                existing_posts = list(reader)
        
        all_posts = existing_posts + posts
        
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_posts)
        
        print(f"\n💾 Saved to {self.csv_path}")

if __name__ == "__main__":
    factory = ContentFactory()
    factory.generate_content()
