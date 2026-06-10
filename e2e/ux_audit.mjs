/* e2e/ux_audit.mjs — a MEASURABLE UI/UX analysis framework across all front-end domains.
   For each surface it loads in a real browser and extracts COMPUTED styles + geometry to flag
   concrete, troubleshootable issues — not vibes:
     · fonts: distinct font-families in use vs the design system (Hanken Grotesk display + IBM Plex
       Mono mono); flags off-system families.
     · type scale: font sizes in use; flags text < 12px (legibility).
     · tap targets: interactive elements whose min dimension < 44px (WCAG 2.5.5 / mobile).
     · overflow: horizontal overflow (broken layout).
     · contrast proxy: very-low-opacity text.
   It also builds the UI/UX ACTION GRAPH (surface → nav targets, from [data-nav]/a[href]) and emits a
   Mermaid graph. Output: artifacts/e2e/reports/ux-audit.{json,md} with findings RANKED by severity
   so they can be fixed one by one. Honest: measures the rendered DOM only; cap + per-surface budget. */
import { join } from 'node:path';
import { launchGate, saveJSON, saveText } from './gate_common.mjs';

const SYSTEM_FONTS = ['hanken grotesk', 'ibm plex mono', 'inter', 'system-ui', '-apple-system',
  'segoe ui', 'roboto', 'monospace', 'sans-serif', 'serif', 'ui-monospace', 'arial'];
const MIN_FONT_PX = 12;
const MIN_TAP_PX = 44;

const HUBS = ['opencontexthub', 'openreviewhub', 'openroutinghub', 'openharnesshub'];
const SURFACES = [
  { id: 'parent', url: 'http://127.0.0.1:9101/' },
  { id: 'baltor', url: 'http://127.0.0.1:8001/' },
  { id: 'teleon', url: 'http://127.0.0.1:9210/teleon/' + encodeURIComponent('Teleon Prototype.html') },
  { id: 'harness-hub', url: 'http://127.0.0.1:8000/' },
  { id: 'control-tower', url: 'http://127.0.0.1:9000/' },
  ...HUBS.map((h) => ({ id: 'hub:' + h, url: `http://127.0.0.1:9210/${h}/${encodeURIComponent(h.replace(/^open/, 'Open').replace(/hub$/, 'Hub') + ' Prototype.html')}` })),
];

const { browser, context } = await launchGate();
const page = await context.newPage();
const surfaces = [];
const navGraph = {};
let totalFindings = 0;

