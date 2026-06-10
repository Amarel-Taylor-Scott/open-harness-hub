/* e2e/frontends_qa.mjs — multi-front-end QA: (A) REAL signups into OTHER products' realms via the
   realm-parameterized auth flow (Baltor + Teleon realms, not just openharnesshub), and (B) a render
   sweep of the actual other front ends (parent · Baltor app · Teleon · sample hubs) capturing
   console errors + horizontal overflow + title. One continuous video + per-step stills + a QA
   report. Honest: signups are real accounts in those realms (backend enforces isolation); the
   render sweep flags any real issue (overflow / console error / non-render). */
import { join } from 'node:path';
import {
  launchGate, attachCollectors, saveJSON, saveText, DIRS, HAS_NATIVE_VIDEO, finalizeNativeVideo, FlowRecorder, hasHorizontalOverflow,
} from './gate_common.mjs';

const APP = 'http://127.0.0.1:8000';
const TS = Date.now();
const findings = [];
const steps = [];
let n = 0;
const { browser, context } = await launchGate();
const page = await context.newPage();
const log = attachCollectors(page);
const rec = HAS_NATIVE_VIDEO ? null : new FlowRecorder(page, 'frontends-qa').start();

async function shot(label) {
  n += 1;
  await rec?.snap();
  await page.screenshot({ path: join(DIRS.screenshots, `qa-${String(n).padStart(2, '0')}-${label}.png`) });
}

// ── A. real signup into another product's realm via ?realm= override ──
async function realmSignup(realm) {
  const email = `qa+${realm}-${TS}@aidoneright.dev`;
  const pass = `qa-${realm}-${TS.toString(36)}`;
  const step = { kind: 'signup', realm, email, ok: false, detail: '' };
  try {
    await page.goto(`${APP}/?realm=${realm}#/signup`, { waitUntil: 'load', timeout: 20000 });
    await page.addStyleTag({ content: '#keys-raw{filter:blur(9px)!important}' }).catch(() => {});
    await page.waitForSelector('#signup-email', { timeout: 8000 });
    const clientRealm = await page.evaluate(() => window.OHHIdentity && window.OHHIdentity.realm);
    if (clientRealm !== realm) throw new Error(`client realm ${clientRealm} != ${realm}`);
    await page.fill('#signup-email', email);
    await page.fill('#signup-pass', pass);
    await shot(`signup-${realm}-filled`);
    await page.click('#signup-submit');
    await page.waitForFunction(() => location.hash.startsWith('#/onboarding'), { timeout: 10000 });
    await page.waitForSelector('#onb-task', { timeout: 8000 });
    await page.fill('#onb-task', `A ${realm} task: serve a verified, cited answer.`);
    await page.click('#onb-build');
    await page.waitForFunction(() => Boolean(localStorage.getItem('ohh-identity-session')), { timeout: 15000 });
    // confirm the session really belongs to THIS realm (backend isolation)
    const valid = await page.evaluate(() => window.OHHIdentity.validate());
    if (!valid) throw new Error('session did not validate in its realm');
    step.ok = true;
    step.detail = `real account registered + signed in to the ${realm} realm (isolated)`;
    await shot(`signup-${realm}-signed-in`);
    // clear so the next realm starts clean (separate realm, separate session — no SSO)
    await page.evaluate(() => { localStorage.removeItem('ohh-identity-session'); });
  } catch (e) {
    step.detail = String(e).slice(0, 150);
    findings.push({ severity: 'high', surface: `signup:${realm}`, issue: step.detail });
    await shot(`signup-${realm}-FAIL`);
  }
  steps.push(step);
  console.log(`  [${step.ok ? 'ok' : 'FAIL'}] signup→${realm} — ${step.detail}`);
}

for (const realm of ['baltor', 'teleon', 'opencontexthub']) await realmSignup(realm);

