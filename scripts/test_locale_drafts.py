#!/usr/bin/env python3
"""Checks for the SK/CS localization drafts (staging only). No browser, no network.

Usage: python3 scripts/build_vc_says.py && python3 scripts/test_locale_drafts.py
Exit code 0 = all checks passed. Prints concrete pass/fail counts per section.
"""
import glob
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALES = ["sk", "cs"]
STATUS = "machine_draft_fluent_reviewed_needs_native_approval"
PRIORITY = ["too-early", "not-right-fit", "keep-in-touch", "circle-back-next-quarter", "send-deck",
            "second-meeting", "partner-introduction", "need-more-traction", "no-lead-investor", "investor-ghosting"]
TOOLS = ["investor-signal-decoder", "investor-follow-up-builder", "fundraising-pipeline-calculator", "runway-raise-calculator"]
ARTICLES = ["vc-too-early-meaning", "how-to-follow-up-with-vc-after-meeting", "signs-vc-interested"]
REQUIRED = ["phrase", "synonyms", "h1", "shortAnswer", "interpretations", "positiveSignals", "weakSignals", "clarifyingQuestion",
            "recommendedAction", "followUpTimingNote", "editableReplyTemplate", "exampleScenario", "metaTitle", "metaDescription",
            "status", "reviewNote", "editorialReviewer", "reviewedAt"]
# placeholders that must survive verbatim (machine-substituted or user-facing anchors)
KEEP = ["[Company]", "[Investor name]", "[Your name]", "[topic]", "[progress]", "[milestone]", "[specific next step]",
        "[Partner name]", "[Fund]", "[customer]", "[outcome]"]
DIACRITICS = {"sk": "áäčďéíĺľňóôŕšťúýž", "cs": "áčďéěíňóřšťúůýž"}
LANG_MARKERS = {"sk": ["ľ", "ä", "ô", "ĺ", "ŕ"], "cs": ["ř", "ě", "ů"]}
EN_STOP = {"the", "and", "you", "your", "with", "for", "that", "this", "what", "is", "are", "of", "it", "they", "we", "or", "be", "not"}

results = []
section = "setup"


def check(name, cond, detail=""):
    results.append((section, bool(cond), name, detail))


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def exists(p):
    return os.path.exists(os.path.join(ROOT, p))


def visible_text(s):
    s = re.sub(r"<script\b.*?</script>|<style\b.*?</style>|<head>.*?</head>", " ", s, flags=re.S)
    s = re.sub(r'<[^>]+lang="en"[^>]*>.*?</[^>]+>', " ", s, flags=re.S)   # explicitly-marked English (banner, EN-only links)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))


def brackets(s):
    return re.findall(r"\[[^\]\n]+\]", s)


# ============================================================== 1. EN public files untouched
section = "EN baseline"
base = read("data/locales/EN_PUBLIC_SHA256_BASELINE.txt").split("\n")
for line in [l for l in base if l.strip()]:
    digest, path = line.split(None, 1)
    path = path.strip()
    got = hashlib.sha256(open(os.path.join(ROOT, path), "rb").read()).hexdigest() if exists(path) else None
    check(f"sha256 unchanged: {path}", got == digest, got)
public_html = ["index.html", "tools.html", "articles.html"] + [os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "tools/*.html")) + glob.glob(os.path.join(ROOT, "articles/*.html"))]
try:
    changed = subprocess.run(["git", "-C", ROOT, "diff", "--name-only", "HEAD", "--"] + public_html + ["site.js", "assets/growth/tools.js", "sitemap.xml", "robots.txt"],
                             capture_output=True, text=True, check=True).stdout.split()
    check("public EN tool/article/hub HTML, site.js, tools.js, sitemap, robots unchanged vs HEAD", not changed, changed)
except Exception as ex:  # noqa
    check("git diff available for public-file check", False, str(ex))

