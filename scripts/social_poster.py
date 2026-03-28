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
        
        try:
            post_time = datetime.strptime(row['datetime'], '%Y-%m-%d %H:%M')
        except:
            print(f"⚠️ Invalid datetime: {row.get('datetime')}")
            continue
        
        if post_time > now:
            print(f"⏰ Post scheduled for {post_time} (future)")
            continue
        
        print(f"\n📤 Posting: {row['datetime']} | {row['platform']}")
        print(f"   Content: {row['content'][:100]}...")
        
        platforms = [p.strip() for p in row['platform'].split(',')]
        success = True
        
        for platform in platforms:
            if platform == 'facebook':
                result = post_to_facebook(row['content'], row.get('image_url'), row.get('link'))
            elif platform == 'instagram':
                result = post_to_instagram(row['content'], row.get('image_url'))
            elif platform == 'line':
                result = post_to_line(row['content'], row.get('image_url'))
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
            writer = csv.DictWriter(f, fieldnames=['datetime','platform','content','image_url','link','status'])
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n💾 CSV updated")
    
    print("\n🎉 Dry run complete. Set DRY_RUN = False when tokens are ready.")

if __name__ == '__main__':
    main()
