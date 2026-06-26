/* global React, navigate, Mark, PNotFound */
// Audience landing pages — /for/:who (marketing, sidebar-free)
const USECASES = {
  governments: { tag: 'For governments & standards bodies', hl: 'Publish authoritative facts the world can cite.', sub: 'Sign, date and version your regulations, standards and datasets so any AI pipeline cites them with provenance — and you control freshness and revocation.', cta: 'Publish facts', to: '/publish', points: [['🛡 Signed & dated', 'Every fact carries C2PA provenance traceable to you.'], ['⟳ You control freshness', 'Push amendments and revocations; citing flows update automatically.'], ['🌐 Cited everywhere', 'Become the verified source across the ecosystem.']] },
  builders: { tag: 'For pipeline builders', hl: 'Tired of facts changing faster than your LLM?', sub: 'Stop baking stale knowledge into prompts. Plug governed, live corpora into your pipelines over MCP — fresh, cited and swappable without re-prompting.', cta: 'Improve a pipeline', to: '/improve', points: [['⟳ Always-fresh knowledge', 'Change-data-capture keeps corpora current; your flows don’t rot.'], ['⇄ MCP-native', 'Your agents pull governed components locally; your data stays put.'], ['▲ Measured lift', 'Prove each flow beats a bare model — and watch for decay.']] },
  lawyers: { tag: 'For legal teams', hl: 'Answers with citations a partner would sign off on.', sub: 'Every claim resolves to a sourced clause across jurisdictions and languages — with an attestation you can attach to the file.', cta: 'See certified export', to: '/attest', points: [['✔ Sourced claims', 'A deterministic citation gate — no uncited assertions.'], ['📄 Audit-ready', 'A signed, dated attestation valid through a set date.'], ['🌐 13+ languages', 'Cross-jurisdiction, cross-language coverage.']] },
  regulators: { tag: 'For regulators & auditors', hl: 'Verify compliance with a complete auditable trail.', sub: 'Replayable runs, provenance graphs and immutable audit logs — see exactly what was cited, by whom, and when.', cta: 'Open the trust center', to: '/trust', points: [['▤ Immutable audit', 'Every governance event, exportable.'], ['🔗 Provenance graph', 'Source → signature → citation lineage.'], ['⊘ Revocation', 'Withdrawn facts are pulled from flows within SLA.']] },
};
function PUseCase({ who }) {
  const u = USECASES[who];
  if (!u) return <PNotFound />;
  const { OhTopBar } = window;
  return (
    <div className="pt-mkt pt-view">
      <OhTopBar brand={{ name: 'OpenHubForAI', realm: 'openharnesshub', tld: '.io', glyph: '⎔', accent: 'var(--accent)' }}
        nav={[['Governments', '/for/governments'], ['Builders', '/for/builders'], ['Lawyers', '/for/lawyers'], ['Regulators', '/for/regulators']]}
        cta={{ label: 'Start free', href: '/signup' }} signInHref="/signin" />
      <div className="pt-mkt-body">
        <section className="pt-hero">
          <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--accent)', marginBottom: 14 }}>{u.tag}</div>
          <h1>{u.hl}</h1>
          <p className="sub">{u.sub}</p>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="oh-btn oh-btn--primary" onClick={() => navigate(u.to)}>{u.cta} →</button>
            <button className="oh-btn oh-btn--ghost" onClick={() => navigate('/')}>Describe a task</button>
          </div>
          <div className="pt-grid-3" style={{ maxWidth: 820, width: '100%', marginTop: 40, textAlign: 'left' }}>
            {u.points.map(([t, d]) => (
              <div className="pt-panel" key={t}><div style={{ fontWeight: 700, color: 'var(--fg)', marginBottom: 5 }}>{t}</div><div style={{ fontSize: 13, color: 'var(--fg-muted)', lineHeight: 1.5 }}>{d}</div></div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
Object.assign(window, { PUseCase });
