#!/usr/bin/env python3
"""Build the VC Says library (static HTML).

Source of truth: data/vc_signals.expanded.json + data/i18n/*.json
Chrome (header/footer/signup) is copied verbatim from tools/investor-signal-decoder.html.

Outputs
  vc-says.html                         EN hub (published)
  vc-says/{slug}.html                  EN detail pages (only records with publication.en == approved/published)
  sitemap.xml                          adds /vc-says + EN detail URLs (idempotent)
  robots.txt                           adds Disallow: /_staging/ (idempotent)
  Main nav + footer "Learn" links      "VC Says" added to hubs, tools/*, articles/* (idempotent)
  _staging/locales/{sk,cs,de,pl}/...        full-content drafts via scripts/build_locale_staging.py (noindex, no hreflang, not in sitemap)

Usage: python3 scripts/build_vc_says.py [--no-staging] [--no-nav]
"""
import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://thefundraisinggame.com"
LASTMOD = "2026-11-09"
PUBLIC_EN_STATUSES = {"approved_for_en_milestone", "published"}
DRAFT_LOCALES = ["sk", "cs", "de", "pl"]

NAV_LINK_STYLE = "color: rgb(207, 197, 186); text-decoration: none; min-height: 44px; display: inline-flex; align-items: center;"
NAV_LINK_ACTIVE_STYLE = "color: rgb(245, 154, 106); text-decoration: none; min-height: 44px; display: inline-flex; align-items: center;"
FOOT_LINK_STYLE = "color: rgb(207, 197, 186); text-decoration: none; padding: 4px 0px;"

TOOLS = {
    "investor-signal-decoder": "Investor Signal Decoder",
    "investor-follow-up-builder": "Investor Follow-up Builder",
    "fundraising-pipeline-calculator": "Fundraising Pipeline Calculator",
    "runway-raise-calculator": "Runway & Raise Calculator",
}
CLASS_ORDER = ["positive", "ambiguous", "soft-no", "hard-no"]
STAGES = [("pre-seed", "Pre-seed"), ("seed", "Seed"), ("series-a", "Series A")]
TOPIC_LABELS = {"stage": "Stage", "thesis": "Thesis & fit", "timing": "Timing", "process": "Process",
                "traction": "Traction", "terms": "Round & terms"}
CONTEXT_LABELS = {"first-contact": "First contact", "event": "At an event", "post-meeting": "After a meeting",
                  "email": "By email", "active-process": "During a process", "rejection": "Declining feedback",
                  "silence": "Silence"}
DECODER_NEXT = [("", "Not sure"), ("none", "No next step at all"), ("vague", "Vague (“keep us posted”)"),
                ("specific", "A specific date or meeting"), ("materials", "Requested specific materials"),
                ("internal", "Brought in another partner from their fund"), ("otherfund", "Suggested a different fund")]
DECODER_ELAPSED = [("", "Not sure"), ("short", "Less than a week"), ("mid", "1–3 weeks"),
                   ("long", "More than 3 weeks"), ("missed", "A promised date has passed")]
# Mirrors RULES in assets/growth/vc-says.js (test_vc_says.py checks the IDs stay in sync).
DECODER_RULES = [
    ("R1", "A specific date or meeting was offered → genuine-interest and conditional readings move up; polite-pass moves down."),
    ("R2", "They requested specific materials → interest/conditional readings move up."),
    ("R3", "They brought in another partner from their own fund → process/interest readings move up."),
    ("R4", "They suggested a different fund → fit/mandate mismatch moves up."),
    ("R5", "No next step at all → polite-pass reading moves up."),
    ("R6", "Only a vague next step (“keep us posted”) → conditional and polite-pass readings move up slightly."),
    ("R7", "More than three weeks with no concrete next step → polite-pass moves up."),
    ("R8", "A promised date has passed → stalled-process/bandwidth and polite-pass readings move up."),
    ("R9", "Less than a week has passed → too soon to read much into timing; logistics readings move up slightly."),
    ("R10", "Pre-seed + “too early”/“traction” → many funds start later, so stage mismatch moves up slightly."),
]

