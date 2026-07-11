# Use case: Human-trafficking signal triage on UGC platforms (Trust + Safety)

A defensive Trust + Safety triage pipeline that reviews user-generated content (job posts, classifieds, escort/massage directories, immigration forums, dating-app messages) for human-trafficking **recruitment** and **solicitation** signals, then escalates flagged posts to a trained human moderator queue with extracted indicators and a structured statement of reasons. Optional Polaris-hotline referral packet; CSAM-suspicion routes to NCMEC **without** model classification.

This is a **defensive** use case. The catalog refuses to host attack tooling, evasion guides, or content-generation flows that would be useful to traffickers. Trust + Safety teams, anti-trafficking NGOs, and law-enforcement-adjacent reviewers are the legitimate audience.

## The ask

> "I need to harness Gemma 4 to detect illicit social-media posts related to human trafficking on user-generated content platforms, and have the catalog be smart enough to find the best components and string them together."

That ask resolves to one new pipeline composed entirely of existing patterns + two new rule packs + the existing Gemma-4 vision adapter.

## What the pipeline does

`pipeline/gemma4-trafficking-ugc-triage` takes a content packet `{ text, images, platform, post_id, locale }`, redacts PII before any inference, runs two GREP packs in order (CSAM-route first so suspected-CSAM short-circuits **before** the model sees the post; then the trafficking-signal pack), uses Gemma-4 vision in a two-stage extract-then-judge call to lift advertised service / claimed identity / control markers / transit cues / contact pathway / image semantics, scores the extracted JSON against the Polaris Project typology, and emits decision + severity + extracted indicators + DSA Art 17 statement of reasons + (optional) referral packet.

The rubric is load-bearing on five things:

1. **CSAM suspicion → NCMEC route without classification.** The model never describes, scores, or labels suspected CSAM material. `pattern/critical-tier-output-override` forces the NCMEC-packet route on a keyword hit; the moderator manually attaches the suspected media to the 18 USC 2258A referral.
2. **Every escalation cites the indicator that triggered it.** Output includes the rule ID, the evidence span, and the Polaris typology category.
3. **`refuse-on-redacted` for missing fields.** Posts with no signal short-circuit to "allow" without inventing findings; redacted PII never reaches the audit trace.
4. **>=2 co-occurring indicators (or 1 critical-tier rule) before escalation.** Single non-critical hits become moderator queue entries with the surfaced indicator, not auto-actions.
5. **Polaris hotline referral is opt-in per jurisdiction.** EU deployments default to local equivalents (e.g. BKA / La Strada); the referral-packet processor reads the jurisdiction from `content_packet.locale`.

## Components

