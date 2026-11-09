#!/usr/bin/env node
/* Math/logic parity: EN assets/growth/tools.js + vc-says.js vs the generated staging locale builds
 * (_staging/locales/{loc}/assets/{tools,vc-says}.locale.js). Tiny stub DOM, no browser, no network.
 * Usage: node scripts/locale_tools_parity.js sk|cs   → prints JSON {checks:{name:{ok,detail}}, counts}
 * Invoked by scripts/test_locale_drafts.py. */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ROOT = path.resolve(__dirname, '..');
const LOC = process.argv[2] || 'sk';
const BCP = { sk: 'sk-SK', cs: 'cs-CZ' }[LOC];
const EN_TOOLS = fs.readFileSync(path.join(ROOT, 'assets/growth/tools.js'), 'utf8');
const LOC_TOOLS = fs.readFileSync(path.join(ROOT, `_staging/locales/${LOC}/assets/tools.locale.js`), 'utf8');
const EN_VCS = fs.readFileSync(path.join(ROOT, 'assets/growth/vc-says.js'), 'utf8');
const LOC_VCS = fs.readFileSync(path.join(ROOT, `_staging/locales/${LOC}/assets/vc-says.locale.js`), 'utf8');
const PACK = JSON.parse(fs.readFileSync(path.join(ROOT, `data/locales/${LOC}/tools.json`), 'utf8'));

class El {
  constructor(tag, id) { this.tagName = tag; this.id = id || ''; this.children = []; this._text = ''; this.value = ''; this.hidden = false; this.style = {}; this.dataset = {}; this.options = []; this.attrs = {}; this.listeners = {}; this.min = ''; this.max = ''; this.checked = false; }
  get textContent() { return this._text + this.children.map(c => (typeof c === 'string' ? c : c.textContent)).join(''); }
  set textContent(v) { this._text = String(v); this.children = []; }
  append(...n) { this.children.push(...n); }
  appendChild(n) { this.children.push(n); return n; }
  addEventListener(t, f) { (this.listeners[t] = this.listeners[t] || []).push(f); }
  click() { (this.listeners.click || []).forEach(f => f.call(this, {})); }
  getAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : null; }
  setAttribute(k, v) { this.attrs[k] = v; }
  hasAttribute(k) { return k in this.attrs; }
  querySelectorAll() { return []; }
  remove() {}
  walk(f) { f(this); this.children.forEach(c => { if (c instanceof El) c.walk(f); }); }
  find(pred) { let r = null; this.walk(n => { if (!r && pred(n)) r = n; }); return r; }
}

function env(ids, search, opts) {
  const els = {};
  ids.forEach(i => { els[i] = new El('div', i); });
  const all = () => { const out = []; Object.values(els).forEach(e => e.walk(n => out.push(n))); return out; };
  const document = {
    readyState: 'complete', documentElement: { lang: (opts && opts.lang) || 'en' },
    body: Object.assign(new El('body'), { dataset: {} }),
    getElementById: id => els[id] || null,
    querySelector: sel => (opts && opts.root && sel === '.tfg-vcsays' ? {} : null),
    querySelectorAll: sel => (sel === 'input[name="signal"]:checked' ? all().filter(n => n.tagName === 'input' && n.name === 'signal' && n.checked) : []),
    createElement: tag => new El(tag), createTextNode: t => t, addEventListener: () => {}, execCommand: () => true,
  };
  const window = { isSecureContext: false };
  const ctx = vm.createContext({ window, document, location: { search: search || '', pathname: '/t' }, navigator: {}, URLSearchParams, Intl, console, Number, JSON, Object, Math, String, Array });
  window.window = window;
  return { ctx, els, window };
}
function run(src, ids, setup, search, opts) { const E = env(ids, search, opts); if (setup) setup(E.els); vm.runInContext(src, E.ctx); return E; }

const parseEN = s => Number(String(s).replace(/[^0-9.\-]/g, ''));
const parseLOC = s => Number(String(s).replace(/[^0-9,\-]/g, '').replace(',', '.'));
const checks = {}; const counts = { comparisons: 0 };
function check(name, ok, detail) { checks[name] = { ok: !!ok, detail: ok ? undefined : detail }; }

