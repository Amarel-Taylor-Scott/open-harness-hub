/* global React, navigate, CELogo, BRANDCE, StatusBadge, ThemeToggle */
// Baltor.ai — Docs. Multi-tab docs site (Home · Guides · Reference · Demos · API)
// parallel to a modern docs experience, but every section leads with our edge:
// verification, freshness, provenance. The docs agent dogfoods /serve.

const DOCS_NAV = [['Overview', 'home'], ['Guides', 'guides'], ['Reference', 'reference'], ['Demos', 'demos'], ['API', 'api']];

/* ---------------- HOME ---------------- */
const HOME_CARDS = [
  ['→', 'Getting Started', 'Connect a source and serve verified context in three steps.', 'guides'],
  ['◷', 'Guides', 'Connect, Verify, Compress and Deliver — the assurance workflow end to end.', 'guides'],
  ['◫', 'Reference', 'Glossary and concepts — assurance, tiers, provenance, oracle corpora.', 'reference'],
  ['✔', 'Verification', 'How we check a corpus against the source of truth — and prove it.', 'reference'],
  ['◳', 'Demos', 'Interactive scenarios where the corpus is checked against live authority.', 'demos'],
  ['⚙', 'API', 'REST reference for corpora, serving, verification, commons and artifacts.', 'api'],
];

