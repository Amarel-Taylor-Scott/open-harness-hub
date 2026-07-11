// Drive the LIVE Baltor /raw feed in real Chrome: post a fresh Pipeline Runtime run, then open
// /raw, switch to the "latest run lineage" view, and capture the run's step_runs + content-addressed
// artifacts + OTel span tree rendering live from the durable ledger (the projection, not its own truth).
//   prereq: BALTOR_DURABLE_DB=… OH_SHOWCASE_TOKEN=… PYTHONPATH=. python3 scripts/baltor_admin_demo_server.py --port 9307
//   run:    BASE=http://127.0.0.1:9307 TOKEN=$(cat dist/baltor-admin-token.txt) node record_raw.mjs
import { chromium } from 'playwright';
import fs from 'node:fs';

const BASE = process.env.BASE || 'http://127.0.0.1:9307';
const TOKEN = process.env.TOKEN || '';
const ART = new URL('./artifacts', import.meta.url).pathname;
fs.mkdirSync(ART, { recursive: true });
const q = (u) => TOKEN ? `${u}${u.includes('?') ? '&' : '?'}token=${encodeURIComponent(TOKEN)}` : u;
const results = [];
const ok = (n, c, d = '') => { results.push({ n, c: !!c }); console.log(`  [${c ? 'ok' : 'FAIL'}] ${n}${c ? '' : ' :: ' + d}`); };
const shot = async (p, n) => { await p.screenshot({ path: `${ART}/${n}.png`, fullPage: false }); console.log('   · shot', n); };

// 1) post a FRESH (non-duplicate) 4-step run so the lineage view shows a rich, newest run.
//    nonce varies the input hash → new idempotency key → a distinct run that sorts newest.
const nonce = `rec-${Date.now()}`;
let postedRunId = '';
try {
  const r = await fetch(q(`${BASE}/api/dev/pipelines/run`), {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ pipeline_id: 'cfpb_structured_ingest', pipeline_version: 'v1',
      tenant_id: 'acme', input: { fixture: true, limit: 5, source_id: 'cfpb', nonce } }),
  });
  const d = await r.json();
  postedRunId = d.run_id || '';
  ok('posted a fresh runtime run (done, not duplicate)', d.status === 'done' && d.duplicate === false, JSON.stringify(d));
} catch (e) { ok('posted a fresh runtime run', false, String(e)); }

const browser = await chromium.launch({ channel: 'chrome', args: ['--no-sandbox', '--disable-dev-shm-usage'] });
const ctx = await browser.newContext({ viewport: { width: 1400, height: 1000 } });
const page = await ctx.newPage();
page.on('pageerror', e => console.log('   PAGEERROR:', e.message));
try {
  await page.goto(q(`${BASE}/raw`), { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(600);
  ok('raw feed title is "Raw Feed"', (await page.title()).includes('Raw Feed'), await page.title());
  ok('lineage view option exists in #src', (await page.locator('#src option[value="lineage"]').count()) === 1);

  // switch to the "latest run lineage" view and force an immediate tick
  await page.selectOption('#src', 'lineage');
  await page.evaluate(() => window.tick && window.tick());
  await page.waitForFunction(() => (document.querySelector('#out')?.textContent || '').includes('span_count'), null, { timeout: 8000 });
  const out = (await page.textContent('#out')) || '';
  ok('lineage view rendered the run (run_id present)', /run-[0-9a-f]+/.test(out), out.slice(0, 120));
  ok('lineage shows step_runs', /"steps"/.test(out));
  ok('lineage shows content-addressed artifacts', /"content_hash"/.test(out) && /"artifacts"/.test(out));
  ok('lineage shows a non-empty OTel span tree (span_count ≥ 3)', /"span_count":\s*([3-9]|\d{2,})/.test(out), out.match(/"span_count":\s*\d+/)?.[0] || '');
  ok('lineage span tree carries one trace_id', /"trace_id"/.test(out));
  if (postedRunId) ok('the freshly-posted run is the one shown (newest)', out.includes(postedRunId), `${postedRunId} not in view`);
  await shot(page, 'raw-lineage');

  // also capture the "pipeline runs" list view
  await page.selectOption('#src', 'pipelines');
  await page.evaluate(() => window.tick && window.tick());
  await page.waitForFunction(() => (document.querySelector('#out')?.textContent || '').includes('"runs"'), null, { timeout: 6000 });
  ok('pipeline runs view lists runs', /"runs"/.test((await page.textContent('#out')) || ''));
  await shot(page, 'raw-runs');
} catch (e) {
  ok('raw recorder completed without throwing', false, String(e));
} finally {
  await browser.close();
}

const failed = results.filter(r => !r.c);
fs.writeFileSync(`${ART}/raw-record-result.json`, JSON.stringify({ base: BASE, posted_run_id: postedRunId, results, pass: failed.length === 0 }, null, 2));
console.log(`\n${failed.length ? `${failed.length} FAILED: ${failed.map(f => f.n).join(', ')}` : 'PASS — /raw lineage view renders a real run’s steps + content-addressed artifacts + OTel span tree (projection over the durable ledger).'}`);
process.exit(failed.length ? 1 : 0);
