/* e2e/register_login_portal.mjs — the END-TO-END account-flow recording for owner review:
   real browser (Chrome) against the REAL local stack — openhubforai SPA (:8000) + the local
   Identity & Access service (:9410, openharnesshub realm).

   Flow (one continuous VIDEO + a numbered screenshot per step):
     01 sign-up page → 02 register demo+<ts>@aidoneright.dev → 03 onboarding → 04 build (realm
     onboarding steps complete + auto-login; REAL session in localStorage) → 05 API-keys console →
     06 mint key (raw key BLURRED in video + redacted before the still; verified server-side) →
     07 revoke → 08 logout → 09 sign back in → 10 session restored.

   Law: the passphrase and raw API key never appear in any artifact (blur is applied BEFORE mint;
   the still is taken only after the field is overwritten with the redacted fixture form). */
import { join } from 'node:path';
import {
  launchGate, attachCollectors, saveJSON, saveText, FlowRecorder, DIRS,
  HAS_NATIVE_VIDEO, finalizeNativeVideo,
} from './gate_common.mjs';

const APP = 'http://127.0.0.1:8000';
const TS = Date.now();
const EMAIL = `demo+${TS}@aidoneright.dev`;
const PASS = `local-${TS.toString(36)}-${Math.random().toString(36).slice(2, 10)}`; // never written to artifacts
const REDACTED = 'aidr_demo_sk_redacted_xxxxxxxxxxxxxxxx';

const steps = [];
let stepNo = 0;
const { browser, context } = await launchGate();
const page = await context.newPage();
const log = attachCollectors(page);
const recorder = HAS_NATIVE_VIDEO ? null
  : new FlowRecorder(page, 'portal-register-login-keys').start();

async function step(name, fn) {
  stepNo += 1;
  const id = String(stepNo).padStart(2, '0');
  let ok = true; let detail = '';
  try { detail = (await fn()) || ''; } catch (err) { ok = false; detail = String(err).slice(0, 300); }
  await recorder?.snap();                                // key moment lands in the fallback GIF
  await page.screenshot({ path: join(DIRS.screenshots, `portal-${id}-${name}.png`) });
  steps.push({ step: stepNo, name, ok, detail });
  console.log(`  [${ok ? 'ok' : 'FAIL'}] ${id} ${name}${ok ? '' : ' — ' + detail}`);
  if (!ok) throw new Error(`step ${id} ${name} failed: ${detail}`);
}