e = lambda s: html.escape(str(s), quote=True)


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def write(p, s):
    full = os.path.join(ROOT, p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(s)
    return p


def load():
    data = json.loads(read("data/vc_signals.expanded.json"))
    i18n = {l: json.loads(read(f"data/i18n/{l}.json")) for l in ["en"] + DRAFT_LOCALES}
    return data, i18n


def public_en(records):
    return [r for r in records if r["publication"]["en"] in PUBLIC_EN_STATUSES]


def article_titles():
    out = {}
    for p in glob.glob(os.path.join(ROOT, "articles", "*.html")):
        slug = os.path.splitext(os.path.basename(p))[0]
        m = re.search(r"<title>([^<]+)</title>", open(p, encoding="utf-8").read())
        out[slug] = html.unescape(m.group(1).split(" | ")[0].strip()) if m else slug
    return out


# --------------------------------------------------------------------------- nav patching
def patch_nav_html(s):
    changed = False
    m = re.search(r'(<nav aria-label="Main"[^>]*>)(.*?)(</nav>)', s, re.S)
    if m and 'href="/vc-says"' not in m.group(2):
        inner = m.group(2)
        am = re.search(r'<a href="/articles"[^>]*>Articles</a>', inner)
        link = f'<a href="/vc-says" style="{NAV_LINK_STYLE}">VC Says</a>'
        inner = inner[:am.end()] + link + inner[am.end():] if am else inner + link
        s = s[:m.start(2)] + inner + s[m.end(2):]
        changed = True
    m = re.search(r'(<nav aria-label="Learn"[^>]*>)(.*?)(</nav>)', s, re.S)
    if m and 'href="/vc-says"' not in m.group(2):
        inner = m.group(2)
        tm = re.search(r'<a href="/tools"[^>]*>Tools</a>', inner)
        link = f'<a href="/vc-says" style="{FOOT_LINK_STYLE}">VC Says</a>'
        inner = inner[:tm.end()] + link + inner[tm.end():] if tm else inner + link
        s = s[:m.start(2)] + inner + s[m.end(2):]
        changed = True
    return s, changed


def patch_nav():
    targets = ["index.html", "tools.html", "articles.html"] + sorted(
        os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "tools", "*.html")) + glob.glob(os.path.join(ROOT, "articles", "*.html")))
    changed = []
    for t in targets:
        if not os.path.exists(os.path.join(ROOT, t)):
            continue
        s, c = patch_nav_html(read(t))
        if c:
            write(t, s)
            changed.append(t)
    return changed


# --------------------------------------------------------------------------- chrome
def chrome():
    src = read("tools/investor-signal-decoder.html")
    src, _ = patch_nav_html(src)
    header = re.search(r'<div class="sc-host"><header.*?</header></div>', src, re.S).group(0)
    header = header.replace(f'<a href="/tools" aria-current="page" style="{NAV_LINK_ACTIVE_STYLE}">Tools</a>',
                            f'<a href="/tools" style="{NAV_LINK_STYLE}">Tools</a>')
    header_active = header.replace(f'<a href="/vc-says" style="{NAV_LINK_STYLE}">VC Says</a>',
                                   f'<a href="/vc-says" aria-current="page" style="{NAV_LINK_ACTIVE_STYLE}">VC Says</a>')
    footer = re.search(r'<div class="sc-host"><div style="font-family: Geist, system-ui, sans-serif; color: rgb\(242, 232, 220\);"><section aria-labelledby="nl-title".*?</footer></div></div>', src, re.S).group(0)
    assert 'aria-current="page"' in header_active and "linkedin.com/company/the-fundraising-game" in header_active
    return header_active, footer


BASE_STYLE = """body{margin:0;background:#12141C}
a{color:#F59A6A}a:hover{color:#F2E8DC}
input::placeholder,textarea::placeholder{color:#8C8378}
.scp0:hover { background: rgb(34, 38, 58) !important; }
.scp1:hover { background: rgb(245, 154, 106) !important; }
.scp2:hover { background: rgb(178, 58, 30) !important; }
html{scroll-behavior:smooth}img{max-width:100%;height:auto}"""


