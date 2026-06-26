---
name: gemma4-trafficking-ugc-triage
description: Triage user-generated content for trafficking signals → allow / restrict
  / escalate / NCMEC-route.
when_to_use: 'Pipeline kind: review.'
---

# Gemma-4 human-trafficking signal triage (UGC platforms)

DEFENSIVE Trust + Safety pipeline. Reviews user-generated content
(job posts, classifieds, escort listings, immigration forums,
dating-app messages) for human-trafficking RECRUITMENT and
SOLICITATION signals using the Polaris Project + ILO indicator
taxonomies, then escalates flagged posts to a human moderator queue
with extracted indicators, a structured statement of reasons, and
(when criteria met) a Polaris-hotline referral packet.

CSAM suspicion always routes to the NCMEC-referral path WITHOUT
model classification of suspected CSAM material, via
`pattern/critical-tier-output-override`. The model never describes,
scores, or labels suspected CSAM.

Built around the existing Gemma-4 26B vision adapter so a single
multimodal call can read both the post text and any attached
imagery; falls back to text-only Gemma-4 when no media is attached.

Composes three already-published patterns:
  - pattern/two-stage-extract-then-judge — stage 1 extracts every
    relevant field (advertised service, claimed identity, control
    markers, transit cues, contact pathway, attached image
    semantics); stage 2 (the classifier rule pack) judges the
    extracted JSON against the Polaris typology.
  - pattern/refuse-on-redacted — return null over hallucination on
    missing/redacted fields. Posts with no signal short-circuit to
    "allow" without invented findings.
  - pattern/critical-tier-output-override — minor-age dispute OR
    victim-disclosure OR CSAM-suspicion forces a deterministic
    output structure (NCMEC route or trained-reviewer queue),
    overriding any other classifier confidence.

Output is decision + severity + extracted indicators + statement of
reasons + (optional) Polaris/NCMEC referral packets. NEVER
auto-action on a single hit; >=2 co-occurring indicators OR any
critical-tier rule are the escalation thresholds.

## Task

Triage user-generated content for trafficking signals → allow / restrict / escalate / NCMEC-route.

## Steps

1. **structured_to_prose** — `processor` → `processor/structured-to-prose`
2. **redact_pii** — `processor` → `processor/redact-pii-text`
3. **grep_csam_route** — `rule_pack` → `rule-pack/grep-platform-moderation-flags`
4. **grep_trafficking_signals** — `rule_pack` → `rule-pack/grep-human-trafficking-ugc-flags`
5. **stage1_extract_fields** — `processor` → `processor/llm-judge`
6. **stage2_typology_judge** — `rule_pack` → `rule-pack/classifier-trafficking-signal`
7. **rag_policy_clause** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
8. **judge_overall** — `processor` → `processor/llm-judge`
9. **assemble_referral_packet** — `processor` → `processor/json-schema-repair`
10. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/trust-and-safety-reviewer
- **model_adapter**: adapter/gemma-4-26b-vision
- **rule_packs**: `rule-pack/grep-human-trafficking-ugc-flags`, `rule-pack/classifier-trafficking-signal`, `rule-pack/grep-platform-moderation-flags`
- **knowledge_packs**: `knowledge-pack/platform-content-policy-frameworks`

## Success criteria

- rubric `rubric/platform-moderation-quality-v1` threshold 0.7

## Provenance

- Hub component: `pipeline/gemma4-trafficking-ugc-triage` v0.1.0
- License: `MIT`
- Industry: compliance, media, humanitarian, humanitarian.trafficking
- Full source manifest: see `references/manifest.yaml`
