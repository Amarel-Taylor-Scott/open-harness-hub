/* OpenHubForAI — side-by-side demo (/compare): bare model vs governed pipeline.
   Makes the value prop visceral on clinical (Duecare-themed, SYNTHETIC) examples: the bare model
   is fluent but uncited and over-confident; the governed pipeline cites every claim, fires
   deterministic red-flag gates, and abstains when the corpus doesn't support an answer.
   No React/JSX/build. Registers /compare (marketing, light). */
(function () {
  "use strict";
  var MARK_SVG = '<span class="oh-mark" aria-hidden="true"><svg width="18" height="18" viewBox="0 0 18 18" fill="none">' +
    '<rect x="1" y="6" width="6" height="6" rx="1.4" fill="currentColor" /><path d="M9 9h3.5" stroke="currentColor" stroke-width="1.4" />' +
    '<rect x="11" y="3" width="6" height="6" rx="3" fill="none" stroke="currentColor" stroke-width="1.4" transform="rotate(45 14 6)" /></svg></span>';

  // Synthetic clinical examples (Duecare theme) — illustrative, NOT copied from _reference.
  var EXAMPLES = [
    {
      task: "Triage a patient note: 58M, crushing chest pain radiating to left arm, diaphoretic, 2h. Differential + red flags?",
      bare: {
        answer: "Likely musculoskeletal strain or GERD; reassure and advise OTC antacids and rest. Could also be anxiety.",
        flaws: ["No citation to any guideline", "MISSES the ACS red-flag pattern (radiation + diaphoresis)", "Reassures instead of escalating — a safety harm", "No abstention / no escalation path"]
      },
      governed: {
        answer: "ACS until proven otherwise — RED FLAG. Differential: STEMI/NSTEMI, unstable angina, aortic dissection, PE. Action: immediate ECG + troponin, do NOT reassure; escalate now.",
        cites: ["ACC/AHA chest-pain guideline §3.2 (radiation + diaphoresis = high-risk)", "rule-pack/clinical-redflag-screen → ACS pattern fired"],
        gates: ["Red-flag gate fired → escalate to clinician", "Cite-or-abstain: every claim sourced", "No reassurance permitted on a fired red-flag"]
      },
      delta: { lift: "+0.46", cited: "100% vs 0%", safety: "red-flag caught (bare missed it)", cost: "$$ · mostly freezable" }
    },
    {
      task: "Reconcile a discharge med list: warfarin 5mg + new fluconazole 150mg. Any interaction?",
      bare: {
        answer: "These are generally fine to take together; monitor as usual.",
        flaws: ["WRONG — fluconazole potentiates warfarin (major interaction)", "No source", "No severity, no action"]
      },
      governed: {
        answer: "MAJOR interaction: fluconazole inhibits CYP2C9 → ↑ warfarin effect → bleeding risk. Action: reduce warfarin dose, increase INR monitoring; flag prescriber.",
        cites: ["Interaction corpus: warfarin × azole-antifungals (CYP2C9), severity=major", "processor/drug-interaction-checker → match"],
        gates: ["Deterministic interaction lookup (no model guess)", "Severity-tiered → prescriber flag", "Cite-or-abstain"]
      },
      delta: { lift: "+0.52", cited: "100% vs 0%", safety: "major interaction caught (bare said 'fine')", cost: "$ · deterministic lookup" }
    },
    {
      task: "Structure a dictated encounter into a SOAP note with coded diagnoses.",
      bare: {
        answer: "Plausible SOAP note with ICD-10 codes inferred from context (e.g. assigns J45.909, I10…).",
        flaws: ["Codes are GUESSED — hallucination risk on ICD-10", "No link from code to documented evidence", "No abstention on undocumented diagnoses"]
      },
      governed: {
        answer: "SOAP note where every coded diagnosis is gated on a terminology corpus and linked to the documented evidence span; undocumented diagnoses are left uncoded (abstain).",
        cites: ["ICD-10-CM terminology corpus (exact-id grounding)", "processor/icd10-code-grounder → each code resolved or abstained"],
        gates: ["Codes grounded on a corpus (no free-text ICD)", "Evidence-span link per code", "Abstain when undocumented"]
      },
      delta: { lift: "+0.38", cited: "100% vs 0%", safety: "no fabricated codes", cost: "$$ · grounding freezable" }
    }
  ];

  function flawList(items, cls, glyph) {
    return items.map(function (x) {
      return '<li style="display:flex;gap:8px;align-items:flex-start;padding:5px 0;font-size:12.5px;color:var(--fg-muted);line-height:1.45">' +
        '<span style="color:var(' + cls + ');flex:0 0 auto">' + glyph + "</span><span>" + ctx_esc(x) + "</span></li>";
    }).join("");
  }
  var ctx_esc; // set per render

  function panel(side, ex) {
    var bare = side === "bare";
    var head = bare
      ? '<span class="oh-badge oh-badge--danger"><span class="gl">⚠</span> Bare model · no harness</span>'
      : '<span class="oh-badge oh-badge--verified"><span class="gl">✔</span> OpenHubForAI pipeline</span>';
    var body = bare ? ex.bare : ex.governed;
    var detail = bare
      ? '<div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--danger);margin:12px 0 4px">Failure modes</div><ul style="margin:0;padding:0;list-style:none">' + flawList(ex.bare.flaws, "--danger", "✗") + "</ul>"
      : '<div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--verified);margin:12px 0 4px">Cited to</div><ul style="margin:0;padding:0;list-style:none">' + flawList(ex.governed.cites, "--verified", "⛁") + "</ul>" +
        '<div style="font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--accent);margin:12px 0 4px">Gates</div><ul style="margin:0;padding:0;list-style:none">' + flawList(ex.governed.gates, "--accent", "◈") + "</ul>";
    return '<div class="pt-panel" style="flex:1;min-width:0;border-color:' + (bare ? "color-mix(in srgb, var(--danger) 35%, var(--line))" : "color-mix(in srgb, var(--verified) 40%, var(--line))") + '">' +
      head +
      '<div style="font-size:13.5px;color:var(--fg);line-height:1.5;margin-top:12px">' + ctx_esc(body.answer) + "</div>" +
      detail + "</div>";
  }

  function render(ctx) {
    ctx_esc = ctx.esc;
    var sel = (ctx.params && ctx.params.n != null) ? (parseInt(ctx.params.n, 10) || 0) : 0;
    var ex = EXAMPLES[sel] || EXAMPLES[0];
    var tabs = EXAMPLES.map(function (e, i) {
      return '<button class="pt-chip' + (i === sel ? " on" : "") + '" data-cmp="' + i + '" style="' + (i === sel ? "border-color:var(--accent);color:var(--accent)" : "") + '">' +
        ctx.esc(e.task.length > 46 ? e.task.slice(0, 44) + "…" : e.task) + "</button>";
    }).join("");
    var d = ex.delta;
    var deltaCards = [
      ["▲ " + d.lift, "capability lift vs the bare model", "--success"],
      [d.cited, "claims cited (pipeline vs bare)", "--verified"],
      [d.safety, "safety", "--accent"],
      [d.cost, "cost", "--fg-muted"]
    ].map(function (c) {
      return '<div class="pt-panel" style="flex:1;min-width:140px;text-align:center;padding:14px 12px">' +
        '<div style="font-family:var(--font-display);font-size:18px;font-weight:700;color:var(' + c[2] + ')">' + ctx.esc(c[0]) + "</div>" +
        '<div style="font-size:11px;color:var(--fg-muted);margin-top:3px;text-transform:uppercase;letter-spacing:.05em">' + ctx.esc(c[1]) + "</div></div>";
    }).join("");

    return '<div class="pt-mkt pt-view">' +
      '<header class="pt-mkt-top"><div class="oh-wordmark" style="cursor:pointer" data-nav="/">' + MARK_SVG + " OpenHubForAI</div>" +
      "<nav><a data-nav=\"/pipelines\">Explore</a><a data-nav=\"/compare\" style=\"color:var(--fg);font-weight:600\">Compare</a><a data-nav=\"/pricing\">Pricing</a><a data-nav=\"/docs\">Docs</a></nav>" +
      '<span class="pt-spacer"></span><button class="oh-btn oh-btn--ghost oh-btn--sm" data-nav="/signin">Sign in</button></header>' +
      '<div class="pt-mkt-body"><div class="pt-page" style="max-width:1000px;margin:0 auto">' +
      '<div class="pt-page-head"><div style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:10px">See the lift</div>' +
      "<h1>Same model. The harness is the difference.</h1>" +
      '<div class="sub">A bare frontier model vs the same model inside a governed OpenHubForAI pipeline, on real clinical decisions. The model is fixed — only the harness changes.</div></div>' +
      '<div class="pt-chips" style="justify-content:flex-start;margin:0 0 18px">' + tabs + "</div>" +
      '<div class="oh-cc-id mono" style="margin-bottom:8px">task · ' + ctx.esc(ex.task) + "</div>" +
      '<div style="display:flex;gap:16px;flex-wrap:wrap;align-items:stretch">' + panel("bare", ex) + panel("governed", ex) + "</div>" +
      '<div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:18px">' + deltaCards + "</div>" +
      '<div class="oh-state-msg" style="margin-top:18px;background:var(--accent-weak);border:1px solid color-mix(in srgb, var(--accent) 30%, var(--line));border-radius:var(--r-md);padding:15px 16px;display:flex;gap:10px;align-items:center;flex-wrap:wrap">' +
      '<div style="flex:1;min-width:240px;font-size:13px;color:var(--fg-muted)">Lift is measured at the pipeline level (paired with-vs-without the harness). Most of the harness — the gates, retrieval, citation checks — is deterministic and freezable, so it adds capability without adding recurring cost.</div>' +
      '<button class="oh-btn oh-btn--primary" data-nav="/">Build your own →</button>' +
      '<button class="oh-btn oh-btn--ghost" data-nav="/improve">Improve a pipeline you have</button></div>' +
      '<div style="font-size:11px;color:var(--fg-faint);margin-top:14px;font-family:var(--font-mono)">Examples are synthetic clinical illustrations (Duecare-themed). Deltas are illustrative of the with-vs-without pattern, not a benchmark claim.</div>' +
      "</div></div></div>";
  }

  function onMount(host, ctx) {
    Array.prototype.forEach.call(host.querySelectorAll("[data-cmp]"), function (b) {
      b.addEventListener("click", function () { ctx.navigate("/compare/" + b.getAttribute("data-cmp")); });
    });
  }

  OpenHubForAI.register("/compare", render, onMount, { theme: "light" });
  OpenHubForAI.register("/compare/:n", render, onMount, { theme: "light" });
})();
