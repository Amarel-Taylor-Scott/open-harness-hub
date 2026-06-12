# GitHub repo intel — 2026-06-12 intake batch

Eleven repos run through the governed intake engine (`scripts/repo_intel/engine.py`;
snapshots in `.agent/repo-intel/snapshots.jsonl`, facts `api_verified` via the GitHub
API except revfactory/harness which is `webfetch_github_page`). **Discovery ≠ trust:
every decision below is candidate-grade; nothing becomes active without the full
proof-to-promote ladder** (classification → duplicate check → license review →
provenance → sandbox → eval → red-team → promotion decision).

Lanes used below — *inspiration* (read the design, build our own), *template*
(structure/content we instantiate), *wrap* (run behind a port as a swappable backend;
output never truth), *integrate* (full integration candidate behind the gates).

## The batch

| Repo | Stars | License | Intake decision | Lane | Maps to (ours) |
|---|---|---|---|---|---|
| revfactory/harness | 6.8k | Apache-2.0 | intake_as_skill_candidate | template + inspiration | OpenSkillsHub / OpenHarnessHub — generates domain agent teams + skills from 6 architecture patterns (Pipeline, Fan-out/Fan-in, Expert Pool, Producer-Reviewer, Supervisor, Hierarchical Delegation). Companion paper claims +60% avg quality, n=15 author-measured — treat as unverified-until-reproduced. |
| revfactory/harness-100 | 945 | Apache-2.0 | watch | template | ~200 ready-made harness configs; thin description so the classifier saw nothing — re-classify after a content crawl. Natural follow-up to harness once it clears eval. |
| obra/superpowers | 224.9k | MIT | intake_as_skill_candidate | template + inspiration | OpenSkillsHub — the largest skills framework + methodology; mine its skill-shape conventions for our skill digestion pipeline (`shared-sandbox-and-skill-digestion`). |
| anthropics/skills | 149.5k | none/custom | **quarantine (no_license)** | template (pending) | OpenSkillsHub — official Agent Skills repo; the engine refused intake because the license is custom/unrecognized. Owner license review required before anything is copied. |
| mem0ai/mem0 | 58.4k | Apache-2.0 | intake_as_tool_candidate | wrap | `memory_distilled_write` is our deterministic core of its selective-extraction idea; mem0 itself = swappable memory backend behind ports (already tracked: competitor/complement — differentiate on governance/provability). |
| getzep/graphiti | 27.3k | Apache-2.0 | intake_as_tool_candidate | wrap | `memory_temporal_graph` implements the validity-interval semantics deterministically; Graphiti = live temporal-KG backend candidate for the same `run()` seam. |
| letta-ai/letta | 23.3k | Apache-2.0 | intake_as_tool_candidate | wrap + inspiration | `memory_agentic_hierarchy` is the deterministic page-in/page-out core of the MemGPT idea; Letta = bounded-agent runtime candidate behind ports (agents propose, never serve truth). |
| microsoft/graphrag | 33.7k | MIT | intake_as_tool_candidate | inspiration | `graphrag_retrieve` (catalog manifest; implementation queued) — follow its community/global-sensemaking split; heavy build cost, adopt the algorithm shape not the stack. |
| LMCache/LMCache | 8.5k | Apache-2.0 | watch | integrate (serving layer) | `cache_kv_reuse` is our deterministic reuse PLANNER and cites LMCache's ~7x TTFT ceiling; LMCache itself is the live KV layer when we run self-hosted inference on the Teleon plane. Thin topics → classifier saw little; re-classify when the inference plane goes live. |
| zilliztech/GPTCache | 8.1k | MIT | intake_as_tool_candidate | wrap | `cache_semantic` is the governed deterministic core (personalized-never-served, tenant-scoped); GPTCache = learned-embedding cache backend candidate behind the same `run()`. Last push 2025-07 — check maintenance before integration. |
| microsoft/LLMLingua | 6.3k | MIT | intake_as_tool_candidate | wrap | `llmlingua_compress` implements the budgeting contract with an honest deterministic scorer; LLMLingua = the learned perplexity scorer swapped behind the same seam. |

## Standing rules this batch re-confirmed

- **The engine's honesty held:** the highest-star repo in the batch (anthropics/skills)
  was quarantined on license grounds — stars are not proof, and no_license blocks intake
  regardless of provenance.
- **Pattern worth repeating:** our deterministic processors (cache/memory/retrieval
  packages, 2026-06-12 commit b9c8260f) each cite their reference repo; the reference
  repo then enters intake as the LIVE backend candidate behind the same `run()` seam.
  Deterministic core ours, learned backend theirs, one contract.
- **Re-classify thin repos after a crawl:** harness-100 and LMCache landed `watch`
  purely because their API descriptions are thin — the classifier needs content, not
  prestige.

## How to add the next repo

```bash
# facts (api_verified) → snapshot → classify → decision; never hand-write a decision
python3 - <<'PY'
from scripts.repo_intel import engine as E
repo = {"full_name": "owner/name", "description": "...", "topics": [...],
        "license": "SPDX-ID", "stars_count": 0, "forks_count": 0, "archived": False}
E.append_snapshot(repo, now="<iso8601>", source_method="github_api", source_confidence="api_verified")
cls = E.classify(repo)
print(E.intake_decision(repo, cls, E.compute_trend(repo), E.risk(repo), now="<iso8601>"))
PY
```
