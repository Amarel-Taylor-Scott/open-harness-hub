// Drive the DEV FLYWHEEL dashboard (the builder's view) in real Chrome, assert it renders the live
// dev-status feed (proofs grid, flywheel metric, timeline, backlog), and capture a screenshot.
//   prereq: PYTHONPATH=. python3 scripts/baltor_admin_demo_server.py --port 9307
//   run:    BASE=http://127.0.0.1:9307 node record_dev_dashboard.mjs
import { chromium } from 'playwright';
import fs from 'node:fs';

const BASE = process.env.BASE || 'http://127.0.0.1:9307';
const ART = new URL('./artifacts', import.meta.url).pathname;
fs.mkdirSync(ART, { recursive: true });
const results = [];
const ok = (n, c, d = '') => { results.push({ n, c: !!c }); console.log(`  [${c ? 'ok' : 'FAIL'}] ${n}${c ? '' : ' :: ' + d}`); };

const browser = await chromium.launch({ channel: 'chrome', args: ['--no-sandbox', '--disable-dev-shm-usage'] });
const ctx = await browser.newContext({ viewport: { width: 1400, height: 1100 } });
const page = await ctx.newPage();
page.on('pageerror', e => console.log('   PAGEERROR:', e.message));
try {
  await page.goto(`${BASE}/dev`, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1200); // let the first poll land
  ok('dev dashboard title is Dev Flywheel', (await page.title()).includes('Dev Flywheel'), await page.title());
  const fly = (await page.textContent('#m-fly')) || '';
  ok('flywheel metric shows N/N', /\d+\/\d+/.test(fly), fly);
  ok('flywheel is all-green (good class)', (await page.getAttribute('#m-fly', 'class') || '').includes('good'), fly);
  const proofs = await page.locator('#proofs .proof').count();
  ok('proofs grid populated (>=40 cells)', proofs >= 40, String(proofs));
  ok('no RED proof cells', (await page.locator('#proofs .proof.bad').count()) === 0);
  ok('connected-engines metric populated', /[A-Za-z]/.test((await page.textContent('#m-eng')) || ''));
  ok('review-pack metric populated', /\d+\/\d+/.test((await page.textContent('#m-rev')) || ''));
  ok('development timeline has passes', (await page.locator('#passes .pass').count()) >= 1);
  ok('backlog rendered', (await page.locator('#backlog .bk').count()) >= 1);
  ok('flywheel-tick sparkbars rendered', (await page.locator('#spark .bar').count()) >= 1);
  ok('context/tool registry panel populated (>=5 types)', (await page.locator('#registry .proof').count()) >= 5);
  ok('registry total shows component count', /\d{2,}\s*components/.test((await page.textContent('#reg-total')) || ''));
  ok('MCP/gateway line populated', /MCP \/ gateway/.test((await page.textContent('#mcp')) || ''));
  ok('live refresh badge active', /live/.test((await page.textContent('#refresh')) || ''));
  await page.screenshot({ path: `${ART}/dev-dashboard.png`, fullPage: false });
  console.log('   · shot dev-dashboard');
} catch (e) {
  console.log('EXCEPTION:', e.message);
  results.push({ n: 'no-exception', c: false });
} finally {
  await ctx.close();
  await browser.close();
}
const failed = results.filter(r => !r.c);
console.log(`\nSHOT: ${ART}/dev-dashboard.png`);
console.log(`RESULT: ${results.length - failed.length}/${results.length} dev-dashboard assertions passed` + (failed.length ? ` — FAILED: ${failed.map(f => f.n).join(', ')}` : ' — ALL GREEN'));
process.exit(failed.length ? 1 : 0);
