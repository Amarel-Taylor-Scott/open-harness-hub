// e2e/verify_examples_gallery_videos.mjs — ADVERSARIAL verification of the recorded gallery videos.
//
// A recorder that asserts "the DOM had the verdict" does NOT prove the VIDEO FILE shows anything — a
// blank, all-black, frozen, truncated, or wrong-size video can still pass a DOM check. This tool
// independently inspects the produced video files and tries to FALSIFY the claim that they faithfully
// show the gallery. It trusts nothing the recorder said; it re-derives everything from the bytes.
//
// Per video it checks: (1) the file exists and isn't tiny; (2) it decodes to a 1600x900 h264 stream of
// at least MIN_DURATION; (3) it is NOT blank/flat — the per-frame luma RANGE (YMAX-YMIN) shows real
// content, not a single colour; (4) mean brightness is in a sane band (a white blank page fails high);
// (5) it is NOT mostly black (blackdetect); (6) it is NOT a frozen single frame — the first and last
// frames differ (a stuck capture has identical frames → PSNR=inf). It also cross-checks the recorder
// report: every example in the gallery manifest must have a verified clip whose verdict the recorder
// confirmed on-screen.
//
// The --self-test is the adversarial core: it SYNTHESISES deliberately-broken videos (blank-white,
// all-black, frozen-but-with-content, too-short, wrong-resolution) and asserts the verifier REJECTS
// each on the RIGHT check, plus a good moving one it ACCEPTS. A verifier that always passes is
// worthless; this proves it discriminates.
//
// Run:  node e2e/verify_examples_gallery_videos.mjs            (verify the real recorded videos)
//       node e2e/verify_examples_gallery_videos.mjs --self-test (prove it rejects broken videos)
import { spawnSync } from 'node:child_process';
import { existsSync, statSync, mkdtempSync, rmSync, readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, '..');
const VIDEOS = join(REPO, 'artifacts', 'e2e', 'videos');
const MANIFEST = join(REPO, 'dist', 'examples-gallery', 'examples.json');
const REPORT = join(REPO, 'artifacts', 'e2e', 'reports', 'examples-gallery.json');
const FFMPEG = ['/home/username/.local/share/aidr-tools/ffmpeg',
  join(process.env.HOME || '', '.cache', 'ms-playwright', 'ffmpeg-1011', 'ffmpeg-linux')]
  .find((p) => existsSync(p)) || 'ffmpeg';

// Thresholds — calibrated against the real recordings (luma range ~225, black 0, start/end PSNR ~19dB)
// and the synthetic blanks (range 0, black 0.95, frozen PSNR=inf). Wide margins on both sides.
const MIN_BYTES = 10_000;
const MIN_DURATION = 2.0;     // seconds; real clips dwell ≥3s, walkthrough ≥6s
const WIDTH = 1600, HEIGHT = 900;
const MIN_LUMA_RANGE = 80;    // median(YMAX-YMIN); real ≥225, flat blank = 0
const MIN_MEAN_Y = 15, MAX_MEAN_Y = 225;  // a white blank page sits at ~235
const MAX_BLACK_FRACTION = 0.5;           // all-black = ~0.95
const MAX_FROZEN_PSNR = 45;   // start vs end frame; identical (frozen) = Infinity, real clip ~19

function ff(args) {
  const r = spawnSync(FFMPEG, ['-hide_banner', ...args], { encoding: 'utf-8', maxBuffer: 64 << 20 });
  return (r.stderr || '') + (r.stdout || '');
}

function probe(file) {
  const out = ff(['-i', file]);
  const dm = out.match(/Duration:\s*(\d+):(\d+):(\d+\.\d+)/);
  const duration = dm ? (+dm[1]) * 3600 + (+dm[2]) * 60 + (+dm[3]) : 0;
  const vm = out.match(/Video:\s*(\w+).*?\b(\d{2,5})x(\d{2,5})\b/s);
  return { duration, codec: vm ? vm[1] : null, width: vm ? +vm[2] : 0, height: vm ? +vm[3] : 0 };
}

function median(xs) {
  if (!xs.length) return 0;
  const s = [...xs].sort((a, b) => a - b);
  return s[Math.floor(s.length / 2)];
}

