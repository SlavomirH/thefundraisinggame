/* VC Says library — search, filters, mini decoder, copy.
 * Privacy: everything runs locally. This file makes NO network requests and never
 * sends typed/pasted text anywhere. Analytics hooks only call window.tfgTrack if the
 * site has defined it, and only with category/ID properties (never raw text).
 */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var root = document.querySelector('.tfg-vcsays');
  if (!root) return;
  var LOCALE = document.documentElement.lang || 'en';

  /* ---------- analytics (opt-in hook only) ---------- */
  function track(name, props) {
    if (typeof window.tfgTrack !== 'function') return;
    try {
      var p = { locale: LOCALE, source_path: location.pathname };
      for (var k in props) if (Object.prototype.hasOwnProperty.call(props, k)) p[k] = props[k];
      window.tfgTrack(name, p);
    } catch (e) { /* never break the page for analytics */ }
  }

  /* ---------- helpers ---------- */
  var BCP47 = { en: 'en-US', sk: 'sk-SK', cs: 'cs-CZ', de: 'de-DE', pl: 'pl-PL' };
  /* Display-only number formatting. Never use the output for calculations. */
  function formatNumber(n, locale, opts) {
    var v = Number(n);
    if (!Number.isFinite(v)) v = 0;
    try { return new Intl.NumberFormat(BCP47[locale] || locale || 'en-US', opts || {}).format(v); }
    catch (e) { return String(v); }
  }
  function norm(s) {
    return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
      .replace(/[’'`´]/g, '').replace(/[^a-z0-9ßł ]+/g, ' ').replace(/\s+/g, ' ').trim();
  }
  function readIndex() {
    var el = $('vc-says-index');
    if (!el) return [];
    try { return JSON.parse(el.textContent); } catch (e) { return []; }
  }
  var INDEX = readIndex();
  var BY_ID = {};
  INDEX.forEach(function (r) { BY_ID[r.id] = r; r._hay = norm([r.phrase, r.shortAnswer, (r.synonyms || []).join(' '), (r.topicTags || []).join(' '), (r.localePhrases || []).join(' ')].join(' ')); });

  function copyText(text, statusEl, okMsg, failMsg, onOk) {
    function ok() { if (statusEl) statusEl.textContent = okMsg; if (onOk) onOk(); }
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.top = '-9999px';
      document.body.appendChild(ta); ta.select();
      try { if (document.execCommand('copy')) ok(); else if (statusEl) statusEl.textContent = failMsg; }
      catch (e) { if (statusEl) statusEl.textContent = failMsg; }
      ta.remove();
    }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(ok, fallback);
    else fallback();
  }

  /* ---------- hub: search + filters ---------- */
  function initHub() {
    var list = $('vc-list');
    if (!list) return;
    var cards = Array.prototype.slice.call(list.querySelectorAll('[data-vc-id]'));
    var q = $('vc-q'), clear = $('vc-q-clear'), reset = $('vc-reset'), count = $('vc-count'), empty = $('vc-empty');
    var filters = { stage: $('vc-f-stage'), cls: $('vc-f-class'), topic: $('vc-f-topic'), context: $('vc-f-context') };
    var countTpl = count ? (count.getAttribute('data-template') || '{n}') : '{n}';
    var searchTracked = false;

    function apply(source) {
      var terms = norm(q && q.value).split(' ').filter(Boolean);
      var shown = 0;
      cards.forEach(function (c) {
        var rec = BY_ID[c.getAttribute('data-vc-id')] || {};
        var hay = rec._hay || norm(c.textContent);
        var ok = terms.every(function (t) { return hay.indexOf(t) !== -1; });
        if (ok && filters.stage && filters.stage.value) ok = (' ' + c.getAttribute('data-stage') + ' ').indexOf(' ' + filters.stage.value + ' ') !== -1;
        if (ok && filters.cls && filters.cls.value) ok = c.getAttribute('data-class') === filters.cls.value;
        if (ok && filters.topic && filters.topic.value) ok = (' ' + c.getAttribute('data-topic') + ' ').indexOf(' ' + filters.topic.value + ' ') !== -1;
        if (ok && filters.context && filters.context.value) ok = (' ' + c.getAttribute('data-context') + ' ').indexOf(' ' + filters.context.value + ' ') !== -1;
        c.hidden = !ok;
        if (ok) shown++;
      });
      if (count) count.textContent = countTpl.replace('{n}', formatNumber(shown, LOCALE));
      if (empty) empty.hidden = shown !== 0;
      if (clear) clear.hidden = !(q && q.value);
      if (source === 'search' && !searchTracked && terms.length) { searchTracked = true; track('vc_says_search_used', { result_count: shown }); }
      if (source === 'filter') track('vc_says_filter_used', {
        stage: filters.stage ? filters.stage.value || 'all' : 'all',
        signal_class: filters.cls ? filters.cls.value || 'all' : 'all',
        topic: filters.topic ? filters.topic.value || 'all' : 'all',
        context: filters.context ? filters.context.value || 'all' : 'all', result_count: shown });
    }
    if (q) q.addEventListener('input', function () { apply('search'); });
    if (q) q.addEventListener('keydown', function (e) { if (e.key === 'Escape') { q.value = ''; apply('search'); } });
    if (clear) clear.addEventListener('click', function () { q.value = ''; apply('search'); q.focus(); });
    Object.keys(filters).forEach(function (k) { if (filters[k]) filters[k].addEventListener('change', function () { apply('filter'); }); });
    if (reset) reset.addEventListener('click', function () {
      if (q) q.value = '';
      Object.keys(filters).forEach(function (k) { if (filters[k]) filters[k].value = ''; });
      apply('reset');
      if (q) q.focus();
    });
    var form = $('vc-search-form');
    if (form) form.addEventListener('submit', function (e) { e.preventDefault(); apply('search'); });
    apply('init');
    track('vc_says_hub_view', {});
  }

  /* ---------- mini decoder: transparent editorial rules ---------- */
  /* Each interpretation has a "kind": interest | condition | mismatch | pass | noise.
     Rules add or subtract points per kind. Ties keep editorial order. No probabilities. */
  var RULES = [
    { id: 'R1', when: function (s) { return s.next === 'specific'; }, add: { interest: 3, condition: 2, pass: -2 }, text: 'A specific date or meeting was offered → genuine interest and conditional readings move up; polite-pass moves down.' },
    { id: 'R2', when: function (s) { return s.next === 'materials'; }, add: { interest: 2, condition: 2, pass: -1 }, text: 'They requested specific materials → interest/conditional readings move up.' },
    { id: 'R3', when: function (s) { return s.next === 'internal'; }, add: { interest: 3, noise: 1, pass: -2 }, text: 'They brought in another partner from their own fund → process/interest readings move up.' },
    { id: 'R4', when: function (s) { return s.next === 'otherfund'; }, add: { mismatch: 3, pass: 1, interest: -1 }, text: 'They suggested a different fund → fit/mandate mismatch moves up.' },
    { id: 'R5', when: function (s) { return s.next === 'none'; }, add: { pass: 2, interest: -1 }, text: 'No next step at all → polite-pass reading moves up.' },
    { id: 'R6', when: function (s) { return s.next === 'vague'; }, add: { pass: 1, condition: 1 }, text: 'Only a vague next step (“keep us posted”) → conditional and polite-pass readings move up slightly.' },
    { id: 'R7', when: function (s) { return s.elapsed === 'long' && (s.next === 'none' || s.next === 'vague'); }, add: { pass: 2 }, text: 'More than three weeks with no concrete next step → polite-pass moves up.' },
    { id: 'R8', when: function (s) { return s.elapsed === 'missed'; }, add: { noise: 2, pass: 1 }, text: 'A promised date has passed → stalled-process/bandwidth and polite-pass readings move up.' },
    { id: 'R9', when: function (s) { return s.elapsed === 'short'; }, add: { noise: 1 }, text: 'Less than a week has passed → too soon to read much into timing; logistics readings move up slightly.' },
    { id: 'R10', when: function (s) { return s.stage === 'pre-seed' && (s.category === 'too-early' || s.category === 'need-more-traction'); }, add: { mismatch: 1 }, text: 'Pre-seed + “too early”/“traction” → many funds start later, so stage mismatch moves up slightly.' }
  ];
  var RANK_LABELS = ['Most consistent with your answers', 'Also plausible', 'Less consistent, but still possible'];

  function decode(state) {
    var rec = BY_ID[state.category];
    if (!rec) return null;
    var fired = RULES.filter(function (r) { return r.when(state); });
    var ranked = (rec.interpretations || []).map(function (it, i) {
      var score = -i * 0.1; // editorial order breaks ties
      fired.forEach(function (r) { score += (r.add[it.kind] || 0); });
      return { it: it, score: score, order: i };
    }).sort(function (a, b) { return b.score - a.score || a.order - b.order; });
    return { rec: rec, ranked: ranked, fired: fired };
  }

  function guessCategory(text) {
    var t = norm(text);
    if (!t) return null;
    var words = t.split(' ').filter(function (w) { return w.length > 2; });
    var best = null, bestScore = 0;
    INDEX.forEach(function (r) {
      var phrases = [r.phrase].concat(r.synonyms || [], r.localePhrases || []);
      var score = 0;
      phrases.forEach(function (p) {
        var pn = norm(p);
        if (pn && t.indexOf(pn) !== -1) score += 10;
        pn.split(' ').forEach(function (w) { if (w.length > 3 && words.indexOf(w) !== -1) score += 1; });
      });
      if (score > bestScore) { bestScore = score; best = r.id; }
    });
    return bestScore >= 2 ? best : null;
  }

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

  function initDecoder() {
    var btn = $('vc-dec-run');
    if (!btn) return;
    var out = $('vc-dec-out'), paste = $('vc-dec-paste'), hint = $('vc-dec-paste-hint'), cat = $('vc-dec-category');
    var suggestedId = null;
    function setHintForSuggestion(id) {
      if (!hint) return;
      if (id && BY_ID[id]) {
        hint.textContent = 'Closest library match: “' + BY_ID[id].phrase + '”. Selected below — change the category if it doesn’t fit.';
      } else if (paste && paste.value) {
        hint.textContent = 'No close match — choose the closest category below.';
      } else {
        hint.textContent = '';
      }
    }
    function syncHintWithManualChoice() {
      if (!hint || !cat) return;
      if (!suggestedId) return; // nothing auto-suggested yet
      if (cat.value === suggestedId) {
        setHintForSuggestion(suggestedId);
      } else if (cat.value && BY_ID[cat.value]) {
        hint.textContent = 'Using “' + BY_ID[cat.value].phrase + '” (you changed the suggested match).';
      } else {
        hint.textContent = 'Choose the closest category below.';
      }
    }
    if (paste) paste.addEventListener('input', function () {
      var id = guessCategory(paste.value);   // local only — text is never sent or tracked
      suggestedId = id;
      if (id && cat) cat.value = id;
      setHintForSuggestion(id);
    });
    if (cat) cat.addEventListener('change', syncHintWithManualChoice);
    btn.addEventListener('click', function () {
      var state = { stage: $('vc-dec-stage').value, category: cat.value, next: $('vc-dec-next').value, elapsed: $('vc-dec-elapsed').value };
      var res = decode(state);
      out.textContent = '';
      if (!res) { out.appendChild(el('p', 'vc-why', 'Choose what the investor said or did to see plausible interpretations.')); return; }
      out.appendChild(el('h3', null, 'Plausible interpretations of “' + res.rec.phrase + '”'));
      var ol = el('ol');
      res.ranked.forEach(function (r, i) {
        var li = el('li');
        li.appendChild(el('span', 'vc-rank', RANK_LABELS[Math.min(i, RANK_LABELS.length - 1)]));
        li.appendChild(document.createTextNode(r.it.possibility));
        ol.appendChild(li);
      });
      out.appendChild(ol);
      var why = el('p', 'vc-why');
      why.textContent = res.fired.length ? 'Rules applied: ' + res.fired.map(function (r) { return r.id; }).join(', ') + '. ' + res.fired.map(function (r) { return r.text; }).join(' ')
        : 'No rules applied — interpretations shown in editorial order.';
      out.appendChild(why);
      out.appendChild(el('h3', null, 'A question that would clarify it'));
      out.appendChild(el('p', 'vc-ask', res.rec.clarifyingQuestion));
      var a = el('a', 'vc-btn secondary', 'Read the full entry and reply template →');
      a.href = res.rec.url;
      out.appendChild(a);
      out.appendChild(el('p', 'vc-why', 'This is a conversation aid based on editorial rules, not a prediction of the investor’s decision. No probabilities are calculated.'));
      track('vc_says_decoder_used', { signal_id: res.rec.id, signal_class: res.rec.signalClass, stage: state.stage || 'unspecified', next_step: state.next || 'unspecified', elapsed: state.elapsed || 'unspecified' });
    });
  }

  /* ---------- detail page: copy + view tracking ---------- */
  function initDetail() {
    var page = document.body.getAttribute('data-vc-signal');
    if (page) track('vc_says_entry_view', { signal_id: page, signal_class: document.body.getAttribute('data-vc-class') || '' });
    var copyBtn = $('vc-copy');
    if (copyBtn) copyBtn.addEventListener('click', function () {
      var ta = $('vc-reply'), st = $('vc-copy-status');
      copyText(ta.value, st, copyBtn.getAttribute('data-ok') || 'Copied ✓', copyBtn.getAttribute('data-fail') || 'Copy failed — select the text and copy manually',
        function () { track('vc_says_reply_copied', { signal_id: page || '' }); });  // never the text itself
    });
    var resetBtn = $('vc-reply-reset');
    if (resetBtn) resetBtn.addEventListener('click', function () { var ta = $('vc-reply'); ta.value = ta.defaultValue; ta.focus(); });
  }

  /* ---------- related tool / CTA clicks ---------- */
  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a[data-vc-tool],a[data-signup-cta]') : null;
    if (!a) return;
    if (a.hasAttribute('data-vc-tool')) track('vc_says_related_tool_opened', { tool_slug: a.getAttribute('data-vc-tool'), signal_id: document.body.getAttribute('data-vc-signal') || '' });
    else track('signup_cta_clicked', { signal_id: document.body.getAttribute('data-vc-signal') || '' });
  });

  window.TFGVcSays = { formatNumber: formatNumber, decode: decode, rules: RULES };
  initHub(); initDecoder(); initDetail();
})();
