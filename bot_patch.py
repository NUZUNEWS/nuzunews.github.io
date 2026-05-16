#!/usr/bin/env python3
"""
NUZU News — bot_patch.py
=========================
One-command installer. Run once from the repo root:

    python3 bot_patch.py

WHAT IT DOES:
  1. Backs up bot.py → bot.py.backup
  2. Adds <script src="/nuzu-bundle.js"> to the HTML template (1 line)
  3. Adds the sanitize_title / sanitize_url import and 5 surgical patches
     that prevent XSS via compromised RSS feeds
  4. Verifies every patch applied cleanly
  5. Prints a clear summary — green lines = done, yellow = already done, red = problem

WHAT IT DOES NOT DO:
  • Does not change any logic, layout, or features
  • Does not touch sw.js, manifest.json, or any other file
  • Does not run the bot — you still trigger that as normal

SAFE TO RE-RUN:
  Already-applied patches are detected and skipped (idempotent).
  If something goes wrong, restore with: cp bot.py.backup bot.py
"""

import re
import sys
import shutil
import textwrap
from pathlib import Path

# ─── Colours ─────────────────────────────────────────────────────────────────
def green(s):  return '\033[92m' + s + '\033[0m'
def yellow(s): return '\033[93m' + s + '\033[0m'
def red(s):    return '\033[91m' + s + '\033[0m'
def bold(s):   return '\033[1m'  + s + '\033[0m'

BOT = Path('bot.py')

# ─────────────────────────────────────────────────────────────────────────────
# PREFLIGHT
# ─────────────────────────────────────────────────────────────────────────────
def preflight():
    if not BOT.exists():
        print(red('✗ bot.py not found. Run this script from the repo root.'))
        sys.exit(1)
    if not Path('nuzu-bundle.js').exists():
        print(red('✗ nuzu-bundle.js not found. Make sure it is in the same folder.'))
        sys.exit(1)
    if not Path('bot_sanitizer.py').exists():
        print(red('✗ bot_sanitizer.py not found. Make sure it is in the same folder.'))
        sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# BACKUP
# ─────────────────────────────────────────────────────────────────────────────
def backup():
    dst = Path('bot.py.backup')
    if not dst.exists():
        shutil.copy2(BOT, dst)
        print(green('✓ Backup created: bot.py.backup'))
    else:
        print(yellow('~ Backup already exists: bot.py.backup (skipping overwrite)'))

# ─────────────────────────────────────────────────────────────────────────────
# PATCH ENGINE
# ─────────────────────────────────────────────────────────────────────────────
class Patcher:
    def __init__(self, src: str):
        self.src     = src
        self.applied = []
        self.skipped = []
        self.failed  = []

    def insert_before(self, name: str, needle: str, insertion: str) -> bool:
        """Insert `insertion` immediately before the first occurrence of `needle`."""
        if insertion.strip() in self.src:
            self.skipped.append(name)
            return True
        idx = self.src.find(needle)
        if idx == -1:
            self.failed.append((name, f'Could not find anchor: {repr(needle[:60])}'))
            return False
        self.src = self.src[:idx] + insertion + self.src[idx:]
        self.applied.append(name)
        return True

    def insert_after(self, name: str, needle: str, insertion: str) -> bool:
        """Insert `insertion` immediately after the first occurrence of `needle`."""
        if insertion.strip() in self.src:
            self.skipped.append(name)
            return True
        idx = self.src.find(needle)
        if idx == -1:
            self.failed.append((name, f'Could not find anchor: {repr(needle[:60])}'))
            return False
        end = idx + len(needle)
        self.src = self.src[:end] + insertion + self.src[end:]
        self.applied.append(name)
        return True

    def replace_first(self, name: str, old: str, new: str) -> bool:
        """Replace the first occurrence of `old` with `new`."""
        if new.strip() in self.src:
            self.skipped.append(name)
            return True
        if old not in self.src:
            self.failed.append((name, f'Could not find text to replace: {repr(old[:60])}'))
            return False
        self.src = self.src.replace(old, new, 1)
        self.applied.append(name)
        return True

    def report(self):
        print()
        print(bold('─── Patch Summary ───────────────────────────────'))
        for name in self.applied:  print(green(f'  ✓ Applied : {name}'))
        for name in self.skipped:  print(yellow(f'  ~ Already : {name}'))
        for name, reason in self.failed:
            print(red(f'  ✗ FAILED  : {name}'))
            print(red(f'              {reason}'))
        print()
        if self.failed:
            print(red(f'  {len(self.failed)} patch(es) failed — see above.'))
            print(red('  The file has NOT been written. Restore: cp bot.py.backup bot.py'))
            return False
        total = len(self.applied) + len(self.skipped)
        print(green(f'  {len(self.applied)} applied, {len(self.skipped)} already in place ({total} total).'))
        return True