- Persona: [`persona/trust-and-safety-reviewer`](https://github.com/Amarel-Taylor-Scott/openhubforai/blob/main/catalog/personas/trust-and-safety-reviewer.yaml)
- Adapter: [`adapter/gemma-4-26b-vision`](https://github.com/Amarel-Taylor-Scott/openhubforai/blob/main/catalog/adapters/gemma-4-26b-vision.yaml) (multimodal: text + image)
- Knowledge pack: `knowledge-pack/platform-content-policy-frameworks` (DSA + UK OSA + COPPA + NCMEC + GIFCT + NetzDG)
- Rule pack (GREP): [`rule-pack/grep-human-trafficking-ugc-flags`](https://github.com/Amarel-Taylor-Scott/openhubforai/blob/main/catalog/rule-packs/grep/human-trafficking-ugc-flags.yaml) (18 detectors, Polaris + ILO indicators)
- Rule pack (classifier): [`rule-pack/classifier-trafficking-signal`](https://github.com/Amarel-Taylor-Scott/openhubforai/blob/main/catalog/rule-packs/classifier/trafficking-signal-classifier.yaml) (10 Polaris typology slots)
- Rule pack (CSAM-route safety): `rule-pack/grep-platform-moderation-flags`
- Rubric: `rubric/platform-moderation-quality-v1`
- Patterns: `pattern/two-stage-extract-then-judge`, `pattern/critical-tier-output-override`, `pattern/refuse-on-redacted`, `pattern/concept-graph-from-text`
- Pipeline: [`pipeline/gemma4-trafficking-ugc-triage`](https://github.com/Amarel-Taylor-Scott/openhubforai/blob/main/catalog/pipelines/platform-moderation/gemma4-trafficking-ugc-triage.yaml)

## How the catalog finds this for you

Given the free-text task `"detect illicit social media posts related to human trafficking on UGC platforms with Gemma 4"`, the scaffolder script returns the components above in ranked order. Run:

```bash
python3 scripts/scaffold_pipeline_from_task.py \
  "Detect illicit social media posts related to human trafficking on user-generated content platforms with Gemma 4" \
  --hybrid --draft-yaml > /tmp/draft.yaml
```

The `--hybrid` flag turns on semantic search (sentence-transformers over the embeddings sidecar) layered on top of the lexical token overlap. The composer then auto-picks the highest-scoring persona, model adapter, rule packs, knowledge pack, and rubric. For this task, the resulting draft is almost identical to the manifest above — the catalog has the components, it just needed to know which to pick.

## What this pipeline is NOT

- Not an automated CSAM detector. Suspected CSAM is routed to humans + NCMEC. The catalog does not host CSAM classifiers because deploying one without GIFCT + NCMEC + law-enforcement integration is unsafe.
- Not a legal determination engine. The pipeline applies a documented indicator taxonomy and surfaces evidence; trafficking determinations stay with humans (and law enforcement where applicable).
- Not a trafficker-evasion guide. The rule pack patterns are advertising-side cues drawn from publicly-published NGO/UN moderator references; they do not catalog evasion techniques.
- Not a victim-outreach tool. The Polaris hotline referral is one optional pathway; jurisdictional alternatives are the default in non-US locales.

## Pairing patterns

- `pattern/two-stage-extract-then-judge` — separate extraction call from classification call so "focused criteria do not compete with extraction for the model's attention" (this is the exact phrase from the Bill_info AI port that established the pattern).
- `pattern/critical-tier-output-override` — minor-age dispute, victim-disclosure, document-retention, restricted-movement, coerced-speech, and debt-bondage signals force a deterministic output structure, regardless of any other classifier confidence.
- `pattern/refuse-on-redacted` — null over hallucination on missing fields, including missing imagery.
- `pattern/concept-graph-from-text` — extracted indicators + relationships are stored as typed nodes/edges so the moderator queue can group related posts (same control marker, same recruitment ad reposted, same advertised location).

## Deployment notes

- **Run locally.** Gemma-4 26B-A4B-IT is Apache-2.0 and self-hostable. The default `adapter/gemma-4-26b-vision` transport is `transformers`; switch to `vllm` or `mlc-llm` for higher throughput.
- **Sample throughput.** On a single 80 GB GPU, ~6 posts/second at batch 4 (text-only); ~1.2 posts/second with single-image multimodal input. Batch the moderator queue by severity tier.
- **Calibrate thresholds per platform.** The default `threshold: 0.55` on classifier rules is conservative. Run `python3 scripts/bench_pipelines.py` against your own labeled set before lowering it.
- **Audit trace is mandatory.** `processor/audit-trace-emitter` records every applied layer + every rule fired + every cited policy clause. Required for DSA Art 24/27 transparency reports and for any later law-enforcement referral.

## Source taxonomies

- **Polaris Project** — National Human Trafficking Hotline, [Recognizing the signs](https://humantraffickinghotline.org/en/type-trafficking/recognizing-signs), [Typology of 25 modern slavery types](https://polarisproject.org/the-typology-of-modern-slavery/).
- **ILO** — Hard to See, Harder to Count: Survey Guidelines to Estimate Forced Labour of Adults and Children (11-indicator framework).
- **UNODC** — Global Report on Trafficking in Persons (2022).
- **FBI Innocence Lost National Initiative** — public-facing typology of commercial-sexual-exploitation-of-minors signals (sex-trafficking-minor branch only).

All four are NGO/UN moderator-facing taxonomies, not enforcement playbooks.
