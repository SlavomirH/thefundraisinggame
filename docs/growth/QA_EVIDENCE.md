# QA evidence — growth release 2026-11-09 (Europe/Bratislava)

## Automated (Playwright set_content + system Chrome)
- PASS: 15 routes render with H1 + canonical (no trailing slash except homepage)
- PASS: Tools nav link present
- PASS: Pipeline defaults → 30.0 / 9.0 / 1.80 / 1.08 / 112
- PASS: Runway defaults → €713,000 raise, 15.1% dilution
- PASS: Signal decoder Insufficient → Meaningful → mismatch paths
- PASS: Follow-up builder includes company; HTML-like input kept as literal text
- PASS: Signup CTA `/#join` present; existing `form[data-signup]` on older article
- PASS: Homepage `#tfg-tools-blurb`; BlogPosting + WebApplication JSON-LD present
- PASS: No trailing-slash internal hrefs on sample article
- NOT RUN: live signup POST (no authorized test email)
- NOT RUN: visual pixel review / computerUse browser (static tests only)
- NOT RUN: GSC submit

## Claude Code editorial pass
- articles.html New guides section repaired
- Softened unverifiable attributions in three articles
- Fixed markdown-link leftovers; signal decoder group label
- See docs/growth/QA_LOCAL.md

## Rollback
`git revert <release-commit>` on `main` (GitHub Pages rebuilds from main).
