// node render.js <pdf-out-dir> [png <png-dir>] : PDFs for both formats, optional per-slide PNG previews
const { chromium } = require('playwright');
const path = require('path');
const out = process.argv[2] || '.';
(async () => {
  const b = await chromium.launch();
  for (const [m, w, h] of [['wide', 1920, 1080], ['tall', 1080, 1920]]) {
    const p = await b.newPage({ viewport: { width: w, height: h } });
    await p.goto('file://' + path.resolve(__dirname, 'index.html') + '#print-' + m);
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(500);
    await p.addStyleTag({ content: `@page{size:${w}px ${h}px;margin:0}` });
    await p.pdf({ path: path.join(out, `NORDIS-${m === 'wide' ? '16x9' : '9x16'}.pdf`), width: w + 'px', height: h + 'px', printBackground: true });
    if (process.argv[3] === 'png') {
      const fr = await p.$$('.frame');
      for (let i = 0; i < fr.length; i++) await fr[i].screenshot({ path: path.join(process.argv[4], `${m}-${String(i + 1).padStart(2, '0')}.png`) });
    }
    const bad = await p.evaluate(() => [...document.querySelectorAll('.s')].map((s, i) => {
      const mn = s.querySelector('.main');
      return (mn.scrollHeight > mn.clientHeight + 2) ? i + 1 : 0;
    }).filter(Boolean));
    console.log(m, 'overflow slides:', bad.join(',') || 'none');
    await p.close();
  }
  await b.close();
})();
