# -*- coding: utf-8 -*-
"""
NUZU ORIGINALS — in-house article / byline system.
═══════════════════════════════════════════════════════════════════════════════

WHAT THIS IS
    A completely self-contained module that turns plain-text article files in
    the `articles/` folder into:
      1. Featured "NUZU ORIGINALS" strip near the top of the homepage
      2. Native-looking cards inside the matching news section
      3. `originals.html`      — the Sean Mitchell byline / author hub page
      4. `originals/<slug>.html` — a full newspaper-style page per article

WHY IT IS A SEPARATE MODULE
    bot.py is ~488 KB and assembles the whole page as one giant f-string. Adding
    800 lines there risks brace-escaping bugs and surrogate crashes. Keeping the
    engine here means:
      * bot.py needs only a handful of tiny hooks
      * this file can be tested on its own (`python nuzu_originals.py --selftest`)
      * if this file is missing or raises, bot.py degrades to the old behaviour
        and the site still builds. Nothing here can take the site down.

SURROGATE SAFETY (see bot.py header)
    NO \\uXXXX escapes anywhere in this file. Emoji / symbols are emitted as HTML
    numeric entities only. This is the rule that has broken past builds.

AUTHORING FORMAT — articles/<anything>.txt
    ---------------------------------------------------------------
    title: The Quiet Collapse of the Local Newsroom
    subtitle: Four hundred counties now have no daily paper
    section: us
    author: Sean Mitchell
    published: 2026-08-04 09:00
    featured: yes
    tags: media, democracy
    summary: One or two sentences shown on the card.
    ---
    Body starts after the three dashes. Just write normally.

    A blank line starts a new paragraph.

    ## A subheading
    > A pull quote.
    - A bullet
    ---------------------------------------------------------------
"""

import os
import re
import html as _html
import unicodedata
from datetime import datetime, timedelta

__all__ = [
    "load_articles", "originals_css", "render_featured_strip",
    "render_section_originals", "write_originals_pages",
    "nav_link_html", "footer_links_html", "has_articles",
]

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

ARTICLES_DIR   = "articles"          # where you drop your .txt files
OUT_HUB        = "originals.html"    # the byline / author hub page
OUT_DIR        = "originals"         # per-article pages live here
SITE_BASE_URL  = "https://nuzunews.github.io/"
DEFAULT_AUTHOR = "Sean Mitchell"
PDT_OFFSET     = timedelta(hours=-7)

# The house gold. Used for every in-house byline so an original is instantly
# recognisable against the aggregated feed.
GOLD       = "#C9A227"
GOLD_LIGHT = "#E3C15A"
GOLD_DEEP  = "#8A6D12"

VALID_SECTIONS = {
    "us":       ("US",          "#C0392B", "section-us"),
    "mideast":  ("Middle East", "#D35400", "section-mideast"),
    "world":    ("World",       "#1A6FA8", "section-world"),
    "tech":     ("Tech",        "#1E4FD8", "section-tech"),
    "business": ("Business",    "#8B6914", "section-business"),
    "sports":   ("Sports",      "#1A7A4A", "section-sports"),
    "culture":  ("Culture",     "#7B2D8B", "section-culture"),
}

# Friendly aliases so a typo in the section field still lands somewhere sane.
_SECTION_ALIASES = {
    "u.s.": "us", "usa": "us", "america": "us", "domestic": "us", "politics": "us",
    "middle east": "mideast", "middle-east": "mideast", "me": "mideast",
    "international": "world", "global": "world", "foreign": "world",
    "technology": "tech", "science": "tech", "ai": "tech",
    "finance": "business", "economy": "business", "markets": "business",
    "sport": "sports",
    "arts": "culture", "entertainment": "culture", "opinion": "culture",
}


# ─────────────────────────────────────────────────────────────────────────────
# SMALL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _esc(s):
    """HTML-escape. Always applied BEFORE inline markdown so tags cannot inject."""
    return _html.escape(str(s or ""), quote=True)


def _strip_surrogates(text):
    """Last line of defence — mirrors bot.py's nz_safe_text()."""
    try:
        text.encode("utf-8")
        return text
    except UnicodeEncodeError:
        return "".join(ch for ch in text if not (0xD800 <= ord(ch) <= 0xDFFF))


def slugify(value, fallback="article"):
    """URL-safe slug. ASCII only, so the filename is never a surprise."""
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = value.encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    value = re.sub(r"-{2,}", "-", value)
    return (value or fallback)[:80]


