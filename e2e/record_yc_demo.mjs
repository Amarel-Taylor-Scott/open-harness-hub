// e2e/record_yc_demo.mjs — narrated YC-demo video.
// Plays architecture/yc_demo_storyboard.json: opens each scene against the (containerized) demo server, injects a
// caption/text-overlay HUD, records Playwright native video, and writes a narration track for the AUDIO step
// (narration -> TTS -> ffmpeg mux). Reuses e2e/gate_common.mjs (native video + dirs), matching record_user_journeys.mjs.
//
// Run:  docker build -f deploy/demo-web.Dockerfile -t aidr-demos . && docker run --rm -p 8088:8088 aidr-demos   (serve)
//       npm i -D playwright && npx playwright install chromium && node e2e/record_yc_demo.mjs                    (record)
//       (audio) TTS each track.narration -> wav, then: ffmpeg -i yc-demo.mp4 -i voice.wav -shortest yc-demo.final.mp4
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { launchGate, finalizeNativeVideo, DIRS, REPO_ROOT, HAS_NATIVE_VIDEO } from './gate_common.mjs';

const SB = JSON.parse(readFileSync(join(REPO_ROOT, 'architecture', 'yc_demo_storyboard.json'), 'utf8'));
const BASE = process.env.DEMO_BASE_URL || SB.base_url;

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

const { browser, context } = await launchGate();
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
if (HAS_NATIVE_VIDEO && video) await finalizeNativeVideo(video, 'yc-demo');
writeFileSync(join(DIRS.videos, 'yc-demo.narration.json'), JSON.stringify({ base: BASE, total_s: t, track }, null, 2));
console.log(`recorded ${SB.scenes.length} scenes (~${t}s) -> artifacts/e2e/videos/yc-demo.* ; narration track written for the TTS+ffmpeg audio step.`);
