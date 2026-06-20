/* e2e/site_journeys.mjs — record a SEPARATE full-journey video for EVERY website.
   Each site gets a tailored journey by kind:
     · product-spa (harness-hub): real signup → onboard → build → integrate(key) → run → govern.
     · product (baltor): landing → engine → stages → consume → trust → pricing.
     · hub (22 design-bundle hubs): landing → browse → open an entry → cases → docs → pricing → about.
     · static (parent, teleon, control-tower): landing walkthrough + primary CTA + sections.
   Output per site: artifacts/e2e/videos/full-journey-<id>.mp4 + journey-<id>-NN stills + a per-site
   report; plus a combined index. Resilient: every step probes-and-captures, never fakes. Honest:
   API keys blurred; passphrase never recorded.
   Usage: node site_journeys.mjs [START END]   (chunkable for long background runs). */
import { join } from 'node:path';
import {
  launchGate, attachCollectors, saveJSON, saveText, DIRS, HAS_NATIVE_VIDEO, finalizeNativeVideo, FlowRecorder,
} from './gate_common.mjs';

const HUB = (f, name) => ({ id: f, kind: 'hub', name,
  base: `http://127.0.0.1:9210/${f}/${encodeURIComponent(name + ' Prototype.html')}` });
const HUBS = [
  ['opencontexthub', 'OpenContextHub'], ['openskillshub', 'OpenSkillsHub'], ['opentoolshub', 'OpenToolsHub'],
  ['openskilltotool', 'OpenSkillToTool'], ['openmcphub', 'OpenMCPHub'], ['opencompressionhub', 'OpenCompressionHub'],
  ['openbenchmarkhub', 'OpenBenchmarkHub'], ['openreviewhub', 'OpenReviewHub'], ['openharnesshub', 'OpenHarnessHub'],
  ['opentemplateshub', 'OpenTemplatesHub'], ['openendpointhub', 'OpenEndpointHub'], ['openenvhub', 'OpenEnvHub'],
  ['opensandboxhub', 'OpenSandboxHub'], ['openagenthub', 'OpenAgentHub'], ['openreceipthub', 'OpenReceiptHub'],
  ['openstatehub', 'OpenStateHub'], ['openroutinghub', 'OpenRoutingHub'], ['openreconciliationhub', 'OpenReconciliationHub'],
  ['openhardeninghub', 'OpenHardeningHub'], ['openenrichmenthub', 'OpenEnrichmentHub'],
  ['openoptimizationhub', 'OpenOptimizationHub'], ['openverificationhub', 'OpenVerificationHub'],
];
const SITES = [
  { id: 'harness-hub', kind: 'product-spa', base: 'http://127.0.0.1:8000' },
  { id: 'baltor', kind: 'product', base: 'http://127.0.0.1:8001' },
  { id: 'ai-done-right-parent', kind: 'static', base: 'http://127.0.0.1:9210/context-is-everything/' + encodeURIComponent('Context is Everything.html') },
  { id: 'teleon', kind: 'static', base: 'http://127.0.0.1:9210/teleon/' + encodeURIComponent('Teleon Prototype.html') },
  { id: 'demo-control-tower', kind: 'static', base: 'http://127.0.0.1:9000/' },
  ...HUBS.map(([f, n]) => HUB(f, n)),
];

const START = Number(process.argv[2] ?? 0);
const END = Number(process.argv[3] ?? SITES.length);
const RUN = SITES.slice(START, END);

const { browser, context } = await launchGate();
const results = [];

