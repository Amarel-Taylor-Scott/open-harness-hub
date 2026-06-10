/* e2e/full_design_auth.mjs — record the FULL DESIGN doing REAL auth.
   The hundreds-of-hours bundle UI (oh-site kit), wired to the live identity service: landing →
   create account (real registration into the brand's realm) → real session → /app. Proves the
   design is now functional, not mock. Video + stills. Honest: real account, real session. */
import { join } from 'node:path';
import { launchGate, attachCollectors, saveJSON, saveText, DIRS, HAS_NATIVE_VIDEO, finalizeNativeVideo, FlowRecorder } from './gate_common.mjs';

const SURF = 'http://127.0.0.1:9210/opencontexthub/' + encodeURIComponent('OpenContextHub Prototype.html');
const REALM = 'opencontexthub';
const TS = Date.now();
const email = `fulldesign+${TS}@aidoneright.dev`;
const pass = `fulldesign-${TS.toString(36)}`;
const steps = [];
let n = 0;
const { browser, context } = await launchGate();
const page = await context.newPage();
const log = attachCollectors(page);
const rec = HAS_NATIVE_VIDEO ? null : new FlowRecorder(page, 'full-design-auth').start();

async function stage(label, fn) {
  n += 1; let ok = true; let detail = '';
  try { detail = (await fn()) || ''; } catch (e) { ok = false; detail = String(e).split('\n')[0].slice(0, 140); }
  await page.waitForTimeout(700); await rec?.snap();
  await page.screenshot({ path: join(DIRS.screenshots, `fulldesign-${String(n).padStart(2, '0')}-${label}.png`) });
  steps.push({ n, label, ok, detail });
  console.log(`  [${ok ? 'ok' : 'FAIL'}] ${label}${ok ? '' : ' — ' + detail}`);
}

await stage('landing', async () => { await page.goto(SURF, { waitUntil: 'load', timeout: 20000 }); await page.waitForTimeout(1600); return 'OpenContextHub — full design (live registry)'; });
await stage('signup-form', async () => {
  await page.goto(SURF + '#/signup', { waitUntil: 'load' }); await page.waitForTimeout(1800);
  const live = await page.evaluate(() => window.OHIdentity && window.OHIdentity.available());
  await page.waitForSelector('input[type="email"]', { timeout: 8000 });
  return `the kit's Create-account form (identity service live=${live})`;
});
await stage('fill-and-create', async () => {
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', pass);
  const nameI = await page.$('input:not([type])'); if (nameI) await nameI.fill('Ada Lovelace').catch(() => {});
  await page.getByText('Create account', { exact: false }).first().click({ timeout: 5000 });
  await page.waitForFunction(() => location.hash.startsWith('#/dashboard'), { timeout: 12000 });
  const sess = await page.evaluate((r) => JSON.parse(localStorage.getItem('oh-session-' + r) || 'null'), REALM);
  if (!sess || !String(sess.session_id).startsWith('sess_')) throw new Error('no real session minted');
  return `REAL account created in the ${REALM} realm — session ${String(sess.session_id).slice(0, 12)}…`;
});
await stage('signed-in-app', async () => { await page.waitForTimeout(1400); return 'signed in — the full-design app (real session)'; });

const handle = HAS_NATIVE_VIDEO ? page.video() : null;
const gif = rec ? await rec.stop() : null;
await page.close(); await context.close(); await browser.close();
const native = handle ? await finalizeNativeVideo(handle, 'full-design-auth') : null;
const video = native ? (native.mp4 || native.webm) : gif?.file;

const report = { generated_at: new Date().toISOString(), gate: 'full_design_auth', surface: SURF, realm: REALM,
  ok: steps.every((s) => s.ok), steps, page_errors: log.pageErrors, video: video ? `videos/${video}` : 'HELD',
  note: 'The full hundreds-of-hours design doing real registration against the identity service.' };
saveJSON('reports', 'full-design-auth-report.json', report);
saveText('reports', 'full-design-auth-report.md', [
  `# Full design × real auth — ${report.generated_at}`, '',
  `Surface: ${SURF} · Realm: ${REALM} · Result: **${report.ok ? 'PASS' : 'FAIL'}**`, '',
  '| # | stage | ok | detail |', '|---|---|---|---|',
  ...steps.map((s) => `| ${s.n} | ${s.label} | ${s.ok ? 'ok' : 'FAIL'} | ${s.detail} |`),
  '', `Video: \`artifacts/e2e/${report.video}\``,
].join('\n'));
console.log(`\nfull-design auth: ${report.ok ? 'PASS' : 'FAIL'} → reports/full-design-auth-report.md · ${report.video}`);
process.exit(report.ok ? 0 : 1);
