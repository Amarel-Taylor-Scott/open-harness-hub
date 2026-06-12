// e2e/record_examples_gallery.mjs — narrated VIDEO recordings of the Governed Examples Gallery.
//
// Self-contained: builds the gallery from the REAL pipelines, serves dist/examples-gallery/ on a
// local port, then records (a) one full walkthrough video scrolling every example with dwell time,
// and (b) one short clip per example deep-linked to its card — ASSERTING each card's real verdict
// (read from the builder's examples.json sidecar, never typed here) is actually on screen. The
// server is killed by its exact PID. Output: artifacts/e2e/videos/examples-*.{webm,mp4} +
// per-card stills + a report at artifacts/e2e/reports/examples-gallery.json.
//
// Run:  node e2e/record_examples_gallery.mjs            (default: all examples + walkthrough)
//       node e2e/record_examples_gallery.mjs sanctions_aml_screening cve_dependency_triage
//
// Prereq: examples-gallery is built by scripts/build_examples_gallery.py (this script runs it).
import { chromium } from 'playwright';
import { spawn, spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { finalizeNativeVideo, DIRS, HAS_NATIVE_VIDEO } from './gate_common.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..');
const PORT = Number(process.env.PORT || 9108);
const BASE = `http://127.0.0.1:${PORT}`;
const SIZE = { width: 1600, height: 900 };
const GALLERY_DIR = join(REPO, 'dist', 'examples-gallery');
const STILLS = join(REPO, 'artifacts', 'e2e', 'examples-stills');
const PY = process.env.PYTHON || 'python3';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// 1. Build the gallery from the real pipelines (fresh, deterministic output).
function buildGallery() {
  const r = spawnSync(PY, ['scripts/build_examples_gallery.py'],
    { cwd: REPO, env: { ...process.env, PYTHONPATH: REPO }, encoding: 'utf-8' });
  if (r.status !== 0) { console.error(r.stdout || '', r.stderr || ''); throw new Error('gallery build failed'); }
  process.stdout.write(`  · ${(r.stdout || '').trim()}\n`);
  const manifest = JSON.parse(readFileSync(join(GALLERY_DIR, 'examples.json'), 'utf-8'));
  return manifest.examples;
}

// 2. Serve the static gallery; return the child so we can kill it by exact PID.
async function serveGallery() {
  const srv = spawn(PY, ['-m', 'http.server', String(PORT), '--bind', '127.0.0.1', '--directory', GALLERY_DIR],
    { cwd: REPO, stdio: 'ignore' });
  for (let i = 0; i < 60; i++) {
    try {
      const res = await fetch(`${BASE}/`, { signal: AbortSignal.timeout(1000) });
      if (res.ok) return srv;
    } catch { /* not up yet */ }
    await sleep(250);
  }
  throw new Error('gallery server did not come up');
}

async function recordWalkthrough(browser, examples) {
  const context = await browser.newContext({
    viewport: SIZE,
    ...(HAS_NATIVE_VIDEO ? { recordVideo: { dir: DIRS.videos, size: SIZE } } : {}),
  });
  const page = await context.newPage();
  const chapters = [];
  await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('.hero h1');
  await sleep(2500); // dwell on the hero
  chapters.push({ at: 'hero', title: await page.textContent('.hero h1') });
  let onScreen = 0;
  for (const ex of examples) {
    const card = page.locator(`#ex-${ex.id}`);
    await card.scrollIntoViewIfNeeded();
    await sleep(2600); // real dwell so the card is readable in the video
    // the verdict chip text really is on screen
    const chipVisible = await page.locator(`#ex-${ex.id} .chip`, { hasText: ex.verdict.slice(0, 24) }).count();
    if (chipVisible) onScreen++;
    await page.screenshot({ path: join(STILLS, `card-${String(onScreen).padStart(2, '0')}-${ex.id}.png`) }).catch(() => {});
    chapters.push({ at: ex.id, verdict: ex.verdict, chip_on_screen: chipVisible > 0 });
  }
  await sleep(1200);
  const handle = page.video();
  await page.close();
  await context.close();
  const out = await finalizeNativeVideo(handle, 'examples-gallery-walkthrough');
  return { video: out, chapters, verdicts_on_screen: onScreen, total: examples.length };
}