# ─────────────────────────────────────────────────────────────────────────────
# DEFINE PATCHES
# ─────────────────────────────────────────────────────────────────────────────

def run_patches(src: str) -> tuple[str, bool]:
    p = Patcher(src)

    # ── PATCH 0: Import sanitizer ─────────────────────────────────────────
    # Insert after the last existing import line at the top
    p.insert_after(
        'Import sanitizer',
        'socket.setdefaulttimeout(20)',
        '\n\n# ── NUZU sanitizer: prevents XSS via compromised RSS feeds ──\ntry:\n    from bot_sanitizer import sanitize_title, sanitize_attr, sanitize_url, sanitize_source_name, sanitize_summary, validate_feed_entry\nexcept ImportError:\n    # Fallback no-ops if bot_sanitizer.py is not present\n    import html as _html\n    def sanitize_title(s, max_len=300): return _html.escape(str(s or ""), quote=True)[:max_len]\n    def sanitize_attr(s, max_len=300):  return _html.escape(str(s or ""), quote=True).replace("\'","&#39;")[:max_len]\n    def sanitize_url(s):                return s if str(s).startswith(("http://","https://","/")) else "#"\n    def sanitize_source_name(s):        return _html.escape(str(s or ""), quote=True)[:80]\n    def sanitize_summary(s, max_len=400): return _html.escape(str(s or ""), quote=True)[:max_len]\n    def validate_feed_entry(e, src):    return True, ""\n'
    )

    # ── PATCH 1: Add nuzu-bundle.js script tag before </body> ─────────────
    # The </body> tag in bot.py's template
    BODY_CLOSE = '</body>'
    BUNDLE_TAG = '    <script src="/nuzu-bundle.js?v={BUILD_STAMP}"></script>\n'
    # We need to insert before the LAST </body> in the template section
    # Find the template </body> (it's inside an f-string, not at line start)
    p.insert_before(
        'nuzu-bundle.js script tag',
        BODY_CLOSE,
        BUNDLE_TAG
    )

    # ── PATCH 2: Single-source headline — sanitize display_title ──────────
    OLD2 = "            display_title = clean_title[0].upper() + clean_title[1:] if clean_title else clean_title"
    NEW2 = (
        "            display_title = clean_title[0].upper() + clean_title[1:] if clean_title else clean_title\n"
        "            display_title = sanitize_title(display_title)  # NUZU: XSS guard"
    )
    p.replace_first('Sanitize single-source display_title', OLD2, NEW2)

    # ── PATCH 3: Single-source headline — sanitize safe_title_attr ────────
    OLD3 = "            safe_title_attr = display_title.replace('\"', \"'\")\n            _hl_sum = _ARTICLE_SUMMARIES.get(link, '')\n            _hl_sum_html = (f'<span class=\"hl-summary\">{_hl_sum}</span>' if _hl_sum else '')"
    NEW3 = (
        "            safe_title_attr = sanitize_attr(display_title)  # NUZU: XSS guard (replaces .replace)\n"
        "            _hl_sum_raw = _ARTICLE_SUMMARIES.get(link, '')\n"
        "            _hl_sum = sanitize_summary(_hl_sum_raw)  # NUZU: sanitize summary\n"
        "            _hl_sum_html = (f'<span class=\"hl-summary\">{_hl_sum}</span>' if _hl_sum else '')"
    )
    p.replace_first('Sanitize single-source safe_title_attr + summary', OLD3, NEW3)

    # ── PATCH 4: Cluster — sanitize display_title ─────────────────────────
    OLD4 = "            display_title = clean_lead[0].upper() + clean_lead[1:] if clean_lead else clean_lead"
    NEW4 = (
        "            display_title = clean_lead[0].upper() + clean_lead[1:] if clean_lead else clean_lead\n"
        "            display_title = sanitize_title(display_title)  # NUZU: XSS guard"
    )
    p.replace_first('Sanitize cluster display_title', OLD4, NEW4)

    # ── PATCH 5: Cluster — sanitize safe_title_attr ───────────────────────
    OLD5 = "            safe_title_attr = display_title.replace('\"', \"'\")\n            trust_pct"
    NEW5 = (
        "            safe_title_attr = sanitize_attr(display_title)  # NUZU: XSS guard\n"
        "            trust_pct"
    )
    p.replace_first('Sanitize cluster safe_title_attr', OLD5, NEW5)

    # ── PATCH 6: Cluster source pills ────────────────────────────────────
    OLD6 = "                '<span class=\"cluster-src-pill\">' + s + '</span>' for s in top3_srcs"
    NEW6 = "                '<span class=\"cluster-src-pill\">' + sanitize_source_name(s) + '</span>' for s in top3_srcs  # NUZU"
    p.replace_first('Sanitize cluster-src-pills', OLD6, NEW6)

    # ── PATCH 7: Cluster summary ─────────────────────────────────────────
    OLD7 = "            _cl_sum = _ARTICLE_SUMMARIES.get(lead_link, '')\n            _cl_sum_html = f'<span class=\"hl-summary\">{_cl_sum}</span>' if _cl_sum else ''"
    NEW7 = (
        "            _cl_sum_raw = _ARTICLE_SUMMARIES.get(lead_link, '')\n"
        "            _cl_sum = sanitize_summary(_cl_sum_raw)  # NUZU: XSS guard\n"
        "            _cl_sum_html = f'<span class=\"hl-summary\">{_cl_sum}</span>' if _cl_sum else ''"
    )
    p.replace_first('Sanitize cluster summary', OLD7, NEW7)

    ok = p.report()
    return p.src, ok


