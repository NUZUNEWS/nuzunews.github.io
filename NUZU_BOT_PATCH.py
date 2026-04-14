"""
NUZU_BOT_PATCH.py
─────────────────────────────────────────────────────────────────────────
This file contains EVERY addition needed to update bot.py.
Do NOT paste this file as-is — follow the step-by-step instructions below
to insert each block in the correct location in your existing bot.py.

CHANGES OVERVIEW
 1. Two new rendering functions  (add after source_summary_from_clusters)
 2. New CSS block               (add at the end of the <style> tag)
 3. Horoscope + Comic sections  (add after section-local block)
 4. Video Feed #8 URL fix       (two line changes)
 5. WR_FEEDS country labels     (replace 10 label strings in JS)
 6. Main-page country overlays  (update video-grid HTML)
─────────────────────────────────────────────────────────────────────────
"""

# ══════════════════════════════════════════════════════════════════════
# STEP 1 — Add these two functions to bot.py
#          Paste them AFTER the def source_summary_from_clusters() function
# ══════════════════════════════════════════════════════════════════════

STEP1_FUNCTIONS = '''
# ── Horoscope section renderer ─────────────────────────────────────
def render_horoscope_section():
    """Read horoscopes.json and return full HTML for the daily horoscope section."""
    import json, os
    if not os.path.exists('horoscopes.json'):
        return ''
    try:
        with open('horoscopes.json', encoding='utf-8') as _f:
            _data = json.load(_f)
    except Exception:
        return ''

    horoscopes = _data.get('horoscopes', [])
    updated    = _data.get('updated', '')
    if not horoscopes:
        return ''

    cards_html = ''
    for h in horoscopes:
        symbol  = h.get('symbol', '')
        name    = h.get('name', h.get('sign', '').title())
        dates   = h.get('dates', '')
        element = h.get('element', '')
        desc    = h.get('description', '')
        mood    = h.get('mood', '')
        lucky_n = h.get('lucky_number', '')
        lucky_c = h.get('lucky_color', '')
        compat  = h.get('compatibility', '')

        meta_parts = ''
        if mood:
            meta_parts += f'<span class="horo-meta-item"><span class="horo-meta-label">Mood</span>{mood}</span>'
        if lucky_n:
            meta_parts += f'<span class="horo-meta-item"><span class="horo-meta-label">Lucky&nbsp;#</span>{lucky_n}</span>'
        if lucky_c:
            meta_parts += f'<span class="horo-meta-item"><span class="horo-meta-label">Color</span>{lucky_c}</span>'
        if compat:
            meta_parts += f'<span class="horo-meta-item"><span class="horo-meta-label">✦</span>{compat}</span>'
        meta_html = f'<div class="horo-meta">{meta_parts}</div>' if meta_parts else ''

        elem_badge = f'<span class="horo-element horo-elem-{element.lower()}">{element}</span>' if element else ''

        cards_html += (
            f'<div class="horo-card">'
            f'<div class="horo-card-header">'
            f'<span class="horo-symbol" aria-label="{name}">{symbol}</span>'
            f'<div class="horo-sign-info">'
            f'<span class="horo-sign-name">{name}</span>'
            f'<span class="horo-dates">{dates}</span>'
            f'</div>'
            f'{elem_badge}'
            f'</div>'
            f'<p class="horo-desc">{desc}</p>'
            f'{meta_html}'
            f'</div>\\n'
        )

    updated_label = f' <span class="horo-updated">— {updated}</span>' if updated else ''

    return (
        f'<div id="section-horoscopes" class="section-wrap">\\n'
        f'<div class="section-banner horoscope-color-banner">'
        f'<div class="section-banner-inner">'
        f'<h2 class="section-title horoscope-color">'
        f'<span class="sec-dot" style="background:#7B5EA7"></span>'
        f'DAILY HOROSCOPES{updated_label}'
        f'</h2>'
        f'<button class="section-collapse-btn" data-target="section-horoscopes-cols" '
        f'aria-label="Collapse section" title="Collapse / expand">&#9660;</button>'
        f'</div></div>\\n'
        f'<div id="section-horoscopes-cols" class="section-columns">\\n'
        f'<div class="horo-grid">\\n'
        f'{cards_html}'
        f'</div>\\n'
        f'</div>\\n'
        f'</div>\\n'
    )


# ── Comic section renderer ──────────────────────────────────────────
def render_comic_section():
    """Read comics.rss and return full HTML for the daily classic comic section."""
    import feedparser, os
    if not os.path.exists('comics.rss'):
        return ''
    try:
        feed = feedparser.parse('comics.rss')
        if not feed.entries:
            return ''
        entry = feed.entries[0]
    except Exception:
        return ''

    raw_title = entry.get('title', 'Classic Comic of the Day')
    link      = entry.get('link', 'https://comicbookplus.com/?cid=6')
    raw_desc  = entry.get('summary', '')

    # Strip HTML from description for display
    import re as _re
    clean_desc = _re.sub(r'<[^>]+>', '', raw_desc).strip()

    # Parse title parts: "Classic PD Comic — Series — Strip"
    parts = [p.strip() for p in raw_title.split('—')]
    if len(parts) >= 3:
        series_name   = parts[1]
        display_title = parts[2]
    elif len(parts) == 2:
        series_name   = ''
        display_title = parts[1]
    else:
        series_name   = ''
        display_title = raw_title

    series_html = (
        f'<div class="comic-series-name">{series_name}</div>'
        if series_name else ''
    )
    desc_snippet = (clean_desc[:320] + '…') if len(clean_desc) > 320 else clean_desc

    return (
        f'<div id="section-comics" class="section-wrap">\\n'
        f'<div class="section-banner comics-color-banner">'
        f'<div class="section-banner-inner">'
        f'<h2 class="section-title comics-color">'
        f'<span class="sec-dot" style="background:#7C4A1E"></span>'
        f'CLASSIC COMIC OF THE DAY'
        f'</h2>'
        f'<button class="section-collapse-btn" data-target="section-comics-cols" '
        f'aria-label="Collapse section" title="Collapse / expand">&#9660;</button>'
        f'</div></div>\\n'
        f'<div id="section-comics-cols" class="section-columns">\\n'
        f'<div class="container" style="display:block;max-width:1400px;margin:0 auto;padding:16px 20px;">\\n'
        f'<div class="comic-card">\\n'
        f'<div class="comic-card-inner">\\n'
        f'<span class="comic-pd-badge">&#127381; Public Domain Archive</span>\\n'
        f'{series_html}'
        f'<h3 class="comic-title">{display_title}</h3>\\n'
        f'<p class="comic-desc">{desc_snippet}</p>\\n'
        f'<div class="comic-footer">\\n'
        f'<a href="{link}" target="_blank" rel="noopener noreferrer" class="comic-read-btn">'
        f'&#128214;&nbsp;Read This Strip&nbsp;&#8599;</a>\\n'
        f'<a href="https://comicbookplus.com/?cid=6" target="_blank" rel="noopener noreferrer" '
        f'class="comic-archive-link">Browse Full Archive &#8599;</a>\\n'
        f'</div>\\n'
        f'</div>\\n'
        f'<div class="comic-attribution">'
        f'All comics from <a href="https://comicbookplus.com" target="_blank" rel="noopener noreferrer">'
        f'ComicBookPlus.com</a> — a free archive of public-domain print history. '
        f'A different classic every day, cycling through 100+ series.'
        f'</div>\\n'
        f'</div>\\n'
        f'</div>\\n'
        f'</div>\\n'
        f'</div>\\n'
    )
'''