for (const s of SURFACES) {
  const rec = { id: s.id, url: s.url, findings: [], metrics: {} };
  try {
    await page.goto(s.url, { waitUntil: 'load', timeout: 20000 });
    await page.waitForTimeout(1300);
    const data = await page.evaluate(({ MIN_FONT_PX, MIN_TAP_PX }) => {
      const out = { fonts: {}, sizes: {}, tinyText: [], smallTaps: [], navTargets: [], lowOpacity: 0, overflow: false };
      out.overflow = document.documentElement.scrollWidth > document.documentElement.clientWidth + 1;
      const visible = (el) => {
        const r = el.getBoundingClientRect();
        const st = getComputedStyle(el);
        return r.width > 0 && r.height > 0 && st.visibility !== 'hidden' && st.display !== 'none';
      };
      // fonts + type scale over text-bearing elements
      for (const el of document.querySelectorAll('body *')) {
        if (!el.childNodes.length || !visible(el)) continue;
        const hasText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
        if (!hasText) continue;
        const st = getComputedStyle(el);
        const fam = (st.fontFamily || '').split(',')[0].replace(/["']/g, '').trim().toLowerCase();
        if (fam) out.fonts[fam] = (out.fonts[fam] || 0) + 1;
        const px = Math.round(parseFloat(st.fontSize));
        if (px) out.sizes[px] = (out.sizes[px] || 0) + 1;
        if (px && px < MIN_FONT_PX) out.tinyText.push({ px, text: el.textContent.trim().slice(0, 30) });
        if (parseFloat(st.opacity) > 0 && parseFloat(st.opacity) < 0.45) out.lowOpacity += 1;
      }
      // tap targets + nav graph over interactive elements
      for (const el of document.querySelectorAll('button, a[href], [role="button"], .oh-btn, [data-nav]')) {
        if (!visible(el)) continue;
        const r = el.getBoundingClientRect();
        const min = Math.min(r.width, r.height);
        const label = (el.innerText || el.getAttribute('aria-label') || '').trim().slice(0, 30);
        if (min > 0 && min < MIN_TAP_PX) out.smallTaps.push({ min: Math.round(min), label });
        const nav = el.getAttribute('data-nav') || el.getAttribute('href') || '';
        if (nav && !/^https?:\/\//.test(nav)) out.navTargets.push(nav.slice(0, 30));
      }
      return out;
    }, { MIN_FONT_PX, MIN_TAP_PX });

    const offSystem = Object.keys(data.fonts).filter((f) => !SYSTEM_FONTS.some((sf) => f.includes(sf)));
    rec.metrics = {
      fonts: data.fonts, sizes: data.sizes,
      distinct_fonts: Object.keys(data.fonts).length,
      tiny_text: data.tinyText.length, small_taps: data.smallTaps.length,
      low_opacity: data.lowOpacity, overflow: data.overflow,
    };
    navGraph[s.id] = [...new Set(data.navTargets)];
    // rank findings
    if (data.overflow) rec.findings.push({ sev: 'high', kind: 'overflow', detail: 'horizontal overflow' });
    if (offSystem.length) rec.findings.push({ sev: 'medium', kind: 'off-system-font', detail: `off-design-system fonts: ${offSystem.join(', ')}` });
    if (Object.keys(data.fonts).length > 3) rec.findings.push({ sev: 'low', kind: 'font-sprawl', detail: `${Object.keys(data.fonts).length} distinct font families (expect ≤3)` });
    if (data.tinyText.length) rec.findings.push({ sev: 'medium', kind: 'tiny-text', detail: `${data.tinyText.length} text elements < ${MIN_FONT_PX}px (e.g. "${data.tinyText[0]?.text}" ${data.tinyText[0]?.px}px)` });
    if (data.smallTaps.length) rec.findings.push({ sev: 'low', kind: 'small-tap-target', detail: `${data.smallTaps.length} interactive elements < ${MIN_TAP_PX}px (e.g. "${data.smallTaps[0]?.label}" ${data.smallTaps[0]?.min}px)` });
  } catch (e) {
    rec.findings.push({ sev: 'high', kind: 'load-failed', detail: String(e).slice(0, 100) });
  }
  totalFindings += rec.findings.length;
  surfaces.push(rec);
  console.log(`  ${rec.id}: ${rec.findings.length} findings · ${rec.metrics.distinct_fonts ?? '?'} fonts · taps<44:${rec.metrics.small_taps ?? '?'} · tiny:${rec.metrics.tiny_text ?? '?'} · overflow:${rec.metrics.overflow ?? '?'}`);
}

await page.close(); await context.close(); await browser.close();

const mermaid = ['graph LR', ...Object.entries(navGraph).flatMap(([from, tos]) =>
  tos.slice(0, 8).map((t) => `  ${from.replace(/[^a-zA-Z0-9]/g, '_')} --> ${('r' + t).replace(/[^a-zA-Z0-9]/g, '_')}`))].join('\n');
const bySev = { high: 0, medium: 0, low: 0 };
for (const s of surfaces) for (const f of s.findings) bySev[f.sev] = (bySev[f.sev] || 0) + 1;

const report = { generated_at: new Date().toISOString(), gate: 'ux_audit',
  design_system: { display: 'Hanken Grotesk', mono: 'IBM Plex Mono', min_font_px: MIN_FONT_PX, min_tap_px: MIN_TAP_PX },
  totals: { surfaces: surfaces.length, findings: totalFindings, by_severity: bySev },
  surfaces, nav_graph: navGraph };
saveJSON('reports', 'ux-audit.json', report);
saveText('reports', 'ux-audit.md', [
  `# UI/UX audit — ${report.generated_at}`, '',
  `Design system: **Hanken Grotesk** (display) + **IBM Plex Mono** (mono) · min text ${MIN_FONT_PX}px · min tap ${MIN_TAP_PX}px.`,
  `**${surfaces.length} surfaces · ${totalFindings} findings** (high ${bySev.high}, medium ${bySev.medium}, low ${bySev.low})`, '',
  '## Findings to troubleshoot (ranked)',
  ...['high', 'medium', 'low'].flatMap((sev) =>
    surfaces.flatMap((s) => s.findings.filter((f) => f.sev === sev).map((f) => `- **[${sev}] ${s.id}** · ${f.kind}: ${f.detail}`))),
  '', '## Per-surface metrics',
  '| surface | fonts | taps<44 | tiny text | overflow |', '|---|---|---|---|---|',
  ...surfaces.map((s) => `| ${s.id} | ${s.metrics.distinct_fonts ?? '?'} | ${s.metrics.small_taps ?? '?'} | ${s.metrics.tiny_text ?? '?'} | ${s.metrics.overflow ? 'YES' : 'no'} |`),
  '', '## UI/UX action graph (surface → nav targets)', '```mermaid', mermaid, '```',
].join('\n'));
console.log(`\nUX audit: ${totalFindings} findings across ${surfaces.length} surfaces (H${bySev.high}/M${bySev.medium}/L${bySev.low}) → reports/ux-audit.md`);
process.exit(0);
