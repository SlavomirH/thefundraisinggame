# Implementation specification — multilingual site and VC Says database

## 1. Desired product

Book-led editorial site + free tool suite + searchable "VC Says vs. What It Means" knowledge base. A founder enters from Google via a specific question, sees actionable context, uses a short reply/template, follows related tools, and can optionally join the book early-access list. The tool must NOT claim knowledge of the investor's private intentions or guarantee investment.

## 2. URL map

Preserve the REAL existing English URLs, including homepage and all article links; do not force `/en/`. Add only routes missing in production. For the new library:

| Locale | Hub | Example detail |
|---|---|---|
| English | `/vc-says/` | `/vc-says/too-early/` |
| Slovak | `/sk/vc-says/` | `/sk/vc-says/too-early/` |
| Czech | `/cs/vc-says/` | `/cs/vc-says/too-early/` |
| German | `/de/vc-says/` | `/de/vc-says/too-early/` |
| Polish | `/pl/vc-says/` | `/pl/vc-says/too-early/` |

Stable universal slugs allow straightforward locale switching and no translation collisions; user-visible titles and browser metadata MUST be localized. Prefer canonical stable IDs for records. Add localized tool variants e.g. `/sk/tools/investor-signal-decoder/` if existing route structure supports it, keeping English URL intact.

## 3. Architecture and file organization

Discover actual site tech first (do not assume Next.js, Astro, React, etc.). Choose simplest framework-native build process. The application can remain static: locale JSON dictionaries + markdown/MDX article content + validated static JSON dataset + at-build generated detail pages; dynamic search/filter powered by client JavaScript. Rendering must contain real main content in initial HTML; don't make all useful content dependent on client-side JS.

Suggested conceptual structures (adapt to actual repo):

```
src/content/vc-signals/{stable-id}.json
src/content/articles/{locale}/{article-id}.md
src/i18n/{locale}.json
src/i18n/locales.ts
src/components/LocaleSwitcher
src/components/VcSaysSearch
src/components/VcSaysEntry
src/components/ReplyBuilder
src/lib/hreflang.ts
src/lib/search-index.ts
scripts/validate-locales
scripts/validate-vc-says
```

Maintain an explicit locale publication registry: `draft`, `needs-review`, `approved`, `published`; build only published, complete translations into the public sitemap and hreflang groups. A missing locale should not be served as mixed-language filler. English root is source-of-truth for fixed code labels, not unverified source-of-truth for local cultural claims.

## 4. Records and editorial schema

The attached seed JSON contains 30 canonical phrases/behaviors, stage and topic tags, preliminary phrase translations, possible interpretations, observable cues, clarifier question, and next step. The seed does not contain attributed quotes. Use a stronger final schema such as:

```
Signal {
  id: string; slug: string; recordType: "phrase" | "behavior";
  stageTags: ("pre-seed"|"seed"|"series-a")[];
  topicTags: string[]; signalClass: "positive"|"ambiguous"|"soft-no"|"hard-no";
  contexts: string[];
  sources: {url:string; title:string; publicationDate?:string; reviewedDate:string; claimSupported:string}[];
  evidenceType: "independent-public-source"|"author-experience"|"approved-interview"|"editorial-analysis";
  interviewPermission?: {consentId:string; quoteApproved:boolean; permissionDate:string};
  revisedAt:string;
  locales: Record<Locale, {
    status:"draft"|"needs-review"|"approved"|"published";
    phrase:string; synonyms:string[]; h1:string; shortAnswer:string;
    interpretations:{possibility:string; contextualClues:string}[];
    positiveSignals:string[]; weakSignals:string[];
    clarifyingQuestion:string; recommendedAction:string;
    followUpTimingNote:string; editableReplyTemplate:string;
    exampleScenario:{description:string; hypothetical:boolean};
    metaTitle:string; metaDescription:string; editorialReviewer?:string; reviewedAt?:string;
  }>;
}
```

**Never** transform seed's `possible_meanings_en` into categorical assertions. Do not show a "90% rejection" probability unsupported by reliable observation. Display uncertainty as prose, not fake precision.

## 5. UX — library homepage

Hero: "VC Says vs. What It Means" / "Decode investor feedback without overthinking it." A supportive subheading: "Common phrases, possible interpretations, signals to watch, and an exact next step."

- Search bar: type a phrase or topic, instant client-side results; clear button; proper keyboard and screen-reader semantics.
- Filter controls: `Stage`, `Signal`, `Topic`, `Situation` and Reset; counts update. Default sort editorial relevance, then alphabetical, not a fake data-driven ranking.
- Signal card: exact common phrase, neutral classification, 1–2 sentence summary and 'See how to respond'. Indicate if it is an observed behavior rather than an utterance.
- Detail: "What they said", "What it might mean", "What strengthens or weakens the signal", "What to ask", "What to do next", "A reply you can adapt", sources, related entries and book CTA.
- Editable reply with Copy button, no automatic emailing; show confirmation after copying.
- Optional **mini decoder**: ask contextual questions (round stage, words vs actions, next meeting, promised timeline). Use transparent decision rules, returning a ranked *list of plausible interpretations* and recommended clarifier; no chat transcripts uploaded without consent.
- User submission: optional "Suggest a phrase" button. Do not send investor message by default; if implemented, provide a privacy-aware form and moderation queue with explicit consent.
- Book CTA should state real available language and upcoming status; preserve existing real signup.

