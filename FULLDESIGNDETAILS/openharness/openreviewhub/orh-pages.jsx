/* global React */
// openreviewhub/orh-pages.jsx — the review-report surface for OpenReviewHub.io.
// Rendered through the shared hub's generic entryExtra hook, so the site stays
// branded-house: it composes the same .oh-* primitives + tokens, and just adds the
// review-specific substance the generic registry can't know — the artifact under
// review, an axis scorecard (capability · verifiability · reproducibility ·
// robustness), and a claim → evidence → verdict ledger. Discovery is not trust.

// ---------------------------------------------------------------------------
// Per-review substance: the real artifact each review scrutinises and what the
// reviewer actually found — claims mapped to evidence and a reproduced verdict.
// ---------------------------------------------------------------------------
const ORH_DATA = {
  'cov-claims': {
    target: ['Paper', 'arXiv:2406.xxxxx · "Chain-of-Verification"', 'a released-prompts reproduction'],
    verdict: ['Partially reproduced', 'partial'],
    axes: [['Capability', 78, 'Gains real on 2 of 3 reported tasks'], ['Verifiability', 90, 'Prompts + seeds released'], ['Reproducibility', 64, 'One table did not reproduce on the released prompts'], ['Robustness', 71, 'Sensitive to prompt phrasing']],
    claims: [
      ['+12% on factual QA over baseline', 'Re-ran released prompts, 5 seeds — observed +9.4%', 'partial'],
      ['Holds across model sizes', 'Confirmed on 7B and 13B from the repo', 'reproduced'],
      ['No extra inference cost', 'Verification pass adds ~1.7× calls — claim is wrong', 'failed'],
    ],
    method: 'Re-ran the authors’ released prompts at 5 seeds on the two model checkpoints they cite; compared against the paper’s reported deltas.',
    notTested: 'Closed-model results (no API access in the released harness) and the human-eval subset.',
  },
  'agent-runtime-repo': {
    target: ['Repo', 'github.com/example/agent-runtime @ a3f19c2', 'a clean-build + quickstart run'],
    verdict: ['Reproduced', 'reproduced'],
    axes: [['Capability', 88, 'Quickstart demo works end-to-end'], ['Verifiability', 82, 'Pinned deps, lockfile present'], ['Reproducibility', 94, 'Clean clone built first try'], ['Robustness', 70, 'Flaky on the streaming example']],
    claims: [
      ['Builds clean from a fresh clone', 'Fresh container, `make build` — green', 'reproduced'],
      ['Quickstart works in <5 min', 'Followed README verbatim — 4m12s to first run', 'reproduced'],
      ['100% test coverage', 'Coverage report shows 81%, not 100%', 'failed'],
    ],
    method: 'Fresh container, pinned to the documented toolchain. Ran the README quickstart verbatim and the project’s own test + coverage targets.',
    notTested: 'The optional GPU path (no device available) and the cloud-deploy guide.',
  },
  'ow-7b-card': {
    target: ['Model', 'open-weights-7b · capability card v2', 'an eval re-run on released weights'],
    verdict: ['Partially reproduced', 'partial'],
    axes: [['Capability', 80, 'Most evals within ±1.5 pts'], ['Verifiability', 86, 'Weights + eval configs public'], ['Reproducibility', 68, 'Two scores drift beyond noise'], ['Robustness', 74, 'Decoding params matter a lot']],
    claims: [
      ['MMLU 64.2', 'lm-eval-harness, same config — 63.8 (within noise)', 'reproduced'],
      ['GSM8K 52.1', 'Re-ran — 47.3; gap traced to decoding temperature', 'partial'],
      ['No benchmark contamination', 'Decontamination script reproduces the authors’ report', 'reproduced'],
    ],
    method: 'Ran the published lm-evaluation-harness configs on the released weights; investigated any score that drifted beyond run-to-run noise.',
    notTested: 'Long-context evals above 8k (card does not specify a config) and multilingual splits.',
  },
  'web-research-agent': {
    target: ['Agent', 'web-research-agent v1.3 · task suite', 'a sandboxed end-to-end run'],
    verdict: ['Reproduced', 'reproduced'],
    axes: [['Capability', 84, 'Completes 17/20 sandbox tasks'], ['Verifiability', 79, 'Traces + tool calls logged'], ['Reproducibility', 81, 'Stable across 3 sandbox runs'], ['Robustness', 66, 'Degrades on paywalled sources']],
    claims: [
      ['Completes the 20-task research suite', 'Sandboxed run — 17/20 passed, traces attached', 'partial'],
      ['Stays within declared tool scopes', 'No out-of-scope calls observed across runs', 'reproduced'],
      ['Cites every claim it returns', 'Spot-checked 40 claims — all carried a source', 'reproduced'],
    ],
    method: 'Ran the agent in an isolated sandbox against its own task suite, three times, capturing every tool call and the final cited output.',
    notTested: 'Live-web tasks behind authentication and the optional human-in-the-loop mode.',
  },
  'it-set-provenance': {
    target: ['Dataset', 'instruct-tune-set v4 · 1.2M rows', 'a provenance + contamination audit'],
    verdict: ['Concerns found', 'failed'],
    axes: [['Capability', 60, 'Useful but mislabelled in places'], ['Verifiability', 55, 'Source list incomplete'], ['Reproducibility', 72, 'Dedup script reproduces'], ['Robustness', 48, 'Licence mix unresolved']],
    claims: [
      ['All sources permissively licensed', '6% of rows trace to a non-commercial source', 'failed'],
      ['Deduplicated to <0.5% near-dupes', 'Re-ran MinHash — 0.4% near-dupes, confirmed', 'reproduced'],
      ['No eval-set contamination', 'Found 0.9% overlap with a common eval split', 'partial'],
    ],
    method: 'Re-ran the published dedup pipeline and a contamination scan against common eval sets; sampled 2,000 rows to verify licence provenance.',
    notTested: 'Manual quality grading of free-text rows and PII screening at full scale.',
  },
  'rag-reference': {
    target: ['Repo', 'github.com/example/rag-reference @ 8810de1', 'a metric reproduction'],
    verdict: ['Reproduced', 'reproduced'],
    axes: [['Capability', 86, 'Hits the reported retrieval metrics'], ['Verifiability', 88, 'Index + corpus snapshot pinned'], ['Reproducibility', 90, 'Reran eval to within 0.4 pts'], ['Robustness', 73, 'Sensitive to chunk size']],
    claims: [
      ['Recall@10 = 0.91 on the demo corpus', 'Rebuilt the index, re-ran eval — 0.908', 'reproduced'],
      ['Faithfulness > 0.85', 'Re-scored with the repo’s own judge — 0.86', 'reproduced'],
      ['Runs on a single 16GB GPU', 'OOM at the documented batch size; needed 24GB', 'failed'],
    ],
    method: 'Rebuilt the vector index from the pinned corpus snapshot and re-ran the repo’s evaluation script with its default configuration.',
    notTested: 'The streaming-ingest path and corpora larger than the bundled demo set.',
  },
};

