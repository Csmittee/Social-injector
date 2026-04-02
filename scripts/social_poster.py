import csv
import os
from datetime import datetime

CSV_PATH = "social/posts.csv"

def load_approved_posts():
    """Load posts with status 'approved'"""
    if not os.path.isfile(CSV_PATH):
        print("❌ posts.csv not found!")
        return []
    
    approved = []
    with open(CSV_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get('status') or '').strip().lower() == 'approved':
                approved.append(row)
    return approved


def simulate_post(post):
    """Simulate posting - No real API call yet"""
    print(f"\n🔄 [DRY RUN] Simulating post: {post.get('title')}")
    print(f"   Platform : {post.get('platform', 'N/A')}")
    print(f"   Date     : {post.get('post_date', 'N/A')}")
    print(f"   Caption  : {post.get('caption', '')[:120]}...\n")
    
    # In real version, you will call Facebook/Instagram API here
    return True  # Simulate success


def main():
    print("=" * 60)
    print("🚀 SOCIAL POSTER - DRY RUN MODE")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    approved_posts = load_approved_posts()
    
    if not approved_posts:
        print("✅ No approved posts ready to post at this time.")
        print("   (Approve some posts from the dashboard first)")
        return
    
    print(f"Found {len(approved_posts)} approved post(s).\n")
    
    for post in approved_posts:
        success = simulate_post(post)
        if success:
            print(f"✅ [DRY RUN] Successfully simulated posting: {post.get('title')}")
            # TODO: Later change status to 'posted'
        else:
            print(f"❌ Failed to simulate post: {post.get('title')}")
    
    print("\n🏁 Dry run completed. No real posting happened.")
    print("   When ready, we will connect real social media APIs.")


if __name__ == "__main__":
    main()