# ============================================================== 2. data: 10 SK/CS entries
section = "SK/CS entries"
data = json.loads(read("data/vc_signals.expanded.json"))
recs = {r["id"]: r for r in data["records"]}
en_src = {r["id"]: r for r in json.loads(read("data/locales/en_first10_source.json"))}
for loc in LOCALES:
    mirror = json.loads(read(f"data/locales/{loc}/vc_signals.first10.json"))
    check(f"{loc}: mirror file has 10 records in priority order", [r["id"] for r in mirror["records"]] == PRIORITY)
    mir = {r["id"]: r for r in mirror["records"]}
    for rid in PRIORITY:
        L, en = recs[rid]["locales"][loc], recs[rid]["locales"]["en"]
        missing = [k for k in REQUIRED if not L.get(k)]
        check(f"{loc}/{rid}: all required fields non-empty", not missing, missing)
        check(f"{loc}/{rid}: status={STATUS}, reviewer=claude-fluent-pass, ISO reviewedAt",
              L.get("status") == STATUS and L.get("editorialReviewer") == "claude-fluent-pass" and re.match(r"^\d{4}-\d{2}-\d{2}$", L.get("reviewedAt", "")))
        check(f"{loc}/{rid}: reviewNote says AI fluent pass + needs native human",
              re.search(r"fluent", L.get("reviewNote", ""), re.I) and re.search(r"native", L.get("reviewNote", ""), re.I) and re.search(r"not reviewed by a native", L.get("reviewNote", ""), re.I))
        check(f"{loc}/{rid}: ≥2 interpretations, same kinds/order as EN, each with clues",
              len(L["interpretations"]) >= 2 and [i["kind"] for i in L["interpretations"]] == [i["kind"] for i in en["interpretations"]]
              and all(i["possibility"].strip() and i["contextualClues"].strip() for i in L["interpretations"]))
        check(f"{loc}/{rid}: list lengths match EN (synonyms/positive/weak)",
              all(len(L[k]) == len(en[k]) and all(x.strip() for x in L[k]) for k in ["synonyms", "positiveSignals", "weakSignals"]))
        check(f"{loc}/{rid}: example hypothetical:true", L["exampleScenario"].get("hypothetical") is True and len(L["exampleScenario"]["description"]) > 80)
        tpl_en, tpl = en["editableReplyTemplate"], L["editableReplyTemplate"]
        lost = [p for p in KEEP if p in tpl_en and p not in tpl]
        check(f"{loc}/{rid}: reply template keeps verbatim placeholders {sorted(p for p in KEEP if p in tpl_en)}", not lost, lost)
        check(f"{loc}/{rid}: reply template has same number of [..] slots as EN", len(brackets(tpl)) == len(brackets(tpl_en)), (len(brackets(tpl)), len(brackets(tpl_en))))
        check(f"{loc}/{rid}: no %/probability claims", not re.search(r"\d\s?%|percent|pravdepodobnosť \d|pravděpodobnost \d", json.dumps(L, ensure_ascii=False)))
        check(f"{loc}/{rid}: text is not English (diacritics present, EN shortAnswer not reused)",
              L["shortAnswer"] != en["shortAnswer"] and sum(L["shortAnswer"].count(c) for c in DIACRITICS[loc]) >= 5)
        check(f"{loc}/{rid}: seedPhrase recorded and matches seed file", L.get("seedPhrase") == next(x for x in json.loads(read("data/vc_signals.seed.json"))["records"] if x["id"] == rid)["phrase"][loc])
        m = mir[rid]
        check(f"{loc}/{rid}: mirror file == merged expanded.json fields", all(m[k] == L[k] for k in REQUIRED if k != "exampleScenario") and m["exampleScenario"]["description"] == L["exampleScenario"]["description"])
        check(f"{loc}/{rid}: publication remains non-public draft", recs[rid]["publication"][loc].startswith("draft") and recs[rid]["publication"]["en"] != "")
    leftovers = [k for k, v in en_src.items() if k in PRIORITY and v["en"]["phrase"] == recs[k]["locales"][loc]["phrase"]]
    check(f"{loc}: no entry still uses the English phrase", not leftovers, leftovers)