/* ---------------- GUIDES ---------------- */
const GUIDE_NAV = [
  ['Start here', [['start', 'Getting Started'], ['why', 'Why assurance'], ['concepts', 'Core concepts']]],
  ['The workflow', [['connect', 'Connect a source'], ['verify', 'Verify against truth'], ['compress', 'Compress to tiers'], ['deliver', 'Deliver to agents']]],
  ['Operate', [['freshness', 'Freshness & SLAs'], ['hitl', 'Human-in-the-loop'], ['compliance', 'Compliance artifacts']]],
];
// each guide page has real content; TOC is derived from its h2 blocks.
const GUIDE_ARTICLES = {
  start: { crumb: 'Start here', title: 'Getting Started', lede: 'Everything you need to serve verified, current, provable context to your agents.', body: [
    ['p', 'Baltor is the context-assurance layer for AI agents. Most tools check that your documents are current. Baltor checks that they are correct — against the source of truth — then proves it with signed provenance and serves it into the agent you already run.'],
    ['callout', 'We never train on your data, and every served claim is traceable to a source you approved.'],
    ['h2', 'How it works'],
    ['p', 'Getting started takes three steps:'],
    ['steps', [
      ['Connect a source', 'Point Baltor at your docs, a repo, or subscribe to an oracle corpus from the Commons. Parsing handles tables, figures and complex layouts.'],
      ['Verify against truth', 'Baltor continuously checks each claim against live authoritative sources. Stale or contradicted claims are flagged and escalated to a human.'],
      ['Serve to your agent', 'Query over MCP or REST. Every response is tier-selected, citation-anchored and verified.'],
    ]],
    ['h2', 'Your first corpus'],
    ['p', 'Create a corpus from a source URL. Your data stays isolated; nothing is shared across workspaces.'],
    ['code', 'POST /v1/corpora\n{ "source": "https://docs.acme.com", "tiers": ["raw","compressed","hyper"] }'],
    ['h2', 'Next steps'],
    ['p', 'Read “Why assurance” for the thesis, or jump to “Connect a source” to wire up your first authoritative feed.'],
  ] },
  why: { crumb: 'Start here', title: 'Why assurance', lede: 'Current is not the same as correct. Here is the gap Baltor closes.', body: [
    ['p', 'Retrieval-augmented generation makes an answer faithful to your corpus — even when the corpus is wrong. Sync keeps an index in step with a source, but says nothing about whether the source itself is stale or contradicted.'],
    ['h2', 'The four failure modes'],
    ['p', 'Context fails in ways no amount of model quality can fix:'],
    ['steps', [
      ['Stale', 'A regulation changed two weeks ago; the index still serves the old number.'],
      ['Unverified', 'Retrieved confidently from a source nobody checked against the truth.'],
      ['Contradictory', 'Two authoritative sources disagree and nothing reconciles them.'],
      ['Bloated', 'Tens of thousands of tokens where a few hundred verified ones would do.'],
    ]],
    ['h2', 'What assurance adds'],
    ['p', 'Assurance is a bundle: provenance (where it came from), verification (it is correct), and freshness (it is current) — with proof on all three. Nobody sells all three together; that bundle is the differentiator.'],
    ['callout', 'Most platforms check your docs are current. We check they are correct against the source of truth.'],
  ] },
  concepts: { crumb: 'Start here', title: 'Core concepts', lede: 'The objects you will work with across the platform.', body: [
    ['h2', 'Corpus'],
    ['p', 'A governed, tiered set of context built from one or more sources. Every corpus has provenance, a verification record, freshness status and emittable compliance artifacts.'],
    ['h2', 'Tiers'],
    ['p', 'One corpus, three representations — raw (full fidelity), compressed (deduped, near-full), and hyper-efficient (claim-level, token-minimal). Every tier preserves source spans.'],
    ['h2', 'Oracle publisher'],
    ['p', 'A government, agency or standards body that signs and publishes a corpus to the Commons — the authoritative source the rest of the system reconciles against.'],
    ['h2', 'Conflict'],
    ['p', 'A detected mismatch between internal content and the authoritative source: superseded, contradicted, stale, or integrity-flagged. Conflicts route to human review before serving.'],
  ] },
  connect: { crumb: 'The workflow', title: 'Connect a source', lede: 'Bring context in — your own, or an oracle corpus from the Commons.', body: [
    ['p', 'There are two ways context enters Baltor. You never “build” a corpus by hand — you Connect your own, or Subscribe to one we maintain.'],
    ['h2', 'Connect your own'],
    ['p', 'Point at a docs site, a repository, files, or a database. Parsing handles tables, figures and complex layouts; each source is chunked and fingerprinted.'],
    ['code', 'POST /v1/corpora\n{ "source": "github.com/acme/policies", "type": "repo" }'],
    ['h2', 'Subscribe to an oracle corpus'],
    ['p', 'Browse the Commons and subscribe to a signed, continuously-verified corpus — OFAC, EUR-Lex, FATF, ILO, Codex and more. It stays verified against its source automatically.'],
    ['callout', 'A domain we don’t carry yet can be requested — we build and verify it, then it enters the Commons.'],
  ] },
  verify: { crumb: 'The workflow', title: 'Verify against truth', lede: 'The differentiator — an adversarial check of your corpus against live authority.', body: [
    ['p', 'Baltor watches the authoritative sources behind your corpus and reconciles your content against them on every change. Freshness is sync; verification is correctness — Baltor does both.'],
    ['h2', 'What gets checked'],
    ['steps', [
      ['Currency', 'Has the cited value been superseded by a newer authoritative version?'],
      ['Consistency', 'Do two authoritative sources disagree, and which governs?'],
      ['Integrity', 'Is a document signed by a real publisher, or an unsigned imposter (corpus-poisoning)?'],
    ]],
    ['h2', 'When a conflict is found'],
    ['p', 'The claim is flagged with a severity and held out of serving. A human reviews and decides — apply the update, keep internal, or escalate. Every decision is recorded.'],
    ['code', 'GET /v1/corpora/eu-reg/verify\n→ { "conflicts": [ { "type": "superseded", "severity": "high", "status": "open" } ] }'],
  ] },
  compress: { crumb: 'The workflow', title: 'Compress to tiers', lede: 'Fewer tokens, measured fidelity — never a black box.', body: [
    ['p', 'After verification, Baltor distils the corpus into three tiers so agents can request exactly the fidelity they need.'],
    ['h2', 'The three tiers'],
    ['steps', [
      ['Raw', 'Full fidelity — every token, every source span. For audit and re-processing.'],
      ['Compressed', 'Deduped and normalized; near-full fidelity. The everyday default.'],
      ['Hyper-efficient', 'Claim-level, citation-anchored, token-minimal. For live agent context windows.'],
    ]],
    ['h2', 'Measured fidelity'],
    ['p', 'Every compression step emits a fidelity delta so you can see exactly what was traded for token savings — the opposite of an opaque embedding.'],
    ['callout', 'We say “lean” and “efficient,” never “lossless.” The fidelity record proves the trade-off.'],
  ] },
  deliver: { crumb: 'The workflow', title: 'Deliver to agents', lede: 'Serve verified context into the agent you already run — or push it upstream.', body: [
    ['p', 'One governed endpoint per corpus. Agents request the tier they need; every response is cited and verified — model- and platform-neutral.'],
    ['h2', 'Serve over MCP or REST'],
    ['code', 'GET /v1/corpora/acme-policy/serve?tier=hyper-efficient&cite=true'],
    ['p', 'Works with Claude Code, Codex, Cursor, or any MCP-aware agent. No re-platforming.'],
    ['h2', 'Push upstream'],
    ['p', 'Export a verified corpus into Snowflake, pgvector, or another RAG platform. Baltor sits upstream as the verified-context supplier — the assurance layer your stack lacks.'],
  ] },
  freshness: { crumb: 'Operate', title: 'Freshness & SLAs', lede: 'You pay for the latency of truth.', body: [
    ['p', 'Freshness is how quickly a change in the authoritative source propagates to your served context. Different domains demand different latencies.'],
    ['h2', 'Cadence by domain'],
    ['steps', [
      ['Live · webhook', 'Changelogs and internal registries — propagate on push.'],
      ['Several times a day', 'Sanctions and export-control lists — a stale list is a federal-risk event.'],
      ['On amendment', 'Statutes and regulations — reconciled when the authoritative text changes.'],
    ]],
    ['h2', 'The change feed'],
    ['p', 'Every watched source emits a change feed. When something moves, affected corpora are re-verified and any newly-stale claim is flagged.'],
  ] },
  hitl: { crumb: 'Operate', title: 'Human-in-the-loop', lede: 'Automation finds the conflict; a human makes the call.', body: [
    ['p', 'When verification flags an ambiguous conflict, Baltor does not silently overwrite your corpus. It escalates to a reviewer with the evidence.'],
    ['h2', 'The review decision'],
    ['steps', [
      ['Apply update', 'Accept the authoritative value; the corpus and affected tiers are re-anchored.'],
      ['Keep internal', 'Retain the internal value (with a recorded rationale).'],
      ['Escalate', 'Route to a domain owner for a deeper call.'],
    ]],
    ['h2', 'Audit trail'],
    ['p', 'Every decision is recorded with who, when and why — the basis of the compliance artifacts.'],
  ] },
  compliance: { crumb: 'Operate', title: 'Compliance artifacts', lede: 'The regulator-facing deliverable — beyond in-product citations.', body: [
    ['p', 'For any corpus version, Baltor emits portable, signed artifacts that prove what was served and where it came from.'],
    ['h2', 'What you can emit'],
    ['steps', [
      ['AIBOM · CycloneDX', 'A machine-readable bill of materials for every source, tier and signature.'],
      ['EU AI Act dossier', 'Article 10 data-governance + Article 50 transparency documentation, pre-filled.'],
      ['C2PA manifest', 'A signed origin chain — who published each source, when, and the verifying signature.'],
      ['Measured-fidelity record', 'Groundedness and freshness scores with the verification log behind them.'],
    ]],
    ['callout', 'Provenance proves origin; verification proves it’s still true — every artifact carries both.'],
  ] },
};

