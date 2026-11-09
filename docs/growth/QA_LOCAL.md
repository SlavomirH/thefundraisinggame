# Local QA notes (2026-11-09)

No commits, pushes, deploys, or external calls. robots.txt, CNAME, site.js and DNS untouched.

## Articles (6 new files in articles/)
- Fact-check: no "100+ investors", fabricated quotes, guaranteed outcomes or search volumes found. Worked examples (funnel 120→1.08, runway €713k, 15.1% ownership) re-checked arithmetically; they are labelled illustrative.
- Softened unverifiable attributions: the DocSend "repeat batch" claim (how-many-investors), "Carta's 2026 guidance" (how-much-to-raise), and "many published guides suggest about a working week" (follow-up).
- Fixed literal markdown `[text](/tools/x/)` that rendered as plain text → real anchors, no trailing slash.
- Removed stray `>` paragraphs between email-template blockquotes (follow-up article).
- External source links were NOT re-verified (no network); check them before launch.

## Links
- No internal links with trailing slashes remain; signup CTAs use /#join.

## Tools
- Labels, button types and aria-live="polite" on results were already present.
- Added role="group" + aria-label to the signal checkbox list in the Signal Decoder.

## articles.html
- "New guides" section had been inserted inside the "Coming soon" `<h2>`. Moved it out as a sibling before the "Coming soon" section; the four draft cards and the two live older articles are intact.
