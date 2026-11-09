# SK localization — AI fluent review notes (2026-11-09)

**Status of every SK string:** `machine_draft_fluent_reviewed_needs_native_approval`. This copy has **not been reviewed by a native human**. Nothing here is a native sign-off. All pages live only under `_staging/locales/sk/` (noindex,nofollow, not in sitemap, no hreflang).

## What was reviewed (AI fluent pass)

| Surface | Source file(s) | Staging output |
|---|---|---|
| 10 VC Says entries (all fields: phrase, synonyms, H1, short answer, interpretations + clues, signals, question, next step, timing, reply template, hypothetical example, meta) | `data/locales/sk/vc_signals.first10.json` → merged into `data/vc_signals.expanded.json` (`locales.sk`) | `_staging/locales/sk/vc-says/{slug}.html` |
| Hub UI, mini decoder, rules, filters, stages/topics/situations, nav/footer chrome | `data/i18n/sk.json` | `_staging/locales/sk/vc-says/index.html` |
| 4 tools + tools hub (labels, signal checklist, result texts, 7 follow-up email scenarios, pipeline/runway labels, notes, disclaimers) | `data/locales/sk/tools.json` | `_staging/locales/sk/tools/*.html` + `assets/tools.locale.js` |
| 3 articles | `content/articles/sk/*.md` | `_staging/locales/sk/articles/*.html` |
| Signup, captcha, cookie banner, VIP list copy | `data/locales/sk/chrome_signup.json` | footer + `assets/site.locale.js` |

Process: (1) translation draft; (2) a separate critical "fluent reviewer" pass over every string; (3) an independent spot-check of templates and questions by the orchestrating pass, with fixes applied to the source files; (4) automated checks (`scripts/test_locale_drafts.py`: placeholders, structure parity, no English UI left, English-only book disclosure, math parity).

## Issues found and fixed

**False friends and wrong collocations**
- „pripomienka“ for a follow-up email. In Slovak this primarily means a remark or objection (cf. *pripomienkové konanie*). Changed to „pripomenutie / následná správa“; the calendar reminder keeps „pripomienka“.
- „aktualizácia“ for an investor update sounds like a software update. Changed to „správa o pokroku“ throughout.
- „ohľadom“ (non-standard) avoided in templates.
- „Mäkké nie“ (calque of *soft no*) → „Zdvorilé nie“ (signal class label).