# ============================================================== 3. i18n + chrome packs
section = "i18n + chrome"
i18n = {l: json.loads(read(f"data/i18n/{l}.json")) for l in ["en", "sk", "cs", "de", "pl"]}
keys = set(i18n["en"]["strings"])
for l in ["sk", "cs", "de", "pl"]:
    s = i18n[l]["strings"]
    check(f"i18n {l}: same key set as EN ({len(keys)} keys)", set(s) == keys, sorted(set(s) ^ keys)[:10])
    check(f"i18n {l}: no empty values", all(str(v).strip() for v in s.values()))
    same = [k for k in keys if s[k] == i18n["en"]["strings"][k] and not re.fullmatch(r"(Seed|Pre-seed|Pre-Seed|Proces|Signal|Situation|Timing|Traction|FAQ|Tools|Autor|Mini dekoder)", s[k])]
    if l in LOCALES:
        check(f"i18n {l}: values translated (≤5 identical to EN, e.g. brand/stage names)", len(same) <= 5, same)
        check(f"i18n {l}: review_status={STATUS}", i18n[l]["review_status"] == STATUS)
        hub_keys = ["search_label", "filter_stage", "filter_signal", "filter_topic", "filter_context", "filter_reset", "no_results", "privacy_note",
                    "copy", "reply_reset", "decoder_paste_label", "decoder_stage_label", "decoder_category_label", "decoder_next_label",
                    "decoder_elapsed_label", "rules_intro", "rule_R1", "rule_R10", "h_tools", "h_guides", "book_cta", "book_language_note",
                    "class_positive", "class_hard-no", "stage_series-a", "topic_traction", "context_silence", "nav_book", "draft_banner"]
        check(f"i18n {l}: hub UI coverage (nav, filters, search, decoder labels/rules, privacy, empty state, copy/reset, book CTA, classes, stages, topics, situations)",
              all(k in s and s[k] for k in hub_keys))
        check(f"i18n {l}: book note discloses English-only", re.search(r"angličtin", s["book_language_note"]) and re.search(r"iba|pouze", s["book_language_note"]))
    else:
        check(f"i18n {l}: still machine_draft_needs_native_review (lighter DE/PL pass)", i18n[l]["review_status"] == "machine_draft_needs_native_review")
    check(f"i18n {l}: no native-approval claim", not re.search(r"native_approved|human_translat|\"approved\"|published", json.dumps({k: v for k, v in i18n[l].items() if k != "publication_status"})))
en_cs_keys = None
for loc in LOCALES:
    c = json.loads(read(f"data/locales/{loc}/chrome_signup.json"))
    need = ["get_early_access", "join_the_list", "no_spam", "captcha_label", "captcha_refresh", "captcha_loading", "captcha_load_error", "sending",
            "success_title", "success_body", "error_generic", "error_network", "cookie_text", "cookie_accept", "cookie_reject", "cookie_settings",
            "vip_eyebrow", "vip_title", "vip_body", "book_english_only"]
    check(f"chrome_signup {loc}: all signup/captcha/cookie/VIP keys present and translated",
          all(c["strings"].get(k) and c["strings"][k] != c["en_source"].get(k) for k in need), [k for k in need if not c["strings"].get(k) or c["strings"][k] == c["en_source"].get(k)])
    check(f"chrome_signup {loc}: English-only book note", "angličtin" in c["strings"]["book_english_only"])
    check(f"chrome_signup {loc}: status {STATUS}", c["status"] == STATUS)

