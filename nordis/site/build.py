"""Assemble NORDIS site pages: src/<page>.html bodies + shared head, header, footer -> public/."""
import pathlib, re

HERE = pathlib.Path(__file__).parent
SRC, OUT = HERE / "src", HERE / "public"
DOMAIN = "https://nordis.kz"

NAV = [("ii-sotrudniki", "ИИ-сотрудники"), ("sobstvenniku", "Собственнику"), ("prodazhi", "Продажи и команда"),
       ("bezopasnost", "Безопасность"), ("pakety", "Пакеты")]

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
</head>
<body>
<a class="skip" href="#main">К содержанию</a>
"""

def header(active):
    cur = ' aria-current="page"'
    links = "".join(f'<a href="{slug}.html"{cur if slug == active else ""}>{name}</a>' for slug, name in NAV)
    return f"""<header class="hdr"><div class="wrap">
  <a class="logo" href="index.html" aria-label="NORDIS — на главную"><img src="assets/logo.svg" alt="NORDIS" width="104" height="24"></a>
  <nav class="nav" id="nav" aria-label="Разделы">{links}</nav>
  <a class="btn primary" href="index.html#zayavka">10 дней бесплатно</a>
  <button class="burger" type="button" aria-expanded="false" aria-controls="nav">Меню</button>
</div></header>
<main id="main">
"""

FOOT = """</main>
<footer class="ftr"><div class="wrap">
  <div class="col" style="gap:12px">
    <img src="assets/logo.svg" alt="NORDIS" width="104" height="24">
    <p class="muted">Платформа для управления бизнесом с ИИ-сотрудниками. Данные хранятся в Казахстане.</p>
    <p class="muted">Елена Дарс — основатель и разработчик NORDIS</p>
  </div>
  <div><h4>Платформа</h4><ul>{links}</ul></div>
  <div><h4>Связаться</h4><ul>
    <li><a href="https://wa.me/77022681777" target="_blank" rel="noopener">WhatsApp +7 702 268 17 77</a></li>
    <li><a href="files/NORDIS-presentation.pdf">Презентация, PDF</a></li>
    <li><a href="index.html#zayavka">10 дней бесплатно</a></li>
  </ul></div>
</div></footer>
<div class="mcta"><a class="btn ghost" href="https://wa.me/77022681777" target="_blank" rel="noopener">WhatsApp</a><a class="btn primary" href="index.html#zayavka">10 дней бесплатно</a></div>
<script src="assets/site.js" defer></script>
</body>
</html>
"""

FORM = (SRC / "_form.html").read_text()

def build():
    pages = []
    for f in sorted(SRC.glob("*.html")):
        if f.name.startswith("_"):
            continue
        raw = f.read_text()
        meta = dict(re.findall(r"<!--\s*(\w+):\s*(.*?)\s*-->", raw.split("\n\n", 1)[0]))
        body = raw.split("\n\n", 1)[1].replace("{{FORM}}", FORM)
        slug = f.stem
        url = DOMAIN + "/" + ("" if slug == "index" else slug)
        if meta.get("bare") == "1":
            html = HEAD.format(title=meta["title"], desc=meta["desc"], url=url) + body + "\n</body>\n</html>\n"
        else:
            links = "".join(f'<li><a href="{s}.html">{n}</a></li>' for s, n in NAV)
            html = (HEAD.format(title=meta["title"], desc=meta["desc"], url=url) + header(slug) + body
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