def head(title, desc, canonical=None, lang="en", robots=None, breadcrumbs=None):
    parts = [f'<!DOCTYPE html>\n<html lang="{e(lang)}">\n<head>', '<meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             f"<title>{e(title)}</title>", f'<meta name="description" content="{e(desc)}">']
    if robots:
        parts.append(f'<meta name="robots" content="{e(robots)}">')
    if canonical:
        parts += [f'<link rel="canonical" href="{e(canonical)}">']
    parts.append('<link rel="icon" type="image/png" href="/favicon.png">')
    if canonical:
        parts += ['<meta property="og:type" content="article">', '<meta property="og:site_name" content="The Fundraising Game">',
                  f'<meta property="og:title" content="{e(title)}">', f'<meta property="og:description" content="{e(desc)}">',
                  f'<meta property="og:url" content="{e(canonical)}">', f'<meta property="og:image" content="{SITE}/assets/og-image.jpg">',
                  '<meta name="twitter:card" content="summary_large_image">', f'<meta name="twitter:title" content="{e(title)}">',
                  f'<meta name="twitter:description" content="{e(desc)}">', f'<meta name="twitter:image" content="{SITE}/assets/og-image.jpg">']
    parts += ['<link rel="preconnect" href="https://fonts.googleapis.com">',
              '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
              '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&amp;family=Geist:wght@400;500;600;700&amp;family=Geist+Mono:wght@400;500&amp;display=swap">',
              f"<style>\n{BASE_STYLE}\n</style>", '<link rel="stylesheet" href="/assets/growth/vc-says.css">']
    if breadcrumbs:
        ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(breadcrumbs)]}
        parts.append(f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    parts.append("</head>")
    return "\n".join(parts)


def breadcrumb_nav(items):
    lis = []
    for i, (name, href) in enumerate(items):
        if i:
            lis.append('<li aria-hidden="true">/</li>')
        if href:
            lis.append(f'<li><a href="{e(href)}" style="color: rgb(185, 175, 164); text-decoration: none;">{e(name)}</a></li>')
        else:
            lis.append(f'<li><span aria-current="page" style="color: rgb(242, 232, 220);">{e(name)}</span></li>')
    return ('<nav aria-label="Breadcrumb" style="max-width: 1240px; margin: 0px auto; padding: 28px 24px 0px; font-family: &quot;Geist Mono&quot;, monospace; font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase;">'
            '<ol style="list-style: none; margin: 0px; padding: 0px; display: flex; flex-wrap: wrap; gap: 8px; color: rgb(140, 131, 120);">' + "".join(lis) + "</ol></nav>")


def page(head_html, header, footer, main, body_attrs="", banner=""):
    return (f"{head_html}\n<body{body_attrs}>\n{banner}"
            '<div class="sc-host"><div style="background: rgb(18, 20, 28); color: rgb(242, 232, 220); font-family: Geist, system-ui, sans-serif; font-size: 18px; line-height: 1.7; min-height: 100vh;">\n'
            f"{header}\n{main}\n{footer}\n</div></div>\n"
            '<script src="/site.js" defer></script>\n<script src="/assets/growth/vc-says.js" defer></script>\n</body>\n</html>\n')


def class_label(t, c):
    return t["strings"].get(f"class_{c}", c)


def pills(r, t):
    out = [f'<span class="vc-pill cls-{e(r["signalClass"])}">{e(class_label(t, r["signalClass"]))}</span>']
    if r["recordType"] == "behavior":
        out.append(f'<span class="vc-pill">{e(t["strings"]["behavior_badge"])}</span>')
    out += [f'<span class="vc-pill">{e(TOPIC_LABELS.get(x, x))}</span>' for x in r["topicTags"]]
    return '<p class="vc-meta">' + "".join(out) + "</p>"


def book_cta(t):
    s = t["strings"]
    return ('<aside class="vc-panel" aria-label="The book"><h2>Fundraising is a relationship, not just a spreadsheet.</h2>'
            f'<p>VC Dating Secrets is a book about the human side of raising capital. {e(s["book_language_note"])}</p>'
            f'<a class="vc-btn" data-signup-cta href="/#join">{e(s["book_cta"])}</a></aside>')


DISCLAIMER = '<p style="font-size:13px;color:rgb(140,131,120)">Educational content and illustrative tools only; not legal, investment or tax advice. Interpretations describe possibilities, not what any particular investor thinks.</p>'


# --------------------------------------------------------------------------- hub
def card(r, t):
    en = r["locales"]["en"]
    href = f"/vc-says/{r['slug']}"
    return (f'<li class="vc-card" data-vc-id="{e(r["id"])}" data-class="{e(r["signalClass"])}" data-stage="{e(" ".join(r["stageTags"]))}" '
            f'data-topic="{e(" ".join(r["topicTags"]))}" data-context="{e(" ".join(r["contexts"]))}">'
            f'{pills(r, t)}<h3><a href="{href}">{e(en["phrase"])}</a></h3><p>{e(en["shortAnswer"])}</p>'
            f'<a class="vc-more" href="{href}" aria-label="See how to respond to “{e(en["phrase"])}”">{e(t["strings"]["see_how_to_respond"])}</a></li>')


def select(id_, label, options):
    opts = "".join(f'<option value="{e(v)}">{e(l)}</option>' for v, l in options)
    return f'<div class="vc-field"><label for="{id_}">{e(label)}</label><select id="{id_}">{opts}</select></div>'


def search_index(pub):
    idx = []
    for r in pub:
        en = r["locales"]["en"]
        idx.append({"id": r["id"], "url": f"/vc-says/{r['slug']}", "phrase": en["phrase"], "synonyms": en["synonyms"],
                    "shortAnswer": en["shortAnswer"], "signalClass": r["signalClass"], "recordType": r["recordType"],
                    "topicTags": r["topicTags"], "stageTags": r["stageTags"], "contexts": r["contexts"],
                    "clarifyingQuestion": en["clarifyingQuestion"],
                    "interpretations": [{"kind": i["kind"], "possibility": i["possibility"]} for i in en["interpretations"]],
                    # draft locale phrase seeds: used ONLY for local search matching, never displayed
                    # seedPhrase (if a fluent pass revised the phrase) keeps the public EN hub byte-identical
                    "localePhrases": [r["locales"][l].get("seedPhrase", r["locales"][l]["phrase"]) for l in DRAFT_LOCALES]})
    return json.dumps(idx, ensure_ascii=False).replace("</", "<\\/")


def build_hub(pub, t, header, footer, titles):
    s = t["strings"]
    all_ = s["filter_all"]
    topics = sorted({x for r in pub for x in r["topicTags"]}, key=lambda x: list(TOPIC_LABELS).index(x) if x in TOPIC_LABELS else 99)
    contexts = [c for c in CONTEXT_LABELS if any(c in r["contexts"] for r in pub)]
    classes = [c for c in CLASS_ORDER if any(r["signalClass"] == c for r in pub)]
    controls = (
        '<section class="vc-wrap" aria-labelledby="vc-browse-title" style="display:flex;flex-direction:column;gap:18px;padding-bottom:40px">'
        '<h2 id="vc-browse-title">Browse the library</h2>'
        '<form id="vc-search-form" role="search" class="vc-panel" onsubmit="return false">'
        f'<div class="vc-field"><label for="vc-q">{e(s["search_label"])}</label><div class="vc-searchrow">'
        f'<input id="vc-q" type="search" autocomplete="off" placeholder="{e(s["search_placeholder"])}" aria-describedby="vc-count">'
        f'<button id="vc-q-clear" type="button" class="vc-btn secondary" hidden>{e(s["search_clear"])}</button></div></div>'
        '<div class="vc-controls">'
        + select("vc-f-stage", s["filter_stage"], [("", all_)] + STAGES)
        + select("vc-f-class", s["filter_signal"], [("", all_)] + [(c, class_label(t, c)) for c in classes])
        + select("vc-f-topic", s["filter_topic"], [("", all_)] + [(x, TOPIC_LABELS.get(x, x)) for x in topics])
        + select("vc-f-context", s["filter_context"], [("", all_)] + [(c, CONTEXT_LABELS[c]) for c in contexts])
        + f'<button id="vc-reset" type="button" class="vc-btn secondary">{e(s["filter_reset"])}</button></div>'
        f'<p id="vc-count" class="vc-count" aria-live="polite" data-template="{e(s["results_count"])}">{e(s["results_count"].replace("{n}", str(len(pub))))}</p>'
        '</form>'
        f'<ul id="vc-list" class="vc-grid">{"".join(card(r, t) for r in pub)}</ul>'
        f'<p id="vc-empty" class="vc-empty" hidden>{e(s["no_results"])}</p>'
        '<p class="vc-count">More entries are in editorial review and will be added once they are complete. Default order is editorial relevance — not a data-driven ranking.</p>'
        '</section>')
    decoder = (
        '<section class="vc-wrap" aria-labelledby="vc-dec-title" style="padding-bottom:40px"><div class="vc-panel">'
        f'<span class="vc-eyebrow">{e(s["decoder_title"])}</span>'
        '<h2 id="vc-dec-title">Not sure which one you got? Try the mini decoder.</h2>'
        f'<p class="vc-notice" id="vc-privacy">{e(s["privacy_note"])}</p>'
        '<div class="vc-field"><label for="vc-dec-paste">Paste the investor’s message (optional)</label>'
        '<textarea id="vc-dec-paste" rows="3" autocomplete="off" placeholder="e.g. Thanks for the time — you’re a bit early for us, but keep us posted." aria-describedby="vc-privacy vc-dec-paste-hint"></textarea>'
        '<p id="vc-dec-paste-hint" class="vc-why" aria-live="polite"></p></div>'
        '<div class="vc-controls">'
        + select("vc-dec-stage", "Your round", [("", "Not sure")] + STAGES)
        + select("vc-dec-category", "What they said or did", [("", "Choose…")] + [(r["id"], r["locales"]["en"]["phrase"]) for r in pub])
        + select("vc-dec-next", "Next step offered", DECODER_NEXT)
        + select("vc-dec-elapsed", "Time since last contact", DECODER_ELAPSED)
        + '</div>'
        f'<button id="vc-dec-run" type="button" class="vc-btn">{e(s["decoder_run"])} →</button>'
        '<div id="vc-dec-out" class="vc-decoder-out" aria-live="polite"></div>'
        f'<p class="vc-why">{e(s["decoder_disclaimer"])}</p>'
        '<details class="vc-rules"><summary>See the rules the decoder uses</summary><p>Each library entry lists 2–3 possible interpretations, each tagged as interest, conditional, mismatch, polite pass or logistics/noise. These rules move them up or down; ties keep the editorial order.</p><ul>'
        + "".join(f"<li><b>{rid}</b> — {e(txt)}</li>" for rid, txt in DECODER_RULES)
        + '</ul></details></div></section>')
    article_links = "".join(f'<li><a href="/articles/{e(a)}">{e(titles.get(a, a))}</a></li>' for a in
                            ["vc-too-early-meaning", "signs-vc-interested", "how-to-follow-up-with-vc-after-meeting",
                             "questions-to-ask-venture-capitalists", "how-many-investors-to-contact", "how-vcs-make-decisions"] if a in titles)
    tool_links = "".join(f'<li><a href="/tools/{k}" data-vc-tool="{k}">{e(v)}</a></li>' for k, v in TOOLS.items())
    related = (
        '<section class="vc-narrow" style="display:flex;flex-direction:column;gap:22px;padding-bottom:72px">'
        '<div class="vc-section"><h2>Free tools that work with this library</h2><ul class="vc-links">' + tool_links + '</ul>'
        '<p style="color:rgb(207,197,186)">The <a href="/tools/investor-signal-decoder" data-vc-tool="investor-signal-decoder">Investor Signal Decoder</a> weighs what investors <em>did</em>; the <a href="/tools/investor-follow-up-builder" data-vc-tool="investor-follow-up-builder">Follow-up Builder</a> drafts your reply. Each entry here links to both.</p></div>'
        '<div class="vc-section"><h2>Related guides</h2><ul class="vc-links">' + article_links + '</ul></div>'
        f'<p class="vc-label">{e(s["editorial_label"])}</p><p style="color:rgb(207,197,186)">{e(s["editorial_note"])}</p>'
        + book_cta(t) + DISCLAIMER + '</section>')
    hero = ('<div class="vc-hero"><span class="vc-eyebrow">Free library · Investor language</span>'
            f'<h1>{e(s["hub_title"])}</h1><p class="vc-lead">{e(s["hub_subtitle"])} {e(s["hub_lead"])}</p>'
            '<p class="vc-meta"><span class="vc-pill">No account required</span><span class="vc-pill">Runs locally in your browser</span>'
            f'<span class="vc-pill">{e(s["editorial_label"])}</span></p></div>')
    main = (f'<main class="tfg-vcsays">{breadcrumb_nav([(s["breadcrumb_home"], "/"), (s["nav_vc_says"], None)])}{hero}{controls}{decoder}{related}'
            f'<script type="application/json" id="vc-says-index">{search_index(pub)}</script></main>')
    title = "VC Says vs. What It Means: Decode Investor Feedback | The Fundraising Game"
    desc = "Common things VCs say — “too early”, “keep in touch”, “send me your deck” — with possible meanings, signals to watch, a question to ask and a reply to copy."
    h = head(title, desc, f"{SITE}/vc-says", breadcrumbs=[("Home", f"{SITE}/"), ("VC Says", f"{SITE}/vc-says")])
    return write("vc-says.html", page(h, header, footer, main, ' data-vc-hub="en"'))


# --------------------------------------------------------------------------- detail
def ul(items):
    return "<ul>" + "".join(f"<li>{e(x)}</li>" for x in items) + "</ul>"


def detail_main(r, t, titles, by_id, s_en=None, draft_locale=None):
    s = t["strings"]
    en = r["locales"]["en"]
    phrase = r["locales"][draft_locale]["phrase"] if draft_locale else en["phrase"]
    hub_href = "/vc-says"
    is_beh = r["recordType"] == "behavior"
    body_lang = ' lang="en"' if draft_locale else ""
    interp = "".join(f'<li><b>{e(i["possibility"])}</b><span class="vc-clues">Clues: {e(i["contextualClues"])}</span></li>' for i in en["interpretations"])
    srcs = r.get("sources") or []
    src_html = (f'<p class="vc-label">{e(s["editorial_label"])}</p><p>{e(s["editorial_note"])}</p>'
                '<p>Evidence type: editorial analysis. No investor quotes, interviews or private messages are used on this page.</p>')
    if srcs:
        src_html += ("<p>Background reading (general context only — not quoted, and not evidence of any specific investor’s intent):</p><ul>"
                     + "".join(f'<li><a href="{e(x["url"])}" rel="noopener" target="_blank">{e(x["title"])}</a></li>' for x in srcs) + "</ul>")
    rel_entries = "".join(f'<li><a href="/vc-says/{e(by_id[x]["slug"])}">{e(by_id[x]["locales"]["en"]["phrase"])}</a></li>'
                          for x in r.get("relatedSignalIds", []) if x in by_id)
    rel_articles = "".join(f'<li><a href="/articles/{e(a)}">{e(titles.get(a, a))}</a></li>' for a in r.get("relatedArticleSlugs", []) if a in titles)
    rel_tools = "".join(
        f'<li><a href="/tools/{e(k)}{"?signal=" + e(r["id"]) if k == "investor-follow-up-builder" else ""}" data-vc-tool="{e(k)}">{e(TOOLS[k])}</a></li>'
        for k in r.get("relatedToolSlugs", []) if k in TOOLS)
    said_note = '<p class="vc-why">This is an observed behaviour rather than something the investor said.</p>' if is_beh else ""
    syn = f'<p class="vc-why">Also phrased as: {e(" · ".join("“" + x + "”" for x in en["synonyms"]))}</p>' if en["synonyms"] else ""
    fub = f'/tools/investor-follow-up-builder?signal={e(r["id"])}'
    main = (
        f'<main class="tfg-vcsays">{breadcrumb_nav([(s["breadcrumb_home"], "/"), (s["nav_vc_says"], hub_href), (phrase, None)])}'
        f'<div class="vc-hero"><span class="vc-eyebrow">VC Says · {e(class_label(t, r["signalClass"]))}</span>'
        f'<h1>{e(phrase if draft_locale else en["h1"])}</h1>{pills(r, t)}'
        f'<p class="vc-label">{e(s["editorial_label"])} · Updated {e(r["revisedAt"])}</p></div>'
        f'<article class="vc-narrow"{body_lang} style="display:flex;flex-direction:column;padding-bottom:72px">'
        f'<p class="vc-lead" style="padding-bottom:28px">{e(en["shortAnswer"])}</p>'
        f'<section class="vc-section"><h2>{e(s["h_what_they_said"])}</h2><blockquote class="vc-quote">{e(en["phrase"])}</blockquote>{said_note}{syn}</section>'
        f'<section class="vc-section"><h2>{e(s["h_might_mean"])}</h2><p>Several readings are plausible. Context decides — not the words alone.</p><ul class="vc-interp">{interp}</ul></section>'
        f'<section class="vc-section"><h2>What strengthens or weakens the signal</h2><div class="vc-two">'
        f'<div><h3>{e(s["h_strengthens"])}</h3>{ul(en["positiveSignals"])}</div><div><h3>{e(s["h_weakens"])}</h3>{ul(en["weakSignals"])}</div></div></section>'
        f'<section class="vc-section"><h2>{e(s["h_ask"])}</h2><p class="vc-ask">{e(en["clarifyingQuestion"])}</p></section>'
        f'<section class="vc-section"><h2>{e(s["h_next"])}</h2><p>{e(en["recommendedAction"])}</p>'
        f'<h3>{e(s["h_timing"])}</h3><p>{e(en["followUpTimingNote"])}</p></section>'
        f'<section class="vc-section" aria-labelledby="vc-reply-h"><h2 id="vc-reply-h">{e(s["h_reply"])}</h2>'
        f'<p class="vc-why">Edit the text, replace the [brackets], then copy. Nothing is sent or saved — it stays in your browser.</p>'
        f'<label for="vc-reply" class="vc-label">Editable reply</label>'
        f'<textarea id="vc-reply" class="vc-reply" spellcheck="true">{e(en["editableReplyTemplate"])}</textarea>'
        f'<div class="vc-copyrow"><button id="vc-copy" type="button" class="vc-btn" data-ok="{e(s["copied"])}" data-fail="{e(s["copy_failed"])}">{e(s["copy"])}</button>'
        f'<button id="vc-reply-reset" type="button" class="vc-btn secondary">Reset text</button>'
        f'<span id="vc-copy-status" class="vc-status" role="status" aria-live="polite"></span></div>'
        f'<p class="vc-why">Want a fuller email with your own details? <a href="{fub}" data-vc-tool="investor-follow-up-builder">Open it in the Investor Follow-up Builder</a>.</p></section>'
        f'<section class="vc-section"><h2>{e(s["h_example"])}</h2><p class="vc-why">{e(s["hypothetical"])} — not a real company or investor.</p><p>{e(en["exampleScenario"]["description"])}</p></section>'
        f'<section class="vc-section"><h2>{e(s["h_sources"])}</h2>{src_html}</section>'
        f'<section class="vc-section"><h2>{e(s["h_related"])}</h2>'
        + (f'<h3>More VC Says entries</h3><ul class="vc-links">{rel_entries}</ul>' if rel_entries else "")
        + (f'<h3>Guides</h3><ul class="vc-links">{rel_articles}</ul>' if rel_articles else "")
        + (f'<h3>Tools</h3><ul class="vc-links">{rel_tools}</ul>' if rel_tools else "")
        + f'<p><a href="{hub_href}">← All VC Says entries</a></p></section>'
        + book_cta(t) + DISCLAIMER + "</article></main>")
    return main


def build_detail(r, t, header, footer, titles, by_id):
    en = r["locales"]["en"]
    url = f"{SITE}/vc-says/{r['slug']}"
    h = head(en["metaTitle"], en["metaDescription"], url,
             breadcrumbs=[("Home", f"{SITE}/"), ("VC Says", f"{SITE}/vc-says"), (en["phrase"], url)])
    attrs = f' data-vc-signal="{e(r["id"])}" data-vc-class="{e(r["signalClass"])}"'
    return write(f"vc-says/{r['slug']}.html", page(h, header, footer, detail_main(r, t, titles, by_id), attrs))


# --------------------------------------------------------------------------- staging (drafts)
# All four draft locales (SK/CS/DE/PL) are built from full locale content by scripts/build_locale_staging.py.
# (The former DE/PL "light draft" path that rendered the English body has been removed.)


def build_staging(records, pub, i18n, header, footer, titles, by_id):
    out = []
    import build_locale_staging  # SK/CS/DE/PL full-content drafts (hub, 10 entries, 4 tools + hub, 3 articles, locale JS)
    out += build_locale_staging.build_all()
    write("_staging/locales/README.md",
          "# Locale drafts — NOT PUBLIC\n\nEvery page here has `<meta name=\"robots\" content=\"noindex,nofollow\">`, no canonical, "
          "no hreflang, and is excluded from `sitemap.xml`; `robots.txt` disallows `/_staging/` and `vercel.json` sends "
          "`X-Robots-Tag: noindex, nofollow`.\n\n"
          "## SK / CS / DE / PL — full drafts (`machine_draft_fluent_reviewed_needs_native_approval`)\n"
          "Built by `scripts/build_locale_staging.py` from complete translated content: VC Says hub + 10 entries, tools hub + 4 tools "
          "(with `assets/tools.locale.js`, math identical to EN — see `scripts/locale_tools_parity.js`), 3 articles, localized "
          "signup/cookie chrome (`assets/site.locale.js`). AI fluent pass only — NOT approved by a native human. "
          "Review with `docs/vc-says/REVIEWER_CHECKLIST.md`.\n\n"
          "DE uses formal *Sie*, PL a formal register (Państwo / gender-neutral forms); see `docs/vc-says/REVIEW_DE.md`, `REVIEW_PL.md`.\n\n"
          "Do not move anything into `/sk/`, `/cs/`, `/de/` or `/pl/` until a native reviewer approves it (docs/vc-says/EDITORIAL_WORKFLOW.md).\n")
    return out


# --------------------------------------------------------------------------- sitemap / robots
def update_sitemap(pub):
    s = read("sitemap.xml")
    urls = [f"{SITE}/vc-says"] + [f"{SITE}/vc-says/{r['slug']}" for r in pub]
    add = "".join(f"  <url><loc>{u}</loc><lastmod>{LASTMOD}</lastmod></url>\n" for u in urls if f"<loc>{u}</loc>" not in s)
    if add:
        s = s.replace("</urlset>", add + "</urlset>")
        write("sitemap.xml", s)
    return bool(add)


def update_robots():
    s = read("robots.txt")
    if "Disallow: /_staging/" in s:
        return False
    s = s.replace("Allow: /\n", "Allow: /\nDisallow: /_staging/\n", 1) if "Allow: /\n" in s else s.rstrip("\n") + "\nDisallow: /_staging/\n"
    write("robots.txt", s)
    return True


def main():
    args = set(sys.argv[1:])
    data, i18n = load()
    records = data["records"]
    by_id_all = {r["id"]: r for r in records}
    pub = public_en(records)
    by_id = {r["id"]: r for r in pub}
    titles = article_titles()
    nav_changed = [] if "--no-nav" in args else patch_nav()
    header, footer = chrome()
    t = i18n["en"]
    written = [build_hub(pub, t, header, footer, titles)]
    written += [build_detail(r, t, header, footer, titles, by_id) for r in pub]
    staging = [] if "--no-staging" in args else build_staging(records, pub, i18n, header, footer, titles, by_id)
    sm = update_sitemap(pub)
    rb = update_robots()
    print(f"VC Says build: {len(pub)} public EN entries, {len(records) - len(pub)} drafts kept out of public build")
    print("  public pages:", len(written))
    for w in written:
        print("   ", w)
    print("  staging draft files:", len(staging))
    print("  nav patched:", ", ".join(nav_changed) if nav_changed else "(already up to date)")
    print("  sitemap updated:", sm, "| robots updated:", rb)
    assert set(by_id_all) >= set(data["priority_ids"])


if __name__ == "__main__":
    main()