function orhData(e) {
  return ORH_DATA[e.id] || {
    target: ['Artifact', e.name, 'a reproduction review'],
    verdict: ['Reviewed', 'partial'],
    axes: [['Capability', 80, ''], ['Verifiability', 80, ''], ['Reproducibility', 80, ''], ['Robustness', 75, '']],
    claims: [['Headline claim', 'Checked against released materials', 'partial']],
    method: 'Reviewed against the artifact’s released materials.',
    notTested: 'Components without released code or data.',
  };
}

const VERDICT_LABEL = { reproduced: 'reproduced', partial: 'partial', failed: 'failed', verified: 'verified' };

// ===========================================================================
// entryExtra — the review report on every entry-detail page
// ===========================================================================
function ORHReviewReport({ e }) {
  const d = orhData(e);
  const [kind, ref, sub] = d.target;
  const [vlabel, vtone] = d.verdict;
  return (
    <React.Fragment>
      {/* the artifact under review */}
      <div className="oh-card oh-card--pad orh-section">
        <span className="orh-eyebrow">Under review</span>
        <div className="orh-target">
          <div>
            <span className="orh-kind">{kind}</span>
            <div className="orh-target-ref mono">{ref}</div>
            <div className="orh-target-sub">{sub}</div>
          </div>
          <span className={'orh-verdict ' + vtone}>{vlabel}</span>
        </div>
      </div>

      {/* axis scorecard */}
      <div className="oh-card oh-card--pad orh-section">
        <span className="orh-eyebrow">Scorecard · review axes</span>
        <div className="orh-axes">
          {d.axes.map(([axis, pct, note]) => (
            <div className="orh-axis" key={axis}>
              <div className="orh-axis-head"><span className="orh-axis-name">{axis}</span><span className="orh-axis-pct mono">{pct}</span></div>
              <div className="orh-bar"><i style={{ width: pct + '%' }} /></div>
              {note && <div className="orh-axis-note">{note}</div>}
            </div>
          ))}
        </div>
      </div>

      {/* claims → evidence → verdict */}
      <div className="oh-card oh-card--pad orh-section">
        <span className="orh-eyebrow">Claims &amp; evidence</span>
        <table className="orh-claims">
          <thead><tr><th>Claim</th><th>Evidence</th><th>Verdict</th></tr></thead>
          <tbody>
            {d.claims.map(([c, ev, v], i) => (
              <tr key={i}>
                <td className="cl">{c}</td>
                <td className="ev">{ev}</td>
                <td><span className={'orh-vchip ' + v}>{VERDICT_LABEL[v] || v}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* method & scope */}
      <div className="oh-card oh-card--pad orh-section">
        <span className="orh-eyebrow">Method &amp; scope</span>
        <p className="orh-method">{d.method}</p>
        <div className="orh-scope"><span className="orh-scope-k">Not tested</span><span className="orh-scope-v">{d.notTested}</span></div>
      </div>
    </React.Fragment>
  );
}

Object.assign(window, { ORHReviewReport });