/* ---- 1. Signal decoder: all 256 subsets ---- */
{
  const ids = ['signals-list', 'signals-calculate', 'signal-status', 'signal-desc', 'signal-next', 'signal-count', 'signal-meter', 'signal-related'];
  const enStatus = ['Insufficient signal', 'Likely structural mismatch', 'Meaningful process signals', 'Early signs of engagement', 'Weak or declining momentum'];
  const R = PACK.tools['investor-signal-decoder'].results;
  const locStatus = [R.insufficient.status, R.mismatch.status, R.meaningful.status, R.early.status, R.weak.status];
  const keys = ['next', 'partner', 'diligence', 'champion', 'question', 'polite', 'noresponse', 'wrong'];
  const bad = []; let labelsOk = true;
  for (let mask = 0; mask < 256; mask++) {
    const out = [EN_TOOLS, LOC_TOOLS].map((src, li) => {
      const E = run(src, ids);
      const boxes = []; E.els['signals-list'].walk(n => { if (n.tagName === 'input') boxes.push(n); });
      if (li === 1 && mask === 0) labelsOk = E.els['signals-list'].children.map(l => l.textContent).every((t, i) => t === PACK.tools['investor-signal-decoder'].signalItems[keys[i]]);
      boxes.forEach((b, i) => { b.checked = !!(mask & (1 << i)); });
      E.els['signals-calculate'].click();
      const rel = E.els['signal-related'].find(n => n.tagName === 'a');
      return { status: E.els['signal-status'].textContent, width: E.els['signal-meter'].style.width, count: parseInt(E.els['signal-count'].textContent, 10), rel: rel ? rel.href.split('/').pop() : null };
    });
    counts.comparisons++;
    const b0 = enStatus.indexOf(out[0].status), b1 = locStatus.indexOf(out[1].status);
    const relEN = out[0].rel === 'vc-says' ? 'vc-says' : out[0].rel; const relLOC = out[1].rel;
    if (b0 < 0 || b0 !== b1 || out[0].width !== out[1].width || out[0].count !== out[1].count || relEN !== relLOC) bad.push({ mask, en: out[0], loc: out[1] });
  }
  check('decoder: 256 checkbox combinations → same result bucket, meter width, count, related entry', bad.length === 0, bad.slice(0, 3));
  check('decoder: rendered checkbox labels are the pack signalItems (8)', labelsOk);
}

/* ---- 2. Pipeline ---- */
{
  const ids = ['pipeline-calculate', 'pipe-leads', 'pipe-r1', 'pipe-r2', 'pipe-r3', 'pipe-r4', 'pipe-meetings', 'pipe-deep', 'pipe-terms', 'pipe-closes', 'pipe-close-rate', 'pipe-needed', 'pipe-note'];
  const cases = [[120, 25, 30, 20, 60], [0, 25, 30, 20, 60], [10000, 100, 100, 100, 100], [37, 12.5, 33.3, 7.7, 49.9], [5, 0, 0, 0, 0], [99999, 150, -5, 20.25, 60], [1234, 1.1, 2.2, 3.3, 4.4], [800, 33.33, 66.67, 15.55, 80.05]];
  const bad = []; let inputsUnchanged = true;
  const P = PACK.tools['fundraising-pipeline-calculator'];
  for (const c of cases) {
    const vals = ['pipe-leads', 'pipe-r1', 'pipe-r2', 'pipe-r3', 'pipe-r4'];
    const setup = els => { vals.forEach((k, i) => { els[k].value = String(c[i]); els[k].min = '0'; els[k].max = k === 'pipe-leads' ? '10000' : '100'; }); };
    const [en, lo] = [EN_TOOLS, LOC_TOOLS].map(src => run(src, ids, setup));
    vals.forEach((k, i) => { if (lo.els[k].value !== String(c[i])) inputsUnchanged = false; });
    for (const k of ['pipe-meetings', 'pipe-deep', 'pipe-terms', 'pipe-closes', 'pipe-close-rate', 'pipe-needed']) {
      counts.comparisons++;
      const a = parseEN(en.els[k].textContent), b = parseLOC(lo.els[k].textContent);
      if (!(a === b)) bad.push({ c, k, en: en.els[k].textContent, loc: lo.els[k].textContent });
    }
    const enLow = en.els['pipe-note'].textContent.startsWith('Under these'), loLow = lo.els['pipe-note'].textContent === P.note_low;
    if (enLow !== loLow) bad.push({ c, k: 'pipe-note' });
  }
  check('pipeline: identical numbers (meetings, deep, term sheets, closes, close rate, contacts needed) across 8 input sets incl. clamping', bad.length === 0, bad.slice(0, 4));
  check('pipeline: numeric helpers do not modify input values', inputsUnchanged);
}

