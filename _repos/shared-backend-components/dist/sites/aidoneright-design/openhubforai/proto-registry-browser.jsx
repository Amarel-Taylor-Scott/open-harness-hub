/* global React, OPENHUBFORAI_BRAND, OhLayout, OhTable, OhPageHead */
// OpenHubForAI registry browser: browse every record in the family, many ways, with filters and search.
// Built on the shared kit (OhLayout variant="no-sidebar" + OhTable) over the REAL reconciled spine via the
// /registry/browse seam (scripts/registry_api_server.py -> src.teleon.registry.browse). serves_truth=false:
// a registry is a pointer plus a shape, not asserted truth; status is shown honestly (live / partial / gap).

const REG_BASE = (window.OPENHUBFORAI_REGISTRY_BASE || '/registry');
const OPENHUB_ACCENT = '#3b6fd4';
// the facet dimensions we surface as a rail (type is one-per-registry -> 242 distinct, not a useful rail facet)
const FACET_RAIL = [['category', 'Category'], ['status', 'Status'], ['kind', 'Kind'], ['layer', 'Layer']];

function qstr(obj) {
  return Object.entries(obj).filter(([, v]) => v)
    .map(([k, v]) => encodeURIComponent(k) + '=' + encodeURIComponent(v)).join('&');
}

function StatusBadge({ s }) {
  const c = { live: '#1a7f37', partial: '#9a6700', gap: '#cf222e' }[s] || 'var(--fg-muted)';
  return <span className="mono" style={{ color: c, fontWeight: 600, fontSize: 12 }}>● {s}</span>;
}

// the registry's own records (drilled in from the detail view), via /registry/registries/{id}/records
function RecordList({ id }) {
  const [recs, setRecs] = React.useState(null);
  const [err, setErr] = React.useState(false);
  React.useEffect(() => {
    let live = true;
    fetch(REG_BASE + '/api/openhubforai/registries/' + encodeURIComponent(id) + '/records')
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { if (live) setRecs(Array.isArray(d.records) ? d.records : []); })
      .catch(() => { if (live) { setErr(true); setRecs([]); } });
    return () => { live = false; };
  }, [id]);
  if (recs === null) return <div className="ohl-empty">Loading records…</div>;
  const cols = [
    { key: 'id', label: 'Record', sortable: true, render: (r) => <span className="mono">{r.id}</span> },
    { key: 'name', label: 'Name', sortable: true, render: (r) => r.name || r.id },
    { key: 'type', label: 'Type', sortable: true },
  ];
  return <OhTable cols={cols} rows={recs} rowKey={(r) => r.id} dense
    empty={err ? 'Could not load records for this registry.' : 'This registry projects no records yet.'} />;
}