/* ---------------- REFERENCE (glossary) ---------------- */
const GLOSSARY = [
  ['Assurance', 'The bundle that makes context trustworthy: provenance (where it came from), verification (it’s correct), and freshness (it’s current) — with proof on all three.'],
  ['Verification', 'An adversarial check of corpus content against an external authoritative source, with human-in-the-loop on conflicts. Proves the corpus is correct, not just retrieved.'],
  ['Tiers', 'One corpus, three representations: raw (full fidelity), compressed (deduped, near-full), and hyper-efficient (claim-level, token-minimal). Every tier keeps source spans.'],
  ['Oracle publisher', 'A government, UN agency or standards body that signs and publishes a corpus to the Commons — the authoritative source the rest of the system reconciles against.'],
  ['Provenance', 'A signed origin chain (C2PA-style manifest + attestation registry). Verify any corpus version by file hash.'],
  ['Freshness SLA', 'The latency of truth: how quickly a change in the authoritative source propagates to your served context. You pay for lower latency.'],
  ['Reconciliation', 'Resolving a conflict between internal content and the authoritative source — superseded, contradicted, stale, or integrity-flagged.'],
  ['HITL', 'Human-in-the-loop: a reviewer decision (apply / keep / escalate) recorded when verification flags an ambiguous conflict.'],
  ['Compliance artifact', 'A regulator-facing export — AIBOM (CycloneDX), EU AI Act dossier, C2PA manifest, or measured-fidelity record — emitted per corpus version.'],
];

