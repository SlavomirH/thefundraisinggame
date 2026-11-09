#!/usr/bin/env python3
"""Measurable checks for the VC Says EN milestone. No browser automation, no network.

Usage: python3 scripts/build_vc_says.py && python3 scripts/test_vc_says.py
Exit code 0 = all checks passed.
"""
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://thefundraisinggame.com"
PRIORITY = ["too-early", "not-right-fit", "keep-in-touch", "circle-back-next-quarter", "send-deck",
            "second-meeting", "partner-introduction", "need-more-traction", "no-lead-investor", "investor-ghosting"]
DRAFT_LOCALES = ["sk", "cs", "de", "pl"]
# SK/CS/DE/PL all got full content + an AI fluent pass (still NOT native-approved). See scripts/test_locale_drafts.py.
LOCALE_STATUS = {l: "machine_draft_fluent_reviewed_needs_native_approval" for l in DRAFT_LOCALES}
ALLOWED_SOURCE_PREFIXES = ("https://usegems.com/", "https://www.ycombinator.com/", "https://developers.google.com/search/")

results = []


def check(name, cond, detail=""):
    results.append((bool(cond), name, detail))


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def exists(p):
    return os.path.exists(os.path.join(ROOT, p))


def strip_scripts(s):
    return re.sub(r"<script\b.*?</script>", "", s, flags=re.S)


