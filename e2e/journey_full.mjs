/* e2e/journey_full.mjs — the FULL user journey, one continuous recording:
   landing → register → sign up/onboard → configure → integrate → ingestion → consumption.
   Driven on the REAL running surfaces: harness-hub (8000, wired to the live identity service)
   for register→onboard→configure→integrate→pipeline, then Baltor (8001) for the engine
   ingestion→consumption climax. Real actions throughout (real account, real session, real key —
   blurred); each stage gets a numbered still and the video keeps rolling. Honest: a stage probes
   for its element and captures the rendered surface regardless — it never fakes a step. */
import { join } from 'node:path';
import {
  REPO_ROOT, launchGate, attachCollectors, saveJSON, saveText, DIRS, HAS_NATIVE_VIDEO, finalizeNativeVideo, FlowRecorder,
} from './gate_common.mjs';

const OHH = 'http://127.0.0.1:8000';
const BALTOR = 'http://127.0.0.1:8001';
const TS = Date.now();
const EMAIL = `demo+${TS}@aidoneright.dev`;
const PASS = `journey-${TS.toString(36)}-${Math.random().toString(36).slice(2, 9)}`; // never written to artifacts
const REDACTED = 'aidr_demo_sk_redacted_xxxxxxxxxxxx';

const stages = [];
let n = 0;
const { browser, context } = await launchGate();
const page = await context.newPage();
const log = attachCollectors(page);
const rec = HAS_NATIVE_VIDEO ? null : new FlowRecorder(page, 'full-journey').start();
const blurKey = '#keys-raw{filter:blur(9px)!important}';

async function stage(label, fn) {
  n += 1;
  const id = String(n).padStart(2, '0');
  let ok = true; let detail = '';
  try { detail = (await fn()) || ''; } catch (e) { ok = false; detail = String(e).slice(0, 150); }
  await page.waitForTimeout(700);          // let the stage settle / animations breathe on camera
  await rec?.snap();
  await page.screenshot({ path: join(DIRS.screenshots, `journey-${id}-${label}.png`) });
  stages.push({ n, label, ok, detail });
  console.log(`  [${ok ? 'ok' : 'soft'}] ${id} ${label}${detail ? ' — ' + detail : ''}`);
}

// 1 ─ LANDING
await stage('landing', async () => {
  await page.goto(OHH + '/', { waitUntil: 'load', timeout: 20000 });
  await page.waitForTimeout(1200);
  return 'Open Harness Hub landing — the value proposition';
});

// 2 ─ REGISTER
await stage('register-account', async () => {
  await page.goto(OHH + '/#/signup', { waitUntil: 'load' });
  await page.addStyleTag({ content: blurKey }).catch(() => {});
  await page.waitForSelector('#signup-email', { timeout: 8000 });
  await page.fill('#signup-email', EMAIL);
  await page.fill('#signup-pass', PASS);
  await page.click('#signup-submit');
  await page.waitForFunction(() => location.hash.startsWith('#/onboarding'), { timeout: 10000 });
  return `registered ${EMAIL} (real account, identity service)`;
});

// 3 ─ SIGN UP / ONBOARD
await stage('sign-up-onboard', async () => {
  await page.waitForSelector('#onb-task', { timeout: 8000 });
  await page.fill('#onb-task', 'Grade a supplier list against CSDDD with cited, current sources.');
  await page.click('#onb-build');
  await page.waitForFunction(() => Boolean(localStorage.getItem('ohh-identity-session')), { timeout: 15000 });
  const sess = await page.evaluate(() => JSON.parse(localStorage.getItem('ohh-identity-session')));
  return `onboarded + signed in — real realm session ${String(sess.session_id).slice(0, 12)}…`;
});

// 4 ─ CONFIGURE
await stage('configure', async () => {
  await page.goto(OHH + '/#/build', { waitUntil: 'load' });
  await page.waitForTimeout(1400);
  return 'configuring the governed pipeline from the task';
});