**Calques**
- „Zatiaľ ste pre nás príliš skoro“ → „Na nás je to zatiaľ priskoro“ (the original seed is kept in `seedPhrase` and as a synonym).
- „…alebo to mám zo stola stiahnuť?“ (*take it off your plate*) → „…alebo to mám zatiaľ považovať za uzavreté?“
- „Poďme sa spojiť o pár mesiacov“ (*reconnect*) → „Porozprávajme sa znova o pár mesiacov“
- „positioning“ → „ako sa na trhu profilujete“
- „Váš príbeh sa nedostane k investorovi“ (*isn't getting through*) → „Váš príbeh nie je dosť zrozumiteľný“
- „Ktorá časť vám najťažšie zapadala do obrazu“ (*get comfortable with*) → „Pri ktorej časti ste mali najväčšie pochybnosti?“
- „robiť/dávať zmysel“ in emails replaced by „bolo by vhodné / malo by zmysel“ where it read as an anglicism.
- „Rozlúštite spätnú väzbu … bez zbytočného premýšľania“ → „Porozumejte spätnej väzbe investorov bez zbytočného hĺbania“

**Grammar and case traps with placeholders**
- „Od [časové obdobie] sme [kľúčový pokrok]“ (broken verb slot) → „Za [časové obdobie] sme dosiahli [kľúčový pokrok]“
- „uzavrieť kolo do [cieľový mesiac]“ (requires genitive) → „uzavretie kola momentálne plánujeme na [cieľový mesiac]“
- „poslať po [milestone]“ (requires locative) → „po dosiahnutí míľnika [milestone]“, in both the template and the question.
- „Je pre vás [Company] stále zaujímavá“ (gender depends on the company name) → „Máte o [Company] stále záujem“
- „Rozhovory … vedte“ → „veďte“; „vašu prezentáciu“ → „svoju“ (reflexive possessive); „Vyhovoval by mi [dva termíny]“ → „Mám čas [dva navrhované termíny]“
- „Ďakujem za jasnú odpoveď — naozaj mi pomáha“ (no subject) → „…— veľmi mi pomohla.“

**Formality and gender**
- Vykanie is used throughout. Slovak vykanie uses plural participles („by ste chceli“), which is correct.
- Investor-facing verbs were made gender-neutral where possible. Tool email templates avoid gendered first person entirely („nadväzujem“, „veľmi ocením tip“ instead of „bol by som vďačný“).
- The reusable article reply template switched to neutral „my“ („radi sa vtedy ozveme“).

**Czechisms checked:** none found in final copy (checked forms such as „doporučiť“, „rozhodnutí“, „tiež“ misuse).

## Remaining risks requiring a native human

1. **Gendered founder voice.** VC Says reply templates and questions use the masculine first person („rád“, „sústredil“, „pochopil“, „vďačný“, „stručný“). Female founders must edit these, so the reviewer should decide between a UI hint and a neutral rewrite.
2. **Placeholders inside Slovak syntax.** These must stay verbatim English and cannot inflect: „s [Partner name]“ (instrumental), „pomáhame [customer]“ (dative), „Dobrý deň, [Investor name],“ (formal SK usually says „Dobrý deň, pán Novák,“). A fill-in hint is needed.
3. **Brand naming.** UI uses „VC hovorí“, while `metaTitle` keeps „| VC Says“. Decide one policy.
4. **Jargon acceptance:** „trakcia“, „pipeline“ (gender: masculine used), „asociát“ (VC associate), „seniornejší partner“, „burn“, „runway“, „term sheet“, „pre-money“, „opčný pool“, „kolo s pevným ocenením (priced round)“.
5. **Investor voice.** Do phrases such as „Na nás je to zatiaľ priskoro“, „Kolá nevedieme“ and „Ozvite sa nám znova budúci štvrťrok“ sound like real SK investors?
6. **Lowercase after the greeting comma** („Dobrý deň, …,\n\nďakujem…“) follows SK convention; confirm house style.
7. **SEO.** Titles and descriptions are untested against real SK search phrasing („príliš skoro“ vs „priskoro“). Some `metaTitle`s exceed 60 characters.
8. **Invented labels.** Pipeline stage labels in the follow-up article (Prieskum → Preverený → …) and the tool name „Generátor follow-up e-mailov“ are my own choices.
9. **Footer/nav chrome:** „Pre médiá“, „Časté otázky“, „Tlačová sada a materiály pre médiá“, „Vzdelávanie“.
10. **Untranslated EN pages.** Links to articles that have no SK version point to the EN pages, labelled „(v angličtine)“.

## Checklist for the human reviewer (SK)
- [ ] Read all 10 entries on `_staging/locales/sk/vc-says/` and mark any phrase that does not sound like a real investor.
- [ ] Decide the gender strategy (rád/rada) and the vocative/title hint; apply it to `data/locales/sk/vc_signals.first10.json`.
- [ ] Check every reply template: tone, vykanie, placeholders still verbatim (`[Company]`, `[Investor name]`, `[Your name]`, `[milestone]`, …).
- [ ] Check the tools (`_staging/locales/sk/tools/`): run each tool, read the result texts and all 7 follow-up scenarios.
- [ ] Read the 3 articles end to end (flow, headings, FAQ, tables).
- [ ] Confirm the English-only book wording („Kniha vychádza čoskoro — zatiaľ iba v angličtine.“).
- [ ] Decide on the brand („VC hovorí“ vs „VC Says“) and the jargon list above.
- [ ] Record your name and date (see `REVIEWER_CHECKLIST.md` → "Recording approval").
