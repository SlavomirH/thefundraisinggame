# CS localization — AI fluent review notes (2026-11-09)

**Status of every CS string:** `machine_draft_fluent_reviewed_needs_native_approval`. This copy has **not been reviewed by a native human**. Nothing here is a native sign-off. All pages live only under `_staging/locales/cs/` (noindex,nofollow, not in sitemap, no hreflang).

## What was reviewed (AI fluent pass)

| Surface | Source file(s) | Staging output |
|---|---|---|
| 10 VC Says entries (all fields) | `data/locales/cs/vc_signals.first10.json` → merged into `data/vc_signals.expanded.json` (`locales.cs`) | `_staging/locales/cs/vc-says/{slug}.html` |
| Hub UI, mini decoder + rules, filters, stages/topics/situations, nav/footer | `data/i18n/cs.json` | `_staging/locales/cs/vc-says/index.html` |
| 4 tools + tools hub | `data/locales/cs/tools.json` | `_staging/locales/cs/tools/*.html` + `assets/tools.locale.js` |
| 3 articles | `content/articles/cs/*.md` | `_staging/locales/cs/articles/*.html` |
| Signup, captcha, cookie banner, VIP copy | `data/locales/cs/chrome_signup.json` | footer + `assets/site.locale.js` |

Process: (1) translation draft; (2) a separate critical "fluent reviewer" pass over every string; (3) an independent spot-check of templates and questions by the orchestrating pass, with fixes applied to the source files; (4) automated checks (`scripts/test_locale_drafts.py`).

## Issues found and fixed

**Formality: Czech vykání agrees in gender, unlike Slovak.** Czech formal address uses singular gendered participles („byl jste“, „chtěl byste“), so every investor-facing verb was checked:
- „děkuji, že jste si udělal čas“ → „děkuji za Váš čas věnovaný [Company]“
- „oceňuji, že jste nás nenechal v nejistotě“ → „oceňuji, že nás nenecháváte v nejistotě“
- „jakou výši investice byste zvážil“ → „jakou výši investice by Váš fond zvážil“ (tools: „jaká výše investice by pro vás přicházela v úvahu“)
- „o čem byste se chtěl dozvídat“ → „co by pro Vás bylo nejzajímavější sledovat“; „abyste to nemusel řešit“ → „ať Vám to nezabírá čas“
- In tool emails, plural-participle shortcuts („byste chtěli“) were replaced by neutral constructions („nebo vás zajímá konkrétní metrika?“)

**Calques and anglicisms**
- „Dávalo by smysl naplánovat…“ → „Bylo by vhodné naplánovat…“
- „positioning“ → „jak se na trhu vymezujete“; „slide“ → „snímek“
- „vynaložit svůj interní kredit“ (*spend internal capital*) → „je ochoten se za vás uvnitř fondu postavit“
- „levný způsob“ (*low-cost way*) → „nenáročný způsob“
- „krátký update“ / „investorský update“ in outgoing emails and advice → „krátká zpráva o pokroku“ / „pravidelné zprávy pro investory“
- „Měkké ne“ (calque of *soft no*) → „Zdvořilé ne“
- „Rozluštěte … bez zbytečného přemýšlení“ → „Porozumějte zpětné vazbě investorů bez zbytečného dumání“

**Grammar and case traps**
- „Ozvěte se nám znovu příští čtvrtletí“ → „… v příštím čtvrtletí“ (seed kept in `seedPhrase`)
- „uzavřít do [cílový měsíc]“ (genitive) → „jako cílový měsíc uzavření kola nyní plánujeme [cílový měsíc]“
- „Od [časové období] jsme …“ → „Za [časové období, např. posledních šest měsíců] jsme …“
- „nepřikládejte formulaci optimismus“ → „nevkládejte do formulace optimismus“; „Můžu“ → „Mohu“ (written register)
- Tool templates use a colon before user-filled slots („Naše nejdůležitější novinka: [progress].“) so any case the user types fits.

**Slovakisms:** checked across all files. One was found in a **seed** outside the 10 entries: `not-proceeding` read „V tejto rundě …“ („tejto“ is Slovak). It is corrected to „V tomto kole nebudeme v investičním procesu pokračovat.“ The original is kept in `seedPhrase`, with `seedFixNote` recorded.

## Remaining risks requiring a native human

1. **Gendered founder voice.** Templates and questions use the masculine first person („rád“, „vděčný“, „stručný“, „soustředil“). Decide between rád/ráda and neutral rewrites.
2. **Vocative.** „Dobrý den, [Investor name],“ only works if the user types the vocative („pane Nováku“, „paní Nováková“). Add a hint.
3. **English placeholders inside Czech sentences:** „pomáháme [customer] [outcome]“ (dative), „z [Fund]“ (genitive; fine for indeclinable fund names), „s [Partner name]“ (instrumental).
4. **Capitalised „Vy/Vám/Váš“.** The fork used capitals in investor-facing emails and questions (letter convention), while the tool email packs and UI use lowercase. Choose one house style.
5. **Jargon acceptance:** „trakce“, „retence“, „pipeline“, „tiket“, „burn“, „runway“, „term sheet“, „business anděl“, „demo day“, plus the colloquial synonym „leada“.
6. **Investor voice** of the phrases („Zatím jste pro nás v příliš rané fázi“, „Potřebujeme vidět větší trakci“).
7. **Brand:** UI „VC říká“ vs `metaTitle` „| VC Says“.
8. **SEO** phrasing untested („příliš brzy“ vs „moc brzy“). Some titles exceed 60 characters.
9. **Invented labels:** pipeline stage names (Průzkum → Prověřený → …), the tool names, and footer labels („Pro média“, „Časté dotazy“, „Vzdělávání“).
10. **Stage name:** UI says „Série A“ while some example texts say „Series A“. Unify.

## Checklist for the human reviewer (CS)
- [ ] Read all 10 entries on `_staging/locales/cs/vc-says/`; flag phrases that sound translated.
- [ ] Check gender agreement in every investor-facing sentence (vykání + participle).
- [ ] Decide rád/ráda, the vocative hint, and capital Vy; apply the decisions in `data/locales/cs/vc_signals.first10.json` and `data/locales/cs/tools.json`.
- [ ] Run all 4 tools on `_staging/locales/cs/tools/`, read every result and all 7 email scenarios.
- [ ] Read the 3 articles end to end.
- [ ] Confirm the English-only book wording („Kniha vychází brzy — zatím pouze v angličtině.“).
- [ ] Record your name and date (see `REVIEWER_CHECKLIST.md`).
