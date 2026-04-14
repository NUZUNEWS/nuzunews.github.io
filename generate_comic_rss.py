"""
generate_comic_rss.py
NUZU News — Daily Classic Comic RSS Generator
Reads comic_playlist.json and writes comics.rss with today's selection.
Uses days-since-epoch math for perfectly deterministic daily cycling.
Run once per day via GitHub Actions before bot.py.
"""

import json
import os
from datetime import date
from email.utils import formatdate
import xml.sax.saxutils as saxutils

# ── Epoch: first day of playlist cycling ──────────────────────────────────
# Change this only if you want to reset the cycle.
PLAYLIST_EPOCH = date(2025, 1, 1)

PLAYLIST_FILE = 'comic_playlist.json'
OUTPUT_FILE = 'comics.rss'


def load_playlist():
    if not os.path.exists(PLAYLIST_FILE):
        print(f"❌ {PLAYLIST_FILE} not found.")
        print("   Run build_comic_playlist.py first.")
        return None

    with open(PLAYLIST_FILE, encoding='utf-8') as f:
        data = json.load(f)

    strips = data.get('strips', [])
    if not strips:
        print(f"❌ Playlist is empty. Rebuild with build_comic_playlist.py.")
        return None

    return strips


def pick_todays_strip(strips):
    today = date.today()
    days_elapsed = (today - PLAYLIST_EPOCH).days
    idx = days_elapsed % len(strips)
    strip = strips[idx]
    print(f"Today: {today}")
    print(f"Days since epoch: {days_elapsed}")
    print(f"Playlist size: {len(strips)}")
    print(f"Selected index: {idx} → \"{strip['title']}\"")
    return strip, idx


def xml_escape(s):
    return saxutils.escape(str(s))


def generate_rss(strip, idx, total):
    today = date.today()
    pub_date = formatdate(usegmt=True)

    title = strip['title']
    link = strip['url']

    # Build a clean RSS title
    rss_title = f"Classic PD Comic — {xml_escape(title)}"

    # Build a descriptive blurb
    description = (
        f"Today's public-domain classic: <strong>{xml_escape(title)}</strong>. "
        f"Strip {idx + 1} of {total} in the NUZU rotating archive. "
        f"All comics from <a href=\"https://comicbookplus.com/?cid=6\">"
        f"ComicBookPlus.com</a> — a free repository of public-domain comic history. "
        f"New classic every day."
    )

    rss_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>NUZU Classic Comic of the Day</title>
    <link>https://comicbookplus.com/?cid=6</link>
    <atom:link href="https://nuzunews.github.io/comics.rss" rel="self" type="application/rss+xml"/>
    <description>Daily rotating public-domain classic comic strips from ComicBookPlus.com, curated by NUZU News.</description>
    <language>en-us</language>
    <copyright>Public Domain — no rights reserved</copyright>
    <lastBuildDate>{pub_date}</lastBuildDate>
    <ttl>1440</ttl>
    <item>
      <title>{rss_title}</title>
      <link>{xml_escape(link)}</link>
      <guid isPermaLink="true">{xml_escape(link)}</guid>
      <description><![CDATA[{description}]]></description>
      <pubDate>{pub_date}</pubDate>
    </item>
  </channel>
</rss>'''

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(rss_content)

    print(f"✅ Written to {OUTPUT_FILE}")
    return strip


def main():
    print("NUZU Daily Comic Generator")
    print("=" * 40)

    strips = load_playlist()
    if not strips:
        return

    strip, idx = pick_todays_strip(strips)
    generate_rss(strip, idx, len(strips))
    print(f"\nURL: {strip['url']}")


if __name__ == '__main__':
    main()
