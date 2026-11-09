# Multilingual VC Says — test and launch acceptance

## Automated route/SEO tests

- [ ] English homepage and all original URLs unchanged; no redirect chains or broken newsletter signup.
- [ ] Each public `en` / `sk` / `cs` / `de` / `pl` page renders a localized full main body in initial HTML.
- [ ] `<html lang>` matches content language. Correct UTF-8 characters and typography.
- [ ] Each published locale page has localized title, description, unique H1 and **self-referencing canonical**.
- [ ] `hreflang` points only to actual live equivalents; each hreflang group is fully reciprocal and includes self. `x-default` optional and correct.
- [ ] Draft, unfinished, filtered and query-parameter result pages not indexed or in sitemap.
- [ ] No broken assets/404s. All locale-switcher destinations exist. Missing locale goes to the corresponding language hub, not an English page disguised as translated.
- [ ] Hubs and detail pages appear in nav/internal links and actual deployed sitemap.
- [ ] No fake SEO claims, keyword-volume fields, or published investor quotes without attributable sources.

## Library interaction tests

- [ ] Search "too early", "zostaňme v kontakte", "zu früh", "zbyt wczesnym etapie" finds appropriate entries (search locale behavior documented).
- [ ] Filter by stage, signal class, topic and context works; reset clears all filters.
- [ ] No result state is meaningful in all live languages.
- [ ] Signal detail lists multiple plausible meanings and evidence cues, not a deterministic label.
- [ ] Copy response yields correct language string and works without empty placeholders.
- [ ] Edit the proposed email and copy; no network request transmitting text if client-side only.
- [ ] Optional phrase-input mini decoder treats uncertainty honestly and processes pasted input locally.
- [ ] Related articles, tool pages and book CTA go to working correct-language destinations.
- [ ] The existing Signal Decoder and Follow-up Builder do not contradict the library; links and shared signal IDs resolve.

## Existing tools: localization regression

- [ ] All four tool calculators/builders run in English and every published language.
- [ ] Core numeric calculations do not change with locale; only format changes. Test decimal separators, negative/zero inputs, ranges and copy output.
- [ ] Investor Follow-up Builder uses correct language, professional register and updated context.
- [ ] Signup success event only fires when provider confirms registration, with legitimate test credentials.

## Accessibility and mobile

- [ ] Keyboard navigable search, filters, language switcher, accordions and copy actions.
- [ ] Correct labels/aria for controls, focus state, contrast and semantic headings.
- [ ] Mobile view ~375 px: no horizontal overflow, long Polish/German phrases wrap, cards and CTA visible.
- [ ] Low JavaScript or blocked JS still shows useful crawlable entry text and links.

## Analytics/privacy

- [ ] Locale, signal ID and allowed categorization events tracked once, with consent where needed.
- [ ] No raw pasted message, email content, founder financials, names, email addresses or sensitive information captured by analytics or server logs.
- [ ] Events verified by a real test session, not assumed.

## Review/release requirements

- [ ] First 10 entries genuinely editorial-reviewed and substantively localized in each launched language.
- [ ] Source links inspected, claims supported, named interviews approved and saved in audit trail.
- [ ] Search volumes only reported if source, country, timeframe and account export are available.
- [ ] Staging screenshot and test log captured for each locale.
- [ ] Publish via existing approved production workflow, smoke test live HTTPS URLs and preserve rollback plan.
- [ ] Deliver a coverage matrix: Locale × pages × tools × entries × approved/published, and complete live URL list.
