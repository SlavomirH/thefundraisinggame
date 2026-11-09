# VC Says — coverage matrix (updated 2026-11-09, SK/CS/DE/PL draft milestone)

Status vocabulary:
- **published**: live, indexable, in sitemap.
- **approved_for_en_milestone**: EN editorial draft approved for the EN milestone by project instruction (no named human reviewer recorded).
- **`machine_draft_fluent_reviewed_needs_native_approval`** (SK/CS/DE/PL): full translated content, an AI fluent-review pass done, **no native human review**.
- **machine_draft_needs_native_review**: earlier lighter-pass status; no longer used by the 10 priority entries in any locale (the 20 seed-only records keep `draft_machine_translation_needs_native_review`).
- **draft (staging)**: built under `_staging/locales/`, `noindex,nofollow`, not in sitemap, no hreflang, and `X-Robots-Tag: noindex` via `vercel.json`.
- **seed only**: phrase string exists in data, no page.
- **—**: not built.

**No locale other than EN has been reviewed by a native speaker. Nothing below claims human translation approval. No SK/CS/DE/PL page is public.**

## Locale × surface

| Locale | Hub | Detail pages (10 priority) | Other entries (20) | UI strings (`data/i18n`) | Tools (4 + hub) | Articles (3 priority) | Signup/cookie chrome | Sitemap | hreflang |
|---|---|---|---|---|---|---|---|---|---|
| en | published (`/vc-says`) | 10 × approved_for_en_milestone → `/vc-says/{slug}` | seed only | source of truth (159 keys) | EN (existing, unchanged) | EN (existing, unchanged) | EN (`site.js`, unchanged) | hub + 10 | none |
| sk | draft (staging), full SK hub incl. search, filters, mini decoder (`vc-says.locale.js`) | 10 × `machine_draft_fluent_reviewed_needs_native_approval`, **full SK body** | seed only (1 list on hub) | fluent-reviewed draft, all 159 keys | draft (staging): 4 tools + hub, `tools.locale.js` (math parity tested) | draft (staging): 3 full SK articles from `content/articles/sk/*.md` | draft: `chrome_signup.json` → `site.locale.js` (staging only) | excluded | excluded |
| cs | draft (staging), full CS hub | 10 × `machine_draft_fluent_reviewed_needs_native_approval`, **full CS body** | seed only (`not-proceeding` seed Slovakism fixed) | fluent-reviewed draft, all 159 keys | draft (staging): 4 tools + hub, parity tested | draft (staging): 3 full CS articles | draft: `chrome_signup.json` → `site.locale.js` | excluded | excluded |
| de | draft (staging), full DE hub incl. search, filters, mini decoder | 10 × `machine_draft_fluent_reviewed_needs_native_approval`, **full DE body** (formal *Sie* in replies) | seed only | fluent-reviewed draft, all 159 keys | draft (staging): 4 tools + hub, `tools.locale.js` (math parity tested, `de-DE`) | draft (staging): 3 full DE articles | draft: `chrome_signup.json` → `site.locale.js` | excluded | excluded |
| pl | draft (staging), full PL hub incl. search, filters, mini decoder | 10 × `machine_draft_fluent_reviewed_needs_native_approval`, **full PL body** (formal register: Państwo / gender-neutral forms, Pan/Pani only where unavoidable) | seed only | fluent-reviewed draft, all 159 keys | draft (staging): 4 tools + hub, `tools.locale.js` (math parity tested, `pl-PL`) | draft (staging): 3 full PL articles | draft: `chrome_signup.json` → `site.locale.js` | excluded | excluded |

## Entry × locale

SK/CS phrase marked † = revised from the seed in the fluent pass (seed kept in `seedPhrase`; the public EN hub search index still uses the seed, so public EN output is byte-identical).

