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
    var text = 'Здравствуйте! Хочу разбор и подключение NORDIS, первый месяц −50%.\n' +
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

/* savings calculator */
(function () {
  var root = document.getElementById('calc');
  if (!root) return;
  var $ = function (id) { return document.getElementById(id); };
  var num = function (id) { var v = parseFloat(String($(id).value).replace(',', '.')); return isFinite(v) && v > 0 ? v : 0; };
  var fmt = function (v) {
    var m = v / 1e6;
    return (v < 0 ? '−' : '') + Math.abs(m).toLocaleString('ru-RU', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + ' млн ₸';
  };
  function calc() {
    var rev = num('c-rev') * 1e6, margin = Math.min(num('c-margin'), 95) / 100;
    var mgr = Math.floor(num('c-mgr')), sal = num('c-sal');
    var ads = num('c-ads') * 1e6;
    var pack, price, team;
    if (rev < 20e6) { pack = 'Лайт'; price = 1.2e6; team = false; }
    else if (rev < 100e6) { pack = 'Бизнес'; price = 2e6; team = true; }
    else { pack = 'Премиум'; price = 3.3e6; team = true; }
    var fot = Math.min(mgr, 2) * sal;
    if (team && $('c-rop').checked) fot += num('c-ropsal');
    if (team && $('c-tg').checked) fot += num('c-tgsal');
    var adSave = ads * 0.14;
    var grow = rev * 0.10 * margin;
    var fee = price + rev * 0.4 * 0.01;
    var total = fot + adSave + grow - fee;
    $('c-pack').textContent = 'пакет ' + pack;
    $('r-fot').textContent = '+' + fmt(fot);
    $('r-ads').textContent = '+' + fmt(adSave);
    $('r-grow').textContent = '+' + fmt(grow);
    $('r-fee').textContent = '−' + fmt(fee);
    $('r-total').textContent = (total >= 0 ? '+' : '') + fmt(total);
    $('r-roi').textContent = fee > 0
      ? 'Каждый тенге в NORDIS возвращает ' + ((fot + adSave + grow) / fee).toLocaleString('ru-RU', { maximumFractionDigits: 1 }) +
        ' ₸. За год: ' + (total >= 0 ? '+' : '') + fmt(total * 12) + '. В первый месяц пакет стоит на ' + fmt(price / 2) + ' меньше.'
      : '';
  }
  root.addEventListener('input', calc);
  root.addEventListener('change', calc);
  calc();
})();
