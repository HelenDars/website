/* NORDIS site: menu, lead form, UTM capture */
/* Цели для Яндекс Метрики и пикселя Meta (если счётчики стоят): lead — заявка из формы, chat_lead — заявка из чата
   Елены, whatsapp — нажали WhatsApp, chat_open — открыли чат. В Метрике цели создаются как «JavaScript-событие». */
/* Conversions API (17.11): то же событие отправляет и сервер NORDIS — с тем же eventID, Meta считает его один раз.
   nordisMeta() — данные для сервера: id события, куки пикселя _fbp/_fbc, адрес страницы. */
window.nordisMeta = function (prefix) {
  var c = function (n) { var m = document.cookie.match(new RegExp('(?:^|; )' + n + '=([^;]*)')); return m ? decodeURIComponent(m[1]) : ''; };
  var fbc = c('_fbc');
  if (!fbc) { try { var id = new URLSearchParams(location.search).get('fbclid'); if (id) fbc = 'fb.1.' + Date.now() + '.' + id; } catch (e) {} }
  return { event_id: (prefix || 'ev') + '.' + Date.now().toString(36) + '.' + Math.random().toString(36).slice(2, 10),
           fbp: c('_fbp'), fbc: fbc, url: location.href.slice(0, 500) };
};
window.nordisGoal = function (name, eventId) {
  try { if (window.ym && window.NORDIS_YM) window.ym(window.NORDIS_YM, 'reachGoal', name); } catch (e) {}
  try {
    var opt = eventId ? { eventID: eventId } : undefined;
    if (name === 'whatsapp' && !eventId) {        // Contact: сервер получает его сам (sendBeacon), браузер — с тем же id
      var m = window.nordisMeta('wa'); opt = { eventID: m.event_id };
      var b = JSON.stringify({ event: 'Contact', page: location.pathname, meta: m });
      if (navigator.sendBeacon) navigator.sendBeacon('/api/public/site-event', new Blob([b], { type: 'application/json' }));
    }
    if (window.fbq) {
      if (name === 'lead' || name === 'chat_lead') window.fbq('track', 'Lead', { content_name: name }, opt);
      else if (name === 'whatsapp') window.fbq('track', 'Contact', {}, opt);
      else window.fbq('trackCustom', name);
    }
  } catch (e) {}
};
document.addEventListener('click', function (e) {
  var a = e.target.closest && e.target.closest('a[href*="wa.me/"]');
  if (!a) return;
  // Посетитель с рекламы (есть utm): вместо личного WhatsApp — чат ИИ-продавца на сайте, заявка попадёт в NORDIS
  // с меткой объявления (Елена, 17.11). Кнопка «Отправить заявку в WhatsApp» из самого чата — как была, с пометкой.
  var ad = false;
  try { ad = Object.keys(JSON.parse(sessionStorage.getItem('nordis_utm') || '{}')).length > 0; } catch (x) {}
  if (ad && !a.classList.contains('ec-wa') && window.nordisOpenChat) {
    e.preventDefault(); window.nordisOpenChat(); window.nordisGoal('chat_open'); return;
  }
  if (ad && a.href.indexOf('%D0%B8%D0%B7%20%D1%80%D0%B5%D0%BA%D0%BB%D0%B0%D0%BC%D1%8B') < 0) {
    a.href += (a.href.indexOf('?text=') >= 0 ? '' : '?text=') + encodeURIComponent(' (из рекламы)');
  }
  window.nordisGoal('whatsapp');
});
(function () {
  // Address of the NORDIS CRM endpoint that accepts leads (POST, JSON).
  // While it is empty, the form opens WhatsApp with the filled-in request.
  var LEAD_ENDPOINT = '/api/public/site-lead';
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
      source: 'nordis.kz',
      meta: window.nordisMeta('lead')
    };
    if (!d.name || d.phone.replace(/\D/g, '').length < 10) {
      // называем именно пустое поле и ставим в него курсор (16.11: номер был верный, а ошибка звучала про оба поля)
      var miss = !d.name ? 'name' : 'phone';
      show(!d.name ? 'Укажите имя — поле «Имя» вверху формы.' : 'Укажите номер телефона — 10 или 11 цифр.', false);
      var el = form.querySelector('[name="' + miss + '"]');
      if (el) { el.focus(); el.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
      return;
    }
    var btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;

    var done = function () {
      form.reset();
      window.nordisGoal('lead', d.meta.event_id);
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
  var mln = function (v) { return (v / 1e6).toLocaleString('ru-RU', { maximumFractionDigits: 1 }); };
  var tg = function (v) { return Math.round(v).toLocaleString('ru-RU') + ' ₸'; };
  var pct = function (v) { return (v * 100).toLocaleString('ru-RU', { maximumFractionDigits: 1 }) + '%'; };
  function calc() {
    var rev = num('c-rev') * 1e6, margin = Math.min(num('c-margin'), 95) / 100;
    var mgr = Math.floor(num('c-mgr')), sal = num('c-sal');
    var ads = num('c-ads') * 1e6;
    var pack, price, team;
    if (rev < 20e6) { pack = 'Лайт'; price = 1.2e6; team = false; }
    else if (rev < 100e6) { pack = 'Бизнес'; price = 2e6; team = true; }
    else { pack = 'Премиум'; price = 3.3e6; team = true; }
    // зарплаты: ИИ-продавец заменяет до двух менеджеров; ИИ-РОП и ИИ-таргетолог — в Бизнес и Премиум
    var repl = Math.min(mgr, 2), fot = repl * sal, who = [];
    if (repl) who.push(repl + ' из ' + mgr + ' менеджеров по ' + tg(sal));
    if (team && $('c-rop').checked) { fot += num('c-ropsal'); who.push('РОП'); }
    if (team && $('c-tg').checked) { fot += num('c-tgsal'); who.push('таргетолог'); }
    // реклама: NORDIS показывает объявления без продаж, в проекте расход 14 → 12 млн ₸ (−14%)
    var adSave = ads / 7;
    // рост продаж: новая выручка × маржа
    var g = Math.min(num('c-grow'), 100) / 100, extra = rev * g, grow = extra * margin;
    var comm = extra * Math.min(num('c-comm'), 10) / 100;
    var fee = price + rev * 0.47 * 0.01;   // +1% с продаж, которые закрыл ИИ-продавец (около половины продаж)
    var rate = Math.min(num('c-rate'), 50) / 100, simple = $('c-tax').value === 'simple', tax;
    if (simple) tax = extra * rate;        // упрощёнка: налог с выручки — экономия налогом не облагается
    else tax = Math.max(0, (fot + adSave + grow - comm - fee) * rate);   // КПН с прибавки к прибыли
    var total = fot + adSave + grow - comm - tax - fee;
    $('c-pack').textContent = 'пакет ' + pack;
    $('l-fot').textContent = who.length ? 'Зарплаты: ИИ-сотрудники заменяют ' + who.join(', ') + '. Остаётся у вас' : 'Зарплаты: менеджеров на замену нет';
    $('l-ads').textContent = 'Реклама: тратили ' + mln(ads) + ' млн ₸ в месяц → станет ' + mln(ads - adSave) + ' млн ₸ (−14%: NORDIS показывает объявления без продаж). Остаётся у вас';
    $('l-grow').textContent = 'Рост продаж: выручка ' + mln(rev) + ' → ' + mln(rev + extra) + ' млн ₸ (+' + pct(g) + '), маржа ' + pct(margin) + '. Прибыль с новых продаж';
    $('l-comm').textContent = 'Комиссия за приём оплат с новой выручки (' + pct(Math.min(num('c-comm'), 10) / 100) + ')';
    $('l-tax').textContent = simple ? 'Налог: упрощёнка ' + pct(rate) + ' с новой выручки (экономия на зарплатах и рекламе налогом не облагается)'
      : 'Налог: КПН ' + pct(rate) + ' с прибавки к прибыли';
    $('l-fee').textContent = 'NORDIS: пакет ' + pack + ' ' + mln(price) + ' млн ₸ + 1% с продаж ИИ-продавца';
    $('r-fot').textContent = '+' + fmt(fot);
    $('r-ads').textContent = '+' + fmt(adSave);
    $('r-grow').textContent = '+' + fmt(grow);
    $('r-comm').textContent = '−' + fmt(comm);
    $('r-tax').textContent = '−' + fmt(tax);
    $('r-fee').textContent = '−' + fmt(fee);
    $('r-total').textContent = (total >= 0 ? '+' : '') + fmt(total);
    $('r-roi').textContent = fee > 0
      ? 'Каждый тенге в NORDIS возвращает ' + ((total + fee) / fee).toLocaleString('ru-RU', { maximumFractionDigits: 1 }) +
        ' ₸. За год: ' + (total >= 0 ? '+' : '') + fmt(total * 12) + '. В первый месяц пакет стоит на ' + fmt(price / 2) + ' меньше.'
      : '';
  }
  $('c-tax').addEventListener('change', function () { $('c-rate').value = this.value === 'simple' ? 4 : 20; });
  root.addEventListener('input', calc);
  root.addEventListener('change', calc);
  calc();
})();

/* пакеты: клик по карточке или плашке — раскрыть состав; «Записаться — пакет …» — к форме с выбранным пакетом */
(function () {
  var TURN = { 'Лайт': '5–20 млн ₸', 'Бизнес': '20–100 млн ₸', 'Премиум': 'больше 100 млн ₸' };
  document.querySelectorAll('.pack').forEach(function (card) {
    var more = card.querySelector('details.more');
    if (!more) return;
    card.addEventListener('click', function (e) {
      if (e.target.closest('a, summary, button, input, select, textarea')) return;
      more.open = !more.open;
    });
  });
  document.querySelectorAll('[data-pick]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var form = document.getElementById('zayavka');
      var pack = a.getAttribute('data-pick');
      if (!form) return;              // формы на странице нет — обычный переход
      e.preventDefault();
      var sel = document.getElementById('f-turnover'), com = document.getElementById('f-comment');
      if (sel) Array.prototype.forEach.call(sel.options, function (o) { if (o.text === TURN[pack]) sel.value = o.value || o.text; });
      if (com && com.value.indexOf('Пакет') !== 0) com.value = 'Пакет ' + pack + (com.value ? '. ' + com.value : '');
      form.scrollIntoView({ behavior: 'smooth', block: 'start' });
      var name = document.getElementById('f-name');
      if (name) setTimeout(function () { name.focus({ preventScroll: true }); }, 600);
    });
  });
})();