/* ---- 3. Runway ---- */
{
  const ids = ['runway-calculate', 'run-cash', 'run-expenses', 'run-revenue', 'run-months', 'run-onetime', 'run-buffer', 'run-pre', 'run-net', 'run-existing', 'run-raise', 'run-dilution', 'run-post', 'run-pool', 'run-note'];
  const vals = ['run-cash', 'run-expenses', 'run-revenue', 'run-months', 'run-onetime', 'run-buffer', 'run-pre'];
  const mins = { 'run-months': '1' }, maxs = { 'run-months': '60', 'run-buffer': '100' };
  const cases = [[120000, 45000, 10000, 20, 40000, 15, 4000000], [0, 0, 0, 1, 0, 0, 0], [500000, 20000, 30000, 18, 0, 10, 3000000],
    [1e6, 123456.78, 9876.5, 61, 55555, 150, 12345678], [75000.5, 33333.33, 0, 12, 1000, 7.5, -100], [1, 2, 0, 0, 0, 0, 1]];
  const bad = []; let inputsUnchanged = true; let noBurnOk = true;
  const Rn = PACK.tools['runway-raise-calculator'];
  for (const c of cases) {
    const setup = els => vals.forEach((k, i) => { els[k].value = String(c[i]); els[k].min = mins[k] || '0'; els[k].max = maxs[k] || ''; });
    const [en, lo] = [EN_TOOLS, LOC_TOOLS].map(src => run(src, ids, setup));
    vals.forEach((k, i) => { if (lo.els[k].value !== String(c[i])) inputsUnchanged = false; });
    for (const k of ['run-net', 'run-existing', 'run-raise', 'run-dilution', 'run-post', 'run-pool']) {
      counts.comparisons++;
      const et = en.els[k].textContent, lt = lo.els[k].textContent;
      if (et === 'No net burn') { if (lt !== Rn.no_net_burn) noBurnOk = false; continue; }
      if (!(parseEN(et) === parseLOC(lt))) bad.push({ c, k, en: et, loc: lt });
    }
    const enNoPre = en.els['run-note'].textContent.startsWith('Enter a positive'), loNoPre = lo.els['run-note'].textContent === Rn.note_no_pre;
    if (enNoPre !== loNoPre) bad.push({ c, k: 'run-note' });
  }
  check('runway: identical net burn, runway, raise, dilution, post-money, buffer across 6 input sets incl. clamping/edge cases', bad.length === 0, bad.slice(0, 4));
  check('runway: "no net burn" branch maps to localized label', noBurnOk);
  check('runway: numeric helpers do not modify input values', inputsUnchanged);
}

/* ---- 4. Follow-up builder ---- */
{
  const ids = ['followup-calculate', 'follow-type', 'follow-company', 'follow-name', 'follow-topic', 'follow-progress', 'follow-milestone', 'follow-next', 'follow-output', 'follow-copy', 'follow-signal-note'];
  const types = ['meeting', 'tooearly', 'quiet', 'update', 'notfit', 'nolead', 'cold'];
  const filled = { 'follow-company': 'AcmeX', 'follow-name': 'Jana', 'follow-topic': 'TOPICX', 'follow-progress': 'PROGX', 'follow-milestone': 'MILEX', 'follow-next': 'NEXTX' };
  const bad = []; const keep = ['[Company]', '[Investor name]', '[Your name]'];
  for (const t of types) for (const data of [filled, {}]) {
    const setup = els => { els['follow-type'].value = t; els['follow-type'].options = types.map(v => ({ value: v })); Object.entries(data).forEach(([k, v]) => { els[k].value = v; }); };
    const [en, lo] = [EN_TOOLS, LOC_TOOLS].map(src => run(src, ids, setup).els['follow-output'].value);
    counts.comparisons++;
    for (const v of Object.values(filled)) { const ce = en.split(v).length, cl = lo.split(v).length; if (ce !== cl) bad.push({ t, v, en: ce - 1, loc: cl - 1 }); }
    if (!Object.keys(data).length) for (const p of keep) if (en.includes(p) !== lo.includes(p)) bad.push({ t, p });
    if (!lo.includes('[Your name]')) bad.push({ t, missing: '[Your name]' });
  }
  check('follow-up: every scenario substitutes the same user fields the same number of times as EN; placeholders preserved when empty', bad.length === 0, bad.slice(0, 5));
  const expected = { 'too-early': 'tooearly', 'not-right-fit': 'notfit', 'keep-in-touch': 'update', 'circle-back-next-quarter': 'update', 'send-deck': 'meeting', 'second-meeting': 'meeting', 'partner-introduction': 'meeting', 'need-more-traction': 'tooearly', 'no-lead-investor': 'nolead', 'investor-ghosting': 'quiet' };
  const badSig = [];
  for (const [id, tpl] of Object.entries(expected)) {
    const E = run(LOC_TOOLS, ids, els => { els['follow-type'].value = 'meeting'; els['follow-type'].options = types.map(v => ({ value: v })); els['follow-signal-note'].hidden = true; }, '?signal=' + id);
    const link = E.els['follow-signal-note'].find(n => n.tagName === 'a');
    if (E.els['follow-type'].value !== tpl || !link || link.href !== `/_staging/locales/${LOC}/vc-says/${id}`) badSig.push({ id, got: E.els['follow-type'].value, link: link && link.href });
  }
  check('follow-up: ?signal=ID preselects the same scenario as EN and links the staging entry (10)', badSig.length === 0, badSig);
}

