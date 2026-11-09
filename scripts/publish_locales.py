#!/usr/bin/env python3
"""Promote complete SK/CS/DE/PL Release A content to public /{loc}/ routes.

Owner publication approval (2026-11-09, Cursor message pt15u "publish them") overrides the
native-review gate for these machine-fluent drafts. Does NOT invent native human signoff.

Scope: 10 VC Says entries + hub, 4 tools + hub, 3 articles, locale landing, chrome/forms.
Does NOT expand the remaining 20 seed entries. English URLs unchanged except reciprocal hreflang.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_locale_staging as S  # noqa: E402
import build_vc_says as B  # noqa: E402

LOCALES = ["sk", "cs", "de", "pl"]
SITE = "https://thefundraisinggame.com"
PRIORITY = [
    "too-early", "not-right-fit", "keep-in-touch", "circle-back-next-quarter", "send-deck",
    "second-meeting", "partner-introduction", "need-more-traction", "no-lead-investor", "investor-ghosting",
]
TOOLS = list(B.TOOLS)
ARTICLES = S.ARTICLES
TODAY = "2026-11-09"


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path.relative_to(ROOT))


def abs_url(path: str) -> str:
    if path == "/":
        return SITE + "/"
    return SITE + path.rstrip("/")


def hreflang_block(kind: str, slug: str | None = None) -> str:
    lines = []
    for code in ["en", "sk", "cs", "de", "pl"]:
        loc = None if code == "en" else code
        lines.append(
            f'<link rel="alternate" hreflang="{code}" href="{abs_url(S.page_kind_path(loc, kind, slug))}">'
        )
    lines.append(
        f'<link rel="alternate" hreflang="x-default" href="{abs_url(S.page_kind_path(None, kind, slug))}">'
    )
    return "\n".join(lines)


def inject_hreflang_en(path: str, kind: str, slug: str | None = None):
    fp = ROOT / path
    html = fp.read_text(encoding="utf-8")
    # Remove prior alternate/hreflang we may have injected
    html = re.sub(r'\n?<link rel="alternate" hreflang="[^"]+" href="[^"]+">', "", html)
    html = re.sub(
        r'<div style="max-width:1240px;margin:0 auto;padding:0 24px 12px"><nav aria-label="[^"]*" class="tfg-lang".*?</nav></div>',
        "",
        html,
        flags=re.S,
    )
    html = re.sub(r'<nav aria-label="[^"]*" class="tfg-lang".*?</nav>', "", html, flags=re.S)
    block = hreflang_block(kind, slug)
    if "</head>" not in html:
        raise SystemExit(f"no </head> in {path}")
    html = html.replace("</head>", block + "\n</head>", 1)
    # Language switcher for EN equivalents
    if "</header>" in html:
        switch = (
            '<div style="max-width:1240px;margin:0 auto;padding:0 24px 12px">'
            '<nav aria-label="Language" class="tfg-lang" style="display:inline-flex;flex-wrap:wrap;gap:8px 14px;align-items:center;font-size:13px">'
            '<span style="color:rgb(140,131,120)">Language:</span>'
            '<span aria-current="true" style="font-weight:600;color:rgb(245,154,106)">English</span>'
        )
        for code, label in [("sk", "Slovenčina"), ("cs", "Čeština"), ("de", "Deutsch"), ("pl", "Polski")]:
            href = S.page_kind_path(code, kind, slug)
            switch += (
                f'<a href="{href}" style="color:rgb(207,197,186);text-decoration:none;min-height:44px;'
                f'display:inline-flex;align-items:center" hreflang="{code}" lang="{code}">{label}</a>'
            )
        switch += "</nav></div>"
        html = html.replace("</header>", switch + "</header>", 1)
    fp.write_text(html, encoding="utf-8")
    return path


def update_sitemap():
    urls = [
        ("/", "2026-10-20"),
        ("/book", "2026-10-20"),
        ("/author", "2026-10-20"),
        ("/articles", "2026-10-20"),
        ("/reviews", "2026-10-20"),
        ("/faq", "2026-10-20"),
        ("/press", "2026-10-20"),
        ("/articles/how-vcs-make-decisions", "2026-10-20"),
        ("/articles/how-to-pitch-to-investors", "2026-10-20"),
        ("/tools", TODAY),
        ("/resources", TODAY),
    ]
    for t in TOOLS:
        urls.append((f"/tools/{t}", TODAY))
    for a in [
        "vc-too-early-meaning",
        "how-to-follow-up-with-vc-after-meeting",
        "signs-vc-interested",
        "how-many-investors-to-contact",
        "questions-to-ask-venture-capitalists",
        "how-much-to-raise-runway",
    ]:
        urls.append((f"/articles/{a}", TODAY))
    urls.append(("/vc-says", TODAY))
    for pid in PRIORITY:
        urls.append((f"/vc-says/{pid}", TODAY))
    # locale published routes
    for loc in LOCALES:
        urls.append((f"/{loc}", TODAY))
        urls.append((f"/{loc}/vc-says", TODAY))
        for pid in PRIORITY:
            urls.append((f"/{loc}/vc-says/{pid}", TODAY))
        urls.append((f"/{loc}/tools", TODAY))
        for t in TOOLS:
            urls.append((f"/{loc}/tools/{t}", TODAY))
        for a in ARTICLES:
            urls.append((f"/{loc}/articles/{a}", TODAY))
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, lastmod in urls:
        loc = abs_url(path) if path != "/" else SITE + "/"
        # sitemap uses no trailing slash except root
        if path != "/" and loc.endswith("/"):
            loc = loc[:-1]
        body.append(f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>")
    body.append("</urlset>\n")
    write(ROOT / "sitemap.xml", "\n".join(body))
    return len(urls)


def record_approval():
    rec = {
        "approvedAt": TODAY,
        "approvedBy": "Slavomir Hruska",
        "source": "Cursor owner message pt15u",
        "verbatim": "publish them",
        "scope": {
            "locales": LOCALES,
            "vcSaysEntries": PRIORITY,
            "tools": TOOLS,
            "articles": ARTICLES,
            "excluded": "remaining 20 seed phrases not expanded; book and non-listed site pages remain English-only",
        },
        "reviewProvenance": {
            "aiFluentReviewer": "claude-fluent-pass",
            "aiStatus": "machine_draft_fluent_reviewed_needs_native_approval",
            "nativeHumanReview": False,
            "publicationKind": S.PUBLISHED_KIND,
            "note": "Owner knowingly authorized publishing AI-fluent drafts without native human signoff. Do not claim native approval.",
        },
        "rollback": "Revert merge commit that introduced /sk /cs /de /pl public trees and restore prior sitemap.xml + EN hreflang-free pages from main@6a56414.",
    }
    write(ROOT / "data/PUBLICATION_APPROVAL.json", json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
    # Update publication fields on expanded records for the 10
    data = json.loads((ROOT / "data/vc_signals.expanded.json").read_text(encoding="utf-8"))
    for r in data["records"]:
        if r["id"] not in PRIORITY:
            continue
        pub = r.setdefault("publication", {})
        for loc in LOCALES:
            pub[loc] = f"/{loc}/vc-says/{r['slug']}"
        pub["en"] = f"/vc-says/{r['slug']}"
    data["localization_note"] = (
        "SK/CS/DE/PL: 10 priority records published at /{loc}/vc-says/… after owner approval (pt15u) of AI-fluent drafts. "
        "NOT native-human-reviewed. Other 20 records remain phrase seeds only. Book inLanguage=en."
    )
    write(ROOT / "data/vc_signals.expanded.json", json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return rec


def patch_en_equivalents():
    changed = []
    changed.append(inject_hreflang_en("vc-says.html", "vc_hub"))
    for pid in PRIORITY:
        changed.append(inject_hreflang_en(f"vc-says/{pid}.html", "vc_entry", pid))
    changed.append(inject_hreflang_en("tools.html", "tools_hub"))
    for t in TOOLS:
        changed.append(inject_hreflang_en(f"tools/{t}.html", "tool", t))
    for a in ARTICLES:
        changed.append(inject_hreflang_en(f"articles/{a}.html", "article", a))
    # EN home gets landing alternates pointing at locale landings
    changed.append(inject_hreflang_en("index.html", "landing"))
    return changed


def nav_crosslink_en_footer():
    """Add a Languages footer note on EN chrome pages that already have Learn nav — skip heavy rewrite; locale switcher covers UX."""
    return []


def main():
    os.chdir(ROOT)
    S.PUBLIC = True
    print("Building public locale trees…")
    written = S.build_all()
    print(f"  wrote {len(written)} locale files")
    n = update_sitemap()
    print(f"  sitemap urls: {n}")
    en = patch_en_equivalents()
    print(f"  EN hreflang patched: {len(en)}")
    rec = record_approval()
    print(f"  approval recorded: {rec['publicationKind'] if False else rec['reviewProvenance']['publicationKind']}")
    print("Staging trees left as-is under _staging/locales/ (still noindex).")
    print("DONE")


if __name__ == "__main__":
    main()
