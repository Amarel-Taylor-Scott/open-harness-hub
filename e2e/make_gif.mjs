// Stitch the screenshot filmstrip into an animated GIF (pure-JS — no ffmpeg/imagemagick needed).
import GIFEncoder from 'gif-encoder-2';
import { PNG } from 'pngjs';
import fs from 'node:fs';

const ART = process.env.ART || new URL('./artifacts', import.meta.url).pathname;
const OUT = process.env.OUT || 'baltor-demo.gif';
const frames = (process.env.FRAMES ||
  '01-acme-loaded,02-acme-ran,03-node-detail,04-expand-source,05-restricted-denied,06-cfpb-ran,07-reviews,08-review-approved'
).split(',').map(s => s.trim()).filter(Boolean);

function halve(png) {
  const { width: W, height: H, data } = png;
  const w = W >> 1, h = H >> 1;
  const out = new Uint8ClampedArray(w * h * 4);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const s = ((y * 2) * W + (x * 2)) * 4, d = (y * w + x) * 4;
    out[d] = data[s]; out[d + 1] = data[s + 1]; out[d + 2] = data[s + 2]; out[d + 3] = 255;
  }
  return { w, h, out };
}

let enc = null;
for (const name of frames) {
  const p = `${ART}/${name}.png`;
  if (!fs.existsSync(p)) { console.log('  ! missing', name, '(run record_demo.mjs first)'); continue; }
  const png = PNG.sync.read(fs.readFileSync(p));
  const { w, h, out } = halve(png);
  if (!enc) { enc = new GIFEncoder(w, h, 'neuquant', false); enc.setRepeat(0); enc.setDelay(1400); enc.setQuality(12); enc.start(); }
  enc.addFrame(out);
  console.log('  + frame', name, `${w}x${h}`);
}
if (enc) {
  enc.finish();
  const buf = enc.out.getData();
  fs.writeFileSync(`${ART}/${OUT}`, buf);
  console.log(`\nGIF: ${ART}/${OUT} (${(buf.length / 1024 / 1024).toFixed(2)} MB)`);
}