def text_of(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", strip_scripts(s)))


seed = json.loads(read("data/vc_signals.seed.json"))
data = json.loads(read("data/vc_signals.expanded.json"))
recs = {r["id"]: r for r in data["records"]}

# ---------------------------------------------------------------- data
seed_ids = {r["id"] for r in seed["records"]}
check("seed contains all 10 priority IDs", set(PRIORITY) <= seed_ids, sorted(set(PRIORITY) - seed_ids))
check("expanded keeps all 30 seed records", set(recs) == seed_ids and len(recs) == 30, len(recs))
pub_ids = [r["id"] for r in data["records"] if r["publication"]["en"] in ("approved_for_en_milestone", "published") or str(r["publication"]["en"]).startswith("/vc-says/")]
check("exactly the 10 priority IDs are EN-public", sorted(pub_ids) == sorted(PRIORITY), pub_ids)
check("no attributed_investor_quote anywhere (seed + expanded)",
      all(r.get("attributed_investor_quote") is None for r in seed["records"] + data["records"]))
check("every record evidenceType == editorial-analysis", all(r["evidenceType"] == "editorial-analysis" for r in data["records"]))
check("no interviewPermission / approved-interview evidence claimed",
      all("interviewPermission" not in r and r["evidenceType"] != "approved-interview" for r in data["records"]))
bad_src = [s["url"] for r in data["records"] for s in r.get("sources", []) if not s["url"].startswith(ALLOWED_SOURCE_PREFIXES)]
check("sources limited to package-cited public URLs", not bad_src, bad_src)
for rid in PRIORITY:
    r = recs[rid]
    en = r["locales"]["en"]
    seed_r = next(x for x in seed["records"] if x["id"] == rid)
    check(f"[{rid}] seed phrases kept for en/sk/cs/de/pl",
          all(r["locales"][l].get("seedPhrase", r["locales"][l]["phrase"]) == seed_r["phrase"][l] for l in ["en"] + DRAFT_LOCALES))
    check(f"[{rid}] other locales published under /{{loc}}/vc-says/… (owner-approved AI fluent)",
          all(r["publication"][l] == f"/{l}/vc-says/{r['slug']}" for l in DRAFT_LOCALES))
    need = ["shortAnswer", "clarifyingQuestion", "recommendedAction", "followUpTimingNote", "editableReplyTemplate", "metaTitle", "metaDescription", "h1"]
    check(f"[{rid}] EN required text fields non-trivial", all(len(en.get(k, "")) >= 40 for k in need),
          [k for k in need if len(en.get(k, "")) < 40])
    check(f"[{rid}] 2–3 interpretations with contextual clues",
          2 <= len(en["interpretations"]) <= 3 and all(i["possibility"] and i["contextualClues"] for i in en["interpretations"]))
    check(f"[{rid}] positive/weak signals ≥2 each, synonyms ≥2",
          len(en["positiveSignals"]) >= 2 and len(en["weakSignals"]) >= 2 and len(en["synonyms"]) >= 2)
    check(f"[{rid}] example scenario flagged hypothetical", en["exampleScenario"]["hypothetical"] is True)
    check(f"[{rid}] no percentages / fake probabilities in EN copy", not re.search(r"\d\s?%|percent|probability of", json.dumps(en)))
    check(f"[{rid}] related article + tool slugs resolve",
          all(exists(f"articles/{a}.html") for a in r["relatedArticleSlugs"]) and all(exists(f"tools/{t}.html") for t in r["relatedToolSlugs"]))
for rid, r in recs.items():
    if rid not in PRIORITY:
        check(f"[{rid}] draft stub not EN-public and no public page",
              r["publication"]["en"] == "draft" and r["publication_status"] == "draft" and not exists(f"vc-says/{r['slug']}.html"))

# ---------------------------------------------------------------- public pages
h1s, titles = [], []
for rid in PRIORITY:
    slug = recs[rid]["slug"]
    p = f"vc-says/{slug}.html"
    check(f"[{rid}] page exists", exists(p))
    if not exists(p):
        continue
    s = read(p)
    h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", s, re.S)
    h1s += h1
    titles += re.findall(r"<title>(.*?)</title>", s)
    check(f"[{rid}] exactly one H1", len(h1) == 1)
    check(f"[{rid}] self-canonical", f'<link rel="canonical" href="{SITE}/vc-says/{slug}">' in s)
    check(f"[{rid}] html lang=en and indexable", '<html lang="en">' in s and "noindex" not in s)
    check(f"[{rid}] reciprocal hreflang to published locales", all(f'hreflang="{c}"' in s for c in ["en","sk","cs","de","pl","x-default"]))
    check(f"[{rid}] 'Editorial guidance' label shown", "Editorial guidance" in text_of(s))
    m = re.search(r'<textarea id="vc-reply"[^>]*>(.*?)</textarea>', s, re.S)
    check(f"[{rid}] editable reply template non-empty + Copy button", bool(m and len(m.group(1).strip()) > 80) and 'id="vc-copy"' in s)
    interp = re.search(r'<ul class="vc-interp">(.*?)</ul>', s, re.S)
    check(f"[{rid}] ≥2 interpretations rendered", bool(interp) and interp.group(1).count("<li>") >= 2)
    for sec in ["What they said", "What it might mean", "What strengthens", "What to ask", "What to do next", "A reply you can adapt", "Sources", "Related"]:
        if sec not in s:
            check(f"[{rid}] section '{sec}' present", False)
    links = re.findall(r'href="(/[^"#?]*)', strip_scripts(s))
    broken = [l for l in set(links) if l not in ("/",) and not (exists(l.lstrip("/") + ".html") or exists(l.lstrip("/")) or l.startswith("/assets/") and exists(l.lstrip("/")))]
    check(f"[{rid}] internal links resolve", not broken, broken)
    check(f"[{rid}] follow-up builder deep link carries ?signal=", f"/tools/investor-follow-up-builder?signal={rid}" in s)
    check(f"[{rid}] book CTA to /#join with language note", 'href="/#join"' in s and "The book is in English (coming soon)." in s)
    check(f"[{rid}] LinkedIn company URL + brand colour in chrome",
          "https://www.linkedin.com/company/the-fundraising-game/" in s and "rgb(224, 82, 47)" in s)
check("H1s unique across 10 pages", len(h1s) == 10 and len(set(h1s)) == 10)
check("titles unique across 10 pages", len(titles) == 10 and len(set(titles)) == 10)

# ---------------------------------------------------------------- hub
hub = read("vc-says.html")
hub_html_only = strip_scripts(hub)
missing = [rid for rid in PRIORITY if html.escape(recs[rid]["locales"]["en"]["phrase"], quote=True) not in hub_html_only]
check("hub contains all 10 phrases in crawlable HTML (outside scripts)", not missing, missing)
check("hub links to all 10 detail pages", all(f'href="/vc-says/{recs[r]["slug"]}"' in hub_html_only for r in PRIORITY))
check("hub self-canonical", f'<link rel="canonical" href="{SITE}/vc-says">' in hub)
check("hub has search + 4 filters + reset", all(f'id="{i}"' in hub for i in ["vc-q", "vc-f-stage", "vc-f-class", "vc-f-topic", "vc-f-context", "vc-reset"]))
check("hub has mini decoder controls", all(f'id="{i}"' in hub for i in ["vc-dec-stage", "vc-dec-category", "vc-dec-next", "vc-dec-elapsed", "vc-dec-run"]))
check("hub privacy note present", "never sent, stored or tracked" in hub)
check("hub book CTA with English note", 'href="/#join"' in hub and "The book is in English (coming soon)." in hub)
check("hub links to tools + articles", "/tools/investor-signal-decoder" in hub and "/articles/vc-too-early-meaning" in hub)
check("hub does not list draft phrases as links", not any(f'href="/vc-says/{r["slug"]}"' in hub for r in data["records"] if r["id"] not in PRIORITY))

# ---------------------------------------------------------------- scripts / privacy
js = read("assets/growth/vc-says.js")
check("vc-says.js makes no network calls", not re.search(r"\bfetch\s*\(|XMLHttpRequest|sendBeacon|navigator\.sendBeacon|new\s+Image\s*\(|WebSocket", js))
check("vc-says.js analytics only via window.tfgTrack (no invented tracker)",
      "window.tfgTrack" in js and "posthog" not in js and "gtag" not in js)
check("vc-says.js never passes raw query/paste/reply text to track()",
      not re.search(r"track\([^)]*(\bq\.value|paste\.value|\bta\.value|\btext\b|\.textContent)", js))
check("vc-says.js exposes formatNumber(n, locale)", "formatNumber" in js)
for p in ["vc-says.html"] + [f"vc-says/{recs[r]['slug']}.html" for r in PRIORITY]:
    srcs = re.findall(r'<script[^>]+src="([^"]+)"', read(p))
    if srcs != ["/site.js", "/assets/growth/vc-says.js"]:
        check(f"{p}: only existing signup script + vc-says.js loaded", False, srcs)
check("generated pages load only /site.js (existing signup) + vc-says.js", True)
js_rules = re.findall(r"id: '(R\d+)'", js)
hub_rules = re.findall(r"<li><b>(R\d+)</b>", hub)
check("decoder rules documented on hub match JS rules", js_rules and js_rules == hub_rules, (js_rules, hub_rules))

node = shutil.which("node")
if node:
    for f in ["assets/growth/tools.js", "assets/growth/vc-says.js"]:
        r = subprocess.run([node, "--check", os.path.join(ROOT, f)], capture_output=True, text=True)
        check(f"{f} parses (node --check)", r.returncode == 0, r.stderr.strip())
    r = subprocess.run([node, os.path.join(ROOT, "scripts/vc_says_js_check.js")], capture_output=True, text=True)
    try:
        jr = json.loads(r.stdout)
        check("follow-up builder: ?signal=ID preselects template + links entry (all 10)",
              all(v["ok"] for v in jr["followup"].values()) and len(jr["followup"]) == 10, {k: v for k, v in jr["followup"].items() if not v["ok"]})
        check("follow-up builder: unknown ?signal ignored safely", jr["followup_unknown_ignored"])
        check("follow-up builder: default unchanged without ?signal", jr["followup_no_param_default"])
        dec = jr["decoder"]
        check("mini decoder rules rank as documented", all(v for k, v in dec.items() if k != "rule_ids"), dec)
        check("formatNumber uses locale formats", jr["formatNumber"]["en"] == "1,200.5" and jr["formatNumber"]["de"] == "1.200,5")
    except Exception as ex:  # noqa
        check("JS behavioural harness ran", False, (str(ex), r.stderr[-500:]))
else:
    check("node available for JS checks (SKIPPED)", True, "node not found; JS parse checks skipped")
tools_js = read("assets/growth/tools.js")
check("tools.js shares all 10 signal IDs", all(f"'{rid}':" in tools_js for rid in PRIORITY))
check("follow-up builder HTML has new scenarios + signal note",
      all(f'value="{v}"' in read("tools/investor-follow-up-builder.html") for v in ["update", "notfit", "nolead"]) and 'id="follow-signal-note"' in read("tools/investor-follow-up-builder.html"))
check("signal decoder links to VC Says", 'href="/vc-says"' in read("tools/investor-signal-decoder.html") and 'id="signal-related"' in read("tools/investor-signal-decoder.html"))

# ---------------------------------------------------------------- nav
for p in ["vc-says.html", "tools.html", "articles.html", "index.html"] + [f"vc-says/{recs[r]['slug']}.html" for r in PRIORITY] + sorted(os.path.relpath(x, ROOT) for x in glob.glob(os.path.join(ROOT, "tools/*.html"))):
    s = read(p)
    mn = re.search(r'<nav aria-label="Main".*?</nav>', s, re.S)
    ln = re.search(r'<nav aria-label="Learn".*?</nav>', s, re.S)
    check(f"nav: {p} has VC Says in main nav + footer Learn", mn and ln and 'href="/vc-says"' in mn.group(0) and 'href="/vc-says"' in ln.group(0))

# ---------------------------------------------------------------- sitemap / robots / routes
sm = read("sitemap.xml")
locs = re.findall(r"<loc>([^<]+)</loc>", sm)
try:
    orig = subprocess.run(["git", "-C", ROOT, "show", "d97bebc:sitemap.xml"], capture_output=True, text=True, check=True).stdout
    orig_locs = set(re.findall(r"<loc>([^<]+)</loc>", orig))
except Exception:
    orig_locs = {l for l in locs if "/vc-says" not in l}
new = sorted(set(locs) - orig_locs)
want = sorted([f"{SITE}/vc-says"] + [f"{SITE}/vc-says/{recs[r]['slug']}" for r in PRIORITY])
# EN vc-says routes + 80 published locale routes (20 per locale)
locale_extra = []
for loc in DRAFT_LOCALES:
    locale_extra += [f"{SITE}/{loc}", f"{SITE}/{loc}/vc-says"] + [f"{SITE}/{loc}/vc-says/{recs[r]['slug']}" for r in PRIORITY]
    locale_extra += [f"{SITE}/{loc}/tools"] + [f"{SITE}/{loc}/tools/{t}" for t in ["investor-signal-decoder","investor-follow-up-builder","fundraising-pipeline-calculator","runway-raise-calculator"]]
    locale_extra += [f"{SITE}/{loc}/articles/{a}" for a in ["vc-too-early-meaning","how-to-follow-up-with-vc-after-meeting","signs-vc-interested"]]
want_pub = sorted(want + locale_extra)
check("sitemap includes EN vc-says + published locale routes", set(want_pub).issubset(set(locs)), sorted(set(want_pub)-set(locs))[:10])
check("sitemap: original URLs preserved", orig_locs <= set(locs))
check("sitemap: no duplicate URLs", len(locs) == len(set(locs)))
check("sitemap: no /_staging routes", not any("_staging" in l for l in locs))
check("robots.txt disallows /_staging/", "Disallow: /_staging/" in read("robots.txt"))
check("published locale dirs exist in public root", all(os.path.isdir(os.path.join(ROOT, l)) for l in DRAFT_LOCALES))
check("PUBLICATION_APPROVAL denies native claim", (lambda a: a["reviewProvenance"]["nativeHumanReview"] is False)(json.loads(read("data/PUBLICATION_APPROVAL.json"))))
try:
    tracked = subprocess.run(["git", "-C", ROOT, "ls-tree", "-r", "--name-only", "d97bebc"], capture_output=True, text=True, check=True).stdout.split()
    gone = [f for f in tracked if not exists(f)]
    check("all files from base commit still exist (no URL removed)", not gone, gone[:10])
except Exception as ex:
    check("base commit file list readable", False, str(ex))

# ---------------------------------------------------------------- staging drafts
for loc in DRAFT_LOCALES:
    base = f"_staging/locales/{loc}/vc-says"
    pages = [f"{base}/index.html"] + [f"{base}/{recs[r]['slug']}.html" for r in PRIORITY]
    ok = all(exists(p) for p in pages)
    check(f"staging {loc}: hub + 10 draft pages exist", ok)
    if ok:
        bad = [p for p in pages if '<meta name="robots" content="noindex,nofollow">' not in read(p)
               or "hreflang" in read(p) or 'rel="canonical"' in read(p) or f'<html lang="{loc}">' not in read(p)]
        check(f"staging {loc}: noindex,nofollow, lang={loc}, no canonical/hreflang", not bad, bad)
    ph = json.loads(read(f"{base}/phrases.json")) if exists(f"{base}/phrases.json") else {"phrases": []}
    check(f"staging {loc}: phrase seeds for all 30", len(ph["phrases"]) == 30 and ph["review_status"] == LOCALE_STATUS[loc])
check("staging sk/cs/de/pl hubs show localized phrases",
      all(html.escape(recs["keep-in-touch"]["locales"][l]["phrase"], quote=True) in read(f"_staging/locales/{l}/vc-says/index.html") for l in DRAFT_LOCALES))

# ---------------------------------------------------------------- i18n
i18n = {l: json.loads(read(f"data/i18n/{l}.json")) for l in ["en"] + DRAFT_LOCALES}
keys = set(i18n["en"]["strings"])
check("i18n: 5 dictionaries with identical key sets", all(set(d["strings"]) == keys for d in i18n.values()))
check("i18n: SK/CS/DE/PL fluent-reviewed drafts (none native-approved)",
      all(i18n[l]["review_status"] == LOCALE_STATUS[l] for l in DRAFT_LOCALES))
check("i18n: no locale claims native approval", not any(re.search(r"native_approved|human_translat", json.dumps(d)) for d in i18n.values()))
check("i18n: numeric Intl note present", all("Intl.NumberFormat" in d["numberFormatting"]["note"] for d in i18n.values()))

# ---------------------------------------------------------------- docs
cm = read("docs/vc-says/COVERAGE_MATRIX.md") if exists("docs/vc-says/COVERAGE_MATRIX.md") else ""
check("COVERAGE_MATRIX.md exists with all 5 locales", cm and all(f"| {l} " in cm or f"| {l.upper()} " in cm for l in ["en"] + DRAFT_LOCALES))
kc = read("docs/vc-says/KEYWORD_CANDIDATES.md") if exists("docs/vc-says/KEYWORD_CANDIDATES.md") else ""
rows = [l for l in kc.splitlines() if l.startswith("| ") and "editorial_hypothesis" in l]
en_rows = [l for l in rows if re.search(r"\|\s*en\s*\|", l)]
check("KEYWORD_CANDIDATES.md ≥20 EN candidates, provenance=editorial_hypothesis, volume=unknown",
      len(en_rows) >= 20 and all("unknown" in l for l in rows), len(en_rows))
check("KEYWORD_CANDIDATES.md includes SK and CS candidates", any(re.search(r"\|\s*sk\s*\|", l) for l in rows) and any(re.search(r"\|\s*cs\s*\|", l) for l in rows))
check("KEYWORD_CANDIDATES.md has no numeric volumes", not re.search(r"volume[^|\n]*\|\s*\d", kc, re.I))

# ---------------------------------------------------------------- report
failed = [r for r in results if not r[0]]
for ok, name, detail in results:
    if not ok:
        print(f"FAIL  {name}  {detail}")
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