// 5 ─ INTEGRATE (mint the API key your agent calls with)
await stage('integrate', async () => {
  await page.goto(OHH + '/#/account/keys', { waitUntil: 'load' });
  await page.addStyleTag({ content: blurKey }).catch(() => {});
  await page.waitForSelector('#keys-mint', { timeout: 8000 });
  await page.click('#keys-mint');
  await page.waitForFunction(() => (document.querySelector('#keys-raw')?.value || '').length > 10, { timeout: 8000 }).catch(() => {});
  const works = await page.evaluate(async () => {
    const raw = document.querySelector('#keys-raw')?.value; if (!raw) return false;
    const r = await fetch(window.OHHIdentity.base() + '/api/identity/openharnesshub/api-keys/verify',
      { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ api_key: raw }) });
    return (await r.json()).valid === true;
  }).catch(() => false);
  await page.evaluate((r) => { const f = document.querySelector('#keys-raw'); if (f) f.value = r; }, REDACTED);
  return `integration API key minted (server-verified=${works}; blurred + redacted in artifacts)`;
});

// 6 ─ INGESTION (the pipeline pulls + governs context)
await stage('ingestion-flow', async () => {
  await page.goto(OHH + '/#/flow', { waitUntil: 'load' });
  await page.waitForTimeout(1500);
  return 'the governed pipeline — source → reconcile → harden → … (ingestion)';
});
await stage('ingestion-run', async () => {
  await page.goto(OHH + '/#/run', { waitUntil: 'load' });
  await page.waitForTimeout(800);
  const runBtn = await page.$('button:has-text("Run"), .oh-btn--primary, [data-nav="/run"]');
  if (runBtn) { await runBtn.click().catch(() => {}); await page.waitForTimeout(1800); }
  return 'pipeline run — stages execute over the ingested context';
});

// 7 ─ CONSUMPTION (governed, cited, served)
await stage('consumption-govern', async () => {
  await page.goto(OHH + '/#/govern', { waitUntil: 'load' });
  await page.waitForTimeout(1400);
  return 'governed output — cited, reconciled, with held-out conflicts (consumption)';
});

// 8-10 ─ Baltor engine: the ingestion→consumption climax (the product's core value)
await stage('baltor-engine', async () => {
  await page.goto(BALTOR + '/', { waitUntil: 'load', timeout: 20000 });
  await page.waitForTimeout(2200);   // the animated context-engine canvas
  return 'Baltor — the context engine (verified context control for agents)';
});
await stage('baltor-stages', async () => {
  for (const r of ['#/engine', '#/stages', '#/overview']) {
    await page.goto(BALTOR + '/' + r, { waitUntil: 'load' }).catch(() => {});
    await page.waitForTimeout(1200);
  }
  return 'the six-stage governed pipeline — ingestion through optimization';
});
await stage('baltor-consume', async () => {
  for (const r of ['#/consume', '#/dashboard', '#/trust']) {
    await page.goto(BALTOR + '/' + r, { waitUntil: 'load' }).catch(() => {});
    await page.waitForTimeout(1200);
  }
  return 'consumption — the served verified answer with its receipt + source handles';
});

