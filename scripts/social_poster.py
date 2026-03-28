# Inside main(), after reading CSV
for i, post in enumerate(posts):
    # Skip if already posted
    if post.get('status') == 'posted':
        continue
    
    # Skip if not approved
    if post.get('status') != 'approved':
        continue
    
    # Rest of the posting logic...
