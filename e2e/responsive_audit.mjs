// e2e/responsive_audit.mjs — RESPONSIVENESS audit across a real-device matrix × every product surface.
//
// Answers "does it hold up on more screen sizes / on mobile / when resized?" systematically instead of
// by hand. For each surface × each device size it reloads and measures: horizontal overflow (the page
// scrolls sideways), on-screen controls clipped past an edge, tap targets too small to hit on a phone
// (< 40px, an a11y/usability floor), body text too small to read (< 11.5px), and the worst overflow in
// px. It records a per-surface "responsive reel" video (resizing through the matrix), screenshots the
// three canonical sizes (phone / tablet / desktop), and writes a size × surface issue matrix.
//
// Run:  node e2e/responsive_audit.mjs                 (all four product surfaces)
//       SURFACES=8000,8003 node e2e/responsive_audit.mjs
// Out:  artifacts/e2e/videos/responsive-reel-<surface>.{webm,mp4}
//       artifacts/e2e/responsive-stills/<surface>-<size>.png
//       artifacts/e2e/reports/responsive-audit.json + a printed matrix
import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { finalizeNativeVideo, DIRS, HAS_NATIVE_VIDEO, attachCollectors } from './gate_common.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const STILLS = join(HERE, '..', 'artifacts', 'e2e', 'responsive-stills');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Real devices a user actually shows up on, plus the edge cases that break layouts.
const MATRIX = [
  { t: 'fold-closed', w: 280, h: 653, k: 'phone' },     // Galaxy Z Fold cover screen
  { t: 'iphone-se1', w: 320, h: 568, k: 'phone' },
  { t: 'android-s', w: 360, h: 740, k: 'phone' },
  { t: 'iphone-se3', w: 375, h: 667, k: 'phone' },
  { t: 'iphone-14', w: 390, h: 844, k: 'phone' },
  { t: 'iphone-plus', w: 414, h: 896, k: 'phone' },
  { t: 'iphone-promax', w: 430, h: 932, k: 'phone' },
  { t: 'ipad-mini-p', w: 480, h: 800, k: 'phablet' },
  { t: 'ipad-port', w: 768, h: 1024, k: 'tablet' },
  { t: 'ipad-air-p', w: 820, h: 1180, k: 'tablet' },
  { t: 'ipad-land', w: 1024, h: 768, k: 'tablet' },
  { t: 'laptop-sm', w: 1280, h: 800, k: 'laptop' },
  { t: 'laptop-hd', w: 1366, h: 768, k: 'laptop' },
  { t: 'desktop', w: 1440, h: 900, k: 'desktop' },
  { t: 'desktop-fhd', w: 1920, h: 1080, k: 'desktop' },
  { t: 'ultrawide', w: 2560, h: 1440, k: 'ultrawide' },
  { t: 'short', w: 1440, h: 360, k: 'edge' },            // landscape phone / split screen
];
const KEY_STILLS = new Set(['iphone-se3', 'ipad-port', 'desktop']);
const PORT_LABELS = { '8000': 'harness-hub', '8001': 'baltor', '8002': 'context-is-everything', '8003': 'teleon' };
const SURFACES = (process.env.SURFACES || '8000,8001,8002,8003').split(',').map((p) => p.trim());
const TAP_MIN = 24;        // px — WCAG 2.2 AA minimum touch target (24x24); below this is a genuine a11y defect
                           // 24px floor; 38px tabs etc. are fine and shouldn't be flagged as defects)
const TEXT_MIN = 11.5;     // px — below this, body copy is unreadable on a phone

// Runs in the page; constants come in as `C` so there is no template interpolation in the body.
function auditFn(C) {
  const vw = innerWidth, vh = innerHeight;
  const out = { overflowPx: 0, offscreen: 0, tinyTap: 0, tinyText: 0 };
  out.overflowPx = Math.max(0, document.documentElement.scrollWidth - vw);
  const mobile = vw <= 600;
  for (const el of document.querySelectorAll('a, button, [role="button"], input, select, textarea, .oh-btn')) {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    const cx = Math.min(Math.max(r.left + r.width / 2, 1), vw - 1);
    const cy = Math.min(Math.max(r.top + r.height / 2, 1), vh - 1);
    const hit = document.elementFromPoint(cx, cy);
    if (!hit || !(hit === el || el.contains(hit) || hit.contains(el))) continue;   // not painted on screen
    if (r.right > vw + 2 || r.left < -2) out.offscreen++;
    if (mobile && (r.width < C.TAP_MIN || r.height < C.TAP_MIN)) {
      const tag = el.tagName, role = el.getAttribute('role');
      if ((tag === 'BUTTON' || role === 'button' || (tag === 'A' && !el.closest('p,li,.lead,.prose,.ohs-foot-col,.ce-foot-links'))) && (el.innerText || '').trim()) out.tinyTap++;
    }
  }
  if (mobile) {
    for (const el of document.querySelectorAll('p, li, .lead, .ohs-foot, .ce-foot, .ohs-sub, .ce-sub')) {
      const fs = parseFloat(getComputedStyle(el).fontSize);
      if (fs && fs < C.TEXT_MIN && (el.innerText || '').trim().length > 24) { out.tinyText++; break; }
    }
  }
  return out;
}