try {
  await step('signup-page', async () => {
    await page.goto(`${APP}/#/signup`, { waitUntil: 'load' });
    await page.waitForSelector('#signup-email', { timeout: 10000 });
    // blur any future raw-key field BEFORE it can ever render (video frames stay clean)
    await page.addStyleTag({ content: '#keys-raw { filter: blur(9px) !important; }' });
  });

  await step('register', async () => {
    await page.fill('#signup-email', EMAIL);
    await page.fill('#signup-pass', PASS);
    await page.click('#signup-submit');
    await page.waitForFunction(() => location.hash.startsWith('#/onboarding'), { timeout: 10000 });
    return `registered ${EMAIL}`;
  });

  await step('onboarding', async () => {
    await page.waitForSelector('#onb-task', { timeout: 10000 });
    await page.fill('#onb-task', 'Grade a supplier list against CSDDD with cited sources.');
  });

  await step('activate-and-login', async () => {
    await page.click('#onb-build');
    await page.waitForFunction(
      () => Boolean(localStorage.getItem('ohh-identity-session')), { timeout: 15000 });
    await page.waitForTimeout(800);
    const sess = await page.evaluate(() => JSON.parse(localStorage.getItem('ohh-identity-session')));
    if (!sess?.session_id?.startsWith('sess_')) throw new Error('no realm session minted');
    return `REAL session ${sess.session_id.slice(0, 12)}… (realm-scoped, opaque)`;
  });

  await step('keys-console', async () => {
    await page.goto(`${APP}/#/account/keys`, { waitUntil: 'load' });
    await page.addStyleTag({ content: '#keys-raw { filter: blur(9px) !important; }' });
    await page.waitForSelector('#keys-mint', { timeout: 10000 });
  });

  let mintedKeyWorks = false;
  await step('mint-key-blurred', async () => {
    await page.click('#keys-mint');
    await page.waitForFunction(
      () => document.querySelector('#keys-raw')?.value?.length > 10, { timeout: 10000 });
    // verify the raw key REALLY works server-side, inside the page (key never leaves the browser)
    mintedKeyWorks = await page.evaluate(async () => {
      const raw = document.querySelector('#keys-raw').value;
      const base = window.OHHIdentity.base();
      const resp = await fetch(`${base}/api/identity/openharnesshub/api-keys/verify`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: raw }),
      });
      return (await resp.json()).valid === true;
    });
    // REDACT before the still (belt + braces with the blur already covering the video)
    await page.evaluate((redacted) => {
      document.querySelector('#keys-raw').value = redacted;
    }, REDACTED);
    if (!mintedKeyWorks) throw new Error('minted key failed server-side verify');
    return 'key minted; server-side verify=valid; field redacted+blurred in artifacts';
  });

  await step('revoke-key', async () => {
    await page.waitForSelector('[data-revoke]', { timeout: 10000 });
    await page.click('[data-revoke]');
    await page.waitForFunction(
      () => document.body.innerText.includes('revoked'), { timeout: 10000 });
  });

  await step('logout', async () => {
    const out = await page.evaluate(async () => (await window.OHHIdentity.logout()).body);
    const sess = await page.evaluate(() => localStorage.getItem('ohh-identity-session'));
    if (sess) throw new Error('session handle not cleared');
    return `logged_out=${out.logged_out}`;
  });

  await step('sign-back-in', async () => {
    await page.goto(`${APP}/#/signin`, { waitUntil: 'load' });
    await page.fill('#signin-email', EMAIL);
    await page.fill('#signin-pass', PASS);
    await page.click('#signin-submit');
    await page.waitForFunction(() => location.hash.startsWith('#/app'), { timeout: 10000 });
  });

  await step('session-restored', async () => {
    const ok = await page.evaluate(() => window.OHHIdentity.validate());
    if (!ok) throw new Error('restored session failed validation');
    return 'realm session validates after re-login';
  });
} finally {
  const gif = recorder ? await recorder.stop() : null;
  const handle = HAS_NATIVE_VIDEO ? page.video() : null;
  await page.close();
  await context.close();
  await browser.close();
  const native = handle ? await finalizeNativeVideo(handle, 'portal-register-login-keys') : null;
  const vid = native
    ? { file: native.mp4 || native.webm, frames: 'continuous', webm: native.webm }
    : gif;

  const ok = steps.every((s) => s.ok);
  const report = {
    generated_at: new Date().toISOString(),
    gate: 'register_login_portal',
    app: APP,
    realm: 'openharnesshub',
    demo_identity: EMAIL,                 // synthetic; the passphrase is intentionally NOT recorded
    ok,
    steps,
    page_errors: log.pageErrors,
    video: vid ? `videos/${vid.file}` : 'HELD (no video captured)',
    video_frames: vid?.frames ?? 0,
    video_webm: vid?.webm ? `videos/${vid.webm}` : null,
    video_format_note: HAS_NATIVE_VIDEO
      ? 'native continuous webm + mp4 render (static ffmpeg 7.0.2, md5-verified, owner-authorized download)'
      : 'animated GIF via frame capture (Playwright webm needs an ffmpeg helper with no ubuntu26.04-x64 build — HELD honestly)',
    secrets_policy: 'raw key blurred in every frame + redacted before stills; passphrase never written to artifacts',
  };
  saveJSON('reports', 'portal-flow-report.json', report);
  saveText('reports', 'portal-flow-report.md', [
    `# Register → onboard → login → API keys → logout → login (E2E) — ${report.generated_at}`,
    '',
    `App: ${APP} · Realm: openharnesshub · Identity service: real (localhost:9410) · Result: **${ok ? 'PASS' : 'FAIL'}**`,
    '',
    '| # | step | ok | detail |',
    '|---|---|---|---|',
    ...steps.map((s) => `| ${s.step} | ${s.name} | ${s.ok ? 'ok' : 'FAIL'} | ${s.detail} |`),
    '',
    `Video: \`artifacts/e2e/${report.video}\` (${report.video_frames} frames) · Stills: \`artifacts/e2e/screenshots/portal-*.png\``,
    '',
    '_Raw key blurred+redacted in all artifacts; passphrase never recorded._',
  ].join('\n'));
  console.log(`\nportal flow: ${ok ? 'PASS' : 'FAIL'} (${steps.filter((s) => s.ok).length}/${steps.length} steps)`);
  process.exitCode = ok ? 0 : 1;
}
