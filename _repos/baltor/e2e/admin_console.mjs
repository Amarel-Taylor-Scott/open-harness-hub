/* e2e/admin_console.mjs — prove the ADMIN CONSOLE grants reviewers, end to end, with real accounts.
   A contributor submits a candidate and is gated out of /admin ("no admin access"). An OPERATOR
   bootstraps a separate account as admin via the CLI (admin status is never self-served). That admin,
   through the in-app console, grants the contributor reviewer access — and the reviewer roster updates
   live. Video + stills. Honest: real accounts, real operator bootstrap, real in-console grant. */
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';
import { launchGate, attachCollectors, saveJSON, saveText, DIRS, HAS_NATIVE_VIDEO, finalizeNativeVideo, FlowRecorder } from './gate_common.mjs';

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const BASE = 'http://127.0.0.1:9210/opencontexthub/' + encodeURIComponent('OpenContextHub.html');
const REALM = 'opencontexthub';
const TS = Date.now();
const candName = 'E2E Admin Pack ' + TS;
const contribEmail = `contrib+${TS}@aidoneright.dev`;
const adminEmail = `admin+${TS}@aidoneright.dev`;
const pass = `admin-${TS.toString(36)}`;
const steps = [];
let n = 0;
const { browser, context } = await launchGate();
const page = await context.newPage();
const log = attachCollectors(page);
const rec = HAS_NATIVE_VIDEO ? null : new FlowRecorder(page, 'admin-console').start();

async function stage(label, fn) {
  n += 1; let ok = true; let detail = '';
  try { detail = (await fn()) || ''; } catch (e) { ok = false; detail = String(e).split('\n')[0].slice(0, 160); }
  await page.waitForTimeout(700); await rec?.snap();
  await page.screenshot({ path: join(DIRS.screenshots, `admin-${String(n).padStart(2, '0')}-${label}.png`) });
  steps.push({ n, label, ok, detail });
  console.log(`  [${ok ? 'ok' : 'FAIL'}] ${label}${ok ? '' : ' — ' + detail}`);
}
async function signUp(email) {
  await page.goto(BASE + '#/signup', { waitUntil: 'load' }); await page.waitForTimeout(1200);
  await page.waitForSelector('input[type="email"]', { timeout: 8000 });
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', pass);
  const nameI = await page.$('input:not([type])'); if (nameI) await nameI.fill('E2E User').catch(() => {});
  await page.getByText('Create account', { exact: false }).first().click({ timeout: 5000 });
  await page.waitForFunction(() => location.hash.startsWith('#/dashboard'), { timeout: 12000 });
  const sess = await page.evaluate((r) => JSON.parse(localStorage.getItem('oh-session-' + r) || 'null'), REALM);
  if (!sess || !sess.account_id) throw new Error('no session/account minted');
  return sess.account_id;
}

let contribAcct = '';
await stage('contributor-submits', async () => {
  contribAcct = await signUp(contribEmail);
  await page.goto(BASE + '#/publish', { waitUntil: 'load' }); await page.waitForTimeout(1200);
  await page.getByLabel('Name', { exact: true }).fill(candName);
  await page.getByText('Submit for review', { exact: false }).first().click({ timeout: 5000 });
  await page.waitForSelector('text=in review', { timeout: 8000 });
  return `contributor ${contribAcct.slice(0, 14)}… submitted a candidate`;
});

await stage('contributor-has-no-admin-access', async () => {
  await page.goto(BASE + '#/admin', { waitUntil: 'load' }); await page.waitForTimeout(1400);
  const txt = (await page.evaluate(() => document.body.innerText)).toLowerCase();
  if (!txt.includes('admin access')) throw new Error('contributor was not gated out of the admin console');
  return 'a non-admin is gated: "You don’t have admin access" — the controls are hidden';
});

let adminAcct = '';
await stage('register-separate-admin', async () => {
  adminAcct = await signUp(adminEmail);    // overwrites the realm session — now the admin-to-be
  return `separate admin account ${adminAcct.slice(0, 14)}… registered`;
});

await stage('operator-bootstraps-admin', async () => {
  // the ROOT of trust — admin status is operator-bootstrapped only, never set from inside the app.
  const out = execSync(`python3 -m scripts.registry_local_service --grant-admin ${REALM} ${adminAcct}`,
    { cwd: REPO_ROOT, encoding: 'utf-8' });
  return out.trim().split('\n').slice(-1)[0];
});

await stage('admin-grants-reviewer', async () => {
  await page.goto(BASE + '#/admin', { waitUntil: 'load' }); await page.waitForTimeout(1600);
  await page.waitForSelector('text=Grant a reviewer', { timeout: 8000 });   // admin console rendered
  // grant the contributor via their row in "Recent contributors" (newest first → our contributor).
  const row = page.locator('tr', { hasText: contribAcct.slice(0, 18) }).first();
  await row.getByText('Grant', { exact: true }).click({ timeout: 6000 });
  await page.waitForSelector('text=Granted reviewer', { timeout: 8000 });
  // confirm through the client: the reviewer roster now contains the contributor
  const isRev = await page.evaluate((args) => window.OHRegistry.adminReviewers(args.r).then(
    (d) => !!(d && d.reviewers && d.reviewers.indexOf(args.a) >= 0)), { r: REALM, a: contribAcct });
  if (!isRev) throw new Error('the contributor was not added to the reviewer roster');
  return `admin granted reviewer → ${contribAcct.slice(0, 14)}… is now in the reviewer roster`;
});

const handle = HAS_NATIVE_VIDEO ? page.video() : null;
const gif = rec ? await rec.stop() : null;
await page.close(); await context.close(); await browser.close();
const native = handle ? await finalizeNativeVideo(handle, 'admin-console') : null;
const video = native ? (native.mp4 || native.webm) : gif?.file;

const report = { generated_at: new Date().toISOString(), gate: 'admin_console', surface: BASE, realm: REALM,
  admin_account: adminAcct, granted_reviewer: contribAcct, ok: steps.every((s) => s.ok), steps, page_errors: log.pageErrors,
  video: video ? `videos/${video}` : 'HELD',
  note: 'The admin console end to end: a non-admin is gated out → an operator bootstraps an admin → that admin grants a contributor reviewer access in-app → the reviewer roster updates live. Admin status is operator-rooted; the console grants reviewers only.' };
saveJSON('reports', 'admin-console-report.json', report);
saveText('reports', 'admin-console-report.md', [
  `# Admin console × real accounts — ${report.generated_at}`, '',
  `Surface: ${BASE} · Realm: ${REALM} · Result: **${report.ok ? 'PASS' : 'FAIL'}**`, '',
  '| # | stage | ok | detail |', '|---|---|---|---|',
  ...steps.map((s) => `| ${s.n} | ${s.label} | ${s.ok ? 'ok' : 'FAIL'} | ${s.detail} |`),
  '', `Video: \`artifacts/e2e/${report.video}\``,
].join('\n'));
console.log(`\nadmin-console: ${report.ok ? 'PASS' : 'FAIL'} → reports/admin-console-report.md · ${report.video}`);
process.exit(report.ok ? 0 : 1);