# ============================================================== 4. tools packs + locale JS
section = "tools packs + parity"
tools_js = read("assets/growth/tools.js")
en_items = dict(re.findall(r"\{key:'(\w+)',label:'([^']+)'", tools_js))
en_tpl_keys = re.findall(r"\n (\w+):\{subject:", tools_js)
for loc in LOCALES:
    p = json.loads(read(f"data/locales/{loc}/tools.json"))
    T = p["tools"]
    check(f"tools.json {loc}: all 4 tools present with meta title/description/h1", set(T) == set(TOOLS) and all(T[t]["meta_title"] and T[t]["meta_description"] and T[t]["h1"] for t in TOOLS))
    si = T["investor-signal-decoder"]["signalItems"]
    check(f"tools.json {loc}: all {len(en_items)} signalItem labels from tools.js present + translated",
          set(si) == set(en_items) and all(si[k] and si[k] != en_items[k] for k in en_items), sorted(set(si) ^ set(en_items)))
    check(f"tools.json {loc}: 5 decoder result buckets × status/desc/next", all(all(T["investor-signal-decoder"]["results"][b][f] for f in ["status", "desc", "next"])
                                                                              for b in ["insufficient", "mismatch", "meaningful", "early", "weak"]))
    fub = T["investor-follow-up-builder"]
    check(f"tools.json {loc}: follow-up templates for all {len(en_tpl_keys)} scenarios (subject/intro/mid/ask) + scenario labels",
          set(fub["templates"]) == set(en_tpl_keys) and set(fub["scenarios"]) == set(en_tpl_keys) and all(all(fub["templates"][k][f] for f in ["subject", "intro", "mid", "ask"]) for k in en_tpl_keys))
    bad = []
    for key in en_tpl_keys:
        en_body = re.search(r"\n " + key + r":\{(.*?)\}", tools_js).group(1)
        loc_body = " ".join(fub["templates"][key].values())
        for ph in ["[Company]", "[topic]", "[progress]", "[milestone]", "[specific next step]", "[customer]", "[outcome]"]:
            if en_body.count(ph) != loc_body.count(ph):
                bad.append((key, ph, en_body.count(ph), loc_body.count(ph)))
    check(f"tools.json {loc}: machine-substituted placeholders preserved per scenario (same counts as EN)", not bad, bad)
    check(f"tools.json {loc}: pipeline + runway labels/metrics/notes complete",
          len(T["fundraising-pipeline-calculator"]["fields"]) == 5 and len(T["fundraising-pipeline-calculator"]["metrics"]) == 4
          and len(T["runway-raise-calculator"]["fields"]) == 7 and len(T["runway-raise-calculator"]["metrics"]) == 4
          and all(T["runway-raise-calculator"][k] for k in ["no_net_burn", "note_no_pre", "note_ok"]))
    check(f"tools.json {loc}: disclaimers, buttons, related-link text present",
          all(p["common"][k] for k in ["disclaimer", "book_cta", "book_p", "related_guide", "related_tools_link", "copied"]) and all(T[t]["calculate"] for t in TOOLS))
    check(f"tools.json {loc}: book CTA discloses English-only", "angličtin" in p["common"]["book_p"])
    check(f"tools.json {loc}: math parity + Intl number formatting documented", "unchanged" in p["mathParity"] and "Intl.NumberFormat" in p["numberFormatting"])
    for a in ["tools.locale.js", "vc-says.locale.js", "site.locale.js"]:
        check(f"{loc}: _staging/locales/{loc}/assets/{a} exists", exists(f"_staging/locales/{loc}/assets/{a}"))
    sj = read(f"_staging/locales/{loc}/assets/site.locale.js") if exists(f"_staging/locales/{loc}/assets/site.locale.js") else ""
    en_sj = read("site.js")
    check(f"{loc}: site.locale.js keeps the same endpoints + consent defaults as site.js",
          all(x in sj for x in re.findall(r"https://[^'\"]+", en_sj)) and "analytics_storage: 'denied'" in sj and "Sending…" not in sj and "Cookie settings" not in sj)

node = shutil.which("node")
if node:
    for loc in LOCALES:
        for a in ["tools.locale.js", "vc-says.locale.js", "site.locale.js"]:
            r = subprocess.run([node, "--check", os.path.join(ROOT, f"_staging/locales/{loc}/assets/{a}")], capture_output=True, text=True)
            check(f"{loc}: {a} parses (node --check)", r.returncode == 0, r.stderr[-300:])
        r = subprocess.run([node, os.path.join(ROOT, "scripts/locale_tools_parity.js"), loc], capture_output=True, text=True)
        try:
            jr = json.loads(r.stdout)
            for name, v in jr["checks"].items():
                check(f"{loc} parity: {name}", v["ok"], v.get("detail"))
            check(f"{loc} parity: ran {jr['counts']['comparisons']} EN-vs-locale comparisons", jr["counts"]["comparisons"] > 1000)
        except Exception as ex:  # noqa
            check(f"{loc}: parity harness ran", False, (str(ex), r.stderr[-500:]))
else:
    check("node available for parity checks", False, "node not found")

# ============================================================== 5. articles (markdown sources)
section = "articles"
for slug in ARTICLES:
    en_html = read(f"content/articles/_source/{slug}.en.html")
    art = en_html[en_html.find("<article"):en_html.find("</article>")]
    en_h2, en_h3 = len(re.findall(r"<h2\b", art)), len(re.findall(r"<h3\b", art))
    en_rows = len(re.findall(r"<tr>", art))
    for loc in LOCALES:
        p = f"content/articles/{loc}/{slug}.md"
        check(f"{loc}/{slug}.md exists", exists(p))
        if not exists(p):
            continue
        src = read(p)
        fm = dict(l.split(":", 1) for l in re.match(r"---\n(.*?)\n---", src, re.S).group(1).splitlines())
        fm = {k.strip(): v.strip() for k, v in fm.items()}
        body = src.split("---", 2)[2]
        check(f"{loc}/{slug}: front matter title/description/h1/status", all(fm.get(k) for k in ["title", "description", "h1", "eyebrow", "readingTime"]) and fm.get("status") == STATUS)
        h2 = len(re.findall(r"^## ", body, re.M)) - 1   # minus added Related section
        h3 = len(re.findall(r"^### ", body, re.M))
        check(f"{loc}/{slug}: section structure matches EN (h2 {en_h2}, h3 {en_h3})", (h2, h3) == (en_h2, en_h3), (h2, h3))
        rows = len([l for l in body.splitlines() if l.startswith("|") and not re.match(r"^\|\s*-", l)])
        check(f"{loc}/{slug}: table rows match EN ({en_rows})", rows == en_rows, rows)
        check(f"{loc}/{slug}: full body length ≥70% of EN text", len(visible_text(body)) >= 0.7 * len(visible_text(art)), (len(visible_text(body)), len(visible_text(art))))
        check(f"{loc}/{slug}: no [Investor]/[Name] EN-only placeholders left", "[Investor]" not in body and "[Name]" not in body)
        check(f"{loc}/{slug}: CTA discloses English-only book", re.search(r"(iba|pouze) v angličtině?|(iba|pouze) v angličtine", body))