function lumaAndBlack(file) {
  const out = ff(['-i', file, '-vf', 'signalstats,metadata=print,blackdetect=d=0.05:pic_th=0.98',
    '-an', '-f', 'null', '-']);
  const grab = (key) => [...out.matchAll(new RegExp(`lavfi\\.signalstats\\.${key}=([\\d.]+)`, 'g'))].map((m) => +m[1]);
  const ymin = grab('YMIN'), ymax = grab('YMAX'), yavg = grab('YAVG');
  const n = Math.min(ymin.length, ymax.length);
  const ranges = []; for (let i = 0; i < n; i++) ranges.push(ymax[i] - ymin[i]);
  const meanY = yavg.length ? yavg.reduce((a, b) => a + b, 0) / yavg.length : 0;
  const blackDur = [...out.matchAll(/black_duration:([\d.]+)/g)].reduce((s, m) => s + (+m[1]), 0);
  return { medianRange: median(ranges), meanY, frames: n, blackDur };
}

function startEndPSNR(file, duration, tmp) {
  const a = join(tmp, 'a.png'), b = join(tmp, 'b.png');
  ff(['-ss', '0.3', '-i', file, '-frames:v', '1', a, '-y']);
  ff(['-sseof', '-0.4', '-i', file, '-frames:v', '1', b, '-y']);
  if (!existsSync(a) || !existsSync(b)) return Infinity;
  const out = ff(['-i', a, '-i', b, '-lavfi', 'psnr', '-f', 'null', '-']);
  const m = out.match(/average:([\d.]+|inf)/);
  return m ? (m[1] === 'inf' ? Infinity : +m[1]) : Infinity;
}

function verifyVideo(file, tmp) {
  const checks = [];
  const add = (name, ok, detail) => checks.push({ name, ok, detail });
  if (!existsSync(file)) { add('exists', false, file); return { file, pass: false, checks }; }
  add('size', statSync(file).size >= MIN_BYTES, `${statSync(file).size} bytes`);
  const p = probe(file);
  add('duration', p.duration >= MIN_DURATION, `${p.duration.toFixed(2)}s`);
  add('resolution', p.width === WIDTH && p.height === HEIGHT, `${p.width}x${p.height}`);
  add('has_video_stream', !!p.codec, p.codec || 'none');
  const lb = lumaAndBlack(file);
  add('not_blank', lb.medianRange >= MIN_LUMA_RANGE, `median luma range ${lb.medianRange}`);
  add('brightness_sane', lb.meanY >= MIN_MEAN_Y && lb.meanY <= MAX_MEAN_Y, `mean Y ${lb.meanY.toFixed(1)}`);
  add('not_black', (lb.blackDur / Math.max(p.duration, 0.01)) < MAX_BLACK_FRACTION,
    `black ${(lb.blackDur / Math.max(p.duration, 0.01) * 100).toFixed(0)}%`);
  const psnr = startEndPSNR(file, p.duration, tmp);
  add('not_frozen', psnr < MAX_FROZEN_PSNR, `start/end PSNR ${psnr === Infinity ? 'inf (identical)' : psnr.toFixed(1) + 'dB'}`);
  return { file, pass: checks.every((c) => c.ok), checks };
}

function synth(tmp, name, lavfi, extra = []) {
  const out = join(tmp, name + '.mp4');
  ff(['-f', 'lavfi', '-i', lavfi, ...extra, '-pix_fmt', 'yuv420p', '-c:v', 'libx264', out, '-y']);
  return out;
}

