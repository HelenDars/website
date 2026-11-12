/* NORDIS site: menu, lead form, UTM capture */
(function () {
  // Address of the NORDIS CRM endpoint that accepts leads (POST, JSON).
  // While it is empty, the form opens WhatsApp with the filled-in request.
  var LEAD_ENDPOINT = '';
  var WHATSAPP = '77022681777';

  var burger = document.querySelector('.burger');
  var nav = document.getElementById('nav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      burger.setAttribute('aria-expanded', String(open));
    });
  }

  // keep UTM tags for the AI targetologist
  var utm = {};
  try {
    var q = new URLSearchParams(location.search);
    ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach(function (k) {
      if (q.get(k)) utm[k] = q.get(k);
    });
    if (Object.keys(utm).length) sessionStorage.setItem('nordis_utm', JSON.stringify(utm));
    else utm = JSON.parse(sessionStorage.getItem('nordis_utm') || '{}');
  } catch (e) { utm = {}; }

  var form = document.getElementById('lead-form');
  if (!form) return;
  var msg = document.getElementById('form-msg');

  function show(text, ok) {
    msg.hidden = false;
    msg.className = 'form-msg ' + (ok ? 'ok' : 'err');
    msg.innerHTML = text;
  }

  function waLink(d) {
    var text = 'Здравствуйте! Хочу 10 дней NORDIS бесплатно.\n' +
      'Имя: ' + d.name + '\nКомпания: ' + (d.company || '—') + '\nОборот в месяц: ' + d.turnover +
      (d.comment ? '\nЗадача: ' + d.comment : '');
    return 'https://wa.me/' + WHATSAPP + '?text=' + encodeURIComponent(text);
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var f = new FormData(form);
    var d = {
      name: (f.get('name') || '').trim(),
      phone: (f.get('phone') || '').trim(),
      company: (f.get('company') || '').trim(),
      turnover: f.get('turnover') || '',
      comment: (f.get('comment') || '').trim(),
      page: location.pathname,
      utm: utm,
      source: 'nordis.kz'
    };
    if (!d.name || d.phone.replace(/\D/g, '').length < 10) {
      show('Укажите имя и номер телефона — 10 или 11 цифр.', false);
      return;
    }
    var btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;

    var done = function () {
      form.reset();
      show('Спасибо! Заявка принята. Я свяжусь с вами в WhatsApp в течение рабочего дня.', true);
      btn.disabled = false;
    };
    var fallback = function () {
      show('Нажмите, чтобы отправить заявку в WhatsApp: <a href="' + waLink(d) + '" target="_blank" rel="noopener">открыть WhatsApp</a>. Или позвоните: +7 702 268 17 77.', true);
      btn.disabled = false;
    };

    if (!LEAD_ENDPOINT) { fallback(); return; }
    fetch(LEAD_ENDPOINT, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(d) })
      .then(function (r) { if (r.ok) done(); else fallback(); })
      .catch(fallback);
  });
})();
