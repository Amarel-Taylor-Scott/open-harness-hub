/* e2e/gate_common.mjs — shared plumbing for the Browser E2E + Local Service Emulation Gate.
   Real Chrome via Playwright (channel: 'chrome'), per-page VIDEO recording, 1440/1280/390 screenshots,
   console/pageerror/network-failure capture, overflow + dead-link checks. Artifacts land under
   artifacts/e2e/{videos,screenshots,html,console,network,reports}/ for owner review.
   Law: no fake URLs (localhost only unless a real tunnel URL is passed in), no raw secrets in any
   artifact (callers must blur/redact secret-bearing fields BEFORE capture). */
import { chromium } from 'playwright';
import GIFEncoder from 'gif-encoder-2';
import { PNG } from 'pngjs';
import { mkdirSync, writeFileSync, existsSync, renameSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { homedir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

export const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
export const ART = join(REPO_ROOT, 'artifacts', 'e2e');
export const DIRS = Object.fromEntries(
  ['videos', 'screenshots', 'html', 'console', 'network', 'reports']
    .map((d) => [d, join(ART, d)]));
for (const d of Object.values(DIRS)) mkdirSync(d, { recursive: true });

export const VIEWPORTS = [
  { tag: '1440', width: 1440, height: 900 },
  { tag: '1280', width: 1280, height: 800 },
  { tag: '390', width: 390, height: 844 },
];

/* Static ffmpeg (7.0.2, md5-verified, owner-authorized download 2026-06-09) — placed both in local
   tooling and at Playwright's expected helper path, enabling NATIVE continuous webm recording.
   When absent, the GIF frame-capture fallback below still produces review videos. */
export const FFMPEG = [
  join(homedir(), '.local', 'share', 'aidr-tools', 'ffmpeg'),
  join(homedir(), '.cache', 'ms-playwright', 'ffmpeg-1011', 'ffmpeg-linux'),
].find((p) => existsSync(p)) || null;
export const HAS_NATIVE_VIDEO = Boolean(FFMPEG);

export async function launchGate() {
  const browser = await chromium.launch({
    channel: 'chrome', headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    ...(HAS_NATIVE_VIDEO
      ? { recordVideo: { dir: DIRS.videos, size: { width: 1280, height: 800 } } } : {}),
  });
  return { browser, context };
}

/* After context.close(): give the native webm a friendly name and render an mp4 (H.264, faststart)
   for easy review. Returns { webm, mp4 } file names or null. */
export async function finalizeNativeVideo(video, base) {
  if (!video) return null;
  let raw;
  try { raw = await video.path(); } catch { return null; }
  const webm = join(DIRS.videos, `${base}.webm`);
  try { renameSync(raw, webm); } catch { return null; }
  let mp4 = `${base}.mp4`;
  const res = spawnSync(FFMPEG, ['-y', '-loglevel', 'error', '-i', webm,
    '-movflags', '+faststart', '-pix_fmt', 'yuv420p', join(DIRS.videos, mp4)]);
  if (res.status !== 0) mp4 = null;
  return { webm: `${base}.webm`, mp4 };
}

/* Review "video" recorder — Playwright's webm path needs an ffmpeg helper that does not exist for
   ubuntu26.04-x64, so we use the repo's established pattern (see make_gif.mjs): interval frame
   capture → animated GIF. Frames are page.screenshots, so secret-field blur/redaction CSS applies
   to every frame. */
export class FlowRecorder {
  constructor(page, name, { intervalMs = 700, delayMs = 550 } = {}) {
    this.page = page; this.name = name; this.frames = [];
    this.intervalMs = intervalMs; this.delayMs = delayMs;
    this._busy = false; this._timer = null;
  }
  async snap() {
    if (this._busy || this.page.isClosed()) return;
    this._busy = true;
    try { this.frames.push(await this.page.screenshot({ type: 'png' })); } catch {}
    this._busy = false;
  }
  start() { this._timer = setInterval(() => this.snap(), this.intervalMs); return this; }
  async stop() {
    if (this._timer) clearInterval(this._timer);
    await this.snap().catch(() => {});
    if (!this.frames.length) return null;
    let enc = null;
    for (const buf of this.frames) {
      const png = PNG.sync.read(buf);
      const w = png.width >> 1, h = png.height >> 1;
      const out = new Uint8ClampedArray(w * h * 4);
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        const s = ((y * 2) * png.width + (x * 2)) * 4, d = (y * w + x) * 4;
        out[d] = png.data[s]; out[d + 1] = png.data[s + 1];
        out[d + 2] = png.data[s + 2]; out[d + 3] = 255;
      }
      if (!enc) {
        enc = new GIFEncoder(w, h, 'neuquant', false);
        enc.setRepeat(0); enc.setDelay(this.delayMs); enc.setQuality(12); enc.start();
      }
      enc.addFrame(out);
    }
    enc.finish();
    const file = `${this.name}.gif`;
    writeFileSync(join(DIRS.videos, file), enc.out.getData());
    return { file, frames: this.frames.length };
  }
}

/* Attach console / uncaught-error / failed-request collectors to a page. */
export function attachCollectors(page) {
  const log = { console: [], pageErrors: [], requestFailures: [] };
  page.on('console', (m) => log.console.push({ type: m.type(), text: m.text().slice(0, 400) }));
  page.on('pageerror', (e) => log.pageErrors.push(String(e).slice(0, 400)));
  page.on('requestfailed', (r) => log.requestFailures.push(
    { url: r.url().slice(0, 200), failure: r.failure()?.errorText }));
  return log;
}

export async function hasHorizontalOverflow(page) {
  return page.evaluate(() =>
    document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
}

/* Screenshot the page at every gate viewport. Returns the file names. */
export async function shootViewports(page, name) {
  const files = [];
  for (const vp of VIEWPORTS) {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    await page.waitForTimeout(250);
    const file = `${name}-${vp.tag}px.png`;
    await page.screenshot({ path: join(DIRS.screenshots, file), fullPage: vp.tag !== '390' });
    files.push(file);
  }
  await page.setViewportSize({ width: 1280, height: 800 });
  return files;
}

/* Same-origin dead-link sweep (capped) using the context's request client. */
export async function deadLinkSweep(page, cap = 40) {
  const origin = new URL(page.url()).origin;
  const hrefs = await page.evaluate(() =>
    Array.from(document.querySelectorAll('a[href]'), (a) => a.href));
  const sameOrigin = [...new Set(hrefs)]
    .filter((h) => h.startsWith(origin) && !h.includes('#')).slice(0, cap);
  const dead = [];
  for (const url of sameOrigin) {
    try {
      const resp = await page.request.get(url, { timeout: 5000 });
      if (resp.status() >= 400) dead.push({ url, status: resp.status() });
    } catch { dead.push({ url, status: 'unreachable' }); }
  }
  return { checked: sameOrigin.length, dead };
}

export function saveText(dir, file, text) { writeFileSync(join(DIRS[dir], file), text); }
export function saveJSON(dir, file, obj) { saveText(dir, file, JSON.stringify(obj, null, 2)); }
