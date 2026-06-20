/* global React, PRIMS */
// Color-scheme palette card — a compact identity swatch per direction.
// Wrapped in its scope (dir-* theme-*) by app.jsx, so it reads live tokens.

function PaletteCard({ name, audience, blurb, onPick }) {
  return (
    <div className="oh-pal">
      <div className="oh-pal-head">
        <div className="oh-pal-name">{name}</div>
        <div className="oh-pal-aud">{audience}</div>
      </div>
      <div className="oh-pal-blurb">{blurb}</div>

      <div>
        <div className="oh-pal-lbl">Surfaces</div>
        <div className="oh-pal-ramp">
          {['--bg', '--bg-subtle', '--panel', '--panel-2', '--line-strong'].map((v) => (
            <span className="sw" key={v} style={{ background: `var(${v})` }} />
          ))}
        </div>
      </div>

      <div>
        <div className="oh-pal-lbl">Accent · verified · lift · stop</div>
        <div className="oh-pal-accents">
          <span className="oh-pal-accent-lg">Primary action</span>
          <span className="oh-pal-sq" style={{ background: 'var(--verified)' }} title="verified">🛡</span>
          <span className="oh-pal-sq" style={{ background: 'var(--success)' }} title="lift">▲</span>
          <span className="oh-pal-sq" style={{ background: 'var(--danger)' }} title="stop">⊘</span>
        </div>
      </div>

      <div>
        <div className="oh-pal-lbl">Seven-primitive legend</div>
        <div className="oh-pal-prims">
          {Object.entries(PRIMS).map(([k, p]) => (
            <span className="oh-pal-prim" key={k} style={{ background: `var(${p.v})` }} title={p.label}>{p.glyph}</span>
          ))}
          <span className="oh-pal-prim op" title="Operator">◇</span>
        </div>
      </div>

      <div className="oh-pal-type">
        <div className="oh-pal-lbl">Type</div>
        <div className="disp">Describe a task.</div>
        <div className="body">Costed, deployable pipelines that beat a bare model.</div>
        <div className="mono">harness/esg-cite-first</div>
      </div>

      <div className="oh-pal-mini">
        <button className="oh-btn oh-btn--sm oh-btn--apply" onClick={onPick}>Apply to all pages →</button>
        <span className="oh-badge oh-badge--verified">✔ sourced</span>
      </div>
    </div>
  );
}

Object.assign(window, { PaletteCard });
