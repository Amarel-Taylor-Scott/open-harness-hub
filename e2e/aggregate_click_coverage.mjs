/* e2e/aggregate_click_coverage.mjs — merge the per-chunk click-coverage-*.json into one report. */
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { REPO_ROOT } from './gate_common.mjs';

const dir = join(REPO_ROOT, 'artifacts', 'e2e', 'reports');
const chunks = readdirSync(dir).filter((f) => /^click-coverage-\d+-\d+\.json$/.test(f));
const surfaces = [];
const t = { surfaces: 0, found: 0, tested: 0, held: 0, capped: 0, errors: 0, secret_leaks: 0 };
for (const f of chunks) {
  const r = JSON.parse(readFileSync(join(dir, f), 'utf-8'));
  surfaces.push(...r.surfaces);
  for (const k of Object.keys(t)) t[k] += (k === 'surfaces' ? r.surfaces.length : (r.totals[k] || 0));
}
const out = { generated_at: new Date().toISOString(), gate: 'click_everything_aggregate', chunks: chunks.length, totals: t, surfaces };
writeFileSync(join(dir, 'click-coverage.json'), JSON.stringify(out, null, 2));
writeFileSync(join(dir, 'click-coverage.md'), [
  `# Every-element click coverage (aggregated ${chunks.length} chunks) — ${out.generated_at}`, '',
  `**${t.surfaces} surfaces · ${t.found} interactive elements found · ${t.tested} clicked · ${t.held} held · ` +
  `${t.capped} over-cap (untested, listed) · ${t.secret_leaks} secret leaks · ${t.errors} error notes**`, '',
  '| surface | found | tested | held | external | navs | errors |', '|---|---|---|---|---|---|---|',
  ...surfaces.map((s) => `| ${s.id} | ${s.found} | ${s.tested} | ${s.held} | ${s.external} | ${s.navigations} | ${s.errors.length} |`),
  '', '## Error/leak notes', ...(surfaces.flatMap((s) => s.errors.map((e) => `- **${s.id}**: ${e}`)) || ['none']),
].join('\n'));
console.log(`aggregated ${chunks.length} chunks → ${t.tested}/${t.found} clicked across ${t.surfaces} surfaces, ${t.held} held, ${t.secret_leaks} leaks, ${t.errors} error notes`);
