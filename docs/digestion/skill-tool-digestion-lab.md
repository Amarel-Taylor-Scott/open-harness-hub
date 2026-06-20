# Skill / Tool Digestion Lab — turn skills into cheaper deterministic runtimes

**Status:** core built + proven (`scripts/check_skill_digestion.py`, flywheel-registered). Code:
`src/teleon/digestion/`. Composes the Sandbox Gateway (`src/teleon/sandbox/`) + Inference Gateway (advisory) +
Teleon PurposeTask candidates.

> **The money loop.** Observe an expensive skill → **parse it (parse-only, never execute)** → infer capability +
> I/O contracts + required tools/models → **extract deterministic substeps** → recommend a cheap→expensive
> cascade (`cache → deterministic → browser → llm → human`) → emit a **runtime candidate** (status *candidate*,
> never active) that keeps the original skill as **fallback**. Promotion needs sandbox + eval + redteam.

## Worked example (the deterministic fixture)
Skill *"research official regulatory source"* (LLM playbook + browser + search) digests to deterministic
substeps: `domain_allowlist · deterministic_source_ranking · deterministic_parser_rule · http_fetch_first ·
deterministic_conflict_holdout`, with the LLM reserved for ambiguity and the browser as fallback — i.e. a cheap
HTTP-fetch-first cascade instead of an always-LLM/always-browser path. The original skill is retained as
fallback; promotion is gated.

## Invariants (proven)
Parse-only (no `exec`/`subprocess`/`os.system` in the adapter) · unsafe skills (secret reads/exfil/log-destruction)
→ **quarantine** (never run) · digest decision is a **candidate**, never active · original kept as fallback ·
`proof_to_promote = sandbox_run + behavioral_eval + redteam + contract_validation + keep_original_fallback` ·
LLM-assist advisory only (via the Inference Gateway) · sandbox output / skill output / digest are **not truth** ·
deterministic · dependency-law clean (no `src.baltor` import).

## Contracts
`schemas/digestion/{SkillDigestRun,DeterminismExtractionReport,SkillToRuntimeCandidate}.v1` (registered).

## Built vs queued
**Built + proven:** the SKILL.md adapter (parse-only), the determinism extractor, the runtime-candidate builder,
the 3 contracts, 2 fixtures, the proof. **Queued** (`prompts/shared-sandbox-and-skill-digestion-lab.md`): more
skill-format adapters (Hermes/Codex/OpenClaw variants), tool digestion, the model-compatibility runner (real
providers), open-hub candidate-record outputs, `/api/digestion` + UI, the full redteam.