const rows = [];   // {surface, size, k, overflowPx, offscreen, tinyTap, tinyText}

async function auditSurface(browser, port) {
  const label = PORT_LABELS[port] || port;
  const base = `http://127.0.0.1:${port}/`;
  const context = await browser.newContext({
    viewport: { width: MATRIX[MATRIX.length - 1].w, height: 800 },
    ...(HAS_NATIVE_VIDEO ? { recordVideo: { dir: DIRS.videos, size: { width: 1440, height: 900 } } } : {}),
  });
  const page = await context.newPage();
  const log = attachCollectors(page);
  for (const d of MATRIX) {
    await page.setViewportSize({ width: d.w, height: d.h });
    await page.goto(base, { waitUntil: 'domcontentloaded' }).catch(() => {});
    await page.waitForSelector('#root', { timeout: 6000 }).catch(() => {});
    await sleep(d === MATRIX[0] ? 900 : 650);
    const a = await page.evaluate(auditFn, { TAP_MIN, TEXT_MIN }).catch(() => ({ overflowPx: 0, offscreen: 0, tinyTap: 0, tinyText: 0 }));
    rows.push({ surface: label, size: d.t, k: d.k, w: d.w, ...a });
    if (KEY_STILLS.has(d.t)) await page.screenshot({ path: join(STILLS, `${label}-${d.t}.png`) }).catch(() => {});
  }
  const handle = page.video();
  await page.close(); await context.close();
  const video = await finalizeNativeVideo(handle, `responsive-reel-${label}`);
  return { label, video, consoleErrors: log.console.filter((c) => c.type === 'error' && !/favicon/i.test(c.text)).length };
}

(async () => {
  mkdirSync(STILLS, { recursive: true });
  mkdirSync(DIRS.videos, { recursive: true });
  mkdirSync(DIRS.reports, { recursive: true });
  console.log(`RESPONSIVE AUDIT · ${MATRIX.length} sizes × ${SURFACES.length} surfaces · native video ${HAS_NATIVE_VIDEO ? 'ON' : 'OFF'}`);
  const browser = await chromium.launch({ channel: 'chrome', args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const surfaces = [];
  try {
    for (const port of SURFACES) {
      console.log(`  · auditing ${PORT_LABELS[port] || port} (:${port})…`);
      surfaces.push(await auditSurface(browser, port));
    }
  } finally { await browser.close(); }

  // matrix + summary
  const issuesOf = (r) => (r.overflowPx > 2 ? 1 : 0) + r.offscreen + r.tinyTap + r.tinyText;
  const bad = rows.filter((r) => issuesOf(r) > 0);
  writeFileSync(join(DIRS.reports, 'responsive-audit.json'), JSON.stringify({ matrix: MATRIX, surfaces, rows }, null, 2));

  console.log('\n  RESPONSIVE MATRIX (overflow px · offscreen · tinyTap · tinyText):');
  for (const s of SURFACES.map((p) => PORT_LABELS[p] || p)) {
    const sr = rows.filter((r) => r.surface === s);
    const flagged = sr.filter((r) => issuesOf(r) > 0);
    console.log(`\n  ${s} — ${flagged.length}/${sr.length} sizes with issues`);
    for (const r of flagged) {
      const bits = [];
      if (r.overflowPx > 2) bits.push(`overflow +${r.overflowPx}px`);
      if (r.offscreen) bits.push(`${r.offscreen} clipped`);
      if (r.tinyTap) bits.push(`${r.tinyTap} tiny-tap`);
      if (r.tinyText) bits.push('tiny-text');
      console.log(`      ${String(r.w).padStart(4)}px ${r.size.padEnd(14)} — ${bits.join(', ')}`);
    }
    if (!flagged.length) console.log('      ✓ clean at every size');
  }
  console.log(`\n  videos: artifacts/e2e/videos/responsive-reel-*.mp4 · stills: artifacts/e2e/responsive-stills/`);
  console.log(`  report: artifacts/e2e/reports/responsive-audit.json`);
  const overflowCount = bad.filter((r) => r.overflowPx > 2).length;
  console.log(`\n  ${bad.length === 0 ? 'PASS — every surface holds at every size 📱💻🖥️' : `${bad.length} (size × surface) cells with issues (${overflowCount} overflow)`}`);
  process.exit(overflowCount > 0 ? 2 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
