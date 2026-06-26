/* e2e/review_surfaces.mjs — browse every live public surface like a normal user: full-page screenshot,
   capture HTML, and extract standardization signals (font, accent, chrome, links, console errors). Read-only. */
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';

const OUT = '/tmp/claude-1000/-home-username-ai-harness-and-knowledge-facts-and-logic-website-sharing/a1b3374d-9cc4-43b0-9f7b-b9dd635cf5cb/scratchpad/surface-review';
mkdirSync(OUT, { recursive: true });

const SURFACES = [
  ['c1-aidoneright-hub', 'https://flags-employee-robinson-nevada.trycloudflare.com'],
  ['c2-teleon',          'https://commodities-cleaner-entities-dangerous.trycloudflare.com'],
  ['c3-baltor',          'https://marathon-crop-moore-logistics.trycloudflare.com'],
  ['c4-aidevobserver',   'https://somerset-evaluations-schedules-copying.trycloudflare.com'],
  ['c5-openhubforai',    'https://chancellor-photography-coins-cir.trycloudflare.com'],
  ['c6-teleon-demo',     'https://commodities-cleaner-entities-dangerous.trycloudflare.com/demo'],
  ['c7-openhubforai-browse','https://chancellor-photography-coins-cir.trycloudflare.com/browse'],
];

const browser = await chromium.launch({ channel: 'chrome', headless: true });
const summary = [];
for (const [name, url] of SURFACES) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 180)); });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + String(e).slice(0, 180)));
  const rec = { name, url, ok: false };
  try {
    const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2800); // let any SPA hydrate
    rec.status = resp ? resp.status() : null;
    rec.title = await page.title();
    Object.assign(rec, await page.evaluate(() => {
      const cs = getComputedStyle(document.body);
      const h1 = document.querySelector('h1');
      const links = [...document.querySelectorAll('a')];
      const btn = document.querySelector('button, .btn, a.go, .cta, .card');
      const accent = btn ? getComputedStyle(btn).backgroundColor : null;
      return {
        bodyFont: cs.fontFamily, bodyBg: cs.backgroundColor, bodyColor: cs.color,
        h1: h1 ? h1.textContent.trim().slice(0, 80) : null,
        hasChrome: !!document.querySelector('header, nav, [class*=nav], [class*=header]'),
        linkCount: links.length,
        sampleLinks: links.map(a => (a.textContent || '').trim()).filter(Boolean).slice(0, 14),
        accentSample: accent, textLen: document.body.innerText.length,
        looksEmpty: document.body.innerText.trim().length < 40,
        has404: /\b404\b|not found/i.test(document.body.innerText.slice(0, 4000)),
      };
    }));
    rec.errors = errors;
    rec.ok = true;
    await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
    writeFileSync(`${OUT}/${name}.html`, await page.content());
  } catch (e) {
    rec.error = String(e).slice(0, 300); rec.errors = errors;
    try { await page.screenshot({ path: `${OUT}/${name}-FAIL.png` }); } catch {}
  }
  summary.push(rec);
  await ctx.close();
}
await browser.close();
writeFileSync(`${OUT}/_summary.json`, JSON.stringify(summary, null, 2));
for (const r of summary) {
  console.log(`\n[${r.ok ? 'OK' : 'FAIL'}] ${r.name}  (${r.status ?? r.error ?? ''})`);
  if (r.ok) console.log(`   title=${JSON.stringify(r.title)} h1=${JSON.stringify(r.h1)}\n   font=${r.bodyFont}\n   bg=${r.bodyBg} accent=${r.accentSample} links=${r.linkCount} empty=${r.looksEmpty} 404=${r.has404} errs=${r.errors.length}`);
}
console.log(`\nscreenshots+html → ${OUT}`);