# ============================================================== 6. staging pages
section = "staging pages"
EN_PHRASES = ["What they said", "What it might mean", "What to ask", "What to do next", "A reply you can adapt", "Browse the library",
              "Your inputs", "How to use this", "Short answer", "Join the list", "Get early access", "Interpret the signals",
              "Meeting context", "Funnel assumptions", "Cash & burn", "Frequently asked questions", "Useful question", "Related guides",
              "Expected outcomes", "Illustrative results", "No account required", "Educational content"]
for loc in LOCALES:
    pages = ([f"_staging/locales/{loc}/vc-says/index.html"] + [f"_staging/locales/{loc}/vc-says/{recs[r]['slug']}.html" for r in PRIORITY]
             + [f"_staging/locales/{loc}/tools/index.html"] + [f"_staging/locales/{loc}/tools/{t}.html" for t in TOOLS]
             + [f"_staging/locales/{loc}/articles/{a}.html" for a in ARTICLES])
    missing = [p for p in pages if not exists(p)]
    check(f"{loc}: hub + 10 entries + tools hub + 4 tools + 3 articles exist ({len(pages)} pages)", not missing, missing)
    stats = []
    for p in [x for x in pages if exists(x)]:
        s = read(p)
        name = p.split(f"/{loc}/", 1)[1]
        check(f"{loc}/{name}: noindex,nofollow + lang={loc} + no canonical/hreflang",
              '<meta name="robots" content="noindex,nofollow">' in s and f'<html lang="{loc}">' in s and "hreflang" not in s and 'rel="canonical"' not in s)
        check(f"{loc}/{name}: draft banner (AI fluent draft, needs native human approval)", "DRAFT — AI fluent draft, needs native human approval. noindex." in s)
        txt = visible_text(s)
        found_en = [x for x in EN_PHRASES if x in txt]
        words = re.findall(r"[a-záäčďéěíĺľňóôŕřšťúůýž]+", re.sub(r"\[[^\]]*\]", " ", txt.lower()))
        en_ratio = sum(w in EN_STOP for w in words) / max(1, len(words))
        dia = sum(txt.count(c) for c in DIACRITICS[loc])
        stats.append((name, round(en_ratio, 3), dia))
        check(f"{loc}/{name}: body not predominantly English (no EN UI phrases; EN stop-word ratio {en_ratio:.1%} < 3%; {dia} diacritics)",
              not found_en and en_ratio < 0.03 and dia >= 40 and any(m in txt for m in LANG_MARKERS[loc]), (found_en, en_ratio, dia))
        check(f"{loc}/{name}: English-only book disclosure visible", re.search(r"(iba|pouze) v angličtin", txt))
        links = set(re.findall(r'href="(/[^"#?]*)', re.sub(r"<script\b.*?</script>", "", s, flags=re.S)))
        broken = [l for l in links if l != "/" and not (exists(l.lstrip("/") + ".html") or exists(l.lstrip("/") + "/index.html") or exists(l.lstrip("/")))]
        check(f"{loc}/{name}: internal links resolve", not broken, broken)
        srcs = re.findall(r'<script[^>]+src="([^"]+)"', s)
        check(f"{loc}/{name}: loads only staging locale scripts (not public site.js)", srcs and all(x.startswith(f"/_staging/locales/{loc}/assets/") for x in srcs), srcs)
    for p in [f"_staging/locales/{loc}/vc-says/{recs[r]['slug']}.html" for r in PRIORITY if exists(f"_staging/locales/{loc}/vc-says/{recs[r]['slug']}.html")]:
        rid = re.search(r'data-vc-signal="([^"]+)"', read(p)).group(1)
        m = re.search(r'<textarea id="vc-reply"[^>]*>(.*?)</textarea>', read(p), re.S)
        tpl = html.unescape(m.group(1)) if m else ""
        check(f"{loc}/{rid}: rendered reply == translated template (placeholders intact)", tpl == recs[rid]["locales"][loc]["editableReplyTemplate"])
    hub = read(f"_staging/locales/{loc}/vc-says/index.html")
    check(f"{loc}: hub lists all 10 localized phrases + filters + decoder controls",
          all(html.escape(recs[r]["locales"][loc]["phrase"], quote=True) in hub for r in PRIORITY)
          and all(f'id="{i}"' in hub for i in ["vc-q", "vc-f-stage", "vc-f-class", "vc-f-topic", "vc-f-context", "vc-reset", "vc-dec-run", "vc-dec-paste"]))
    tool_pages = "".join(read(f"_staging/locales/{loc}/tools/{t}.html") for t in TOOLS)
    check(f"{loc}: tool pages keep EN element IDs/input attributes (min/max/step/value)",
          all(re.search(r'<input id="' + i + '"[^>]*>', read(f"tools/{t}.html")).group(0).split("placeholder")[0] in tool_pages
              for t in TOOLS for i in re.findall(r'<input id="([^"]+)"', read(f"tools/{t}.html"))))
    print(f"  [{loc}] EN-stopword ratio / diacritics per page: " + ", ".join(f"{n}={r}/{d}" for n, r, d in stats[:4]) + " …")