## 6. Localization implementation

Launch order: English content maintained; SK and CS first; DE and PL after native-language review. Architect but don't expose ES/FR/PT/IT to search until complete. Translators adapt financial terminology, grammatical gender/formality, metaphors, realistic follow-up etiquette, units/currency formats and regional explanations; don't conflate `sk` with Slovakia-only or `de` with Germany-only. Context notes by country must cite real local evidence.

All strings must be localized: nav, footer, tools, article body, H1/H2, filters, no-result text, form validation, email copies, disclaimer, privacy and CTA; never launch a page with only translated boilerplate.

Money dates and decimal formatting use locale-aware built-ins, preserving numeric business logic. Example: EUR `1,200.50` (en) vs `1 200,50` (sk, depending on locale formatter). Locale change should preserve entered state when safe; never silently change the amount's currency or underlying calculation. Avoid mutating English source text to use translation string IDs blindly if doing so would damage existing copy or SEO.

## 7. SEO and crawling

- Each published language equivalent has a distinct indexable URL, human-useful HTML, its own meta title/description and self-canonical.
- Build reciprocal `hreflang` alternate sets only for exact conceptual equivalents that actually exist and are indexable. Include a self-entry and optional `x-default` pointing to English hub/fallback page where appropriate. Use valid ISO language tags: `en`, `sk`, `cs`, `de`, `pl`.
- Do not canonicalize SK/CS/DE/PL page to English; that can suppress intended locale pages. Do not automatically redirect by browser language or IP address.
- Include all published pages in a sitemap (or framework sitemap), excluding drafts, filters, `?query=`, and private results. No more than one URL should canonically represent each locale/entry.
- Use `<html lang="...">`, visible locale-appropriate content, localized internal linking and alternate-language switcher.
- Structured data only if genuinely applicable and valid, e.g. BreadcrumbList and Article for editorial articles. Do not rely on FAQ-rich results for ordinary founder sites.
- Ensure local articles aren't mechanically duplicated with different keywords. If content offers little beyond a translated one-sentence fragment, keep it on the hub instead of creating an indexable thin detail page.
- Measure GSC by page+query+country. Avoid implying Google Search uses `llms.txt` for AI search ranking.

Example detail markup (URLs illustrate the structure; generate tags only for actually-published locale versions):

```html
<link rel="canonical" href="https://thefundraisinggame.com/sk/vc-says/too-early/">
<link rel="alternate" hreflang="en" href="https://thefundraisinggame.com/vc-says/too-early/">
<link rel="alternate" hreflang="sk" href="https://thefundraisinggame.com/sk/vc-says/too-early/">
<link rel="alternate" hreflang="cs" href="https://thefundraisinggame.com/cs/vc-says/too-early/">
<!-- Add de, pl only when genuinely live and reciprocal -->
```

## 8. Integration with existing growth tools

Existing Investor Signal Decoder becomes a short scenario/input front door; the new database provides structured related content and contextual deep-links. Avoid two different contradictory interpretations of the same phrase. Investor Follow-up Builder should accept a signal ID and locale to preselect appropriate drafting templates. Pipeline and Runway calculators retain mathematical logic but localize labels/output, not formulas. Every screen provides relevant article and book links; don't overdo CTAs.

## 9. Analytics, privacy, and metrics

Reuse existing PostHog/other analytics if installed. Event properties: `locale`, `signal_id`, `signal_class`, `stage`, `source_path`, `channel`, `published_version`. Events: `vc_says_hub_view`, `vc_says_search_used` (DO NOT log raw user query), `vc_says_filter_used`, `vc_says_entry_view`, `vc_says_reply_copied`, `vc_says_related_tool_opened`, `signup_cta_clicked`, `signup_success` (ONLY on provider-confirmed success). Never log raw pasted investor messages, company financials, contact info, replies or copied text. Respect consent and the existing privacy policy; do not auto-install duplicate trackers.

Dashboard by locale: indexed pages, search impressions, clicks, relevant query coverage, organic sessions, page engagement, reply copies, tool use, CTA click-through, successful newsletter signups; distinguish observed numbers from estimates.

## 10. Definition of done

A production URL matrix for every live locale, working filters/reply builder, reviewed first 10 detailed entries, verified current signup, no broken old routes, correct reciprocal SEO annotations, passing tests (see LAUNCH_TESTS), reviewed native copy and a truthful release report.
