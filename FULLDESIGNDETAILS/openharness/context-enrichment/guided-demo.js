/* guided-demo.js — shared engine + scenario library for Baltor data-example demos.
   A page sets <body data-scenario="cfpb"> (or sanctions / eudr / refund) and includes
   this script + guided-demo.css. The engine renders the whole demo from SCENARIOS[key]
   and wires the interactive 7-stage run. Governed context: the model never decides truth;
   the contradiction is held out, never served; receipts + source handles are preserved. */
(function () {
  // every scenario shares the 7-stage spine; only headlines/chips/evidence differ
  const STAGE_NAMES = [
    ['00', 'Source Systems'],
    ['01', 'Reconciliation'],
    ['02', 'Hardening'],
    ['03', 'Enhancement'],
    ['04', 'Optimization'],
    ['05', 'Consumption'],
    ['06', 'Verification Rail'],
  ];

  const SCENARIOS = {
    cfpb: {
      domain: 'Reg E · error-resolution deadline', runLabel: 'Integrate CFPB data',
      h1: 'Watch governed context resolve a real contradiction.',
      intro: 'Ask: <em>“What’s the error-resolution deadline under Regulation E?”</em> Two internal sources disagree. Baltor runs seven stages, serves the verified answer with receipts, and holds the contradiction out where you can still see it.',
      live: 'Live API attempt (eCFR) · falls back to the offline corpus — fallback is never silent',
      answer: '10 business days', handles: ['12 CFR 1005 / Reg E', '§1005.11'],
      held: { v: 'FAQ said “30 days”', why: 'Held out / superseded by Reg E §1005.11 — surfaced here, never served as the answer.' },
      receipt: 'rcpt-047bea64f222', verifiedVs: 'live authoritative source (eCFR)', lift: '↑ measured lift +0.5857',
      stages: [
        { head: '4 sources ingested with ACLs, hashes & handles', chips: ['Reg E · 12 CFR 1005', 'CFPB FAQ', 'policy wiki', 'billing config'], ev: 'Reg E (eCFR), the CFPB FAQ, an internal policy page and billing config enter with permissions, content hashes and expandable <b>source handles</b> — before any claim is trusted.' },
        { head: '1 conflict surfaced across 2 internal sources', chips: ['3 candidates', 'precedence → Reg E'], ev: 'The FAQ says <b>“30 days”</b>; Reg E §1005.11 says <b>“10 business days”</b>. Baltor links the evidence and applies source precedence — the regulation outranks the FAQ — rather than guessing.' },
        { head: 'volatile deadline pinned to a live object', chips: ['1 fragile value → object', 'anchored to eCFR'], ev: 'The deadline changes upstream, so Baltor replaces the copied text with a <b>refreshable object</b> anchored to eCFR — it re-checks the source instead of going stale.' },
        { head: 'citation & cross-references attached', chips: ['+2 cross-refs', '§1005.11'], ev: 'Baltor attaches the governing citation (§1005.11, error-resolution) and the connective facts an agent needs to use the answer correctly.' },
        { head: 'shaped to a claim-level cited pack', chips: ['0.06× tokens', 'ranked claims'], ev: 'A long policy thread becomes a <b>token-minimal, citation-anchored</b> pack: the ranked claim, its citation, the held-out conflict, and expansion handles.' },
        { head: 'served to the agent, cited', chips: ['served → Claude Code', 'handle expansion'], ev: 'The agent receives the governed pack and may expand approved <b>source handles</b>. Baltor records what was served, why, and under which policy.' },
        { head: 'verified vs live source · 0 stale · 100% cited', chips: ['adversarial check: pass', 'held-out preserved'], ev: 'Continuous verification checks contradictions, source precedence, freshness and policy. The held-out FAQ value is preserved as a warning, not served.' },
      ],
      warnings: [
        ['warn', 'FAQ “30 days” — held out', 'Superseded by Reg E §1005.11. Surfaced here, never served as the answer.'],
        ['ok', 'Allegations — none served', 'No unverified allegation entered the served pack.'],
        ['ok', 'Stale / unverified — 0 served', 'Every served claim is current and cited; checked 40s ago.'],
      ],
      facts: [
        ['Error-resolution deadline = 10 business days', '12 CFR 1005 / §1005.11', 'vrcpt-8a14', 'orcpt-3f0c', 'verified 40s ago'],
        ['Provisional credit applies after 10 business days', '12 CFR 1005 / §1005.11(c)', 'vrcpt-8a15', 'orcpt-3f0d', 'verified 40s ago'],
        ['(held out) FAQ “30 days”', 'CFPB FAQ (superseded)', '— not served', '—', 'flagged · superseded'],
      ],
    },

    sanctions: {
      domain: 'OFAC SDN · sanctions screening', runLabel: 'Screen against OFAC SDN',
      h1: 'Catch a sanctioned entity the internal list missed.',
      intro: 'Ask: <em>“Is counterparty <b>Northwind Trading LLC</b> sanctioned?”</em> The internal screening list is six days stale. Baltor reconciles it against the live OFAC SDN feed, serves the current answer with receipts, and holds the stale “no match” out.',
      live: 'Live OFAC SDN feed attempt · falls back to the last verified snapshot — fallback is never silent',
      answer: 'Match — sanctioned', handles: ['OFAC SDN (live)', 'added 2026-06-01'],
      held: { v: 'Internal list: “no match”', why: 'The internal list is 6 days stale and missed an entity added 2026-06-01. Held out — never served as a clear.' },
      receipt: 'rcpt-9c12fa3b7e40', verifiedVs: 'live OFAC SDN feed', lift: '↑ caught 6-day stale gap',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['OFAC SDN (live)', 'internal screening list', 'BIS entity list'], ev: 'The live OFAC SDN feed, the internal screening list, and the BIS entity list enter with hashes and <b>source handles</b> — before any match is trusted.' },
        { head: '1 conflict surfaced · stale vs live', chips: ['internal: no match', 'live: match'], ev: 'The internal list returns <b>no match</b>; the live SDN feed returns a <b>match</b> for an entity added six days ago. Baltor applies precedence — the live authoritative feed outranks the snapshot.' },
        { head: 'screening list pinned to the live feed', chips: ['snapshot → refreshable object', 'cadence: several/wk'], ev: 'Sanctions lists change several times a week, so Baltor replaces the copied snapshot with a <b>refreshable object</b> anchored to the live feed — being a day stale is a violation, not an inconvenience.' },
        { head: 'match enriched with program & date', chips: ['+SDN program', 'list-date 2026-06-01'], ev: 'The match is enriched with the sanctions program, the date the entity was added, and the alias that triggered it — the context a reviewer needs.' },
        { head: 'shaped to a screening decision pack', chips: ['0.08× tokens', 'decision + evidence'], ev: 'The result is distilled to a decision pack: the match, the program, the SDN list version, and expansion handles — fewer tokens, full provenance.' },
        { head: 'served to the screening agent, cited', chips: ['served → screening flow', 'handle expansion'], ev: 'The screening agent receives the governed match with a citation to the SDN list version. Baltor records what was served and under which policy.' },
        { head: 'verified vs live SDN · 0 stale served · 100% cited', chips: ['adversarial check: pass', 'stale clear held-out'], ev: 'Verification confirms the match against the live SDN version in force; the stale internal “no match” is preserved as a warning, never served as a clear.' },
      ],
      warnings: [
        ['warn', 'Internal “no match” — held out', '6-day-stale snapshot missed an entity added 2026-06-01. Never served as a clear.'],
        ['ok', 'No clear on a sanctioned party', 'The stale negative was caught before it could produce a false clear.'],
        ['ok', 'Stale / unverified — 0 served', 'The served match cites the live SDN list version in force.'],
      ],
      facts: [
        ['Northwind Trading LLC = SDN match', 'OFAC SDN / 2026-06-01', 'vrcpt-1f7a', 'orcpt-22b9', 'verified 1m ago'],
        ['Program = global sanctions list', 'OFAC SDN program field', 'vrcpt-1f7b', 'orcpt-22ba', 'verified 1m ago'],
        ['(held out) internal “no match”', 'internal list (6d stale)', '— not served', '—', 'flagged · stale'],
      ],
    },

    eudr: {
      domain: 'EUDR · application-date change', runLabel: 'Integrate EUR-Lex change',
      h1: 'Stop citing a regulation date that just moved.',
      intro: 'Ask: <em>“When does the EU Deforestation Regulation apply for large operators?”</em> Internal guidance still cites the old date. Baltor reconciles against the live EUR-Lex amendment, serves the current date, and holds the superseded one out.',
      live: 'Live EUR-Lex attempt · falls back to the last verified snapshot — fallback is never silent',
      answer: '30 December 2025', handles: ['EUR-Lex · Reg (EU) 2023/1115', 'amended'],
      held: { v: 'Internal guidance: “30 Dec 2024”', why: 'Superseded by the EUR-Lex 12-month deferral. Held out — surfaced here, never served as the answer.' },
      receipt: 'rcpt-3ad8be1029f4', verifiedVs: 'live EUR-Lex (amended)', lift: '↑ propagated same-day',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['EUR-Lex (live)', 'EU regulatory corpus', 'internal guidance'], ev: 'The live EUR-Lex entry, the internal EU regulatory corpus and internal guidance enter with hashes and <b>source handles</b> before any date is trusted.' },
        { head: '1 conflict surfaced · amendment vs guidance', chips: ['guidance: 2024', 'live: 2025'], ev: 'Internal guidance says <b>30 Dec 2024</b>; EUR-Lex now says <b>30 Dec 2025</b> after a 12-month deferral. Baltor applies precedence — the live regulation outranks internal guidance.' },
        { head: 'application date pinned to EUR-Lex', chips: ['date → refreshable object', 'watch: amendments'], ev: 'The application date is volatile, so Baltor replaces the copied date with a <b>refreshable object</b> watching EUR-Lex — an amendment re-checks the source instead of going stale.' },
        { head: 'enriched with the deferral citation', chips: ['+amending act', 'Art. 38'], ev: 'The date is enriched with the amending act and the article that sets the new application date — the citation a reviewer can verify.' },
        { head: 'shaped to a claim-level cited pack', chips: ['0.07× tokens', 'ranked claims'], ev: 'The corpus is distilled to a cited pack: the current date, its citation, the superseded date held out, and expansion handles.' },
        { head: 'served to the agent, cited', chips: ['served → compliance agent', 'handle expansion'], ev: 'The agent receives the governed pack citing the amended regulation. Baltor records what was served and under which policy.' },
        { head: 'verified vs live EUR-Lex · 0 stale · 100% cited', chips: ['adversarial check: pass', 'superseded date held-out'], ev: 'Verification confirms the date against the amended EUR-Lex text in force; the superseded 2024 date is preserved as a warning, never served.' },
      ],
      warnings: [
        ['warn', 'Old date “30 Dec 2024” — held out', 'Superseded by the EUR-Lex deferral. Surfaced here, never served as the answer.'],
        ['ok', 'No superseded date served', 'Agents stopped citing the old date the same day the regulation changed.'],
        ['ok', 'Stale / unverified — 0 served', 'The served date cites the amended EUR-Lex text in force.'],
      ],
      facts: [
        ['EUDR applies for large operators = 30 Dec 2025', 'EUR-Lex / Reg (EU) 2023/1115 (amended)', 'vrcpt-5c01', 'orcpt-77a2', 'verified 4h ago'],
        ['12-month deferral via amending act', 'EUR-Lex amending act', 'vrcpt-5c02', 'orcpt-77a3', 'verified 4h ago'],
        ['(held out) “30 Dec 2024”', 'internal guidance (superseded)', '— not served', '—', 'flagged · superseded'],
      ],
    },

    refund: {
      domain: 'Internal policy · refund window', runLabel: 'Reconcile refund policy',
      h1: 'Three systems, three answers, one enforced truth.',
      intro: 'Ask: <em>“What’s our refund window?”</em> Jira, an old wiki page, and the billing system disagree. Baltor reconciles them against the enforcing system, serves the one that’s actually applied, and holds the others out.',
      live: 'Live billing-config read · falls back to the last verified snapshot — fallback is never silent',
      answer: '21 days', handles: ['billing-config (enforcing)', 'policy/refunds'],
      held: { v: 'Jira “30 days” · wiki “14 days”', why: 'Neither is enforced. Held out — the served answer is the value the billing system actually applies.' },
      receipt: 'rcpt-21bd4407c9aa', verifiedVs: 'enforcing billing system', lift: '↓ 52% fewer escalations',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['billing config', 'Jira', 'policy wiki'], ev: 'The billing system config, a Jira decision and an old wiki page enter with hashes and <b>source handles</b> — comments separated from decisions.' },
        { head: '1 conflict surfaced · 3 disagreeing values', chips: ['30 / 14 / 21', 'precedence → billing'], ev: 'Jira says <b>30 days</b>, the wiki <b>14</b>, billing enforces <b>21</b>. Baltor applies precedence — the system that <b>enforces</b> the policy outranks documents about it.' },
        { head: 'refund window pinned to the enforcing system', chips: ['value → refreshable object', 'source: billing'], ev: 'The window is whatever billing actually enforces, so Baltor anchors a <b>refreshable object</b> to the billing config rather than copying a number from a doc.' },
        { head: 'enriched with the owning decision', chips: ['+Jira decision link', 'effective date'], ev: 'The value is enriched with the decision that set it and its effective date — so the answer is explainable, not just asserted.' },
        { head: 'shaped to a support-answer pack', chips: ['0.05× tokens', 'answer + source'], ev: 'The result is distilled to a support pack: the enforced window, the system it came from, the held-out conflicts, and expansion handles.' },
        { head: 'served to the support copilot, cited', chips: ['served → support copilot', 'handle expansion'], ev: 'The copilot answers with the enforced 21-day window, cited to billing. Baltor records what was served and under which policy.' },
        { head: 'verified vs billing · 0 stale · 100% cited', chips: ['adversarial check: pass', 'doc values held-out'], ev: 'Verification confirms the window against the live billing config; the Jira and wiki values are preserved as warnings, never served.' },
      ],
      warnings: [
        ['warn', 'Jira “30” / wiki “14” — held out', 'Neither is enforced. Surfaced here, never served as the answer.'],
        ['ok', 'Confident-but-wrong values caught', 'Retrieval would have served whichever doc it hit first; reconciliation caught the conflict.'],
        ['ok', 'Stale / unverified — 0 served', 'The served window cites the enforcing billing system.'],
      ],
      facts: [
        ['Refund window = 21 days', 'billing-config / refunds', 'vrcpt-7e21', 'orcpt-90c4', 'verified 2m ago'],
        ['Set by decision JIRA-4821', 'Jira decision (linked)', 'vrcpt-7e22', 'orcpt-90c5', 'verified 2m ago'],
        ['(held out) wiki “14” · Jira “30”', 'wiki / Jira (not enforced)', '— not served', '—', 'flagged · unenforced'],
      ],
    },

    tariff: {
      domain: 'WCO HS · tariff classification', runLabel: 'Classify against WCO HS',
      h1: 'Classify a product against the tariff code that’s actually in force.',
      intro: 'Ask: <em>“What’s the HS code and duty basis for lithium-ion battery packs?”</em> An internal mapping still points at the old nomenclature. Baltor reconciles it against the live WCO Harmonized System, serves the current code, and holds the superseded one out.',
      live: 'Live WCO HS lookup attempt · falls back to the last verified snapshot — fallback is never silent',
      answer: 'HS 8507.60', handles: ['WCO HS 2022', 'heading 85.07'],
      held: { v: 'Internal map: “8507.80”', why: 'Points at a pre-2022 sub-heading retired in the HS 2022 revision. Held out — never served as the classification.' },
      receipt: 'rcpt-6b21d9f0ac57', verifiedVs: 'live WCO HS 2022', lift: '↑ caught retired sub-heading',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['WCO HS 2022 (live)', 'internal HS map', 'product master'], ev: 'The live WCO Harmonized System, the internal HS mapping and the product master enter with hashes and <b>source handles</b> before any code is trusted.' },
        { head: '1 conflict surfaced · retired vs current', chips: ['internal: 8507.80', 'live: 8507.60'], ev: 'The internal map says <b>8507.80</b>; WCO HS 2022 places lithium-ion accumulators at <b>8507.60</b>. Baltor applies precedence — the live nomenclature outranks the internal copy.' },
        { head: 'classification pinned to the live nomenclature', chips: ['code → refreshable object', 'watch: HS revisions'], ev: 'HS codes shift on revision cycles, so Baltor anchors a <b>refreshable object</b> to the WCO HS edition rather than copying a sub-heading into stale context.' },
        { head: 'enriched with heading & notes', chips: ['+heading 85.07', 'chapter notes'], ev: 'The code is enriched with its heading, the chapter notes that govern it, and the revision that set it — the basis a classifier can defend.' },
        { head: 'shaped to a classification pack', chips: ['0.07× tokens', 'code + basis'], ev: 'The result is distilled to a pack: the current code, the heading, the held-out retired code, and expansion handles — duty <b>rates are jurisdiction-specific and not asserted here</b>.' },
        { head: 'served to the classification agent, cited', chips: ['served → trade agent', 'handle expansion'], ev: 'The agent receives the governed classification citing the WCO HS edition. Baltor records what was served and under which policy.' },
        { head: 'verified vs live HS · 0 stale · 100% cited', chips: ['adversarial check: pass', 'retired code held-out'], ev: 'Verification confirms the code against the WCO HS edition in force; the retired sub-heading is preserved as a warning, never served.' },
      ],
      warnings: [
        ['warn', 'Retired code “8507.80” — held out', 'Retired in HS 2022. Surfaced here, never served as the classification.'],
        ['ok', 'No duty rate asserted', 'Duty rates are jurisdiction-specific; the pack serves the code + basis, not an unverified rate.'],
        ['ok', 'Stale / unverified — 0 served', 'The served code cites the WCO HS edition in force.'],
      ],
      facts: [
        ['Lithium-ion battery packs = HS 8507.60', 'WCO HS 2022 / 85.07', 'vrcpt-c401', 'orcpt-d92a', 'verified 2h ago'],
        ['Governed by chapter 85 notes', 'WCO HS chapter notes', 'vrcpt-c402', 'orcpt-d92b', 'verified 2h ago'],
        ['(held out) internal “8507.80”', 'internal HS map (retired)', '— not served', '—', 'flagged · retired'],
      ],
    },

    dgr: {
      domain: 'IATA DGR · dangerous-goods shipping', runLabel: 'Check dangerous-goods rule',
      h1: 'Ship the lithium batteries under the rule that’s current.',
      intro: 'Ask: <em>“Can we ship these lithium-ion batteries by air, and at what state of charge?”</em> An internal SOP cites a superseded threshold. Baltor reconciles against the current IATA Dangerous Goods Regulations, serves the rule in force, and holds the old one out.',
      live: 'Live IATA DGR edition check · falls back to the last verified snapshot — fallback is never silent',
      answer: 'Max 30% state of charge', handles: ['IATA DGR (current ed.)', 'PI 965 §II'],
      held: { v: 'SOP: “no SoC limit”', why: 'Predates the state-of-charge restriction. Held out — never served as the shipping rule.' },
      receipt: 'rcpt-0d7e44b18c93', verifiedVs: 'current IATA DGR edition', lift: '↑ caught superseded SOP',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['IATA DGR (current)', 'internal SOP', 'product safety sheet'], ev: 'The current IATA Dangerous Goods Regulations, the internal shipping SOP and the product safety sheet enter with hashes and <b>source handles</b> before any rule is trusted.' },
        { head: '1 conflict surfaced · SOP vs current edition', chips: ['SOP: no limit', 'DGR: ≤30% SoC'], ev: 'The SOP says <b>no state-of-charge limit</b>; the current DGR (Packing Instruction 965) caps lithium-ion cells at <b>30% SoC</b> for air transport. Baltor applies precedence — the live regulation outranks the SOP.' },
        { head: 'rule pinned to the live DGR edition', chips: ['threshold → refreshable object', 'watch: annual edition'], ev: 'The DGR revises annually, so Baltor anchors a <b>refreshable object</b> to the current edition rather than copying a threshold into a stale SOP.' },
        { head: 'enriched with packing instruction', chips: ['+PI 965 §II', 'UN3480'], ev: 'The rule is enriched with the packing instruction, the UN number, and the edition that set it — the citation a shipper can present to a carrier.' },
        { head: 'shaped to a shipping-decision pack', chips: ['0.06× tokens', 'rule + citation'], ev: 'The result is distilled to a pack: the SoC limit, the packing instruction, the held-out SOP, and expansion handles.' },
        { head: 'served to the logistics agent, cited', chips: ['served → logistics agent', 'handle expansion'], ev: 'The agent receives the governed rule citing the current DGR edition. Baltor records what was served and under which policy.' },
        { head: 'verified vs live DGR · 0 stale · 100% cited', chips: ['adversarial check: pass', 'old SOP held-out'], ev: 'Verification confirms the rule against the DGR edition in force; the superseded SOP threshold is preserved as a warning, never served.' },
      ],
      warnings: [
        ['warn', 'SOP “no SoC limit” — held out', 'Predates the 30% restriction. Surfaced here, never served as the rule.'],
        ['ok', 'No unsafe shipment cleared', 'The superseded SOP could not authorize an out-of-spec air shipment.'],
        ['ok', 'Stale / unverified — 0 served', 'The served rule cites the DGR edition in force.'],
      ],
      facts: [
        ['Air transport lithium-ion = ≤30% SoC', 'IATA DGR / PI 965 §II', 'vrcpt-9a31', 'orcpt-1b7c', 'verified 1h ago'],
        ['Classified UN3480 (batteries alone)', 'IATA DGR / UN3480', 'vrcpt-9a32', 'orcpt-1b7d', 'verified 1h ago'],
        ['(held out) SOP “no limit”', 'internal SOP (superseded)', '— not served', '—', 'flagged · superseded'],
      ],
    },

    transit: {
      domain: 'Ocean freight · transit-time SLA', runLabel: 'Reconcile transit SLA',
      h1: 'Quote the transit time the carrier contract actually commits.',
      intro: 'Ask: <em>“What’s the committed transit time, EU→US East Coast ocean freight?”</em> The marketing page and the carrier contract disagree. Baltor reconciles them against the enforcing contract, serves the committed SLA, and holds the optimistic number out.',
      live: 'Live carrier-contract read · falls back to the last verified snapshot — fallback is never silent',
      answer: '18–21 days (committed)', handles: ['carrier contract (enforcing)', 'lane EU→USEC'],
      held: { v: 'Marketing page: “12 days”', why: 'A best-case figure, not the contracted SLA. Held out — never served as the commitment.' },
      receipt: 'rcpt-4f80a2c6e1d5', verifiedVs: 'enforcing carrier contract', lift: '↓ fewer missed-ETA disputes',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['carrier contract', 'marketing page', 'lane schedule'], ev: 'The carrier contract, a marketing page and the published lane schedule enter with hashes and <b>source handles</b> — marketing claims separated from contractual commitments.' },
        { head: '1 conflict surfaced · marketing vs contract', chips: ['marketing: 12d', 'contract: 18–21d'], ev: 'The marketing page says <b>12 days</b>; the carrier contract commits <b>18–21 days</b> with a transit guarantee. Baltor applies precedence — the <b>enforcing</b> contract outranks marketing copy.' },
        { head: 'SLA pinned to the enforcing contract', chips: ['ETA → refreshable object', 'source: contract'], ev: 'The committed transit time is whatever the contract enforces, so Baltor anchors a <b>refreshable object</b> to the contract rather than quoting a best-case marketing figure.' },
        { head: 'enriched with lane & guarantee terms', chips: ['+lane EU→USEC', 'transit guarantee'], ev: 'The SLA is enriched with the lane, the guarantee clause and the contract version — so a quoted ETA is explainable, not optimistic.' },
        { head: 'shaped to a quoting pack', chips: ['0.05× tokens', 'SLA + clause'], ev: 'The result is distilled to a pack: the committed window, the contract clause, the held-out marketing figure, and expansion handles.' },
        { head: 'served to the quoting agent, cited', chips: ['served → quoting agent', 'handle expansion'], ev: 'The agent quotes the committed 18–21 day window, cited to the contract. Baltor records what was served and under which policy.' },
        { head: 'verified vs contract · 0 stale · 100% cited', chips: ['adversarial check: pass', 'marketing figure held-out'], ev: 'Verification confirms the SLA against the contract in force; the optimistic marketing figure is preserved as a warning, never served as the commitment.' },
      ],
      warnings: [
        ['warn', 'Marketing “12 days” — held out', 'A best-case figure, not the contracted SLA. Never served as the commitment.'],
        ['ok', 'No over-promise quoted', 'The optimistic figure could not be served as a committed ETA.'],
        ['ok', 'Stale / unverified — 0 served', 'The served SLA cites the enforcing carrier contract.'],
      ],
      facts: [
        ['EU→USEC committed transit = 18–21 days', 'carrier contract / lane EU→USEC', 'vrcpt-2d11', 'orcpt-8e40', 'verified 30m ago'],
        ['Transit guarantee clause applies', 'carrier contract § transit', 'vrcpt-2d12', 'orcpt-8e41', 'verified 30m ago'],
        ['(held out) marketing “12 days”', 'marketing page (best-case)', '— not served', '—', 'flagged · not contractual'],
      ],
    },

    water: {
      domain: 'EPA LCRR · drinking-water safety', runLabel: 'Integrate EPA lead rule',
      h1: 'Serve the lead limit that’s actually enforceable today.',
      intro: 'Ask: <em>“What’s the lead limit for our drinking-water system?”</em> An internal SOP knows only the old action level. Baltor reconciles against the EPA Lead &amp; Copper Rule Revisions, serves the current thresholds, and holds the incomplete one out.',
      live: 'Live eCFR (40 CFR 141) attempt · falls back to the last verified snapshot — fallback is never silent',
      answer: '15 ppb action + 10 ppb trigger', handles: ['EPA LCRR', '40 CFR 141'],
      held: { v: 'SOP: “15 ppb only”', why: 'Pre-LCRR — misses the new 10 ppb trigger level. Held out, never served as the complete rule.' },
      receipt: 'rcpt-7c44e2901b8a', verifiedVs: 'live eCFR (40 CFR 141)', lift: '↑ added missing trigger level',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['EPA LCRR (live)', 'internal SOP', 'sampling log'], ev: 'The live EPA Lead &amp; Copper Rule Revisions, the internal SOP and the system’s sampling log enter with hashes and <b>source handles</b> before any threshold is trusted.' },
        { head: '1 gap surfaced · SOP missing the trigger', chips: ['SOP: 15 ppb', 'LCRR: 15 + 10 ppb'], ev: 'The SOP knows only the <b>15 ppb action level</b>; the LCRR adds a <b>10 ppb trigger level</b> requiring action earlier. Baltor applies precedence — the live rule outranks the SOP.' },
        { head: 'thresholds pinned to the live rule', chips: ['values → refreshable object', 'watch: rule revisions'], ev: 'Drinking-water limits revise, so Baltor anchors a <b>refreshable object</b> to the eCFR rule rather than copying a number into a stale SOP.' },
        { head: 'enriched with sampling & action duties', chips: ['+tap-sampling', '§141.80'], ev: 'The thresholds are enriched with the sampling protocol and the actions each level triggers — the duty a water system must actually perform.' },
        { head: 'shaped to a compliance pack', chips: ['0.06× tokens', 'thresholds + duties'], ev: 'The result is distilled to a pack: both thresholds, the duties they trigger, the held-out incomplete rule, and expansion handles.' },
        { head: 'served to the compliance agent, cited', chips: ['served → water-ops agent', 'handle expansion'], ev: 'The agent receives the governed thresholds citing the LCRR. Baltor records what was served and under which policy.' },
        { head: 'verified vs live rule · 0 stale · 100% cited', chips: ['adversarial check: pass', 'incomplete rule held-out'], ev: 'Verification confirms the thresholds against the rule in force; the SOP’s incomplete “15 ppb only” is preserved as a warning, never served.' },
      ],
      warnings: [
        ['warn', 'SOP “15 ppb only” — held out', 'Misses the LCRR 10 ppb trigger. Surfaced here, never served as the complete rule.'],
        ['ok', 'No under-protective limit served', 'The incomplete SOP could not be served as the operative rule.'],
        ['ok', 'Stale / unverified — 0 served', 'The served thresholds cite the eCFR rule in force.'],
      ],
      facts: [
        ['Lead action level = 15 ppb', 'EPA LCRR / 40 CFR 141.80', 'vrcpt-e201', 'orcpt-aa10', 'verified 3h ago'],
        ['Trigger level = 10 ppb (LCRR)', 'EPA LCRR / 40 CFR 141.80(c)', 'vrcpt-e202', 'orcpt-aa11', 'verified 3h ago'],
        ['(held out) SOP “15 ppb only”', 'internal SOP (pre-LCRR)', '— not served', '—', 'flagged · incomplete'],
      ],
    },

    freight: {
      domain: 'FMCSA HOS · freight delivery time', runLabel: 'Reconcile driving-hours rule',
      h1: 'Plan delivery ETAs against the driving limit that’s in force.',
      intro: 'Ask: <em>“What’s the maximum daily driving time for our US delivery drivers?”</em> The dispatch SOP cites an outdated limit. Baltor reconciles against the FMCSA Hours-of-Service rule, serves the current limit, and holds the stale one out — so ETAs are legal, not optimistic.',
      live: 'Live eCFR (49 CFR 395) attempt · falls back to the last verified snapshot — fallback is never silent',
      answer: '11 hrs driving / 14-hr window', handles: ['FMCSA HOS', '49 CFR 395'],
      held: { v: 'Dispatch SOP: “10 hrs”', why: 'Pre-2003 driving limit. Held out — never served as the operative rule (and it would mis-plan ETAs).' },
      receipt: 'rcpt-1e93ad60f472', verifiedVs: 'live eCFR (49 CFR 395)', lift: '↑ legal ETAs, fewer violations',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['FMCSA HOS (live)', 'dispatch SOP', 'ELD logs'], ev: 'The live FMCSA Hours-of-Service rule, the dispatch SOP and the ELD logs enter with hashes and <b>source handles</b> before any limit is trusted.' },
        { head: '1 conflict surfaced · SOP vs current rule', chips: ['SOP: 10 hrs', 'FMCSA: 11 hrs / 14-hr'], ev: 'The SOP says <b>10 hours</b>; FMCSA allows <b>11 hours driving within a 14-hour window</b> after 10 hours off. Baltor applies precedence — the live regulation outranks the SOP.' },
        { head: 'limit pinned to the live rule', chips: ['limit → refreshable object', 'watch: HOS amendments'], ev: 'HOS rules change, so Baltor anchors a <b>refreshable object</b> to the eCFR rule rather than copying an hour count into a stale SOP.' },
        { head: 'enriched with window & rest duties', chips: ['+14-hr window', '30-min break'], ev: 'The limit is enriched with the 14-hour window, the required 30-minute break and the 10-hour reset — the constraints an ETA planner must respect.' },
        { head: 'shaped to a planning pack', chips: ['0.05× tokens', 'limit + window'], ev: 'The result is distilled to a pack: the driving limit, the window, the held-out stale limit, and expansion handles.' },
        { head: 'served to the routing agent, cited', chips: ['served → routing agent', 'handle expansion'], ev: 'The agent plans ETAs against the governed 11-hour limit, cited to FMCSA. Baltor records what was served and under which policy.' },
        { head: 'verified vs live rule · 0 stale · 100% cited', chips: ['adversarial check: pass', 'stale limit held-out'], ev: 'Verification confirms the limit against the rule in force; the SOP’s stale 10-hour figure is preserved as a warning, never served.' },
      ],
      warnings: [
        ['warn', 'SOP “10 hrs” — held out', 'Pre-2003 limit. Surfaced here, never served as the operative rule.'],
        ['ok', 'No illegal ETA planned', 'The stale limit could not be used to plan a non-compliant route.'],
        ['ok', 'Stale / unverified — 0 served', 'The served limit cites the eCFR rule in force.'],
      ],
      facts: [
        ['Max driving = 11 hrs / 14-hr window', 'FMCSA / 49 CFR 395.3', 'vrcpt-f311', 'orcpt-bb20', 'verified 1h ago'],
        ['30-min break required by 8th hour', 'FMCSA / 49 CFR 395.3(a)(3)', 'vrcpt-f312', 'orcpt-bb21', 'verified 1h ago'],
        ['(held out) SOP “10 hrs”', 'dispatch SOP (pre-2003)', '— not served', '—', 'flagged · superseded'],
      ],
    },

    reserves: {
      domain: 'SEC reserves · oil & gas booking', runLabel: 'Reconcile reserves basis',
      h1: 'Book proved reserves on the price basis the rule requires.',
      intro: 'Ask: <em>“Can we book these barrels as proved reserves at today’s price?”</em> An internal model uses spot price. Baltor reconciles against the SEC reserves rule, serves the required pricing basis, and holds the spot-price assumption out.',
      live: 'Live SEC rule (17 CFR 210.4-10) attempt · falls back to the last verified snapshot — fallback is never silent',
      answer: '12-month average price basis', handles: ['SEC 17 CFR 210.4-10', 'SPE-PRMS'],
      held: { v: 'Model: “spot price”', why: 'SEC proved reserves use the unweighted 12-month first-of-month average, not spot. Held out — never served as the booking basis.' },
      receipt: 'rcpt-58c1de24a9f0', verifiedVs: 'live SEC reserves rule', lift: '↑ caught non-compliant basis',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['SEC rule (live)', 'internal reserves model', 'price deck'], ev: 'The live SEC reserves rule, the internal reserves model and the price deck enter with hashes and <b>source handles</b> before any basis is trusted.' },
        { head: '1 conflict surfaced · spot vs SEC basis', chips: ['model: spot', 'SEC: 12-mo avg'], ev: 'The model books at <b>spot price</b>; the SEC requires the <b>unweighted 12-month first-of-month average</b> for proved reserves. Baltor applies precedence — the rule outranks the model assumption.' },
        { head: 'basis pinned to the live rule', chips: ['basis → refreshable object', 'watch: SEC guidance'], ev: 'The pricing basis is defined by rule, so Baltor anchors a <b>refreshable object</b> to the SEC text rather than copying an assumption into the model.' },
        { head: 'enriched with certainty & category', chips: ['+reasonable certainty', '1P / proved'], ev: 'The basis is enriched with the reasonable-certainty standard and the proved (1P) category definition — the criteria an auditor checks.' },
        { head: 'shaped to a booking pack', chips: ['0.07× tokens', 'basis + criteria'], ev: 'The result is distilled to a pack: the pricing basis, the certainty standard, the held-out spot assumption, and expansion handles — <b>no reserve volume is asserted here</b>.' },
        { head: 'served to the reserves agent, cited', chips: ['served → reserves agent', 'handle expansion'], ev: 'The agent applies the governed basis citing the SEC rule. Baltor records what was served and under which policy.' },
        { head: 'verified vs live rule · 0 stale · 100% cited', chips: ['adversarial check: pass', 'spot basis held-out'], ev: 'Verification confirms the basis against the rule in force; the spot-price assumption is preserved as a warning, never served as the booking basis.' },
      ],
      warnings: [
        ['warn', 'Model “spot price” — held out', 'Not the SEC basis for proved reserves. Surfaced here, never served.'],
        ['ok', 'No non-compliant booking served', 'The spot-price assumption could not be served as the proved-reserves basis.'],
        ['ok', 'No reserve volume asserted', 'The pack serves the basis + criteria, not an unverified barrel count.'],
      ],
      facts: [
        ['Proved reserves basis = 12-mo avg price', 'SEC / 17 CFR 210.4-10', 'vrcpt-a701', 'orcpt-cc30', 'verified 5h ago'],
        ['Requires reasonable certainty (1P)', 'SEC / SPE-PRMS', 'vrcpt-a702', 'orcpt-cc31', 'verified 5h ago'],
        ['(held out) model “spot price”', 'internal model (non-compliant)', '— not served', '—', 'flagged · wrong basis'],
      ],
    },

    bunker: {
      domain: 'IMO 2020 / MARPOL · marine fuel delivery', runLabel: 'Check marine-fuel sulphur cap',
      h1: 'Deliver bunker fuel under the sulphur cap that’s in force.',
      intro: 'Ask: <em>“What’s the maximum sulphur content for the marine fuel we deliver?”</em> An internal spec predates IMO 2020. Baltor reconciles against MARPOL Annex VI, serves the current cap, and holds the pre-2020 limit out.',
      live: 'Live MARPOL Annex VI reference attempt · falls back to the last verified snapshot — fallback is never silent',
      answer: '0.50% sulphur (0.10% in ECA)', handles: ['MARPOL Annex VI', 'IMO 2020'],
      held: { v: 'Spec: “3.50%”', why: 'The pre-2020 global cap. Held out — never served as the deliverable spec (it would be a violation).' },
      receipt: 'rcpt-9f02bc7715ae', verifiedVs: 'MARPOL Annex VI (in force)', lift: '↑ caught pre-2020 spec',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['MARPOL Annex VI', 'internal fuel spec', 'bunker delivery note'], ev: 'The live MARPOL Annex VI reference, the internal fuel spec and the bunker delivery note enter with hashes and <b>source handles</b> before any limit is trusted.' },
        { head: '1 conflict surfaced · spec vs IMO 2020', chips: ['spec: 3.50%', 'IMO: 0.50%'], ev: 'The internal spec allows <b>3.50%</b>; IMO 2020 caps sulphur at <b>0.50% m/m</b> globally (0.10% in Emission Control Areas). Baltor applies precedence — the regulation in force outranks the old spec.' },
        { head: 'cap pinned to the live regulation', chips: ['cap → refreshable object', 'watch: ECA zones'], ev: 'Sulphur caps and ECA boundaries change, so Baltor anchors a <b>refreshable object</b> to MARPOL Annex VI rather than copying a percentage into a stale spec.' },
        { head: 'enriched with ECA & compliance options', chips: ['+0.10% ECA', 'scrubber note'], ev: 'The cap is enriched with the ECA limit and the equivalent-compliance options (e.g. scrubbers) — the context a fuel desk needs to deliver compliantly.' },
        { head: 'shaped to a delivery-spec pack', chips: ['0.06× tokens', 'cap + ECA'], ev: 'The result is distilled to a pack: the global cap, the ECA limit, the held-out old spec, and expansion handles.' },
        { head: 'served to the bunkering agent, cited', chips: ['served → bunkering agent', 'handle expansion'], ev: 'The agent delivers to the governed cap citing MARPOL Annex VI. Baltor records what was served and under which policy.' },
        { head: 'verified vs regulation · 0 stale · 100% cited', chips: ['adversarial check: pass', 'old spec held-out'], ev: 'Verification confirms the cap against the regulation in force; the pre-2020 3.50% spec is preserved as a warning, never served as the deliverable.' },
      ],
      warnings: [
        ['warn', 'Spec “3.50%” — held out', 'Pre-2020 cap. Surfaced here, never served as the deliverable spec.'],
        ['ok', 'No non-compliant fuel spec served', 'The old spec could not be served as a deliverable in an IMO 2020 world.'],
        ['ok', 'Stale / unverified — 0 served', 'The served cap cites MARPOL Annex VI in force.'],
      ],
      facts: [
        ['Global sulphur cap = 0.50% m/m', 'MARPOL Annex VI / Reg 14', 'vrcpt-b801', 'orcpt-dd40', 'verified 2h ago'],
        ['ECA limit = 0.10% m/m', 'MARPOL Annex VI / ECA', 'vrcpt-b802', 'orcpt-dd41', 'verified 2h ago'],
        ['(held out) spec “3.50%”', 'internal fuel spec (pre-2020)', '— not served', '—', 'flagged · superseded'],
      ],
    },

    fda: {
      domain: 'FDA · 21 CFR drug labeling', runLabel: 'Integrate FDA limit',
      h1: 'Serve the dosage limit the FDA actually enforces.',
      intro: 'Ask: <em>“What’s the max acetaminophen per dosage unit in a prescription combination product?”</em> An internal monograph cites the old level. Baltor reconciles against the FDA limit, serves the current value, and holds the superseded one out.',
      live: 'Live FDA reference attempt · falls back to the last verified snapshot — fallback is never silent',
      answer: '325 mg per dosage unit', handles: ['FDA · 21 CFR', 'Rx combination'],
      held: { v: 'Monograph: “500 mg”', why: 'Pre-2014 level. Held out — never served as the enforceable limit.' },
      receipt: 'rcpt-d31a8047fe62', verifiedVs: 'live FDA limit', lift: '↑ caught pre-2014 level',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['FDA limit (live)', 'internal monograph', 'product spec'], ev: 'The live FDA limit, the internal monograph and the product spec enter with hashes and <b>source handles</b> before any value is trusted.' },
        { head: '1 conflict surfaced · monograph vs FDA', chips: ['monograph: 500mg', 'FDA: 325mg'], ev: 'The monograph says <b>500 mg</b>; the FDA capped acetaminophen in prescription combination products at <b>325 mg per dosage unit</b>. Baltor applies precedence — the agency limit outranks the internal monograph.' },
        { head: 'limit pinned to the live FDA value', chips: ['value → refreshable object', 'watch: FDA actions'], ev: 'Drug limits change by FDA action, so Baltor anchors a <b>refreshable object</b> to the FDA reference rather than copying a value into a stale monograph.' },
        { head: 'enriched with scope & basis', chips: ['+Rx combination', 'safety basis'], ev: 'The limit is enriched with the product scope it applies to and the safety basis the FDA cited — the context a labeler must respect.' },
        { head: 'shaped to a labeling pack', chips: ['0.06× tokens', 'limit + scope'], ev: 'The result is distilled to a pack: the limit, its scope, the held-out old value, and expansion handles. <b>Not medical advice.</b>' },
        { head: 'served to the labeling agent, cited', chips: ['served → labeling agent', 'handle expansion'], ev: 'The agent applies the governed limit citing the FDA action. Baltor records what was served and under which policy.' },
        { head: 'verified vs live FDA · 0 stale · 100% cited', chips: ['adversarial check: pass', 'old level held-out'], ev: 'Verification confirms the limit against the FDA value in force; the pre-2014 monograph level is preserved as a warning, never served.' },
      ],
      warnings: [
        ['warn', 'Monograph “500 mg” — held out', 'Pre-2014 level. Surfaced here, never served as the enforceable limit.'],
        ['ok', 'No over-limit value served', 'The stale monograph could not be served as the labeling limit.'],
        ['ok', 'Not medical advice', 'The pack serves the regulatory limit + citation, not clinical guidance.'],
      ],
      facts: [
        ['Rx combination APAP = 325 mg / dosage unit', 'FDA · 21 CFR', 'vrcpt-g101', 'orcpt-ee50', 'verified 2h ago'],
        ['Applies to prescription combinations', 'FDA action (2014)', 'vrcpt-g102', 'orcpt-ee51', 'verified 2h ago'],
        ['(held out) monograph “500 mg”', 'internal monograph (pre-2014)', '— not served', '—', 'flagged · superseded'],
      ],
    },

    icd: {
      domain: 'WHO ICD-11 · clinical coding', runLabel: 'Integrate ICD-11 code',
      h1: 'Code against the classification edition in force.',
      intro: 'Ask: <em>“Which diagnostic code applies under the current classification?”</em> The internal mapping still uses the prior edition. Baltor reconciles against WHO ICD-11, serves the current code, and holds the superseded mapping out.',
      live: 'Live ICD-11 reference attempt · falls back to the last verified snapshot — fallback is never silent',
      answer: 'ICD-11 code in force', handles: ['WHO ICD-11', 'release in force'],
      held: { v: 'Map: prior-edition code', why: 'A superseded ICD-10 mapping. Held out — never served as the current code.' },
      receipt: 'rcpt-4e7720bd1ac9', verifiedVs: 'live WHO ICD-11 release', lift: '↑ caught superseded edition',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['WHO ICD-11 (live)', 'internal code map', 'crosswalk'], ev: 'The live WHO ICD-11 release, the internal code map and the ICD-10→-11 crosswalk enter with hashes and <b>source handles</b> before any code is trusted.' },
        { head: '1 conflict surfaced · prior edition vs current', chips: ['map: prior edition', 'WHO: ICD-11'], ev: 'The internal map returns a <b>prior-edition</b> code; the live release is <b>ICD-11</b>. Baltor applies precedence — the edition in force outranks the internal mapping.' },
        { head: 'code pinned to the live release', chips: ['code → refreshable object', 'watch: releases'], ev: 'Clinical classifications revise on release cycles, so Baltor anchors a <b>refreshable object</b> to the ICD-11 release rather than copying a code into a stale map.' },
        { head: 'enriched with crosswalk & title', chips: ['+ICD-10 crosswalk', 'code title'], ev: 'The code is enriched with its title and the crosswalk from the prior edition — so the mapping is explainable, not asserted.' },
        { head: 'shaped to a coding pack', chips: ['0.06× tokens', 'code + crosswalk'], ev: 'The result is distilled to a pack: the current code, its title, the held-out prior code, and expansion handles. <b>Not clinical advice.</b>' },
        { head: 'served to the coding agent, cited', chips: ['served → coding agent', 'handle expansion'], ev: 'The agent applies the governed code citing the ICD-11 release. Baltor records what was served and under which policy.' },
        { head: 'verified vs live release · 0 stale · 100% cited', chips: ['adversarial check: pass', 'prior code held-out'], ev: 'Verification confirms the code against the release in force; the superseded prior-edition code is preserved as a warning, never served.' },
      ],
      warnings: [
        ['warn', 'Prior-edition code — held out', 'Superseded by the current ICD-11 release. Never served as the current code.'],
        ['ok', 'No superseded code served', 'The stale mapping could not be served as the in-force code.'],
        ['ok', 'Not clinical advice', 'The pack serves the code + crosswalk, not a diagnosis.'],
      ],
      facts: [
        ['Diagnostic code = ICD-11 (in force)', 'WHO ICD-11 release', 'vrcpt-h201', 'orcpt-ff60', 'verified 6h ago'],
        ['Crosswalk from prior edition attached', 'WHO ICD-10→-11 crosswalk', 'vrcpt-h202', 'orcpt-ff61', 'verified 6h ago'],
        ['(held out) prior-edition code', 'internal map (superseded)', '— not served', '—', 'flagged · superseded'],
      ],
    },

    osha: {
      domain: 'OSHA · 29 CFR exposure limit', runLabel: 'Integrate OSHA PEL',
      h1: 'Serve the exposure limit that’s enforceable on the floor.',
      intro: 'Ask: <em>“What’s the permissible exposure limit for respirable crystalline silica?”</em> The internal safety sheet cites the old PEL. Baltor reconciles against the OSHA standard, serves the current limit, and holds the superseded one out.',
      live: 'Live eCFR (29 CFR 1910) attempt · falls back to the last verified snapshot — fallback is never silent',
      answer: '50 µg/m³ (8-hr TWA)', handles: ['OSHA · 29 CFR 1910.1053', 'silica'],
      held: { v: 'Safety sheet: “100 µg/m³”', why: 'The pre-2016 PEL. Held out — never served as the enforceable limit.' },
      receipt: 'rcpt-86fb0e4d2271', verifiedVs: 'live eCFR (29 CFR 1910)', lift: '↑ caught pre-2016 PEL',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['OSHA std (live)', 'internal safety sheet', 'exposure log'], ev: 'The live OSHA silica standard, the internal safety sheet and the exposure log enter with hashes and <b>source handles</b> before any limit is trusted.' },
        { head: '1 conflict surfaced · sheet vs current PEL', chips: ['sheet: 100', 'OSHA: 50 µg/m³'], ev: 'The safety sheet says <b>100 µg/m³</b>; OSHA lowered the silica PEL to <b>50 µg/m³</b> (8-hr TWA) in 2016. Baltor applies precedence — the standard outranks the sheet.' },
        { head: 'PEL pinned to the live standard', chips: ['limit → refreshable object', 'watch: 29 CFR updates'], ev: 'Exposure limits change, so Baltor anchors a <b>refreshable object</b> to the eCFR standard rather than copying a number into a stale safety sheet.' },
        { head: 'enriched with action level & duties', chips: ['+action level 25', 'controls'], ev: 'The PEL is enriched with the 25 µg/m³ action level and the control duties it triggers — what a site must actually do.' },
        { head: 'shaped to a safety pack', chips: ['0.05× tokens', 'PEL + duties'], ev: 'The result is distilled to a pack: the PEL, the action level, the held-out old limit, and expansion handles.' },
        { head: 'served to the EHS agent, cited', chips: ['served → EHS agent', 'handle expansion'], ev: 'The agent applies the governed PEL citing 29 CFR 1910.1053. Baltor records what was served and under which policy.' },
        { head: 'verified vs live standard · 0 stale · 100% cited', chips: ['adversarial check: pass', 'old PEL held-out'], ev: 'Verification confirms the PEL against the standard in force; the pre-2016 100 µg/m³ limit is preserved as a warning, never served.' },
      ],
      warnings: [
        ['warn', 'Sheet “100 µg/m³” — held out', 'Pre-2016 PEL. Surfaced here, never served as the enforceable limit.'],
        ['ok', 'No under-protective limit served', 'The stale sheet could not be served as the operative PEL.'],
        ['ok', 'Stale / unverified — 0 served', 'The served PEL cites the eCFR standard in force.'],
      ],
      facts: [
        ['Silica PEL = 50 µg/m³ (8-hr TWA)', 'OSHA · 29 CFR 1910.1053', 'vrcpt-i301', 'orcpt-1170', 'verified 1h ago'],
        ['Action level = 25 µg/m³', 'OSHA · 29 CFR 1910.1053(b)', 'vrcpt-i302', 'orcpt-1171', 'verified 1h ago'],
        ['(held out) sheet “100 µg/m³”', 'internal safety sheet (pre-2016)', '— not served', '—', 'flagged · superseded'],
      ],
    },

    minwage: {
      domain: 'US Dept of Labor · state & local wage', runLabel: 'Reconcile minimum wage',
      h1: 'Pay the minimum wage that’s actually in force where they work.',
      intro: 'Ask: <em>“What’s the minimum wage we must pay our Seattle staff?”</em> The HR handbook cites the federal floor. Baltor reconciles against the rate in force for that location — federal vs state vs local — serves the highest applicable, and holds the stale figure out.',
      live: 'Live Seattle OLS + WA L&I + US DOL check · falls back to the last verified snapshot — fallback is never silent',
      answer: '$21.30 / hour (Seattle, 2026)', handles: ['Seattle OLS 2026', 'FLSA · 29 CFR 531'],
      held: { v: 'Handbook: $7.25 (federal)', why: 'The federal floor, unchanged since 2009. For a Seattle worker the highest applicable rate governs — held out, never served.' },
      receipt: 'rcpt-7c92ab40f118', verifiedVs: 'Seattle OLS rate in force', lift: '↑ caught a wage-law violation',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['Seattle OLS (live)', 'WA L&I', 'internal handbook'], ev: 'The live Seattle Office of Labor Standards rate, the Washington state rate and the internal HR handbook enter with hashes and <b>source handles</b> before any number is trusted.' },
        { head: '1 conflict surfaced · handbook vs in-force', chips: ['handbook: $7.25', 'Seattle: $21.30'], ev: 'The handbook cites the <b>federal $7.25</b>; Seattle’s 2026 local ordinance is <b>$21.30</b> (WA state is $17.13). Baltor applies precedence — the <b>highest applicable</b> rate for the work location governs.' },
        { head: 'rate pinned to the live local ordinance', chips: ['rate → refreshable object', 'watch: annual CPI'], ev: 'Local minimum wages adjust annually for inflation, so Baltor anchors a <b>refreshable object</b> to the Seattle OLS rate rather than copying a number into a stale handbook.' },
        { head: 'enriched with jurisdiction & basis', chips: ['+work-location rule', 'employer size'], ev: 'The rate is enriched with the work-location rule (the rate where the employee performs work), employer-size tier, and the ordinance that set it — what payroll must actually apply.' },
        { head: 'shaped to a payroll pack', chips: ['0.05× tokens', 'rate + rule'], ev: 'The result is distilled to a pack: the in-force rate, the highest-applicable rule, the held-out federal figure, and expansion handles. <b>Not legal advice.</b>' },
        { head: 'served to the payroll agent, cited', chips: ['served → payroll agent', 'handle expansion'], ev: 'The agent applies the governed rate citing Seattle OLS. Baltor records what was served and under which policy.' },
        { head: 'verified vs live OLS · 0 stale · 100% cited', chips: ['adversarial check: pass', 'federal figure held-out'], ev: 'Verification confirms the rate against the ordinance in force; the federal floor is preserved as a warning, never served as the operative minimum.' },
      ],
      warnings: [
        ['warn', 'Handbook “$7.25” — held out', 'The federal floor. Paying it to a Seattle worker is a wage violation; surfaced here, never served.'],
        ['ok', 'No underpayment served', 'The stale federal figure could not be served as the operative minimum wage.'],
        ['ok', 'Stale / unverified — 0 served', 'The served rate cites the Seattle ordinance in force.'],
      ],
      facts: [
        ['Seattle minimum wage (2026) = $21.30 / hr', 'Seattle OLS · 2026 ordinance', 'vrcpt-7c01', 'orcpt-aa90', 'verified 20m ago'],
        ['Highest applicable rate governs by work location', 'US DOL WHD · FLSA', 'vrcpt-7c02', 'orcpt-aa91', 'verified 20m ago'],
        ['(held out) handbook “$7.25”', 'internal handbook (federal floor)', '— not served', '—', 'flagged · superseded'],
      ],
    },

    export: {
      domain: 'BIS · 15 CFR export controls', runLabel: 'Classify export control',
      h1: 'Don’t ship on a classification that’s wrong.',
      intro: 'Ask: <em>“Can we export this item to that destination without a license?”</em> An internal classification says EAR99 — no license needed. Baltor reconciles against the current Commerce Control List, serves the controlled classification, and holds the EAR99 call out.',
      live: 'Live BIS Commerce Control List lookup · falls back to the last verified snapshot — fallback is never silent',
      answer: 'License required · ECCN-controlled', handles: ['BIS CCL (current)', '15 CFR · EAR'],
      held: { v: 'Internal: “EAR99 — no license”', why: 'A misclassification: the item is on the Commerce Control List for this destination. Held out — never served as the export decision.' },
      receipt: 'rcpt-3e51c7d0a92b', verifiedVs: 'current BIS Commerce Control List', lift: '↑ caught a controlled-item misclassification',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['BIS CCL (live)', 'internal class.', 'item spec'], ev: 'The live BIS Commerce Control List, the internal classification record and the item spec enter with hashes and <b>source handles</b> before any export call is trusted.' },
        { head: '1 conflict surfaced · EAR99 vs controlled', chips: ['internal: EAR99', 'CCL: ECCN-controlled'], ev: 'The internal record says <b>EAR99</b> (no license); the current CCL classifies the item under an <b>ECCN controlled to this destination</b>. Baltor applies precedence — the live CCL outranks the internal record.' },
        { head: 'classification pinned to the live CCL', chips: ['ECCN → refreshable object', 'watch: CCL + entity list'], ev: 'Control lists and destination policies change, so Baltor anchors a <b>refreshable object</b> to the CCL classification rather than copying “EAR99” into stale context.' },
        { head: 'enriched with reason & destination', chips: ['+reason for control', 'destination policy'], ev: 'The classification is enriched with the reason for control and the destination’s licensing policy — the basis an export decision must cite.' },
        { head: 'shaped to a screening pack', chips: ['0.06× tokens', 'ECCN + basis'], ev: 'The result is distilled to a pack: the controlled classification, the licensing requirement, the held-out EAR99 call, and expansion handles. <b>Not legal advice.</b>' },
        { head: 'served to the trade-compliance agent, cited', chips: ['served → compliance agent', 'handle expansion'], ev: 'The agent receives the governed classification citing the CCL and routes the shipment to licensing. Baltor records what was served and under which policy.' },
        { head: 'verified vs live CCL · 0 stale · 100% cited', chips: ['adversarial check: pass', 'EAR99 call held-out'], ev: 'Verification confirms the classification against the CCL in force; the EAR99 misclassification is preserved as a warning, never served as the export decision.' },
      ],
      warnings: [
        ['warn', 'Internal “EAR99” — held out', 'A misclassification of a controlled item. Shipping on it risks a violation; surfaced here, never served.'],
        ['ok', 'No unlicensed export cleared', 'The EAR99 call could not authorize a license-free shipment of a controlled item.'],
        ['ok', 'Stale / unverified — 0 served', 'The served classification cites the Commerce Control List in force.'],
      ],
      facts: [
        ['Item is ECCN-controlled to this destination', 'BIS CCL · 15 CFR (EAR)', 'vrcpt-3e01', 'orcpt-bc70', 'verified 50m ago'],
        ['License required before export', 'BIS · destination licensing policy', 'vrcpt-3e02', 'orcpt-bc71', 'verified 50m ago'],
        ['(held out) internal “EAR99”', 'internal classification (misclassified)', '— not served', '—', 'flagged · misclassified'],
      ],
    },

    faa: {
      domain: 'FAA · 14 CFR airworthiness', runLabel: 'Check airworthiness directive',
      h1: 'Ground the part the FAA actually mandates action on.',
      intro: 'Ask: <em>“Is this engine component subject to an active airworthiness directive?”</em> The maintenance record cites a closed AD. Baltor reconciles against the live FAA AD list, serves the directive in force, and holds the superseded one out.',
      live: 'Live FAA Airworthiness Directives lookup · falls back to the last verified snapshot — fallback is never silent',
      answer: 'AD active · repetitive inspection due', handles: ['FAA AD (current)', '14 CFR 39'],
      held: { v: 'Record: “AD closed (2019)”', why: 'Superseded by a later AD that reopened the requirement. Held out — never served as the airworthiness status.' },
      receipt: 'rcpt-9d34fa72b610', verifiedVs: 'live FAA AD list', lift: '↑ caught a superseded AD',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['FAA AD (live)', 'maintenance record', 'part catalog'], ev: 'The live FAA Airworthiness Directives list, the internal maintenance record and the part catalog enter with hashes and <b>source handles</b> before any status is trusted.' },
        { head: '1 conflict surfaced · record vs current AD', chips: ['record: closed', 'FAA: active'], ev: 'The record says the AD is <b>closed</b>; the FAA shows a <b>later AD</b> that superseded it and reopened a repetitive inspection. Baltor applies precedence — the directive in force outranks the maintenance record.' },
        { head: 'status pinned to the live AD', chips: ['AD → refreshable object', 'watch: FAA issuances'], ev: 'ADs supersede on issuance, so Baltor anchors a <b>refreshable object</b> to the FAA AD list rather than copying a “closed” status into a stale record.' },
        { head: 'enriched with action & interval', chips: ['+inspection interval', 'effective date'], ev: 'The status is enriched with the required action, the repetitive interval and the AD’s effective date — what maintenance must actually perform.' },
        { head: 'shaped to an airworthiness pack', chips: ['0.06× tokens', 'AD + action'], ev: 'The result is distilled to a pack: the active AD, the required action, the held-out closed status, and expansion handles. <b>Not airworthiness advice.</b>' },
        { head: 'served to the maintenance agent, cited', chips: ['served → maintenance agent', 'handle expansion'], ev: 'The agent flags the active AD citing the FAA list. Baltor records what was served and under which policy.' },
        { head: 'verified vs live FAA · 0 stale · 100% cited', chips: ['adversarial check: pass', 'closed status held-out'], ev: 'Verification confirms the AD against the FAA list in force; the superseded “closed” status is preserved as a warning, never served.' },
      ],
      warnings: [
        ['warn', 'Record “AD closed” — held out', 'Superseded by a later AD. Flying on it risks an unairworthy part; surfaced here, never served.'],
        ['ok', 'No unsafe status served', 'The stale “closed” record could not be served as the airworthiness status.'],
        ['ok', 'Stale / unverified — 0 served', 'The served status cites the FAA AD list in force.'],
      ],
      facts: [
        ['Component subject to active AD · repetitive inspection', 'FAA AD · 14 CFR 39', 'vrcpt-9d01', 'orcpt-ce80', 'verified 35m ago'],
        ['Supersedes the 2019 AD on record', 'FAA AD supersedure', 'vrcpt-9d02', 'orcpt-ce81', 'verified 35m ago'],
        ['(held out) record “closed 2019”', 'maintenance record (superseded)', '— not served', '—', 'flagged · superseded'],
      ],
    },

    gaap: {
      domain: 'FASB · accounting effective date', runLabel: 'Reconcile effective date',
      h1: 'Apply the standard on the date it’s actually effective for you.',
      intro: 'Ask: <em>“When does the new standard take effect for us?”</em> A finance memo cites the original date. Baltor reconciles against the FASB Accounting Standards Update — including its deferral — serves the effective date in force, and holds the stale one out.',
      live: 'Live FASB ASU + deferral check · falls back to the last verified snapshot — fallback is never silent',
      answer: 'Effective FY2027 (per deferral)', handles: ['FASB ASU (amended)', 'effective-date §'],
      held: { v: 'Memo: “effective FY2025”', why: 'The original date, later deferred by an amending ASU. Held out — never served as the effective date.' },
      receipt: 'rcpt-2b88e1c4079a', verifiedVs: 'current FASB ASU (with deferral)', lift: '↑ caught a pre-deferral date',
      stages: [
        { head: '3 sources ingested with ACLs, hashes & handles', chips: ['FASB ASU (live)', 'finance memo', 'entity profile'], ev: 'The live FASB Accounting Standards Update, the internal finance memo and the entity profile (filer status) enter with hashes and <b>source handles</b> before any date is trusted.' },
        { head: '1 conflict surfaced · memo vs amended ASU', chips: ['memo: FY2025', 'ASU: FY2027'], ev: 'The memo cites the <b>original FY2025</b> date; an amending ASU <b>deferred</b> it to FY2027 for this filer class. Baltor applies precedence — the amended standard outranks the internal memo.' },
        { head: 'date pinned to the live ASU', chips: ['date → refreshable object', 'watch: amending ASUs'], ev: 'Effective dates shift by amendment, so Baltor anchors a <b>refreshable object</b> to the ASU rather than copying a date into a stale memo.' },
        { head: 'enriched with filer class & transition', chips: ['+filer class', 'transition method'], ev: 'The date is enriched with the filer class it applies to and the transition method — the basis a controller must apply.' },
        { head: 'shaped to a reporting pack', chips: ['0.05× tokens', 'date + basis'], ev: 'The result is distilled to a pack: the effective date in force, the filer-class basis, the held-out original date, and expansion handles. <b>Not accounting advice.</b>' },
        { head: 'served to the reporting agent, cited', chips: ['served → reporting agent', 'handle expansion'], ev: 'The agent applies the governed date citing the amended ASU. Baltor records what was served and under which policy.' },
        { head: 'verified vs live ASU · 0 stale · 100% cited', chips: ['adversarial check: pass', 'original date held-out'], ev: 'Verification confirms the date against the ASU in force; the pre-deferral date is preserved as a warning, never served.' },
      ],
      warnings: [
        ['warn', 'Memo “FY2025” — held out', 'The pre-deferral date. Adopting early on it misstates the period; surfaced here, never served.'],
        ['ok', 'No premature adoption served', 'The stale memo date could not be served as the effective date.'],
        ['ok', 'Stale / unverified — 0 served', 'The served date cites the amended ASU in force.'],
      ],
      facts: [
        ['Effective FY2027 for this filer class (per deferral)', 'FASB ASU · effective-date §', 'vrcpt-2b01', 'orcpt-df90', 'verified 1h ago'],
        ['Deferred from the original FY2025 date', 'FASB amending ASU', 'vrcpt-2b02', 'orcpt-df91', 'verified 1h ago'],
        ['(held out) memo “FY2025”', 'internal finance memo (pre-deferral)', '— not served', '—', 'flagged · superseded'],
      ],
    },
  };

  const WHY_SAFE = [
    'No unverified allegation was served.',
    'The held-out contradiction is visible — separately from the answer.',
    'Every served fact keeps its receipt.',
    'Every served fact keeps its source handle.',
    'The model proposed; Baltor disposed. Output is a candidate, not truth.',
  ];

  function esc(s) { return s; }
  function render(root, key) {
    const S = SCENARIOS[key] || SCENARIOS.cfpb;
    const stages = S.stages.map((st, i) => {
      const [n, nm] = STAGE_NAMES[i];
      return `<div class="cd-stage ${i === 6 ? 'verify' : ''}" data-i="${i}">
        <div class="cd-stage-row">
          <span class="cd-stage-dot"></span><span class="cd-stage-n">${n}</span>
          <div class="cd-stage-body">
            <div class="cd-stage-nm">${nm} <span class="cd-stage-status">pending</span></div>
            <div class="cd-stage-head">${st.head}</div>
            <div class="cd-stage-chips">${st.chips.map((c) => `<span>${c}</span>`).join('')}</div>
            <div class="cd-stage-ev">${st.ev}</div>
          </div>
          <span class="cd-caret">▸</span>
        </div></div>`;
    }).join('');

    root.innerHTML = `
      <div class="cd-top"><div class="cd-wrap" style="display:flex;align-items:center;gap:14px;padding-top:0;padding-bottom:0;width:100%;box-sizing:border-box;">
        <a class="cd-logo" href="Baltor Guided Demos.html"><span class="cd-mark">◳</span><span>Baltor<small>guided demo · ${S.domain}</small></span></a>
        <span class="sp"></span>
        <a class="cd-back" href="Baltor Guided Demos.html">← All data examples</a>
        <span class="cd-tag" style="margin-left:14px;">Governed context · the model never decides truth</span>
      </div></div>
      <div class="cd-wrap">
        <section class="cd-hero">
          <div class="cd-eyebrow">${S.domain}</div>
          <h1>${S.h1}</h1>
          <p>${S.intro} The model never decides the truth.</p>
        </section>
        <div class="cd-run">
          <button class="cd-runbtn" id="cdRun">▶ ${S.runLabel}</button>
          <div class="cd-toggle" id="cdMode" role="group" aria-label="Source mode">
            <button class="on" data-mode="offline">Offline reference corpus</button>
            <button data-mode="live">Live API + offline fallback</button>
          </div>
          <span class="cd-mode-note" id="cdModeNote">Offline · reproducible, no network</span>
          <div class="cd-progress"><i id="cdBar"></i></div>
        </div>
        <div class="oh-card cd-result" id="cdResult">
          <div class="cd-result-top">
            <div class="cd-answer">
              <div class="k">Served answer</div>
              <div class="a" id="cdAnswer"><span class="pend">— run to serve —</span></div>
              <div class="src" id="cdSrc"></div>
            </div>
            <div class="cd-held">
              <div class="k">⚠ Held-out contradiction</div>
              <div class="v" id="cdHeldV">—</div>
              <div class="why" id="cdHeldWhy">Surfaced separately — never served as the answer.</div>
            </div>
          </div>
          <div class="cd-result-foot">
            <span>receipt <b id="cdRcpt">—</b></span>
            <span>verified vs <b id="cdVer">live authoritative source</b></span>
            <span class="cd-lift" id="cdLift"></span>
          </div>
        </div>
        <section class="cd-sec">
          <div class="cd-sec-h"><h2>Pipeline</h2><span class="note">Click the button to run · click any stage for evidence</span></div>
          <div id="cdStages">${stages}</div>
        </section>
        <div class="cd-grid2">
          <section class="cd-sec" style="margin-top:30px;">
            <div class="oh-card oh-card--pad"><div class="card-h">Warnings &amp; held-out</div>
              ${S.warnings.map((w) => `<div class="cd-warn"><span class="ic ${w[0] === 'ok' ? 'ok' : ''}">${w[0] === 'ok' ? '✓' : '⚠'}</span><div><div class="t">${w[1]}</div><div class="d">${w[2]}</div></div></div>`).join('')}
            </div>
          </section>
          <section class="cd-sec" style="margin-top:30px;">
            <div class="oh-card oh-card--pad"><div class="card-h">Why this is safe</div>
              ${WHY_SAFE.map((s) => `<div class="cd-safe"><span class="ck">✓</span>${s}</div>`).join('')}
            </div>
          </section>
        </div>
        <section class="cd-sec">
          <div class="cd-sec-h"><h2>Served facts</h2><span class="note">Each fact carries its handle, receipts and freshness</span></div>
          <div class="oh-card oh-card--pad" style="padding:6px 6px;"><table class="cd-facts" id="cdFacts"></table></div>
        </section>
        <div class="cd-foot"><b>What this demonstrates.</b> Baltor governs context end-to-end — reconciles the conflict, hardens the volatile value, enhances it with the citation, optimizes it to a cited pack, serves it, and verifies it against the live source — preserving receipts and source handles, and holding the contradiction out. <b>It does not</b> show a raw model answer, and the model does not decide the truth.</div>
      </div>`;

    // wire interactions
    const stageEls = [...root.querySelectorAll('.cd-stage')];
    stageEls.forEach((el) => el.querySelector('.cd-stage-row').addEventListener('click', () => el.classList.toggle('open')));

    let mode = 'offline';
    root.querySelector('#cdMode').addEventListener('click', (e) => {
      const b = e.target.closest('button[data-mode]'); if (!b) return; mode = b.dataset.mode;
      [...e.currentTarget.querySelectorAll('button')].forEach((x) => x.classList.toggle('on', x === b));
      root.querySelector('#cdModeNote').textContent = mode === 'offline' ? 'Offline · reproducible, no network' : S.live;
    });

    const runBtn = root.querySelector('#cdRun'), bar = root.querySelector('#cdBar'), result = root.querySelector('#cdResult');
    let running = false;
    function reset() {
      stageEls.forEach((el) => { el.classList.remove('running', 'done', 'open'); el.querySelector('.cd-stage-status').textContent = 'pending'; });
      bar.style.width = '0'; result.classList.remove('live');
      root.querySelector('#cdAnswer').innerHTML = '<span class="pend">— running… —</span>';
      root.querySelector('#cdSrc').innerHTML = ''; root.querySelector('#cdHeldV').textContent = '—';
      root.querySelector('#cdRcpt').textContent = '—'; root.querySelector('#cdLift').textContent = ''; root.querySelector('#cdFacts').innerHTML = '';
    }
    function finish() {
      root.querySelector('#cdAnswer').textContent = S.answer;
      root.querySelector('#cdSrc').innerHTML = S.handles.map((h) => `<span>${h}</span>`).join('');
      root.querySelector('#cdHeldV').textContent = S.held.v;
      root.querySelector('#cdHeldWhy').textContent = S.held.why;
      root.querySelector('#cdRcpt').textContent = S.receipt;
      root.querySelector('#cdVer').textContent = S.verifiedVs;
      root.querySelector('#cdLift').textContent = S.lift;
      result.classList.add('live');
      root.querySelector('#cdFacts').innerHTML =
        '<thead><tr><th>Served fact</th><th>Source handle</th><th>Verify receipt</th><th>Optimize receipt</th><th>Freshness</th></tr></thead><tbody>' +
        S.facts.map((f) => `<tr><td class="fact">${f[0]}</td><td class="mono">${f[1]}</td><td class="mono">${f[2]}</td><td class="mono">${f[3]}</td><td class="mono">${f[4]}</td></tr>`).join('') + '</tbody>';
    }
    function run() {
      if (running) return; running = true; runBtn.disabled = true; reset();
      const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      const step = reduce ? 60 : 600; let i = 0;
      (function next() {
        if (i > 0) { const p = stageEls[i - 1]; p.classList.remove('running'); p.classList.add('done'); p.querySelector('.cd-stage-status').textContent = 'done'; }
        if (i >= stageEls.length) { bar.style.width = '100%'; finish(); runBtn.disabled = false; runBtn.textContent = '⟳ Run again'; running = false; return; }
        const el = stageEls[i]; el.classList.add('running'); el.querySelector('.cd-stage-status').textContent = 'running';
        bar.style.width = Math.round((i / stageEls.length) * 100) + '%'; i++; setTimeout(next, step);
      })();
    }
    runBtn.addEventListener('click', run);
  }

  window.GuidedDemo = { render, SCENARIOS, STAGE_NAMES };
  document.addEventListener('DOMContentLoaded', function () {
    const root = document.getElementById('cd-root');
    if (root) render(root, document.body.dataset.scenario || 'cfpb');
  });
})();
