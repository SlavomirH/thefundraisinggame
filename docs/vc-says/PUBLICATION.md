# Locale publication (SK/CS/DE/PL Release A)

**Status:** published on owner approval (2026-11-09, Cursor `pt15u`: “publish them”).

**Not native human review.** AI fluent review provenance: `claude-fluent-pass`. See `data/PUBLICATION_APPROVAL.json`.

## Published routes (per locale)
- `/{loc}/` landing hub (partial-translation disclosure)
- `/{loc}/vc-says/` + 10 priority entries
- `/{loc}/tools/` + 4 tools
- `/{loc}/articles/` — 3 priority guides

## Not published / still English
- Remaining 20 VC Says seed phrases
- Book, author, FAQ, press, reviews, other articles
- English URLs unchanged; reciprocal `hreflang` only among real equivalents

## Rollback
Revert the merge that introduced public `sk/` `cs/` `de/` `pl/` trees and restore prior `sitemap.xml` + EN pages from `main@6a56414`.
