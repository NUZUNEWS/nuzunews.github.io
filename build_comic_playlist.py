"""
build_comic_playlist.py
NUZU News — Public Domain Comic Playlist Builder
Scrapes ComicBookPlus.com's Public Domain Comic Strips category and builds
a sequential master playlist. Run monthly (or manually) via GitHub Actions.

All comics are confirmed public domain — safe to reference and link.
Source: https://comicbookplus.com/?cid=6
"""

import json
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import date

BASE = "https://comicbookplus.com"
CATEGORY_URL = f"{BASE}/?cid=6"
FALLBACK_URL = f"{BASE}/?cbplus=humor"

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (compatible; NUZUNewsBot/1.0; '
        '+https://nuzunews.github.io)'
    )
}


def get_page(url, retries=3):
    """Fetch a URL with retries and polite delays."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            if resp.status_code == 200:
                return resp.text
            print(f"  HTTP {resp.status_code} for {url}")
        except Exception as e:
            print(f"  Request error (attempt {attempt+1}): {e}")
        time.sleep(2 ** attempt)
    return None


def extract_items_from_page(html, source_label=""):
    """
    Extract all comic items (dlid links) from a category or listing page.
    Returns list of {title, dlid, url} dicts.
    """
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    seen_dlids = set()

    for a in soup.find_all('a', href=True):
        href = a['href']
        m = re.search(r'[?&]dlid=(\d+)', href)
        if not m:
            continue
        dlid = m.group(1)
        if dlid in seen_dlids:
            continue
        title = a.get_text(strip=True)
        if not title or len(title) < 3:
            continue
        # Skip pagination/nav links
        if title.lower() in ('next', 'prev', 'previous', 'first', 'last', '»', '«'):
            continue
        seen_dlids.add(dlid)
        full_url = f"{BASE}/?dlid={dlid}"
        items.append({'title': title, 'dlid': dlid, 'url': full_url})

    return items


def get_all_pages(start_url):
    """
    Scrape all paginated pages of a category and return merged item list.
    ComicBookPlus uses ?cid=X&page=N style pagination.
    """
    all_items = []
    seen_dlids = set()
    page_num = 1
    base_category = start_url.split('?')[0] + '?' + start_url.split('?')[1].split('&page=')[0]

    while True:
        url = f"{base_category}&page={page_num}" if page_num > 1 else start_url
        print(f"  Fetching page {page_num}: {url}")
        html = get_page(url)
        if not html:
            print(f"  Could not fetch page {page_num}, stopping.")
            break

        items = extract_items_from_page(html)
        new_items = [i for i in items if i['dlid'] not in seen_dlids]

        if not new_items:
            print(f"  No new items on page {page_num} — reached end.")
            break

        for item in new_items:
            seen_dlids.add(item['dlid'])
        all_items.extend(new_items)
        print(f"  → {len(new_items)} items (total so far: {len(all_items)})")

        # Check if there's a next page link
        soup = BeautifulSoup(html, 'html.parser')
        next_links = [a for a in soup.find_all('a', href=True)
                      if 'next' in a.get_text(strip=True).lower()
                      or f'page={page_num+1}' in a['href']]
        if not next_links:
            break

        page_num += 1
        time.sleep(1.5)

    return all_items


def build_playlist():
    """Main function: scrape category and build ordered playlist."""
    print(f"Building comic playlist from: {CATEGORY_URL}")
    print(f"Date: {date.today()}")
    print("-" * 60)

    # Primary source: Public Domain Comic Strips (cid=6)
    items = get_all_pages(CATEGORY_URL)

    # If primary fails or returns too few items, try fallback
    if len(items) < 5:
        print(f"\nPrimary source returned only {len(items)} items.")
        print(f"Trying fallback: {FALLBACK_URL}")
        fallback_html = get_page(FALLBACK_URL)
        if fallback_html:
            fallback_items = extract_items_from_page(fallback_html)
            existing_dlids = {i['dlid'] for i in items}
            new_fallback = [i for i in fallback_items if i['dlid'] not in existing_dlids]
            items.extend(new_fallback)
            print(f"  Added {len(new_fallback)} items from fallback.")

    if not items:
        print("\n❌ ERROR: No items found. Site structure may have changed.")
        print("Manual check required: https://comicbookplus.com/?cid=6")
        return

    # Build final playlist
    playlist = {
        'built': str(date.today()),
        'source': CATEGORY_URL,
        'total': len(items),
        'strips': [
            {
                'title': item['title'],
                'dlid': item['dlid'],
                'url': item['url'],
            }
            for item in items
        ]
    }

    with open('comic_playlist.json', 'w', encoding='utf-8') as f:
        json.dump(playlist, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Playlist built: {len(items)} comics")
    print(f"   Saved to comic_playlist.json")
    print(f"\nSample items:")
    for item in items[:5]:
        print(f"  • [{item['dlid']}] {item['title']}")
    if len(items) > 5:
        print(f"  ... and {len(items) - 5} more")


if __name__ == '__main__':
    build_playlist()
