"""Assemble NORDIS site pages: src/<page>.html bodies + shared head, header, footer -> public/."""
import pathlib, re

HERE = pathlib.Path(__file__).parent
SRC, OUT = HERE / "src", HERE / "public"
DOMAIN = "https://nordis.kz"

# Счётчики: вписать номера — и пересобрать. Пусто — на сайт ничего не ставится.
METRIKA_ID = "114273471"      # Яндекс Метрика: номер счётчика (цифры), metrika.yandex.ru
META_PIXEL_ID = "1834449011219732"   # пиксель Meta: ID набора данных (цифры), Meta Events Manager

def counters():
    out = ""
    if METRIKA_ID:
        out += f"""<!-- Yandex.Metrika counter -->
<script type="text/javascript">(function(m,e,t,r,i,k,a){{m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};
m[i].l=1*new Date();for(var j=0;j<document.scripts.length;j++){{if(document.scripts[j].src===r){{return;}}}}
k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)}})
(window,document,'script','https://mc.yandex.ru/metrika/tag.js?id={METRIKA_ID}','ym');
ym({METRIKA_ID},'init',{{ssr:true,webvisor:true,clickmap:true,ecommerce:"dataLayer",accurateTrackBounce:true,trackLinks:true}});
window.NORDIS_YM={METRIKA_ID};</script>
<noscript><div><img src="https://mc.yandex.ru/watch/{METRIKA_ID}" style="position:absolute;left:-9999px" alt=""></div></noscript>
<!-- /Yandex.Metrika counter -->
"""
    if META_PIXEL_ID:
        out += f"""<script>!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;
s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init','{META_PIXEL_ID}');fbq('track','PageView');</script>
<noscript><img height="1" width="1" style="display:none" alt="" src="https://www.facebook.com/tr?id={META_PIXEL_ID}&ev=PageView&noscript=1"></noscript>
"""
    return out

NAV = [("ii-sotrudniki", "ИИ-сотрудники"), ("sobstvenniku", "Собственнику"), ("prodazhi", "Продажи и команда"),
       ("reklama", "Реклама"), ("otrasli", "Для кого"), ("vnedrenie", "Внедрение"), ("pakety", "Пакеты")]
FOOTNAV = NAV + [("bezopasnost", "Безопасность"), ("kalkulyator", "Калькулятор выгоды"), ("politika", "Обработка персональных данных")]

HEAD = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="ru_KZ">
<meta name="theme-color" content="#FFFFFF">
<link rel="icon" href="assets/icon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@600;700&family=Manrope:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600&display=swap">
<link rel="stylesheet" href="assets/style.css">
{counters}</head>
<body>
<a class="skip" href="#main">К содержанию</a>
"""

def header(active):
    cur = ' aria-current="page"'
    links = "".join(f'<a href="{slug}.html"{cur if slug == active else ""}>{name}</a>' for slug, name in NAV)
    return f"""<header class="hdr"><div class="wrap">
  <a class="logo" href="index.html" aria-label="NORDIS — на главную"><img src="assets/logo.svg" alt="NORDIS" width="110" height="24"></a>
  <nav class="nav" id="nav" aria-label="Разделы">{links}</nav>
  <a class="btn primary" href="index.html#zayavka">Записаться на разбор</a>
  <button class="burger" type="button" aria-expanded="false" aria-controls="nav">Меню</button>
</div></header>
<main id="main">
"""

FOOT = """</main>
<footer class="ftr"><div class="wrap">
  <div class="col" style="gap:12px">
    <img src="assets/logo.svg" alt="NORDIS" width="110" height="24">
    <p class="muted">Платформа для управления бизнесом с ИИ-сотрудниками. Данные хранятся в Казахстане.</p>
    <p class="muted" style="font-size:13px">ТОО «Helen Dars» · БИН 180740027180<br>г. Астана, ул. Алматы, д. 1</p>
  </div>
  <div><h4>Платформа</h4><ul>{links}</ul></div>
  <div><h4>Связаться</h4><ul>
    <li><a href="https://wa.me/77022681777" target="_blank" rel="noopener">WhatsApp +7 702 268 17 77</a></li>
    <li><a href="https://wa.me/77022681777?text=%D0%97%D0%B4%D1%80%D0%B0%D0%B2%D1%81%D1%82%D0%B2%D1%83%D0%B9%D1%82%D0%B5%21%20%D0%9F%D1%80%D0%B8%D1%88%D0%BB%D0%B8%D1%82%D0%B5%2C%20%D0%BF%D0%BE%D0%B6%D0%B0%D0%BB%D1%83%D0%B9%D1%81%D1%82%D0%B0%2C%20%D0%BF%D1%80%D0%B5%D0%B7%D0%B5%D0%BD%D1%82%D0%B0%D1%86%D0%B8%D1%8E%20NORDIS" target="_blank" rel="noopener">Презентация в WhatsApp</a></li>
    <li><a href="index.html#zayavka">Разбор и −50% на первый месяц</a></li>
  </ul></div>
</div></footer>
<div class="mcta"><a class="btn ghost" href="https://wa.me/77022681777" target="_blank" rel="noopener">WhatsApp</a><a class="btn primary" href="index.html#zayavka">−50% на 1 месяц</a></div>
<script src="assets/site.js" defer></script>
<script src="assets/chat.js" defer></script>
</body>
</html>
"""

FORM = (SRC / "_form.html").read_text()
CALC = (SRC / "_calc.html").read_text()

def build():
    pages = []
    for f in sorted(SRC.glob("*.html")):
        if f.name.startswith("_"):
            continue
        raw = f.read_text()
        meta = dict(re.findall(r"<!--\s*(\w+):\s*(.*?)\s*-->", raw.split("\n\n", 1)[0]))
        body = raw.split("\n\n", 1)[1].replace("{{FORM}}", FORM).replace("{{CALC}}", CALC)
        slug = f.stem
        url = DOMAIN + "/" + ("" if slug == "index" else slug)
        if meta.get("bare") == "1":
            html = HEAD.format(title=meta["title"], desc=meta["desc"], url=url, counters=counters()) + body + "\n</body>\n</html>\n"
        else:
            links = "".join(f'<li><a href="{s}.html">{n}</a></li>' for s, n in FOOTNAV)
            html = (HEAD.format(title=meta["title"], desc=meta["desc"], url=url, counters=counters()) + header(slug) + body
                    + FOOT.replace("{links}", links))
        (OUT / f.name).write_text(html)
        if slug != "404":
            pages.append(url)
    sm = "".join(f"<url><loc>{u}</loc></url>" for u in pages)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n")
    (OUT / "CNAME").write_text("nordis.kz\n")
    print("built", len(pages), "pages")

build()
