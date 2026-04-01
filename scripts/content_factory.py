#!/usr/bin/env python3
"""
Main Content Factory - Orchestrates the entire automation pipeline
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
        
    def generate_weekly_content(self):
        """Generate a week's worth of content"""
        
        print("🏭 Starting Content Factory")
        print("=" * 50)
        
        # Themes for the week (you can customize)
        themes = [
            "weight loss motivation",
            "fitness equipment tips",
            "client success stories",
            "nutrition advice",
            "workout routines",
            "mindset and motivation",
            "business/fitness studio tips"
        ]
        
        all_posts = []
        start_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        for day, theme in enumerate(themes):
            print(f"\n📅 Day {day+1}: Generating content for '{theme}'")
            
            # Generate ideas for this theme
            ideas = self.generator.generate_ideas(theme, count=2)  # 2 ideas per theme = 14 posts/week
            
            for i, idea in enumerate(ideas):
                # Generate captions for each platform
                captions = self.generator.generate_captions(idea)
                
                # Generate hashtags
                hashtags = self.generator.generate_hashtags(idea.get('title', theme))
                
                # Create post schedule (spread throughout the day)
                post_time = start_date + timedelta(days=day, hours=i*3)
                
                # Combined caption with hashtags
                ig_caption = f"{captions.get('instagram', '')}\n\n{hashtags}"
                
                post = {
                    'title': idea.get('title', f"Idea {day+1}_{i+1}"),
                    'post_date': post_time.strftime('%Y-%m-%d %H:%M'),
                    'platform': 'FB,IG',  # Start with both
                    'caption': ig_caption,
                    'image_urls': '',  # Will be filled by image generator
                    'link': '',  # Will be filled later
                    'status': 'pending'
                }
                
                all_posts.append(post)
                print(f"   ✅ Generated: {post['title']}")
                
                # Optional: Save each idea individually for reference
                idea_file = self.ideas_dir / f"{post_time.strftime('%Y%m%d_%H%M')}_{idea.get('title', 'idea')[:30]}.json"
                with open(idea_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'idea': idea,
                        'captions': captions,
                        'hashtags': hashtags,
                        'post': post
                    }, f, ensure_ascii=False, indent=2)
        
        # Save to CSV
        self.save_to_csv(all_posts)
        print(f"\n🎉 Generated {len(all_posts)} posts for the week!")
        
        return all_posts
    
    def save_to_csv(self, posts):
        """Save posts to CSV file"""
        
        fieldnames = ['title', 'post_date', 'platform', 'caption', 'image_urls', 'link', 'status']
        
        # Load existing posts if file exists
        existing_posts = []
        if self.csv_path.exists():
            with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                existing_posts = list(reader)
        
        # Append new posts
        all_posts = existing_posts + posts
        
        # Write back
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_posts)
        
        print(f"\n💾 Saved to {self.csv_path}")

if __name__ == "__main__":
    factory = ContentFactory()
    
    # Generate weekly content
    posts = factory.generate_weekly_content()
    
    print("\n📊 Summary:")
    print(f"   Total posts: {len(posts)}")
    print(f"   Next steps:")
    print(f"   1. Review posts in dashboard: https://i-flexthailand.com/social/dashboard.html")
    print(f"   2. Approve/reject posts")
    print(f"   3. Enable social poster to auto-publish")