/* ---- 5. Display formatting uses the locale ---- */
{
  const E = run(LOC_TOOLS, ['runway-calculate', 'run-cash', 'run-expenses', 'run-revenue', 'run-months', 'run-onetime', 'run-buffer', 'run-pre', 'run-net', 'run-existing', 'run-raise', 'run-dilution', 'run-post', 'run-pool', 'run-note'],
    els => { const v = { 'run-cash': 120000, 'run-expenses': 45000, 'run-revenue': 10000, 'run-months': 20, 'run-onetime': 40000, 'run-buffer': 15, 'run-pre': 4000000 }; Object.entries(v).forEach(([k, x]) => { els[k].value = String(x); els[k].min = '0'; }); });
  const raise = E.els['run-raise'].textContent, dil = E.els['run-dilution'].textContent;
  const expRaise = new Intl.NumberFormat(BCP, { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(713000);
  check(`format: currency rendered with Intl ${BCP} (EUR, unchanged currency)`, raise === expRaise, { raise, expRaise });
  check('format: percent rendered as "x,y %" (decimal comma)', /^\d+,\d %$/.test(dil), dil);
}

/* ---- 6. VC Says mini-decoder ranking parity ---- */
{
  const hub = fs.readFileSync(path.join(ROOT, `_staging/locales/${LOC}/vc-says/index.html`), 'utf8');
  const idx = hub.match(/<script type="application\/json" id="vc-says-index">([\s\S]*?)<\/script>/)[1];
  const apis = [EN_VCS, LOC_VCS].map((src, i) => { const E = run(src, ['vc-says-index'], els => { els['vc-says-index'].textContent = idx; }, '', { root: true, lang: i ? LOC : 'en' }); return E.window.TFGVcSays; });
  const ids = JSON.parse(idx).map(r => r.id);
  const bad = [];
  for (const category of ids) for (const stage of ['', 'pre-seed', 'seed', 'series-a']) for (const next of ['', 'none', 'vague', 'specific', 'materials', 'internal', 'otherfund']) for (const elapsed of ['', 'short', 'mid', 'long', 'missed']) {
    const st = { category, stage, next, elapsed };
    const [a, b] = apis.map(api => { const r = api.decode(st); return r.ranked.map(x => x.it.kind + ':' + x.score.toFixed(3)).join('|') + '#' + r.fired.map(f => f.id).join(','); });
    counts.comparisons++;
    if (a !== b) bad.push({ st, a, b });
  }
  check('mini decoder: identical ranking + fired rules for every category×stage×next×elapsed combination', bad.length === 0, bad.slice(0, 3));
  check('mini decoder: rule ids/weights unchanged', JSON.stringify(apis[0].rules.map(r => [r.id, r.add])) === JSON.stringify(apis[1].rules.map(r => [r.id, r.add])));
  check(`mini decoder: formatNumber(1200.5, "${LOC}") uses locale`, apis[1].formatNumber(1200.5, LOC) === new Intl.NumberFormat(BCP).format(1200.5), apis[1].formatNumber(1200.5, LOC));
}

process.stdout.write(JSON.stringify({ locale: LOC, checks, counts }));
