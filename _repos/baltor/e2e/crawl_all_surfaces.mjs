/* e2e/crawl_all_surfaces.mjs — Browser E2E gate: crawl every RUNNING local surface from
   architecture/local_service_registry.json (active_local + screenshot_required), record a VIDEO per
   surface, capture 1440/1280/390 screenshots + HTML + console + network failures, check horizontal
   overflow and same-origin dead links. Honest: held/planned services are listed as skipped with
   their reasons — never faked. Exit 1 on load failure or uncaught page error. */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import {
  REPO_ROOT, launchGate, attachCollectors, hasHorizontalOverflow, shootViewports,
  deadLinkSweep, saveJSON, saveText, FlowRecorder, HAS_NATIVE_VIDEO, finalizeNativeVideo,
} from './gate_common.mjs';

const registry = JSON.parse(
  readFileSync(join(REPO_ROOT, 'architecture', 'local_service_registry.json'), 'utf-8'));
const targets = registry.services.filter(
  (s) => s.status === 'active_local' && s.screenshot_required);
const skipped = registry.services.filter((s) => s.status !== 'active_local')
  .map((s) => ({ service_id: s.service_id, status: s.status, reason: s.held_reason || '' }));

const { browser, context } = await launchGate();
const results = [];
const nativeVideos = [];                                  // finalized after context.close()

for (const svc of targets) {
  const url = svc.health_url;
  const page = await context.newPage();
  const log = attachCollectors(page);
  const recorder = HAS_NATIVE_VIDEO ? null : new FlowRecorder(page, `crawl-${svc.service_id}`).start();
  const result = { service_id: svc.service_id, url, ok: false };
  try {
    const resp = await page.goto(url, { waitUntil: 'load', timeout: 20000 });
    await page.waitForTimeout(1500);                      // let the SPA/prototype settle
    result.http_status = resp?.status() ?? null;
    result.title = await page.title();
    result.screenshots = await shootViewports(page, svc.service_id);
    saveText('html', `${svc.service_id}.html`, await page.content());
    result.overflow = await hasHorizontalOverflow(page);
    result.links = await deadLinkSweep(page);
    result.page_errors = log.pageErrors;
    result.console_errors = log.console.filter((c) => c.type === 'error');
    result.request_failures = log.requestFailures;
    result.ok = Boolean(resp && resp.status() < 400) && log.pageErrors.length === 0;
  } catch (err) {
    result.error = String(err).slice(0, 300);
  }
  saveJSON('console', `${svc.service_id}.json`, log);
  if (recorder) {
    result.video = (await recorder.stop())?.file ?? null;
  } else {
    nativeVideos.push({ result, handle: page.video(), base: `crawl-${svc.service_id}` });
  }
  await page.close();
  results.push(result);
  console.log(`  [${result.ok ? 'ok' : 'FAIL'}] ${svc.service_id} ${url}` +
    (result.overflow ? ' OVERFLOW' : '') +
    (result.links?.dead?.length ? ` dead-links=${result.links.dead.length}` : ''));
}

await context.close();                                    // flushes native webm files
await browser.close();
for (const nv of nativeVideos) {
  const out = await finalizeNativeVideo(nv.handle, nv.base);
  nv.result.video = out ? (out.mp4 || out.webm) : null;
  nv.result.video_webm = out?.webm ?? null;
}

const report = {
  generated_at: new Date().toISOString(),
  gate: 'crawl_all_surfaces',
  crawled: results.length,
  passed: results.filter((r) => r.ok).length,
  surfaces: results,
  skipped_not_active: skipped,
};
saveJSON('reports', 'crawl-report.json', report);
saveText('reports', 'crawl-report.md', [
  `# Crawl report — ${report.generated_at}`,
  '',
  `Crawled ${report.crawled} running surfaces; ${report.passed} passed.`,
  '',
  '| surface | http | overflow | page errors | dead links | video | screenshots |',
  '|---|---|---|---|---|---|---|',
  ...results.map((r) => `| ${r.service_id} | ${r.http_status ?? 'ERR'} | ${r.overflow ? 'YES' : 'no'} | ` +
    `${r.page_errors?.length ?? '-'} | ${r.links?.dead?.length ?? '-'} | ` +
    `${r.video ? 'videos/' + r.video : 'HELD (no frames)'} | ${(r.screenshots || []).join('<br>')} |`),
  '',
  HAS_NATIVE_VIDEO
    ? '_Review videos: native continuous recording (webm) + mp4 renders via the md5-verified static ffmpeg (owner-authorized download)._'
    : '_Review videos are animated GIFs (frame-capture): Playwright webm needs an ffmpeg helper that has no ubuntu26.04-x64 build — HELD honestly, not faked._',
  '',
  '## Skipped (held/planned — honest, not faked)',
  ...skipped.map((s) => `- **${s.service_id}** (${s.status}): ${s.reason}`),
].join('\n'));

const failures = results.filter((r) => !r.ok);
console.log(`\ncrawl: ${report.passed}/${report.crawled} ok; report → artifacts/e2e/reports/crawl-report.md`);
process.exit(failures.length ? 1 : 0);
