#!/usr/bin/env python3
"""
AI Content Factory - With Auto-Generated Links
"""

import os
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

class SmartContentFactory:
    def __init__(self):
        self.csv_path = Path('social/posts.csv')
        self.theme = os.getenv('THEME', 'fitness motivation')
        self.count = int(os.getenv('COUNT', '5'))
        
        # Define link templates based on theme
        self.link_templates = {
            'fitness': [
                "https://i-flexthailand.com/equipment",
                "https://i-flexthailand.com/workouts",
                "https://i-flexthailand.com/personal-training",
                "https://i-flexthailand.com/shop",
                "https://i-flexthailand.com/free-guide"
            ],
            'weight loss': [
                "https://i-flexthailand.com/weight-loss",
                "https://i-flexthailand.com/nutrition-plan",
                "https://i-flexthailand.com/fitness-assessment",
                "https://i-flexthailand.com/meal-planner"
            ],
            'nutrition': [
                "https://i-flexthailand.com/healthy-eating",
                "https://i-flexthailand.com/recipes",
                "https://i-flexthailand.com/nutrition-guide"
            ],
            'motivation': [
                "https://i-flexthailand.com/success-stories",
                "https://i-flexthailand.com/free-resources",
                "https://i-flexthailand.com/community"
            ]
        }
        
    def get_link_for_theme(self, theme, post_title):
        """Generate appropriate link based on theme and post title"""
        
        theme_lower = theme.lower()
        
        # Match theme to link category
        link_category = 'fitness'  # default
        for key in self.link_templates:
            if key in theme_lower:
                link_category = key
                break
        
        # Get links for this category
        links = self.link_templates.get(link_category, self.link_templates['fitness'])
        
        # Add CTA-based links
        call_to_actions = [
            "https://i-flexthailand.com/book-consultation",
            "https://i-flexthailand.com/free-trial",
            "https://i-flexthailand.com/contact",
            "https://i-flexthailand.com/special-offer"
        ]
        
        # Choose link based on post content
        if any(word in post_title.lower() for word in ['start', 'begin', 'new']):
            return "https://i-flexthailand.com/new-client-special"
        elif any(word in post_title.lower() for word in ['guide', 'tips', 'how to']):
            return "https://i-flexthailand.com/free-guide"
        elif any(word in post_title.lower() for word in ['success', 'story', 'transform']):
            return "https://i-flexthailand.com/success-stories"
        elif random.random() > 0.6:
            return random.choice(links)
        else:
            return random.choice(call_to_actions)
    
    def run(self):
        print(f"\n{'='*50}")
        print(f"🏭 AI Content Factory (with Links)")
        print(f"   Theme: {self.theme}")
        print(f"   Posts: {self.count}")
        print(f"{'='*50}\n")
        
        # Create posts
        new_posts = []
        start_date = datetime.now().replace(hour=9, minute=0)
        
        # Sample post ideas based on theme
        post_templates = [
            {
                'title': f"💪 Start Your {self.theme.title()} Journey",
                'caption': f"""Ready to transform your life? {self.theme.title()} is the first step toward a healthier, happier you! 🌟

Here's what you'll discover:
✓ Simple daily habits that stick
✓ Expert tips from certified trainers
✓ Real results from real people

The journey of a thousand miles begins with a single step. Take yours today! 💫

👇 Click the link below to get started!

#{self.theme.replace(' ', '')} #I-FlexThailand #FitnessJourney #ThaiFitness #GetStarted #NewYou"""
            },
            {
                'title': f"✨ Daily {self.theme.title()} Motivation",
                'caption': f"""Need a boost today? Here's your daily dose of {self.theme.title()} inspiration! 🔥

Remember: Every expert was once a beginner. Every champion started as a contender. Your journey is unique, and every small step counts.

💡 Pro Tip: Consistency beats intensity. Show up, do the work, trust the process.

What's your goal this week? Drop it below! 👇

#{self.theme.replace(' ', '')} #Motivation #I-FlexThailand #FitnessMindset #DailyInspiration"""
            },
            {
                'title': f"🏆 {self.theme.title()} Success Tips",
                'caption': f"""Want faster results? Here are 3 proven {self.theme.title()} strategies: 🔑

1. Set specific, measurable goals
2. Track your progress daily
3. Celebrate small wins

These simple shifts helped our clients achieve amazing transformations. They can work for you too!

👉 Click the link for your free guide!

#{self.theme.replace(' ', '')} #SuccessTips #I-FlexThailand #FitnessHacks #Results"""
            },
            {
                'title': f"🌟 {self.theme.title()} Made Simple",
                'caption': f"""Think {self.theme.title()} is complicated? Think again! 💫

We've broken it down into 3 simple steps that anyone can follow:
1️⃣ Start small
2️⃣ Stay consistent  
3️⃣ Stack your wins

No complicated equipment. No overwhelming routines. Just real results that last.

Ready to simplify your journey? Tap the link! 👇

#{self.theme.replace(' ', '')} #SimpleFitness #I-FlexThailand #EasyWorkouts #HealthyHabits"""
            },
            {
                'title': f"🔥 {self.theme.title()} Challenge",
                'caption': f"""Ready for a challenge? Join our 7-day {self.theme.title()} challenge! 🎯

What you'll get:
✓ Daily actionable tasks
✓ Support from our community
✓ Progress tracking tools
✓ Prizes for top performers

The best time to start was yesterday. The next best time is NOW!

👇 Sign up through the link below!

#{self.theme.replace(' ', '')} #FitnessChallenge #I-FlexThailand #JoinNow #7DayChallenge"""
            }
        ]
        
        for i in range(self.count):
            # Rotate through templates
            template = post_templates[i % len(post_templates)]
            post_time = start_date + timedelta(hours=i*3, days=i//3)
            
            # Generate link for this post
            post_link = self.get_link_for_theme(self.theme, template['title'])
            
            post = {
                'title': template['title'],
                'post_date': post_time.strftime('%Y-%m-%d %H:%M'),
                'platform': 'FB,IG',
                'caption': template['caption'],
                'image_urls': '',
                'link': post_link,
                'status': 'pending'
            }
            
            new_posts.append(post)
            print(f"✅ Created: {post['title']}")
            print(f"   📅 Date: {post['post_date']}")
            print(f"   🔗 Link: {post['link']}")
            print()
        
        # Save to CSV
        self.save_to_csv(new_posts)
        
        print(f"\n{'='*50}")
        print(f"🎉 SUCCESS! Generated {len(new_posts)} posts with links")
        print(f"📁 Saved to: {self.csv_path}")
        print(f"{'='*50}")
        
    def save_to_csv(self, new_posts):
        fieldnames = ['title', 'post_date', 'platform', 'caption', 'image_urls', 'link', 'status']
        
        existing = []
        if self.csv_path.exists():
            with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                existing = list(reader)
            print(f"📖 Loaded {len(existing)} existing posts")
        
        all_posts = existing + new_posts
        
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_posts)
        
        print(f"💾 Saved {len(new_posts)} new posts to CSV")

if __name__ == "__main__":
    factory = SmartContentFactory()
    factory.run()
