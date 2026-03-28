import csv
import os
from datetime import datetime
from pathlib import Path

CSV_PATH = Path('social/posts.csv')
DRY_RUN = True  # Set to False when you have tokens

def post_to_facebook(message, image_url, link):
    print(f"  📘 [DRY RUN] Would post to Facebook:")
    print(f"     Message: {message[:100]}...")
    if image_url: print(f"     Image: {image_url}")
    if link: print(f"     Link: {link}")
    return True

def post_to_instagram(message, image_url):
    print(f"  📷 [DRY RUN] Would post to Instagram:")
    print(f"     Caption: {message[:100]}...")
    if image_url: print(f"     Image: {image_url}")
    return True

def post_to_line(message, image_url):
    print(f"  💬 [DRY RUN] Would post to Line:")
    print(f"     Message: {message[:100]}...")
    if image_url: print(f"     Image: {image_url}")
    return True

def main():
    print("📱 Social Poster (DRY RUN MODE)")
    print(f"CSV: {CSV_PATH}")
    
    if not CSV_PATH.exists():
        print(f"❌ CSV not found")
        return
    
    now = datetime.now()
    updated = False
    
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    
    for i, row in enumerate(rows):
        if row.get('status') != 'approved':
            continue
        
        # Match your CSV column names
        try:
            post_time = datetime.strptime(row['post_date'], '%Y-%m-%d %H:%M')
        except:
            print(f"⚠️ Invalid datetime: {row.get('post_date')}")
            continue
        
        if post_time > now:
            print(f"⏰ Post scheduled for {post_time} (future)")
            continue
        
        print(f"\n📤 Posting: {row['post_date']} | {row['platform']}")
        print(f"   Caption: {row['caption'][:100]}...")
        
        platforms = [p.strip() for p in row['platform'].split(',')]
        success = True
        
        for platform in platforms:
            plat = platform.lower()
            if 'facebook' in plat or 'fb' in plat:
                result = post_to_facebook(row['caption'], row.get('image_urls'), row.get('link'))
            elif 'instagram' in plat or 'ig' in plat:
                result = post_to_instagram(row['caption'], row.get('image_urls'))
            elif 'line' in plat:
                result = post_to_line(row['caption'], row.get('image_urls'))
            else:
                print(f"⚠️ Unknown platform: {platform}")
                result = False
            
            if not result:
                success = False
        
        if success:
            rows[i]['status'] = 'posted'
            updated = True
            print(f"✅ Marked as posted")
    
    if updated:
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            # Match your CSV headers exactly
            fieldnames = ['title', 'post_date', 'platform', 'caption', 'image_urls', 'link', 'status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n💾 CSV updated")
    
    print("\n🎉 Dry run complete. Set DRY_RUN = False when tokens are ready.")

if __name__ == '__main__':
    main()
