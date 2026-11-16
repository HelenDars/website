/* Елена — ИИ-продавец NORDIS на сайте: ответы за секунды, запись на разбор, заявка в WhatsApp */
(function () {
  var API = '/api/public/site-chat';
  var KEY = 'nordis-chat';
  var hist = [];
  try { hist = JSON.parse(sessionStorage.getItem(KEY) || '[]'); } catch (e) { hist = []; }
  var save = function () { try { sessionStorage.setItem(KEY, JSON.stringify(hist.slice(-24))); } catch (e) {} };
  var HELLO = 'Здравствуйте! Я Елена, ИИ-продавец NORDIS — так же будет работать ИИ-продавец у Вас. Расскажите, чем занимается Ваш бизнес, — подскажу, где NORDIS добавит чистой прибыли.';

  var btn = document.createElement('button');
  btn.type = 'button'; btn.className = 'ec-btn'; btn.setAttribute('aria-label', 'Спросить Елену');
  btn.innerHTML = '<img src="assets/team/elena.webp" alt="" width="44" height="44"><span>Спросить Елену<small>ответ за 30 секунд</small></span>';
  var box = document.createElement('section');
  box.className = 'ec-box'; box.hidden = true; box.setAttribute('aria-label', 'Чат с Еленой');
  box.innerHTML = '<header><img src="assets/team/elena.webp" alt="" width="40" height="40"><div><b>Елена</b><span>ИИ-продавец NORDIS · онлайн 24/7</span></div>' +
    '<button type="button" class="ec-x" aria-label="Закрыть">×</button></header><div class="ec-msgs" aria-live="polite"></div>' +
    '<p class="ec-ok">Отправляя сообщение, вы соглашаетесь с <a href="politika.html" target="_blank">обработкой персональных данных</a></p><form class="ec-form"><textarea rows="1" maxlength="1000" placeholder="Напишите вопрос…" aria-label="Сообщение"></textarea><button class="btn primary" type="submit">→</button></form>';
  var back = document.createElement('div'); back.className = 'ec-back'; back.hidden = true;
  document.body.append(back, btn, box);
  var msgs = box.querySelector('.ec-msgs'), form = box.querySelector('form'), ta = form.querySelector('textarea');

  function bubble(role, text, wa) {
    var d = document.createElement('div'); d.className = 'ec-m ' + (role === 'user' ? 'ec-u' : 'ec-a');
    d.textContent = text;
    if (wa) { var a = document.createElement('a'); a.href = wa; a.target = '_blank'; a.rel = 'noopener'; a.className = 'btn primary ec-wa'; a.textContent = 'Отправить заявку в WhatsApp'; d.appendChild(a); }
    msgs.appendChild(d); msgs.scrollTop = msgs.scrollHeight; return d;
  }
  function draw() { msgs.innerHTML = ''; bubble('assistant', HELLO); hist.forEach(function (m) { bubble(m.role, m.text, m.wa); }); }
  var phone = function () { return window.matchMedia('(max-width: 760px)').matches; };
  function open() { box.hidden = false; btn.hidden = true; back.hidden = !phone(); document.body.classList.toggle('ec-lock', phone()); draw();
    if (!phone()) setTimeout(function () { ta.focus(); }, 50); }   // на телефоне клавиатура — только по нажатию в поле
  function close() { box.hidden = true; btn.hidden = false; back.hidden = true; document.body.classList.remove('ec-lock'); }
  back.onclick = close;
  btn.onclick = open;
  box.querySelector('.ec-x').onclick = close;
  ta.addEventListener('keydown', function (e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); } });
  form.onsubmit = function (e) {
    e.preventDefault();
    var t = ta.value.trim(); if (!t) return;
    ta.value = ''; hist.push({ role: 'user', text: t }); save(); bubble('user', t);
    var wait = bubble('assistant', 'Елена печатает…'); wait.classList.add('ec-wait');
    var body = { messages: [{ role: 'assistant', text: HELLO }].concat(hist.slice(-23).map(function (m) { return { role: m.role, text: m.text.slice(0, 1000) }; })), page: location.pathname };
    fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (x) {
        wait.remove();
        var text = x.ok ? x.d.reply : (x.d.detail || 'Не получилось ответить. Напишите нам в WhatsApp: +7 702 268 17 77');
        var m = { role: 'assistant', text: text, wa: x.ok ? x.d.whatsapp : null }; hist.push(m); save(); bubble('assistant', m.text, m.wa);
      })
      .catch(function () { wait.textContent = 'Нет связи. Напишите нам в WhatsApp: +7 702 268 17 77'; });
  };
  document.querySelectorAll('[data-ask-elena]').forEach(function (a) { a.addEventListener('click', function (e) { e.preventDefault(); open(); }); });
})();
