// e2e/ohh_route_audit.mjs — EVERY OpenHarnessHub route, logged-out AND logged-in, console-gated.
// Also asserts the live-catalog hydration (browse shows the real registry, a real component's
// detail renders with real governance fields, and no fabricated lift appears on live pipelines).
//
// Run: node e2e/ohh_route_audit.mjs [base]   (default http://127.0.0.1:8000)

import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE = process.argv[2] || 'http://127.0.0.1:8000';
const OUT = join(dirname(fileURLToPath(import.meta.url)), 'artifacts', 'full-design');
const EXPECTED = [/in-browser Babel transformer/i, /React DevTools/i];

// the complete static route map of proto-main.jsx (parametrics get live samples below)
const ROUTES = ['/', '/about', '/activity', '/admin', '/app', '/attest', '/audit-log', '/build',
  '/cases', '/checkout', '/components', '/connect', '/contribute', '/dashboards', '/drafts',
  '/flow', '/foundry', '/freshness', '/improve', '/onboarding', '/pipelines', '/preview',
  '/pricing', '/publish', '/registry', '/requests', '/results', '/roles', '/run', '/settings',
  '/signin', '/signup', '/solutions', '/sources', '/status', '/trust', '/upgrade', '/workers',
  '/for/builders', '/for/governments', '/for/lawyers', '/for/regulators'];

const browser = await chromium.launch({ channel: 'chrome' });
const report = { base: BASE, modes: {}, liveCatalog: {}, failures: 0 };

async function walk(mode) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  const errs = {};
  let current = 'boot';
  page.on('console', (m) => {
    if (m.type() === 'error' && !EXPECTED.some((re) => re.test(m.text()))) (errs[current] = errs[current] || []).push(m.text().slice(0, 160));
  });
  page.on('pageerror', (e) => (errs[current] = errs[current] || []).push(String(e).slice(0, 160)));

  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  if (mode === 'logged-in') await page.evaluate(() => localStorage.setItem('ohp-auth', '1'));
  await page.waitForTimeout(2600);

  // live samples for the parametric routes
  const liveId = await page.evaluate(async () => {
    const r = await fetch('/api/components?limit=1');
    const d = await r.json();
    return d.results && d.results[0] && d.results[0].id;
  });
  const routes = [...ROUTES, ...(liveId ? [`/c/${liveId}`] : []), '/k/csddd-articles', '/p/esg-cite-first', '/cases/0'];

  const rows = [];
  for (const r of routes) {
    current = r;
    await page.evaluate((h) => { window.location.hash = h; }, r);
    await page.waitForTimeout(650);
    const state = await page.evaluate(() => ({
      len: document.body.innerText.length,
      notFound: /not found|nothing here|404/i.test((document.querySelector('.pt-page h1, h1') || {}).textContent || ''),
    }));
    const ok = state.len > 120 && !(errs[r] || []).length;
    rows.push({ route: r, ok, len: state.len, errors: errs[r] || [] });
  }
  await ctx.close();
  const bad = rows.filter((x) => !x.ok);
  report.modes[mode] = { total: rows.length, bad };
  report.failures += bad.length;
  console.log(`[${mode}] ${rows.length - bad.length}/${rows.length} routes clean` + (bad.length ? ` — FAILING: ${bad.map((b) => `${b.route}(${b.errors[0] || 'blank:' + b.len})`).join(' · ')}` : ''));
}

await walk('logged-out');
await walk('logged-in');

// ---- live catalog assertions ----
{
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(BASE + '/#/components', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4200);
  const browse = await page.evaluate(() => ({
    poolText: (document.querySelector('.pt-results-bar .pt-muted') || {}).innerText || '',
    cards: document.querySelectorAll('.pt-cards-grid .oh-comp-card').length,
  }));
  const livePool = /of\s+([\d,]+)/.exec(browse.poolText.replace(/ /g, ' '));
  const poolN = livePool ? parseInt(livePool[1].replace(/,/g, ''), 10) : 0;
  report.liveCatalog.browse = { ...browse, poolN };
  const browseOk = poolN > 1000 && browse.cards > 100;
  console.log(`[live-catalog] browse pool=${poolN} cards=${browse.cards} → ${browseOk ? 'LIVE' : 'NOT LIVE'}`);
  if (!browseOk) report.failures += 1;

  // a real pipeline detail must show governance and must NOT fabricate a lift number
  const sample = await page.evaluate(async () => {
    const r = await fetch('/api/components?type=pipeline&limit=1');
    const d = await r.json();
    return d.results && d.results[0];
  });
  if (sample) {
    await page.evaluate((id) => { window.location.hash = `/c/${id}`; }, sample.id);
    await page.waitForTimeout(900);
    const detail = await page.evaluate(() => ({
      text: document.body.innerText.slice(0, 4000),
      unproven: /— unproven/.test(document.body.innerText),
      fabricated: /▲ \+0\.40/.test(document.body.innerText),
    }));
    const detailOk = detail.unproven && !detail.fabricated && detail.text.includes(sample.name.slice(0, 24));
    report.liveCatalog.detail = { id: sample.id, ok: detailOk, unproven: detail.unproven, fabricated: detail.fabricated };
    console.log(`[live-catalog] detail ${sample.id} → ${detailOk ? 'HONEST (unproven, no fabricated lift)' : 'PROBLEM'}`);
    if (!detailOk) report.failures += 1;
    await page.screenshot({ path: join(OUT, 'ohh-live-detail.png') });
  }
  await page.goto(BASE + '/#/components', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4200);
  await page.screenshot({ path: join(OUT, 'ohh-live-browse.png') });
  await ctx.close();
}

await browser.close();
writeFileSync(join(OUT, 'ohh-route-audit.json'), JSON.stringify(report, null, 1));
console.log(`\n${report.failures === 0 ? 'PASS' : 'FAIL'} — OHH route audit (${report.failures} failures) → ${OUT}/ohh-route-audit.json`);
process.exit(report.failures === 0 ? 0 : 1);