| Entry ID | Class | en | sk | cs | de | pl | Follow-up scenario |
|---|---|---|---|---|---|---|---|
| too-early | soft-no | approved_for_en_milestone | fluent draft † | fluent draft | fluent draft | fluent draft | tooearly |
| not-right-fit | hard-no | approved_for_en_milestone | fluent draft | fluent draft | fluent draft | fluent draft | notfit |
| keep-in-touch | soft-no | approved_for_en_milestone | fluent draft | fluent draft | fluent draft | fluent draft | update |
| circle-back-next-quarter | ambiguous | approved_for_en_milestone | fluent draft † | fluent draft † | fluent draft | fluent draft | update |
| send-deck | ambiguous | approved_for_en_milestone | fluent draft † | fluent draft | fluent draft | fluent draft | meeting |
| second-meeting | positive | approved_for_en_milestone | fluent draft | fluent draft | fluent draft | fluent draft | meeting |
| partner-introduction | positive | approved_for_en_milestone | fluent draft | fluent draft | fluent draft | fluent draft | meeting |
| need-more-traction | soft-no | approved_for_en_milestone | fluent draft † | fluent draft † | fluent draft | fluent draft | tooearly |
| no-lead-investor | soft-no | approved_for_en_milestone | fluent draft | fluent draft | fluent draft | fluent draft | nolead |
| investor-ghosting (behaviour) | soft-no | approved_for_en_milestone | fluent draft † | fluent draft † | fluent draft | fluent draft | quiet |
| 20 remaining seed IDs | mixed | draft (seed only) | seed only | seed only | seed only | seed only | — |

"fluent draft" = `machine_draft_fluent_reviewed_needs_native_approval`.

## Tools × locale

| Tool | EN (public) | SK / CS / DE / PL (staging) | Math | Number display |
|---|---|---|---|---|
| Investor Signal Decoder | unchanged | labels, 8 signal items, 5 result buckets, plural counts („3 vybrané signály“), VC Says links → staging entries | identical (256 combinations compared) | n/a |
| Investor Follow-up Builder | unchanged | 7 scenarios × subject/intro/mid/ask, formal greeting/sign-off, placeholders per locale policy (SK/CS localized labels, DE/PL verbatim EN tokens), `?signal=` prefill | identical substitution (field-count parity per scenario) | n/a |
| Fundraising Pipeline Calculator | unchanged | labels, metrics, notes | identical (8 input sets incl. clamping) | `Intl.NumberFormat('sk-SK'/'cs-CZ'/'de-DE'/'pl-PL')`, value rounded with the same `toFixed()` first |
| Runway & Raise Calculator | unchanged | labels, metrics, notes, „Bez čistého burnu“ | identical (6 input sets incl. edge cases) | currency stays EUR; SK/CS/PL „713 000 €“, DE „713.000 €“, „15,1 %“ |

## Where things live
- Data: `data/vc_signals.expanded.json` (`locales.sk|cs|de|pl`, full fields for the 10 priority IDs), with mirrors in `data/locales/{sk,cs,de,pl}/vc_signals.first10.json`.
- Packs: `data/locales/{sk,cs,de,pl}/tools.json`, `data/locales/{sk,cs,de,pl}/chrome_signup.json`, and `data/i18n/*.json`.
- Articles: `content/articles/{sk,cs,de,pl}/*.md`.
- Build: `scripts/build_vc_says.py`, which calls `scripts/build_locale_staging.py` for SK/CS/DE/PL.
- Tests: `scripts/test_vc_says.py` (EN, 300 checks) and `scripts/test_locale_drafts.py` (SK/CS/DE/PL drafts; includes `scripts/locale_tools_parity.js`).

## Remaining before any non-EN publication
1. Native human review of all SK/CS/DE/PL surfaces using [REVIEWER_CHECKLIST.md](REVIEWER_CHECKLIST.md), [REVIEW_DE.md](REVIEW_DE.md), [REVIEW_PL.md](REVIEW_PL.md) and decisions D1–D7.
2. Placeholder policy is split: SK/CS show localized bracket labels, DE/PL keep the EN tokens verbatim (task constraint). Decide one policy (D7).
3. Public `site.js` is still EN-only. The localized copy exists only as staging `site.locale.js`; a production locale switch needs a decision on how `site.js` picks its strings.
4. At release: move approved pages to `/{loc}/…`, add self-canonicals and reciprocal hreflang (EN plus approved locales only), add sitemap entries, and update the tests that currently assert "nothing approved, nothing public".
