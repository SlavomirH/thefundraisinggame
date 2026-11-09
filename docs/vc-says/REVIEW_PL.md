# PL localization — AI fluent review notes (2026-11-09)

**Status of every PL string:** `machine_draft_fluent_reviewed_needs_native_approval`. This copy has **not been reviewed by a native human**. Nothing here is a native sign-off. All pages live only under `_staging/locales/pl/` (noindex,nofollow, X-Robots-Tag via `vercel.json`, not in sitemap, no hreflang, no public `/pl/` route).

## What was reviewed (AI fluent pass)

| Surface | Source file(s) | Staging output |
|---|---|---|
| 10 VC Says entries (all fields: phrase, synonyms, H1, short answer, interpretations + clues, signals, question, next step, timing, reply template, hypothetical example, meta) | `data/locales/pl/vc_signals.first10.json` → merged into `data/vc_signals.expanded.json` (`locales.pl`) | `_staging/locales/pl/vc-says/{slug}.html` |
| Hub UI, mini decoder, rules, filters, stages/topics/situations, nav/footer chrome (159 keys) | `data/i18n/pl.json` | `_staging/locales/pl/vc-says/index.html` |
| 4 tools + tools hub (labels, 8 signal items with Polish plural forms, 5 result buckets, 7 follow-up email scenarios, pipeline/runway labels, notes, disclaimers) | `data/locales/pl/tools.json` | `_staging/locales/pl/tools/*.html` + `assets/tools.locale.js` (`pl-PL` number display, math identical to EN) |
| 3 articles | `content/articles/pl/*.md` | `_staging/locales/pl/articles/*.html` |
| Signup, captcha, cookie banner, VIP list copy | `data/locales/pl/chrome_signup.json` | footer + `assets/site.locale.js` |

Process: (1) translation drafts by three separate drafting passes (entries / tools+chrome+i18n / articles), each with its own self-critique; (2) an **independent** critical fluent-reviewer pass over all PL sources with cross-file consistency fixes; (3) orchestrator spot-checks; (4) automated checks (`scripts/test_locale_drafts.py`: placeholders, structure parity, no English UI left, Polish function-word ratio, English-only book disclosure, math parity via `scripts/locale_tools_parity.js`).

## Register decision (documented choice)
- **Formal professional register.** The reader/founder is addressed with formal **„Państwo”** or impersonal forms („warto”, „należy”, infinitive instructions). Short UI buttons use the usual Polish imperative/infinitive convention („Kopiuj”, „Wybierz”).
- The earlier light draft of `pl.json` used informal „Ty/Twój”; it was replaced. A grep for `\bTy\b|\bTwó|\bTwoj|\bCiebie|\bCi\b` over all PL sources returns **0** hits (26 before the independent pass).
- **Founder → investor emails:** formal and gender-neutral. „Dzień dobry, [Investor name],” → capitalized paragraph → „Z pozdrowieniami” → `[Your name]`. **Pan/Pani is avoided** (it would force a gender guess and a vocative on an uninflectable English placeholder); „Państwo” is used where the fund team is addressed; impersonal forms elsewhere.
- **No gendered founder first person** (chciałbym/chciałabym, byłem/byłam, wdzięczny/wdzięczna): „chętnie prześlę”, „z góry dziękuję”, „udało nam się”.
- **Investor quotes** (phrase, synonyms) keep the plural „wy” of the seeds (investor speaking to the founding team).

## Issues found and fixed
**Register**
- Entries used informal imperatives/2nd person throughout: „Zapytaj więc o ten kamień milowy…” → „Warto zapytać o ten kamień milowy…”; „Przedstawiają Cię inwestorowi” → „Przedstawiają założycieli inwestorowi”; „osiągniesz”, „Wyślij” → impersonal/infinitive forms.

**Calques**
- „waży to, co inwestorzy zrobili” → „ocenia…”; „spotkanie z pitchem” → „po pitchu”; „pytanie do zadania” → „pytanie doprecyzowujące”; „wehikuł” (vehicle) → „fundusz”; „zaadresować obawy” removed; „cieszę się na” removed; „Momentum” → „Poczucie rozpędu”; decoder rules „idą w górę” → „wyżej/niżej”.

**Placeholders and case**
- Placeholders are positioned so they stay nominative: „weźmie udział [Partner name]”, „funduszu [Fund]”, „firmą [Company]”, „dotyczące tematu: [topic]”.
- Partner-introduction phrase made gender-neutral: „Przedstawię was jednemu z naszych partnerów.” (seed kept in `seedPhrase` and as a synonym).

**Consistency / terminology**
- Tool names unified to the `tools.json` H1s (articles had „Kreator follow-upów”, „Dekoder sygnałów inwestorów”): Dekoder sygnałów od inwestorów · Generator wiadomości follow-up do inwestorów · Kalkulator lejka fundraisingowego · Kalkulator runwayu i rundy.
- One email convention everywhere (entries, tool greeting/sign-off, article templates).
- „inwestor wiodący” (explained once as „tzw. lead”; „lead” only in investor-quote synonyms); „kwota inwestycji” (not „wielkość tiketu”); „koinwestor”; „założyciel” (not „founder”); „lejek (fundraisingowy)” (not „pipeline”); „przedstawienie” (not „intro”); „informacja zwrotna” (not „feedback”); kept „trakcja”, „kamień milowy”.
- Signal decoder count uses Polish plural rules: „1 wybrany sygnał / 3 wybrane sygnały / 5 wybranych sygnałów”.

## Remaining risks requiring a native human
1. **„Dzień dobry, Alex,”** with an uninflected name — natural enough, or reintroduce a vocative / „Szanowna Pani / Szanowny Panie”?
2. **„Państwo” for a single investor** in places where the fund team is meant.
3. **Case of user-filled text** after „dla” / „pomaga” (`[customer]`, `[outcome]`) — founders must inflect what they type.
4. **Anglicism acceptance:** „trakcja”, „deck”, „follow-up” as an inflected noun, „runwayu”, „burn”, „term sheet”, „due diligence”.
5. **Tone of „Z pozdrowieniami”** vs warmer „Pozdrawiam serdecznie”.
6. **Placeholders stay English tokens** (`[Company]`, `[Investor name]`, …) per the DE/PL task constraint, unlike SK/CS which now use localized labels (commit f033e60). See REVIEWER_CHECKLIST D7.
7. **SEO:** meta titles/descriptions untested against real PL search phrasing; the no-lead entry phrase/H1/meta were changed in the independent pass.
8. Links to EN-only articles are labelled „(po angielsku)”.

## Checklist for the human reviewer (PL)
- [ ] Read all 10 entries on `_staging/locales/pl/vc-says/` and mark any phrase a Polish investor would not say.
- [ ] Confirm the register (Państwo / impersonal, no Ty) and the greeting decision (D6).
- [ ] Check every reply template: formal, gender-neutral, placeholders verbatim (`[Company]`, `[Investor name]`, `[Your name]`, `[milestone]`, …).
- [ ] Run the 4 tools; read all 7 follow-up scenarios with empty and filled fields; check the plural forms of the signal count.
- [ ] Read the 3 articles end to end (flow, headings, FAQ, tables).
- [ ] Confirm the English-only book wording („Książka ukaże się wkrótce – na razie tylko po angielsku.”).
- [ ] Record name + date per `REVIEWER_CHECKLIST.md` → "Recording approval".
