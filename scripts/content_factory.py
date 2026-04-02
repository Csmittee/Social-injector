import csv
import os
from datetime import datetime

# Robust CSV append function (handles commas, quotes, emojis, newlines safely)
def append_to_csv(new_posts, csv_path="social/posts.csv"):
    """
    Append new posts to posts.csv safely.
    Creates the file and header if it doesn't exist.
    """
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    # All possible columns
    fieldnames = ['title', 'post_date', 'platform', 'caption', 'image_urls', 'link', 'status']
    
    file_exists = os.path.isfile(csv_path)
    
    with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        
        # Write header only if file is new
        if not file_exists:
            writer.writeheader()
        
        for post in new_posts:
            # Ensure all fields exist and clean data
            row = {field: str(post.get(field, '')).strip() for field in fieldnames}
            
            # Force status to lowercase for consistency with dashboard
            if row.get('status'):
                row['status'] = row['status'].lower().strip()
            else:
                row['status'] = 'pending'
            
            # Optional: Add timestamp if post_date is missing
            if not row['post_date']:
                row['post_date'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            writer.writerow(row)
    
    print(f"✅ Successfully appended {len(new_posts)} post(s) to {csv_path}")


# Example usage (you can call this from ai_generator.py or elsewhere)
if __name__ == "__main__":
    # Test / Example
    sample_posts = [
        {
            "title": "Test Yoga Post",
            "post_date": "2026-04-03 10:00",
            "platform": "FB,IG",
            "caption": "This is a test caption with emoji ✨ and, commas in text.",
            "image_urls": "",
            "link": "",
            "status": "pending"
        }
    ]
    
    append_to_csv(sample_posts)