# ══════════════════════════════════════════════════════════════════════
# STEP 2 — New CSS
#          Paste this block INSIDE the existing <style>...</style> tag
#          in bot.py, just before the closing </style> line.
# ══════════════════════════════════════════════════════════════════════

STEP2_CSS = '''
    /* ═══════════════════════════════════════════════════════════════
       HOROSCOPE SECTION
    ═══════════════════════════════════════════════════════════════ */
    .horoscope-color-banner {{
        border-left: 4px solid #7B5EA7;
        background: linear-gradient(90deg, rgba(123,94,167,0.13) 0%, transparent 55%);
    }}
    .horoscope-color {{ color: #7B5EA7; }}

    .horo-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        max-width: 1400px;
        margin: 0 auto;
        padding: 14px 20px 20px;
    }}
    @media (max-width: 1280px) {{ .horo-grid {{ grid-template-columns: repeat(3, 1fr); }} }}
    @media (max-width:  900px) {{ .horo-grid {{ grid-template-columns: repeat(2, 1fr); padding: 12px; }} }}
    @media (max-width:  520px) {{ .horo-grid {{ grid-template-columns: 1fr; }} }}

    .horo-card {{
        background: var(--nuzu-card);
        border: 1px solid var(--nuzu-border);
        border-left: 3px solid #7B5EA7;
        border-radius: 6px;
        padding: 13px 15px 11px;
        transition: background 0.15s;
    }}
    .horo-card:hover {{ background: rgba(123,94,167,0.08); }}

    .horo-card-header {{
        display: flex;
        align-items: flex-start;
        gap: 9px;
        margin-bottom: 9px;
    }}
    .horo-symbol {{
        font-size: 1.65em;
        flex-shrink: 0;
        line-height: 1;
        margin-top: 1px;
    }}
    .horo-sign-info {{
        display: flex;
        flex-direction: column;
        flex: 1;
        min-width: 0;
    }}
    .horo-sign-name {{
        font-family: 'Playfair Display', Georgia, serif;
        font-weight: 700;
        color: var(--nuzu-white);
        font-size: 0.98em;
        line-height: 1.2;
    }}
    .horo-dates {{
        color: var(--nuzu-dim);
        font-size: 0.70em;
        letter-spacing: 0.02em;
        margin-top: 2px;
    }}
    .horo-element {{
        font-size: 0.62em;
        font-weight: bold;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 2px 7px;
        border-radius: 8px;
        flex-shrink: 0;
        align-self: flex-start;
        margin-top: 3px;
    }}
    .horo-elem-fire  {{ background: rgba(220,80,40,0.18);  color: #e06040; }}
    .horo-elem-earth {{ background: rgba(80,140,60,0.18);  color: #6aaa50; }}
    .horo-elem-air   {{ background: rgba(40,140,220,0.18); color: #50aaee; }}
    .horo-elem-water {{ background: rgba(40,80,200,0.18);  color: #608aee; }}

    .horo-desc {{
        color: var(--nuzu-text);
        font-size: 0.83em;
        line-height: 1.62;
        margin-bottom: 9px;
    }}
    .horo-meta {{
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        border-top: 1px solid var(--nuzu-border);
        padding-top: 8px;
    }}
    .horo-meta-item {{
        font-size: 0.70em;
        color: var(--nuzu-muted);
        background: var(--nuzu-border);
        padding: 2px 8px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        gap: 4px;
    }}
    .horo-meta-label {{
        color: #9B7ED5;
        font-weight: bold;
    }}
    .horo-updated {{
        font-size: 0.70em;
        font-weight: 400;
        color: var(--nuzu-dim);
        text-transform: none;
        letter-spacing: 0.04em;
    }}

    /* Light mode */
    body.light-mode .horo-card                     {{ background: #F7F3FF !important; border-left-color: #7B5EA7 !important; }}
    body.light-mode .horo-card:hover               {{ background: rgba(123,94,167,0.06) !important; }}
    body.light-mode .horoscope-color-banner        {{ background: linear-gradient(90deg, rgba(123,94,167,0.09) 0%, transparent 55%) !important; }}
    body.light-mode .horo-sign-name                {{ color: #1a1a1a !important; }}

    /* ═══════════════════════════════════════════════════════════════
       COMICS SECTION
    ═══════════════════════════════════════════════════════════════ */
    .comics-color-banner {{
        border-left: 4px solid #7C4A1E;
        background: linear-gradient(90deg, rgba(124,74,30,0.13) 0%, transparent 55%);
    }}
    .comics-color {{ color: #9A5A28; }}

    .comic-card {{
        background: var(--nuzu-card);
        border: 1px solid var(--nuzu-border);
        border-radius: 8px;
        overflow: hidden;
        max-width: 820px;
        margin: 0 auto;
    }}
    .comic-card-inner {{ padding: 22px 24px 18px; }}
    .comic-pd-badge {{
        display: inline-block;
        background: rgba(124,74,30,0.14);
        color: #9A5A28;
        font-size: 0.70em;
        font-weight: bold;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        padding: 3px 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        border: 1px solid rgba(124,74,30,0.28);
    }}
    .comic-series-name {{
        font-size: 0.78em;
        color: var(--nuzu-muted);
        margin-bottom: 4px;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }}
    .comic-title {{
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.38em;
        font-weight: 700;
        color: var(--nuzu-white);
        margin-bottom: 12px;
        line-height: 1.32;
    }}
    .comic-desc {{
        color: var(--nuzu-text);
        font-size: 0.87em;
        line-height: 1.70;
        margin-bottom: 18px;
    }}
    .comic-footer {{
        display: flex;
        align-items: center;
        gap: 18px;
        flex-wrap: wrap;
    }}
    .comic-read-btn {{
        display: inline-block;
        background: #7C4A1E;
        color: #fff !important;
        padding: 10px 22px;
        border-radius: 4px;
        text-decoration: none;
        font-size: 0.88em;
        font-weight: bold;
        letter-spacing: 0.03em;
        transition: background 0.15s;
    }}
    .comic-read-btn:hover {{ background: #9A5A28; }}
    .comic-archive-link {{
        color: var(--nuzu-muted);
        font-size: 0.80em;
        text-decoration: underline;
        transition: color 0.15s;
    }}
    .comic-archive-link:hover {{ color: var(--nuzu-white); }}
    .comic-attribution {{
        background: rgba(124,74,30,0.07);
        border-top: 1px solid var(--nuzu-border);
        padding: 10px 24px;
        font-size: 0.76em;
        color: var(--nuzu-dim);
        line-height: 1.6;
    }}
    .comic-attribution a {{ color: #9A5A28; text-decoration: underline; }}
    .comic-attribution a:hover {{ color: var(--nuzu-white); }}

    /* Light mode */
    body.light-mode .comic-card            {{ background: #FDF9F5 !important; }}
    body.light-mode .comic-title           {{ color: #2a1500 !important; }}
    body.light-mode .comic-pd-badge        {{ background: rgba(124,74,30,0.09) !important; }}
    body.light-mode .comic-attribution    {{ background: rgba(124,74,30,0.05) !important; }}
    body.light-mode .comics-color-banner   {{ background: linear-gradient(90deg, rgba(124,74,30,0.09) 0%, transparent 55%) !important; }}

    /* ═══════════════════════════════════════════════════════════════
       VIDEO FEED COUNTRY LABELS
    ═══════════════════════════════════════════════════════════════ */
    .youtube-inset {{ position: relative; }}

    /* Main-page desktop labels */
    .feed-country-label {{
        position: absolute;
        bottom: 7px;
        left: 7px;
        background: rgba(0, 0, 0, 0.58);
        color: rgba(255,255,255,0.88);
        font-family: 'Inter', Arial, sans-serif;
        font-size: 0.58em;
        font-weight: 700;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        padding: 3px 8px;
        border-radius: 3px;
        pointer-events: none;
        user-select: none;
        backdrop-filter: blur(3px);
        -webkit-backdrop-filter: blur(3px);
        transition: opacity 0.2s;
        z-index: 2;
    }}
    .youtube-inset:hover .feed-country-label {{ opacity: 0.35; }}
    @media (max-width: 900px) {{ .feed-country-label {{ display: none !important; }} }}

    /* Waiting-room cell number now repurposed as country name — styled wider */
    #wr-grid .wr-cell-num {{
        font-size: 0.66em;
        letter-spacing: 0.06em;
        padding: 3px 9px;
        min-width: 60px;
        text-align: center;
    }}
'''

