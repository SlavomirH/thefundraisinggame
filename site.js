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
