/* e2e/click_everything.mjs — the EXHAUSTIVE every-VISIBLE-element pass (gate "every-button testing").
   For each surface, repeatedly find the next VISIBLE, not-yet-clicked interactive element and
   activate it as a real user would — exploring elements newly revealed by prior clicks — recording
   the result (ok · navigated · external · HELD · click-failed · page-error · SECRET-LEAK), with a
   per-click console/crash/secret check. Visibility filtering is the key fix: the SPA keeps hidden
   route sections in the DOM, so unfiltered selectors matched buttons no user can see → timeouts.
   CHUNKWISE: `node click_everything.mjs START END` runs surfaces [START,END) → per-chunk report;
   run many chunks in the background (hours OK) and aggregate. Honest: per-surface cap + time budget
   are LOGGED when hit (no silent truncation). Exit 1 only on a real secret leak. */
import { join } from 'node:path';
import { REPO_ROOT, launchGate, saveJSON, saveText } from './gate_common.mjs';

const CAP = 150;                       // max distinct visible elements explored per surface (logged if hit)
const SURFACE_BUDGET_MS = 240000;      // hard per-surface time budget (logged if hit)
const SEL = 'button, a[href], [role="button"], input[type="submit"], .oh-btn, .oh-tabs button, ' +
  '.oh-segment button, summary, select, [data-nav]';
const SECRET_RE = /sk-[A-Za-z0-9]{16,}|\bak_[a-z]+_[0-9a-f]{16,}|svt_[a-z]+_[a-z]+_[0-9a-f]{16,}|credref:|keyref:/;

const harnessRoutes = ['/', '/build', '/catalog', '/compare', '/govern', '/pricing', '/docs',
  '/signin', '/signup', '/account/keys', '/ops', '/requests', '/deep', '/flow', '/run', '/sdg',
  '/byo', '/value', '/why', '/landings', '/admin'];
const baltorRoutes = ['/', '/#/engine', '/#/overview', '/#/pricing', '/#/trust', '/#/dashboard'];
// all 22 hubs (folder → display name) served by the design bundle preview on 9210
const HUBS = {
  opencontexthub: 'OpenContextHub', openskillshub: 'OpenSkillsHub', opentoolshub: 'OpenToolsHub',
  openskilltotool: 'OpenSkillToTool', openmcphub: 'OpenMCPHub', opencompressionhub: 'OpenCompressionHub',
  openbenchmarkhub: 'OpenBenchmarkHub', openreviewhub: 'OpenReviewHub', openharnesshub: 'OpenHarnessHub',
  opentemplateshub: 'OpenTemplatesHub', openendpointhub: 'OpenEndpointHub', openenvhub: 'OpenEnvHub',
  opensandboxhub: 'OpenSandboxHub', openagenthub: 'OpenAgentHub', openreceipthub: 'OpenReceiptHub',
  openstatehub: 'OpenStateHub', openroutinghub: 'OpenRoutingHub',
  openreconciliationhub: 'OpenReconciliationHub', openhardeninghub: 'OpenHardeningHub',
  openenrichmenthub: 'OpenEnrichmentHub', openoptimizationhub: 'OpenOptimizationHub',
  openverificationhub: 'OpenVerificationHub',
};
const ALL_SURFACES = [
  ...harnessRoutes.map((r) => ({ id: 'openhubforai' + r, url: 'http://127.0.0.1:8000/#' + r })),
  ...baltorRoutes.map((r) => ({ id: 'baltor' + (r === '/' ? '' : r), url: 'http://127.0.0.1:8001' + r })),
  { id: 'parent-site', url: 'http://127.0.0.1:9101/' },
  { id: 'control-tower', url: 'http://127.0.0.1:9000/' },
  ...Object.entries(HUBS).map(([f, name]) => ({ id: 'hub:' + f, url: `http://127.0.0.1:9210/${f}/${encodeURIComponent(name + '.html')}` })),
];
const START = Number(process.argv[2] ?? 0);
const END = Number(process.argv[3] ?? ALL_SURFACES.length);
const TAG = (process.argv[2] != null) ? `-${START}-${END}` : '';
const SURFACES = ALL_SURFACES.slice(START, END);

