"""Build NORDIS deck: inline logo, QR, charts; render PDFs for 16:9 and 9:16."""
import re, pathlib, sys

HERE = pathlib.Path(__file__).parent
logo = (HERE.parent / "brand" / "nordis-logo-dark-tight.svg").read_text()
paths = re.findall(r'<path fill="#0D1229"(?: fill-rule="evenodd")? d="([^"]+)"', logo)
letters, ring = paths[0], paths[1]

qr_src = pathlib.Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else ""
qr = re.sub(r'width="\d+" height="\d+"', 'viewBox="0 0 250 250"', qr_src.strip(), count=1)

# waterfall
steps = [("Было", 5.20, "base"), ("ФОТ", 2.10, "up"), ("Реклама", 2.00, "up"), ("Рост|продаж", 3.13, "up"),
         ("Комиссии|банков", -0.37, "down"), ("Налоги", -0.10, "down"), ("NORDIS", -1.68, "down"), ("Стало", 10.27, "total")]
W, H, top, bottom = 640, 470, 50, 380
peak = 12.43
k = (bottom - top) / peak
bw, gap, x0 = 52, 26, 24
cum = 0.0
out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Каскад: было 5,2 млн, плюс ФОТ 2,1, плюс реклама 2,0, плюс рост продаж 3,13, минус комиссии 0,37, налоги 0,10, NORDIS 1,68, стало 10,27 млн" class="wf">',
       f'<line x1="0" y1="{bottom}" x2="{W}" y2="{bottom}" stroke="#2E3866" stroke-width="2"/>']
for i, (name, v, kind) in enumerate(steps):
    x = x0 + i * (bw + gap)
    if kind in ("base", "total"):
        a, b = 0, v
        cum = v
    else:
        a, b = cum, cum + v
        cum = b
    y1, y2 = bottom - max(a, b) * k, bottom - min(a, b) * k
    color = {"base": "#5C6B9C", "up": "#C8F542", "down": "#FF6B57", "total": "#C8F542"}[kind]
    out.append(f'<rect x="{x}" y="{y1:.1f}" width="{bw}" height="{max(y2-y1,3):.1f}" rx="7" fill="{color}"/>')
    label = (f"{v:+.2f}" if kind in ("up", "down") else f"{v:.2f}").replace(".", ",").replace("-", "−")
    out.append(f'<text x="{x+bw/2}" y="{y1-12:.1f}" text-anchor="middle" fill="{"#FF8E80" if kind=="down" else "#F2F4FA"}" font-size="19" font-weight="700">{label}</text>')
    if i < len(steps) - 1 and kind != "total":
        out.append(f'<line x1="{x+bw}" y1="{bottom-cum*k:.1f}" x2="{x+bw+gap}" y2="{bottom-cum*k:.1f}" stroke="#5C6B9C" stroke-dasharray="3 4"/>')
    for j, part in enumerate(name.split("|")):
        out.append(f'<text x="{x+bw/2}" y="{bottom+30+j*22}" text-anchor="middle" fill="#A3ACCD" font-size="17">{part}</text>')
out.append("</svg>")
waterfall = "".join(out)

sc = [("Пессимистичный", "+10%", "10,3", 10.3, "+5,1", "+61 млн ₸", "+98%", "3,0 ₸", False),
      ("Реалистичный", "+18,6%", "12,5", 12.5, "+7,3", "+88 млн ₸", "+140%", "4,3 ₸", True),
      ("Оптимистичный", "+30%", "15,4", 15.4, "+10,2", "+123 млн ₸", "+197%", "6,0 ₸", False)]
cards = []
for name, rev, after, af, add, year, growth, ret, hl in sc:
    base_w = 5.2 / 15.4 * 100
    new_w = af / 15.4 * 100
    style = ' style="border:3px solid var(--lime);background:var(--panel2)"' if hl else ""
    cards.append(f'''<div class="card sc"{style}>
  <p class="eyebrow" style="color:var(--mist)">{name}</p>
  <h3>выручка {rev}</h3>
  <div class="scbar" style="position:relative;height:16px;border-radius:8px;background:#232C58;margin-top:6px"><div style="position:absolute;left:0;top:0;bottom:0;width:{new_w:.0f}%;border-radius:8px;background:var(--lime)"></div><div style="position:absolute;left:0;top:0;bottom:0;width:{base_w:.0f}%;border-radius:8px;background:var(--steel)"></div></div>
  <div class="scbar" style="display:flex;justify-content:space-between;font-size:18px;opacity:.6"><span>было 5,2</span><span>стало {after}</span></div>
  <div class="n">{add}<small>млн ₸</small></div>
  <p class="t">к чистой прибыли в месяц</p>
  <div class="m" style="display:grid;grid-template-columns:1fr auto;gap:10px 16px;font-size:22px;border-top:1px solid #FFFFFF1F;padding-top:16px">
    <span style="font-family:var(--txt);opacity:.7">За год</span><b>{year}</b>
    <span style="font-family:var(--txt);opacity:.7">Рост прибыли</span><b>{growth}</b>
    <span style="font-family:var(--txt);opacity:.7">1 ₸ в NORDIS возвращает</span><b>{ret}</b>
  </div>
</div>''')

html = (HERE / "deck.src.html").read_text()
html = (html.replace("{{LETTERS}}", letters).replace("{{RING}}", ring).replace("{{QR}}", qr)
        .replace("{{WATERFALL}}", waterfall).replace("{{SCENARIOS}}", "\n".join(cards)))
(HERE / "index.html").write_text(html)
print("ok", len(html))
