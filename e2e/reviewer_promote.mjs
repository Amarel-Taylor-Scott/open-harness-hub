/* e2e/reviewer_promote.mjs — prove the PROMOTION GATE end to end with two real accounts.
   A publisher submits a candidate (in_review, NOT in Browse). The publisher visiting /review sees
   "no reviewer access" (gating). An OPERATOR grants a separate account reviewer status via the CLI
   (reviewer status is never self-served). That reviewer approves the candidate through the UI, and it
   then appears in Browse as a public-active entry with provenance lineage. Video + stills. Honest:
   real accounts, real session, real operator grant, real promotion — the only candidate→active path. */
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';
import { launchGate, attachCollectors, saveJSON, saveText, DIRS, HAS_NATIVE_VIDEO, finalizeNativeVideo, FlowRecorder } from './gate_common.mjs';

const REPO_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const BASE = 'http://127.0.0.1:9210/opencontexthub/' + encodeURIComponent('OpenContextHub Prototype.html');
const REALM = 'opencontexthub';
const TS = Date.now();
const candName = 'E2E Promote Pack ' + TS;
const pubEmail = `pub+${TS}@aidoneright.dev`;
const revEmail = `rev+${TS}@aidoneright.dev`;
const pass = `promote-${TS.toString(36)}`;
const steps = [];
let n = 0;
const { browser, context } = await launchGate();
const page = await context.newPage();
const log = attachCollectors(page);
const rec = HAS_NATIVE_VIDEO ? null : new FlowRecorder(page, 'reviewer-promote').start();

async function stage(label, fn) {
  n += 1; let ok = true; let detail = '';
  try { detail = (await fn()) || ''; } catch (e) { ok = false; detail = String(e).split('\n')[0].slice(0, 160); }
  await page.waitForTimeout(700); await rec?.snap();
  await page.screenshot({ path: join(DIRS.screenshots, `promote-${String(n).padStart(2, '0')}-${label}.png`) });
  steps.push({ n, label, ok, detail });
  console.log(`  [${ok ? 'ok' : 'FAIL'}] ${label}${ok ? '' : ' — ' + detail}`);
}
// register + sign in a fresh account in this realm through the kit's real client; returns account_id.
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
const searchHasCand = () => page.evaluate((args) => window.OHRegistry.search(args.r).then((es) => !!(es && es.some((e) => e.name === args.n))), { r: REALM, n: candName });

await stage('publisher-submits-candidate', async () => {
  await signUp(pubEmail);
  await page.goto(BASE + '#/publish', { waitUntil: 'load' }); await page.waitForTimeout(1200);
  await page.getByLabel('Name', { exact: true }).fill(candName);
  await page.getByLabel('Description', { exact: true }).fill('A candidate to be promoted by a reviewer.').catch(() => {});
  await page.getByText('Submit for review', { exact: false }).first().click({ timeout: 5000 });
  await page.waitForSelector('text=in review', { timeout: 8000 });
  if (await searchHasCand()) throw new Error('candidate leaked into Browse before review');
  return `submitted "${candName}" → in review, and NOT yet in Browse (candidate ≠ active)`;
});

await stage('publisher-has-no-review-access', async () => {
  await page.goto(BASE + '#/review', { waitUntil: 'load' }); await page.waitForTimeout(1400);
  const txt = (await page.evaluate(() => document.body.innerText)).toLowerCase();
  if (!txt.includes('reviewer access')) throw new Error('publisher was not gated out of the review surface');
  return 'a non-reviewer is gated: "You don’t have reviewer access" — promotion controls hidden';
});

let reviewerAcct = '';
await stage('register-separate-reviewer', async () => {
  reviewerAcct = await signUp(revEmail);     // overwrites the realm session (no SSO) — now the reviewer
  return `separate reviewer account ${reviewerAcct.slice(0, 14)}… registered`;
});

await stage('operator-grants-reviewer', async () => {
  // the OPERATOR action — reviewer status is never self-served; the CLI appends to the roster the
  // running daemon replays, so it takes effect live.
  const out = execSync(`python3 -m scripts.registry_local_service --grant-reviewer ${REALM} ${reviewerAcct}`,
    { cwd: REPO_ROOT, encoding: 'utf-8' });
  return out.trim().split('\n').slice(-1)[0];
});

await stage('reviewer-approves-and-promotes', async () => {
  await page.goto(BASE + '#/review', { waitUntil: 'load' }); await page.waitForTimeout(1600);
  await page.waitForSelector('text=Approve & promote', { timeout: 8000 });
  const body = await page.evaluate(() => document.body.innerText);
  if (!body.includes(candName)) throw new Error('the pending candidate is not visible to the reviewer');
  // the queue accumulates real candidates — approve OUR specific candidate's card, not just the first.
  const card = page.locator('.oh-card', { hasText: candName }).first();
  await card.getByText('Approve & promote', { exact: false }).click({ timeout: 5000 });
  await page.waitForSelector('text=promoted to the catalog', { timeout: 8000 });
  return `reviewer approved "${candName}" → server confirms "promoted to the catalog"`;
});

await stage('promoted-entry-now-in-browse', async () => {
  await page.goto(BASE + '#/browse', { waitUntil: 'load' }); await page.waitForTimeout(1600);
  if (!(await searchHasCand())) throw new Error('the approved candidate did not appear in the catalog');
  const inGrid = await page.evaluate((nm) => [...document.querySelectorAll('.ohub-card h3')].some((h) => h.textContent === nm), candName);
  if (!inGrid) throw new Error('the promoted entry is not rendered in the Browse grid');
  return `the promoted "${candName}" is now public-active in Browse (with submitter+reviewer lineage)`;
});

const handle = HAS_NATIVE_VIDEO ? page.video() : null;
const gif = rec ? await rec.stop() : null;
await page.close(); await context.close(); await browser.close();
const native = handle ? await finalizeNativeVideo(handle, 'reviewer-promote') : null;
const video = native ? (native.mp4 || native.webm) : gif?.file;

const report = { generated_at: new Date().toISOString(), gate: 'reviewer_promote', surface: BASE, realm: REALM,
  candidate: candName, reviewer_account: reviewerAcct, ok: steps.every((s) => s.ok), steps, page_errors: log.pageErrors,
  video: video ? `videos/${video}` : 'HELD',
  note: 'The promotion gate end to end: publisher submits (not in Browse) → non-reviewer gated → operator grants a reviewer → reviewer approves → the candidate becomes public-active in Browse with lineage. The only candidate→active path.' };
saveJSON('reports', 'reviewer-promote-report.json', report);
saveText('reports', 'reviewer-promote-report.md', [
  `# Reviewer promotion gate × real accounts — ${report.generated_at}`, '',
  `Surface: ${BASE} · Realm: ${REALM} · Candidate: ${candName} · Result: **${report.ok ? 'PASS' : 'FAIL'}**`, '',
  '| # | stage | ok | detail |', '|---|---|---|---|',
  ...steps.map((s) => `| ${s.n} | ${s.label} | ${s.ok ? 'ok' : 'FAIL'} | ${s.detail} |`),
  '', `Video: \`artifacts/e2e/${report.video}\``,
].join('\n'));
console.log(`\nreviewer-promote: ${report.ok ? 'PASS' : 'FAIL'} → reports/reviewer-promote-report.md · ${report.video}`);
process.exit(report.ok ? 0 : 1);