async function elInfo(el) {
  return el.evaluate((n) => ({
    tag: n.tagName.toLowerCase(),
    text: (n.innerText || n.value || n.getAttribute('aria-label') || '').trim().slice(0, 60),
    role: n.getAttribute('role') || '', href: n.getAttribute('href') || '', nav: n.getAttribute('data-nav') || '',
    held: n.hasAttribute('data-held') || n.disabled || /\bdisabled\b/.test(n.className),
    heldReason: n.getAttribute('data-held-reason') || (n.disabled ? (n.getAttribute('title') || 'disabled') : ''),
    external: n.getAttribute('target') === '_blank' ||
      (/^https?:\/\//.test(n.getAttribute('href') || '') && !(n.getAttribute('href') || '').includes('127.0.0.1')),
  }));
}

const { browser, context } = await launchGate();
const page = await context.newPage();
const surfaces = [];
const T = { surfaces: 0, found: 0, tested: 0, held: 0, external: 0, navs: 0, capped: 0, errors: 0, secret_leaks: 0 };

for (const surface of SURFACES) {
  const rec = { id: surface.id, url: surface.url, found: 0, tested: 0, held: 0, external: 0,
    navigations: 0, capped: 0, timedout: false, errors: [], leaks: 0, elements: [] };
  let pageErrors = 0;
  const onErr = () => { pageErrors += 1; };
  page.on('pageerror', onErr);
  const t0 = Date.now();
  try {
    const resp = await page.goto(surface.url, { waitUntil: 'load', timeout: 20000 });
    await page.waitForTimeout(1100);
    const base = page.url();
    if (resp && resp.status() >= 400) { rec.errors.push('surface load ' + resp.status()); }
    else {
      const clicked = new Set();
      for (let step = 0; step < CAP; step++) {
        if (Date.now() - t0 > SURFACE_BUDGET_MS) { rec.timedout = true; rec.errors.push(`hit ${SURFACE_BUDGET_MS / 1000}s budget — ${clicked.size} explored`); break; }
        const handles = await page.$$(SEL);
        let chosen = null, info = null, visibleSeen = 0;
        for (const h of handles) {
          let vis = false; try { vis = await h.isVisible(); } catch { vis = false; }
          if (!vis) continue;
          visibleSeen += 1;
          let d; try { d = await elInfo(h); } catch { continue; }
          const sig = `${d.tag}|${d.text}|${d.nav}|${d.href}|${d.role}`;
          if (clicked.has(sig)) continue;
          if (!chosen) { chosen = h; info = d; info.sig = sig; }
        }
        if (step === 0) rec.found = visibleSeen;
        if (!chosen) break;                 // every visible element explored
        clicked.add(info.sig);
        const entry = { tag: info.tag, text: info.text, role: info.role, result: '' };
        if (info.held) { rec.held += 1; entry.result = 'HELD'; entry.reason = info.heldReason; rec.elements.push(entry); continue; }
        if (info.external) { rec.external += 1; entry.result = 'external'; rec.elements.push(entry); continue; }
        const errBefore = pageErrors;
        try { await chosen.scrollIntoViewIfNeeded({ timeout: 1500 }).catch(() => {}); await chosen.click({ timeout: 2500 }); }
        catch (e) { entry.result = 'click-failed'; entry.detail = String(e).split('\n')[0].slice(0, 70); rec.errors.push(`click-failed: ${entry.text || entry.tag}`); rec.elements.push(entry); continue; }
        rec.tested += 1;
        await page.waitForTimeout(160);
        const after = page.url();
        const leak = await page.evaluate((re) => new RegExp(re).test(document.body.innerText), SECRET_RE.source).catch(() => false);
        if (leak) { rec.leaks += 1; entry.result = 'SECRET-LEAK'; rec.errors.push('LEAK after ' + entry.text); }
        else if (pageErrors > errBefore) { entry.result = 'page-error'; rec.errors.push('page-error after ' + entry.text); }
        else if (after !== base) { entry.result = after.includes('#') ? 'nav:' + after.split('#')[1] : 'navigated'; rec.navigations += 1; }
        else { entry.result = 'ok'; }
        rec.elements.push(entry);
        if (after !== base) { await page.goto(base, { waitUntil: 'domcontentloaded' }).catch(() => {}); await page.waitForTimeout(250); }
      }
      if (rec.found >= CAP) { rec.capped = 1; }
    }
  } catch (e) { rec.errors.push('surface failed: ' + String(e).slice(0, 100)); }
  page.off('pageerror', onErr);
  if (pageErrors) rec.errors.push(`${pageErrors} page error(s) total`);
  T.surfaces += 1; T.found += rec.found; T.tested += rec.tested; T.held += rec.held;
  T.external += rec.external; T.navs += rec.navigations; T.capped += rec.capped;
  T.errors += rec.errors.length; T.secret_leaks += rec.leaks;
  surfaces.push(rec);
  console.log(`  [${rec.leaks ? 'LEAK' : rec.errors.length ? 'notes' : 'ok'}] ${rec.id} — visible ${rec.found}, clicked ${rec.tested}, held ${rec.held}, ext ${rec.external}, navs ${rec.navigations}${rec.timedout ? ', TIMEBUDGET' : ''}${rec.errors.length ? `, ${rec.errors.length} notes` : ''} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
}

await page.close(); await context.close(); await browser.close();
const report = { generated_at: new Date().toISOString(), gate: 'click_everything', chunk: TAG || 'all', totals: T, surfaces };
saveJSON('reports', `click-coverage${TAG}.json`, report);
saveText('reports', `click-coverage${TAG}.md`, [
  `# Every-visible-element click coverage ${TAG || '(all)'} — ${report.generated_at}`, '',
  `**${T.surfaces} surfaces · ${T.found} visible interactive elements · ${T.tested} clicked · ${T.held} held · ` +
  `${T.external} external · ${T.navs} navigations · ${T.secret_leaks} secret leaks · ${T.errors} error notes**`, '',
  '| surface | visible | clicked | held | ext | navs | notes |', '|---|---|---|---|---|---|---|',
  ...surfaces.map((s) => `| ${s.id} | ${s.found} | ${s.tested} | ${s.held} | ${s.external} | ${s.navigations} | ${s.errors.length} |`),
  '', '## Error/leak notes', ...(surfaces.flatMap((s) => s.errors.map((e) => `- **${s.id}**: ${e}`))),
].join('\n'));
console.log(`\nchunk${TAG}: ${T.tested}/${T.found} clicked across ${T.surfaces} surfaces, ${T.held} held, ${T.secret_leaks} leaks, ${T.errors} notes → reports/click-coverage${TAG}.md`);
process.exit(T.secret_leaks > 0 ? 1 : 0);
