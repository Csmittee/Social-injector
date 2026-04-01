#!/usr/bin/env python3
"""
AI Content Factory - Real CSV Writer with Long Captions
"""

import os
import csv
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

class AIContentGenerator:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        
    def generate_ideas(self, theme, count=5):
        """Generate rich, detailed post ideas"""
        
        prompt = f"""You are a professional social media strategist. Create {count} engaging social media posts for a brand about "{theme}".

For EACH post, provide:
- title: Catchy headline (max 8 words)
- hook: First sentence that grabs attention (max 15 words)
- core_message: Main content - make it VALUABLE, detailed, and engaging (80-120 words). Include specific tips, relatable stories, or actionable advice.
- visual_description: What image/video should accompany this post

Make the content feel authentic, conversational, and valuable. Return as JSON array.

Example format:
[{{"title": "Start Your Day Right", "hook": "Morning routines that change lives", "core_message": "The first 20 minutes of your morning set the tone for everything. Here's what successful people do...", "visual_description": "Sunrise workout, coffee, journaling setup"}}]"""

        try:
            response = requests.post(
                "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
                headers={"Authorization": f"Bearer {self.github_token}"},
                json={"inputs": prompt, "parameters": {"max_new_tokens": 2000}}
            )
            
            if response.status_code == 200:
                result = response.json()
                text = result[0]['generated_text']
                # Extract JSON
                start = text.find('[')
                end = text.rfind(']') + 1
                if start != -1 and end != 0:
                    return json.loads(text[start:end])
        except:
            pass
        
        # Fallback ideas
        return [
            {"title": f"{theme.title()} - Post 1", "hook": "Start your journey today", 
             "core_message": f"Here's your daily dose of {theme} inspiration. Remember that every small step counts. Consistency beats intensity. Keep showing up, trust the process, and celebrate your progress along the way. You've got this! 💪", 
             "visual_description": "Motivational scene"},
            {"title": f"{theme.title()} - Post 2", "hook": "Small changes, big results", 
             "core_message": f"When it comes to {theme}, it's the little things that add up. A 10-minute practice daily becomes 70 minutes a week. That's over 60 hours a year! Start small, stay consistent, and watch your progress compound.", 
             "visual_description": "Progress visualization"}
        ] * (count // 2)
    
    def generate_captions(self, idea, platforms):
        """Generate platform-specific captions"""
        captions = {}
        
        for platform in platforms:
            platform = platform.lower()
            if platform == 'instagram':
                captions[platform] = f"""✨ {idea['hook']}

{idea['core_message']}

💡 Pro tip: Save this for later!

👇 Drop a comment if this resonates with you!

#I-FlexThailand #{idea['title'].replace(' ', '')} #FitnessJourney #ThaiFitness #Motivation #Workout #HealthyLifestyle #FitFam #ProgressNotPerfection"""
            
            elif platform == 'facebook':
                captions[platform] = f"""{idea['hook']} 💪

{idea['core_message']}

What's your biggest takeaway from this? Share in the comments! 👇

#I-FlexThailand #FitnessMotivation"""
            
            elif platform == 'line':
                captions[platform] = f"""{idea['hook']}

{idea['core_message'][:150]}...

👉 Message us to learn more!"""
        
        return captions

class ContentFactory:
    def __init__(self):
        self.generator = AIContentGenerator()
        self.csv_path = Path('social/posts.csv')
        
        # Read parameters
        self.theme = os.getenv('THEME', 'fitness motivation')
        self.count = int(os.getenv('COUNT', '5'))
        self.platforms = [p.strip() for p in os.getenv('PLATFORMS', 'facebook,instagram').split(',')]
        
    def run(self):
        print(f"\n{'='*50}")
        print(f"🤖 AI Content Factory")
        print(f"   Theme: {self.theme}")
        print(f"   Posts: {self.count}")
        print(f"   Platforms: {', '.join(self.platforms)}")
        print(f"{'='*50}\n")
        
        # Generate ideas
        print(f"📝 Generating {self.count} ideas...")
        ideas = self.generator.generate_ideas(self.theme, self.count)
        
        # Generate posts
        new_posts = []
        start_date = datetime.now().replace(hour=9, minute=0)
        
        for i, idea in enumerate(ideas[:self.count]):
            print(f"\n✍️ Post {i+1}: {idea.get('title', 'Untitled')}")
            
            captions = self.generator.generate_captions(idea, self.platforms)
            
            # Use Instagram caption as main (it's longest)
            main_caption = captions.get('instagram', captions.get('facebook', idea['core_message']))
            
            post_time = start_date + timedelta(hours=i*3)
            
            post = {
                'title': idea.get('title', f"{self.theme} Post {i+1}"),
                'post_date': post_time.strftime('%Y-%m-%d %H:%M'),
                'platform': ','.join([p.upper()[:2] for p in self.platforms]),
                'caption': main_caption,
                'image_urls': '',
                'link': '',
                'status': 'pending'
            }
            
            new_posts.append(post)
            print(f"   ✅ Caption: {len(main_caption)} chars")
        
        # Save to CSV
        self.save_to_csv(new_posts)
        
        print(f"\n{'='*50}")
        print(f"🎉 SUCCESS! Generated {len(new_posts)} posts")
        print(f"📁 Saved to: {self.csv_path}")
        print(f"📊 Total posts now: {self.get_post_count()}")
        print(f"{'='*50}")
        
    def save_to_csv(self, new_posts):
        fieldnames = ['title', 'post_date', 'platform', 'caption', 'image_urls', 'link', 'status']
        
        existing = []
        if self.csv_path.exists():
            with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                existing = list(reader)
        
        all_posts = existing + new_posts
        
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_posts)
    
    def get_post_count(self):
        if not self.csv_path.exists():
            return 0
        with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
            return sum(1 for _ in f) - 1

if __name__ == "__main__":
    factory = ContentFactory()
    factory.run()