/* Видео Елены (В1–В5): файл assets/video/vN.mp4 (+ обложка vN.webp). Пока файла нет — блок скрыт, сайт как раньше.
   Без звука, по кругу, играет только на экране; «уменьшить движение» в системе — без автозапуска (по нажатию).
   «🔊 Со звуком» — цель Метрики video_sound. */
(function () {
  var figs = document.querySelectorAll('figure.vid[data-video]');
  if (!figs.length || !window.fetch) return;
  var still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var io = 'IntersectionObserver' in window;
  function arm(fig) {
    var v = fig.querySelector('video'), snd = fig.querySelector('.vid-snd');
    var src = 'assets/video/' + fig.getAttribute('data-video') + '.mp4';
    fetch(src, { method: 'HEAD' }).then(function (r) {
      var t = r.headers.get('content-type') || '';
      if (!r.ok || t.indexOf('video') !== 0) return;          // файла нет (404 или страница ошибки) — блок не показываем
      v.poster = src.replace(/\.mp4$/, '.webp');
      v.preload = 'metadata';
      v.src = src;
      fig.hidden = false;
      if (still) { v.controls = true; return; }
      if (io) {
        new IntersectionObserver(function (es) {
          es.forEach(function (e) {
            if (e.isIntersecting && e.intersectionRatio >= 0.5) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }
            else v.pause();
          });
        }, { threshold: [0, 0.5] }).observe(fig);
      }
    }).catch(function () {});
    snd.addEventListener('click', function () {
      v.muted = false; v.currentTime = 0; v.controls = true; snd.hidden = true;
      var p = v.play(); if (p && p.catch) p.catch(function () {});
      if (window.nordisGoal) window.nordisGoal('video_sound');
    });
  }
  figs.forEach(function (fig) {
    if (!io) return arm(fig);
    var once = new IntersectionObserver(function (es) {
      if (es[0].isIntersecting) { once.disconnect(); arm(fig); }
    }, { rootMargin: '600px 0px' });
    once.observe(fig.parentNode);                               // сама фигура скрыта — следим за её блоком
  });
})();