function RecordDetail({ item, onBack }) {
  const meta = [
    ['Type', item.type], ['Status', <StatusBadge s={item.status} key="s" />], ['Kind', item.kind || '·'],
    ['Layer', item.layer], ['Source', item.source], ['Records', item.record_count],
    ['In ontology', item.in_ontology ? 'yes' : 'no'], ['Queryable', item.queryable ? 'yes' : 'no'],
    ['Backing', item.backing || '·'],
  ];
  return (
    <div className="ohb-detail">
      <button className="oh-btn oh-btn--ghost oh-btn--sm" onClick={onBack}>← Back to results</button>
      <div className="oh-card oh-card--pad" style={{ marginTop: 12 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
          <h2 className="mono" style={{ margin: 0 }}>{item.id}</h2>
          <StatusBadge s={item.status} />
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', margin: '10px 0' }}>
          {(item.categories || []).map((c) => <span className="oh-pill" key={c}>{c}</span>)}
        </div>
        <p style={{ color: 'var(--fg-muted)', margin: '6px 0 14px' }}>
          {item.holds || 'No description recorded for this registry. It is a pointer plus a shape; records come from population.'}
        </p>
        <div className="ohb-meta">
          {meta.map(([k, v]) => <div className="ohb-meta-row" key={k}><span className="ohb-meta-k">{k}</span><span className="ohb-meta-v">{v}</span></div>)}
        </div>
      </div>
      <h3 style={{ margin: '20px 0 8px' }}>Records</h3>
      <RecordList id={item.id} />
    </div>
  );
}

function FacetRail({ facets, filters, onPick }) {
  const [showAllCat, setShowAllCat] = React.useState(false);
  if (!facets) return null;
  return (
    <aside className="ohb-rail">
      {FACET_RAIL.map(([dim, label]) => {
        const counts = facets[dim] || {};
        let entries = Object.entries(counts);
        const capped = dim === 'category' && !showAllCat && entries.length > 12;
        if (capped) entries = entries.slice(0, 12);
        return (
          <div className="ohb-facet" key={dim}>
            <div className="ohb-facet-h">{label}</div>
            {entries.map(([val, n]) => {
              const on = filters[dim] === val;
              return (
                <button key={val} className={'ohb-facet-v' + (on ? ' on' : '')} onClick={() => onPick(dim, on ? '' : val)}>
                  <span className="ohb-facet-val">{val}</span><span className="ohb-facet-n mono">{n}</span>
                </button>
              );
            })}
            {dim === 'category' && Object.keys(counts).length > 12 && (
              <button className="ohb-facet-more" onClick={() => setShowAllCat((v) => !v)}>
                {showAllCat ? 'Show fewer' : 'Show all ' + Object.keys(counts).length}
              </button>
            )}
          </div>
        );
      })}
    </aside>
  );
}

function CardGrid({ items, onOpen }) {
  if (!items.length) return <div className="ohl-empty">No registries match these filters.</div>;
  return (
    <div className="ohb-cards">
      {items.map((it) => (
        <button className="oh-card oh-card--pad ohb-card" key={it.id} onClick={() => onOpen(it)}>
          <div className="ohb-card-h"><span className="mono ohb-card-id">{it.id}</span><StatusBadge s={it.status} /></div>
          <div className="ohb-card-cats">{(it.categories || []).map((c) => <span className="oh-pill oh-pill--sm" key={c}>{c}</span>)}</div>
          <div className="ohb-card-holds">{it.holds || (it.layer !== 'uncategorized' ? (it.layer + ' registry') : it.type)}</div>
        </button>
      ))}
    </div>
  );
}

function PRegistryBrowser() {
  const [raw, setRaw] = React.useState('');          // search box text
  const [q, setQ] = React.useState('');              // debounced query actually sent
  const [filters, setFilters] = React.useState({});  // {category, kind, layer, status} single-value per dim
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [err, setErr] = React.useState(false);
  const [view, setView] = React.useState('table');   // 'table' | 'cards'
  const [selected, setSelected] = React.useState(null);

  React.useEffect(() => { const t = setTimeout(() => setQ(raw.trim()), 250); return () => clearTimeout(t); }, [raw]);

  React.useEffect(() => {
    let live = true; setLoading(true); setErr(false);
    const query = qstr({ q, ...filters });
    fetch(REG_BASE + '/api/openhubforai/registries' + (query ? '?' + query : ''))
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { if (live) { setData(d); setLoading(false); } })
      .catch(() => { if (live) { setErr(true); setLoading(false); } });
    return () => { live = false; };
  }, [q, filters]);

  const pick = (dim, val) => { setSelected(null); setFilters((f) => { const n = { ...f }; if (val) n[dim] = val; else delete n[dim]; return n; }); };
  const clearAll = () => { setFilters({}); setRaw(''); setQ(''); };
  const activeChips = Object.entries(filters);

  const items = (data && data.items) || [];
  const cols = [
    { key: 'id', label: 'Registry', sortable: true, render: (r) => <span className="mono">{r.id}</span> },
    { key: 'type', label: 'Type', sortable: true },
    { key: 'status', label: 'Status', sortable: true, render: (r) => <StatusBadge s={r.status} /> },
    { key: 'kind', label: 'Kind', sortable: true, sortValue: (r) => r.kind || '', render: (r) => r.kind || '·' },
    { key: 'layer', label: 'Layer', sortable: true },
    { key: 'categories', label: 'Categories', sortValue: (r) => (r.categories || []).join(','), render: (r) => (r.categories || []).join(', ') },
    { key: 'record_count', label: 'Records', align: 'right', sortable: true, sortValue: (r) => r.record_count || 0 },
  ];

  const nav = [['Explore', '/components'], ['Pipelines', '/pipelines'], ['Registries', '/registries'], ['Pricing', '/pricing']];
  const footerProps = {
    tagline: 'The open store both products consume. Part of AI Done Right.',
    cols: [
      ['Browse', [['All registries', '/registries'], ['Components', '/components'], ['Pipelines', '/pipelines']]],
      ['Build', [['Start a build', '/build'], ['Pricing', '/pricing'], ['Trust', '/trust']]],
    ],
  };

  return (
    <div className="oh-site ohb" style={{ '--accent': OPENHUB_ACCENT }}>
      <OhLayout variant="no-sidebar" brand={OPENHUBFORAI_BRAND} nav={nav}
        cta={{ label: 'Open the app', href: '/app' }} signInHref="/signin" footerProps={footerProps}>
        <OhPageHead eyebrow="OpenHubForAI" title="Browse the registries"
          sub="Every registry in the family, faceted by category, status, kind, and layer. Search by id or description, sort any column, and open a registry to see its records. A registry is a pointer plus a shape, not asserted truth." />

        <div className="ohb-toolbar">
          <input className="ohb-search" value={raw} onChange={(e) => setRaw(e.target.value)}
            placeholder="Search registries by id or description…" />
          <div className="ohb-count mono">{loading ? 'loading…' : err ? 'service offline' : (data ? data.count + ' registries' : '')}</div>
          <div className="ohb-views">
            <button className={'ohb-view' + (view === 'table' ? ' on' : '')} onClick={() => setView('table')}>Table</button>
            <button className={'ohb-view' + (view === 'cards' ? ' on' : '')} onClick={() => setView('cards')}>Cards</button>
          </div>
        </div>

        {(activeChips.length > 0 || q) && (
          <div className="ohb-chips">
            {q && <span className="ohb-chip">search: {q}<button onClick={() => { setRaw(''); setQ(''); }}>×</button></span>}
            {activeChips.map(([k, v]) => <span className="ohb-chip" key={k}>{k}: {v}<button onClick={() => pick(k, '')}>×</button></span>)}
            <button className="ohb-clear" onClick={clearAll}>Clear all</button>
          </div>
        )}

        <div className="ohb-grid">
          <FacetRail facets={data && data.facets} filters={filters} onPick={pick} />
          <div className="ohb-main">
            {err
              ? <div className="ohl-empty">The registry service is not reachable. Start it with: python3 scripts/registry_api_server.py</div>
              : selected
                ? <RecordDetail item={selected} onBack={() => setSelected(null)} />
                : loading
                  ? <div className="ohl-empty">Loading registries…</div>
                  : view === 'table'
                    ? <OhTable cols={cols} rows={items} rowKey={(r) => r.id} onRow={(r) => setSelected(r)}
                        empty="No registries match these filters." />
                    : <CardGrid items={items} onOpen={setSelected} />}
          </div>
        </div>
      </OhLayout>
    </div>
  );
}

window.PRegistryBrowser = PRegistryBrowser;