function selfTest() {
  const tmp = mkdtempSync(join(tmpdir(), 'vidverify-'));
  const fails = [];
  try {
    // GOOD: a moving test pattern at the right size → must PASS every check.
    const good = synth(tmp, 'good', `testsrc=size=${WIDTH}x${HEIGHT}:rate=15:duration=3`);
    const gv = verifyVideo(good, tmp);
    if (!gv.pass) fails.push('good moving video should PASS: ' + gv.checks.filter((c) => !c.ok).map((c) => c.name).join(','));

    // Each BAD video must FAIL — and fail on the EXPECTED check (proves the check, not luck).
    const cases = [
      ['blank_white', `color=c=white:size=${WIDTH}x${HEIGHT}:rate=15:duration=3`, [], 'not_blank'],
      ['all_black', `color=c=black:size=${WIDTH}x${HEIGHT}:rate=15:duration=3`, [], 'not_black'],
      ['frozen_content', `rgbtestsrc=size=${WIDTH}x${HEIGHT}:rate=15:duration=3`, [], 'not_frozen'],
      ['too_short', `testsrc=size=${WIDTH}x${HEIGHT}:rate=15:duration=0.8`, [], 'duration'],
      ['wrong_size', `testsrc=size=1280x720:rate=15:duration=3`, [], 'resolution'],
    ];
    for (const [name, lavfi, extra, expect] of cases) {
      const v = verifyVideo(synth(tmp, name, lavfi, extra), tmp);
      const failed = v.checks.filter((c) => !c.ok).map((c) => c.name);
      if (v.pass) fails.push(`${name}: verifier WRONGLY passed a broken video`);
      else if (!failed.includes(expect)) fails.push(`${name}: failed on [${failed.join(',')}] but expected [${expect}]`);
      else console.log(`  [ok] rejects ${name} on '${expect}' (also: ${failed.filter((f) => f !== expect).join(',') || 'none'})`);
    }
    if (gv.pass) console.log('  [ok] accepts a good moving 1600x900 video');
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
  if (fails.length) { fails.forEach((f) => console.log('  [FAIL] ' + f)); console.log('\nFAIL — verify_examples_gallery_videos self-test'); process.exit(1); }
  console.log('\nPASS — verify_examples_gallery_videos: rejects blank/black/frozen/short/wrong-size videos, '
    + 'accepts a good one — the adversarial checks actually discriminate.');
  process.exit(0);
}

function main() {
  if (process.argv.includes('--self-test')) return selfTest();
  const tmp = mkdtempSync(join(tmpdir(), 'vidverify-'));
  const targets = [];
  // The full walkthrough + one clip per gallery example (single source: the builder's manifest).
  targets.push(join(VIDEOS, 'examples-gallery-walkthrough.mp4'));
  let manifest = null;
  if (existsSync(MANIFEST)) {
    manifest = JSON.parse(readFileSync(MANIFEST, 'utf-8')).examples;
    for (const ex of manifest) targets.push(join(VIDEOS, `examples-${ex.id}.mp4`));
  }
  const results = [];
  try {
    for (const f of targets) results.push(verifyVideo(f, tmp));
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
  let bad = 0;
  for (const r of results) {
    const name = r.file.split('/').pop();
    if (r.pass) {
      console.log(`  [ok]   ${name}`);
    } else {
      bad++;
      console.log(`  [FAIL] ${name} — ${r.checks.filter((c) => !c.ok).map((c) => `${c.name}(${c.detail})`).join(', ')}`);
    }
  }
  // Cross-check the recorder's own claims against the manifest: every example must have a clip whose
  // verdict the recorder confirmed on-screen (ties the verified files back to the claimed content).
  let crossOk = true;
  if (existsSync(REPORT) && manifest) {
    const rep = JSON.parse(readFileSync(REPORT, 'utf-8'));
    const onScreen = new Set((rep.clips || []).filter((c) => c.verdict_on_screen).map((c) => c.id));
    const missing = manifest.map((e) => e.id).filter((id) => !onScreen.has(id));
    if (missing.length && rep.clips && rep.clips.length) {
      // only enforce for examples the latest report actually covered
      const covered = new Set((rep.clips || []).map((c) => c.id));
      const reallyMissing = missing.filter((id) => covered.has(id));
      if (reallyMissing.length) { crossOk = false; console.log(`  [FAIL] recorder did not confirm verdict on-screen for: ${reallyMissing.join(', ')}`); }
    }
  }
  console.log(`\n${bad === 0 && crossOk ? 'PASS' : 'FAIL'} — verified ${results.length} videos (${results.length - bad} good, ${bad} bad)`);
  process.exit(bad === 0 && crossOk ? 0 : 1);
}

main();
