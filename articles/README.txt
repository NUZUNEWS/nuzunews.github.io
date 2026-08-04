NUZU ORIGINALS — how to post an article
═══════════════════════════════════════════════════════════════════

Drop a .txt file in this folder. That's it. The site rebuilds every
five minutes and the article goes live on the next run.

Easiest route: open post.html on the site (or straight off your
computer), paste your article, pick the section, hit Download —
then drop the file it gives you back into this folder.


THE FORMAT
───────────────────────────────────────────────────────────────────

  title: Your Headline Here
  subtitle: The smaller line underneath
  section: us
  author: Sean Mitchell
  published: 2026-08-04 09:00
  featured: yes
  tags: media, politics
  summary: One or two sentences shown on the homepage card.
  ---
  Your article starts after the three dashes.

  A blank line starts a new paragraph.


Only "title" and the body are required. Everything else has a
sensible default.

  section    us · mideast · world · tech · business · sports · culture
             (anything unrecognised is filed under culture)
  featured   yes = appears in the gold strip at the top of the homepage
  published  2026-08-04 09:00, or 2026-08-04, or August 4, 2026
  summary    leave it out and the first paragraph is used instead


WRITING IN THE BODY
───────────────────────────────────────────────────────────────────

  blank line        new paragraph
  ## Heading        subheading
  ### Heading       smaller subheading
  > Some text       pull quote
  > Text -- Name    pull quote with attribution
  - Item            bullet list
  1. Item           numbered list
  **bold**          bold
  *italic*          italic
  [text](url)       link
  ![caption](url)   image
  ---               section break


WHAT HAPPENS TO IT
───────────────────────────────────────────────────────────────────

Each article shows up in four places:

  1. The gold NUZU Originals strip near the top of the homepage
     (only if featured: yes)
  2. Inline at the top of whichever section you filed it to
  3. originals.html — the full byline archive
  4. originals/<slug>.html — its own newspaper-styled page

The byline is gold everywhere, so an in-house piece is instantly
distinguishable from the aggregated wire.


IF SOMETHING DOESN'T APPEAR
───────────────────────────────────────────────────────────────────

Check the Actions log for lines starting with [originals]. It says
exactly why a file was skipped. The usual causes:

  · the --- separator is missing
  · there's no title: line
  · the body is empty

A broken article file is always skipped, never fatal. The news wire
keeps running regardless.


DELETING AN ARTICLE
───────────────────────────────────────────────────────────────────

Delete the .txt file. Its page is removed automatically on the next
build and it disappears from the archive.
