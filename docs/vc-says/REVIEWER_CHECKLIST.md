# Native reviewer checklist — SK / CS (for Slavomír and native reviewers)

Everything below is a **draft**: `machine_draft_fluent_reviewed_needs_native_approval` (AI fluent pass, no native human yet). Language-specific findings: [REVIEW_SK.md](REVIEW_SK.md), [REVIEW_CS.md](REVIEW_CS.md).

## 0. Open the drafts (≈2 min)
```bash
cd tfg-vc-says-impl
python3 -m http.server 8000
# SK: http://localhost:8000/_staging/locales/sk/vc-says/   (also /tools/ and /articles/vc-too-early-meaning.html)
# CS: http://localhost:8000/_staging/locales/cs/vc-says/
```
Use the `.html` file names locally (e.g. `/_staging/locales/sk/vc-says/too-early.html`). On a Vercel preview, clean URLs work and `X-Robots-Tag: noindex` is sent.

## 1. Decisions only Slavomír can make (blocking)
| # | Decision | Options | Where it applies |
|---|---|---|---|
| D1 | Brand name in SK/CS | keep „VC Says“ everywhere / „VC hovorí“ + „VC říká“ (current UI) | `data/i18n/{sk,cs}.json` `nav_vc_says`, entry `metaTitle` suffix |
| D2 | Founder gender in templates | masculine (current) / „rád(a)“ / neutral rewrites / UI hint | `editableReplyTemplate`, `clarifyingQuestion` in `data/locales/{sk,cs}/vc_signals.first10.json` |
| D3 | Greeting + vocative | „Dobrý deň/den, [Investor name],“ + hint to use vocative/title / „Vážený pane / Vážená paní“ | same + `data/locales/{sk,cs}/tools.json` `email.greeting` |
| D4 | CS capital „Vy/Vám/Váš“ in emails | capitals (CS entries now) / lowercase (tools now) | CS templates |
| D5 | Jargon | trakcia/trakce, pipeline, runway, burn, term sheet, update vs „správa o pokroku / zpráva o pokroku“ | all |
| D6 | PL/DE register (later) | PL UI currently informal „Ty“; DE formal „Sie“ | `data/i18n/{pl,de}.json` |

## 2. Per-entry review (10 × SK, 10 × CS)
For each `_staging/locales/{loc}/vc-says/{slug}.html`:
- [ ] **Phrase** sounds like something a SK/CS investor would actually say. If the seed was better, restore it (the seed is in `seedPhrase`).
- [ ] **Synonyms** are realistic variants (these drive local search).
- [ ] **Short answer + interpretations** keep the EN meaning: possibilities, not diagnoses, and no probabilities.
- [ ] **Clarifying question** is polite, formal and natural to send as-is.
- [ ] **Reply template**: formal register, correct greeting and sign-off. These placeholders stay **verbatim English**: `[Company] [Investor name] [Your name] [topic] [progress] [milestone] [specific next step] [Partner name] [Fund] [customer] [outcome]`. Other bracket hints may be reworded but must stay in brackets.
- [ ] **Example** still says it is hypothetical.
- [ ] **Meta title/description** read well in a search result (≈60 / ≈155 characters).

## 3. Tools (4 per locale)
- [ ] Signal decoder: tick a few combinations. Do the result title, description and next step read naturally? (The logic is identical to EN; this is verified automatically.)
- [ ] Follow-up builder: try all 7 scenarios with and without your own inputs. The email must read naturally when fields are empty (bracket placeholders) and when filled.
- [ ] Pipeline and runway: check the labels and notes. Numbers display as „1 200,5“, „713 000 €“ and „15,1 %“ (default inputs), and the currency stays EUR.

## 4. Articles (3 per locale)
- [ ] Flow, headings, tables, FAQ. Is the tone suitably direct without being blunt?
- [ ] Templates inside the articles follow the D2–D4 decisions.
- [ ] The CTA says the book is English-only.

## 5. Chrome
- [ ] Nav/footer labels, signup box, captcha texts, success/error messages, cookie banner (`data/locales/{loc}/chrome_signup.json`).
- [ ] Book disclosure everywhere: SK „zatiaľ iba v angličtine“ / CS „zatím pouze v angličtině“.

## 6. How to edit and rebuild
1. Edit the source: entries in `data/locales/{loc}/vc_signals.first10.json`, UI in `data/i18n/{loc}.json`, tools in `data/locales/{loc}/tools.json`, chrome in `data/locales/{loc}/chrome_signup.json`, articles in `content/articles/{loc}/{slug}.md`.
2. `python3 scripts/build_vc_says.py` (rebuilds EN, which stays byte-identical, plus all staging; merges the SK/CS entries into `data/vc_signals.expanded.json`).
3. `python3 scripts/test_vc_says.py && python3 scripts/test_locale_drafts.py`. Both must pass.

## 7. Recording approval (only a native human may do this)
- Per entry: set `editorialReviewer` to your name, `reviewedAt` to the date, and `reviewNote` to what you checked. Only then change `status` to `native_approved` in the mirror file.
- Approval is a precondition for publication, not publication itself. Going live still requires moving pages to `/sk/` and `/cs/`, adding self-canonicals and reciprocal hreflang (EN plus approved locales only), and adding sitemap entries. The tests currently assert that nothing is approved or public, so update them in the same change.
