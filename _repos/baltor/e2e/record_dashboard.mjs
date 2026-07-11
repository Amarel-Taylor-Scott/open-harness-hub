// Drive the LIVE Baltor ops dashboard in real Chrome: open /dashboard (served by the admin server),
// click ▶ Run Full Pipeline, watch real events stream over SSE + the stage board light up, capture it.
//   prereq: PYTHONPATH=. python3 scripts/baltor_admin_demo_server.py --port 9307
//   run:    BASE=http://127.0.0.1:9307 TOKEN=$(cat ../dist/baltor-admin-token.txt) node record_dashboard.mjs
import { chromium } from 'playwright';
import fs from 'node:fs';

const BASE = process.env.BASE || 'http://127.0.0.1:9307';
// the admin server token-gates the mutating "Run Full Pipeline" POST; the dashboard forwards a
// ?token=… URL param to its POSTs (dashboard.html tok()), so open the page WITH the token.
const TOKEN = process.env.TOKEN || '';
const q = (u) => TOKEN ? `${u}${u.includes('?') ? '&' : '?'}token=${encodeURIComponent(TOKEN)}` : u;
const ART = new URL('./artifacts', import.meta.url).pathname;
fs.mkdirSync(ART, { recursive: true });
const results = [];
const ok = (n, c, d = '') => { results.push({ n, c: !!c }); console.log(`  [${c ? 'ok' : 'FAIL'}] ${n}${c ? '' : ' :: ' + d}`); };
const shot = async (p, n) => { await p.screenshot({ path: `${ART}/${n}.png`, fullPage: false }); console.log('   · shot', n); };

const browser = await chromium.launch({ channel: 'chrome', args: ['--no-sandbox', '--disable-dev-shm-usage'] });
const ctx = await browser.newContext({ viewport: { width: 1400, height: 1000 } });
const page = await ctx.newPage();
page.on('pageerror', e => console.log('   PAGEERROR:', e.message));
try {
  await page.goto(q(`${BASE}/dashboard`), { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(800); // let SSE connect
  ok('dashboard title is Baltor Live Ops', (await page.title()).includes('Live Ops'), await page.title());
  ok('six-stage board rendered (7 cards incl. rail)', (await page.locator('.stage').count()) === 7);
  const conn = (await page.textContent('#conn')) || '';
  ok('SSE/poll connection established', /live|polling/i.test(conn), conn);
  // start from a clean slate so the recording tells the empty → fires → populated story
  await page.click('#clear');
  await page.waitForTimeout(500);
  ok('cleared dashboard starts empty', (await page.locator('#events .ev').count()) === 0);
  await shot(page, 'dash-01-loaded');

  // click Run Full Pipeline → real engines fire onto the bus → SSE streams them in
  await page.click('#run');
  await page.waitForTimeout(900);  // catch a mid-fill frame for the recording
  await shot(page, 'dash-02-running');
  await page.waitForTimeout(2800);
  const evCount = await page.locator('#events .ev').count();
  ok('live events streamed into the dashboard', evCount >= 10, String(evCount));
  // at least one stage card lit up (hot or a non-zero count)
  const counts = await page.$$eval('.stage .c', els => els.map(e => parseInt(e.textContent || '0', 10)));
  ok('stage board counters advanced (stages fired)', counts.some(n => n > 0), JSON.stringify(counts));
  // the note shows the pipeline result (answer + events)
  const note = (await page.textContent('#note')) || '';
  ok('run note reports pipeline OK + answer', /answer=5/.test(note), note);
  // enriched panels: measured-lift readout + answer metric + recent-artifacts
  const lift = (await page.textContent('#m-lift')) || '';
  ok('measured-lift readout populated', /[0-9]/.test(lift), lift);
  ok('answer metric shows 5', ((await page.textContent('#m-answer')) || '').trim() === '5');
  // regression guard (C12): verified_context_flow's no-token pack event must NOT clobber the
  // compress token-reduction metric — m-pack must show a real "before→after", never "undefined".
  const pack = ((await page.textContent('#m-pack')) || '').trim();
  ok('pack-tokens metric shows a real reduction (not undefined)', /^\d+→\d+$/.test(pack), pack);
  ok('recent-artifacts panel populated', (await page.locator('#artifacts .art').count()) >= 1);
  await shot(page, 'dash-03-after');

  // event kinds visible in the stream (sample the rendered kind labels)
  const kinds = await page.$$eval('#events .kind', els => els.map(e => e.textContent));
  for (const need of ['pipeline.started', 'contradiction_found', 'swarm.agent.completed', 'context_lift.calculated', 'pipeline.completed']) {
    ok(`stream shows ${need}`, kinds.includes(need));
  }
} catch (e) {
  console.log('EXCEPTION:', e.message);
  results.push({ n: 'no-exception', c: false });
} finally {
  await ctx.close();
  await browser.close();
}
// Stitch the ops gif from the SAME frames we just captured, so live-dashboard.gif is never staler
// than the dash-*.png it's made of. make_gif.mjs stays the single source of GIF logic (we just feed
// it OUT/FRAMES) — no duplicated frame list, no manual one-off invocation that drifts.
const failed0 = results.filter(r => !r.c);
if (!failed0.length) {
  const { spawnSync } = await import('node:child_process');
  const gif = spawnSync(process.execPath, ['make_gif.mjs'], {
    cwd: new URL('.', import.meta.url).pathname,
    env: { ...process.env, OUT: 'live-dashboard.gif', FRAMES: 'dash-01-loaded,dash-02-running,dash-03-after' },
    encoding: 'utf8',
  });
  process.stdout.write(gif.stdout || '');
  ok('live-dashboard.gif stitched from the fresh ops frames', gif.status === 0 && fs.existsSync(`${ART}/live-dashboard.gif`), `make_gif exit ${gif.status}`);
}
const failed = results.filter(r => !r.c);
console.log(`\nSHOTS: ${ART}/dash-*.png`);
console.log(`RESULT: ${results.length - failed.length}/${results.length} live-dashboard assertions passed` + (failed.length ? ` — FAILED: ${failed.map(f => f.n).join(', ')}` : ' — ALL GREEN'));
process.exit(failed.length ? 1 : 0);
