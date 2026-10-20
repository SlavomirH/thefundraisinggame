/* The Fundraising Game: early-access signup (Bluefox) */
(function () {
  var LIST_URL = 'https://api.bluefox.email/v1/subscriber-lists/6960f7e0cfa080251b241006';
  var CAPTCHA_URL = 'https://api.bluefox.email/v1/captcha';

  function el(tag, attrs, html) {
    var e = document.createElement(tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (html) e.innerHTML = html;
    return e;
  }

  function setup(form, idx) {
    var dark = form.getAttribute('data-theme') === 'dark';
    var probe = null;
    var btn = form.querySelector('button[type="submit"]');
    var btnHtml = btn ? btn.innerHTML : '';

    var wrap = el('div', { class: 'tfg-captcha', style: 'display:flex;flex-direction:column;gap:8px;flex-basis:100%' });
    var row = el('div', { style: 'display:flex;align-items:center;gap:10px;flex-wrap:wrap' });
    var img = el('div', { class: 'tfg-captcha-img', 'aria-hidden': 'true', style: 'min-height:50px;min-width:150px;background:#fff;border-radius:10px;display:flex;align-items:center;justify-content:center;overflow:hidden;border:1px solid rgba(18,20,28,0.15)' }, '<span style="font-size:13px;color:#5C564F">Loading…</span>');
    var refresh = el('button', { type: 'button', 'aria-label': 'Load a new code', style: 'min-height:44px;padding:0 14px;border-radius:999px;border:1px solid rgba(18,20,28,0.25);background:transparent;color:#12141C;font:inherit;font-size:14px;cursor:pointer' }, 'New code');
    row.appendChild(img); row.appendChild(refresh);
    var id = 'tfg-captcha-' + idx;
    var label = el('label', { for: id, style: 'font-size:14px;font-weight:600;color:#12141C' }, 'Type the characters shown');
    var input = el('input', { id: id, name: 'captchaText', type: 'text', required: '', autocomplete: 'off', placeholder: 'Code', style: 'min-height:54px;padding:0 18px;border-radius:14px;border:1px solid rgba(18,20,28,0.25);background:#FFFFFF;color:#12141C;font:inherit;font-size:16px' });
    wrap.appendChild(label); wrap.appendChild(row); wrap.appendChild(input);
    var msg = el('p', { role: 'alert', style: 'display:none;margin:0;font-size:14px;color:#B23A1E;flex-basis:100%' });

    if (btn) { btn.parentNode.insertBefore(wrap, btn); btn.parentNode.insertBefore(msg, btn); }
    else form.appendChild(wrap);

    function load() {
      img.innerHTML = '<span style="font-size:13px;color:#5C564F">Loading…</span>';
      fetch(CAPTCHA_URL).then(function (r) { return r.json(); }).then(function (d) {
        img.innerHTML = d.result.data; probe = d.result.probe; input.value = '';
      }).catch(function () { img.innerHTML = '<span style="font-size:13px;color:#B23A1E">Could not load code</span>'; });
    }
    refresh.addEventListener('click', load);
    load();

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      msg.style.display = 'none';
      var email = form.querySelector('input[name="email"]').value.trim();
      if (btn) { btn.disabled = true; btn.innerHTML = 'Sending…'; }
      fetch(LIST_URL, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, captchaText: input.value.trim(), captchaProbe: probe })
      }).then(function (r) {
        if (r.ok) {
          var box = el('div', { role: 'status', style: 'display:flex;flex-direction:column;gap:10px' },
            '<h3 style="margin:0;font-family:\'Instrument Serif\',Georgia,serif;font-weight:400;font-size:34px;line-height:1.1;color:#12141C">You’re on the list.</h3>' +
            '<p style="margin:0;color:#4A453F">Check your inbox to confirm. The bonus chapter is on its way.</p>');
          form.parentNode.replaceChild(box, form);
          return;
        }
        return r.json().catch(function () { return {}; }).then(function (d) {
          throw new Error((d && d.error && d.error.message) || 'Something went wrong. Please try again.');
        });
      }).catch(function (err) {
        msg.textContent = err.message === 'Failed to fetch' ? 'Network error. Please check your connection and try again.' : err.message;
        msg.style.display = 'block';
        if (btn) { btn.disabled = false; btn.innerHTML = btnHtml; }
        load();
      });
    });
  }

  function init() {
    var forms = document.querySelectorAll('form[data-signup]');
    for (var i = 0; i < forms.length; i++) setup(forms[i], i);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();

/* Google Analytics 4 (G-HKGBHJZMNC) with cookie consent (Consent Mode v2, basic) */
(function () {
  var GA_ID = 'G-HKGBHJZMNC';
  var KEY = 'tfg_cookie_consent';
  var loaded = false;

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  gtag('consent', 'default', {
    ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied',
    analytics_storage: 'denied', wait_for_update: 500
  });

  function getChoice() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function setChoice(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }

  function loadGA() {
    if (loaded) return; loaded = true;
    gtag('consent', 'update', { analytics_storage: 'granted' });
    var s = document.createElement('script');
    s.async = true; s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
    gtag('js', new Date());
    gtag('config', GA_ID);
  }

  function removeGACookies() {
    document.cookie.split(';').forEach(function (c) {
      var n = c.split('=')[0].trim();
      if (n === '_ga' || n.indexOf('_ga_') === 0) {
        var host = location.hostname.replace(/^www\./, '');
        ['', '; domain=' + host, '; domain=.' + host].forEach(function (d) {
          document.cookie = n + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/' + d;
        });
      }
    });
  }

  function banner() {
    if (document.getElementById('tfg-cookie')) return;
    var b = document.createElement('div');
    b.id = 'tfg-cookie';
    b.setAttribute('role', 'dialog');
    b.setAttribute('aria-label', 'Cookie consent');
    b.style.cssText = 'position:fixed;left:16px;right:16px;bottom:16px;z-index:9999;max-width:560px;margin:0 auto;background:#12141C;color:#F5F1EA;border-radius:16px;padding:18px 20px;box-shadow:0 10px 30px rgba(0,0,0,.25);font-size:15px;line-height:1.5;display:flex;flex-direction:column;gap:12px';
    b.innerHTML = '<p style="margin:0">We use Google Analytics cookies to understand how visitors use this site. Nothing is tracked unless you accept.</p>' +
      '<div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:flex-end">' +
      '<button type="button" data-c="denied" style="min-height:44px;padding:0 18px;border-radius:999px;border:1px solid rgba(245,241,234,.4);background:transparent;color:#F5F1EA;font:inherit;cursor:pointer">Decline</button>' +
      '<button type="button" data-c="granted" style="min-height:44px;padding:0 18px;border-radius:999px;border:0;background:#F5F1EA;color:#12141C;font:inherit;font-weight:600;cursor:pointer">Accept</button></div>';
    b.addEventListener('click', function (e) {
      var v = e.target && e.target.getAttribute('data-c');
      if (!v) return;
      setChoice(v);
      if (v === 'granted') loadGA();
      else { gtag('consent', 'update', { analytics_storage: 'denied' }); removeGACookies(); }
      b.parentNode.removeChild(b);
    });
    document.body.appendChild(b);
  }

  function addSettingsLink() {
    var f = document.querySelector('footer');
    if (!f || document.getElementById('tfg-cookie-settings')) return;
    var a = document.createElement('a');
    a.id = 'tfg-cookie-settings'; a.href = '#'; a.textContent = 'Cookie settings';
    a.style.cssText = 'display:inline-block;margin-top:12px;font-size:13px;opacity:.75;color:inherit';
    a.addEventListener('click', function (e) { e.preventDefault(); banner(); });
    f.appendChild(a);
  }

  window.tfgCookieSettings = banner;
  var choice = getChoice();
  if (choice === 'granted') loadGA();

  function init() { if (!choice) banner(); addSettingsLink(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
