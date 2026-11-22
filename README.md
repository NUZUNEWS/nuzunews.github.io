# nuzunews.github.io
NUZU News — Real News in Real Time

`bot.py` builds the whole site (`index.html`, `feed.json`, `feed.xml`, `health.json` ...) from
hundreds of news feeds. `.github/workflows/refresh.yml` runs it: each run builds about every 10
minutes for up to 5.5 hours. `health.json` says how the last build went.

## The Argus contract

NUZU is one of the sites inside the Argus Media Player (a side tab). It must also work on its own,
in any browser, and in any Argus version. These are the things Argus relies on. Keep them working,
and run the Argus tests below after changing `bot.py`.

**Saved settings (localStorage, `'1'` or `'0'`)**
- `nuzu_video_on` — the LIVE VIDEO switch. Argus opens NUZU with video OFF unless the person
  turned it on (Argus keeps NUZU's own memory).
- `nuzu_light_mode` — the LIGHT switch (dark = Onyx, the Argus look).

**Page parts Argus finds**
- `#ob-skip` — the first-visit welcome's Skip button.
- The section ids `#section-us`, `#section-mideast`, `#section-world`, `#section-tech`,
  `#section-business`, `#section-sports`, `#section-culture`. The internal key of Science, Tech &
  Health stays `tech` / "Tech" (anchors, saved interests, the Argus tab).
- The tile being heard has the class `audio-active` (`.youtube-inset.audio-active`); it is held on
  screen at every width (NUZU 2.3.1). While the page is hidden only the silent tiles pause (2.4).

**URL options**
- `?section=us|mideast|world|tech|business|sports|culture` scrolls to that section.
- `?panel=saved` opens Saved. (NUZU has no `?video=` or `?theme=`; the switches remember instead.)

**Messages to and from Argus**
- Inside Argus each tile has TAB and ARGUS full-screen buttons. ARGUS sends
  `chrome.webview.postMessage('argus:fill')`, which asks Argus to fill its whole window.
- Argus calls `window.__argusSetAccent('#rrggbb')` with its theme's colour, or `null` on its own
  Onyx; NUZU's dark mode then uses that accent.
- Both live in one plain-string block in `bot.py`, `NZ_ARGUS_1_0_2`. Argus's tests read that block
  straight out of `bot.py`, so keep its name and keep it appended to the page.

**The Argus tests to run** (in the Argus source folder, with Python):
- `tests/nuzu_holds_the_heard_video.py` with `ARGUS_NUZU_BOT` set to this `bot.py`
- `tests/nuzu_and_party_portal_first_visit.py`
- `tests/nuzu_starts_with_live_video_off.py`
- `tests/only_nuzu_news_remembers.py`
