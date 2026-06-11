// e2e/narrate_videos.mjs — add a VOICE-OVER track to the journey videos.
//
// For every journey in the run report, each chapter caption is synthesized (Microsoft Edge
// neural TTS via msedge-tts — no key needed) and placed on the timeline at its chapter
// timestamp; clips that would overrun the gap to the next chapter are tempo-adjusted (≤1.4×)
// and trimmed so narration never overlaps. Output: narrated mp4s (H.264 copied, AAC audio)
// in artifacts/e2e/videos-narrated/, verified with ffprobe (audio stream present, duration
// matches the video). The silent originals stay untouched (lossless).
//
// Run: node e2e/narrate_videos.mjs [journey-id ...]     (default: every journey in the report)

import { MsEdgeTTS, OUTPUT_FORMAT } from 'msedge-tts';
import { readFileSync, writeFileSync, mkdirSync, existsSync, statSync, createWriteStream, rmSync, renameSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { homedir } from 'node:os';

const HERE = dirname(fileURLToPath(import.meta.url));
const VIDEOS = join(HERE, 'artifacts', 'e2e', '..', '..', '..', 'artifacts', 'e2e', 'videos');
const VIDEO_DIR = join(HERE, '..', 'artifacts', 'e2e', 'videos');
const OUT_DIR = join(HERE, '..', 'artifacts', 'e2e', 'videos-narrated');
const REPORT = join(HERE, '..', 'artifacts', 'e2e', 'reports', 'user-journeys.json');
const FFMPEG = [join(homedir(), '.local', 'share', 'aidr-tools', 'ffmpeg'),
  join(homedir(), '.cache', 'ms-playwright', 'ffmpeg-1011', 'ffmpeg-linux')].find((p) => existsSync(p));
const VOICE = 'en-US-AndrewNeural';
mkdirSync(OUT_DIR, { recursive: true });

if (!FFMPEG) { console.error('no ffmpeg'); process.exit(1); }

function ff(args) { return spawnSync(FFMPEG, args, { encoding: 'utf-8' }); }
function probeDuration(file) {
  const r = ff(['-i', file, '-hide_banner']);
  const m = /Duration: (\d+):(\d+):(\d+\.\d+)/.exec(r.stderr || '');
  return m ? (+m[1]) * 3600 + (+m[2]) * 60 + (+m[3]) : null;
}
function probeHasAudio(file) {
  const r = ff(['-i', file, '-hide_banner']);
  return /Stream #.*Audio/.test(r.stderr || '');
}

// strip glyphs/URLs the voice shouldn't read literally
function speakable(caption) {
  return caption
    .replace(/[⌘◌✔▲⛁◈⚡↻⊘⎘◳⟳⬡◇✦⊨⇌·—–]+/g, ' ')
    .replace(/https?:\/\/\S+/g, 'the public link')
    .replace(/\([^)]*deep link[^)]*\)/gi, '')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

async function ttsTo(file, text) {
  const tts = new MsEdgeTTS();
  await tts.setMetadata(VOICE, OUTPUT_FORMAT.AUDIO_24KHZ_48KBITRATE_MONO_MP3);
  const { audioStream } = await tts.toStream(text);
  const out = createWriteStream(file);
  audioStream.pipe(out);
  await new Promise((res, rej) => { out.on('finish', res); out.on('error', rej); });
  return statSync(file).size > 400;
}

const report = JSON.parse(readFileSync(REPORT, 'utf-8'));
const only = process.argv.slice(2).filter((a) => !a.startsWith('-'));
const targets = report.results.filter((j) => (!only.length || only.includes(j.id)) && j.video && j.video.mp4);

let failures = 0;
for (const j of targets) {
  const video = join(VIDEO_DIR, j.video.mp4);
  if (!existsSync(video)) { console.log(`  [skip] ${j.id} — video missing`); continue; }
  const vidDur = probeDuration(video) || (j.duration_s + 4);
  const tmp = join(OUT_DIR, `.tmp-${j.id}`);
  rmSync(tmp, { recursive: true, force: true });
  mkdirSync(tmp, { recursive: true });
  // synthesize concurrently (batches of 6) — serial TTS was the bottleneck
  const specs = j.chapters.map((c, i) => ({ c, i, text: speakable(c.caption) })).filter((s) => s.text);
  for (let b = 0; b < specs.length; b += 6) {
    await Promise.all(specs.slice(b, b + 6).map(async (s) => {
      try { s.ok = await ttsTo(join(tmp, `c${s.i}.mp3`), s.text); } catch (e) { s.ok = false; }
    }));
  }
  const clips = [];
  for (const s of specs) {
    if (!s.ok) { console.log(`  [tts-miss] ${j.id} c${s.i}`); continue; }
    const { c, i } = s;
    const gap = Math.max(1.2, (i + 1 < j.chapters.length ? j.chapters[i + 1].at_s : vidDur) - c.at_s - 0.4);
    const raw = join(tmp, `c${i}.mp3`);
    let dur = probeDuration(raw) || 2;
    let use = raw;
    if (dur > gap) {
      const tempo = Math.min(1.4, dur / gap);
      const fitted = join(tmp, `c${i}-fit.mp3`);
      ff(['-y', '-loglevel', 'error', '-i', raw, '-filter:a', `atempo=${tempo.toFixed(3)}`, '-t', gap.toFixed(2), fitted]);
      if (existsSync(fitted)) { use = fitted; dur = Math.min(dur / tempo, gap); }
    }
    clips.push({ file: use, at: Math.max(0.2, c.at_s) });
  }
  if (!clips.length) { console.log(`  [skip] ${j.id} — no narration clips`); continue; }

  const args = ['-y', '-nostdin', '-loglevel', 'error', '-i', video];
  clips.forEach((c) => args.push('-i', c.file));
  const delays = clips.map((c, i) => `[${i + 1}:a]adelay=${Math.round(c.at * 1000)}|${Math.round(c.at * 1000)}[a${i}]`).join(';');
  const mixIn = clips.map((_, i) => `[a${i}]`).join('');
  const out = join(OUT_DIR, j.video.mp4);
  const part = `${out}.part.mp4`;
  // -t caps the output explicitly: apad makes the mixed audio infinite, and with stream-copied
  // video -shortest alone never terminates (observed: muxes spinning 100+ min on 1-min videos)
  args.push('-filter_complex', `${delays};${mixIn}amix=inputs=${clips.length}:normalize=0,apad[aud]`,
    '-map', '0:v', '-map', '[aud]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '96k',
    '-t', (vidDur + 0.2).toFixed(2), part);
  const r = ff(args);
  const ok = r.status === 0 && existsSync(part) && probeHasAudio(part)
    && Math.abs((probeDuration(part) || 0) - vidDur) < 3;
  if (ok) renameSync(part, out); else rmSync(part, { force: true });
  console.log(`  [${ok ? 'ok' : 'FAIL'}] ${j.id} — ${clips.length} narration clips${ok ? '' : ' — ' + (r.stderr || '').slice(-160)}`);
  if (!ok) failures += 1;
  rmSync(tmp, { recursive: true, force: true });
}
console.log(`\n${failures ? 'FAIL' : 'PASS'} — narrated ${targets.length - failures}/${targets.length} videos → ${OUT_DIR}`);
process.exit(failures ? 1 : 0);