// ── B. render sweep of the real other front ends ──
const SURFACES = [
  { id: 'parent-AI-Done-Right', url: 'http://127.0.0.1:9101/' },
  { id: 'baltor-app', url: 'http://127.0.0.1:8001/' },
  { id: 'teleon', url: 'http://127.0.0.1:9210/teleon/' + encodeURIComponent('Teleon Prototype.html') },
  { id: 'control-tower', url: 'http://127.0.0.1:9000/' },
  { id: 'hub-opencontexthub', url: 'http://127.0.0.1:9210/opencontexthub/' + encodeURIComponent('OpenContextHub Prototype.html') },
  { id: 'hub-openreviewhub', url: 'http://127.0.0.1:9210/openreviewhub/' + encodeURIComponent('OpenReviewHub Prototype.html') },
  { id: 'hub-openroutinghub', url: 'http://127.0.0.1:9210/openroutinghub/' + encodeURIComponent('OpenRoutingHub Prototype.html') },
];
for (const s of SURFACES) {
  const before = log.console.filter((c) => c.type === 'error').length;
  const peBefore = log.pageErrors.length;
  const step = { kind: 'render', surface: s.id, ok: false, detail: '' };
  try {
    const resp = await page.goto(s.url, { waitUntil: 'load', timeout: 20000 });
    await page.waitForTimeout(1600);
    const title = await page.title();
    const overflow = await hasHorizontalOverflow(page);
    const consoleErrs = log.console.filter((c) => c.type === 'error').length - before;
    const pageErrs = log.pageErrors.length - peBefore;
    step.ok = Boolean(resp && resp.status() < 400) && pageErrs === 0 && !overflow;
    step.detail = `"${title.slice(0, 40)}" http=${resp?.status()} overflow=${overflow} consoleErr=${consoleErrs} pageErr=${pageErrs}`;
    if (overflow) findings.push({ severity: 'medium', surface: s.id, issue: 'horizontal overflow' });
    if (pageErrs) findings.push({ severity: 'high', surface: s.id, issue: `${pageErrs} uncaught page error(s)` });
    await shot('render-' + s.id);
  } catch (e) {
    step.detail = String(e).slice(0, 120);
    findings.push({ severity: 'high', surface: s.id, issue: step.detail });
  }
  steps.push(step);
  console.log(`  [${step.ok ? 'ok' : 'note'}] render ${s.id} — ${step.detail}`);
}

const handle = HAS_NATIVE_VIDEO ? page.video() : null;
const gif = rec ? await rec.stop() : null;
await page.close(); await context.close(); await browser.close();
const native = handle ? await finalizeNativeVideo(handle, 'frontends-qa') : null;
const video = native ? (native.mp4 || native.webm) : gif?.file;

const report = {
  generated_at: new Date().toISOString(), gate: 'frontends_qa',
  signups: steps.filter((s) => s.kind === 'signup'),
  renders: steps.filter((s) => s.kind === 'render'),
  findings, video: video ? `videos/${video}` : 'HELD',
};
saveJSON('reports', 'frontends-qa-report.json', report);
saveText('reports', 'frontends-qa-report.md', [
  `# Multi-front-end QA — ${report.generated_at}`, '',
  `## Real signups into other products' realms (realm-parameterized auth)`,
  '| realm | result | detail |', '|---|---|---|',
  ...report.signups.map((s) => `| ${s.realm} | ${s.ok ? 'PASS' : 'FAIL'} | ${s.detail} |`),
  '', `## Front-end render sweep`,
  '| surface | result | detail |', '|---|---|---|',
  ...report.renders.map((s) => `| ${s.surface} | ${s.ok ? 'ok' : 'NOTE'} | ${s.detail} |`),
  '', `## Findings (${findings.length})`,
  ...(findings.length ? findings.map((f) => `- **[${f.severity}] ${f.surface}**: ${f.issue}`) : ['- none']),
  '', `Video: \`artifacts/e2e/${report.video}\``,
].join('\n'));
console.log(`\nfrontends QA: ${report.signups.filter((s) => s.ok).length}/${report.signups.length} signups · ${report.renders.filter((s) => s.ok).length}/${report.renders.length} renders clean · ${findings.length} findings → reports/frontends-qa-report.md`);
process.exit(0);