async function recordOne(browser, ex) {
  const context = await browser.newContext({
    viewport: SIZE,
    ...(HAS_NATIVE_VIDEO ? { recordVideo: { dir: DIRS.videos, size: SIZE } } : {}),
  });
  const page = await context.newPage();
  await page.goto(`${BASE}/#ex-${ex.id}`, { waitUntil: 'domcontentloaded' });
  await page.locator(`#ex-${ex.id}`).scrollIntoViewIfNeeded();
  await sleep(700);
  // ASSERT the real verdict (from the builder) is the chip text on screen.
  const chip = (await page.locator(`#ex-${ex.id} .chip`).textContent().catch(() => '')) || '';
  const ok = chip.includes(ex.verdict.slice(0, 24));
  await sleep(3200); // dwell so the clip shows the contrast + verdict + trace
  await page.screenshot({ path: join(STILLS, `clip-${ex.id}.png`) }).catch(() => {});
  const handle = page.video();
  await page.close();
  await context.close();
  const out = await finalizeNativeVideo(handle, `examples-${ex.id}`);
  return { id: ex.id, verdict: ex.verdict, verdict_on_screen: ok, video: out };
}

(async () => {
  mkdirSync(STILLS, { recursive: true });
  mkdirSync(DIRS.videos, { recursive: true });
  mkdirSync(DIRS.reports, { recursive: true });
  console.log(`examples-gallery recorder · native video: ${HAS_NATIVE_VIDEO ? 'ON (webm + mp4)' : 'OFF'} · ${SIZE.width}×${SIZE.height}`);

  const all = buildGallery();
  const pick = process.argv.slice(2);
  const examples = pick.length ? all.filter((e) => pick.includes(e.id)) : all;
  if (!examples.length) { console.error('no matching examples:', pick.join(', ')); process.exit(1); }

  const srv = await serveGallery();
  console.log(`  · serving ${GALLERY_DIR} on ${BASE} (pid ${srv.pid})`);
  const browser = await chromium.launch({ channel: 'chrome', args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const report = { generated_at: new Date().toISOString(), base: BASE, size: SIZE, clips: [], walkthrough: null };
  try {
    report.walkthrough = await recordWalkthrough(browser, examples);
    console.log(`  [walkthrough] ${report.walkthrough.video ? (report.walkthrough.video.mp4 || report.walkthrough.video.webm) : 'NO VIDEO'} · ${report.walkthrough.verdicts_on_screen}/${report.walkthrough.total} verdicts on screen`);
    for (const ex of examples) {
      const clip = await recordOne(browser, ex);
      report.clips.push(clip);
      console.log(`  [clip] ${ex.id}: ${clip.video ? (clip.video.mp4 || clip.video.webm) : 'NO VIDEO'} · verdict on screen: ${clip.verdict_on_screen ? 'yes' : 'NO'}`);
    }
  } finally {
    await browser.close();
    try { process.kill(srv.pid, 'SIGTERM'); } catch { /* already gone */ }
  }

  writeFileSync(join(DIRS.reports, 'examples-gallery.json'), JSON.stringify(report, null, 2));
  const clipsOk = report.clips.filter((c) => c.video && c.verdict_on_screen).length;
  const walkOk = report.walkthrough && report.walkthrough.video && report.walkthrough.verdicts_on_screen === report.walkthrough.total;
  console.log(`\n  ${clipsOk}/${examples.length} example clips recorded with the real verdict on screen; walkthrough ${walkOk ? 'OK' : 'INCOMPLETE'}.`);
  console.log(`  report: artifacts/e2e/reports/examples-gallery.json · videos: artifacts/e2e/videos/examples-*.{webm,mp4}`);
  process.exit(clipsOk === examples.length && walkOk ? 0 : 1);
})().catch((e) => { console.error(e); process.exit(1); });