# ══════════════════════════════════════════════════════════════════════
# STEP 3 — Add the horoscope and comic sections to HTML output
#
# In bot.py, find the block that renders the local section:
#   html_parts.append('''
#   <hr class="top-divider">
#   <div id="section-local" ...>
#     ...
#   </div>
#   ''')
#
# AFTER that entire block, add the following:
# ══════════════════════════════════════════════════════════════════════

STEP3_SECTION_APPEND = '''
# ── Horoscope section ─────────────────────────────────────────────
_horo_html = render_horoscope_section()
if _horo_html:
    html_parts.append('<hr class="top-divider">\\n')
    html_parts.append(_horo_html)

# ── Comic section (always last) ────────────────────────────────────
_comic_html = render_comic_section()
if _comic_html:
    html_parts.append('<hr class="top-divider">\\n')
    html_parts.append(_comic_html)
'''

# ══════════════════════════════════════════════════════════════════════
# STEP 4 — VIDEO FEED #8 URL FIX
#
# In bot.py, find these two URL occurrences and change them:
#   OLD: iEpJwprxDdk
#   NEW: fO9e9jnhYK8
#
# They appear in:
#   a) The MAIN_FEED_SRCS JavaScript array (8th item, index 7)
#   b) The WR_FEEDS JavaScript array (8th item, index 7)
#   c) The static HTML video-grid <iframe> (8th .youtube-inset div)
# ══════════════════════════════════════════════════════════════════════

