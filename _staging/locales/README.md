# Locale drafts — NOT PUBLIC

Every page here has `<meta name="robots" content="noindex,nofollow">`, no canonical, no hreflang, and is excluded from `sitemap.xml`; `robots.txt` disallows `/_staging/` and `vercel.json` sends `X-Robots-Tag: noindex, nofollow`.

## SK / CS — full drafts (`machine_draft_fluent_reviewed_needs_native_approval`)
Built by `scripts/build_locale_staging.py` from complete translated content: VC Says hub + 10 entries, tools hub + 4 tools (with `assets/tools.locale.js`, math identical to EN — see `scripts/locale_tools_parity.js`), 3 articles, localized signup/cookie chrome (`assets/site.locale.js`). AI fluent pass only — NOT approved by a native human. Review with `docs/vc-says/REVIEWER_CHECKLIST.md`.

## DE / PL — light drafts (`machine_draft_needs_native_review`)
Built by `scripts/build_vc_says.py`: localized UI chrome + phrase seeds; entry body copy is still the English source.

Do not move anything into `/sk/`, `/cs/`, `/de/` or `/pl/` until a native reviewer approves it (docs/vc-says/EDITORIAL_WORKFLOW.md).
