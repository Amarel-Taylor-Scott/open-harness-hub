/* global React, StoreCtx, navigate */
// SDG Solutions — each goal opens a GALLERY OF PIPELINES (not components).

const SDG = [
  [1, '#E5243B', 'No Poverty', 'Living-wage & social-protection compliance'],
  [2, '#DDA63A', 'Zero Hunger', 'Food-supply provenance, safety & nutrition'],
  [3, '#4C9F38', 'Good Health & Well-being', 'GxP & clinical-claim compliance'],
  [4, '#C5192D', 'Quality Education', 'Training-content quality & accessibility'],
  [5, '#FF3A21', 'Gender Equality', 'Pay-equity & diversity disclosures'],
  [6, '#26BDE2', 'Clean Water & Sanitation', 'Water stewardship & discharge permits'],
  [7, '#FCC30B', 'Affordable & Clean Energy', 'Renewable-energy & PPA claims'],
  [8, '#A21942', 'Decent Work & Growth', 'Labour rights & modern-slavery risk'],
  [9, '#FD6925', 'Industry & Infrastructure', 'Supply-chain resilience & R&D claims'],
  [10, '#DD1367', 'Reduced Inequalities', 'Non-discrimination & inclusion'],
  [11, '#FD9D24', 'Sustainable Cities', 'Urban resilience & housing reports'],
  [12, '#BF8B2E', 'Responsible Consumption', 'Circularity, packaging & waste'],
  [13, '#3F7E44', 'Climate Action', 'Scope 1–3 emissions & transition risk'],
  [14, '#0A97D9', 'Life Below Water', 'Seafood sourcing & IUU-fishing risk'],
  [15, '#56C02B', 'Life on Land', 'Deforestation (EUDR) & biodiversity'],
  [16, '#00689D', 'Peace & Justice', 'Sanctions, AML & anti-corruption'],
  [17, '#19486A', 'Partnerships', 'Cross-standard ESG disclosure'],
];
const SDG_BY_N = Object.fromEntries(SDG.map((s) => [s[0], s]));

// 3 hyper-specific pipelines per goal: [name, input, output]
const PIPES = {
  1: [['Living-wage gap screen', 'payroll + locale', 'wage-gap report w/ remediation'], ['Social-protection coverage audit', 'workforce roster', 'coverage gaps by country'], ['In-work poverty flag', 'contract terms', 'at-risk worker list']],
  2: [['Food-safety provenance trace', 'lot / batch IDs', 'provenance + recall exposure'], ['Nutrition-claim validator', 'product labels', 'substantiation + violations'], ['Smallholder sourcing audit', 'supplier list', 'smallholder share + fairness']],
  3: [['GxP deviation triage', 'batch records', 'severity + CAPA'], ['Clinical-claim citation check', 'marketing copy', 'cited vs uncited claims'], ['Adverse-event signal scan', 'case narratives', 'signal summary']],
  4: [['Course accessibility audit', 'course content', 'WCAG gaps + fixes'], ['Learning-outcome alignment', 'syllabus', 'outcome coverage map'], ['Credential-fraud check', 'certificates', 'verification report']],
  5: [['Pay-equity gap analysis', 'comp data', 'adjusted gap + drivers'], ['Board-diversity disclosure', 'governance docs', 'disclosure-ready table'], ['Harassment-policy coverage', 'HR policies', 'gap list vs standard']],
  6: [['Discharge-permit compliance', 'effluent data', 'exceedances + permit map'], ['Water-stewardship score', 'site water data', 'stewardship rating'], ['Basin water-stress exposure', 'site locations', 'stress index by basin']],
  7: [['Renewable / PPA claim verify', 'energy contracts', 'verified % renewable'], ['Scope-2 market vs location', 'utility bills', 'dual-reporting table'], ['Energy-attribute cert trace', 'REC IDs', 'provenance + double-count check']],
  8: [['Human-trafficking indicator scan', 'recruitment ads (HK→PH)', 'exploitation indicators + risk'], ['Working-hours / OT compliance', 'time records', 'violations by site'], ['Grievance-mechanism audit', 'grievance logs', 'coverage + response SLA']],
  9: [['Supply-chain resilience map', 'BOM + suppliers', 'single-point-of-failure map'], ['R&D-claim substantiation', 'patent claims', 'cited evidence'], ['Critical-infra dependency', 'asset list', 'dependency risk']],
  10: [['Non-discrimination disclosure', 'HR + policy', 'disclosure pack'], ['Inclusion-metric audit', 'workforce data', 'representation gaps'], ['Accessible-product check', 'product specs', 'accessibility gaps']],
  11: [['311 triage & routing', '311 report stream', 'department + urgency routing'], ['Building-code compliance', 'permits', 'violation list'], ['Urban-resilience exposure', 'asset geolocation', 'hazard exposure']],
  12: [['Circularity / recyclability', 'packaging specs', 'recyclability + EPR fees'], ['Waste-claim verification', 'waste data', 'verified diversion %'], ['Product-LCA hotspot', 'BOM', 'impact hotspots']],
  13: [['Scope 1–3 emissions calc', 'activity data', 'GHG inventory w/ cited factors'], ['Transition-plan gap (TCFD/ISSB)', 'strategy docs', 'gap list'], ['Physical-climate risk', 'asset locations', 'hazard exposure by scenario']],
  14: [['Seafood IUU-fishing risk', 'catch certificates', 'IUU risk + traceability'], ['Marine-discharge (MARPOL)', 'vessel logs', 'exceedances'], ['Sustainable-sourcing (MSC)', 'product list', 'certification coverage']],
  15: [['EUDR deforestation geo-check', 'plot geolocation', 'deforestation-free proof'], ['Biodiversity impact screen', 'site footprint', 'protected-area overlap'], ['Land-rights / FPIC audit', 'land acquisitions', 'FPIC compliance']],
  16: [['OFAC / SDN sanctions screen', 'counterparty list', 'matches + dispositions'], ['Anti-corruption UBO check', 'entity records', 'UBO + red flags'], ['Whistleblower-policy audit', 'policies', 'gap vs EU Directive']],
  17: [['Cross-standard ESG pack', 'raw metrics', 'GRI / ESRS / ISSB mapped pack'], ['Data-sharing agreement check', 'contracts', 'compliance + risk'], ['Multi-framework crosswalk', 'one disclosure', 'mapped to N frameworks']],
};

