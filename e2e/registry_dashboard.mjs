/* e2e/registry_dashboard.mjs — prove the full-design dashboard shows REAL registry data.
   The acid test mock data can't pass: a NEW account's dashboard starts at Installed 0; we install a
   real entry through the UI ("+ Add to workspace"), and the dashboard number CHANGES to 1 with a real
   activity row — because it's reading the per-account workspace from the registry plane (:9423), which
   resolved the account by validating the realm session against the identity service (:9410).
   Video + stills. Honest: real account, real session, real install, real numbers. */
import { join } from 'node:path';
import { launchGate, attachCollectors, saveJSON, saveText, DIRS, HAS_NATIVE_VIDEO, finalizeNativeVideo, FlowRecorder } from './gate_common.mjs';

const BASE = 'http://127.0.0.1:9210/opencontexthub/' + encodeURIComponent('OpenContextHub Prototype.html');
const REALM = 'opencontexthub';
const ENTRY_ID = 'ilo-forced-labour';
const TS = Date.now();
const email = `registry+${TS}@aidoneright.dev`;
const pass = `registry-${TS.toString(36)}`;
const steps = [];
let n = 0;
const { browser, context } = await launchGate();
const page = await context.newPage();
const log = attachCollectors(page);
const rec = HAS_NATIVE_VIDEO ? null : new FlowRecorder(page, 'registry-dashboard').start();

async function stage(label, fn) {
  n += 1; let ok = true; let detail = '';
  try { detail = (await fn()) || ''; } catch (e) { ok = false; detail = String(e).split('\n')[0].slice(0, 160); }
  await page.waitForTimeout(700); await rec?.snap();
  await page.screenshot({ path: join(DIRS.screenshots, `registry-${String(n).padStart(2, '0')}-${label}.png`) });
  steps.push({ n, label, ok, detail });
  console.log(`  [${ok ? 'ok' : 'FAIL'}] ${label}${ok ? '' : ' — ' + detail}`);
}
// the dashboard summary AS THE UI SEES IT — calls the real client against the registry plane.
const installedCount = () => page.evaluate((r) => window.OHRegistry.workspace(r).then((w) => (w && w.installed ? w.installed.length : -1)), REALM);

await stage('landing', async () => { await page.goto(BASE, { waitUntil: 'load', timeout: 20000 }); await page.waitForTimeout(1200); return 'OpenContextHub — full design, live registry backend'; });

await stage('register-real-account', async () => {
  await page.goto(BASE + '#/signup', { waitUntil: 'load' }); await page.waitForTimeout(1400);
  await page.waitForSelector('input[type="email"]', { timeout: 8000 });
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', pass);
  const nameI = await page.$('input:not([type])'); if (nameI) await nameI.fill('Grace Hopper').catch(() => {});
  await page.getByText('Create account', { exact: false }).first().click({ timeout: 5000 });
  await page.waitForFunction(() => location.hash.startsWith('#/dashboard'), { timeout: 12000 });
  const sess = await page.evaluate((r) => JSON.parse(localStorage.getItem('oh-session-' + r) || 'null'), REALM);
  if (!sess || !String(sess.session_id).startsWith('sess_')) throw new Error('no real session minted');
  return `real account in ${REALM} — session ${String(sess.session_id).slice(0, 12)}…`;
});

await stage('dashboard-starts-empty', async () => {
  await page.waitForTimeout(1500);                 // let the workspace fetch settle
  const c = await installedCount();
  if (c !== 0) throw new Error(`expected a fresh account to show Installed 0, the registry returned ${c}`);
  return 'a brand-new account shows REAL Installed 0 (mock data would show the seeded count)';
});

await stage('open-entry', async () => {
  await page.goto(BASE + '#/e/' + ENTRY_ID, { waitUntil: 'load' }); await page.waitForTimeout(1200);
  await page.waitForSelector('text=Add to workspace', { timeout: 8000 });
  return 'ILO Forced Labour Standards — entry detail';
});

await stage('add-to-workspace', async () => {
  await page.getByText('Add to workspace', { exact: false }).first().click({ timeout: 5000 });
  await page.waitForSelector('text=Added to workspace', { timeout: 8000 });   // button flips on a real 202
  const c = await installedCount();
  if (c !== 1) throw new Error(`after install the registry should report 1 installed, got ${c}`);
  return 'REAL install recorded — registry workspace now reports Installed 1';
});

