#!/usr/bin/env python3
"""Build SK/CS/DE/PL staging drafts from FULL locale content (not English bodies).

NOT PUBLIC. Every page: <meta name="robots" content="noindex,nofollow">, html lang=sk|cs|de|pl, no canonical, no hreflang,
not in sitemap.xml; robots.txt disallows /_staging/ and vercel.json sends X-Robots-Tag: noindex.

Inputs
  data/locales/{sk,cs,de,pl}/vc_signals.first10.json   full translated entries (merged into data/vc_signals.expanded.json)
  data/i18n/{sk,cs,de,pl}.json                          hub/detail/chrome UI strings
  data/locales/{sk,cs,de,pl}/tools.json                 tool string packs
  data/locales/{sk,cs,de,pl}/chrome_signup.json         signup / captcha / cookie strings
  content/articles/{sk,cs,de,pl}/{slug}.md              article drafts
  assets/growth/{tools,vc-says}.js, site.js       EN scripts — read only, never modified

Outputs (all under _staging/locales/{loc}/)
  vc-says/index.html, vc-says/{slug}.html (10), vc-says/phrases.json
  tools/index.html, tools/{tool}.html (4)
  articles/{slug}.html (3)
  assets/tools.locale.js     generated from assets/growth/tools.js by asserted literal substitution (math untouched)
  assets/vc-says.locale.js   generated from assets/growth/vc-says.js (decoder rules/weights untouched)
  assets/site.locale.js      generated from site.js (same endpoints + consent logic, localized strings only)

Usage: python3 scripts/build_locale_staging.py          (also called by scripts/build_vc_says.py)
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_vc_says as B  # noqa: E402  (reuses head(), chrome(), page helpers; does not write public files on import)

ROOT = B.ROOT
LOCALES = ["sk", "cs", "de", "pl"]
# PUBLIC=True writes indexable /{loc}/ trees (owner-approved publish). Default staging stays noindex under _staging/.
PUBLIC = False
SITE = "https://thefundraisinggame.com"
PUBLISHED_KIND = "owner_approved_ai_fluent_review"  # NOT native human review
# per-locale typography / chrome bits that are not in the i18n packs
QUOTES = {"sk": ("„", "“"), "cs": ("„", "“"), "de": ("„", "“"), "pl": ("„", "”")}
DRAFT_TAG = {"sk": "NÁVRH", "cs": "NÁVRH", "de": "ENTWURF", "pl": "SZKIC"}
NEW_TAB = {"sk": "(otvorí sa na novej karte)", "cs": "(otevře se na nové kartě)", "de": "(öffnet in neuem Tab)", "pl": "(otwiera się w nowej karcie)"}
DATE_DISPLAY = {"sk": "9. 11. 2026", "cs": "9. 11. 2026", "de": "9. November 2026", "pl": "9 listopada 2026"}


def q(loc, x):
    return QUOTES[loc][0] + x + QUOTES[loc][1]


def tag(loc):
    if PUBLIC:
        return ""
    return f"[{DRAFT_TAG[loc]} {loc.upper()}]"
STATUS = "machine_draft_fluent_reviewed_needs_native_approval"
REVIEWED_AT = "2026-11-09"
ARTICLES = ["vc-too-early-meaning", "how-to-follow-up-with-vc-after-meeting", "signs-vc-interested"]
TOOL_SLUGS = list(B.TOOLS)
FULL_FIELDS = ["phrase", "synonyms", "h1", "shortAnswer", "interpretations", "positiveSignals", "weakSignals",
               "clarifyingQuestion", "recommendedAction", "followUpTimingNote", "editableReplyTemplate", "exampleScenario",
               "metaTitle", "metaDescription"]
BANNER_EN = "DRAFT — AI fluent draft, needs native human approval. noindex."
# Seed-phrase corrections for non-priority records (original kept as seedPhrase).
SEED_FIXES = {("not-proceeding", "cs"): "V tomto kole nebudeme v investičním procesu pokračovat."}
e = B.e


def jload(p):
    return json.loads(B.read(p))


def base(loc):
    return loc if PUBLIC else f"_staging/locales/{loc}"


def url(loc, *parts):
    return "/" + "/".join([base(loc)] + [p for p in parts if p])


def locale_home(loc):
    return f"/{loc}" if PUBLIC else "/"


def abs_url(path):

    if not path.startswith("/"):
        path = "/" + path
    return SITE + path.rstrip("/") if path != "/" else SITE + "/"


def page_kind_path(loc, kind, slug=None):
    """Return site path for an equivalent page. loc=None|'en' => English roots."""
    en = loc in (None, "en")
    if kind == "landing":
        return "/" if en else f"/{loc}"
    if kind == "vc_hub":
        return "/vc-says" if en else f"/{loc}/vc-says"
    if kind == "vc_entry":
        return f"/vc-says/{slug}" if en else f"/{loc}/vc-says/{slug}"
    if kind == "tools_hub":
        return "/tools" if en else f"/{loc}/tools"
    if kind == "tool":
        return f"/tools/{slug}" if en else f"/{loc}/tools/{slug}"
    if kind == "article":
        return f"/articles/{slug}" if en else f"/{loc}/articles/{slug}"
    raise ValueError(kind)


# --------------------------------------------------------------------------- data merge
def merge_records():
    """Copy full SK/CS/DE/PL first-10 fields into data/vc_signals.expanded.json (idempotent)."""
    data = jload("data/vc_signals.expanded.json")
    recs = {r["id"]: r for r in data["records"]}
    for loc in LOCALES:
        src = jload(f"data/locales/{loc}/vc_signals.first10.json")
        for lr in src["records"]:
            r = recs[lr["id"]]
            cur = r["locales"][loc]
            seed = cur.get("seedPhrase", cur["phrase"])
            assert lr["seedPhrase"] == seed, (loc, lr["id"], lr["seedPhrase"], seed)
            new = {"status": STATUS, "seedPhrase": seed}
            for k in FULL_FIELDS:
                new[k] = lr[k]
            new["exampleScenario"] = {"description": lr["exampleScenario"]["description"], "hypothetical": True}
            new.update({"editorialReviewer": "claude-fluent-pass", "reviewedAt": REVIEWED_AT, "reviewNote": lr["reviewNote"]})
            r["locales"][loc] = new
    for (rid, loc), phrase in SEED_FIXES.items():
        cur = recs[rid]["locales"][loc]
        if cur["phrase"] != phrase:
            cur["seedPhrase"] = cur.get("seedPhrase", cur["phrase"])
            cur["phrase"] = phrase
            cur["seedFixNote"] = "Seed contained a Slovak form (“tejto”); corrected in AI fluent pass. Needs native check."
    data["localization_note"] = ("SK/CS/DE/PL: the 10 priority records carry full translated fields (status " + STATUS +
                                 "; AI fluent pass, NOT native-approved). The other 20 records in every locale are phrase seeds only. "
                                 "seedPhrase keeps the original seed wherever a phrase was revised; the public EN hub search index reads seedPhrase so "
                                 "public EN output stays byte-identical. Nothing non-EN is published.")
    out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if out != B.read("data/vc_signals.expanded.json"):
        B.write("data/vc_signals.expanded.json", out)
    return data


# --------------------------------------------------------------------------- JS generation (literal substitution)
def js_str(s):
    assert " " not in s and " " not in s
    return json.dumps(s, ensure_ascii=False)


class Sub:
    def __init__(self, src, name):
        self.s, self.name, self.log = src, name, []

    def rep(self, old, new, count=None):
        n = self.s.count(old)
        assert n >= 1, f"{self.name}: literal not found: {old[:80]!r}"
        if count is not None:
            assert n == count, f"{self.name}: expected {count}× {old[:60]!r}, found {n}"
        self.s = self.s.replace(old, new)
        self.log.append((old, n))

    def lit(self, en, loc, count=None):
        """Replace a single-quoted JS string literal 'en' by a JSON-quoted localized literal."""
        self.rep("'" + en + "'", js_str(loc), count)


def tools_js(loc, pack, phrases):
    src = B.read("assets/growth/tools.js")
    S = Sub(src, "tools.js")
    T = pack["tools"]
    dec, fub, pipe, run = (T["investor-signal-decoder"], T["investor-follow-up-builder"],
                           T["fundraising-pipeline-calculator"], T["runway-raise-calculator"])
    bcp = pack["bcp47"]
    header = ("\n/* STAGING LOCALE BUILD (" + loc + ") — generated by scripts/build_locale_staging.py from assets/growth/tools.js.\n"
              " * Only string literals and display formatting differ. Formulas, weights, thresholds, clamping and toFixed() rounding are\n"
              " * unchanged; fx() formats the already-rounded value with Intl.NumberFormat. Parity: scripts/locale_tools_parity.js. */\n"
              f"const LOC={js_str(bcp)};\n"
              "const fx=(n,d)=>new Intl.NumberFormat(LOC,{minimumFractionDigits:d,maximumFractionDigits:d}).format(Number(n.toFixed(d)));\n"
              f"const PLC=n=>(n===1?{js_str(dec['count_one'])}:(n>=2&&n<=4)?{js_str(dec['count_few'])}:{js_str(dec['count_many'])}).replace('{{n}}',String(n));\n"
              f"const VCS_LINK={js_str(pack['common']['vcsays_link'])};\n")
    S.rep("(function(){'use strict';", "(function(){'use strict';" + header, 1)
    # display formatting only
    S.rep("new Intl.NumberFormat('en-US',", "new Intl.NumberFormat(LOC,", 1)
    S.rep("const pct=(n)=>(Number.isFinite(n)?n:0).toFixed(1)+'%';", "const pct=(n)=>fx(Number.isFinite(n)?n:0,1)+'\\u00a0%';", 1)
    S.rep("set('pipe-meetings',first.toFixed(1));set('pipe-deep',second.toFixed(1));set('pipe-terms',terms.toFixed(2));set('pipe-closes',closed.toFixed(2));",
          "set('pipe-meetings',fx(first,1));set('pipe-deep',fx(second,1));set('pipe-terms',fx(terms,2));set('pipe-closes',fx(closed,2));", 1)
    S.rep("Math.ceil(1/target).toLocaleString('en-US')", "Math.ceil(1/target).toLocaleString(LOC)", 1)
    S.rep("Number.isFinite(existing)?existing.toFixed(1):'No net burn'", "Number.isFinite(existing)?fx(existing,1):" + js_str(run["no_net_burn"]), 1)
    # strings
    S.lit("Copied ✓", pack["common"]["copied"], 2)
    S.lit("Select text to copy", pack["common"]["copy_select"], 1)
    en_items = re.findall(r"\{key:'(\w+)',label:'([^']+)'", src)
    assert len(en_items) == 8
    for key, label in en_items:
        S.rep(f"label:'{label}'", "label:" + js_str(dec["signalItems"][key]), 1)
    en_results = [("insufficient", "Insufficient signal", "You do not have enough evidence of a concrete process yet. Ask about investor fit and the next decision point.",
                   "Send a short, specific follow-up asking for the appropriate next step, then continue talking to other investors."),
                  ("mismatch", "Likely structural mismatch", "An explicit mismatch on stage, thesis, geography or check size matters more than social warmth.",
                   "Thank them, ask whether there is a better-fit colleague or fund, and move the opportunity out of your active pipeline."),
                  ("meaningful", "Meaningful process signals", "Multiple concrete steps indicate a real evaluation process; they still do not guarantee an investment.",
                   "Confirm owners, materials and dates in writing. Keep your other conversations moving."),
                  ("early", "Early signs of engagement", "A specific action is more informative than compliments, but the process is not yet conclusive.",
                   "Fulfill the request and ask what the next decision and timing will be."),
                  ("weak", "Weak or declining momentum", "Polite interest without action, or missed commitments, needs clarification rather than optimistic interpretation.",
                   "Share one substantive update and request a clear yes/no on continuing; do not invent deadlines.")]
    for k, st, de, nx in en_results:
        r = dec["results"][k]
        S.lit(st, r["status"], 1)
        S.lit(de, r["desc"], 1)
        S.lit(nx, r["next"], 1)
    S.lit("Related phrase guide: ", dec["related_prefix"], 1)
    S.rep("a.href='/vc-says';a.textContent='Browse VC Says: common investor phrases and how to reply'",
          "a.href=" + js_str(url(loc, "vc-says")) + ";a.textContent=" + js_str(dec["browse_vcsays"]), 1)
    S.rep("`${chosen.length} selected signals`", "PLC(chosen.length)", 1)
    S.lit("Under these assumptions, fewer than one term sheet is expected. Improve fit, conversion, or outreach volume; results are not guaranteed.", pipe["note_low"], 1)
    S.lit("This is an expected-value model, not a prediction of actual commitments. Small samples can vary dramatically.", pipe["note_ok"], 1)
    S.lit("Enter a positive pre-money valuation to calculate simplified dilution.", run["note_no_pre"], 1)
    S.lit("Illustrative priced-equity round only: excludes option pools, SAFEs, notes, fees and changes in burn. Confirm deal terms with your advisers.", run["note_ok"], 1)
    # follow-up templates: replace the whole object literal entry by entry
    for key, parts in re.findall(r"\n (\w+):\{(subject:'.*?',intro:'.*?',mid:'.*?',ask:'.*?')\}", src):
        loc_t = fub["templates"][key]
        for f in ["subject", "intro", "mid", "ask"]:
            en_v = re.search(f"{f}:'(.*?)'(?:,|$)", parts).group(1)
            S.rep(f"{f}:'{en_v}'", f"{f}:" + js_str(loc_t[f]), 1)
    S.rep("clean($('follow-topic').value,'the business')", "clean($('follow-topic').value," + js_str(fub["defaults"]["topic"]) + ")", 1)
    S.rep("clean($('follow-progress').value,'[specific, verifiable progress]')", "clean($('follow-progress').value," + js_str(fub["defaults"]["progress"]) + ")", 1)
    S.rep("clean($('follow-milestone').value,'[the agreed milestone]')", "clean($('follow-milestone').value," + js_str(fub["defaults"]["milestone"]) + ")", 1)
    S.rep("clean($('follow-next').value,'a short follow-up call')", "clean($('follow-next').value," + js_str(fub["defaults"]["next"]) + ")", 1)
    em = fub["email"]
    for ch in "`$\\":
        assert ch not in em["subject_prefix"] + em["greeting"] + em["signoff"]
    S.rep("`Subject: ${subs.subject}\\n\\nHi ${person},\\n\\n${subs.intro}\\n\\n${subs.mid}\\n\\n${subs.ask}\\n\\nBest,\\n[Your name]`",
          "`" + em["subject_prefix"] + "${subs.subject}\\n\\n" + em["greeting"].replace("{person}", "${person}") +
          "\\n\\n${subs.intro}\\n\\n${subs.mid}\\n\\n${subs.ask}\\n\\n" + em["signoff"] + "\\n[Your name]`", 1)
    S.lit("Scenario preselected from the VC Says entry: ", fub["signal_note_prefix"], 1)
    # Localized visible placeholders in generated emails (map from EN tokens)
    _pmap = pack.get("placeholderMapFromEnglish") or {}
    for _en, _loc in sorted(_pmap.items(), key=lambda kv: -len(kv[0])):
        S.s = S.s.replace(f"[{_en}]", f"[{_loc}]")
        S.s = S.s.replace(f"'[{_en}]'", f"'[{_loc}]'")

    # VC Says links + phrases
    S.rep("a.href='/vc-says/'+id;a.textContent='\\u201C'+VC_SAYS[id].phrase.replace(/\\.$/,'')+'\\u201D in VC Says';",
          "a.href=" + js_str(url(loc, "vc-says") + "/") + "+id;a.textContent=VCS_LINK.replace('{phrase}',VC_SAYS[id].phrase.replace(/[.?!]$/,''));", 1)
    for rid, en_phrase in re.findall(r"'([a-z-]+)':\{phrase:'(.*?)',tpl:", src):
        S.rep(f"'{rid}':{{phrase:'{en_phrase}',", f"'{rid}':{{phrase:" + js_str(phrases[rid]) + ",", 1)
    # nothing English left in user-visible literals that we know of
    out = S.s
    for leftover in ["Insufficient signal", "Copied ✓", "selected signals", "Hi ${person}", "Browse VC Says", "\\u201D in VC Says", "No net burn"]:
        assert leftover not in out, leftover
    return out


def vcsays_js(loc, t):
    s = t["strings"]
    src = B.read("assets/growth/vc-says.js")
    S = Sub(src, "vc-says.js")
    S.rep("(function () {\n  'use strict';", "(function () {\n  'use strict';\n  /* STAGING LOCALE BUILD (" + loc +
          ") — generated by scripts/build_locale_staging.py from assets/growth/vc-says.js. Only UI strings differ; RULES weights, "
          "conditions and ranking are unchanged. */", 1)
    for rid, txt in re.findall(r"\{ id: '(R\d+)'.*?text: '(.*?)' \}", src):
        S.rep(f"text: '{txt}'", "text: " + js_str(s[f"rule_{rid}"]), 1)
    S.rep("var RANK_LABELS = ['Most consistent with your answers', 'Also plausible', 'Less consistent, but still possible'];",
          "var RANK_LABELS = [" + ", ".join(js_str(s[f"decoder_rank_{i}"]) for i in (1, 2, 3)) + "];", 1)
    # Hint strings (EN source uses setHintForSuggestion / syncHintWithManualChoice). Every locale pack must define all four keys.
    S.rep("'Closest library match: “' + BY_ID[id].phrase + '”. Selected below — change the category if it doesn’t fit.'",
          js_str(s["decoder_hint_match"]) + ".replace('{phrase}', BY_ID[id].phrase)", 1)
    S.lit("No close match — choose the closest category below.", s["decoder_hint_nomatch"], 1)
    S.rep("'Using “' + BY_ID[cat.value].phrase + '” (you changed the suggested match).'",
          js_str(s["decoder_hint_manual"]) + ".replace('{phrase}', BY_ID[cat.value].phrase)", 1)
    S.lit("Choose the closest category below.", s["decoder_hint_choose"], 1)
    S.lit("Choose what the investor said or did to see plausible interpretations.", s["decoder_choose_first"], 1)
    S.rep("'Plausible interpretations of “' + res.rec.phrase + '”'", js_str(s["decoder_out_heading"]) + ".replace('{phrase}', res.rec.phrase)", 1)
    S.lit("Rules applied: ", s["decoder_rules_applied"], 1)
    S.lit("No rules applied — interpretations shown in editorial order.", s["decoder_no_rules"], 1)
    S.lit("A question that would clarify it", s["decoder_ask_heading"], 1)
    S.lit("Read the full entry and reply template →", s["decoder_read_full"], 1)
    S.lit("This is a conversation aid based on editorial rules, not a prediction of the investor’s decision. No probabilities are calculated.", s["decoder_footer_note"], 1)
    S.lit("Copied ✓", s["copied"], 1)
    S.lit("Copy failed — select the text and copy manually", s["copy_failed"], 1)
    return S.s


def site_js(loc, cs):
    s = cs["strings"]
    for v in s.values():
        assert "'" not in v and "\\" not in v, v
    src = B.read("site.js")
    S = Sub(src, "site.js")
    S.rep("/* The Fundraising Game: early-access signup (Bluefox) */",
          "/* STAGING LOCALE BUILD (" + loc + ") — generated by scripts/build_locale_staging.py from /site.js. Same endpoints, "
          "captcha flow and Consent Mode logic; only visible strings differ. */\n/* The Fundraising Game: early-access signup (Bluefox) */", 1)
    S.rep("'aria-label': 'Load a new code'", "'aria-label': '" + s["captcha_refresh_aria"] + "'", 1)
    S.rep("}, 'New code');", "}, '" + s["captcha_refresh"] + "');", 1)
    S.rep("}, 'Type the characters shown');", "}, '" + s["captcha_label"] + "');", 1)
    S.rep("placeholder: 'Code',", "placeholder: '" + s["captcha_placeholder"] + "',", 1)
    S.rep(">Loading…<", ">" + s["captcha_loading"] + "<", 2)
    S.rep(">Could not load code<", ">" + s["captcha_load_error"] + "<", 1)
    S.rep("btn.innerHTML = 'Sending…';", "btn.innerHTML = '" + s["sending"] + "';", 1)
    S.rep(">You’re on the list.<", ">" + s["success_title"] + "<", 1)
    S.rep(">Check your inbox to confirm. The bonus chapter is on its way.<", ">" + s["success_body"] + "<", 1)
    S.rep("'Something went wrong. Please try again.'", "'" + s["error_generic"] + "'", 1)
    S.rep("'Network error. Please check your connection and try again.'", "'" + s["error_network"] + "'", 1)
    S.rep("b.setAttribute('aria-label', 'Cookie consent');", "b.setAttribute('aria-label', '" + s["cookie_aria"] + "');", 1)
    S.rep(">We use Google Analytics cookies to understand how visitors use this site. Nothing is tracked unless you accept.<", ">" + s["cookie_text"] + "<", 1)
    S.rep(">Decline</button>", ">" + s["cookie_reject"] + "</button>", 1)
    S.rep(">Accept</button>", ">" + s["cookie_accept"] + "</button>", 1)
    S.rep("a.textContent = 'Cookie settings';", "a.textContent = '" + s["cookie_settings"] + "';", 1)
    return S.s


# --------------------------------------------------------------------------- chrome
def localized_chrome(loc, t, cs):
    s, c = t["strings"], cs["strings"]
    header, footer = B.chrome()
    header = header.replace(f'<a href="/vc-says" aria-current="page" style="{B.NAV_LINK_ACTIVE_STYLE}">VC Says</a>',
                            f'<a href="/vc-says" style="{B.NAV_LINK_STYLE}">VC Says</a>')
    new_tab = NEW_TAB[loc]
    reps_h = [(">The Book</a>", s["nav_book"]), (">Author</a>", s["nav_author"]), (">Articles</a>", s["nav_articles"]),
              (">VC Says</a>", s["nav_vc_says"]), (">Tools</a>", s["nav_tools"]), (">Reviews</a>", s["nav_reviews"]),
              (">FAQ</a>", s["nav_faq"]), (">Press</a>", s["nav_press"]), (">Get early access</a>", s["nav_get_early_access"])]
    for old, new in reps_h:
        assert header.count(old) == 1, old
        header = header.replace(old, ">" + e(new) + "</a>")
    header = header.replace("(opens in new tab)", new_tab).replace('href="/vc-says"', f'href="{url(loc, "vc-says")}"').replace(
        'href="/tools"', f'href="{url(loc, "tools")}"')
    if PUBLIC:
        # Brand + Home targets locale landing; English-only sections keep absolute EN paths.
        header = header.replace('href="/"', f'href="{locale_home(loc)}"', 1)
    reps_f = [(">The VIP list<", c["vip_eyebrow"]), (">Get the playbook before it hits Amazon<", c["vip_title"]),
              (">Early access, the bonus chapter PDF and a launch-day discount. One email when it matters, nothing in between.<",
               c["vip_body"] + " " + c["book_english_only"]),
              (">Email address<", c["email_label"]), (">Join the list<", c["join_the_list"]),
              (">No spam, ever. Unsubscribe anytime.<", c["no_spam"]),
              (">The unspoken rules of raising capital, from a book by Slavomír Hruška. Coming soon to Amazon.<", s["footer_tagline"]),
              (">The book</span>", None), (">About the book<", s["footer_about_book"]), (">Reviews<", s["footer_reviews"]),
              (">Pre-order<", s["footer_preorder"]), (">Learn</span>", None), (">Articles<", s["nav_articles"]), (">Tools<", s["nav_tools"]),
              (">VC Says<", s["nav_vc_says"]), (">How VCs decide<", s["footer_how_vcs_decide"] + " " + s["in_english_note"]),
              (">How to pitch investors<", s["footer_how_to_pitch"] + " " + s["in_english_note"]), (">FAQ<", s["nav_faq"]),
              (">Author</span>", None), (">About Slavomír<", s["footer_about_author"]), (">Press &amp; media kit<", s["footer_press_kit"]),
              (">Made for founders and VCs<", s["footer_made_for"])]
    for old, new in reps_f:
        assert footer.count(old) == 1, old
        if new is None:
            key = {">The book</span>": "footer_h_book", ">Learn</span>": "footer_h_learn", ">Author</span>": "footer_h_author"}[old]
            footer = footer.replace(old, ">" + e(s[key]) + "</span>")
        else:
            footer = footer.replace(old, ">" + e(new) + "<")
    footer = (footer.replace('placeholder="you@company.com"', f'placeholder="{e(c["email_placeholder"])}"')
              .replace('href="/vc-says"', f'href="{url(loc, "vc-says")}"').replace('href="/tools"', f'href="{url(loc, "tools")}"'))
    return header, footer


def set_active(header, href):
    old = f'<a href="{href}" style="{B.NAV_LINK_STYLE}">'
    assert header.count(old) == 1, href
    return header.replace(old, f'<a href="{href}" aria-current="page" style="{B.NAV_LINK_ACTIVE_STYLE}">')


def banner(loc, t):
    if PUBLIC:
        return ""
    return ('<div class="tfg-vcsays"><p class="vc-draftbanner" role="note" data-locale-status="' + STATUS + '">'
            f'<span lang="en">{e(BANNER_EN)}</span> · {e(t["strings"]["draft_banner"])}</p></div>')


def hreflang_links(kind, slug=None):
    """Reciprocal hreflang for EN + published locales for one equivalent page kind."""
    langs = [("en", "en"), ("sk", "sk"), ("cs", "cs"), ("de", "de"), ("pl", "pl")]
    out = []
    for code, loc in langs:
        path = page_kind_path(None if loc == "en" else loc, kind, slug)
        out.append(f'<link rel="alternate" hreflang="{code}" href="{e(abs_url(path))}">')
    out.append(f'<link rel="alternate" hreflang="x-default" href="{e(abs_url(page_kind_path(None, kind, slug)))}">')
    return "\n".join(out)


def language_switcher(loc, t, kind, slug=None):
    s = t["strings"]
    items = []
    for code, label_key in [("en", "lang_name_en"), ("sk", "lang_name_sk"), ("cs", "lang_name_cs"), ("de", "lang_name_de"), ("pl", "lang_name_pl")]:
        href = page_kind_path(None if code == "en" else code, kind, slug)
        label = s[label_key]
        if code == loc:
            items.append(f'<span aria-current="true" style="font-weight:600;color:rgb(245,154,106)">{e(label)}</span>')
        else:
            items.append(
                f'<a href="{e(href)}" style="color:rgb(207,197,186);text-decoration:none;min-height:44px;display:inline-flex;align-items:center" '
                f'hreflang="{code}" lang="{code}">{e(label)}</a>'
            )
    return (
        '<nav aria-label="' + e(s["lang_switcher_label"]) + '" class="tfg-lang" '
        'style="display:inline-flex;flex-wrap:wrap;gap:8px 14px;align-items:center;font-size:13px">'
        f'<span style="color:rgb(140,131,120)">{e(s["lang_switcher_label"])}:</span>'
        + "".join(items)
        + "</nav>"
    )


def staging_page(loc, t, title, desc, header, footer, main, body_attrs, scripts, extra_style="", *, kind=None, slug=None):
    title = (title or "").strip()
    if PUBLIC:
        assert kind, "public pages require kind for canonical/hreflang"
        canonical = abs_url(page_kind_path(loc, kind, slug))
        h = B.head(title, desc, canonical, lang=loc, robots=None)
        h = h.replace("</head>", hreflang_links(kind, slug) + "\n</head>")
        status_meta = PUBLISHED_KIND
        # Strip any leaked EN language switcher copied from chrome source HTML, then inject the correct one.
        header = re.sub(
            r'<div style="max-width:1240px;margin:0 auto;padding:0 24px 12px"><nav aria-label="[^"]*" class="tfg-lang".*?</nav></div>',
            "",
            header,
            flags=re.S,
        )
        header = re.sub(r'<nav aria-label="[^"]*" class="tfg-lang".*?</nav>', "", header, flags=re.S)
        switch = language_switcher(loc, t, kind, slug)
        if "</header>" in header:
            header = header.replace(
                "</header>",
                f'<div style="max-width:1240px;margin:0 auto;padding:0 24px 12px">{switch}</div></header>',
                1,
            )
    else:
        h = B.head(title, desc, None, lang=loc, robots="noindex,nofollow")
        status_meta = STATUS
    if extra_style:
        h = h.replace("</head>", "<style>\n" + extra_style + "\n</style>\n</head>")
    h = h.replace("</head>", f'<meta name="tfg-locale-status" content="{status_meta}">\n</head>')
    scripts_html = "".join(
        f'<script src="{s}" defer></script>\n' for s in [url(loc, "assets", "site.locale.js")] + scripts
    )
    body = (
        f"{h}\n<body{body_attrs}>\n{banner(loc, t)}"
        '<div class="sc-host"><div style="background: rgb(18, 20, 28); color: rgb(242, 232, 220); '
        'font-family: Geist, system-ui, sans-serif; font-size: 18px; line-height: 1.7; min-height: 100vh;">\n'
        f"{header}\n{main}\n{footer}\n</div></div>\n"
        + scripts_html
        + "</body>\n</html>\n"
    )
    if PUBLIC:
        assert 'rel="canonical"' in body and "hreflang" in body and "noindex" not in body and "vc-draftbanner" not in body
        assert "[NÁVRH" not in body and "[ENTWURF" not in body and "[SZKIC" not in body
    else:
        assert 'rel="canonical"' not in body
        assert 'rel="alternate" hreflang' not in body
        assert "vc-draftbanner" in body or not PUBLIC
    return body


# --------------------------------------------------------------------------- shared bits
def loc_rec(r, loc):
    return r["locales"][loc]


def article_meta(loc):
    out = {}
    for slug in ARTICLES:
        fm, _ = parse_md(B.read(f"content/articles/{loc}/{slug}.md"))
        out[slug] = fm
    return out


def article_link(loc, slug, titles_loc, titles_en, s):
    if slug in titles_loc:
        return f'<a href="{url(loc, "articles", slug)}">{e(titles_loc[slug]["h1"])}</a>'
    return f'<a href="/articles/{e(slug)}">{e(titles_en.get(slug, slug))}</a> <span class="vc-why">{e(s["in_english_note"])}</span>'


def tool_name(pack, slug):
    return pack["tools"][slug]["h1"]


def book_cta(t):
    s = t["strings"]
    return (f'<aside class="vc-panel" aria-label="{e(s["book_h2"])}"><h2>{e(s["book_h2"])}</h2>'
            f'<p>{e(s["book_p"])} {e(s["book_language_note"])}</p>'
            f'<a class="vc-btn" data-signup-cta href="/#join">{e(s["book_cta"])}</a></aside>')


def disclaimer(t):
    return f'<p style="font-size:13px;color:rgb(140,131,120)">{e(t["strings"]["disclaimer"])}</p>'


def class_label(t, c):
    return t["strings"].get(f"class_{c}", c)


def pills(r, t):
    s = t["strings"]
    out = [f'<span class="vc-pill cls-{e(r["signalClass"])}">{e(class_label(t, r["signalClass"]))}</span>']
    if r["recordType"] == "behavior":
        out.append(f'<span class="vc-pill">{e(s["behavior_badge"])}</span>')
    out += [f'<span class="vc-pill">{e(s.get("topic_" + x, x))}</span>' for x in r["topicTags"]]
    return '<p class="vc-meta">' + "".join(out) + "</p>"


def select(id_, label, options):
    opts = "".join(f'<option value="{e(v)}">{e(l)}</option>' for v, l in options)
    return f'<div class="vc-field"><label for="{id_}">{e(label)}</label><select id="{id_}">{opts}</select></div>'


# --------------------------------------------------------------------------- VC Says hub + detail
def build_vcsays(loc, t, pack, data, header, footer, titles_loc, titles_en):
    s = t["strings"]
    records = data["records"]
    pub = [r for r in records if r["id"] in data["priority_ids"]]
    pub.sort(key=lambda r: data["priority_ids"].index(r["id"]))
    by_id = {r["id"]: r for r in pub}
    hdr = set_active(header, url(loc, "vc-says"))
    written = []
    js = [url(loc, "assets", "vc-says.locale.js")]

    def card(r):
        L = loc_rec(r, loc)
        href = url(loc, "vc-says", r["slug"])
        return (f'<li class="vc-card" data-vc-id="{e(r["id"])}" data-class="{e(r["signalClass"])}" data-stage="{e(" ".join(r["stageTags"]))}" '
                f'data-topic="{e(" ".join(r["topicTags"]))}" data-context="{e(" ".join(r["contexts"]))}">'
                f'{pills(r, t)}<h3><a href="{href}">{e(L["phrase"])}</a></h3><p>{e(L["shortAnswer"])}</p>'
                f'<a class="vc-more" href="{href}" aria-label="{e(s["see_how_to_respond"])} {e(q(loc, L["phrase"]))}">{e(s["see_how_to_respond"])}</a></li>')

    idx = []
    for r in pub:
        L, en = loc_rec(r, loc), r["locales"]["en"]
        idx.append({"id": r["id"], "url": url(loc, "vc-says", r["slug"]), "phrase": L["phrase"], "synonyms": L["synonyms"],
                    "shortAnswer": L["shortAnswer"], "signalClass": r["signalClass"], "recordType": r["recordType"],
                    "topicTags": r["topicTags"], "stageTags": r["stageTags"], "contexts": r["contexts"],
                    "clarifyingQuestion": L["clarifyingQuestion"],
                    "interpretations": [{"kind": i["kind"], "possibility": i["possibility"]} for i in L["interpretations"]],
                    # EN phrase + synonyms + seed: matching only (so pasting an English message still finds the entry)
                    "localePhrases": [en["phrase"]] + en["synonyms"] + ([L["seedPhrase"]] if L.get("seedPhrase") and L["seedPhrase"] != L["phrase"] else [])})
    index_json = json.dumps(idx, ensure_ascii=False).replace("</", "<\\/")
    all_ = s["filter_all"]
    stages = [(k, s[f"stage_{k}"]) for k, _ in B.STAGES]
    topics = sorted({x for r in pub for x in r["topicTags"]}, key=lambda x: list(B.TOPIC_LABELS).index(x) if x in B.TOPIC_LABELS else 99)
    contexts = [c for c in B.CONTEXT_LABELS if any(c in r["contexts"] for r in pub)]
    classes = [c for c in B.CLASS_ORDER if any(r["signalClass"] == c for r in pub)]
    count_tpl = s["results_count"]
    prep = [r for r in records if r["id"] not in data["priority_ids"]]
    controls = (
        '<section class="vc-wrap" aria-labelledby="vc-browse-title" style="display:flex;flex-direction:column;gap:18px;padding-bottom:40px">'
        f'<h2 id="vc-browse-title">{e(s["h_browse"])}</h2>'
        '<form id="vc-search-form" role="search" class="vc-panel" onsubmit="return false">'
        f'<div class="vc-field"><label for="vc-q">{e(s["search_label"])}</label><div class="vc-searchrow">'
        f'<input id="vc-q" type="search" autocomplete="off" placeholder="{e(s["search_placeholder"])}" aria-describedby="vc-count">'
        f'<button id="vc-q-clear" type="button" class="vc-btn secondary" hidden>{e(s["search_clear"])}</button></div></div>'
        '<div class="vc-controls">'
        + select("vc-f-stage", s["filter_stage"], [("", all_)] + stages)
        + select("vc-f-class", s["filter_signal"], [("", all_)] + [(c, class_label(t, c)) for c in classes])
        + select("vc-f-topic", s["filter_topic"], [("", all_)] + [(x, s.get("topic_" + x, x)) for x in topics])
        + select("vc-f-context", s["filter_context"], [("", all_)] + [(c, s["context_" + c]) for c in contexts])
        + f'<button id="vc-reset" type="button" class="vc-btn secondary">{e(s["filter_reset"])}</button></div>'
        f'<p id="vc-count" class="vc-count" aria-live="polite" data-template="{e(count_tpl)}">{e(count_tpl.replace("{n}", str(len(pub))))}</p>'
        '</form>'
        f'<ul id="vc-list" class="vc-grid">{"".join(card(r) for r in pub)}</ul>'
        f'<p id="vc-empty" class="vc-empty" hidden>{e(s["no_results"])}</p>'
        f'<p class="vc-count">{e(s["more_entries_note"])}</p>'
        f'<details class="vc-rules"><summary>{e(s["h_in_preparation"])} ({len(prep)})</summary><p>{e(s["in_preparation_note"])}</p><ul>'
        + "".join(f'<li>{e(loc_rec(r, loc)["phrase"])} <span class="vc-why">· {e(class_label(t, r["signalClass"]))}</span></li>' for r in prep)
        + '</ul></details></section>')
    next_opts = [("", s["opt_not_sure"])] + [(k, s["next_" + k]) for k in ["none", "vague", "specific", "materials", "internal", "otherfund"]]
    el_opts = [("", s["opt_not_sure"])] + [(k, s["elapsed_" + k]) for k in ["short", "mid", "long", "missed"]]
    rule_ids = [rid for rid, _ in B.DECODER_RULES]
    decoder = (
        '<section class="vc-wrap" aria-labelledby="vc-dec-title" style="padding-bottom:40px"><div class="vc-panel">'
        f'<span class="vc-eyebrow">{e(s["decoder_title"])}</span>'
        f'<h2 id="vc-dec-title">{e(s["decoder_h2"])}</h2>'
        f'<p class="vc-notice" id="vc-privacy">{e(s["privacy_note"])}</p>'
        f'<div class="vc-field"><label for="vc-dec-paste">{e(s["decoder_paste_label"])}</label>'
        f'<textarea id="vc-dec-paste" rows="3" autocomplete="off" placeholder="{e(s["decoder_paste_placeholder"])}" aria-describedby="vc-privacy vc-dec-paste-hint"></textarea>'
        '<p id="vc-dec-paste-hint" class="vc-why" aria-live="polite"></p></div>'
        '<div class="vc-controls">'
        + select("vc-dec-stage", s["decoder_stage_label"], [("", s["opt_not_sure"])] + stages)
        + select("vc-dec-category", s["decoder_category_label"], [("", s["opt_choose"])] + [(r["id"], loc_rec(r, loc)["phrase"]) for r in pub])
        + select("vc-dec-next", s["decoder_next_label"], next_opts)
        + select("vc-dec-elapsed", s["decoder_elapsed_label"], el_opts)
        + '</div>'
        f'<button id="vc-dec-run" type="button" class="vc-btn">{e(s["decoder_run"])} →</button>'
        '<div id="vc-dec-out" class="vc-decoder-out" aria-live="polite"></div>'
        f'<p class="vc-why">{e(s["decoder_disclaimer"])}</p>'
        f'<details class="vc-rules"><summary>{e(s["rules_summary"])}</summary><p>{e(s["rules_intro"])}</p><ul>'
        + "".join(f"<li><b>{rid}</b> — {e(s['rule_' + rid])}</li>" for rid in rule_ids)
        + '</ul></details></div></section>')
    tool_links = "".join(f'<li><a href="{url(loc, "tools", k)}" data-vc-tool="{k}">{e(tool_name(pack, k))}</a></li>' for k in TOOL_SLUGS)
    dec_a = f'<a href="{url(loc, "tools", "investor-signal-decoder")}" data-vc-tool="investor-signal-decoder">{e(tool_name(pack, "investor-signal-decoder"))}</a>'
    fub_a = f'<a href="{url(loc, "tools", "investor-follow-up-builder")}" data-vc-tool="investor-follow-up-builder">{e(tool_name(pack, "investor-follow-up-builder"))}</a>'
    tools_para = e(s["tools_para"]).replace("{decoder}", dec_a).replace("{builder}", fub_a)
    art = "".join(f"<li>{article_link(loc, a, titles_loc, titles_en, s)}</li>" for a in
                  ["vc-too-early-meaning", "signs-vc-interested", "how-to-follow-up-with-vc-after-meeting",
                   "questions-to-ask-venture-capitalists", "how-many-investors-to-contact", "how-vcs-make-decisions"]
                  if a in titles_loc or a in titles_en)
    related = (
        '<section class="vc-narrow" style="display:flex;flex-direction:column;gap:22px;padding-bottom:72px">'
        f'<div class="vc-section"><h2>{e(s["h_tools"])}</h2><ul class="vc-links">{tool_links}</ul>'
        f'<p style="color:rgb(207,197,186)">{tools_para}</p></div>'
        f'<div class="vc-section"><h2>{e(s["h_guides"])}</h2><ul class="vc-links">{art}</ul></div>'
        f'<p class="vc-label">{e(s["editorial_label"])}</p><p style="color:rgb(207,197,186)">{e(s["editorial_note"])}</p>'
        + book_cta(t) + disclaimer(t) + '</section>')
    hero = (f'<div class="vc-hero"><span class="vc-eyebrow">{e(s["hub_eyebrow"])}</span>'
            f'<h1>{e(s["hub_title"])}</h1><p class="vc-lead">{e(s["hub_subtitle"])} {e(s["hub_lead"])}</p>'
            f'<p class="vc-meta"><span class="vc-pill">{e(s["badge_no_account"])}</span><span class="vc-pill">{e(s["badge_local"])}</span>'
            f'<span class="vc-pill">{e(s["editorial_label"])}</span></p></div>')
    main = (f'<main class="tfg-vcsays">{B.breadcrumb_nav([(s["breadcrumb_home"], locale_home(loc)), (s["nav_vc_says"], None)])}{hero}{controls}{decoder}{related}'
            f'<script type="application/json" id="vc-says-index">{index_json}</script></main>')
    title = f'{tag(loc)} {s["hub_title"]} | The Fundraising Game'
    written.append(B.write(f"{base(loc)}/vc-says/index.html",
                           staging_page(loc, t, title, f'{s["hub_subtitle"]} {s["hub_lead"]}', hdr, footer, main,
                                        f' data-vc-hub="{loc}"' + ("" if PUBLIC else f' data-vc-draft="{loc}"'), js,
                                        kind="vc_hub")))

    for r in pub:
        L = loc_rec(r, loc)
        hub_href = url(loc, "vc-says")
        is_beh = r["recordType"] == "behavior"
        interp = "".join(f'<li><b>{e(i["possibility"])}</b><span class="vc-clues">{e(s["clues_label"])} {e(i["contextualClues"])}</span></li>'
                         for i in L["interpretations"])
        srcs = r.get("sources") or []
        src_html = f'<p class="vc-label">{e(s["editorial_label"])}</p><p>{e(s["editorial_note"])}</p><p>{e(s["evidence_note"])}</p>'
        if srcs:
            src_html += (f"<p>{e(s['background_reading'])}</p><ul>"
                         + "".join(f'<li><a href="{e(x["url"])}" rel="noopener" target="_blank">{e(x["title"])}</a></li>' for x in srcs) + "</ul>")
        rel_entries = "".join(f'<li><a href="{url(loc, "vc-says", by_id[x]["slug"])}">{e(loc_rec(by_id[x], loc)["phrase"])}</a></li>'
                              for x in r.get("relatedSignalIds", []) if x in by_id)
        rel_articles = "".join(f"<li>{article_link(loc, a, titles_loc, titles_en, s)}</li>" for a in r.get("relatedArticleSlugs", [])
                               if a in titles_loc or a in titles_en)
        rel_tools = "".join(
            f'<li><a href="{url(loc, "tools", k)}{"?signal=" + e(r["id"]) if k == "investor-follow-up-builder" else ""}" data-vc-tool="{e(k)}">{e(tool_name(pack, k))}</a></li>'
            for k in r.get("relatedToolSlugs", []) if k in B.TOOLS)
        said_note = f'<p class="vc-why">{e(s["behavior_note"])}</p>' if is_beh else ""
        syn = f'<p class="vc-why">{e(s["also_phrased"])} {e(" · ".join(q(loc, x) for x in L["synonyms"]))}</p>' if L["synonyms"] else ""
        fub = f'{url(loc, "tools", "investor-follow-up-builder")}?signal={e(r["id"])}'
        main = (
            f'<main class="tfg-vcsays">{B.breadcrumb_nav([(s["breadcrumb_home"], locale_home(loc)), (s["nav_vc_says"], hub_href), (L["phrase"], None)])}'
            f'<div class="vc-hero"><span class="vc-eyebrow">{e(s["nav_vc_says"])} · {e(class_label(t, r["signalClass"]))}</span>'
            f'<h1>{e(L["h1"])}</h1>{pills(r, t)}'
            f'<p class="vc-label">{e(s["editorial_label"])} · {e(s["updated"])} {e(r["revisedAt"])}</p></div>'
            f'<article class="vc-narrow" style="display:flex;flex-direction:column;padding-bottom:72px">'
            f'<p class="vc-lead" style="padding-bottom:28px">{e(L["shortAnswer"])}</p>'
            f'<section class="vc-section"><h2>{e(s["h_what_they_said"])}</h2><blockquote class="vc-quote">{e(L["phrase"])}</blockquote>{said_note}{syn}</section>'
            f'<section class="vc-section"><h2>{e(s["h_might_mean"])}</h2><p>{e(s["interp_intro"])}</p><ul class="vc-interp">{interp}</ul></section>'
            f'<section class="vc-section"><h2>{e(s["h_strengthens_weakens"])}</h2><div class="vc-two">'
            f'<div><h3>{e(s["h_strengthens"])}</h3>{B.ul(L["positiveSignals"])}</div><div><h3>{e(s["h_weakens"])}</h3>{B.ul(L["weakSignals"])}</div></div></section>'
            f'<section class="vc-section"><h2>{e(s["h_ask"])}</h2><p class="vc-ask">{e(L["clarifyingQuestion"])}</p></section>'
            f'<section class="vc-section"><h2>{e(s["h_next"])}</h2><p>{e(L["recommendedAction"])}</p>'
            f'<h3>{e(s["h_timing"])}</h3><p>{e(L["followUpTimingNote"])}</p></section>'
            f'<section class="vc-section" aria-labelledby="vc-reply-h"><h2 id="vc-reply-h">{e(s["h_reply"])}</h2>'
            f'<p class="vc-why">{e(s["reply_hint"])}</p>'
            f'<label for="vc-reply" class="vc-label">{e(s["reply_label"])}</label>'
            f'<textarea id="vc-reply" class="vc-reply" spellcheck="true" lang="{loc}">{e(L["editableReplyTemplate"])}</textarea>'
            f'<div class="vc-copyrow"><button id="vc-copy" type="button" class="vc-btn" data-ok="{e(s["copied"])}" data-fail="{e(s["copy_failed"])}">{e(s["copy"])}</button>'
            f'<button id="vc-reply-reset" type="button" class="vc-btn secondary">{e(s["reply_reset"])}</button>'
            f'<span id="vc-copy-status" class="vc-status" role="status" aria-live="polite"></span></div>'
            f'<p class="vc-why">{e(s["reply_fub_prefix"])} <a href="{fub}" data-vc-tool="investor-follow-up-builder">{e(s["reply_fub_link"])}</a>.</p></section>'
            f'<section class="vc-section"><h2>{e(s["h_example"])}</h2><p class="vc-why">{e(s["hypothetical"])} {e(s["hypothetical_suffix"])}</p><p>{e(L["exampleScenario"]["description"])}</p></section>'
            f'<section class="vc-section"><h2>{e(s["h_sources"])}</h2>{src_html}</section>'
            f'<section class="vc-section"><h2>{e(s["h_related"])}</h2>'
            + (f'<h3>{e(s["h_more_entries"])}</h3><ul class="vc-links">{rel_entries}</ul>' if rel_entries else "")
            + (f'<h3>{e(s["h_guides_short"])}</h3><ul class="vc-links">{rel_articles}</ul>' if rel_articles else "")
            + (f'<h3>{e(s["h_tools_short"])}</h3><ul class="vc-links">{rel_tools}</ul>' if rel_tools else "")
            + f'<p><a href="{hub_href}">{e(s["all_entries"])}</a></p></section>'
            + book_cta(t) + disclaimer(t) + "</article></main>")
        title = f'{tag(loc)} {L["metaTitle"]}'
        written.append(B.write(f"{base(loc)}/vc-says/{r['slug']}.html",
                               staging_page(loc, t, title, L["metaDescription"], hdr, footer, main,
                                            ("" if PUBLIC else f' data-vc-draft="{loc}"') + f' data-vc-signal="{e(r["id"])}" data-vc-class="{e(r["signalClass"])}"', js,
                                            kind="vc_entry", slug=r["slug"])))
    phrases = {"locale": loc, "review_status": STATUS if not PUBLIC else PUBLISHED_KIND,
               "publication_status": "published_owner_approved_ai_fluent" if PUBLIC else "draft_not_public",
               "note": ("10 priority entries published with owner approval after AI fluent review (not native human review). Other 20: phrase seeds only."
                        if PUBLIC else "10 priority entries: full fluent-reviewed drafts (needs native approval). Other 20: phrase seeds only."),
               "phrases": [{"id": r["id"], "signalClass": r["signalClass"], "en": r["locales"]["en"]["phrase"],
                            loc: loc_rec(r, loc)["phrase"], "seedPhrase": loc_rec(r, loc).get("seedPhrase", loc_rec(r, loc)["phrase"]),
                            "status": loc_rec(r, loc)["status"]} for r in records]}
    written.append(B.write(f"{base(loc)}/vc-says/phrases.json", json.dumps(phrases, ensure_ascii=False, indent=2) + "\n"))
    return written


# --------------------------------------------------------------------------- tools
STYLE_MONO = "font-family:&quot;Geist Mono&quot;,monospace;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:rgb(245,154,106)"
STYLE_SERIF = "margin:0;font-family:&quot;Instrument Serif&quot;,Georgia,serif;font-weight:400"
PILL = "display:inline-flex;padding:6px 12px;border-radius:999px;background:rgba(242,232,220,.08);font-size:13px;color:rgb(185,175,164)"


def tool_style():
    src = B.read("tools/investor-signal-decoder.html")
    m = re.search(r"/\* growth tools scoped \*/(.*?)</style>", src, re.S)
    return "/* growth tools scoped (copied from tools/*.html) */" + m.group(1).rstrip()


def en_input(tool, id_):
    m = re.search(r'<input id="' + re.escape(id_) + r'"[^>]*>', B.read(f"tools/{tool}.html"))
    assert m, (tool, id_)
    return m.group(0)


def vcs_phrase_link(loc, pack, rid, phrase):
    return f'<a href="{url(loc, "vc-says", rid)}">{e(q(loc, phrase.rstrip(".?!")))}</a>'


def build_tools(loc, t, pack, phrases, header, footer, titles_loc, titles_en):
    C, s = pack["common"], t["strings"]
    hdr = set_active(header, url(loc, "tools"))
    style = tool_style()
    js = [url(loc, "assets", "tools.locale.js")]
    written = []
    hub_link = f'<a href="{url(loc, "vc-says")}">{e(s["nav_vc_says"])}</a>'

    def crumbs(name):
        return B.breadcrumb_nav([(C["breadcrumb_home"], locale_home(loc)), (C["breadcrumb_tools"], url(loc, "tools")), (name, None)])

    def hero(T):
        return ('<div style="max-width:1240px;margin:0 auto;padding:40px 24px 28px;display:flex;flex-direction:column;gap:14px">'
                f'<span style="{STYLE_MONO}">{e(T["eyebrow"])}</span>'
                f'<h1 style="{STYLE_SERIF};font-size:clamp(40px,5vw,64px);line-height:1.05">{e(T["h1"])}</h1>'
                f'<p style="margin:0;max-width:720px;font-size:20px;color:rgb(207,197,186)">{e(T["meta_description"])}</p>'
                f'<p style="margin:0;display:flex;flex-wrap:wrap;gap:8px"><span style="{PILL}">{e(C["badge_no_account"])}</span><span style="{PILL}">{e(C["badge_local"])}</span></p></div>')

    def how(T, extra=""):
        a = T["related_article"]
        if a in titles_loc:
            link = f'<a href="{url(loc, "articles", a)}">{e(C["related_guide_link"])}</a>'
        else:
            link = f'<a href="/articles/{a}">{e(C["related_guide_link"])}</a> {e(C["in_english_note"])}'
        rel = e(C["related_guide"]).replace("{link}", link).replace("{tools}", f'<a href="{url(loc, "tools")}">{e(C["related_tools_link"])}</a>')
        return ('<section style="max-width:760px;margin:0 auto;padding:8px 24px 72px;display:flex;flex-direction:column;gap:18px;color:rgb(207,197,186)">\n'
                f'<h2 style="{STYLE_SERIF};font-size:32px;color:rgb(242,232,220)">{e(C["how_h2"])}</h2>\n'
                f'<p style="margin:0">{e(C["how_p"])}</p>\n<p style="margin:0">{rel}</p>\n{extra}'
                '<aside style="margin-top:12px;padding:28px;border-radius:20px;background:rgb(26,29,39);display:flex;flex-direction:column;gap:12px">'
                f'<h3 style="{STYLE_SERIF};font-size:26px;color:rgb(242,232,220)">{e(C["book_h3"])}</h3><p style="margin:0">{e(C["book_p"])}</p>'
                f'<a class="tfg-btn" data-signup-cta href="/#join">{e(C["book_cta"])}</a></aside>\n'
                f'<p style="margin:0;font-size:13px;color:rgb(140,131,120)">{e(C["disclaimer"])}</p>\n</section>')

    def fill_para(tpl, ids):
        out = tpl.replace("{hub}", hub_link)
        for rid in ids:
            out = out.replace("{" + rid + "}", vcs_phrase_link(loc, pack, rid, phrases[rid]))
        assert "{" not in out, out
        return f'<p style="margin:0">{out}</p>\n'

    def h2(x):
        return f'<h2 style="{STYLE_SERIF};font-size:28px">{e(x)}</h2>'

    def field(id_, label, inp):
        return f'<div class="field"><label for="{id_}">{e(label)}</label>{inp}</div>\n'

    pages = {}
    # signal decoder
    T = pack["tools"]["investor-signal-decoder"]
    pages["investor-signal-decoder"] = (
        f'<div class="tool-layout"><section class="toolbox" aria-label="{e(C["inputs_aria"])}">{h2(T["inputs_h2"])}<p class="hint">{e(T["hint"])}</p>'
        f'<div id="signals-list" role="group" aria-label="{e(T["group_aria"])}"></div><button id="signals-calculate" class="tfg-btn" type="button">{e(T["calculate"])}</button></section>'
        f'<section class="result" aria-live="polite"><span style="{STYLE_MONO}">{e(T["result_eyebrow"])}</span>'
        f'<h3 id="signal-status" style="{STYLE_SERIF};font-size:28px">{e(T["initial_status"])}</h3><div class="scoreline" aria-hidden="true"><span id="signal-meter" style="width:5%"></span></div>'
        f'<p id="signal-count" class="mini">{e(T["initial_count"])}</p><p id="signal-desc">{e(T["initial_desc"])}</p>'
        f'<h3 style="margin:8px 0 0;font-family:&quot;Instrument Serif&quot;,Georgia,serif;font-weight:400;font-size:22px">{e(T["next_h3"])}</h3>'
        f'<p id="signal-next">{e(T["initial_next"])}</p><p id="signal-related" class="mini"><a href="{url(loc, "vc-says")}">{e(T["browse_vcsays"])}</a></p>'
        f'<div class="notice">{e(T["notice"])}</div></section></div>'
        + how(T, fill_para(T["vcsays_para"], ["second-meeting", "partner-introduction", "not-right-fit", "investor-ghosting"])))
    # follow-up builder
    T = pack["tools"]["investor-follow-up-builder"]
    opts = "".join(f'<option value="{k}">{e(v)}</option>' for k, v in T["scenarios"].items())
    fl = ""
    for fid, key in [("follow-company", "company"), ("follow-name", "name"), ("follow-topic", "topic"), ("follow-progress", "progress"),
                     ("follow-milestone", "milestone"), ("follow-next", "next")]:
        inp = re.sub(r'placeholder="[^"]*"', f'placeholder="{e(T["fields"][key]["placeholder"])}"', en_input("investor-follow-up-builder", fid))
        fl += field(fid, T["fields"][key]["label"], inp)
    pages["investor-follow-up-builder"] = (
        f'<div class="tool-layout"><section class="toolbox" aria-label="{e(C["inputs_aria"])}">{h2(T["inputs_h2"])}<p class="hint">{e(T["hint"])}</p>\n'
        '<p id="follow-signal-note" class="notice" hidden></p>\n'
        + field("follow-type", T["scenario_label"], f'<select id="follow-type">{opts}</select>') + fl
        + f'<button id="followup-calculate" class="tfg-btn" type="button">{e(T["calculate"])}</button></section>\n'
        f'<section class="result" aria-live="polite"><span style="{STYLE_MONO}">{e(T["result_eyebrow"])}</span>\n'
        + field("follow-output", T["output_label"], f'<textarea id="follow-output" readonly rows="14" lang="{loc}"></textarea>')
        + f'<button id="follow-copy" class="tfg-btn secondary" type="button">{e(T["copy"])}</button>\n'
        f'<div class="notice">{e(T["notice"])}</div></section></div>'
        + how(T, fill_para(T["vcsays_para"], ["too-early", "keep-in-touch", "investor-ghosting"])))
    # pipeline
    T = pack["tools"]["fundraising-pipeline-calculator"]
    fl = "".join(field(k, v, en_input("fundraising-pipeline-calculator", k)) for k, v in T["fields"].items())
    mets = "".join(f'<div class="metric"><b id="{k}">—</b><span>{e(v)}</span></div>' for k, v in T["metrics"].items())
    pages["fundraising-pipeline-calculator"] = (
        f'<div class="tool-layout"><section class="toolbox" aria-label="{e(C["inputs_aria"])}">{h2(T["inputs_h2"])}<p class="hint">{e(T["hint"])}</p>\n{fl}'
        f'<button id="pipeline-calculate" class="tfg-btn" type="button">{e(T["calculate"])}</button></section>\n'
        f'<section class="result" aria-live="polite"><span style="{STYLE_MONO}">{e(T["result_eyebrow"])}</span>\n<div class="metrics">{mets}</div>\n'
        f'<p class="mini">{e(T["close_rate"])} <strong id="pipe-close-rate" style="color:rgb(242,232,220)">—</strong></p>\n'
        f'<p class="mini">{e(T["needed"])} <strong id="pipe-needed" style="color:rgb(242,232,220)">—</strong></p>\n'
        '<p id="pipe-note" class="notice"></p></section></div>' + how(T))
    # runway
    T = pack["tools"]["runway-raise-calculator"]
    fl = "".join(field(k, v, en_input("runway-raise-calculator", k)) for k, v in T["fields"].items())
    mets = "".join(f'<div class="metric"><b id="{k}">—</b><span>{e(v)}</span></div>' for k, v in T["metrics"].items())
    pages["runway-raise-calculator"] = (
        f'<div class="tool-layout"><section class="toolbox" aria-label="{e(C["inputs_aria"])}">{h2(T["inputs_h2"])}<p class="hint">{e(T["hint"])}</p>\n{fl}'
        f'<button id="runway-calculate" class="tfg-btn" type="button">{e(T["calculate"])}</button></section>\n'
        f'<section class="result" aria-live="polite"><span style="{STYLE_MONO}">{e(T["result_eyebrow"])}</span>\n<div class="metrics">{mets}</div>\n'
        f'<p class="mini">{e(T["post"])} <strong id="run-post" style="color:rgb(242,232,220)">—</strong></p>\n'
        f'<p class="mini">{e(T["pool"])} <strong id="run-pool" style="color:rgb(242,232,220)">—</strong></p>\n'
        '<p id="run-note" class="notice"></p></section></div>' + how(T))
    for slug, body in pages.items():
        T = pack["tools"][slug]
        main = f'<main class="tfg-tool">{crumbs(T["h1"])}{hero(T)}{body}</main>'
        written.append(B.write(f"{base(loc)}/tools/{slug}.html",
                               staging_page(loc, t, f'{tag(loc)} {T["meta_title"]}', T["meta_description"], hdr, footer, main,
                                            f' data-tool="{slug}"' + ("" if PUBLIC else f' data-tfg-draft="{loc}"'), js, style,
                                            kind="tool", slug=slug)))
    H = pack["hub"]
    cards = "".join(
        f'<a href="{url(loc, "tools", k)}" class="scp0" style="display:flex;flex-direction:column;gap:10px;padding:28px;border-radius:20px;background:rgb(26,29,39);color:rgb(242,232,220);text-decoration:none">'
        f'<span style="font-family:&quot;Geist Mono&quot;,monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:rgb(245,154,106)">{e(H["card_badge"])}</span>'
        f'<span style="font-family:&quot;Instrument Serif&quot;,Georgia,serif;font-size:30px;line-height:1.15">{e(pack["tools"][k]["h1"])}</span>'
        f'<span style="font-size:16px;color:rgb(185,175,164)">{e(pack["tools"][k]["meta_description"])}</span></a>' for k in TOOL_SLUGS)
    foot = e(H["footer"]).replace("{guides}", f'<a href="/articles">{e(H["footer_guides_link"])}</a> {e(C["in_english_note"])}')
    main = ('<main><div style="max-width:1240px;margin:0 auto;padding:56px 24px 88px;display:flex;flex-direction:column;gap:28px">'
            f'{B.breadcrumb_nav([(C["breadcrumb_home"], locale_home(loc)), (C["breadcrumb_tools"], None)])}'
            f'<header style="display:flex;flex-direction:column;gap:14px;max-width:760px"><span style="{STYLE_MONO}">{e(H["eyebrow"])}</span>'
            f'<h1 style="{STYLE_SERIF};font-size:clamp(42px,5vw,64px);line-height:1.05">{e(H["h1_before"])}<span style="font-style:italic;color:rgb(224,82,47)">{e(H["h1_em"])}</span>{e(H["h1_after"])}</h1>'
            f'<p style="margin:0;font-size:20px;color:rgb(207,197,186)">{e(H["lead"])}</p></header>'
            f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:20px">{cards}</div>'
            f'<p style="margin:12px 0 0;font-size:14px;color:rgb(140,131,120)">{foot}</p></div></main>')
    written.append(B.write(f"{base(loc)}/tools/index.html",
                           staging_page(loc, t, f'{tag(loc)} {H["meta_title"]}', H["meta_description"], hdr, footer, main,
                                        ("" if PUBLIC else f' data-tfg-draft="{loc}"'), js,
                                        kind="tools_hub")))
    return written


# --------------------------------------------------------------------------- articles (minimal markdown)
def parse_md(src):
    m = re.match(r"---\n(.*?)\n---\n(.*)$", src, re.S)
    assert m, "front matter missing"
    fm = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm, m.group(2).strip()


A_P = "margin:0;color:rgb(207,197,186)"
A_H2 = "margin:24px 0 0;font-family:&quot;Instrument Serif&quot;,Georgia,serif;font-weight:400;font-size:36px;line-height:1.1"
A_H3 = "margin:18px 0 0;font-family:&quot;Instrument Serif&quot;,Georgia,serif;font-weight:400;font-size:28px;line-height:1.15"
A_BQ = "margin:0;padding:18px 22px;border-left:3px solid rgb(224,82,47);background:rgb(26,29,39);border-radius:0 16px 16px 0;color:rgb(207,197,186)"
A_ASIDE = "margin:0;padding:24px 28px;border-radius:20px;background:rgb(242,232,220);color:rgb(18,20,28)"
A_LIST = "margin:0;padding-left:24px;color:rgb(207,197,186);display:flex;flex-direction:column;gap:10px"
A_TD = "padding:10px;border-bottom:1px solid rgba(242,232,220,.08);vertical-align:top;text-align:left"


def inline(txt, loc, titles_loc):
    def link(m):
        label, href = m.group(1), m.group(2)
        if href.startswith("/tools/"):
            href2 = url(loc, "tools", href.split("/")[2])
            return f'<a href="{e(href2)}">{label}</a>'
        if href.startswith("/articles/"):
            slug = href.split("/")[2]
            if slug in titles_loc:
                return f'<a href="{e(url(loc, "articles", slug))}">{label}</a>'
            return f'<a href="{e(href)}">{label}</a>'
        if href.startswith("http"):
            return f'<a href="{e(href)}" rel="noopener" target="_blank">{label}</a>'
        return f'<a href="{e(href)}"' + (' data-signup-cta' if href == "/#join" else "") + f'>{label}</a>'
    out = e(txt)
    out = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: link(m), out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", out)
    return out


def md_to_html(body, loc, titles_loc):
    blocks = re.split(r"\n\s*\n", body.strip())
    out, first = [], True
    for b in blocks:
        lines = b.splitlines()
        if b.startswith("|"):
            rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines if not re.match(r"^\|\s*-", l)]
            head_, rows_ = rows[0], rows[1:]
            out.append('<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:15px;color:rgb(207,197,186)"><thead><tr>'
                       + "".join(f'<th style="{A_TD};color:rgb(242,232,220)">{inline(c, loc, titles_loc)}</th>' for c in head_) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f'<td style="{A_TD}">{inline(c, loc, titles_loc)}</td>' for c in r) + "</tr>" for r in rows_)
                       + "</tbody></table></div>")
        elif b.startswith(">"):
            inner = "<br>".join(inline(re.sub(r"^>\s?", "", l), loc, titles_loc) for l in lines)
            if first:
                out.append(f'<aside style="{A_ASIDE}">{inner}</aside>')
            else:
                out.append(f'<blockquote style="{A_BQ}">{inner}</blockquote>')
        elif b.startswith("### "):
            out.append(f'<h3 style="{A_H3}">{inline(b[4:], loc, titles_loc)}</h3>')
        elif b.startswith("## "):
            out.append(f'<h2 style="{A_H2}">{inline(b[3:], loc, titles_loc)}</h2>')
        elif re.match(r"^\d+\.\s", b):
            out.append(f'<ol style="{A_LIST}">' + "".join(f"<li>{inline(re.sub(r'^\d+\.\s+', '', l), loc, titles_loc)}</li>" for l in lines) + "</ol>")
        elif b.startswith("- "):
            out.append(f'<ul style="{A_LIST}">' + "".join(f"<li>{inline(l[2:], loc, titles_loc)}</li>" for l in lines) + "</ul>")
        else:
            out.append(f'<p style="{A_P}">{inline(" ".join(l.strip() for l in lines), loc, titles_loc)}</p>')
        first = False
    return "\n".join(out)


def build_articles(loc, t, header, footer, titles_loc):
    hdr = set_active(header, "/articles")
    written = []
    for slug in ARTICLES:
        fm, body = parse_md(B.read(f"content/articles/{loc}/{slug}.md"))
        for k in ["title", "description", "h1", "eyebrow", "readingTime", "status"]:
            assert fm.get(k), (loc, slug, k)
        assert fm["status"] == STATUS, (loc, slug)
        meta = (f'<div style="display:flex;align-items:center;gap:12px;font-size:15px;color:rgb(185,175,164)">'
                f'<img src="/assets/slavomir-hruska-portrait.webp" alt="" style="width:40px;height:40px;border-radius:50%;object-fit:cover">'
                f'<span><a href="/author" style="color:rgb(242,232,220);text-decoration:none;font-weight:600">Slavomír Hruška</a> · '
                f'<time datetime="2026-11-09">{DATE_DISPLAY[loc]}</time> · {e(fm["readingTime"])}</span></div>')
        main = ('<main><article style="max-width:760px;margin:0 auto;padding:40px 24px 88px;display:flex;flex-direction:column;gap:24px">'
                '<header style="display:flex;flex-direction:column;gap:22px;padding-bottom:16px">'
                f'<span style="{STYLE_MONO}">{e(fm["eyebrow"])}</span>'
                f'<h1 style="margin:0;font-family:&quot;Instrument Serif&quot;,Georgia,serif;font-weight:400;font-size:clamp(42px,5.4vw,68px);line-height:1.02;letter-spacing:-.01em;text-wrap:balance">{e(fm["h1"])}</h1>'
                f'{meta}</header>{md_to_html(body, loc, titles_loc)}</article></main>')
        written.append(B.write(f"{base(loc)}/articles/{slug}.html",
                               staging_page(loc, t, f'{tag(loc)} {fm["title"]} | The Fundraising Game', fm["description"],
                                            hdr, footer, main, f' data-article="{slug}"' + ("" if PUBLIC else f' data-tfg-draft="{loc}"'), [],
                                            kind="article", slug=slug)))
    return written



def build_landing(loc, t, pack, data, header, footer, titles_loc):
    """Locale home hub listing published VC Says / tools / articles only."""
    s = t["strings"]
    lang = s[f"lang_name_{loc}"]
    hdr = header  # no nav section is "current" on landing; brand links to locale home
    # Point brand logo to locale landing
    hdr = hdr.replace('href="/"', f'href="{locale_home(loc)}"', 1)
    pub = [r for r in data["records"] if r["id"] in data["priority_ids"]]
    pub.sort(key=lambda r: data["priority_ids"].index(r["id"]))
    cards_vc = "".join(
        f'<li style="margin:0"><a href="{url(loc, "vc-says", r["slug"])}" style="color:rgb(242,232,220);text-decoration:none">{e(loc_rec(r, loc)["phrase"])}</a></li>'
        for r in pub
    )
    cards_tools = "".join(
        f'<li style="margin:0"><a href="{url(loc, "tools", k)}" style="color:rgb(242,232,220);text-decoration:none">{e(pack["tools"][k]["h1"])}</a></li>'
        for k in TOOL_SLUGS
    )
    cards_art = "".join(
        f'<li style="margin:0"><a href="{url(loc, "articles", slug)}" style="color:rgb(242,232,220);text-decoration:none">{e(titles_loc[slug]["h1"])}</a></li>'
        for slug in ARTICLES
    )
    title = s["locale_landing_title"].replace("{lang}", lang)
    desc = s["locale_landing_desc"].replace("{lang}", lang)
    h1 = s["locale_landing_h1"].replace("{lang}", lang)
    lead = s["locale_landing_lead"]
    main = (
        f'<main><div style="max-width:1240px;margin:0 auto;padding:40px 24px 72px;display:flex;flex-direction:column;gap:28px">'
        f'<p class="vc-meta"><span class="vc-pill">{e(s["locale_partial_badge"])}</span></p>'
        f'<h1 style="margin:0;font-family:&quot;Instrument Serif&quot;,Georgia,serif;font-weight:400;font-size:clamp(40px,5vw,64px);line-height:1.05">{e(h1)}</h1>'
        f'<p style="margin:0;max-width:720px;color:rgb(207,197,186)">{e(lead)}</p>'
        f'<p style="margin:0;font-size:14px;color:rgb(140,131,120)">{e(s["locale_landing_ai_note"])}</p>'
        f'<section style="display:flex;flex-direction:column;gap:12px"><h2 style="margin:0;font-size:22px">{e(s["locale_landing_section_vcsays"])}</h2>'
        f'<p><a href="{url(loc, "vc-says")}">{e(s["nav_vc_says"])} →</a></p><ul style="margin:0;padding-left:18px;display:flex;flex-direction:column;gap:8px">{cards_vc}</ul></section>'
        f'<section style="display:flex;flex-direction:column;gap:12px"><h2 style="margin:0;font-size:22px">{e(s["locale_landing_section_tools"])}</h2>'
        f'<p><a href="{url(loc, "tools")}">{e(s["nav_tools"])} →</a></p><ul style="margin:0;padding-left:18px;display:flex;flex-direction:column;gap:8px">{cards_tools}</ul></section>'
        f'<section style="display:flex;flex-direction:column;gap:12px"><h2 style="margin:0;font-size:22px">{e(s["locale_landing_section_articles"])}</h2>'
        f'<ul style="margin:0;padding-left:18px;display:flex;flex-direction:column;gap:8px">{cards_art}</ul></section>'
        f'<section style="display:flex;flex-direction:column;gap:12px"><h2 style="margin:0;font-size:22px">{e(s["locale_landing_section_en"])}</h2>'
        f'<p style="margin:0;color:rgb(185,175,164)">{e(s["locale_landing_en_note"])}</p>'
        f'<p><a href="/">{e(s["lang_name_en"])} →</a></p></section>'
        f'{book_cta(t)}{disclaimer(t)}</div></main>'
    )
    # landing uses index.html under base(loc)
    path = f"{base(loc)}/index.html"
    return [B.write(path, staging_page(loc, t, title + " | The Fundraising Game", desc, hdr, footer, main,
                                       f' data-locale-landing="{loc}"', [], kind="landing"))]


# --------------------------------------------------------------------------- main
def build_all():
    data = merge_records()
    titles_en = B.article_titles()
    written = []
    for loc in LOCALES:
        t = jload(f"data/i18n/{loc}.json")
        pack = jload(f"data/locales/{loc}/tools.json")
        cs = jload(f"data/locales/{loc}/chrome_signup.json")
        recs = {r["id"]: r for r in data["records"]}
        phrases = {rid: recs[rid]["locales"][loc]["phrase"] for rid in data["priority_ids"]}
        header, footer = localized_chrome(loc, t, cs)
        titles_loc = article_meta(loc)
        written.append(B.write(f"{base(loc)}/assets/tools.locale.js", tools_js(loc, pack, phrases)))
        written.append(B.write(f"{base(loc)}/assets/vc-says.locale.js", vcsays_js(loc, t)))
        written.append(B.write(f"{base(loc)}/assets/site.locale.js", site_js(loc, cs)))
        if PUBLIC:
            written += build_landing(loc, t, pack, data, header, footer, titles_loc)
        written += build_vcsays(loc, t, pack, data, header, footer, titles_loc, titles_en)
        written += build_tools(loc, t, pack, phrases, header, footer, titles_loc, titles_en)
        written += build_articles(loc, t, header, footer, titles_loc)
    return written


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--public", action="store_true", help="Write indexable /{loc}/ trees (owner-approved publish)")
    args = ap.parse_args()
    if args.public:
        PUBLIC = True  # noqa: F841 — assigned for module callers; set below via globals
        globals()["PUBLIC"] = True
    w = build_all()
    mode = "PUBLIC" if PUBLIC else "staging"
    print(f"SK/CS/DE/PL {mode} build: {len(w)} files")
    for x in w:
        print("   ", x)