/* ---------------- DEMOS ---------------- */
const DEMOS = [
  { group: 'Context assurance', blurb: 'Scenarios where the corpus is checked against live authority — and we catch what’s wrong before an agent reads it.', items: [
    { id: 'sanctions', tag: 'FLAGSHIP', name: 'Sanctions Currency Check', domain: 'OFAC · BIS · EU',
      desc: 'Screen an internal sanctions list against the live OFAC SDN feed. Baltor catches an entity added six days ago that the internal index missed — a stale-list federal-risk event.',
      corpus: 'acme_sanctions_screening.corpus', source: 'OFAC SDN (live)',
      queries: ['Is this counterparty currently sanctioned?', 'What changed in the last 7 days?', 'Which served claims are now stale?'],
      caught: { type: 'superseded', sev: 'high', claim: '“Entity ‘Volna Shipping LLC’ is not on the SDN list.”', now: 'Added to OFAC SDN 6 days ago', src: 'OFAC SDN · 2026-05-22 update' } },
    { id: 'eudr', tag: 'PRODUCTION', name: 'Regulatory Reconciliation', domain: 'EUR-Lex · CSDDD',
      desc: 'Reconcile an internal compliance corpus against EUR-Lex. Baltor detects the EUDR application date was deferred 12 months and the old date is still being served.',
      corpus: 'eu_compliance.corpus', source: 'EUR-Lex (live)',
      queries: ['When does EUDR apply to large operators?', 'Has any cited date been superseded?', 'Show the reconciliation trail.'],
      caught: { type: 'superseded', sev: 'high', claim: '“EUDR obligations apply from 30 December 2024.”', now: 'Deferred to 30 December 2025', src: 'EUR-Lex · Reg (EU) 2023/1115 amendment' } },
    { id: 'poison', tag: 'NEW', name: 'Corpus Poisoning Defense', domain: 'Integrity',
      desc: 'An unsigned document appears to supersede a real rule. Baltor quarantines it — no authoritative signature, classic BadRAG/TrojanRAG pattern — before it can be cited.',
      corpus: 'acme_policy.corpus', source: 'Attestation registry',
      queries: ['Was this policy threshold raised to 5,000?', 'Which sources lack a valid signature?', 'What was quarantined and why?'],
      caught: { type: 'integrity', sev: 'high', claim: '“An internal memo raised the CSDDD threshold to 5,000.”', now: 'No corroborating oracle source · no C2PA manifest', src: 'Integrity check · quarantined' } },
  ] },
  { group: 'Agentic serving', blurb: 'Serve verified, token-lean context into the agent you already run — model- and platform-neutral.', items: [
    { id: 'claude-code', tag: 'PRODUCTION', name: 'Claude Code over MCP', domain: 'MCP',
      desc: 'Serve the hyper-efficient tier into Claude Code over MCP. Every chunk is cited and verified; ~1.2k tokens instead of ~24k raw.',
      corpus: 'product_docs.corpus', source: 'MCP endpoint',
      queries: ['What’s the current API rate limit?', 'Cite the source for each answer.', 'How many tokens did this cost?'],
      caught: null },
    { id: 'upstream', tag: 'PRODUCTION', name: 'Upstream of any RAG stack', domain: 'Snowflake · pgvector',
      desc: 'Push a verified corpus into Snowflake, pgvector or even Contextual. Baltor sits upstream as the verified-context supplier — the assurance layer your stack lacks.',
      corpus: 'research_library.corpus', source: 'Export target',
      queries: ['Export the compressed tier to Snowflake.', 'Attach the AIBOM artifact.', 'Verify the export by hash.'],
      caught: null },
  ] },
];
const DEMO_BY_ID = Object.fromEntries(DEMOS.flatMap((g) => g.items).map((d) => [d.id, d]));
const SEVB = { high: 'oh-badge--danger', med: 'oh-badge--warn', low: 'oh-badge--muted' };

