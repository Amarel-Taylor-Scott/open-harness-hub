// e2e/family_surfaces_gate.mjs — EVERY remaining family surface, verified: the 21+ Open*Hub
// registries (live + private bench), the internal planes (Shared Inference Gateway, Shared
// Template Registry), and the Design Acceptance Scorecard. Served via the bundle root mounts on
// the parent app origin (web/ apps' showcase server).
//
// Checks per hub: renders console-clean · #/browse grid renders · private-preview banner
// presence matches shared/products.js (counts derived from source, never hand-typed) · plus one
// REAL registry install on a live hub (session-gated through the registry service).
//
// Run: node e2e/family_surfaces_gate.mjs [base]   (default http://127.0.0.1:8002)

import { chromium } from 'playwright';
import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE = (process.argv[2] || 'http://127.0.0.1:8002').replace(/\/+$/, '');
const HERE = dirname(fileURLToPath(import.meta.url));
const BUNDLE = join(HERE, '..', 'dist', 'sites', 'openharness-design');
const OUT = join(HERE, 'artifacts', 'full-design');
const EXPECTED = [/in-browser Babel transformer/i, /React DevTools/i];

// surfaces from disk (the bundle is the source of truth); openharnesshub is the bespoke product
// surface with its own dedicated gate (e2e/ohh_route_audit.mjs — 46 routes), not a makeHub site
const hubFolders = readdirSync(BUNDLE, { withFileTypes: true })
  .filter((d) => d.isDirectory() && /^open.+hub$|^openskilltotool$/.test(d.name) && d.name !== 'openharnesshub')
  .map((d) => d.name).sort();
const entryOf = (folder) => readdirSync(join(BUNDLE, folder)).find((f) => / Prototype\.html$/.test(f));
const PLANES = [
  ['inference-gateway', 'Shared Inference Gateway.html'],
  ['template-registry', 'Shared Template Registry.html'],
];
// expected private/live split derived PER ENTITY from products.js (a hub is private when its
// entity block carries status: 'private'), never hand-typed
const productsJs = readFileSync(join(BUNDLE, 'shared', 'products.js'), 'utf-8');
const privateHubs = hubFolders.filter((folder) => {
  const at = productsJs.indexOf(`'../${folder}/`);
  if (at === -1) return false;
  const block = productsJs.slice(Math.max(0, at - 600), at + 600);
  return /status: 'private'/.test(block);
});
const expectedPrivate = privateHubs.length;
const expectedLive = hubFolders.length - expectedPrivate;

const checks = [];
let failures = 0;
const check = (name, ok, detail = '') => {
  checks.push({ name, ok, detail });
  console.log(`  [${ok ? 'ok' : 'FAIL'}] ${name}${detail && !ok ? ' — ' + detail : ''}`);
  if (!ok) failures += 1;
};

const browser = await chromium.launch({ channel: 'chrome' });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });

console.log(`family gate → ${BASE} · ${hubFolders.length} hubs (${expectedPrivate} private per products.js) + ${PLANES.length} planes + scorecard\n`);

let banners = 0;
const hubResults = [];
for (const folder of hubFolders) {
  const entry = entryOf(folder);
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', (m) => { if (m.type() === 'error' && !EXPECTED.some((re) => re.test(m.text()))) errs.push(m.text().slice(0, 120)); });
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 120)));
  await page.goto(`${BASE}/${encodeURIComponent(folder)}/${encodeURIComponent(entry)}`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2400);
  const landing = await page.evaluate(() => ({
    len: document.body.innerText.length,
    banner: /Private preview/i.test(document.body.innerText),
  }));
  await page.evaluate(() => { window.location.hash = '/browse'; });
  await page.waitForTimeout(900);
  const browse = await page.evaluate(() => document.querySelectorAll('.oh-card, .ohub-grid > *').length);
  const ok = landing.len > 300 && errs.length === 0 && browse > 0;
  hubResults.push({ folder, ok, banner: landing.banner, browse, errs: errs.slice(0, 2) });
  if (landing.banner) banners += 1;
  if (!ok) check(`${folder}: renders + browse + console-clean`, false, `${errs[0] || 'len:' + landing.len + ' browse:' + browse}`);
  await page.close();
}
check(`all ${hubFolders.length} hubs render console-clean with a working browse grid`, hubResults.every((h) => h.ok),
  hubResults.filter((h) => !h.ok).map((h) => h.folder).join(', '));
check(`private-preview banners match products.js (${expectedPrivate} private / ${expectedLive} live)`,
  banners === expectedPrivate, `saw ${banners} banners`);

// internal planes + scorecard
for (const [folder, entry] of PLANES) {
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', (m) => { if (m.type() === 'error' && !EXPECTED.some((re) => re.test(m.text()))) errs.push(m.text().slice(0, 120)); });
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 120)));
  await page.goto(`${BASE}/${encodeURIComponent(folder)}/${encodeURIComponent(entry)}`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2200);
  check(`${folder}: renders console-clean`,
    await page.evaluate(() => document.body.innerText.length > 300) && errs.length === 0, errs[0] || '');
  await page.close();
}
{
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 120)));
  // the scorecard lives at the bundle ROOT — reachable through the /design mount
  await page.goto(`${BASE}/design/${encodeURIComponent('Design Acceptance Scorecard.html')}`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
  check('Design Acceptance Scorecard renders', await page.evaluate(() => /Scorecard|family/i.test(document.body.innerText)) && errs.length === 0, errs[0] || '');
  await page.screenshot({ path: join(OUT, 'family-scorecard.png') });
  await page.close();
}

// one REAL registry install on a live hub (opencontexthub) — session-gated end to end
{
  const page = await ctx.newPage();
  await page.goto(`${BASE}/opencontexthub/${encodeURIComponent(entryOf('opencontexthub'))}#/signup`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2600);
  await page.locator('input[type="email"], input[placeholder*="mail" i]').first().fill(`family-gate-${Date.now()}@example.test`);
  await page.locator('input[type="password"]').first().fill('family-gate-pass');
  await page.locator('button:has-text("Create"), button[type="submit"]').first().click();
  await page.waitForTimeout(3600);
  const installed = await page.evaluate(async () => {
    const entries = await window.OHRegistry.search('opencontexthub', '');
    if (!entries || !entries.length) return { step: 'search', ok: false };
    const res = await window.OHRegistry.install('opencontexthub', entries[0]);
    if (!res.ok) return { step: 'install', ok: false };
    const ws = await window.OHRegistry.workspace('opencontexthub');
    return { step: 'workspace', ok: !!(ws && ws.installed && ws.installed.length >= 1), entry: entries[0].id || entries[0].name };
  });
  check('REAL registry install on a live hub (search → install → workspace)', installed.ok, JSON.stringify(installed));
  await page.close();
}

await ctx.close();
await browser.close();
writeFileSync(join(OUT, 'family-surfaces-gate.json'), JSON.stringify({ base: BASE, hubs: hubResults, checks, failures, at: new Date().toISOString() }, null, 1));
console.log(`\n${failures === 0 ? 'PASS' : 'FAIL'} — family surfaces gate (${checks.length} rolled-up checks over ${hubFolders.length + PLANES.length + 2} surfaces, ${failures} failures)`);
process.exit(failures === 0 ? 0 : 1);
