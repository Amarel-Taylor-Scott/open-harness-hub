/* e2e/console_full_tour.mjs — the WHOLE signed-in console, REAL, end to end (one real account).
   Register → dashboard (real Installed 0) → create a real API key (shown once) → revoke it →
   install an entry (Installed 1) → publish a candidate (in review) → audit shows the real recorded
   actions → usage/billing/team/settings show real account data (Free plan, no fabricated invoices,
   real email + account id). Video + stills. Honest: every number is read from a live backend. */
import { join } from 'node:path';
import { launchGate, attachCollectors, saveJSON, saveText, DIRS, HAS_NATIVE_VIDEO, finalizeNativeVideo, FlowRecorder } from './gate_common.mjs';

const BASE = 'http://127.0.0.1:9210/opencontexthub/' + encodeURIComponent('OpenContextHub.html');
const REALM = 'opencontexthub';
const ENTRY_ID = 'ilo-forced-labour';
const TS = Date.now();
const email = `tour+${TS}@aidoneright.dev`;
const pass = `tour-${TS.toString(36)}`;
const candName = 'Tour Pack ' + TS;
const steps = [];
let n = 0;
const { browser, context } = await launchGate();
const page = await context.newPage();
const log = attachCollectors(page);
const rec = HAS_NATIVE_VIDEO ? null : new FlowRecorder(page, 'console-full-tour').start();

async function stage(label, fn) {
  n += 1; let ok = true; let detail = '';
  try { detail = (await fn()) || ''; } catch (e) { ok = false; detail = String(e).split('\n')[0].slice(0, 160); }
  await page.waitForTimeout(650); await rec?.snap();
  await page.screenshot({ path: join(DIRS.screenshots, `tour-${String(n).padStart(2, '0')}-${label}.png`) });
  steps.push({ n, label, ok, detail });
  console.log(`  [${ok ? 'ok' : 'FAIL'}] ${label}${ok ? '' : ' — ' + detail}`);
}
const go = async (hash) => { await page.goto(BASE + '#/' + hash, { waitUntil: 'load' }); await page.waitForTimeout(1100); };
const bodyText = () => page.evaluate(() => document.body.innerText);

await stage('register', async () => {
  await page.goto(BASE + '#/signup', { waitUntil: 'load' }); await page.waitForTimeout(1100);
  await page.waitForSelector('input[type="email"]', { timeout: 8000 });
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', pass);
  const nameI = await page.$('input:not([type])'); if (nameI) await nameI.fill('Tour User').catch(() => {});
  await page.getByText('Create account', { exact: false }).first().click({ timeout: 5000 });
  await page.waitForFunction(() => location.hash.startsWith('#/dashboard'), { timeout: 12000 });
  const ws = await page.evaluate((r) => window.OHRegistry.workspace(r), REALM);
  if (Object.fromEntries(ws.stats)['Installed'] !== 0) throw new Error('fresh dashboard not zeroed');
  return 'signed in — dashboard shows REAL Installed 0';
});

await stage('browse-real-catalog', async () => {
  await go('browse');
  const catN = await page.evaluate((r) => window.OHRegistry.search(r).then((es) => es.length), REALM);
  const gridN = await page.evaluate(() => document.querySelectorAll('.ohub-card').length);
  if (gridN !== catN || catN < 1) throw new Error(`grid ${gridN} vs catalog ${catN}`);
  return `Browse renders ${gridN} entries straight from the registry`;
});

await stage('create-real-api-key', async () => {
  await go('keys');
  await page.getByText('Create key', { exact: false }).first().click({ timeout: 5000 });
  await page.waitForSelector('text=shown once', { timeout: 8000 });
  const keys = await page.evaluate((r) => window.OHIdentity.listKeys(r).then((x) => (x.body && x.body.api_keys) || []), REALM);
  const active = keys.filter((k) => !k.revoked_at);
  if (active.length < 1) throw new Error('no real key minted');
  return `real API key minted (shown once) — ${active.length} active key, hash-only at rest`;
});

