// e2e/record_yc_demo.mjs — narrated YC-demo video (self-sufficient: bundled chromium + recordVideo webm -> mp4 via ffmpeg).
// Plays architecture/yc_demo_storyboard.json against the (containerized) demo server, injects caption/text overlays,
// records real video, and writes a narration track for the AUDIO step (narration -> TTS -> ffmpeg mux).
//
// Run:  (serve)  python3 -m http.server 8088 --directory dist   OR   docker run -p 8088:8088 aidr-demos
//       (record) node e2e/record_yc_demo.mjs                     -> artifacts/e2e/videos/yc-demo.{webm,mp4}
//       (audio)  TTS each track.narration -> voice.wav, then ffmpeg -i yc-demo.mp4 -i voice.wav -shortest final.mp4
import { readFileSync, writeFileSync, mkdirSync, renameSync, existsSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { homedir } from 'node:os';
import { chromium } from 'playwright';

const REPO = join(dirname(fileURLToPath(import.meta.url)), '..');
const VID = join(REPO, 'artifacts', 'e2e', 'videos');
mkdirSync(VID, { recursive: true });
const SB = JSON.parse(readFileSync(join(REPO, 'architecture', 'yc_demo_storyboard.json'), 'utf8'));
const BASE = process.env.DEMO_BASE_URL || SB.base_url;
const FFMPEG = [join(homedir(), '.local', 'share', 'aidr-tools', 'ffmpeg'), process.env.FFMPEG_BIN].find((p) => p && existsSync(p)) || 'ffmpeg';

async function hud(page, text) {
  await page.evaluate((t) => {
    let el = document.getElementById('__yc_caption__');
    if (!el) {
      el = document.createElement('div');
      el.id = '__yc_caption__';
      el.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:2147483647;padding:18px 28px;'
        + 'font:600 23px/1.35 system-ui,-apple-system,Segoe UI,sans-serif;color:#fff;text-align:center;letter-spacing:-.01em;'
        + 'background:linear-gradient(0deg,rgba(15,18,34,.94),rgba(15,18,34,0))';
      document.body.appendChild(el);
    }
    el.textContent = t;
  }, text);
}

// Use whichever chromium build is actually installed (avoids playwright version<->build-number mismatches).
function findChrome() {
  const base = join(homedir(), '.cache', 'ms-playwright');
  const cands = [];
  try {
    for (const d of readdirSync(base)) {
      if (d.startsWith('chromium-')) cands.push(join(base, d, 'chrome-linux64', 'chrome'), join(base, d, 'chrome-linux', 'chrome'));
      if (d.startsWith('chromium_headless_shell-')) cands.push(join(base, d, 'chrome-headless-shell-linux64', 'chrome-headless-shell'));
    }
  } catch { /* fall through to playwright default */ }
  return cands.find((p) => existsSync(p));
}
const executablePath = process.env.CHROME_BIN || findChrome();
const browser = await chromium.launch({ headless: true, executablePath, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, recordVideo: { dir: VID, size: { width: 1280, height: 800 } } });
const page = await context.newPage();
const track = [];
let t = 0;
for (const s of SB.scenes) {
  await page.goto(BASE + s.url, { waitUntil: 'load' });
  if (s.scroll_to) {
    await page.evaluate((sel) => { const e = document.querySelector(sel); if (e) e.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, s.scroll_to).catch(() => {});
    await page.waitForTimeout(900);
  }
  await hud(page, s.caption);
  track.push({ id: s.id, at_s: t, seconds: s.seconds, caption: s.caption, narration: s.narration });
  t += s.seconds;
  await page.waitForTimeout(s.seconds * 1000);
}
const video = page.video();
await page.close(); await context.close(); await browser.close();
const out = { webm: null, mp4: null };
if (video) {
  const raw = await video.path();
  const webm = join(VID, 'yc-demo.webm');
  renameSync(raw, webm); out.webm = 'yc-demo.webm';
  const res = spawnSync(FFMPEG, ['-y', '-loglevel', 'error', '-i', webm, '-movflags', '+faststart', '-pix_fmt', 'yuv420p', join(VID, 'yc-demo.mp4')]);
  if (res.status === 0) out.mp4 = 'yc-demo.mp4';
}
writeFileSync(join(VID, 'yc-demo.narration.json'), JSON.stringify({ base: BASE, total_s: t, track }, null, 2));
console.log(`recorded ${SB.scenes.length} scenes (~${t}s) -> artifacts/e2e/videos/${out.mp4 || out.webm || 'NONE'}; narration track written.`);
