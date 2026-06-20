# Use case: Illicit content + platform moderation (Trust + Safety)

A defensive Trust + Safety triage pipeline that applies a documented platform policy to user-generated content. Surfaces illicit + harmful patterns, routes CSAM suspicion to a human queue + NCMEC referral packet without model classification, and produces an EU DSA Article 17 statement of reasons for every restriction.

This is a **defensive** use case. The catalog refuses to host attack tooling, evasion guides, or content-generation flows that would be useful to abusers. Trust + Safety operations are the legitimate audience.

## What the pipeline does

`pipeline/platform-content-triage` takes a content packet, redacts PII before any inference, runs GREP triage for text-only signals (drug + weapon sale offers, terrorist designated-org glorification, NCII non-consent signals, doxx patterns, self-harm intent, election-day disinfo), retrieves relevant policy clauses (DSA Art 16 / 17, UK OSA Schedule 5, COPPA, NCMEC 18 USC 2258A, GIFCT, NetzDG), then grades the candidate against `rubric/platform-moderation-quality-v1`.

The rubric is load-bearing on five things:

1. CSAM suspicion routes to the human queue + NCMEC referral packet **without** classifier analysis. The model never describes, scores, or labels suspected CSAM. A keyword-routed bypass triggers the referral packet structure (18 USC 2258A required fields) for human submission.
2. Every decision cites the policy clause that authorized it (DSA Art 17 statement of reasons).
3. Up to three quoted evidence spans per decision.
4. Severity 1 to 4 aligned with the documented severity-to-action map.
5. Ambiguous and policy-silent cases escalate to human review.

## Components

- Persona: `persona/trust-and-safety-reviewer`
- Knowledge pack: `knowledge-pack/platform-content-policy-frameworks` (DSA + UK OSA + COPPA + NCMEC + GIFCT + NetzDG)
- Rule pack: `rule-pack/grep-platform-moderation-flags` (10 detectors)
- Rubric: `rubric/platform-moderation-quality-v1`
- Pipeline: `pipeline/platform-content-triage`

## What this pipeline is NOT

- Not an automated CSAM detector. Suspected CSAM is routed to humans + NCMEC. The catalog does not host CSAM classifiers because deploying one without GIFCT + NCMEC + law-enforcement integration is unsafe.
- Not a legal determination engine. The pipeline applies documented policy and surfaces evidence; legal calls stay with humans.
- Not a moderation policy generator. Policy is the input; the pipeline applies it.

## Related use case

[Human-trafficking signal triage on UGC platforms](human-trafficking-ugc-detection.md) extends this pipeline with a Gemma-4 multimodal stage, Polaris/ILO trafficking indicator rule packs, and a Polaris-hotline referral path — sharing the same CSAM-route safety pattern.

## Pairing patterns

- `pattern/critical-tier-output-override` ensures CSAM-suspicion + self-harm-intent override any other classifier confidence.
- `pattern/refuse-on-redacted` ensures un-redacted PII never reaches the audit trace.
- `pattern/anti-silent-tool-failure` ensures a failed hash lookup is not treated as "no match."
- `pattern/anti-no-audit-trace` ensures every decision is reconstructible.