# ─────────────────────────────────────────────────────────────────────────────
# VERIFY
# ─────────────────────────────────────────────────────────────────────────────
def verify(src: str):
    checks = {
        'sanitize_title import':    'from bot_sanitizer import sanitize_title',
        'bundle script tag':        'nuzu-bundle.js',
        'sanitize_title in render': 'display_title = sanitize_title(display_title)',
        'sanitize_attr in render':  'sanitize_attr(display_title)',
        'sanitize cluster pills':   'sanitize_source_name(s)',
        'sanitize summary':         'sanitize_summary(',
    }
    print(bold('─── Verification ────────────────────────────────'))
    all_ok = True
    for name, needle in checks.items():
        if needle in src:
            print(green(f'  ✓ {name}'))
        else:
            print(red(f'  ✗ NOT FOUND: {name}'))
            all_ok = False
    print()
    return all_ok


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print(bold('\nNUZU bot_patch.py — Production Hardening Installer'))
    print('=' * 52)

    preflight()
    backup()

    print(bold('\nReading bot.py...'))
    src = BOT.read_text(encoding='utf-8')
    original_len = len(src)

    print(bold('Applying patches...\n'))
    patched, ok = run_patches(src)

    if not ok:
        print(red('\nAborted — bot.py was NOT modified.'))
        print(red('Fix the issues above, then run bot_patch.py again.'))
        sys.exit(1)

    # Verify before writing
    if not verify(patched):
        print(red('Verification failed — bot.py was NOT modified.'))
        sys.exit(1)

    # Write
    BOT.write_text(patched, encoding='utf-8')
    added = len(patched) - original_len
    print(green(f'✓ bot.py written (+{added} bytes)'))

    print()
    print(bold('═══ INSTALL COMPLETE ══════════════════════════════'))
    print(green('✓ bot_patch.py finished successfully.'))
    print()
    print('  Next steps:')
    print('  1. Verify: git diff bot.py  (review the changes)')
    print('  2. Trigger a bot run: python3 bot.py')
    print('     (this regenerates index.html with all hardening in place)')
    print('  3. Commit and push everything:')
    print('     git add bot.py nuzu-bundle.js sw.js manifest.json bot_sanitizer.py')
    print('     git add .github/workflows/quality.yml offline.html')
    print('     git commit -m "Production hardening v3.0"')
    print('     git push')
    print()
    print('  The live site will update within ~2 minutes after push.')
    print('  The service worker will notify open tabs of the update.')
    print()

if __name__ == '__main__':
    main()
