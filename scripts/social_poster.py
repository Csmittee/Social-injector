import csv
import os
from datetime import datetime

CSV_PATH = "social/posts.csv"

def load_all_posts():
    """Load every post from CSV"""
    if not os.path.isfile(CSV_PATH):
        print("❌ posts.csv not found!")
        return []
    
    posts = []
    with open(CSV_PATH, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            posts.append(row)
    return posts


def save_all_posts(posts):
    """Rewrite the entire CSV with updated statuses"""
    fieldnames = ['title', 'post_date', 'platform', 'caption', 'image_urls', 'link', 'status']
    
    with open(CSV_PATH, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(posts)
    
    print(f"✅ CSV updated and saved ({len(posts)} total posts)")


def simulate_post(post):
    """Dry-run simulation - no real social media call yet"""
    print(f"\n🔄 [DRY RUN] Simulating post → {post.get('title')}")
    print(f"   Platform : {post.get('platform', 'N/A')}")
    print(f"   Link     : {post.get('link', '(empty)')}")
    print(f"   Caption  : {post.get('caption', '')[:120]}...\n")
    return True  # always success in dry-run


def main():
    print("=" * 70)
    print("🚀 SOCIAL POSTER - DRY RUN MODE (with status update)")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    all_posts = load_all_posts()
    approved_posts = [p for p in all_posts if (p.get('status') or '').strip().lower() == 'approved']
    
    if not approved_posts:
        print("✅ No approved posts ready to process.")
        print("   (Go to dashboard → approve some posts first)")
        return
    
    print(f"Found {len(approved_posts)} approved post(s) to simulate...\n")
    
    updated_count = 0
    for post in approved_posts:
        success = simulate_post(post)
        if success:
            post['status'] = 'posted'          # ← This is the important line
            updated_count += 1
            print(f"✅ Marked as POSTED: {post.get('title')}")
    
    # Save changes back to CSV
    save_all_posts(all_posts)
    
    print(f"\n🏁 Dry run finished. {updated_count} post(s) moved to 'posted' status.")
    print("   The workflow will now commit this change automatically.")


if __name__ == "__main__":
    main()