# ============================================================== 7. no public exposure
section = "no public exposure"
sm = read("sitemap.xml")
locs = re.findall(r"<loc>([^<]+)</loc>", sm)
check("sitemap: no /sk/, /cs/, /de/, /pl/ or /_staging/ URLs", not any(re.search(r"/(sk|cs|de|pl)(/|$)|_staging", l) for l in locs))
check("robots.txt disallows /_staging/", "Disallow: /_staging/" in read("robots.txt"))
vj = json.loads(read("vercel.json"))
check("vercel.json sends X-Robots-Tag noindex for /_staging/", any(h["source"].startswith("/_staging/") and any("noindex" in x["value"] for x in h["headers"]) for h in vj.get("headers", [])))
check("no public /sk or /cs route directories", not any(os.path.isdir(os.path.join(ROOT, l)) for l in ["sk", "cs", "de", "pl"]))
pub_hreflang = [p for p in public_html + ["vc-says.html"] if "hreflang" in read(p)]
check("no hreflang on any public page", not pub_hreflang, pub_hreflang)
check("no SK/CS status claims approval/publication", all(recs[r]["locales"][l]["status"] == STATUS for r in PRIORITY for l in LOCALES)
      and not re.search(r'"(sk|cs)": "(published|approved[^"]*)"', read("data/vc_signals.expanded.json")))

# ============================================================== 8. docs
section = "docs"
for d in ["REVIEW_SK.md", "REVIEW_CS.md", "REVIEWER_CHECKLIST.md", "COVERAGE_MATRIX.md"]:
    check(f"docs/vc-says/{d} exists", exists(f"docs/vc-says/{d}"))
for d, loc in [("REVIEW_SK.md", "sk"), ("REVIEW_CS.md", "cs")]:
    if exists(f"docs/vc-says/{d}"):
        t = read(f"docs/vc-says/{d}")
        check(f"{d}: covers what was reviewed / issues fixed / remaining risks / checklist",
              all(re.search(x, t, re.I) for x in [r"what was reviewed", r"issues found", r"remaining risks", r"checklist"]))
        check(f"{d}: does not claim native sign-off", re.search(r"not (been )?reviewed by a native|no native", t, re.I))
cm = read("docs/vc-says/COVERAGE_MATRIX.md") if exists("docs/vc-says/COVERAGE_MATRIX.md") else ""
check("COVERAGE_MATRIX.md reflects SK/CS fluent-reviewed status", STATUS in cm)

# ============================================================== report
by = {}
for sec, ok, name, detail in results:
    by.setdefault(sec, [0, 0])[0 if ok else 1] += 1
fails = [r for r in results if not r[1]]
for sec, ok, name, detail in fails:
    print(f"FAIL  [{sec}] {name}  {detail}")
print("\nSection results (pass / fail):")
for sec, (p, f) in by.items():
    print(f"  {sec:<22} {p:>4} pass  {f:>3} fail")
print(f"\n{len(results) - len(fails)}/{len(results)} checks passed, {len(fails)} failed")
sys.exit(1 if fails else 0)