STEP4_URL_CHANGE = "Replace ALL occurrences of 'iEpJwprxDdk' with 'fO9e9jnhYK8'"

# ══════════════════════════════════════════════════════════════════════
# STEP 5 — WR_FEEDS country labels
#
# In bot.py, find the WR_FEEDS JavaScript array inside the f-string
# section. Replace the label values as follows:
# ══════════════════════════════════════════════════════════════════════

STEP5_WR_FEEDS = """
Replace this in bot.py (inside the large JS f-string):

    var WR_FEEDS = [
      {{src:'https://...iipR5yUp36o...',label:'Feed 1'}},
      {{src:'https://...Ap-UM1O9RBU...',label:'Feed 2'}},
      {{src:'https://...QliL4CGc7iY...',label:'Feed 3'}},
      {{src:'https://...pykpO5kQJ98...',label:'Feed 4'}},
      {{src:'https://...YDvsBbKfLPA...',label:'Feed 5'}},
      {{src:'https://...vfszY1JYbMc...',label:'Feed 6'}},
      {{src:'https://..._6dRRfnYJws...',label:'Feed 7'}},
      {{src:'https://...iEpJwprxDdk...',label:'Feed 8'}},   ← also change URL
      {{src:'https://...LuKwFajn37U...',label:'Feed 9'}},
      {{src:'https://...UCNye-wNBqNL5ZzHSJj3l8Bg...',label:'Feed 10'}}
    ];

WITH THIS (update labels + fix URL for #8):

    var WR_FEEDS = [
      {{src:'https://...iipR5yUp36o...',  label:'United States'}},
      {{src:'https://...Ap-UM1O9RBU...',  label:'France'}},
      {{src:'https://...QliL4CGc7iY...',  label:'England'}},
      {{src:'https://...pykpO5kQJ98...',  label:'Europe'}},
      {{src:'https://...YDvsBbKfLPA...',  label:'Australia'}},
      {{src:'https://...vfszY1JYbMc...',  label:'India'}},
      {{src:'https://..._6dRRfnYJws...',  label:'China'}},
      {{src:'https://...fO9e9jnhYK8...',  label:'Earth'}},     ← new URL + label
      {{src:'https://...LuKwFajn37U...',  label:'Germany'}},
      {{src:'https://...UCNye-wNBqNL5ZzHSJj3l8Bg...', label:'Middle East'}}
    ];

Keep all the ?autoplay=1&mute=1&controls=1&... query parameters unchanged.
Only change the label strings and the Feed 8 video ID.
"""

