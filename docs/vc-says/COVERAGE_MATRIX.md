# VC Says — coverage matrix (EN milestone, 2026-11-09)

Status vocabulary: **published** = live, indexable, in sitemap · **approved_for_en_milestone** = EN editorial draft approved for this milestone by project instruction (no named human reviewer recorded yet) · **draft (staging)** = generated under `_staging/locales/`, `noindex,nofollow`, not in sitemap, no hreflang · **seed only** = phrase string exists in data, no page · **—** = not built.

No locale other than EN has been reviewed by a native speaker. Nothing below claims human translation approval.

## Locale × surface

| Locale | Hub `/vc-says` | Detail pages (10 priority) | Draft entries (20) | UI strings (`data/i18n`) | Tools (4) localized | Sitemap | hreflang |
|---|---|---|---|---|---|---|---|
| en | published (`/vc-says`) | 10 × approved_for_en_milestone → built at `/vc-says/{slug}` | seed only (not built) | source of truth | EN (existing) | hub + 10 | none (no reciprocal locale live) |
| sk | draft (staging) `_staging/locales/sk/vc-says/` | 10 × draft (staging): SK phrase + SK UI chrome, EN body | seed only (`phrases.json`) | machine_draft_needs_native_review | — | excluded | excluded |
| cs | draft (staging) | 10 × draft (staging) | seed only | machine_draft_needs_native_review | — | excluded | excluded |
| de | draft (staging) | 10 × draft (staging) | seed only | machine_draft_needs_native_review | — | excluded | excluded |
| pl | draft (staging) | 10 × draft (staging) | seed only | machine_draft_needs_native_review | — | excluded | excluded |

## Entry × locale

| Entry ID | Class | en | sk | cs | de | pl | Follow-up Builder scenario (`?signal=`) |
|---|---|---|---|---|---|---|---|
| too-early | soft-no | approved_for_en_milestone | draft | draft | draft | draft | tooearly |
| not-right-fit | hard-no | approved_for_en_milestone | draft | draft | draft | draft | notfit |
| keep-in-touch | soft-no | approved_for_en_milestone | draft | draft | draft | draft | update |
| circle-back-next-quarter | ambiguous | approved_for_en_milestone | draft | draft | draft | draft | update |
| send-deck | ambiguous | approved_for_en_milestone | draft | draft | draft | draft | meeting |
| second-meeting | positive | approved_for_en_milestone | draft | draft | draft | draft | meeting |
| partner-introduction | positive | approved_for_en_milestone | draft | draft | draft | draft | meeting |
| need-more-traction | soft-no | approved_for_en_milestone | draft | draft | draft | draft | tooearly |
| no-lead-investor | soft-no | approved_for_en_milestone | draft | draft | draft | draft | nolead |
| investor-ghosting (behaviour) | soft-no | approved_for_en_milestone | draft | draft | draft | draft | quiet |
| 20 remaining seed IDs | mixed | draft (seed only) | seed only | seed only | seed only | seed only | — |

## Tools × integration

| Tool | VC Says link | Shared signal IDs | Locale |
|---|---|---|---|
| Investor Signal Decoder | static links + dynamic "Related phrase guide" after interpreting (wrong→not-right-fit, noresponse→investor-ghosting, partner→partner-introduction, next→second-meeting, polite→keep-in-touch) | yes | EN only |
| Investor Follow-up Builder | `?signal=ID` preselects scenario + shows link to entry; unknown IDs ignored | yes (10) | EN only |
| Fundraising Pipeline Calculator | nav + footer only | — | EN only (numbers via existing en-US formatting) |
| Runway & Raise Calculator | nav + footer only | — | EN only |

## Remaining before any non-EN publication
1. Native review of `data/i18n/{sk,cs}.json` and the 10 entries' full body copy (not just phrases).
2. Move approved locale pages from `_staging/locales/{loc}/` to `/{loc}/vc-says/`, add self-canonicals, reciprocal hreflang (en + reviewed locales only), sitemap entries.
3. Localize tool labels; keep formulas unchanged and use `Intl.NumberFormat` for display only.