def _parse_date(raw):
    """Accept the handful of date shapes a human actually types."""
    raw = (raw or "").strip()
    if not raw:
        return datetime.utcnow()
    raw = raw.replace("T", " ").replace("Z", "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                "%m/%d/%Y %H:%M", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return datetime.utcnow()


def _truthy(raw):
    return str(raw or "").strip().lower() in {"yes", "y", "true", "1", "on", "featured"}


def _fmt_date(dt):
    """'August 4, 2026' with no platform-specific strftime flags."""
    return "%s %d, %d" % (dt.strftime("%B"), dt.day, dt.year)


def _fmt_datetime(dt):
    hour = dt.hour % 12 or 12
    ampm = "AM" if dt.hour < 12 else "PM"
    return "%s %d, %d at %d:%02d %s PDT" % (
        dt.strftime("%B"), dt.day, dt.year, hour, dt.minute, ampm)


def _reading_time(text):
    words = len(re.findall(r"\S+", text))
    return max(1, round(words / 200.0))


# ─────────────────────────────────────────────────────────────────────────────
# BODY MARKDOWN  (deliberately tiny — everything a news article actually needs)
# ─────────────────────────────────────────────────────────────────────────────

def _inline(text):
    """Inline markdown. Input is ALREADY html-escaped, so this only adds tags."""
    # `code`
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # **bold** then *italic* (bold first so ** is not eaten by the * rule)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    # [label](https://url) — http/https/relative only, so no javascript: URIs
    def _link(m):
        label, url = m.group(1), m.group(2)
        if not re.match(r"^(https?://|/|\#)", url):
            return label
        ext = ' target="_blank" rel="noopener noreferrer"' if url.startswith("http") else ""
        return '<a href="%s"%s>%s</a>' % (url, ext, label)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", _link, text)
    return text


# ─────────────────────────────────────────────────────────────────────────────
# VIDEO
# ─────────────────────────────────────────────────────────────────────────────

_YT_PATTERNS = [
    r"(?:youtube\.com|youtube-nocookie\.com)/watch\?(?:.*&)?v=([A-Za-z0-9_-]{11})",
    r"youtu\.be/([A-Za-z0-9_-]{11})",
    r"(?:youtube\.com|youtube-nocookie\.com)/embed/([A-Za-z0-9_-]{11})",
    r"(?:youtube\.com|youtube-nocookie\.com)/shorts/([A-Za-z0-9_-]{11})",
    r"(?:youtube\.com|youtube-nocookie\.com)/live/([A-Za-z0-9_-]{11})",
]


def youtube_id(raw):
    """
    Pull an 11-character YouTube id out of whatever the author pasted.
    Accepts full watch URLs, youtu.be short links, embed/shorts/live URLs,
    or a bare id. Returns None if nothing usable is found.
    """
    raw = (raw or "").strip()
    if not raw:
        return None
    for pat in _YT_PATTERNS:
        m = re.search(pat, raw)
        if m:
            return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", raw):
        return raw
    return None


def _video_embed(vid, caption="", lazy=True):
    """
    Responsive 16:9 YouTube embed.

    Deliberately NO enablejsapi=1 here. On this site that parameter wakes the
    YouTube Player API and has previously activated dormant timers and state
    listeners on the video wall. Article embeds need none of that, so they stay
    plain and inert.

    Uses youtube-nocookie.com so a reader who never presses play is not tracked.
    """
    cap = ('<figcaption class="nzo-figcap">%s</figcaption>' % _inline(_esc(caption))) if caption else ""
    return (
        '<figure class="nzo-video">'
        '<div class="nzo-video-frame">'
        '<iframe src="https://www.youtube-nocookie.com/embed/%s?rel=0" '
        'title="%s" frameborder="0" %s'
        'allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
        'gyroscope; picture-in-picture; web-share" '
        'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>'
        '</div>%s</figure>'
        % (_esc(vid), _esc(caption or "Video"),
           'loading="lazy" ' if lazy else "", cap)
    )


# ─────────────────────────────────────────────────────────────────────────────
# DROP CAP
# ─────────────────────────────────────────────────────────────────────────────

def _apply_dropcap(body_html):
    """
    Wrap the first character of the first paragraph in an explicit span.

    The old approach leaned on ::first-letter with :first-of-type, which only
    fires when the opening element happens to be a plain paragraph. Any article
    that led with a heading, a pull quote or an image either lost the drop cap
    entirely or had it land halfway down the page.

    Doing it in the markup makes it deterministic: the gold capital always sits
    on the first paragraph, whatever comes before it.
    """
    m = re.search(r'<p class="nzo-p">\s*(&[a-zA-Z]+;|&#\d+;|[^\s<&])', body_html)
    if not m:
        return body_html
    ch = m.group(1)
    start, end = m.start(), m.end()
    return (body_html[:start]
            + '<p class="nzo-p"><span class="nzo-dropcap">' + ch + '</span>'
            + body_html[end:])


def _render_body(raw_body):
    """Plain text -> article HTML. Blank line separates blocks."""
    blocks, out = re.split(r"\n\s*\n", (raw_body or "").strip()), []
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Horizontal rule
        if re.fullmatch(r"[-*_]{3,}", block):
            out.append('<hr class="nzo-rule">')
            continue

        # Video:  [video: URL]  or  [video: URL | Caption]
        m = re.fullmatch(r"\[video:\s*([^\]|]+?)(?:\s*\|\s*(.+?))?\s*\]", block, re.I)
        if m:
            vid = youtube_id(m.group(1))
            if vid:
                out.append(_video_embed(vid, (m.group(2) or "").strip()))
                continue

        # A bare YouTube link on its own line becomes an embed. Authors paste
        # links far more often than they remember bespoke syntax.
        if "\n" not in block:
            vid = youtube_id(block)
            if vid and (block.startswith("http") or re.fullmatch(r"[A-Za-z0-9_-]{11}", block)):
                out.append(_video_embed(vid))
                continue

        lines = block.split("\n")

        # Bullet list
        if all(re.match(r"^\s*[-*+]\s+", ln) for ln in lines):
            items = "".join(
                "<li>%s</li>" % _inline(_esc(re.sub(r"^\s*[-*+]\s+", "", ln)))
                for ln in lines)
            out.append("<ul class=\"nzo-list\">%s</ul>" % items)
            continue

        # Numbered list
        if all(re.match(r"^\s*\d+[.)]\s+", ln) for ln in lines):
            items = "".join(
                "<li>%s</li>" % _inline(_esc(re.sub(r"^\s*\d+[.)]\s+", "", ln)))
                for ln in lines)
            out.append("<ol class=\"nzo-list\">%s</ol>" % items)
            continue

        # Blockquote / pull quote
        if all(ln.lstrip().startswith(">") for ln in lines):
            body = " ".join(re.sub(r"^\s*>\s?", "", ln) for ln in lines)
            cite = ""
            m = re.search(r"\s+--\s*(.+)$", body)
            if m:
                cite = '<cite class="nzo-cite">%s</cite>' % _inline(_esc(m.group(1).strip()))
                body = body[:m.start()]
            out.append('<blockquote class="nzo-quote">%s%s</blockquote>'
                       % (_inline(_esc(body.strip())), cite))
            continue

        # Headings
        m = re.match(r"^(#{2,4})\s+(.*)$", lines[0])
        if m and len(lines) == 1:
            level = min(len(m.group(1)), 4)
            out.append('<h%d class="nzo-h%d">%s</h%d>'
                       % (level, level, _inline(_esc(m.group(2).strip())), level))
            continue

        # Image  ![caption](url)
        m = re.fullmatch(r"!\[([^\]]*)\]\(([^)\s]+)\)", block)
        if m:
            cap, src = m.group(1), m.group(2)
            if re.match(r"^(https?://|/)", src):
                cap_html = ('<figcaption class="nzo-figcap">%s</figcaption>'
                            % _inline(_esc(cap))) if cap else ""
                out.append('<figure class="nzo-figure">'
                           '<img src="%s" alt="%s" loading="lazy">%s</figure>'
                           % (_esc(src), _esc(cap), cap_html))
                continue

        # Default: paragraph (single newlines become spaces)
        out.append('<p class="nzo-p">%s</p>' % _inline(_esc(" ".join(lines))))

    return _apply_dropcap("\n".join(out))


# ─────────────────────────────────────────────────────────────────────────────
# LOADING
# ─────────────────────────────────────────────────────────────────────────────

def _parse_article_file(path):
    """Parse one article file. Returns a dict, or None if unusable."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
    except Exception as e:
        print("  [originals] SKIP %s - unreadable: %s" % (path, e))
        return None

    raw = raw.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")

    # Split front matter from body on the first standalone --- line.
    parts = re.split(r"^\s*---\s*$", raw, maxsplit=1, flags=re.MULTILINE)
    if len(parts) == 2:
        fm_raw, body_raw = parts
    else:
        fm_raw, body_raw = raw, ""

    meta = {}
    for line in fm_raw.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        meta[key.strip().lower()] = val.strip()

    title = meta.get("title", "").strip()
    if not title:
        print("  [originals] SKIP %s - no title:" % path)
        return None
    if not body_raw.strip():
        print("  [originals] SKIP %s - empty body (is the --- separator there?)" % path)
        return None

    # Section normalisation
    sec = (meta.get("section", "") or "").strip().lower()
    sec = _SECTION_ALIASES.get(sec, sec)
    if sec not in VALID_SECTIONS:
        if sec:
            print("  [originals] '%s' has unknown section '%s' - filing under Culture"
                  % (os.path.basename(path), sec))
        sec = "culture"

    published = _parse_date(meta.get("published") or meta.get("date"))
    slug = slugify(meta.get("slug") or title)

    body_html = _render_body(body_raw)
    plain = re.sub(r"<[^>]+>", " ", body_html)

    summary = (meta.get("summary") or meta.get("dek") or "").strip()
    if not summary:
        first_p = re.search(r'<p class="nzo-p">(.*?)</p>', body_html, re.S)
        summary = re.sub(r"<[^>]+>", "", first_p.group(1)).strip() if first_p else ""
    if len(summary) > 240:
        summary = summary[:237].rsplit(" ", 1)[0] + "..."

    tags = [t.strip() for t in (meta.get("tags") or "").split(",") if t.strip()]

    # Hero media. A video wins over an image when both are given, because a
    # lead video is the stronger visual and two heroes stacked looks cluttered.
    hero_video = youtube_id(meta.get("video") or meta.get("youtube") or "")
    hero_image = (meta.get("image") or meta.get("photo") or "").strip()
    if hero_image and not re.match(r"^(https?://|/)", hero_image):
        print("  [originals] '%s' image is not a full URL - ignoring: %s"
              % (os.path.basename(path), hero_image[:60]))
        hero_image = ""
    hero_caption = (meta.get("caption") or meta.get("imagecaption") or "").strip()

    return {
        "hero_video":   hero_video,
        "hero_image":   hero_image,
        "hero_caption": hero_caption,
        "slug":       slug,
        "title":      title,
        "subtitle":   (meta.get("subtitle") or meta.get("deck") or "").strip(),
        "section":    sec,
        "author":     (meta.get("author") or DEFAULT_AUTHOR).strip(),
        "published":  published,
        "featured":   _truthy(meta.get("featured")),
        "tags":       tags,
        "summary":    summary,
        "body_html":  body_html,
        "read_min":   _reading_time(plain),
        "url":        "%s/%s.html" % (OUT_DIR, slug),
        "source_file": os.path.basename(path),
    }


def load_articles(base_dir="."):
    """Load every article, newest first. Never raises."""
    folder = os.path.join(base_dir, ARTICLES_DIR)
    if not os.path.isdir(folder):
        return []

    out, seen = [], {}
    try:
        names = sorted(os.listdir(folder))
    except Exception:
        return []

    for name in names:
        if name.startswith(".") or name.startswith("_"):
            continue
        # Documentation living alongside the articles must never be published.
        # The format guide contains a worked example, complete with a --- line,
        # which would otherwise parse as a real article and go live.
        if os.path.splitext(name)[0].lower() in {
                "readme", "read-me", "notes", "template", "example", "sample"}:
            continue
        if not name.lower().endswith((".txt", ".md", ".markdown", ".article")):
            continue
        art = _parse_article_file(os.path.join(folder, name))
        if not art:
            continue
        # Guarantee unique slugs so no page silently overwrites another.
        if art["slug"] in seen:
            n, base = 2, art["slug"]
            while ("%s-%d" % (base, n)) in seen:
                n += 1
            art["slug"] = "%s-%d" % (base, n)
            art["url"] = "%s/%s.html" % (OUT_DIR, art["slug"])
        seen[art["slug"]] = True
        out.append(art)

    out.sort(key=lambda a: a["published"], reverse=True)
    if out:
        print("  [originals] loaded %d article(s): %s"
              % (len(out), ", ".join(a["slug"] for a in out[:5])))
    return out


def has_articles(articles):
    return bool(articles)


# ─────────────────────────────────────────────────────────────────────────────
# CSS  — returned as a plain string. bot.py interpolates it as a VALUE, so no
#        brace-doubling is needed here. That is the whole point of this design.
# ─────────────────────────────────────────────────────────────────────────────

def originals_css():
    return """
    /* ══════════════════ NUZU ORIGINALS — in-house byline layer ══════════════════ */
    :root {
        --nzo-gold:      %(gold)s;
        --nzo-gold-lite: %(gold_light)s;
        --nzo-gold-deep: %(gold_deep)s;
    }

    /* — The gold byline. The single most important visual signal on the site. — */
    .nzo-byline {
        color: var(--nzo-gold-lite);
        font-weight: 700;
        letter-spacing: 0.02em;
        text-decoration: none;
    }
    .nzo-byline:hover { color: #F0D480; text-decoration: underline; }
    body.light-mode .nzo-byline { color: %(gold_deep)s; }

    .nzo-badge {
        display: inline-block;
        font-size: 0.58em; font-weight: 900; letter-spacing: 0.13em;
        text-transform: uppercase;
        color: #12100A;
        background: linear-gradient(135deg, var(--nzo-gold-lite), var(--nzo-gold));
        padding: 2px 7px; border-radius: 3px;
        vertical-align: middle; white-space: nowrap;
    }

    /* — Homepage featured strip — */
    .nzo-strip {
        max-width: 1400px; margin: 22px auto 4px; padding: 0 32px;
    }
    .nzo-strip-head {
        display: flex; align-items: center; gap: 12px;
        border-bottom: 2px solid var(--nzo-gold);
        padding-bottom: 7px; margin-bottom: 14px; flex-wrap: wrap;
    }
    .nzo-strip-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.12em; font-weight: 900; letter-spacing: 0.09em;
        text-transform: uppercase; color: var(--nzo-gold-lite); margin: 0;
    }
    body.light-mode .nzo-strip-title { color: %(gold_deep)s; }
    .nzo-strip-sub {
        font-size: 0.74em; color: var(--nuzu-muted); font-style: italic;
        margin-right: auto;
    }
    .nzo-strip-all {
        font-size: 0.72em; font-weight: 700; letter-spacing: 0.06em;
        text-transform: uppercase; color: var(--nzo-gold-lite);
        text-decoration: none; border: 1px solid rgba(201,162,39,0.45);
        padding: 4px 11px; border-radius: 3px; white-space: nowrap;
    }
    .nzo-strip-all:hover { background: rgba(201,162,39,0.14); }
    body.light-mode .nzo-strip-all { color: %(gold_deep)s; border-color: rgba(138,109,18,0.45); }

    .nzo-strip-grid {
        display: grid; gap: 14px;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    }

    .nzo-card {
        display: block; text-decoration: none; color: inherit;
        background: linear-gradient(160deg, rgba(201,162,39,0.07), rgba(201,162,39,0.015));
        border: 1px solid rgba(201,162,39,0.30);
        border-left: 3px solid var(--nzo-gold);
        border-radius: 6px; padding: 15px 17px 14px;
        transition: border-color 0.16s, transform 0.16s, background 0.16s;
    }
    .nzo-card:hover {
        border-color: rgba(201,162,39,0.65);
        background: linear-gradient(160deg, rgba(201,162,39,0.12), rgba(201,162,39,0.03));
        transform: translateY(-2px);
    }
    body.light-mode .nzo-card {
        background: linear-gradient(160deg, rgba(201,162,39,0.10), rgba(255,255,255,0.6));
        border-color: rgba(138,109,18,0.32);
    }
    .nzo-card-lead { border-left-width: 5px; }

    .nzo-card-kicker {
        display: flex; align-items: center; gap: 8px;
        margin-bottom: 8px; flex-wrap: wrap;
    }
    .nzo-card-sec {
        font-size: 0.6em; font-weight: 800; letter-spacing: 0.1em;
        text-transform: uppercase; padding: 2px 7px; border-radius: 3px;
        color: #fff;
    }
    .nzo-card-title {
        font-family: 'Playfair Display', Georgia, serif;
        font-size: 1.12em; font-weight: 700; line-height: 1.28;
        color: var(--nuzu-white); margin: 0 0 6px;
    }
    .nzo-card-lead .nzo-card-title { font-size: 1.34em; }
    body.light-mode .nzo-card-title { color: #14181F; }
    .nzo-card:hover .nzo-card-title { color: var(--nzo-gold-lite); }
    body.light-mode .nzo-card:hover .nzo-card-title { color: %(gold_deep)s; }

    .nzo-card-dek {
        font-size: 0.83em; line-height: 1.55; color: var(--nuzu-text);
        opacity: 0.86; margin: 0 0 9px;
    }
    body.light-mode .nzo-card-dek { color: #3C4757; }
    .nzo-card-meta {
        font-size: 0.72em; color: var(--nuzu-muted);
        display: flex; align-items: center; gap: 7px; flex-wrap: wrap;
    }
    .nzo-dot-sep { opacity: 0.5; }

    /* — Inline card that sits inside a normal news section — */
    .nzo-inline {
        display: block; text-decoration: none; color: inherit;
        border-left: 3px solid var(--nzo-gold);
        background: linear-gradient(90deg, rgba(201,162,39,0.09), rgba(201,162,39,0.01) 70%%);
        padding: 10px 12px 11px; margin: 0 0 10px;
        border-radius: 0 5px 5px 0;
        transition: background 0.16s;
    }
    .nzo-inline:hover { background: linear-gradient(90deg, rgba(201,162,39,0.16), rgba(201,162,39,0.03) 70%%); }
    .nzo-inline-top {
        display: flex; align-items: center; gap: 8px;
        margin-bottom: 5px; flex-wrap: wrap;
    }
    .nzo-inline-title {
        display: block; font-weight: 600; line-height: 1.4;
        color: var(--nuzu-white); margin-bottom: 4px;
    }
    body.light-mode .nzo-inline-title { color: #14181F; }
    .nzo-inline:hover .nzo-inline-title { color: var(--nzo-gold-lite); }
    body.light-mode .nzo-inline:hover .nzo-inline-title { color: %(gold_deep)s; }
    .nzo-inline-dek {
        display: block; font-size: 0.82em; line-height: 1.5;
        color: var(--nuzu-muted); margin-bottom: 5px;
    }
    .nzo-inline-meta { font-size: 0.72em; color: var(--nuzu-muted); }

    @media (max-width: 900px) {
        .nzo-strip { padding: 0 16px; margin-top: 16px; }
        .nzo-strip-grid { grid-template-columns: 1fr; }
        .nzo-card-lead .nzo-card-title { font-size: 1.18em; }
        .nzo-strip-sub { display: none; }
    }
    /* ════════════════ END NUZU ORIGINALS ════════════════ */
""" % {"gold": GOLD, "gold_light": GOLD_LIGHT, "gold_deep": GOLD_DEEP}


# ─────────────────────────────────────────────────────────────────────────────
# HOMEPAGE FRAGMENTS
# ─────────────────────────────────────────────────────────────────────────────

def _card_html(art, lead=False):
    label, color, _ = VALID_SECTIONS[art["section"]]
    dek = ('<p class="nzo-card-dek">%s</p>' % _esc(art["summary"])) if art["summary"] else ""
    return (
        '<a class="nzo-card%s" href="%s">'
        '<span class="nzo-card-kicker">'
        '<span class="nzo-badge">NUZU Original</span>'
        '<span class="nzo-card-sec" style="background:%s">%s</span>'
        '</span>'
        '<h3 class="nzo-card-title">%s</h3>'
        '%s'
        '<span class="nzo-card-meta">By <span class="nzo-byline">%s</span>'
        '<span class="nzo-dot-sep">&middot;</span>%s'
        '<span class="nzo-dot-sep">&middot;</span>%d min read</span>'
        '</a>'
        % (" nzo-card-lead" if lead else "", _esc(art["url"]),
           color, _esc(label), _esc(art["title"]), dek,
           _esc(art["author"]), _esc(_fmt_date(art["published"])), art["read_min"])
    )


def render_featured_strip(articles, max_cards=3):
    """The gold band under the top-stories strip. '' when there are no articles."""
    if not articles:
        return ""
    featured = [a for a in articles if a["featured"]] or articles
    picks = featured[:max_cards]
    cards = "".join(_card_html(a, lead=(i == 0)) for i, a in enumerate(picks))
    return (
        '<section class="nzo-strip" id="nuzu-originals" aria-labelledby="nzo-strip-h">'
        '<div class="nzo-strip-head">'
        '<h2 class="nzo-strip-title" id="nzo-strip-h">NUZU Originals</h2>'
        '<span class="nzo-strip-sub">Reporting and analysis written in house</span>'
        '<a class="nzo-strip-all" href="%s">All Originals &rarr;</a>'
        '</div>'
        '<div class="nzo-strip-grid">%s</div>'
        '</section>\n' % (OUT_HUB, cards)
    )


def render_section_originals(articles, section_id, limit=2):
    """
    Cards for one news section, to be prepended into that section's breaking
    column so an original reads as part of the section, not bolted on.
    """
    if not articles:
        return ""
    sid = section_id.replace("section-", "")
    if sid not in VALID_SECTIONS:
        return ""
    picks = [a for a in articles if a["section"] == sid][:limit]
    if not picks:
        return ""

    out = ""
    for art in picks:
        dek = ('<span class="nzo-inline-dek">%s</span>' % _esc(art["summary"])) if art["summary"] else ""
        out += (
            '<a class="nzo-inline" href="%s">'
            '<span class="nzo-inline-top"><span class="nzo-badge">NUZU Original</span></span>'
            '<span class="nzo-inline-title">%s</span>'
            '%s'
            '<span class="nzo-inline-meta">By <span class="nzo-byline">%s</span> '
            '&middot; %s &middot; %d min read</span>'
            '</a>\n'
            % (_esc(art["url"]), _esc(art["title"]), dek,
               _esc(art["author"]), _esc(_fmt_date(art["published"])), art["read_min"])
        )
    return out


def nav_link_html():
    """Sticky-nav tab. Kept as its own function so bot.py stays a one-line hook."""
    return ('<a href="%s" class="nav-link nav-originals" role="menuitem" '
            'style="border-left-color:%s">Originals</a>' % (OUT_HUB, GOLD))


def footer_links_html():
    return ('<li><a href="%s" style="color:%s;font-weight:600">Original Articles</a></li>'
            % (OUT_HUB, GOLD_LIGHT))


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE PAGES
# ─────────────────────────────────────────────────────────────────────────────

def _page_css():
    """CSS for originals.html and each article page. Self-contained, no deps."""
    return """
:root{
  --nuzu-dark:#020912; --nuzu-card:#060C1A; --nuzu-border:#0F1E35;
  --nuzu-text:#D0DAE8; --nuzu-muted:#4A6A99; --nuzu-white:#FFF;
  --nuzu-blue:#1E4FD8; --nzo-gold:%(gold)s; --nzo-gold-lite:%(gold_light)s;
  --nzo-gold-deep:%(gold_deep)s;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--nuzu-dark);color:var(--nuzu-text);
  font-family:'Inter',-apple-system,Arial,sans-serif;line-height:1.65;
  padding-top:48px;-webkit-text-size-adjust:100%%}
body.light-mode{background:#F4F6FA;color:#222}
a{color:var(--nzo-gold-lite)}
body.light-mode a{color:var(--nzo-gold-deep)}

.nzo-nav{position:fixed;top:0;left:0;right:0;height:48px;z-index:1000;
  background:#000;border-bottom:3px solid var(--nuzu-blue);
  display:flex;align-items:center;gap:16px;padding:0 20px}
body.light-mode .nzo-nav{background:#fff;border-bottom-color:#C9A227}
.nzo-nav .brand{font-family:'Playfair Display',Georgia,serif;font-weight:900;
  font-size:1.25em;letter-spacing:0.14em;color:#fff;text-decoration:none}
body.light-mode .nzo-nav .brand{color:#0D1B4B}
.nzo-nav .back{font-size:0.8em;color:var(--nuzu-muted);text-decoration:none;
  letter-spacing:0.05em}
.nzo-nav .back:hover{color:#fff}
body.light-mode .nzo-nav .back:hover{color:#000}
.nzo-nav .spacer{margin-left:auto}
.nzo-theme{background:none;border:1px solid var(--nuzu-border);color:var(--nuzu-muted);
  border-radius:4px;padding:4px 10px;font-size:0.75em;cursor:pointer;font-family:inherit}
.nzo-theme:hover{color:#fff;border-color:var(--nuzu-muted)}
body.light-mode .nzo-theme{border-color:#ccd;color:#666}

.nzo-wrap{max-width:820px;margin:0 auto;padding:34px 22px 80px}
.nzo-wrap-wide{max-width:1120px}

/* — Masthead — */
.nzo-mast{text-align:center;border-bottom:3px double var(--nzo-gold);
  padding-bottom:22px;margin-bottom:30px}
.nzo-mast h1{font-family:'Playfair Display',Georgia,serif;font-size:2.5em;
  font-weight:900;letter-spacing:0.06em;color:var(--nuzu-white);line-height:1.1}
body.light-mode .nzo-mast h1{color:#12161C}
.nzo-mast .tag{font-size:0.8em;color:var(--nuzu-muted);font-style:italic;margin-top:8px}
.nzo-mast .rule{font-size:0.66em;letter-spacing:0.28em;text-transform:uppercase;
  color:var(--nzo-gold-lite);margin-top:12px;font-weight:700}
body.light-mode .nzo-mast .rule{color:var(--nzo-gold-deep)}

/* — Author hub — */
.nzo-author-card{display:flex;gap:20px;align-items:center;flex-wrap:wrap;
  background:linear-gradient(140deg,rgba(201,162,39,0.09),rgba(201,162,39,0.02));
  border:1px solid rgba(201,162,39,0.30);border-left:4px solid var(--nzo-gold);
  border-radius:8px;padding:22px 24px;margin-bottom:34px}
body.light-mode .nzo-author-card{background:linear-gradient(140deg,rgba(201,162,39,0.13),#fff)}
.nzo-avatar{width:74px;height:74px;border-radius:50%%;flex-shrink:0;
  background:linear-gradient(140deg,var(--nzo-gold-lite),var(--nzo-gold-deep));
  display:flex;align-items:center;justify-content:center;
  font-family:'Playfair Display',Georgia,serif;font-size:1.75em;font-weight:900;color:#12100A}
.nzo-author-info{flex:1;min-width:220px}
.nzo-author-name{font-family:'Playfair Display',Georgia,serif;font-size:1.6em;
  font-weight:700;color:var(--nzo-gold-lite);line-height:1.2}
body.light-mode .nzo-author-name{color:var(--nzo-gold-deep)}
.nzo-author-role{font-size:0.78em;letter-spacing:0.13em;text-transform:uppercase;
  color:var(--nuzu-muted);margin-top:3px;font-weight:600}
.nzo-author-bio{font-size:0.88em;margin-top:9px;color:var(--nuzu-text);opacity:0.85;line-height:1.6}
body.light-mode .nzo-author-bio{color:#444}
.nzo-author-stat{font-size:0.75em;color:var(--nuzu-muted);margin-top:9px;letter-spacing:0.04em}

/* — Archive list — */
.nzo-arch-head{font-size:0.7em;font-weight:800;letter-spacing:0.16em;
  text-transform:uppercase;color:var(--nzo-gold-lite);
  border-bottom:1px solid rgba(201,162,39,0.3);padding-bottom:8px;margin-bottom:4px}
body.light-mode .nzo-arch-head{color:var(--nzo-gold-deep)}
.nzo-arch-item{display:block;text-decoration:none;color:inherit;
  border-bottom:1px solid var(--nuzu-border);padding:20px 4px;transition:background 0.15s}
body.light-mode .nzo-arch-item{border-bottom-color:#E2E6EE}
.nzo-arch-item:hover{background:rgba(201,162,39,0.055)}
.nzo-arch-kicker{display:flex;align-items:center;gap:9px;margin-bottom:7px;flex-wrap:wrap}
.nzo-arch-sec{font-size:0.6em;font-weight:800;letter-spacing:0.1em;text-transform:uppercase;
  padding:2px 8px;border-radius:3px;color:#fff}
.nzo-arch-date{font-size:0.73em;color:var(--nuzu-muted)}
.nzo-arch-title{font-family:'Playfair Display',Georgia,serif;font-size:1.34em;
  font-weight:700;line-height:1.3;color:var(--nuzu-white);margin-bottom:6px}
body.light-mode .nzo-arch-title{color:#12161C}
.nzo-arch-item:hover .nzo-arch-title{color:var(--nzo-gold-lite)}
body.light-mode .nzo-arch-item:hover .nzo-arch-title{color:var(--nzo-gold-deep)}
.nzo-arch-dek{font-size:0.88em;color:var(--nuzu-text);opacity:0.82;line-height:1.6;margin-bottom:7px}
body.light-mode .nzo-arch-dek{color:#49535F}
.nzo-arch-meta{font-size:0.75em;color:var(--nuzu-muted)}
.nzo-byline{color:var(--nzo-gold-lite);font-weight:700}
body.light-mode .nzo-byline{color:var(--nzo-gold-deep)}
.nzo-badge{display:inline-block;font-size:0.58em;font-weight:900;letter-spacing:0.13em;
  text-transform:uppercase;color:#12100A;
  background:linear-gradient(135deg,var(--nzo-gold-lite),var(--nzo-gold));
  padding:2px 7px;border-radius:3px;vertical-align:middle}

.nzo-empty{text-align:center;padding:64px 20px;color:var(--nuzu-muted)}
.nzo-empty h2{font-family:'Playfair Display',Georgia,serif;color:var(--nzo-gold-lite);
  font-size:1.5em;margin-bottom:10px}

/* — Article page — */
.nzo-art-head{border-bottom:1px solid var(--nuzu-border);padding-bottom:22px;margin-bottom:28px}
body.light-mode .nzo-art-head{border-bottom-color:#DDE2EA}
.nzo-art-kicker{display:flex;align-items:center;gap:10px;margin-bottom:14px;flex-wrap:wrap}
.nzo-art-title{font-family:'Playfair Display',Georgia,serif;font-size:2.35em;
  font-weight:900;line-height:1.16;color:var(--nuzu-white);margin-bottom:12px;
  letter-spacing:-0.01em}
body.light-mode .nzo-art-title{color:#0E1319}
.nzo-art-sub{font-size:1.06em;line-height:1.55;color:var(--nuzu-muted);
  font-weight:400;margin-bottom:18px}
.nzo-art-byline{display:flex;align-items:center;gap:12px;flex-wrap:wrap;font-size:0.84em;
  color:var(--nuzu-muted);border-top:1px solid var(--nuzu-border);padding-top:15px}
body.light-mode .nzo-art-byline{border-top-color:#DDE2EA}
.nzo-art-avatar{width:42px;height:42px;border-radius:50%%;flex-shrink:0;
  background:linear-gradient(140deg,var(--nzo-gold-lite),var(--nzo-gold-deep));
  display:flex;align-items:center;justify-content:center;
  font-family:'Playfair Display',Georgia,serif;font-weight:900;color:#12100A;font-size:1em}
.nzo-art-byline-txt{line-height:1.45}
.nzo-art-byline-name{font-size:1.08em}

/* — Body copy: the part that has to feel like a newspaper — */
.nzo-body{font-size:1.075em;line-height:1.82}
.nzo-p{margin-bottom:1.32em}
/* Drop cap. An explicit span, not ::first-letter, so it always lands on the
   opening paragraph even when the article leads with a quote or an image. */
.nzo-dropcap{float:left;font-family:'Playfair Display',Georgia,serif;
  font-size:3.5em;line-height:0.78;font-weight:900;color:var(--nzo-gold-lite);
  margin:0.05em 0.10em 0 0;text-shadow:0 2px 14px rgba(201,162,39,0.25)}
body.light-mode .nzo-dropcap{color:var(--nzo-gold-deep);text-shadow:none}

/* Byline. The gold is the whole point: it is how a reader tells an in-house
   piece from the two hundred wire sources on the rest of the site. */
.nzo-art-byline-name{font-size:1.12em;font-weight:600}
.nzo-art-byline-name a.nzo-byline,
a.nzo-byline,.nzo-byline{color:var(--nzo-gold-lite);font-weight:800;
  letter-spacing:0.02em;text-decoration:none}
body.light-mode .nzo-art-byline-name a.nzo-byline,
body.light-mode a.nzo-byline,body.light-mode .nzo-byline{color:var(--nzo-gold-deep)}
.nzo-art-byline-name a.nzo-byline:hover{text-decoration:underline}
.nzo-art-byline-role{font-size:0.78em;letter-spacing:0.14em;text-transform:uppercase;
  color:var(--nzo-gold);opacity:0.75;font-weight:700;margin-top:2px}

/* Video */
.nzo-video{margin:1.9em 0}
.nzo-video-frame{position:relative;width:100%%;padding-top:56.25%%;
  border-radius:7px;overflow:hidden;background:#000;
  border:1px solid rgba(201,162,39,0.22)}
.nzo-video-frame iframe{position:absolute;top:0;left:0;width:100%%;height:100%%;border:0}
.nzo-hero-img img{border:1px solid rgba(201,162,39,0.22)}
.nzo-art-head + .nzo-video,.nzo-art-head + .nzo-figure{margin-top:0;margin-bottom:2em}
.nzo-h2{font-family:'Playfair Display',Georgia,serif;font-size:1.5em;font-weight:700;
  color:var(--nuzu-white);margin:1.7em 0 0.55em;line-height:1.3}
.nzo-h3{font-size:1.2em;font-weight:700;color:var(--nuzu-white);margin:1.5em 0 0.5em}
.nzo-h4{font-size:1.03em;font-weight:700;color:var(--nuzu-white);margin:1.35em 0 0.45em}
body.light-mode .nzo-h2,body.light-mode .nzo-h3,body.light-mode .nzo-h4{color:#12161C}
.nzo-quote{border-left:3px solid var(--nzo-gold);padding:6px 0 6px 22px;
  margin:1.7em 0;font-family:'Playfair Display',Georgia,serif;font-size:1.28em;
  line-height:1.5;font-style:italic;color:var(--nuzu-white)}
body.light-mode .nzo-quote{color:#1B2028}
.nzo-cite{display:block;font-family:'Inter',Arial,sans-serif;font-size:0.6em;
  font-style:normal;color:var(--nuzu-muted);margin-top:10px;letter-spacing:0.05em}
.nzo-cite::before{content:"— "}
.nzo-list{margin:0 0 1.32em 1.4em}
.nzo-list li{margin-bottom:0.5em}
.nzo-rule{border:0;height:1px;background:var(--nuzu-border);margin:2.2em auto;width:44%%}
.nzo-figure{margin:1.8em 0}
.nzo-figure img{width:100%%;height:auto;border-radius:6px;display:block}
.nzo-figcap{font-size:0.79em;color:var(--nuzu-muted);margin-top:8px;
  text-align:center;font-style:italic}
.nzo-body code{background:rgba(255,255,255,0.07);padding:1px 5px;border-radius:3px;
  font-size:0.9em;font-family:ui-monospace,Menlo,Consolas,monospace}
body.light-mode .nzo-body code{background:rgba(0,0,0,0.06)}

.nzo-tags{margin-top:34px;padding-top:18px;border-top:1px solid var(--nuzu-border);
  display:flex;gap:8px;flex-wrap:wrap;align-items:center}
body.light-mode .nzo-tags{border-top-color:#DDE2EA}
.nzo-tag{font-size:0.72em;color:var(--nuzu-muted);border:1px solid var(--nuzu-border);
  padding:3px 10px;border-radius:12px}
body.light-mode .nzo-tag{border-color:#D6DBE4}

.nzo-endnote{margin-top:30px;padding:18px 20px;border-radius:6px;
  background:rgba(201,162,39,0.055);border:1px solid rgba(201,162,39,0.22);
  font-size:0.84em;line-height:1.65;color:var(--nuzu-muted)}

.nzo-more{margin-top:44px;padding-top:24px;border-top:3px double var(--nzo-gold)}
.nzo-more-h{font-size:0.7em;font-weight:800;letter-spacing:0.16em;text-transform:uppercase;
  color:var(--nzo-gold-lite);margin-bottom:14px}
body.light-mode .nzo-more-h{color:var(--nzo-gold-deep)}
.nzo-more-grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.nzo-more-card{display:block;text-decoration:none;color:inherit;padding:13px 15px;
  border:1px solid var(--nuzu-border);border-left:3px solid var(--nzo-gold);
  border-radius:0 5px 5px 0;transition:background 0.15s}
.nzo-more-card:hover{background:rgba(201,162,39,0.07)}
body.light-mode .nzo-more-card{border-color:#DDE2EA;border-left-color:var(--nzo-gold)}
.nzo-more-title{font-weight:600;line-height:1.4;color:var(--nuzu-white);
  margin-bottom:5px;font-size:0.95em}
body.light-mode .nzo-more-title{color:#12161C}
.nzo-more-meta{font-size:0.73em;color:var(--nuzu-muted)}

.nzo-foot{max-width:820px;margin:0 auto;padding:26px 22px 44px;text-align:center;
  border-top:1px solid var(--nuzu-border);font-size:0.78em;color:var(--nuzu-muted)}
body.light-mode .nzo-foot{border-top-color:#DDE2EA}
.nzo-foot a{color:var(--nuzu-muted);text-decoration:none;margin:0 9px}
.nzo-foot a:hover{color:var(--nzo-gold-lite)}

@media (max-width:700px){
  .nzo-wrap{padding:24px 16px 60px}
  .nzo-mast h1{font-size:1.85em}
  .nzo-art-title{font-size:1.72em}
  .nzo-body{font-size:1.02em;line-height:1.75}
  .nzo-arch-title{font-size:1.14em}
  .nzo-author-card{padding:18px}
  .nzo-quote{font-size:1.12em;padding-left:16px}
}
""" % {"gold": GOLD, "gold_light": GOLD_LIGHT, "gold_deep": GOLD_DEEP}


_THEME_JS = """
<script>
(function(){
  try{
    if(localStorage.getItem('nuzu_light_mode')==='1'){document.body.classList.add('light-mode');}
  }catch(e){}
  var b=document.getElementById('nzo-theme');
  if(b){b.addEventListener('click',function(){
    var on=document.body.classList.toggle('light-mode');
    try{localStorage.setItem('nuzu_light_mode',on?'1':'0');}catch(e){}
  });}
})();
</script>
"""


def _page_shell(title, description, body_html, depth=0, canonical=""):
    """Common HTML wrapper. depth=1 for pages inside originals/."""
    up = "../" if depth else ""
    canon = canonical or SITE_BASE_URL
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(canon)s">
<meta name="theme-color" content="#0D1B4B">
<meta property="og:type" content="article">
<meta property="og:site_name" content="NUZU News">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(canon)s">
<meta property="og:image" content="%(base)sicons/icon-512.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(title)s">
<meta name="twitter:description" content="%(desc)s">
<link rel="icon" href="%(up)sicons/icon-192.png">
<link rel="apple-touch-icon" href="%(up)sicons/icon-192.png">
<link rel="manifest" href="%(up)smanifest.json">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>%(css)s</style>
<script>if("serviceWorker"in navigator){navigator.serviceWorker.register("%(up)ssw.js").catch(function(){});}</script>
</head>
<body>
<nav class="nzo-nav">
  <a class="brand" href="%(up)sindex.html">NUZU</a>
  <a class="back" href="%(up)sindex.html">&larr; Back to the wire</a>
  <span class="spacer"></span>
  <button class="nzo-theme" id="nzo-theme" type="button">Light / Dark</button>
</nav>
%(body)s
<div class="nzo-foot">
  <p>&copy; %(year)d NUZU News &middot; Original reporting by NUZU staff.</p>
  <p style="margin-top:8px">
    <a href="%(up)sindex.html">Home</a>
    <a href="%(up)soriginals.html">Originals</a>
    <a href="%(up)sabout.html">About</a>
    <a href="%(up)sprivacy.html">Privacy</a>
    <a href="%(up)sterms.html">Terms</a>
  </p>
</div>
%(js)s
</body>
</html>
""" % {
        "title": _esc(title), "desc": _esc(description), "canon": _esc(canon),
        "base": SITE_BASE_URL, "up": up, "css": _page_css(),
        "body": body_html, "js": _THEME_JS, "year": datetime.utcnow().year,
    }


def _render_hub(articles, author_name=DEFAULT_AUTHOR):
    """originals.html — the byline page. Looks like a real journalist archive."""
    initials = "".join(w[0] for w in author_name.split()[:2]).upper() or "NZ"

    if articles:
        items = ""
        for art in articles:
            label, color, _ = VALID_SECTIONS[art["section"]]
            dek = ('<div class="nzo-arch-dek">%s</div>' % _esc(art["summary"])) if art["summary"] else ""
            items += (
                '<a class="nzo-arch-item" href="%s">'
                '<div class="nzo-arch-kicker">'
                '<span class="nzo-arch-sec" style="background:%s">%s</span>'
                '<span class="nzo-arch-date">%s</span>'
                '</div>'
                '<div class="nzo-arch-title">%s</div>'
                '%s'
                '<div class="nzo-arch-meta">By <span class="nzo-byline">%s</span> '
                '&middot; %d min read</div>'
                '</a>\n'
                % (_esc(art["url"]), color, _esc(label),
                   _esc(_fmt_date(art["published"])), _esc(art["title"]), dek,
                   _esc(art["author"]), art["read_min"])
            )
        latest = articles[0]["published"]
        stat = ("%d article%s published &middot; most recent %s"
                % (len(articles), "" if len(articles) == 1 else "s", _fmt_date(latest)))
        archive = ('<div class="nzo-arch-head">Complete Archive</div>%s' % items)
    else:
        stat = "Archive coming soon"
        archive = ('<div class="nzo-empty"><h2>No originals published yet</h2>'
                   '<p>Drop a text file into the <code>articles/</code> folder and it '
                   'will appear here within about five minutes.</p></div>')

    body = """
<div class="nzo-wrap nzo-wrap-wide">
  <div class="nzo-mast">
    <h1>NUZU Originals</h1>
    <div class="tag">Reporting and analysis written in house</div>
    <div class="rule">Original Journalism &middot; NUZU News</div>
  </div>

  <div class="nzo-author-card">
    <div class="nzo-avatar">%(initials)s</div>
    <div class="nzo-author-info">
      <div class="nzo-author-name">%(author)s</div>
      <div class="nzo-author-role">Staff Writer &middot; NUZU News</div>
      <div class="nzo-author-bio">%(author)s writes original reporting and analysis for
        NUZU News across politics, world affairs, technology, business, sport and
        culture &mdash; the connective tissue between the headlines the wire brings in
        every five minutes.</div>
      <div class="nzo-author-stat">%(stat)s</div>
    </div>
  </div>

  %(archive)s
</div>
""" % {"initials": _esc(initials), "author": _esc(author_name),
       "stat": stat, "archive": archive}

    return _page_shell(
        "NUZU Originals — Original Reporting by %s" % author_name,
        "Original articles, reporting and analysis written in house for NUZU News by %s." % author_name,
        body, depth=0, canonical=SITE_BASE_URL + OUT_HUB)


def _render_article_page(art, siblings):
    """One full article page."""
    label, color, section_anchor = VALID_SECTIONS[art["section"]]
    initials = "".join(w[0] for w in art["author"].split()[:2]).upper() or "NZ"

    sub = ('<p class="nzo-art-sub">%s</p>' % _esc(art["subtitle"])) if art["subtitle"] else ""

    # Lead media, directly under the byline.
    hero = ""
    if art.get("hero_video"):
        hero = _video_embed(art["hero_video"], art.get("hero_caption", ""), lazy=False)
    elif art.get("hero_image"):
        hcap = (('<figcaption class="nzo-figcap">%s</figcaption>'
                 % _inline(_esc(art["hero_caption"]))) if art.get("hero_caption") else "")
        hero = ('<figure class="nzo-figure nzo-hero-img">'
                '<img src="%s" alt="%s">%s</figure>'
                % (_esc(art["hero_image"]), _esc(art.get("hero_caption") or art["title"]), hcap))

    tags = ""
    if art["tags"]:
        chips = "".join('<span class="nzo-tag">%s</span>' % _esc(t) for t in art["tags"])
        tags = '<div class="nzo-tags">%s</div>' % chips

    more = ""
    others = [a for a in siblings if a["slug"] != art["slug"]][:4]
    if others:
        cards = ""
        for o in others:
            olabel, ocolor, _ = VALID_SECTIONS[o["section"]]
            cards += (
                '<a class="nzo-more-card" href="../%s">'
                '<div class="nzo-more-title">%s</div>'
                '<div class="nzo-more-meta">%s &middot; %s</div></a>'
                % (_esc(o["url"]), _esc(o["title"]),
                   _esc(olabel), _esc(_fmt_date(o["published"])))
            )
        more = ('<div class="nzo-more"><div class="nzo-more-h">More from %s</div>'
                '<div class="nzo-more-grid">%s</div></div>'
                % (_esc(art["author"]), cards))

    body = """
<div class="nzo-wrap">
  <article>
    <header class="nzo-art-head">
      <div class="nzo-art-kicker">
        <span class="nzo-badge">NUZU Original</span>
        <span class="nzo-arch-sec" style="background:%(color)s">%(label)s</span>
        <a href="../index.html#%(anchor)s" style="font-size:0.74em;color:inherit;opacity:0.7">
          See the %(label)s wire &rarr;</a>
      </div>
      <h1 class="nzo-art-title">%(title)s</h1>
      %(sub)s
      <div class="nzo-art-byline">
        <div class="nzo-art-avatar">%(initials)s</div>
        <div class="nzo-art-byline-txt">
          <div class="nzo-art-byline-name">By <a class="nzo-byline" href="../originals.html">%(author)s</a></div>
          <div class="nzo-art-byline-role">NUZU Staff Writer</div>
          <div>%(datetime)s &middot; %(read)d min read</div>
        </div>
      </div>
    </header>

    %(hero)s

    <div class="nzo-body">
%(body)s
    </div>

    %(tags)s

    <div class="nzo-endnote">
      <strong style="color:var(--nzo-gold-lite)">About this article.</strong>
      This is an original NUZU News piece, written and edited in house. It is not
      aggregated content. Everything else on NUZU links out to the publisher that
      reported it &mdash; this does not.
    </div>

    %(more)s
  </article>
</div>
""" % {"color": color, "label": _esc(label), "anchor": section_anchor,
       "title": _esc(art["title"]), "sub": sub, "initials": _esc(initials),
       "author": _esc(art["author"]),
       "datetime": _esc(_fmt_datetime(art["published"])),
       "read": art["read_min"], "body": art["body_html"],
       "hero": hero, "tags": tags, "more": more}

    desc = art["summary"] or art["subtitle"] or art["title"]
    return _page_shell(
        "%s — NUZU News" % art["title"], desc, body,
        depth=1, canonical="%s%s" % (SITE_BASE_URL, art["url"]))


def write_originals_pages(articles, base_dir=".", author_name=DEFAULT_AUTHOR):
    """
    Write originals.html plus one page per article.
    Returns the list of paths written (relative), for the workflow's git add.
    Never raises — a failure here must never abort the news build.
    """
    written = []
    try:
        hub_path = os.path.join(base_dir, OUT_HUB)
        with open(hub_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(_strip_surrogates(_render_hub(articles, author_name)))
        written.append(OUT_HUB)

        out_dir = os.path.join(base_dir, OUT_DIR)
        os.makedirs(out_dir, exist_ok=True)

        current = set()
        for art in articles:
            fname = "%s.html" % art["slug"]
            current.add(fname)
            with open(os.path.join(out_dir, fname), "w",
                      encoding="utf-8", errors="replace") as f:
                f.write(_strip_surrogates(_render_article_page(art, articles)))
            written.append("%s/%s" % (OUT_DIR, fname))

        # Remove pages whose source file was deleted or renamed, so the archive
        # never shows a link to a page that is no longer referenced.
        for stale in os.listdir(out_dir):
            if stale.endswith(".html") and stale not in current:
                try:
                    os.remove(os.path.join(out_dir, stale))
                    print("  [originals] removed stale page: %s" % stale)
                except Exception:
                    pass

        print("  [originals] wrote %s + %d article page(s)" % (OUT_HUB, len(articles)))
    except Exception as e:
        print("  [originals] WARNING - page write failed (site build continues): %s" % e)
    return written


# ─────────────────────────────────────────────────────────────────────────────
# SELF TEST
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        arts = load_articles(".")
        print("Articles found: %d" % len(arts))
        for a in arts:
            print("  - [%s] %s  (%s, %d min, featured=%s)"
                  % (a["section"], a["title"], a["slug"], a["read_min"], a["featured"]))
        write_originals_pages(arts, ".")
        print("CSS bytes: %d" % len(originals_css()))
        print("Strip bytes: %d" % len(render_featured_strip(arts)))
        print("Self test complete.")