# ══════════════════════════════════════════════════════════════════════
# STEP 6 — Add country labels to the static video grid HTML
#
# In bot.py, find the <!-- VIDEO BANNER desktop only --> block.
# Each <div class="youtube-inset"> needs a .feed-country-label added.
# Replace the existing video-grid block with the one below.
# ══════════════════════════════════════════════════════════════════════

STEP6_VIDEO_HTML = '''ts_html += """<!-- VIDEO BANNER desktop only -->
<div class="banner">
  <div class="video-grid">
    <div class="youtube-inset">
      <iframe data-src="https://www.youtube.com/embed/iipR5yUp36o?autoplay=1&mute=1&controls=1&modestbranding=1&rel=0&iv_load_policy=3&playsinline=1" allow="autoplay;encrypted-media" allowfullscreen></iframe>
      <span class="feed-country-label">United States</span>
    </div>
    <div class="youtube-inset">
      <iframe data-src="https://www.youtube.com/embed/Ap-UM1O9RBU?autoplay=1&mute=1&controls=1&modestbranding=1&rel=0&iv_load_policy=3&playsinline=1" allow="autoplay;encrypted-media" allowfullscreen></iframe>
      <span class="feed-country-label">France</span>
    </div>
    <div class="youtube-inset">
      <iframe data-src="https://www.youtube.com/embed/QliL4CGc7iY?autoplay=1&mute=1&controls=1&modestbranding=1&rel=0&iv_load_policy=3&playsinline=1" allow="autoplay;encrypted-media" allowfullscreen></iframe>
      <span class="feed-country-label">England</span>
    </div>
    <div class="youtube-inset">
      <iframe data-src="https://www.youtube.com/embed/pykpO5kQJ98?autoplay=1&mute=1&controls=1&modestbranding=1&rel=0&iv_load_policy=3&playsinline=1" allow="autoplay;encrypted-media" allowfullscreen></iframe>
      <span class="feed-country-label">Europe</span>
    </div>
    <div class="youtube-inset">
      <iframe data-src="https://www.youtube.com/embed/YDvsBbKfLPA?autoplay=1&mute=1&controls=1&modestbranding=1&rel=0&iv_load_policy=3&playsinline=1" allow="autoplay;encrypted-media" allowfullscreen></iframe>
      <span class="feed-country-label">Australia</span>
    </div>
    <div class="youtube-inset">
      <iframe data-src="https://www.youtube.com/embed/vfszY1JYbMc?autoplay=1&mute=1&controls=1&modestbranding=1&rel=0&iv_load_policy=3&playsinline=1" allow="autoplay;encrypted-media" allowfullscreen></iframe>
      <span class="feed-country-label">India</span>
    </div>
    <div class="youtube-inset">
      <iframe data-src="https://www.youtube.com/embed/_6dRRfnYJws?autoplay=1&mute=1&controls=1&modestbranding=1&rel=0&iv_load_policy=3&playsinline=1" allow="autoplay;encrypted-media" allowfullscreen></iframe>
      <span class="feed-country-label">China</span>
    </div>
    <div class="youtube-inset">
      <iframe data-src="https://www.youtube.com/embed/fO9e9jnhYK8?autoplay=1&mute=1&controls=1&modestbranding=1&rel=0&iv_load_policy=3&playsinline=1" allow="autoplay;encrypted-media" allowfullscreen></iframe>
      <span class="feed-country-label">Earth</span>
    </div>
    <div class="youtube-inset">
      <iframe data-src="https://www.youtube.com/embed/LuKwFajn37U?autoplay=1&mute=1&controls=1&modestbranding=1&rel=0&iv_load_policy=3&playsinline=1" allow="autoplay;encrypted-media" allowfullscreen></iframe>
      <span class="feed-country-label">Germany</span>
    </div>
    <div class="youtube-inset">
      <iframe data-src="https://www.youtube.com/embed/live_stream?channel=UCNye-wNBqNL5ZzHSJj3l8Bg&autoplay=1&mute=1&controls=1&modestbranding=1&rel=0&iv_load_policy=3&playsinline=1" allow="autoplay;encrypted-media" allowfullscreen></iframe>
      <span class="feed-country-label">Middle East</span>
    </div>
  </div>
</div>\\n"""
'''