function PSolutions() {
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-page-head"><h1>SDG solutions</h1><div className="sub">Pick a goal to browse its prebuilt, governed pipelines — hyper-specific to the work, not generic.</div></div>
      <div className="pt-sdg-grid">
        {SDG.map(([n, c, title, task]) => (
          <button key={n} className="pt-sdg-card" style={{ ['--sdg']: c }} onClick={() => navigate('/solutions/' + n)}>
            <span className="wheel">◎</span>
            <span className="num">{n < 10 ? '0' + n : n}</span>
            <span className="ttl">{title}</span>
            <span className="task">{task}</span>
            <span className="go">{(PIPES[n] || []).length} pipelines →</span>
          </button>
        ))}
      </div>
      <div className="pt-sdg-pay">
        <span className="gl">🛡</span>
        <span><b>Free to browse; subscription to run.</b> The pipeline shapes &amp; spec are open — running them on <b>governed, live, cited</b> data is the paid product.</span>
      </div>
    </div>
  );
}

function PSolution({ n }) {
  const { toast } = React.useContext(StoreCtx);
  const s = SDG_BY_N[Number(n)];
  if (!s) return <div className="pt-page pt-view"><div className="pt-page-head"><h1>Unknown goal</h1></div><button className="oh-btn oh-btn--ghost" onClick={() => navigate('/solutions')}>← All SDG solutions</button></div>;
  const [num, c, title, task] = s;
  const pipes = PIPES[num] || [];
  return (
    <div className="pt-page wide pt-view">
      <div className="pt-crumb" style={{ marginBottom: 14 }}><a style={{ cursor: 'pointer' }} onClick={() => navigate('/solutions')}>SDG solutions</a><span className="sep">/</span><b>Goal {num}</b></div>
      <div className="pt-sdg-band" style={{ ['--sdg']: c }}>
        <span className="bignum">{num < 10 ? '0' + num : num}</span>
        <div><div className="bt">{title}</div><div className="bd">{task} · {pipes.length} prebuilt pipelines, each with a QA / evaluation stage.</div></div>
        <span className="bgwheel">◎</span>
      </div>
      <div className="pt-cards-grid">
        {pipes.map(([name, inp, outp]) => (
          <div key={name} className="pt-pipe" style={{ ['--sdg']: c }} onClick={() => navigate('/flow')}>
            <div className="pn">{name}</div>
            <div className="pio"><span className="in">⌖ {inp}</span><span className="ar">→</span><span className="out">⎘ {outp}</span></div>
            <div className="pf"><span className="go">Open pipeline →</span></div>
          </div>
        ))}
      </div>
      <div className="pt-sdg-pay"><span className="gl">🛡</span><span>Preview free. <b>Run &amp; deploy on a subscription</b> — with live, cited data that stays fresh as the standards for SDG {num} evolve.</span></div>
    </div>
  );
}

Object.assign(window, { PSolutions, PSolution });