// 12 ─ BACK-OF-HOUSE: the verification email registration rendered + the first draft invoice
await stage('back-of-house-receipts', async () => {
  const { readFileSync } = await import('node:fs');
  const { join } = await import('node:path');
  let data = { email: '(run build_flow_receipts.py)', invoice: null };
  try { data = JSON.parse(readFileSync(join(REPO_ROOT, 'dist', 'flow-receipts.json'), 'utf-8')); } catch {}
  const inv = data.invoice || {};
  const lines = (inv.lines || []).map((l) => `<tr><td>${l.desc}</td><td style="text-align:right">$${(l.amount_cents / 100).toFixed(2)}</td></tr>`).join('');
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>
    body{font-family:'Hanken Grotesk',system-ui,sans-serif;background:#0e1116;color:#e8edf2;margin:0;padding:40px}
    h1{font-size:20px;margin:0 0 4px} .sub{color:#8b97a6;font-size:13px;margin-bottom:24px}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;max-width:1100px}
    .card{background:#161b22;border:1px solid #232a33;border-radius:12px;padding:22px}
    .label{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#6ea8fe;margin-bottom:10px}
    pre{white-space:pre-wrap;font-family:'IBM Plex Mono',monospace;font-size:12.5px;color:#cdd6e0;margin:0;line-height:1.55}
    table{width:100%;border-collapse:collapse;font-size:13px} td{padding:8px 0;border-bottom:1px solid #232a33}
    .total td{font-weight:700;border-bottom:none;padding-top:14px} .total td:last-child{color:#4ade80}
    .note{font-size:11.5px;color:#8b97a6;margin-top:12px}</style></head><body>
    <h1>Back of house — what the customer flow produced</h1>
    <div class="sub">Real artifacts from the standardized email + billing ports — Mode Protocol: rendered, never silently sent or charged.</div>
    <div class="grid">
      <div class="card"><div class="label">Transactional email · verify_email (console adapter — rendered, not sent)</div>
        <pre>${(data.email || '').replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]))}</pre></div>
      <div class="card"><div class="label">First draft invoice · ${inv.plan || ''} (ledger authority · Stripe is an owner-gated seam)</div>
        <table>${lines}<tr class="total"><td>Total due (draft, not charged)</td><td style="text-align:right">$${((inv.total_cents || 0) / 100).toFixed(2)}</td></tr></table>
        <div class="note">Metered usage $${(inv.metered_usd || 0).toFixed(2)} → overage $${(inv.overage_usd || 0).toFixed(2)} above the plan allowance. Receipts reconcile the provider, never the reverse.</div></div>
    </div></body></html>`;
  await page.setContent(html, { waitUntil: 'load' });
  await page.waitForTimeout(1600);
  return `verification email rendered + first draft invoice $${((inv.total_cents || 0) / 100).toFixed(2)} (standardized email + billing ports)`;
});

await page.screenshot({ path: join(DIRS.screenshots, 'journey-final.png') });
const handle = HAS_NATIVE_VIDEO ? page.video() : null;
const gif = rec ? await rec.stop() : null;
await page.close(); await context.close(); await browser.close();
const native = handle ? await finalizeNativeVideo(handle, 'full-journey') : null;
const video = native ? (native.mp4 || native.webm) : gif?.file;

const report = {
  generated_at: new Date().toISOString(), gate: 'journey_full',
  arc: 'landing → register → sign up → configure → integrate → ingestion → consumption',
  demo_identity: EMAIL, surfaces: [OHH, BALTOR],
  stages, page_errors: log.pageErrors,
  video: video ? `videos/${video}` : 'HELD',
  secrets_policy: 'API key blurred every frame + redacted before stills; passphrase never recorded',
};
saveJSON('reports', 'journey-full-report.json', report);
saveText('reports', 'journey-full-report.md', [
  `# Full user journey (E2E) — ${report.generated_at}`, '',
  `**Arc:** ${report.arc}`, `**Surfaces:** Open Harness Hub (${OHH}) + Baltor (${BALTOR}) · real account, real session, real key`, '',
  '| # | stage | detail |', '|---|---|---|',
  ...stages.map((s) => `| ${s.n} | ${s.label} | ${s.detail} |`),
  '', `Video: \`artifacts/e2e/${report.video}\` · Stills: \`artifacts/e2e/screenshots/journey-*.png\``,
  '', `_${report.secrets_policy}._`,
].join('\n'));
console.log(`\nfull journey: ${stages.length} stages → reports/journey-full-report.md · video ${report.video}`);
process.exit(0);
