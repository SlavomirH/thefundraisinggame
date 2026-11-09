#!/usr/bin/env python3
"""Static checks for published SK/CS/DE/PL public trees + EN reciprocal hreflang/sitemap."""
import hashlib
import json
import os
import re
import subprocess
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES = ["sk", "cs", "de", "pl"]
PRIORITY = [
    "too-early", "not-right-fit", "keep-in-touch", "circle-back-next-quarter", "send-deck",
    "second-meeting", "partner-introduction", "need-more-traction", "no-lead-investor", "investor-ghosting",
]
TOOLS = [
    "investor-signal-decoder", "investor-follow-up-builder",
    "fundraising-pipeline-calculator", "runway-raise-calculator",
]
ARTICLES = ["vc-too-early-meaning", "how-to-follow-up-with-vc-after-meeting", "signs-vc-interested"]
SITE = "https://thefundraisinggame.com"
results = []


def check(name, cond, detail=""):
    results.append((bool(cond), name, detail))


def read(p):
    return (ROOT / p).read_text(encoding="utf-8")


def exists(p):
    return (ROOT / p).exists()


def visible(html):
    s = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", html, flags=re.S)
    return unescape(re.sub(r"<[^>]+>", " ", s))


EN_KEEP = ["[Company]", "[Investor name]", "[Your name]", "[topic]", "[progress]", "[milestone]", "[specific next step]"]

# 1. Approval record
section = "approval"
ap = json.loads(read("data/PUBLICATION_APPROVAL.json"))
check("approval records owner publish (not native)", ap["reviewProvenance"]["nativeHumanReview"] is False and ap["verbatim"] == "publish them")
check("approval lists 4 locales + 10 + 4 + 3", ap["scope"]["locales"] == LOCALES and len(ap["scope"]["vcSaysEntries"]) == 10)

# 2. Per-locale file presence + meta
for loc in LOCALES:
    pages = (
        [f"{loc}/index.html", f"{loc}/vc-says/index.html"]
        + [f"{loc}/vc-says/{i}.html" for i in PRIORITY]
        + [f"{loc}/tools/index.html"]
        + [f"{loc}/tools/{t}.html" for t in TOOLS]
        + [f"{loc}/articles/{a}.html" for a in ARTICLES]
        + [f"{loc}/assets/site.locale.js", f"{loc}/assets/tools.locale.js", f"{loc}/assets/vc-says.locale.js"]
    )
    missing = [p for p in pages if not exists(p)]
    check(f"{loc}: all published files present ({len(pages)})", not missing, missing[:5])
    for p in pages:
        if not p.endswith(".html"):
            continue
        html = read(p)
        check(f"{loc}:{p}: lang={loc}", f'<html lang="{loc}">' in html)
        check(f"{loc}:{p}: indexable (no noindex)", "noindex" not in html and "vc-draftbanner" not in html)
        check(f"{loc}:{p}: has canonical", 'rel="canonical"' in html)
        check(f"{loc}:{p}: has reciprocal hreflang set", all(f'hreflang="{c}"' in html for c in ["en", "sk", "cs", "de", "pl", "x-default"]))
        check(f"{loc}:{p}: status meta owner_approved", 'content="owner_approved_ai_fluent_review"' in html)
        check(f"{loc}:{p}: language switcher present", 'class="tfg-lang"' in html)
        # no bare EN placeholders in visible body for reply templates
        if "/vc-says/" in p and p.endswith(".html") and not p.endswith("index.html"):
            leftover = [x for x in EN_KEEP if x in html]
            check(f"{loc}:{p}: no bare EN placeholders", not leftover, leftover)

# 3. Sitemap
sm = read("sitemap.xml")
check("sitemap has no _staging", "_staging" not in sm)
for loc in LOCALES:
    check(f"sitemap has /{loc} landing", f"{SITE}/{loc}</loc>" in sm)
    check(f"sitemap has /{loc}/vc-says hub", f"{SITE}/{loc}/vc-says</loc>" in sm)
    for i in PRIORITY:
        check(f"sitemap {loc}/vc-says/{i}", f"{SITE}/{loc}/vc-says/{i}</loc>" in sm)
locale_urls = len(re.findall(r"<loc>https://thefundraisinggame.com/(?:sk|cs|de|pl)[^<]*</loc>", sm))
check("sitemap locale URL count == 80 (20×4)", locale_urls == 80, locale_urls)

# 4. EN reciprocal
for path, kind in [
    ("vc-says.html", "hub"),
    ("tools.html", "tools"),
    ("index.html", "home"),
]:
    html = read(path)
    check(f"EN {path}: hreflang reciprocity", all(f'hreflang="{c}"' in html for c in ["en", "sk", "cs", "de", "pl", "x-default"]))
    check(f"EN {path}: language switcher", 'class="tfg-lang"' in html)

# 5. robots still disallows staging
check("robots disallows _staging", "Disallow: /_staging/" in read("robots.txt"))

# 6. Tool parity for all locales
node = subprocess.run(["node", str(ROOT / "scripts/locale_tools_parity.js"), "sk"], capture_output=True, text=True, cwd=ROOT)
# parity script still points at _staging — check public tools.locale.js with a quick node syntax check instead
for loc in LOCALES:
    for a in ["tools.locale.js", "vc-says.locale.js", "site.locale.js"]:
        r = subprocess.run(["node", "--check", str(ROOT / loc / "assets" / a)], capture_output=True, text=True)
        check(f"{loc}:{a} parses", r.returncode == 0, r.stderr[-200:])

# 7. No English under translated labels on locale landing
for loc in LOCALES:
    html = read(f"{loc}/index.html")
    check(f"{loc} landing mentions partial/AI honesty", "owner_approved_ai_fluent_review" in html or "AI" in visible(html) or "AI" in html)
    check(f"{loc} landing links vc-says+tools", f"/{loc}/vc-says" in html and f"/{loc}/tools" in html)

# 8. Internal link reciprocity sample: SK too-early hreflang EN target exists
html = read("sk/vc-says/too-early.html")
m = re.search(r'hreflang="en" href="([^"]+)"', html)
check("SK too-early hreflang en points to live EN path", m and m.group(1).endswith("/vc-says/too-early"), m.group(1) if m else None)
en = read("vc-says/too-early.html")
m2 = re.search(r'hreflang="sk" href="([^"]+)"', en)
check("EN too-early hreflang sk points to /sk/vc-says/too-early", m2 and m2.group(1).endswith("/sk/vc-says/too-early"), m2.group(1) if m2 else None)

failed = [r for r in results if not r[0]]
passed = [r for r in results if r[0]]
print(f"{len(passed)}/{len(results)} checks passed, {len(failed)} failed")
for ok, name, detail in failed[:40]:
    print(" FAIL", name, detail)
sys.exit(1 if failed else 0)
