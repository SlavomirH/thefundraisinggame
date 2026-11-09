# DE localization — AI fluent review notes (2026-11-09)

**Status of every DE string:** `machine_draft_fluent_reviewed_needs_native_approval`. This copy has **not been reviewed by a native human**. Nothing here is a native sign-off. All pages live only under `_staging/locales/de/` (noindex,nofollow, X-Robots-Tag via `vercel.json`, not in sitemap, no hreflang, no public `/de/` route).

## What was reviewed (AI fluent pass)

| Surface | Source file(s) | Staging output |
|---|---|---|
| 10 VC Says entries (all fields: phrase, synonyms, H1, short answer, interpretations + clues, signals, question, next step, timing, reply template, hypothetical example, meta) | `data/locales/de/vc_signals.first10.json` → merged into `data/vc_signals.expanded.json` (`locales.de`) | `_staging/locales/de/vc-says/{slug}.html` |
| Hub UI, mini decoder, rules, filters, stages/topics/situations, nav/footer chrome (159 keys) | `data/i18n/de.json` | `_staging/locales/de/vc-says/index.html` |
| 4 tools + tools hub (labels, 8 signal items, 5 result buckets, 7 follow-up email scenarios, pipeline/runway labels, notes, disclaimers) | `data/locales/de/tools.json` | `_staging/locales/de/tools/*.html` + `assets/tools.locale.js` (`de-DE` number display, math identical to EN) |
| 3 articles | `content/articles/de/*.md` | `_staging/locales/de/articles/*.html` |
| Signup, captcha, cookie banner, VIP list copy | `data/locales/de/chrome_signup.json` | footer + `assets/site.locale.js` |

Process: (1) translation drafts by three separate drafting passes (entries / tools+chrome+i18n / articles), each with its own self-critique; (2) an **independent** critical fluent-reviewer pass over all DE sources with cross-file consistency fixes; (3) orchestrator spot-checks; (4) automated checks (`scripts/test_locale_drafts.py`: placeholders, structure parity, no English UI left, German function-word ratio, English-only book disclosure, math parity via `scripts/locale_tools_parity.js`).

## Register decision (documented choice)
- **Founder-facing copy and all outbound emails: formal *Sie*** (Sie/Ihnen/Ihr capitalized). German letter convention: „Hallo [Investor name],“ → body starts lowercase → „Viele Grüße“ (no comma) → `[Your name]`.
- Greeting „Hallo“ rather than „Guten Tag“: with a surname („Hallo Frau Berger“) it is normal modern business German with Sie; the follow-up builder's name field example was changed to „z. B. Frau Berger“ to steer users to the surname.
- **Investor quotes** (phrase, synonyms, decoder options, quoted lines) use the informal ihr/euch of the seeds, reflecting common DACH startup speech. Founder text never uses du/ihr.
- First person is gender-neutral in German, so no rád/ráda-type decision is needed.

## Issues found and fixed
**Real UX bug**
- Follow-up scenario labels started with „Sie sagten, es sei noch zu früh“ — a founder reads that as *you* said. Now „Feedback: „noch zu früh““, „Investor will zuerst einen Lead-Investor sehen“.

**Grammar with placeholders**
- „Wir helfen [customer] dabei, [outcome].“ (no verb) → „…, [outcome] zu erreichen.“
- „Seit [Zeitraum] haben wir [wichtigster Fortschritt].“ (no participle) → „… erreicht.“
- `[topic]` is always framed as „zum Thema [topic]“ so the English token needs no case ending.

**Calques / anglicisms**
- „Momentum fühlt sich gut an“ → „Rückenwind tut gut“
- „das Meeting ehrlich genossen“ → „das Gespräch hat mir ehrlich gefallen“
- „ausgedrückt durch Nicht-Antworten“ → „im Ausbleiben einer Antwort“
- „wird nach der Übergabe still“ → „meldet sich … nicht mehr“
- „Engagement“ (= commitment in German) → „Interesse“
- „meinem Partner“ (can read as life partner) → „einem meiner Partner“
- „Mismatch“ → „fehlende Passung“; „Weiches Nein“ → „Höfliches Nein“; „VC sagt“ → brand „VC Says“
- singular „Bedenken“ → „Einwand / Sorge“ (5×); „Investment-These“ → „Investmentthese“

**Style**
- „Behandeln Sie den Investor als nicht Teil…“ → „Zählen Sie den Investor nicht zu…“; duplicated „vorab … Vorab-Unterlage“ removed; word order fixed in „wenn Sie unterscheiden zwischen…“.

**Consistency**
- Tool names unified to the `tools.json` H1s everywhere (articles had „Investoren-Signal-Decoder“, „Follow-up-Generator“): Investorensignal-Decoder · Follow-up-Generator für Investoren · Fundraising-Pipeline-Rechner · Runway- und Finanzierungsrechner.
- Early-access CTA unified to „Early Access sichern“ (articles had „Frühzugang sichern“).
- Two decoder hint strings that were still English in the old light draft are translated; footer tagline now discloses English-only.

## Remaining risks requiring a native human
1. **„Hallo“ vs „Guten Tag“** for a *first* email to an investor; and whether `[Investor name]` should be a first name or „Frau/Herr + surname“.
2. **Investor voice: ihr vs Sie.** Many DACH VCs say Sie to founders, especially outside Berlin; decide per brand.
3. **Anglicism level:** Traction (chosen over the calque „Traktion“; seed kept as synonym), Lead-Investor, Ticketgröße, Pitch Deck, Term Sheet, Due Diligence, Series A, Runway, Burn, Momentum, Timing, Early Access.
4. **Placeholders stay English tokens** (`[Company]`, `[Investor name]`, …) per the DE/PL task constraint, unlike SK/CS which now use localized labels (commit f033e60). See REVIEWER_CHECKLIST D7.
5. **Generic masculine** („Investor“, „Gründer“) throughout.
6. **Number display** „713.000 €“, „15,1 %“ (de-DE) — confirm house style for Austria/Switzerland (CHF not offered; currency stays EUR).
7. **SEO:** meta titles/descriptions untested against real DE search phrasing; „VC Says“ brand suffix kept.
8. Links to EN-only articles are labelled „(auf Englisch)“.

## Checklist for the human reviewer (DE)
- [ ] Read all 10 entries on `_staging/locales/de/vc-says/` and mark any phrase a DACH investor would not say.
- [ ] Decide D6 (ihr vs Sie in investor quotes) and the greeting (Hallo / Guten Tag).
- [ ] Check every reply template: Sie register, lowercase after greeting comma, placeholders verbatim (`[Company]`, `[Investor name]`, `[Your name]`, `[milestone]`, …).
- [ ] Run the 4 tools; read all 7 follow-up scenarios with empty and filled fields.
- [ ] Read the 3 articles end to end (flow, headings, FAQ, tables).
- [ ] Confirm the English-only book wording („Das Buch erscheint in Kürze – vorerst nur auf Englisch.“).
- [ ] Record name + date per `REVIEWER_CHECKLIST.md` → "Recording approval".
