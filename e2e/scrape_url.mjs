// e2e/scrape_url.mjs <url> — JS-compatible scrape (the "scrape" tier of the OpenClaw tool repository).
// Renders a page with chromium (handles JS) and prints {title, links[]} as JSON for OpenClaw to turn into candidates.
// The UNBOUNDED/expensive tier: the descent uses it only when cheaper bounded tools (github/HN APIs) don't suffice.
import { chromium } from 'playwright';
import { existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';

function findChrome() {
  const base = join(homedir(), '.cache', 'ms-playwright');
  try {
    for (const d of readdirSync(base)) {
      if (d.startsWith('chromium-')) {
        for (const p of [join(base, d, 'chrome-linux64', 'chrome'), join(base, d, 'chrome-linux', 'chrome')]) if (existsSync(p)) return p;
      }
    }
  } catch { /* default */ }
}

const url = process.argv[2];
if (!url) { console.log(JSON.stringify({ error: 'usage: scrape_url.mjs <url>' })); process.exit(0); }
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME_BIN || findChrome(), args: ['--no-sandbox', '--disable-dev-shm-usage'] });
try {
  // a real UA + viewport so sites that serve a stub/challenge to headless defaults (e.g. PyPI search behind Fastly)
  // return the same page a human sees — this is what makes the browser tier succeed where a raw HTTP fetch is blocked.
  const page = await (await browser.newContext({
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    viewport: { width: 1280, height: 900 },
  })).newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 20000 });
  // best-effort: let JS-rendered / late content settle (capped) so we read what a user would, not the pre-hydration DOM.
  await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});
  const out = await page.evaluate(() => ({
    title: document.title,
    // body text (capped) so the LLM-driven browser can extract a target field; additive — link-only callers ignore it.
    text: ((document.body && document.body.innerText) || '').replace(/\s+/g, ' ').trim().slice(0, 12000),
    links: [...document.querySelectorAll('a[href]')].slice(0, 40)
      .map((a) => ({ text: (a.textContent || '').trim().slice(0, 80), href: a.href }))
      .filter((x) => x.text),
  }));
  console.log(JSON.stringify(out));
} catch (e) {
  console.log(JSON.stringify({ error: String(e).split('\n')[0] }));
} finally {
  await browser.close();
}