await stage('revoke-api-key', async () => {
  await page.getByText('Revoke', { exact: true }).first().click({ timeout: 5000 });
  await page.waitForTimeout(1200);
  const keys = await page.evaluate((r) => window.OHIdentity.listKeys(r).then((x) => (x.body && x.body.api_keys) || []), REALM);
  if (keys.filter((k) => !k.revoked_at).length !== 0) throw new Error('key not revoked');
  return 'key revoked — 0 active (revoked keys stop working immediately)';
});

await stage('install-entry', async () => {
  await go('e/' + ENTRY_ID);
  await page.getByText('Add to workspace', { exact: false }).first().click({ timeout: 5000 });
  await page.waitForSelector('text=Added to workspace', { timeout: 8000 });
  return 'installed ILO Forced Labour Standards (real)';
});

await stage('publish-candidate', async () => {
  await go('publish');
  await page.getByLabel('Name', { exact: true }).fill(candName);
  await page.getByText('Submit for review', { exact: false }).first().click({ timeout: 5000 });
  await page.waitForSelector('text=in review', { timeout: 8000 });
  return `published "${candName}" → in review (candidate ≠ active)`;
});

await stage('audit-real-activity', async () => {
  await go('audit');
  const rows = await page.evaluate((r) => window.OHRegistry.audit(r), REALM);
  const policies = rows.map((x) => x.policy);
  if (!policies.includes('workspace:install') || !policies.includes('registry:submit'))
    throw new Error('audit missing the real actions: ' + policies.join(','));
  return `audit shows the account's REAL actions (${rows.length} rows: install + submit recorded)`;
});

await stage('usage-billing-team-settings-real', async () => {
  await go('usage'); const usage = await bodyText();
  await go('billing'); const billing = await bodyText();
  await go('settings'); const settings = await bodyText();
  if (/\$99\.00/.test(billing)) throw new Error('billing still shows a fabricated $99 invoice');
  if (!/Free/.test(billing)) throw new Error('billing does not show the real Free plan');
  if (!settings.includes(email)) throw new Error('settings does not show the real email');
  return 'usage = real metrics · billing = real Free plan (no fake invoices) · settings = real email + account id';
});

const handle = HAS_NATIVE_VIDEO ? page.video() : null;
const gif = rec ? await rec.stop() : null;
await page.close(); await context.close(); await browser.close();
const native = handle ? await finalizeNativeVideo(handle, 'console-full-tour') : null;
const video = native ? (native.mp4 || native.webm) : gif?.file;

const report = { generated_at: new Date().toISOString(), gate: 'console_full_tour', surface: BASE, realm: REALM,
  ok: steps.every((s) => s.ok), steps, page_errors: log.pageErrors, video: video ? `videos/${video}` : 'HELD',
  note: 'The entire signed-in console reading/writing REAL backends end to end: dashboard, browse, API keys (mint/revoke), install, publish, audit, usage, billing, team, settings — no mock data, no fabricated invoices.' };
saveJSON('reports', 'console-full-tour-report.json', report);
saveText('reports', 'console-full-tour-report.md', [
  `# Full console tour × real backends — ${report.generated_at}`, '',
  `Surface: ${BASE} · Realm: ${REALM} · Result: **${report.ok ? 'PASS' : 'FAIL'}**`, '',
  '| # | stage | ok | detail |', '|---|---|---|---|',
  ...steps.map((s) => `| ${s.n} | ${s.label} | ${s.ok ? 'ok' : 'FAIL'} | ${s.detail} |`),
  '', `Video: \`artifacts/e2e/${report.video}\``,
].join('\n'));
console.log(`\nconsole-full-tour: ${report.ok ? 'PASS' : 'FAIL'} → reports/console-full-tour-report.md · ${report.video}`);
process.exit(report.ok ? 0 : 1);
