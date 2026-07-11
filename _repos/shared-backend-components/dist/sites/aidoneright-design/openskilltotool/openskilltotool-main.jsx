/* global React, ReactDOM, PORTFOLIO, makeHub, Os2tConverterDetail, Os2tArchitecture, Os2tApiRef, Os2tConvertWizard */
// OpenSkillToTool.io — skill→tool conversion registry. Built on the shared hub module.
// Internal + public-facing. Specializes in converting OPEN-ENDED, context-guided skills into
// MORE DETERMINISTIC, typed, permissioned tools (the same unbounded→deterministic spine Teleon
// runs, applied to skill packaging). The bridge between OpenSkillsHub (know-how) and
// OpenToolsHub (callable actions).

const E = PORTFOLIO.ENTITIES.openSkillToTool;
const App = makeHub({
  brand: { name: 'OpenSkillToTool', tld: '.io', glyph: '⇋', accent: E.accent },
  kind: E.kind,
  themeKey: 'os2t-theme',
  noun: 'converter', nounPlural: 'converters', indefinite: 'a converter',
  heroTitle: <>Open-ended <span className="tint">skill</span> in. Deterministic tool out.</>,
  lede: 'A skill is open-ended, context-guided know-how; a tool is a typed, repeatable action. OpenSkillToTool converts a governed skill into a deterministic tool contract — fixed schema, declared scopes, carried-over eval and provenance — callable over MCP or HTTP. Used internally to harden our own skills, and public-facing for the ecosystem.',
  ledeVariants: {
    A: 'A skill is open-ended, context-guided know-how; a tool is a typed, repeatable action. OpenSkillToTool converts a governed skill into a deterministic tool contract — fixed schema, declared scopes, carried-over eval and provenance — callable over MCP or HTTP. Used internally to harden our own skills, and public-facing for the ecosystem.',
    B: 'Open-ended in, deterministic out. Convert a context-guided skill into a typed, scoped, repeatable tool — with the eval and provenance carried across.',
    C: 'Skills are flexible; tools are dependable. Collapse an open-ended, context-guided skill into a fixed, callable tool contract — schema, least-privilege scopes, signed provenance — in one step.',
  },
  howTitle: 'From an open-ended skill to a deterministic tool.',
  howBody: <>Pick a governed <strong>skill</strong> — open-ended, context-guided know-how — and a converter collapses it
    into a <strong>deterministic tool contract</strong>: a fixed input/output schema, the least-privilege scopes it needs,
    and its eval score + provenance carried across. Use it internally to harden a skill, or publish it to OpenToolsHub
    and call it from Teleon.</>,
  features: [
    ['⇋', 'Open-ended → deterministic', 'Collapses a context-guided skill into a fixed, repeatable tool contract — same input, same shape, every call.'],
    ['⛨', 'Scopes carried across', 'The tool declares the least-privilege scopes the skill actually needs; nothing blind.'],
    ['✓', 'Eval & provenance preserved', 'The skill’s eval score and signed provenance ride along — discovery is not trust.'],
  ],
  facets: ['Research', 'Data', 'Code', 'Comms', 'Ops'],
  convert: {
    navLabel: 'Convert', cta: 'Convert a skill →',
    title: 'Skill → tool workbench',
    sub: 'Pick a governed, open-ended skill and watch it collapse into a deterministic, typed tool contract — schema, scopes, eval and provenance carried across.',
    fromLabel: 'Open-ended skill', fromNote: 'Governed skills from OpenSkillsHub — flexible, context-guided know-how.',
    toLabel: 'Deterministic tool', hint: 'Same input → same shape, every call. Discovery is not trust — the eval and provenance ride along.',
    publishTo: { label: 'OpenToolsHub →', href: '../opentoolshub/OpenToolsHub.html' },
    // multi-step wizard (select skill → review contract → bind scopes → harden & publish)
    render: (h) => <Os2tConvertWizard cfg={h.cfg} />,
  },
  // backend/architecture + API reference as first-class app pages (config-gated hub hooks)
  extraRoutes: [
    { path: '/architecture', navLabel: 'Architecture', navIcon: '◇', group: 'Build', render: () => <Os2tArchitecture /> },
    { path: '/api', navLabel: 'API', navIcon: '⌨', group: 'Developers', render: () => <Os2tApiRef /> },
  ],
  // the rich converter anatomy on every entry-detail page (source skill → contract → scopes → parity → fixtures)
  entryExtra: (e) => <Os2tConverterDetail e={e} />,
  installCmd: (e) => 's2t convert ' + e.id + '@' + (e.ver || '1.2.0') + '\n# → emits a typed tool contract + requests its scopes',
  // each entry = a converter wrapping a named skill into a tool (skill → tool)
  entries: [
    { id: 'summarize-doc', name: 'Summarize Doc → Tool', by: '@ada', facet: 'Research', score: '4.8', installs: '6.4k', ver: '1.4.0', desc: 'Wraps the document-summarization skill as a typed tool: text in, cited summary out.', deps: ['skill:summarize-doc@2.1'] },
    { id: 'classify-risk', name: 'Classify Risk → Tool', by: '@risk-commons', facet: 'Data', score: '4.7', installs: '4.2k', ver: '1.2.0', desc: 'Turns the risk-classification skill into a scoped tool returning a labelled, cited verdict.', deps: ['skill:classify-risk@1.5'] },
    { id: 'extract-fields', name: 'Extract Fields → Tool', by: '@data-open', facet: 'Data', score: '4.9', installs: '8.1k', ver: '2.0.0', desc: 'Wraps the structured-extraction skill: document in, typed JSON record out, schema-validated.', deps: ['skill:extract-fields@3.0'] },
    { id: 'draft-reply', name: 'Draft Reply → Tool', by: '@comms-open', facet: 'Comms', score: '4.4', installs: '3.3k', ver: '1.1.0', desc: 'Converts the reply-drafting skill into a tool with a scoped, rate-limited send step.', deps: ['skill:draft-reply@1.3'] },
    { id: 'review-diff', name: 'Review Diff → Tool', by: '@dev-open', facet: 'Code', score: '4.6', installs: '5.0k', ver: '1.6.0', desc: 'Wraps the code-review skill as a tool: a diff in, structured review comments out.', deps: ['skill:review-diff@2.2'] },
    { id: 'triage-ticket', name: 'Triage Ticket → Tool', by: '@ops-commons', facet: 'Ops', score: '4.5', installs: '3.9k', ver: '1.0.0', desc: 'Turns the ticket-triage skill into a tool returning a routed, prioritised verdict with reasons.', deps: ['skill:triage-ticket@1.1'] },
  ],
});
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
