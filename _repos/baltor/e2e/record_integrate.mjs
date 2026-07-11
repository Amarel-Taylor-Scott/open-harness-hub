// Drive the "Integrate CFPB data" single-page flow: click the button, watch all 7 stages reveal,
// assert the served answer (10) + contradiction + measured lift, capture a screenshot.
//   run: BASE=http://127.0.0.1:9307 TOKEN=<token> node record_integrate.mjs
import { chromium } from 'playwright';
import fs from 'node:fs';
const BASE = process.env.BASE || 'http://127.0.0.1:9307';
const TOKEN = process.env.TOKEN || '';
const ART = new URL('./artifacts', import.meta.url).pathname;
fs.mkdirSync(ART, { recursive: true });
const results = [];
const ok = (n, c, d = '') => { results.push({ n, c: !!c }); console.log(`  [${c ? 'ok' : 'FAIL'}] ${n}${c ? '' : ' :: ' + d}`); };
const browser = await chromium.launch({ channel: 'chrome', args: ['--no-sandbox', '--disable-dev-shm-usage'] });
const ctx = await browser.newContext({ viewport: { width: 1100, height: 1300 } });
const page = await ctx.newPage();
page.on('pageerror', e => console.log('   PAGEERROR:', e.message));
try {
  const url = `${BASE}/integrate${TOKEN ? '?token=' + TOKEN : ''}`;
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  ok('integrate page title', (await page.title()).includes('Integrate CFPB'), await page.title());
  await page.click('#run');
  // wait for the staged reveal + result to finish
  await page.waitForSelector('#result.show', { timeout: 15000 });
  ok('all 7 stage cards rendered', (await page.locator('.stage').count()) === 7, String(await page.locator('.stage').count()));
  ok('all stages marked done', (await page.locator('.stage.done').count()) === 7);
  ok('served answer is 10', ((await page.textContent('#answer')) || '').trim() === '10');
  ok('contradiction shows FAQ 30 superseded', /30 days/.test((await page.textContent('#contra')) || ''));
  ok('measured lift shown (+ value)', /\+[0-9.]+/.test((await page.textContent('#lift')) || ''));
  ok('source banner populated', /Reg E/.test((await page.textContent('#src')) || ''));
  await page.screenshot({ path: `${ART}/integrate-cfpb.png`, fullPage: true });
  console.log('   · shot integrate-cfpb');
} catch (e) { console.log('EXCEPTION:', e.message); results.push({ n: 'no-exception', c: false }); }
finally { await ctx.close(); await browser.close(); }
const failed = results.filter(r => !r.c);
console.log(`\nSHOT: ${ART}/integrate-cfpb.png`);
console.log(`RESULT: ${results.length - failed.length}/${results.length} integrate assertions passed` + (failed.length ? ` — FAILED: ${failed.map(f => f.n).join(', ')}` : ' — ALL GREEN'));
process.exit(failed.length ? 1 : 0);
