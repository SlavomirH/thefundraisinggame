#!/usr/bin/env node
/* Behavioural checks for assets/growth/tools.js and assets/growth/vc-says.js using a tiny stub DOM
 * (no browser automation, no network). Invoked by scripts/test_vc_says.py. Prints JSON results. */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const ROOT = path.resolve(__dirname, '..');

class El {
  constructor(tag, id) { this.tagName = tag; this.id = id || ''; this.children = []; this._text = ''; this.value = ''; this.hidden = false; this.style = {}; this.dataset = {}; this.options = []; this.attrs = {}; this.listeners = {}; }
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
  find(pred) { if (pred(this)) return this; for (const c of this.children) if (c instanceof El) { const r = c.find(pred); if (r) return r; } return null; }
}

function makeEnv(ids, search, extra) {
  const els = {};
  ids.forEach(i => { els[i] = new El('div', i); });
  const document = {
    readyState: 'complete',
    documentElement: { lang: 'en' },
    body: Object.assign(new El('body'), { dataset: {} }),
    getElementById: id => els[id] || null,
    querySelector: sel => (extra && extra.querySelector ? extra.querySelector(sel) : null),
    querySelectorAll: () => [],
    createElement: tag => new El(tag),
    createTextNode: t => t,
    addEventListener: () => {},
    execCommand: () => true,
  };
  const tracked = [];
  const window = { isSecureContext: false, tfgTrack: (n, p) => tracked.push([n, p]) };
  const ctx = { window, document, location: { search: search || '', pathname: '/test' }, navigator: {}, URLSearchParams, Intl, console, Number, JSON, Object, Math, String, Array };
  window.window = window;
  return { ctx: vm.createContext(ctx), els, tracked, window, document };
}

const results = {};

/* ---- Follow-up Builder ?signal= prefill ---- */
function followup(search) {
  const ids = ['followup-calculate', 'follow-type', 'follow-company', 'follow-name', 'follow-topic', 'follow-progress', 'follow-milestone', 'follow-next', 'follow-output', 'follow-copy', 'follow-signal-note'];
  const env = makeEnv(ids, search);
  const sel = env.els['follow-type'];
  sel.value = 'meeting';
  sel.options = ['meeting', 'tooearly', 'quiet', 'update', 'notfit', 'nolead', 'cold'].map(v => ({ value: v }));
  env.els['follow-signal-note'].hidden = true;
  vm.runInContext(fs.readFileSync(path.join(ROOT, 'assets/growth/tools.js'), 'utf8'), env.ctx);
  const note = env.els['follow-signal-note'];
  const link = note.find(n => n.tagName === 'a');
  return { type: sel.value, noteHidden: note.hidden, link: link ? link.href : null, output: env.els['follow-output'].value };
}
const expected = { 'too-early': 'tooearly', 'not-right-fit': 'notfit', 'keep-in-touch': 'update', 'circle-back-next-quarter': 'update', 'send-deck': 'meeting', 'second-meeting': 'meeting', 'partner-introduction': 'meeting', 'need-more-traction': 'tooearly', 'no-lead-investor': 'nolead', 'investor-ghosting': 'quiet' };
results.followup = {};
for (const [id, tpl] of Object.entries(expected)) {
  const r = followup('?signal=' + id);
  results.followup[id] = { ok: r.type === tpl && !r.noteHidden && r.link === '/vc-says/' + id && r.output.includes('Subject:'), got: r.type, link: r.link };
}
const bogus = followup('?signal=<script>alert(1)</script>');
results.followup_unknown_ignored = bogus.type === 'meeting' && bogus.noteHidden === true;
const none = followup('');
results.followup_no_param_default = none.type === 'meeting' && none.noteHidden === true;

/* ---- vc-says.js decoder rules ---- */
const hub = fs.readFileSync(path.join(ROOT, 'vc-says.html'), 'utf8');
const m = hub.match(/<script type="application\/json" id="vc-says-index">([\s\S]*?)<\/script>/);
const env = makeEnv(['vc-says-index'], '', { querySelector: s => (s === '.tfg-vcsays' ? {} : null) });
env.els['vc-says-index'].textContent = m ? m[1] : '[]';
vm.runInContext(fs.readFileSync(path.join(ROOT, 'assets/growth/vc-says.js'), 'utf8'), env.ctx);
const api = env.window.TFGVcSays;
const top = st => { const r = api.decode(st); return r ? r.ranked[0].it.kind : null; };
results.decoder = {
  too_early_none_long_is_pass: top({ category: 'too-early', next: 'none', elapsed: 'long', stage: 'seed' }) === 'pass',
  too_early_specific_is_condition: top({ category: 'too-early', next: 'specific', elapsed: 'short', stage: 'seed' }) === 'condition',
  not_fit_otherfund_is_mismatch: top({ category: 'not-right-fit', next: 'otherfund', elapsed: '', stage: '' }) === 'mismatch',
  partner_internal_is_interest: top({ category: 'partner-introduction', next: 'internal', elapsed: 'short', stage: 'seed' }) === 'interest',
  unknown_category_null: api.decode({ category: 'nope' }) === null,
  no_probability_output: !/%/.test(JSON.stringify(api.rules.map(r => r.text))),
  rule_ids: api.rules.map(r => r.id),
};
results.formatNumber = { en: api.formatNumber(1200.5, 'en'), sk: api.formatNumber(1200.5, 'sk'), de: api.formatNumber(1200.5, 'de') };
results.tracked_events = env.tracked.map(t => t[0]);
process.stdout.write(JSON.stringify(results));