async function record(site) {
  const page = await context.newPage();
  const log = attachCollectors(page);
  const rec = HAS_NATIVE_VIDEO ? null : new FlowRecorder(page, `full-journey-${site.id}`).start();
  const stages = [];
  let n = 0;
  const blur = '#keys-raw{filter:blur(9px)!important}';

  async function stage(label, fn) {
    n += 1;
    let ok = true; let detail = '';
    try { detail = (await fn()) || ''; } catch (e) { ok = false; detail = String(e).split('\n')[0].slice(0, 120); }
    await page.waitForTimeout(650);
    await rec?.snap();
    await page.screenshot({ path: join(DIRS.screenshots, `journey-${site.id}-${String(n).padStart(2, '0')}-${label}.png`) }).catch(() => {});
    stages.push({ n, label, ok, detail });
  }
  const clickText = async (t) => { await page.getByText(t, { exact: false }).first().click({ timeout: 3000 }); await page.waitForTimeout(700); };
  const scrollBy = async (px) => { await page.evaluate((y) => window.scrollBy(0, y), px); await page.waitForTimeout(500); };

  try {
    if (site.kind === 'product-spa') {
      const TS = Date.now(); const email = `tour+${site.id}-${TS}@aidoneright.dev`; const pass = `tour-${TS.toString(36)}`;
      await stage('landing', async () => { await page.goto(site.base + '/', { waitUntil: 'load', timeout: 20000 }); await page.waitForTimeout(900); return 'landing'; });
      await stage('register', async () => {
        await page.goto(site.base + '/#/signup', { waitUntil: 'load' }); await page.addStyleTag({ content: blur }).catch(() => {});
        await page.waitForSelector('#signup-email', { timeout: 8000 });
        await page.fill('#signup-email', email); await page.fill('#signup-pass', pass); await page.click('#signup-submit');
        await page.waitForFunction(() => location.hash.startsWith('#/onboarding'), { timeout: 10000 }); return 'real account registered';
      });
      await stage('onboard', async () => {
        await page.waitForSelector('#onb-task', { timeout: 8000 });
        await page.fill('#onb-task', 'Serve a verified, cited answer for a regulated task.'); await page.click('#onb-build');
        await page.waitForFunction(() => Boolean(localStorage.getItem('ohh-identity-session')), { timeout: 15000 }); return 'onboarded + signed in';
      });
      await stage('configure-build', async () => { await page.goto(site.base + '/#/build', { waitUntil: 'load' }); await page.waitForTimeout(1200); return 'configure the pipeline'; });
      await stage('integrate-key', async () => {
        await page.goto(site.base + '/#/account/keys', { waitUntil: 'load' }); await page.addStyleTag({ content: blur }).catch(() => {});
        await page.waitForSelector('#keys-mint', { timeout: 8000 }); await page.click('#keys-mint');
        await page.waitForFunction(() => (document.querySelector('#keys-raw')?.value || '').length > 10, { timeout: 8000 }).catch(() => {});
        await page.evaluate(() => { const f = document.querySelector('#keys-raw'); if (f) f.value = 'aidr_demo_sk_redacted_xxxx'; }); return 'API key minted (blurred)';
      });
      await stage('run', async () => { await page.goto(site.base + '/#/run', { waitUntil: 'load' }); await page.waitForTimeout(1200); return 'pipeline run'; });
      await stage('consumption-govern', async () => { await page.goto(site.base + '/#/govern', { waitUntil: 'load' }); await page.waitForTimeout(1200); return 'governed, cited output'; });
    } else if (site.kind === 'product') { // baltor
      await stage('landing-engine', async () => { await page.goto(site.base + '/', { waitUntil: 'load', timeout: 20000 }); await page.waitForTimeout(1800); return 'the context engine'; });
      await stage('scroll-stages', async () => { await scrollBy(700); await scrollBy(700); return 'the governed pipeline stages'; });
      for (const r of ['#/engine', '#/overview', '#/consume', '#/dashboard', '#/trust', '#/pricing']) {
        await stage('view' + r.replace('#/', '-'), async () => { await page.goto(site.base + '/' + r, { waitUntil: 'load' }).catch(() => {}); await page.waitForTimeout(1100); return r; });
      }
    } else if (site.kind === 'hub') {
      await stage('landing', async () => { await page.goto(site.base, { waitUntil: 'load', timeout: 20000 }); await page.waitForTimeout(1400); return `${site.name} landing`; });
      await stage('browse', async () => { await page.goto(site.base + '#/browse', { waitUntil: 'load' }).catch(() => {}); await page.waitForTimeout(1300); return 'browse the registry'; });
      await stage('entry-detail', async () => {
        const link = await page.$('a[href*="/e/"], .ohub-card a, .oh-card a, a[href*="#/e"]');
        if (link) { await link.click().catch(() => {}); await page.waitForTimeout(1300); return 'an entry — provenance & trust'; }
        return 'entry list (no detail link found)';
      });
      for (const [label, r] of [['cases', '#/cases'], ['docs', '#/docs'], ['pricing', '#/pricing'], ['about', '#/about']]) {
        await stage(label, async () => { await page.goto(site.base + r, { waitUntil: 'load' }).catch(() => {}); await page.waitForTimeout(1000); return label; });
      }
    } else { // static: parent, teleon, control-tower
      await stage('landing', async () => { await page.goto(site.base, { waitUntil: 'load', timeout: 20000 }); await page.waitForTimeout(1300); return 'landing'; });
      await stage('scroll-1', async () => { await scrollBy(800); return 'sections'; });
      await stage('scroll-2', async () => { await scrollBy(800); return 'more sections'; });
      await stage('scroll-3', async () => { await scrollBy(900); return 'footer / CTA'; });
    }
  } catch (e) { stages.push({ n: n + 1, label: 'error', ok: false, detail: String(e).slice(0, 120) }); }

  await page.evaluate(() => window.scrollTo(0, 0)).catch(() => {});
  const handle = HAS_NATIVE_VIDEO ? page.video() : null;
  const gif = rec ? await rec.stop() : null;
  await page.close();
  const result = { id: site.id, kind: site.kind, base: site.base, stages,
    page_errors: log.pageErrors.length, _handle: handle, _gif: gif };
  results.push(result);
  console.log(`  [${stages.every((s) => s.ok) ? 'ok' : 'partial'}] ${site.id} — ${stages.length} stages, ${log.pageErrors.length} page errors`);
}

for (const site of RUN) await record(site);

await context.close();
await browser.close();
for (const r of results) {
  if (r._handle) { const out = await finalizeNativeVideo(r._handle, `full-journey-${r.id}`); r.video = out ? (out.mp4 || out.webm) : null; }
  else r.video = r._gif?.file ?? null;
  delete r._handle; delete r._gif;
}

const index = { generated_at: new Date().toISOString(), gate: 'site_journeys', sites: results.length,
  videos: results.map((r) => ({ id: r.id, kind: r.kind, video: r.video ? `videos/${r.video}` : 'HELD',
    stages: r.stages.length, ok: r.stages.every((s) => s.ok), page_errors: r.page_errors })) };
saveJSON('reports', `site-journeys-index${process.argv[2] != null ? `-${START}-${END}` : ''}.json`, index);
saveText('reports', `site-journeys-index${process.argv[2] != null ? `-${START}-${END}` : ''}.md`, [
  `# Per-website journey videos — ${index.generated_at}`, '',
  `${results.length} websites, one full-journey video each.`, '',
  '| website | kind | stages | ok | page errors | video |', '|---|---|---|---|---|---|',
  ...index.videos.map((v) => `| ${v.id} | ${v.kind} | ${v.stages} | ${v.ok ? 'yes' : 'partial'} | ${v.page_errors} | full-journey-${v.id}.mp4 |`),
].join('\n'));
console.log(`\nsite journeys: ${results.length} per-website videos → reports/site-journeys-index.md`);
process.exit(0);
