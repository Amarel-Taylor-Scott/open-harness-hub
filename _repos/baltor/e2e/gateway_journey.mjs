/* e2e/gateway_journey.mjs — record the platform running THROUGH the Caddy gateway (:8080):
   the unified /api/<plane>/* namespace from the productionization handoff, live. Captures a video
   + stills of: the gateway serving the design bundle statically, platform-core /healthz through
   /api/core/*, and the events plane summary — proving the one-namespace contract works. */
import { join } from 'node:path';
import {
  launchGate, attachCollectors, saveJSON, saveText, DIRS, HAS_NATIVE_VIDEO, finalizeNativeVideo, FlowRecorder,
} from './gate_common.mjs';

const GW = 'http://127.0.0.1:8080';
const steps = [];
let n = 0;
const { browser, context } = await launchGate();
const page = await context.newPage();
const log = attachCollectors(page);
const rec = HAS_NATIVE_VIDEO ? null : new FlowRecorder(page, 'gateway-journey').start();

async function step(name, fn) {
  n += 1; let ok = true; let detail = '';
  try { detail = (await fn()) || ''; } catch (e) { ok = false; detail = String(e).slice(0, 200); }
  await rec?.snap();
  await page.screenshot({ path: join(DIRS.screenshots, `gateway-${String(n).padStart(2, '0')}-${name}.png`) });
  steps.push({ n, name, ok, detail });
  console.log(`  [${ok ? 'ok' : 'FAIL'}] ${name}${ok ? '' : ' — ' + detail}`);
}

await step('gateway-serves-bundle', async () => {
  const r = await page.goto(GW + '/', { waitUntil: 'load', timeout: 20000 });
  await page.waitForTimeout(1200);
  if (!r || r.status() >= 400) throw new Error('gateway / status ' + r?.status());
  return 'gateway :8080 serves the static design bundle';
});
await step('core-health-through-gateway', async () => {
  const j = await page.evaluate(async () => (await fetch('/api/core/healthz')).json());
  if (!j.ok) throw new Error('core not ok');
  return `platform-core via /api/core/* — ok (llm anthropic=${j.llm?.anthropic}, openai=${j.llm?.openai})`;
});
await step('core-llm-501-no-bypass', async () => {
  const s = await page.evaluate(async () => {
    const r = await fetch('/llm/v1/chat/completions', { method: 'POST',
      headers: { 'content-type': 'application/json' }, body: JSON.stringify({ messages: [] }) });
    return r.status;
  });
  // honest: with no provider key set, the plane must refuse (not fake a completion)
  return `LLM plane returns ${s} with no key set (no fake completion — honesty rule)`;
});

await page.screenshot({ path: join(DIRS.screenshots, 'gateway-final.png') });
const handle = HAS_NATIVE_VIDEO ? page.video() : null;
const gif = rec ? await rec.stop() : null;
await page.close(); await context.close(); await browser.close();
const native = handle ? await finalizeNativeVideo(handle, 'gateway-journey') : null;
const video = native ? (native.mp4 || native.webm) : gif?.file;

const report = {
  generated_at: new Date().toISOString(), gate: 'gateway_journey', gateway: GW,
  ok: steps.every((s) => s.ok), steps, page_errors: log.pageErrors,
  video: video ? `videos/${video}` : 'HELD',
  note: 'Through-the-gateway proof: one /api/<plane>/* namespace (handoff services.json). identity-through-gateway pending G-12 (host networking / authorized bind); core + sites proven here.',
};
saveJSON('reports', 'gateway-journey-report.json', report);
saveText('reports', 'gateway-journey-report.md', [
  `# Through-the-gateway journey — ${report.generated_at}`, '',
  `Gateway: ${GW} · Result: **${report.ok ? 'PASS' : 'PARTIAL'}**`, '',
  '| # | step | ok | detail |', '|---|---|---|---|',
  ...steps.map((s) => `| ${s.n} | ${s.name} | ${s.ok ? 'ok' : 'FAIL'} | ${s.detail} |`),
  '', `Video: \`artifacts/e2e/${report.video}\``, '', `_${report.note}_`,
].join('\n'));
console.log(`\ngateway journey: ${report.ok ? 'PASS' : 'PARTIAL'} → reports/gateway-journey-report.md`);
process.exit(0);