await stage('browse-from-registry', async () => {
  await page.goto(BASE + '#/browse', { waitUntil: 'load' }); await page.waitForTimeout(1600);
  // the registry catalog count, and the rendered grid count — Browse uses the catalog when up, so
  // an unfiltered grid should render exactly the registry's entry count (proves the source switched).
  const catN = await page.evaluate((r) => window.OHRegistry.search(r).then((es) => (es ? es.length : -1)), REALM);
  const gridN = await page.evaluate(() => document.querySelectorAll('.ohub-card').length);
  if (catN < 1) throw new Error(`registry catalog returned ${catN} entries`);
  if (gridN !== catN) throw new Error(`Browse grid (${gridN}) does not match the registry catalog (${catN})`);
  return `Browse renders ${gridN} cards straight from the registry catalog`;
});

await stage('publish-to-review-queue', async () => {
  await page.goto(BASE + '#/publish', { waitUntil: 'load' }); await page.waitForTimeout(1400);
  await page.waitForSelector('text=Submit for review', { timeout: 8000 });
  await page.getByLabel('Name', { exact: true }).fill('My Sanctions Pack ' + TS);
  await page.getByLabel('Description', { exact: true }).fill('A candidate submitted through the publish UI.').catch(() => {});
  await page.getByText('Submit for review', { exact: false }).first().click({ timeout: 5000 });
  await page.waitForSelector('text=in review', { timeout: 8000 });   // success banner + submissions badge
  // prove it through the client: the review queue now holds an in_review candidate (never active)
  const subN = await page.evaluate((r) => window.OHRegistry.submissions(r).then((s) => (s ? s.filter((x) => x.status === 'in_review').length : -1)), REALM);
  if (subN < 1) throw new Error(`expected ≥1 in_review submission, got ${subN}`);
  return `submitted a candidate → ${subN} in the review queue (in_review, not Browse-active)`;
});

await stage('dashboard-shows-real-numbers', async () => {
  await page.goto(BASE + '#/dashboard', { waitUntil: 'load' }); await page.waitForTimeout(1600);
  const seen = await page.evaluate(() => document.body.innerText);
  const ws = await page.evaluate((r) => window.OHRegistry.workspace(r), REALM);
  const stat = Object.fromEntries(ws.stats);
  const hasActivity = /Installed\s+ILO Forced Labour/i.test(seen);
  if (stat.Installed !== 1) throw new Error(`dashboard Installed should be 1, got ${stat.Installed}`);
  if (stat.Published < 1) throw new Error(`dashboard Published should be ≥1, got ${stat.Published}`);
  if (!hasActivity) throw new Error('dashboard activity does not show the real install');
  return `dashboard shows REAL Installed ${stat.Installed} · Published ${stat.Published} + a real activity row`;
});

const handle = HAS_NATIVE_VIDEO ? page.video() : null;
const gif = rec ? await rec.stop() : null;
await page.close(); await context.close(); await browser.close();
const native = handle ? await finalizeNativeVideo(handle, 'registry-dashboard') : null;
const video = native ? (native.mp4 || native.webm) : gif?.file;

const report = { generated_at: new Date().toISOString(), gate: 'registry_dashboard', surface: BASE, realm: REALM, entry: ENTRY_ID,
  ok: steps.every((s) => s.ok), steps, page_errors: log.pageErrors, video: video ? `videos/${video}` : 'HELD',
  note: 'The full-design dashboard reading REAL per-account registry data: a fresh account shows Installed 0, a real install through the UI moves it to 1 with a real activity row.' };
saveJSON('reports', 'registry-dashboard-report.json', report);
saveText('reports', 'registry-dashboard-report.md', [
  `# Registry-backed dashboard × real data — ${report.generated_at}`, '',
  `Surface: ${BASE} · Realm: ${REALM} · Result: **${report.ok ? 'PASS' : 'FAIL'}**`, '',
  '| # | stage | ok | detail |', '|---|---|---|---|',
  ...steps.map((s) => `| ${s.n} | ${s.label} | ${s.ok ? 'ok' : 'FAIL'} | ${s.detail} |`),
  '', `Video: \`artifacts/e2e/${report.video}\``,
].join('\n'));
console.log(`\nregistry-dashboard: ${report.ok ? 'PASS' : 'FAIL'} → reports/registry-dashboard-report.md · ${report.video}`);
process.exit(report.ok ? 0 : 1);
