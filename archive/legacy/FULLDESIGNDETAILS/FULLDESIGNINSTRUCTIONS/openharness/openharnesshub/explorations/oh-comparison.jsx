/* global React */
// Comparison & recommendation — scored against the §2 rubric (13 principles).
// Scores are my design judgment for the compliance/regulated buyer and the
// paste-a-task sacred interaction.

const RUBRIC = [
  ['One sacred interaction', 'entry box → costed flow is the brightest move', 5, 5, 5],
  ['Restraint + one accent', 'colour carries meaning, not mood', 5, 5, 4],
  ['Typographic confidence', 'display + UI grotesk + mono, true scale', 5, 4, 4],
  ['Trust-coding matches buyer', 'reads as governed / human-in-the-loop', 5, 3, 4],
  ['A real spatial system', '4/8 grid, hairlines over shadows', 4, 5, 4],
  ['Motion with meaning', 'stage-by-stage flow assembly', 4, 4, 4],
  ['Every state designed', 'empty · loading · blocked · error', 4, 4, 4],
  ['Accessibility (AA, not colour-alone)', 'glyph + label on every primitive', 4, 4, 4],
  ['Theme parity (light ↔ dark)', 'legend reads identically in both', 4, 5, 3],
  ['Tokens + components = source', 'one card, one badge, reused', 5, 5, 5],
  ['Show the substance', 'lift · provenance · cost on every surface', 5, 4, 5],
  ['Power-tool craft cues', '⌘K, copy-id, optimistic UI', 4, 5, 4],
  ['The distinctiveness test', 'survives a screenshot next to the best', 5, 3, 4],
];

function ScoreCell({ n, win }) {
  return (
    <td className={'sc' + (win ? ' oh-col-win' : '')}>
      <span className="oh-sccell">
        {n}
        <span className="oh-scdots">
          {[1, 2, 3, 4, 5].map((i) => <span key={i} className={'oh-scdot' + (i <= n ? ' on' : '')} />)}
        </span>
      </span>
    </td>
  );
}

function Comparison() {
  const totals = RUBRIC.reduce((t, r) => [t[0] + r[2], t[1] + r[3], t[2] + r[4]], [0, 0, 0]);
  return (
    <div className="oh-cmp">
      <div>
        <h2>Comparison &amp; recommendation</h2>
        <div className="sub">Each direction scored 1–5 against the thirteen best-practice principles · winner column tinted</div>
      </div>

      <div className="oh-cmp-body">
        <table className="oh-rubric">
          <thead>
            <tr>
              <th>Principle</th>
              <th style={{ textAlign: 'center' }}>A · Editorial</th>
              <th style={{ textAlign: 'center' }}>B · Mono</th>
              <th style={{ textAlign: 'center' }}>D · Teal</th>
            </tr>
          </thead>
          <tbody>
            {RUBRIC.map((r) => (
              <tr key={r[0]}>
                <td className="pr">{r[0]}<small>{r[1]}</small></td>
                <ScoreCell n={r[2]} win />
                <ScoreCell n={r[3]} />
                <ScoreCell n={r[4]} />
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td>Total / 65</td>
              <td className="sc oh-col-win">{totals[0]}</td>
              <td className="sc">{totals[1]}</td>
              <td className="sc">{totals[2]}</td>
            </tr>
          </tfoot>
        </table>

        <div className="oh-cmp-aside">
          <div className="oh-pick">
            <span className="tag">★ Recommended</span>
            <h3>A · Warm Editorial “Paper”</h3>
            <p>The wedge buyer is compliance / risk / audit — they reward proof and considered restraint over frontier flash. Warm editorial reads as <em>governed and human-in-the-loop</em>, the serif display lends credibility, and the clay accent evolves the shipped orange so brand continuity survives while the generic dev-dark look is shed. It is the direction most likely to survive a screenshot beside Anthropic and Stripe.</p>
          </div>

          <div className="oh-note">
            <h4>Graft from the runners-up</h4>
            <ul>
              <li>From <b>D</b>: teal as the dedicated <span className="mono">--verified</span> governance colour, and the entry box scaled as the absolute hero.</li>
              <li>From <b>B</b>: heavy-mono IDs/costs, the ⌘K command palette, and strict near-monochrome restraint on dense data screens.</li>
            </ul>
          </div>

          <div className="oh-note">
            <h4>Risks &amp; mitigations</h4>
            <ul>
              <li className="risk"><b>Reads soft on data screens</b> → ship the warm-charcoal dark theme for builder / catalog / trace; keep marketing light.</li>
              <li className="risk"><b>Serif overuse</b> → confine the serif to display ≥ 24px; Inter for all UI.</li>
              <li className="risk"><b>Clay low-contrast small</b> → accent for fills &amp; large type only; body links use <span className="mono">--fg</span>.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { Comparison });
