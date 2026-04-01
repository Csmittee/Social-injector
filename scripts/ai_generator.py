#!/usr/bin/env python3
"""
AI Content Generator for I-Flex Thailand
Generates ideas, captions, and hashtags using free GitHub Models
"""

import os
import json
import csv
import requests
from datetime import datetime, timedelta
from pathlib import Path

class AIContentGenerator:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.api_url = "https://models.inference.ai.azure.com/chat/completions"
        
    def generate_ideas(self, theme, count=10):
        """Generate post ideas using AI"""
        
        prompt = f"""You are a social media strategist for I-Flex Thailand, a fitness equipment brand.
        
Generate {count} engaging social media post ideas about "{theme}".

For each idea, provide:
- Title: Short catchy title
- Hook: First line that grabs attention (max 15 words)
- Core message: Main content (max 50 words)
- Visual description: What image should accompany it
- Target audience: Who this is for (beginners, advanced, business owners)

Return as JSON array with these fields.
Make content authentic and suitable for Thai fitness market.
"""
        
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",  # Free with GitHub
            "messages": [
                {"role": "system", "content": "You are a creative social media strategist. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Parse the JSON response
            content = result['choices'][0]['message']['content']
            # Clean up markdown if present
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
            
            ideas = json.loads(content)
            return ideas
            
        except Exception as e:
            print(f"Error generating ideas: {e}")
            return []
    
    def generate_captions(self, idea, platforms=['facebook', 'instagram', 'line']):
        """Generate platform-specific captions for an idea"""
        
        captions = {}
        
        platform_prompts = {
            'facebook': "Write a Facebook post. Professional but friendly. Include emojis. Max 500 chars.",
            'instagram': "Write an Instagram caption. Inspiring, use emojis, include 5 relevant hashtags. Max 2200 chars.",
            'line': "Write a LINE OA message. Short, personal, conversational. Max 200 chars. Include call-to-action."
        }
        
        for platform in platforms:
            prompt = f"""Idea: {idea['title']} - {idea['core_message']}
            
{platform_prompts[platform]}

Return only the caption text, no explanations."""
            
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            try:
                response = requests.post(self.api_url, headers=headers, json=payload)
                result = response.json()
                captions[platform] = result['choices'][0]['message']['content'].strip()
            except Exception as e:
                print(f"Error generating caption for {platform}: {e}")
                captions[platform] = idea['core_message']
        
        return captions
    
    def generate_hashtags(self, topic, count=10):
        """Generate relevant hashtags"""
        
        prompt = f"""Generate {count} relevant Thai fitness hashtags for: {topic}
        
Return as a comma-separated list with # symbol.
Mix Thai and English tags."""
        
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "max_tokens": 200
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except:
            return "#fitness #thailand #workout #health #wellness"

# Test function
if __name__ == "__main__":
    generator = AIContentGenerator()
    
    print("🎯 Testing AI Content Generator")
    print("-" * 40)
    
    # Generate 3 ideas
    ideas = generator.generate_ideas("fitness motivation", count=3)
    
    for i, idea in enumerate(ideas):
        print(f"\n💡 Idea {i+1}: {idea.get('title', 'Untitled')}")
        print(f"   Hook: {idea.get('hook', 'N/A')}")
        print(f"   Message: {idea.get('core_message', 'N/A')[:100]}...")
        
        # Generate captions for this idea
        captions = generator.generate_captions(idea)
        print(f"   📘 FB Caption: {captions.get('facebook', 'N/A')[:80]}...")
