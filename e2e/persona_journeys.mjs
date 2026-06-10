/* e2e/persona_journeys.mjs — persona-driven E2E: run every customer journey from
   architecture/e2e_persona_journey_registry.json over the RUNNING local surfaces, record one VIDEO
   per persona, and turn every failed step / missing affordance / detected leak into a FRICTION
   finding with its own screenshot. Frictions are the deliverable, not failures: the runner exits 0
   when it completes, and the report ranks what blocked each persona.
   Law: no fake URLs; inverted probes treat MATCHES as leaks; raw secrets never typed or captured. */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import {
  REPO_ROOT, launchGate, attachCollectors, saveJSON, saveText, DIRS,
  HAS_NATIVE_VIDEO, finalizeNativeVideo, FlowRecorder,
} from './gate_common.mjs';

const registry = JSON.parse(readFileSync(
  join(REPO_ROOT, 'architecture', 'e2e_persona_journey_registry.json'), 'utf-8'));

const { browser, context } = await launchGate();
const personas = [];

async function bodyMatches(page, pattern) {
  for (let i = 0; i < 3; i++) {
    const found = await page.evaluate(
      (re) => new RegExp(re, 'i').test(document.body.innerText), pattern).catch(() => false);
    if (found) return true;
    await page.waitForTimeout(700);
  }
  return false;
}

for (const persona of registry.personas) {
  const page = await context.newPage();
  const log = attachCollectors(page);
  const recorder = HAS_NATIVE_VIDEO ? null : new FlowRecorder(page, `persona-${persona.id}`).start();
  const record = { id: persona.id, name: persona.name, goal: persona.goal, steps: [], frictions: [] };
  let stepNo = 0;

  async function friction(kind, note, detail = '') {
    const shot = `friction-${persona.id}-${String(stepNo).padStart(2, '0')}.png`;
    await page.screenshot({ path: join(DIRS.screenshots, shot) }).catch(() => {});
    record.frictions.push({ step: stepNo, kind, note, detail: String(detail).slice(0, 200), screenshot: shot });
  }

  for (const step of persona.journey) {
    stepNo += 1;
    let ok = true;
    try {
      if (step.op === 'goto') {
        const resp = await page.goto(step.arg, { waitUntil: 'load', timeout: 20000 });
        await page.waitForTimeout(900);
        // a null response = same-document hash navigation (SPA route change), which is fine
        if (resp && resp.status() >= 400) { ok = false; await friction('load_failed', `goto ${step.arg}`, resp.status()); }
      } else if (step.op === 'pause') {
        await page.waitForTimeout(Number(step.arg));
      } else if (step.op === 'expect_text') {
        if (!(await bodyMatches(page, step.arg))) { ok = false; await friction('expect_failed', step.note || `expected /${step.arg}/i on ${page.url()}`); }
      } else if (step.op === 'probe_text') {
        const found = await bodyMatches(page, step.arg);
        if (step.invert ? found : !found) {
          ok = false;
          await friction(step.invert ? 'leak_detected' : 'probe_missing', step.note, `pattern /${step.arg}/i on ${page.url()}`);
        }
      } else if (step.op === 'probe_selector') {
        const count = await page.locator(step.arg).count();
        if (count === 0) { ok = false; await friction('probe_missing', step.note, `selector ${step.arg} on ${page.url()}`); }
      } else if (step.op === 'expect_selector') {
        await page.waitForSelector(step.arg, { timeout: 6000 });
      } else if (step.op === 'click_text') {
        await page.getByText(step.arg, { exact: false }).first().click({ timeout: 5000 });
        await page.waitForTimeout(900);
      } else if (step.op === 'fill') {
        await page.fill(step.arg, step.value, { timeout: 6000 });
      } else if (step.op === 'expect_hash') {
        const hash = await page.evaluate(() => location.hash);
        if (!hash.startsWith(step.arg)) { ok = false; await friction('expect_failed', step.note || `expected hash ${step.arg}`, hash); }
      }
    } catch (err) {
      ok = false;
      await friction('step_error', step.note || `${step.op} ${step.arg ?? ''} failed`, err);
    }
    record.steps.push({ step: stepNo, op: step.op, arg: step.arg ?? null, ok });
  }

  await page.screenshot({ path: join(DIRS.screenshots, `persona-${persona.id}-final.png`) }).catch(() => {});
  record.page_errors = log.pageErrors;
  record.console_errors = log.console.filter((c) => c.type === 'error').length;
  if (recorder) record.video = (await recorder.stop())?.file ?? null;
  else record._handle = page.video();
  await page.close();
  personas.push(record);
  console.log(`  [${record.frictions.length ? `${record.frictions.length} frictions` : 'smooth'}] ` +
    `${persona.id} (${record.steps.filter((s) => s.ok).length}/${record.steps.length} steps ok)`);
}

await context.close();
await browser.close();
for (const p of personas) {
  if (p._handle) {
    const out = await finalizeNativeVideo(p._handle, `persona-${p.id}`);
    p.video = out ? (out.mp4 || out.webm) : null;
    delete p._handle;
  }
}

const totalFrictions = personas.reduce((n, p) => n + p.frictions.length, 0);
const report = {
  generated_at: new Date().toISOString(),
  gate: 'persona_journeys',
  personas: personas.length,
  total_frictions: totalFrictions,
  results: personas,
};
saveJSON('reports', 'persona-friction-report.json', report);
saveText('reports', 'persona-friction-report.md', [
  `# Persona friction report — ${report.generated_at}`,
  '',
  `${personas.length} customer personas walked the running surfaces; **${totalFrictions} friction findings** (each with a screenshot).`,
  '',
  ...personas.flatMap((p) => [
    `## ${p.name}`,
    `*Goal:* ${p.goal}`,
    `*Video:* videos/${p.video ?? 'HELD'} · *Steps ok:* ${p.steps.filter((s) => s.ok).length}/${p.steps.length}`,
    '',
    ...(p.frictions.length
      ? ['| # | kind | finding | screenshot |', '|---|---|---|---|',
         ...p.frictions.map((f) => `| ${f.step} | ${f.kind} | ${f.note} | ${f.screenshot} |`)]
      : ['_No frictions — journey was smooth._']),
    '',
  ]),
].join('\n'));
console.log(`\npersona journeys: ${personas.length} personas, ${totalFrictions} frictions → reports/persona-friction-report.md`);
process.exit(0);
