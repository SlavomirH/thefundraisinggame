# VC Says — coverage matrix (updated 2026-11-09, SK/CS draft milestone)

Status vocabulary:
- **published**: live, indexable, in sitemap.
- **approved_for_en_milestone**: EN editorial draft approved for the EN milestone by project instruction (no named human reviewer recorded).
- **`machine_draft_fluent_reviewed_needs_native_approval`** (SK/CS): full translated content, an AI fluent-review pass done, **no native human review**.
- **machine_draft_needs_native_review** (DE/PL): machine draft, lighter pass.
- **draft (staging)**: built under `_staging/locales/`, `noindex,nofollow`, not in sitemap, no hreflang, and `X-Robots-Tag: noindex` via `vercel.json`.
- **seed only**: phrase string exists in data, no page.
- **—**: not built.

**No locale other than EN has been reviewed by a native speaker. Nothing below claims human translation approval. No SK/CS/DE/PL page is public.**

## Locale × surface

| Locale | Hub | Detail pages (10 priority) | Other entries (20) | UI strings (`data/i18n`) | Tools (4 + hub) | Articles (3 priority) | Signup/cookie chrome | Sitemap | hreflang |
|---|---|---|---|---|---|---|---|---|---|
| en | published (`/vc-says`) | 10 × approved_for_en_milestone → `/vc-says/{slug}` | seed only | source of truth (157 keys) | EN (existing, unchanged) | EN (existing, unchanged) | EN (`site.js`, unchanged) | hub + 10 | none |
| sk | draft (staging), full SK hub incl. search, filters, mini decoder (`vc-says.locale.js`) | 10 × `machine_draft_fluent_reviewed_needs_native_approval`, **full SK body** | seed only (1 list on hub) | fluent-reviewed draft, all 157 keys | draft (staging): 4 tools + hub, `tools.locale.js` (math parity tested) | draft (staging): 3 full SK articles from `content/articles/sk/*.md` | draft: `chrome_signup.json` → `site.locale.js` (staging only) | excluded | excluded |
| cs | draft (staging), full CS hub | 10 × `machine_draft_fluent_reviewed_needs_native_approval`, **full CS body** | seed only (`not-proceeding` seed Slovakism fixed) | fluent-reviewed draft, all 157 keys | draft (staging): 4 tools + hub, parity tested | draft (staging): 3 full CS articles | draft: `chrome_signup.json` → `site.locale.js` | excluded | excluded |
| de | draft (staging): DE UI chrome, **EN body** | 10 × draft, EN body copy + DE phrase seed | seed only | machine_draft_needs_native_review, all 157 keys (lighter pass) | — | — | — | excluded | excluded |
| pl | draft (staging): PL UI chrome, **EN body** | 10 × draft, EN body copy + PL phrase seed | seed only | machine_draft_needs_native_review, all 157 keys (lighter pass; informal „Ty“ register to decide) | — | — | — | excluded | excluded |

## Entry × locale

SK/CS phrase marked † = revised from the seed in the fluent pass (seed kept in `seedPhrase`; the public EN hub search index still uses the seed, so public EN output is byte-identical).

| Entry ID | Class | en | sk | cs | de | pl | Follow-up scenario |
|---|---|---|---|---|---|---|---|
| too-early | soft-no | approved_for_en_milestone | fluent draft † | fluent draft | draft (EN body) | draft (EN body) | tooearly |
| not-right-fit | hard-no | approved_for_en_milestone | fluent draft | fluent draft | draft (EN body) | draft (EN body) | notfit |
| keep-in-touch | soft-no | approved_for_en_milestone | fluent draft | fluent draft | draft (EN body) | draft (EN body) | update |
| circle-back-next-quarter | ambiguous | approved_for_en_milestone | fluent draft † | fluent draft † | draft (EN body) | draft (EN body) | update |
| send-deck | ambiguous | approved_for_en_milestone | fluent draft † | fluent draft | draft (EN body) | draft (EN body) | meeting |
| second-meeting | positive | approved_for_en_milestone | fluent draft | fluent draft | draft (EN body) | draft (EN body) | meeting |
| partner-introduction | positive | approved_for_en_milestone | fluent draft | fluent draft | draft (EN body) | draft (EN body) | meeting |
| need-more-traction | soft-no | approved_for_en_milestone | fluent draft † | fluent draft † | draft (EN body) | draft (EN body) | tooearly |
| no-lead-investor | soft-no | approved_for_en_milestone | fluent draft | fluent draft | draft (EN body) | draft (EN body) | nolead |
| investor-ghosting (behaviour) | soft-no | approved_for_en_milestone | fluent draft † | fluent draft † | draft (EN body) | draft (EN body) | quiet |
| 20 remaining seed IDs | mixed | draft (seed only) | seed only | seed only | seed only | seed only | — |

"fluent draft" = `machine_draft_fluent_reviewed_needs_native_approval`.

## Tools × locale

| Tool | EN (public) | SK / CS (staging) | Math | Number display |
|---|---|---|---|---|
| Investor Signal Decoder | unchanged | labels, 8 signal items, 5 result buckets, plural counts („3 vybrané signály“), VC Says links → staging entries | identical (256 combinations compared) | n/a |
| Investor Follow-up Builder | unchanged | 7 scenarios × subject/intro/mid/ask, formal greeting/sign-off, placeholders verbatim, `?signal=` prefill | identical substitution (field-count parity per scenario) | n/a |
| Fundraising Pipeline Calculator | unchanged | labels, metrics, notes | identical (8 input sets incl. clamping) | `Intl.NumberFormat('sk-SK'/'cs-CZ')`, value rounded with the same `toFixed()` first |
| Runway & Raise Calculator | unchanged | labels, metrics, notes, „Bez čistého burnu“ | identical (6 input sets incl. edge cases) | currency stays EUR; „713 000 €“, „15,1 %“ |

## Where things live
- Data: `data/vc_signals.expanded.json` (`locales.sk|cs`, full fields), with mirrors in `data/locales/{sk,cs}/vc_signals.first10.json`.
- Packs: `data/locales/{sk,cs}/tools.json`, `data/locales/{sk,cs}/chrome_signup.json`, and `data/i18n/*.json`.
- Articles: `content/articles/{sk,cs}/*.md`.
- Build: `scripts/build_vc_says.py`, which calls `scripts/build_locale_staging.py` for SK/CS.
- Tests: `scripts/test_vc_says.py` (EN, 300 checks) and `scripts/test_locale_drafts.py` (SK/CS drafts; includes `scripts/locale_tools_parity.js`).

## Remaining before any non-EN publication
1. Native human review of all SK/CS surfaces using [REVIEWER_CHECKLIST.md](REVIEWER_CHECKLIST.md) and decisions D1–D5 (brand, gender, vocative, CS capitalisation, jargon).
2. DE/PL: full entry bodies, tools and articles are **not** translated (only UI chrome and phrase seeds). Optional scope, skipped in this milestone.
3. Public `site.js` is still EN-only. The localized copy exists only as staging `site.locale.js`; a production locale switch needs a decision on how `site.js` picks its strings.
4. At release: move approved pages to `/{loc}/…`, add self-canonicals and reciprocal hreflang (EN plus approved locales only), add sitemap entries, and update the tests that currently assert "nothing approved, nothing public".
