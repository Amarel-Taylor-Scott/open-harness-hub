# Improvement Queue — the standing chain of actions (loop contract)

> The autonomous loop consumes the TOP unblocked item each iteration: execute → gate (self-tests +
> graph_flexibility) → commit with receipt → check the item off HERE in the same change → append the next
> discovered actions to the bottom. Items name their dependency; blocked items are skipped, never deleted.
> candidate/serves_truth=false discipline throughout; verified corpus files are read-only.

## Queue (top = next)

1. [x] **Usefulness gate module** — `primitive_usefulness_gate.py` built + registered + run (placeholder rates
   vf 0.213 / edge 0.62 / minted 0.78); validated by the 43-agent audit fleet (agree within 0.02–0.08);
   wave-2 fingerprints added (calls_signature_echo, mint_capability_slot). NON-DESTRUCTIVE router, not a filter.
   Commits 5e4006162 / f11bd3fa1.
2. [x] **Enrichment verify + wave 2** — wave 1 completed after the token-budget fix (195/200); graded via the
   gate (enriched 0.456→0.005 placeholder on the enriched view) AND the consumption proof (cross-session reach
   lift +0.456, 6.6×); scaled enrichment loop (`--offset`) walking the minted pool in the background. Commits
   26a53a887 / fe7f12849.
3. [x] **Gate + commit the critique fleet's landed changes** — when wf_77cd4de3-4cc completes: run the three
   owned files' self-tests + full flexibility, commit the fleet's diff with its findings summarized.
   *Dep: critique fleet.*
4. [ ] **6K-at-1M gap receipt** — commit `million_gapmap_receipt.json` when the sweep lands; compare vs the
   0.7065 base receipt; feed remaining weak capabilities into the next enrichment/mint wave. *Dep: sweep.*
5. [ ] **Soak receipt** — commit `million_soak_receipt.json` (4h endurance: p50 drift per lane mode, errors).
   *Dep: soak.*
6. [ ] **Lexical lane at 1M** — implement the depth-capped lexical walk OR begin the GIN/ES swap per the
   infra brief; target full-mode p50 < 1.5s. *Unblocked.*
7. [x] **Duplicate-title tie handling in esoteric bench** — the remaining deferred MEDIUM review finding
   (title-equal cards share known-item credit). *Unblocked.*
8. [ ] **Registers store staleness receipt** — the coverage gate's `store_text_freshness` on the 1M stores
   (corpus_text_hash now stamped); wire into the loop's iteration checklist. *Unblocked.*
9. [ ] **Fastembed serving lane** — capability_embedding path row + store rebuild on BGE-small (nDCG 1.00
   raced); A/B vs model2vec on the SaaS suite. *Unblocked, large.*
10. [ ] **Gold-set growth** — convert the SaaS/Kaggle/agentic suites + real-prompt gap clusters into graded
    relevance judgments (the standing trust lever). *Unblocked, ongoing.*
11. [ ] **Go-live transfer** — fly launch → R2 store artifacts → DNS → API keys. *Dep: OWNER accounts.*

12. [ ] **Re-run coverage receipts with de-genericized tokens** — the critique fleet fixed 9 vacuous-token capability rows (df up to 49%); the 0.86/0.9967 receipts carry bounded inflation on those rows — re-sweep and restate. *Unblocked.*
13. [~] **Scaffold-vs-scratch real bench** — built (`primitive_consumption_proof.py --real-savings`); first keyed run found the thinking-model lane SATURATES the token cap so the output-token delta is a FALSE 0 — fraction marked UNMEASURED (verify-the-verifier), the 0.4-0.7 assumption stands labelled. Follow-up: a natural-stop / non-thinking model, or measure SLM-uplift instead. Commit 12aa540fe.
14. [x] **Mint ~100K idea-primitives** (owner request) — `mint_idea_primitives.py`: axis-strided (work×CS×SWE×domain×system×problem→solution, product 35.7M); 100K at 2.4% placeholder (vs old minted 56%), 8 frames cut stamping 8.5×. Commit aca9b958f.
15. [x] **External-repo + paper intake** (owner request) — 5 repos (CubeSandbox/openwiki/repowise/reflect/ctx) + the Agent Primitives ICML-2026 paper reviewed → 6 research-queue rows; all validator+complement, wrap-don't-rebuild. Commits 6e4dc5f4b / 29fb3d6a0.

## Done (receipts in data/dev-intel/session_emulation/)

- [x] Esoteric changed-only recall (`f8ba42397`) · lift proof +0.24 · battery 918/919 · fast paths dense+registers
  (0.100s @1M) · lanes=fast mode (0.633s p50, $0.0012/1K) · enrichment engine registered · 1M pool serving.
