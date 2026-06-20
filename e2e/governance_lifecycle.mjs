/* e2e/governance_lifecycle.mjs — the FULL reviewer lifecycle in one video: approve + reject + revoke.
   A publisher submits two candidates. A separate operator-granted reviewer APPROVES one (it goes live
   in Browse), REJECTS the other (it never goes live), then REVOKES the approved one (it rolls back out
   of Browse — losslessly; the decision is recorded, the candidate preserved). Video + stills. */
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';
import { launchGate, attachCollectors, saveJSON, saveText, DIRS, HAS_NATIVE_VIDEO, finalizeNativeVideo, FlowRecorder } from './gate_common.mjs';

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const BASE = 'http://127.0.0.1:9210/opencontexthub/' + encodeURIComponent('OpenContextHub Prototype.html');
const REALM = 'opencontexthub';
const TS = Date.now();
const nameA = 'Approve Me ' + TS;       // will be promoted then revoked
const nameB = 'Reject Me ' + TS;        // will be rejected
const pass = `gov-${TS.toString(36)}`;
const steps = [];
let n = 0;
const { browser, context } = await launchGate();
const page = await context.newPage();
const log = attachCollectors(page);
const rec = HAS_NATIVE_VIDEO ? null : new FlowRecorder(page, 'governance-lifecycle').start();

async function stage(label, fn) {
  n += 1; let ok = true; let detail = '';
  try { detail = (await fn()) || ''; } catch (e) { ok = false; detail = String(e).split('\n')[0].slice(0, 160); }
  await page.waitForTimeout(650); await rec?.snap();
  await page.screenshot({ path: join(DIRS.screenshots, `gov-${String(n).padStart(2, '0')}-${label}.png`) });
  steps.push({ n, label, ok, detail });
  console.log(`  [${ok ? 'ok' : 'FAIL'}] ${label}${ok ? '' : ' — ' + detail}`);
}
async function signUp(email) {
  await page.goto(BASE + '#/signup', { waitUntil: 'load' }); await page.waitForTimeout(1100);
  await page.waitForSelector('input[type="email"]', { timeout: 8000 });
  await page.fill('input[type="email"]', email); await page.fill('input[type="password"]', pass);
  const nameI = await page.$('input:not([type])'); if (nameI) await nameI.fill('Gov User').catch(() => {});
  await page.getByText('Create account', { exact: false }).first().click({ timeout: 5000 });
  await page.waitForFunction(() => location.hash.startsWith('#/dashboard'), { timeout: 12000 });
  return page.evaluate((r) => JSON.parse(localStorage.getItem('oh-session-' + r) || 'null').account_id, REALM);
}
async function submit(nm) {
  await page.goto(BASE + '#/publish', { waitUntil: 'load' }); await page.waitForTimeout(1000);
  await page.getByLabel('Name', { exact: true }).fill(nm);
  await page.getByText('Submit for review', { exact: false }).first().click({ timeout: 5000 });
  await page.waitForSelector('text=in review', { timeout: 8000 });
}
const inBrowse = (nm) => page.evaluate((a) => window.OHRegistry.search(a.r).then((es) => !!(es && es.some((e) => e.name === a.n))), { r: REALM, n: nm });
const inQueue = (nm) => page.evaluate((a) => window.OHRegistry.reviewQueue(a.r).then((q) => !!(q && q.some((e) => e.name === a.n))), { r: REALM, n: nm });

await stage('publisher-submits-two', async () => {
  await signUp(`gpub+${TS}@aidoneright.dev`);
  await submit(nameA); await submit(nameB);
  if (await inBrowse(nameA) || await inBrowse(nameB)) throw new Error('a candidate leaked into Browse pre-review');
  return 'submitted two candidates — both in review, neither in Browse';
});

let reviewer = '';
await stage('operator-grants-reviewer', async () => {
  reviewer = await signUp(`grev+${TS}@aidoneright.dev`);
  const out = execSync(`python3 -m scripts.registry_local_service --grant-reviewer ${REALM} ${reviewer}`, { cwd: REPO_ROOT, encoding: 'utf-8' });
  return out.trim().split('\n').slice(-1)[0];
});

await stage('reviewer-approves-A', async () => {
  await page.goto(BASE + '#/review', { waitUntil: 'load' }); await page.waitForTimeout(1500);
  await page.waitForSelector('text=Approve & promote', { timeout: 8000 });
  await page.locator('.oh-card', { hasText: nameA }).first().getByText('Approve & promote').click({ timeout: 6000 });
  await page.waitForSelector('text=promoted to the catalog', { timeout: 8000 });
  await page.waitForTimeout(800);
  if (!(await inBrowse(nameA))) throw new Error('A not promoted to Browse');
  return `approved "${nameA}" → now live in Browse`;
});

await stage('reviewer-rejects-B', async () => {
  await page.locator('.oh-card', { hasText: nameB }).first().getByText('Reject', { exact: true }).click({ timeout: 6000 });
  await page.waitForTimeout(1200);
  if (await inBrowse(nameB)) throw new Error('rejected B leaked into Browse');
  if (await inQueue(nameB)) throw new Error('rejected B still pending');
  return `rejected "${nameB}" → never public-active, left the queue (candidate preserved)`;
});

await stage('reviewer-revokes-A', async () => {
  // A is in the "Promoted & live — revertable" section; revoke rolls it back out of Browse.
  await page.locator('.oh-card', { hasText: 'revertable' }).getByRole('row', { name: new RegExp(nameA.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) })
    .getByText('Revoke').click({ timeout: 6000 }).catch(async () => {
      // fallback: click the Revoke in the row containing A's name
      await page.locator('tr', { hasText: nameA }).first().getByText('Revoke').click({ timeout: 6000 });
    });
  await page.waitForTimeout(1200);
  if (await inBrowse(nameA)) throw new Error('revoked A still in Browse');
  return `revoked "${nameA}" → rolled back out of Browse (lossless — decision recorded)`;
});

const handle = HAS_NATIVE_VIDEO ? page.video() : null;
const gif = rec ? await rec.stop() : null;
await page.close(); await context.close(); await browser.close();
const native = handle ? await finalizeNativeVideo(handle, 'governance-lifecycle') : null;
const video = native ? (native.mp4 || native.webm) : gif?.file;

const report = { generated_at: new Date().toISOString(), gate: 'governance_lifecycle', surface: BASE, realm: REALM,
  reviewer, ok: steps.every((s) => s.ok), steps, page_errors: log.pageErrors, video: video ? `videos/${video}` : 'HELD',
  note: 'The full reviewer lifecycle: approve (→ live), reject (→ never live), revoke (→ rolled back), all through the UI, all recorded losslessly.' };
saveJSON('reports', 'governance-lifecycle-report.json', report);
saveText('reports', 'governance-lifecycle-report.md', [
  `# Governance lifecycle — approve · reject · revoke — ${report.generated_at}`, '',
  `Surface: ${BASE} · Realm: ${REALM} · Result: **${report.ok ? 'PASS' : 'FAIL'}**`, '',
  '| # | stage | ok | detail |', '|---|---|---|---|',
  ...steps.map((s) => `| ${s.n} | ${s.label} | ${s.ok ? 'ok' : 'FAIL'} | ${s.detail} |`),
  '', `Video: \`artifacts/e2e/${report.video}\``,
].join('\n'));
console.log(`\ngovernance-lifecycle: ${report.ok ? 'PASS' : 'FAIL'} → reports/governance-lifecycle-report.md · ${report.video}`);
process.exit(report.ok ? 0 : 1);
