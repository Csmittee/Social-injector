name: Social Poster

on:
  # Run every 30 minutes (for testing)
  schedule:
    - cron: '*/30 * * * *'
  
  # Allow manual trigger from GitHub
  workflow_dispatch:

jobs:
  post:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}   # Needed for pushing changes

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies (if any)
        run: |
          pip install requests   # Add more packages if your poster needs them

      - name: Run Social Poster
        run: python scripts/social_poster.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # Add your social media tokens here later:
          # FB_ACCESS_TOKEN: ${{ secrets.FB_ACCESS_TOKEN }}
          # IG_ACCESS_TOKEN: ${{ secrets.IG_ACCESS_TOKEN }}

      - name: Commit and push status changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          
          git add social/posts.csv
          
          # Only commit if there are actual changes
          if git diff --cached --quiet; then
            echo "No changes to commit."
          else
            git commit -m "Update post status to 'posted' [skip ci]"
            git push
          fi