# ══════════════════════════════════════════════════════════════════════
# STEP 7 — Also update MAIN_FEED_SRCS in the JS f-string
#          Find the 8th entry (index 7) in MAIN_FEED_SRCS and change:
#            iEpJwprxDdk  →  fO9e9jnhYK8
# ══════════════════════════════════════════════════════════════════════

STEP7_MAIN_FEED_SRCS = """
In the large JS f-string block, find:
  'https://www.youtube.com/embed/iEpJwprxDdk?...',

And replace with:
  'https://www.youtube.com/embed/fO9e9jnhYK8?...',

Keep all query parameters identical (autoplay=1&mute=1&controls=1&...).
"""

# ══════════════════════════════════════════════════════════════════════
# DEPLOYMENT CHECKLIST
# ══════════════════════════════════════════════════════════════════════
DEPLOYMENT_CHECKLIST = """
DEPLOYMENT CHECKLIST
────────────────────
1. Add generate_horoscopes.py to repo root
2. Add build_comic_playlist.py to repo root
3. Add generate_comic_rss.py to repo root
4. Add .github/workflows/daily-content.yml
5. Add .github/workflows/monthly-comic-playlist.yml
6. Apply all 7 steps above to bot.py
7. Run build_comic_playlist.py once locally (or trigger monthly workflow)
8. Run generate_horoscopes.py once locally (or trigger daily workflow)
9. Run bot.py locally to verify output
10. Commit everything and push
11. In GitHub Actions UI → Run workflow on "NUZU Daily Content Update"
    to verify the pipeline runs end-to-end

FIRST RUN ORDER (local):
  pip install requests beautifulsoup4 feedparser
  python build_comic_playlist.py   # builds comic_playlist.json
  python generate_horoscopes.py    # builds horoscopes.json
  python generate_comic_rss.py     # builds comics.rss
  python bot.py                    # builds index.html

GITHUB ACTIONS ORDER (automated, daily):
  generate_horoscopes.py → generate_comic_rss.py → bot.py → commit
"""

if __name__ == '__main__':
    print("This file is a patch guide, not executable.")
    print("Follow the STEPS above to update bot.py.")
    print(DEPLOYMENT_CHECKLIST)
