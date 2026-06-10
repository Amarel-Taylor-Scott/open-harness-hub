// Drive the live Baltor demo console in real Chrome, ASSERT real DOM outcomes, and record a
// Playwright trace + screenshot filmstrip. No ffmpeg needed (trace is a frame-by-frame replay).
//
//   1) cd web/baltor && python3 -m http.server 8000   (serve the demo)
//   2) cd e2e && npm install && node record_demo.mjs   (drive + assert + capture)
//   3) node make_gif.mjs                               (optional: filmstrip → artifacts/baltor-demo.gif)
//   4) npx playwright show-trace artifacts/trace.zip   (interactive replay)
import { chromium } from 'playwright';
import fs from 'node:fs';

const BASE = process.env.BASE || 'http://localhost:8000';
const ART = process.env.ART || new URL('./artifacts', import.meta.url).pathname;
fs.mkdirSync(ART, { recursive: true });

const results = [];
function assert(name, cond, detail = '') {
  results.push({ name, ok: !!cond, detail });
  console.log(`  [${cond ? 'ok' : 'FAIL'}] ${name}${cond ? '' : ' :: ' + detail}`);
}
const shot = async (page, n) => { await page.screenshot({ path: `${ART}/${n}.png` }); console.log('   · shot', n); };

const browser = await chromium.launch({ channel: 'chrome', args: ['--no-sandbox', '--disable-dev-shm-usage'] });
const context = await browser.newContext({ viewport: { width: 1400, height: 1000 } });
await context.tracing.start({ screenshots: true, snapshots: true, title: 'Baltor full-app demo' });
const page = await context.newPage();
page.on('pageerror', e => console.log('   PAGEERROR:', e.message));

try {
  // 1. demo console loads (Acme by default)
  await page.goto(`${BASE}/demo-console.html`, { waitUntil: 'networkidle' });
  assert('page title is Baltor', (await page.title()).includes('Baltor'), await page.title());
  const headline = await page.textContent('#headline');
  assert('Acme headline rendered with answer 5', /Acme Billing/.test(headline) && /Answer = 5/.test(headline), headline);
  assert('context graph drew 8 nodes', (await page.locator('#graph .gnode').count()) === 8);
  assert('lift matrix drew 5 condition bars', (await page.locator('#lift .liftbar').count()) === 5);
  await shot(page, '01-acme-loaded');

  // 2. run the animation
  await page.click('#run');
  await page.waitForTimeout(7000);
  assert('all 7 stages animated to "on"', (await page.locator('.stage.on').count()) === 7);
  assert('progress bar reached 100%', (await page.evaluate(() => document.querySelector('#bar').style.width)) === '100%');
  await shot(page, '02-acme-ran');

  // 3. click the stale runbook node → detail + version timeline (force: the node pulses, never "stable")
  await page.click('#graph .gnode[data-id="obj-runbook"]', { force: true });
  await page.waitForTimeout(300);
  await page.locator('#panel').scrollIntoViewIfNeeded();
  await page.waitForTimeout(200);
  const panel = await page.textContent('#panel');
  assert('node click opened object detail (runbook)', /runbook/i.test(panel));
  assert('panel shows the version timeline (v2 proposed)', /v2-proposed/.test(panel) && /pending review/i.test(panel));
  await shot(page, '03-node-detail');

  // 4. gated source expansion: allowed → granted excerpt; restricted → denied (no raw)
  await page.click('#bExp'); await page.waitForTimeout(300);
  assert('Expand source returned a granted real excerpt', /granted/i.test(await page.textContent('#expOut')));
  await shot(page, '04-expand-source');
  await page.click('#bDeny'); await page.waitForTimeout(300);
  assert('Try restricted is DENIED with a reason', /DENIED|classification_restricted/i.test(await page.textContent('#expOut')));
  await shot(page, '05-restricted-denied');

  // 5. switch corpus to CFPB → real offline run, answer 10
  await page.selectOption('#corpus', 'cfpb'); await page.waitForTimeout(800);
  const cfHead = await page.textContent('#headline');
  assert('CFPB headline rendered with answer 10', /CFPB/.test(cfHead) && /Answer = 10/.test(cfHead), cfHead);
  await page.click('#run'); await page.waitForTimeout(7000);
  assert('CFPB run animated all 7 stages', (await page.locator('.stage.on').count()) === 7);
  await shot(page, '06-cfpb-ran');

  // 6. human review queue
  await page.goto(`${BASE}/reviews.html`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(500);
  assert('review queue shows open reviews', /open review/.test(await page.textContent('#count')));
  assert('review queue has >= 2 cards (one per corpus)', (await page.locator('.card').count()) >= 2);
  await shot(page, '07-reviews');
  await page.click('.btns button.approve'); await page.waitForTimeout(300);
  const decided = await page.textContent('#decided-0');
  assert('approving records a demo-local decision', /recorded/i.test(decided) && /steward-review-decision/.test(decided));
  await shot(page, '08-review-approved');
} catch (e) {
  console.log('EXCEPTION:', e.message);
  results.push({ name: 'no-exception', ok: false, detail: e.message });
} finally {
  await context.tracing.stop({ path: ART + '/trace.zip' });
  await context.close();
  await browser.close();
}

const failed = results.filter(r => !r.ok);
console.log(`\nTRACE: ${ART}/trace.zip  (view: npx playwright show-trace ${ART}/trace.zip)`);
console.log(`SHOTS: ${ART}/*.png`);
console.log(`RESULT: ${results.length - failed.length}/${results.length} browser assertions passed` + (failed.length ? ` — FAILED: ${failed.map(f => f.name).join(', ')}` : ' — ALL GREEN'));
process.exit(failed.length ? 1 : 0);