const MB = { GET: 'get', POST: 'post', PUT: 'put', DEL: 'del' };

/* ===================== VIEWS ===================== */
function HomeView({ go }) {
  return (
    <div className="ce-docs-home">
      <div className="ce-dh-hero">
        <div className="ce-eyebrow">{BRANDCE.wordmark} Docs</div>
        <h1>Build agents on context you can trust.</h1>
        <p>Connect a source, verify it against the truth, and serve cited context to any agent. Start below.</p>
      </div>
      <div className="ce-dh-grid">
        {HOME_CARDS.map(([ic, t, d, tab]) => (
          <button className="oh-card oh-card--interactive ce-dh-card" key={t} onClick={() => go(tab)}>
            <span className="ic">{ic}</span><div className="t">{t}</div><div className="d">{d}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

function GuidesView() {
  const [active, setActive] = React.useState('start');
  const a = GUIDE_ARTICLES[active] || GUIDE_ARTICLES.start;
  const toc = a.body.filter((b) => b[0] === 'h2').map((b) => b[1]);
  return (
    <div className="ce-docs-body">
      <nav className="ce-docs-side">
        {GUIDE_NAV.map(([sec, items]) => (
          <div className="ds-group" key={sec}>
            <div className="ds-group-h">{sec}</div>
            {items.map(([id, label]) => (
              <button key={id} className={'ds-link plain' + (active === id ? ' on' : '')} onClick={() => setActive(id)}>{label}</button>
            ))}
          </div>
        ))}
      </nav>
      <main className="ce-docs-main">
        <div className="dm-crumb mono">{a.crumb}</div>
        <h1>{a.title}</h1>
        <p className="dm-desc">{a.lede}</p>
        {a.body.map((blk, i) => {
          const [kind, content] = blk;
          if (kind === 'h2') return <h2 className="dm-h2" key={i} id={'s' + i}>{content}</h2>;
          if (kind === 'p') return <p className="dm-body" key={i}>{content}</p>;
          if (kind === 'callout') return <div className="dm-callout" key={i}><span className="i">ⓘ</span><span>{content}</span></div>;
          if (kind === 'code') return <pre className="dsa-code dm-code" key={i}>{content}</pre>;
          if (kind === 'steps') return (
            <ol className="dm-steps" key={i}>
              {content.map(([t, d]) => <li key={t}><b>{t}</b> — {d}</li>)}
            </ol>
          );
          return null;
        })}
        <div className="dm-pagenav">
          {(() => {
            const ids = GUIDE_NAV.flatMap((g) => g[1]);
            const idx = ids.findIndex((x) => x[0] === active);
            const prev = ids[idx - 1], next = ids[idx + 1];
            return (
              <>
                {prev ? <button className="dm-pn prev" onClick={() => setActive(prev[0])}>← {prev[1]}</button> : <span />}
                {next ? <button className="dm-pn next" onClick={() => setActive(next[0])}>{next[1]} →</button> : <span />}
              </>
            );
          })()}
        </div>
      </main>
      <div className="ce-docs-right">
        <div className="ce-toc">
          <div className="ce-toc-h">On this page</div>
          {toc.map((t, i) => <a key={i} href={'#s' + (a.body.findIndex((b) => b[0] === 'h2' && b[1] === t))} className="ce-toc-link">{t}</a>)}
        </div>
      </div>
    </div>
  );
}

function ReferenceView() {
  return (
    <div className="ce-docs-body">
      <nav className="ce-docs-side">
        <div className="ds-group">
          <div className="ds-group-h">Key terms</div>
          {GLOSSARY.map(([t]) => <a key={t} className="ds-link plain" href={'#g-' + t}>{t}</a>)}
        </div>
      </nav>
      <main className="ce-docs-main">
        <div className="dm-crumb mono">Reference</div>
        <h1>Glossary</h1>
        <p className="dm-desc">Essential concepts for context assurance with {BRANDCE.name}.</p>
        {GLOSSARY.map(([t, d]) => (
          <div className="ce-gloss" key={t} id={'g-' + t}><h2 className="dm-h2">{t}</h2><p className="dm-body">{d}</p></div>
        ))}
      </main>
      <div className="ce-docs-right" />
    </div>
  );
}

function ApiView({ sel, setSel, ALL_EP, ENDPOINTS }) {
  const ep = ALL_EP.find((e) => e.id === sel) || ALL_EP[0];
  return (
    <div className="ce-docs-body">
      <nav className="ce-docs-side">
        {ENDPOINTS.map((g) => (
          <div className="ds-group" key={g.group}>
            <div className="ds-group-h">{g.group}</div>
            {g.items.map((e) => (
              <button key={e.id} className={'ds-link' + (sel === e.id ? ' on' : '')} onClick={() => setSel(e.id)}>
                <span className={'ce-mb ce-mb--' + MB[e.m]}>{e.m}</span>{e.name}
              </button>
            ))}
          </div>
        ))}
      </nav>
      <main className="ce-docs-main">
        <div className="dm-crumb mono">{ep.path.split('/').slice(0, 3).join('/')}</div>
        <h1>{ep.name}</h1>
        <p className="dm-desc">{ep.desc}</p>
        <div className="dm-try"><span className={'ce-mb ce-mb--' + MB[ep.m]}>{ep.m}</span><span className="mono">{ep.path}</span><button className="oh-btn oh-btn--primary oh-btn--sm">Try it ▸</button></div>
        <h3 className="dm-h">Authorization</h3>
        <p className="dm-pdesc">Bearer authentication: <span className="mono">Authorization: Bearer &lt;token&gt;</span></p>
        <h3 className="dm-h">Query parameters</h3>
        <div className="dm-params">
          {ep.params.map(([n, t, req, d]) => (
            <div className="dm-param" key={n}>
              <div className="dp-top"><span className="mono dp-name">{n}</span><span className="mono dp-type">{t}</span>{req ? <span className="dp-req">required</span> : <span className="dp-opt">optional</span>}</div>
              <div className="dp-desc">{d}</div>
            </div>
          ))}
        </div>
      </main>
      <div className="ce-docs-right">
        <div className="ce-docs-sample">
          <div className="dsa-head"><span>Response</span><span className="mono">200</span></div>
          <pre className="dsa-code">{ep.res}</pre>
        </div>
        <DocsAgent />
      </div>
    </div>
  );
}

/* ---- Demos: gallery + runner ---- */
function DemosGallery({ open }) {
  return (
    <div className="ce-docs-wide">
      <div className="ce-dh-hero">
        <div className="ce-eyebrow">Demos</div>
        <h1>See assurance in action.</h1>
        <p>Interactive scenarios where a corpus is checked against live authority — and Baltor catches what’s wrong before an agent ever reads it.</p>
      </div>
      {DEMOS.map((g) => (
        <section className="ce-demosec" key={g.group}>
          <h2 className="ce-section-h">{g.group}</h2>
          <p className="ce-demosec-blurb">{g.blurb}</p>
          <div className="ce-demogrid">
            {g.items.map((d) => (
              <button className="oh-card oh-card--interactive ce-democard" key={d.id} onClick={() => open(d.id)}>
                <div className="dc-top"><span className="dc-domain">{d.domain}</span><span className={'ce-demotag t-' + d.tag.toLowerCase()}>{d.tag}</span></div>
                <h3>{d.name}</h3>
                <p>{d.desc}</p>
                <span className="dc-launch">Launch demo →</span>
              </button>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function DemoRunner({ id, back }) {
  const d = DEMO_BY_ID[id];
  const [phase, setPhase] = React.useState('idle'); // idle | running | done
  const [step, setStep] = React.useState(0);
  const STEPS = ['Parsing corpus', 'Watching authoritative source', 'Reconciling claims', 'Scoring freshness & integrity', 'Citing & serving'];
  React.useEffect(() => {
    if (phase !== 'running') return;
    if (step >= STEPS.length) { const t = setTimeout(() => setPhase('done'), 400); return () => clearTimeout(t); }
    const t = setTimeout(() => setStep((s) => s + 1), 520); return () => clearTimeout(t);
  }, [phase, step]);
  const run = () => { setPhase('running'); setStep(0); };
  if (!d) return null;
  return (
    <div className="ce-docs-wide ce-runner">
      <a className="ce-back" onClick={back}>← All demos</a>
      <div className="ce-runner-head">
        <div>
          <div className="ce-eyebrow">{d.domain}</div>
          <h1>{d.name}</h1>
          <p>{d.desc}</p>
        </div>
        <span className={'ce-demotag t-' + d.tag.toLowerCase()}>{d.tag}</span>
      </div>
      <div className="ce-runner-grid">
        <div className="ce-runner-l">
          <div className="oh-card oh-card--pad">
            <div className="ce-rl-h">Inputs</div>
            <div className="ce-filerow"><span className="fr-ic">◫</span><div className="fr-b"><div className="fr-n mono">{d.corpus}</div><div className="fr-t">Your corpus</div></div><button className="oh-btn oh-btn--ghost oh-btn--sm">Preview</button></div>
            <div className="ce-filerow"><span className="fr-ic">✓</span><div className="fr-b"><div className="fr-n mono">{d.source}</div><div className="fr-t">Authoritative source</div></div><span className="oh-badge oh-badge--verified oh-badge--sm">live</span></div>
          </div>
          <div className="oh-card oh-card--pad">
            <div className="ce-rl-h">Analysis progress</div>
            {phase === 'idle' && <div className="ce-rl-idle">Run the analysis to see real-time verification steps and any caught conflicts.</div>}
            {phase !== 'idle' && (
              <div className="ce-progress">
                {STEPS.map((s, i) => (
                  <div key={s} className={'row' + (i < step || phase === 'done' ? ' done' : i === step ? ' active' : '')}>
                    <span className="mk">{(i < step || phase === 'done') ? '✓' : i === step ? '◌' : '·'}</span>{s}
                  </div>
                ))}
              </div>
            )}
            <button className="oh-btn oh-btn--primary" style={{ marginTop: 14, width: '100%', justifyContent: 'center' }} onClick={run} disabled={phase === 'running'}>
              {phase === 'idle' ? 'Run analysis →' : phase === 'running' ? 'Analyzing…' : 'Re-run'}
            </button>
          </div>
          <div className="oh-card oh-card--pad">
            <div className="ce-rl-h">Suggested queries</div>
            <div className="ce-suggq">{d.queries.map((q) => <button key={q} className="ce-sq">{q}</button>)}</div>
          </div>
        </div>
        <div className="ce-runner-r">
          {phase !== 'done' ? (
            <div className="oh-card oh-card--pad ce-runner-empty">
              <div className="re-ic">◳</div>
              <div className="re-t">Verified result will appear here</div>
              <div className="re-d">Baltor serves cited context and flags anything stale, contradicted or unsigned.</div>
            </div>
          ) : (
            <>
              {d.caught ? (
                <div className={'oh-card ce-caught sev-' + d.caught.sev}>
                  <div className="ca-h"><span className={'oh-badge ' + SEVB[d.caught.sev]}>{d.caught.sev === 'high' ? 'High' : 'Medium'}</span><span className="oh-badge">{d.caught.type}</span><span className="ca-ttl">Conflict caught before serving</span></div>
                  <div className="ca-diff">
                    <div className="ca-side bad"><div className="lbl">Internal corpus said</div><div className="val">{d.caught.claim}</div></div>
                    <span className="ca-arrow">→</span>
                    <div className="ca-side good"><div className="lbl">Live authoritative source</div><div className="val">{d.caught.now}</div><div className="src mono">{d.caught.src}</div></div>
                  </div>
                  <div className="ca-foot"><span className="oh-badge oh-badge--warn">escalated to human review</span><span className="mono">held out of /serve</span></div>
                </div>
              ) : (
                <div className="oh-card oh-card--pad ce-served">
                  <div className="ca-h"><span className="oh-badge oh-badge--verified">✔ verified · 0 open conflicts</span></div>
                  <p className="ce-served-q">“{d.queries[0]}”</p>
                  <div className="ce-served-a">Served the hyper-efficient tier with a citation behind every claim — ~1.2k tokens, checked against {d.source} before return.</div>
                  <div className="da-cites"><span className="oh-badge oh-badge--verified oh-badge--sm">✔ cited</span><span className="oh-badge oh-badge--verified oh-badge--sm">✔ current</span></div>
                </div>
              )}
              <div className="oh-card oh-card--pad ce-runner-note">
                <b>Why this matters.</b> A retrieval-only stack would have returned the internal answer confidently. {BRANDCE.name} checks the corpus against the source of truth first — that’s the assurance layer.
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function DocsAgent() {
  return (
    <aside className="ce-docs-agent">
      <div className="da-head">
        <div className="da-title">Docs agent</div>
        <div className="da-by">Powered by {BRANDCE.name}</div>
      </div>
      <div className="da-q">Does the served context stay correct when the law changes?</div>
      <div className="da-steps"><span className="dot" />verified · 4 of 4 steps · 6 sources</div>
      <div className="da-answer">
        <p>Yes. The <code>/serve</code> endpoint checks each chunk against live authoritative sources before returning it; anything stale or contradicted is flagged and held for review.</p>
        <div className="da-cites">
          <span className="oh-badge oh-badge--verified oh-badge--sm">✔ /serve</span>
          <span className="oh-badge oh-badge--verified oh-badge--sm">✔ /verify</span>
        </div>
      </div>
      <div className="da-input"><input placeholder="Ask a question…" /><button className="oh-btn oh-btn--primary oh-btn--sm" aria-label="Ask">↑</button></div>
    </aside>
  );
}

function DocsPage() {
  const [tab, setTab] = React.useState('home');
  const [sel, setSel] = React.useState('serve');
  const [demo, setDemo] = React.useState(null);
  const goTab = (t) => { setTab(t); setDemo(null); };
  return (
    <div className="ce-docs">
      <header className="ce-docs-top">
        <a className="ce-docs-brand" onClick={() => navigate('/')}>
          <span className="ce-docs-wm"><span className="sub">docs.</span>{BRANDCE.name}<span className="tld">.ai</span></span>
        </a>
        <nav className="ce-docs-nav-top">
          {DOCS_NAV.map(([l, k]) => <a key={k} className={tab === k ? 'on' : ''} onClick={() => goTab(k)}>{l}</a>)}
        </nav>
        <span className="ce-spacer" />
        <ThemeToggle />
        <button className="oh-btn oh-btn--primary oh-btn--sm" onClick={() => navigate('/corpora')}>Login ›</button>
      </header>
      {tab === 'home' && <HomeView go={goTab} />}
      {tab === 'guides' && <GuidesView />}
      {tab === 'reference' && <ReferenceView />}
      {tab === 'demos' && (demo ? <DemoRunner id={demo} back={() => setDemo(null)} /> : <DemosGallery open={setDemo} />)}
      {tab === 'api' && <ApiView sel={sel} setSel={setSel} ALL_EP={ALL_EP} ENDPOINTS={ENDPOINTS} />}
    </div>
  );
}

Object.assign(window, { DocsPage });
