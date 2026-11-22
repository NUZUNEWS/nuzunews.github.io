# NUZU NEWS - changelog

## 2.4.0 - 21 November 2026 (made with Argus 1.0.3)

- **Nearly real time.** `.github/workflows/refresh.yml`: GitHub starts a scheduled run only every
  few hours, so each run now keeps building, about every 10 minutes for up to 5.5 hours. A new run
  (or Run workflow after an upload) replaces the one in progress; two never overlap.
- **A breaking ticker that is news.** Only US, World, Middle East and Business stories, and only
  ones that several outlets carry or a Tier 1-2 outlet reports; the newest three hours first, then
  six, then twelve. It used to lead with sports results and gadget news. Each line names its outlet
  and how many outlets carry the story, and quotation marks no longer show as `&quot;`.
- **Each story once.** A story that was in two sections (business and US, say) now shows once,
  where most outlets carry it, with an "also in US" tag.
- **Straight to the article.** 141 outlets' own feeds (BBC, NPR, The Guardian, Al Jazeera, DW,
  France 24, CBC and more; each checked live on 21 November) so their headlines open the outlet's
  page itself. A Google News headline from one of those outlets is given the direct link too when
  the same headline is in the outlet's feed. Google News stays as the fallback.
- **The same top bar as Party Portal.** Saved, Updated, Light, Live Video, Waiting Room, then A- A+,
  in the same look as Party Portal 3.2. Phones keep their own controls.
- **Quieter in the background.** While the page is hidden (another browser tab, or another Argus
  tab), the silent video tiles pause; the tile being heard keeps playing. They resume when the page
  is shown again.
- **health.json** each build: feeds read and failed, items per section, video tiles live, the
  ticker, stories folded, the share of direct links.
- README: the "Argus contract" (what Argus relies on, and the Argus tests to run after a change).
- Files: `bot.py`, `version.json`, `CHANGELOG.md`, `README.md`, `.github/workflows/refresh.yml`.

## 2.3.1 - 14 November 2026 (made with Argus 1.0.2)

- **The heard tile is held.** At 900 px and narrower the whole video banner used to disappear while
  the tile being heard went on sounding, unseen. Now, once a tile's sound is on, it stays on screen
  as the phone-size player; made wide again it is the first tile. It is the same player throughout,
  never moved or reloaded (by CSS alone). Without sound, nothing changes.
- **Full screen everywhere.** Every tile and every phone section video has a full-screen button.
  Inside Argus there are two: TAB fills Argus's side tab, ARGUS fills the whole Argus window.
- **Full screen survives a resize.** A tile in full screen is never hidden when the window narrows.
- **Argus's colours.** Inside Argus, dark mode takes the accent colour of the Argus theme in use.
- Files: `bot.py` (one plain-string block, `NZ_ARGUS_1_0_2`), `version.json`. Checked in a hidden
  Edge: the page as built before fails 11 of the checks, the new block passes all of them.

## 2.3.0 - 7 November 2026 ("Onyx")

- Argus-matching Onyx look, every text colour passing WCAG AA, live-checked video tiles,
  promo/junk filter, Science, Tech & Health, about 75 more sources. (See version.json history.)
