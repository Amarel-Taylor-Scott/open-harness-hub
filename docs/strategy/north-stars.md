# North Stars — OpenHubForAI

The canonical master goal is `docs/codex/master-goal.md`. This file crystallizes
the strategic north stars that the 2026-05-28 research arc sharpened. When a
decision is ambiguous, optimize these.

> **Architecture at a glance (the honest map):** the three-layer portfolio —
> **Baltor** (applied governed context engine) → **Teleon** (runtime / control plane) →
> **OpenHarnessHub + 22 OpenHubForAI registries** (open ecosystem + substrate), under the **AI Done Right**
> holding brand; dependency law Baltor→Teleon→OHH (enforced). **Visual + documented map:**
> [`architecture-map.md`](architecture-map.md) (and `dist/architecture/index.html`). **Adversarial
> validation + reconciliation plan:** [`architecture-validation-2026-06.md`](architecture-validation-2026-06.md).
> Regenerate the map: `python3 scripts/build_architecture_map.py --build`.

## 1. Build our own corpus aggregators for the NEGATIVE SPACE

The product is not what LLMs already know — that's the head of the distribution.
The product is the **negative space**: high-value cells that base models lack.
**Wide net** (name everything in the jurisdiction × industry × source × time ×
publisher × use-case grid) + **selective collection** (keep only confirmed gaps).
If you ask an LLM what to collect, it hands you the head; cell selection is driven
by external signals + a measured coverage map, never model priors.
→ `docs/strategy/corpus-acquisition-grid-spec.md`, `scripts/acquisition/`.

## 2. Two-axis admission: lift AND durability

A component earns a place only if (a) it lifts (`pipeline_score − bare_model_score
> 0`) AND (b) the lift is **structural** — it won't close when the next model
ships. Transient lift (a fact a bigger model absorbs, a tool you could wire) is
revenue today but depreciating inventory; never a defensibility claim. Build where
the advantage is structural: a body, a login, a license, accountability, a
deterministic verifier, or a volatile/un-ingestible source.
→ `docs/concepts/capability-valleys.md`, `scripts/eval/reason_codes.py`.

## 3. Screen before you collect

You can't run a full lift benchmark on uncollected cells. So: **cheap Stage-1
screen** (gap-likelihood, weighted toward model-INDEPENDENT signals) over the whole
net → **expensive Stage-2 confirm** (real lift on a thin sample) → scale only
confirmed gaps. The model tells you where it knows it's weak; only the external
world tells you where it's *confidently blind* — lean on the latter.
→ `docs/strategy/gap-detection-screen-spec.md`, `scripts/acquisition/gap_screen.py`.

## 4. Governance/provenance is the product (the external moat)

A better model gives a better answer; it does not give a chain of custody, a
license audit, a revocation mechanism, or an accountable signer. The lift bar is
the **internal selection criterion**; **governance is the external pitch.**
Regulated buyers pay for "I can defend this to an auditor," not "beats GPT
zero-shot" (which decays). Adopt off-the-shelf standards: C2PA-style signed
manifests, W3C VC/DID verified-publisher identity, SPDX licensing, ISO/IEC 42001 +
NIST AI RMF crosswalks, and feed EU AI Act Art. 11 evidence.

## 5. Maintenance > acquisition

An un-versioned corpus decays into the same staleness as a stale model. Every fact
carries `source_url + retrieved_at + effective_date + source_version + supersedes`.
The recurring cost — and the differentiator — is the **CDC / re-harvest /
revocation loop** that auto-flags downstream facts when upstream changes. Re-run
the gap screen each model generation (`decay_signal`) and retire collection where
the spike has closed.

## 6. Maximum flexibility + interop

Users run pipelines **on our platform (Pro) or their own**, with **our cloud models
or theirs** — env-driven provider neutrality (local now, cloud later). Be a
**governed, capability-lift-gated MCP subregistry** (cross-cloud neutral), emit
deploy bundles for the hyperscalers rather than competing on infrastructure. The
competitive window to own "the governed, lift-gated, cross-cloud component layer"
is months, not years (AWS Agent Registry et al.) — prove one wedge end-to-end with
a paying buyer.

## Value propositions (owner-stated)

1. **Valleys** — capability where base models are weak (the negative space).
2. **Streamlining** — paste a task, get a deployable, costed pipeline of components.
3. **Cost savings** — gates, routing, cheaper models on narrow scopes.
4. **Tracking** — provenance, freshness, CDC, decay signals, coverage maps.

## Safety stance (non-negotiable)

Sensitive domains (trafficking, forced labor, laundering, overcharging) are worked
**defensively only**: detection red-flags, routing-with-citations, review queues,
verified facts, signed publishers, redaction, deterministic gates. No evasion
guidance. No real PII — public/synthetic metadata only. No `_reference/` republish.
No new insurance pipelines. Detection is bidirectionally biased — carry bias review,
not just recall.
