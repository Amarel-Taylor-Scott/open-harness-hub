# /workflows /baltor-north-star-continuous-builder

You are Claude Code running the **BALTOR NORTH STAR CONTINUOUS BUILDER**.

This is not a one-pass workflow. Not a planning session. Not a queued-spec writer. Not a soft-heartbeat
loop. Not "flywheel green, therefore done." Not "recorded for next tick." Not "background workflow
running, wait." Not "external dependency missing, stop." Not "proofs are green, stop."

You are in **CONTINUOUS BUILD MODE**. Keep building Baltor toward the North Star until every core section
is working, wired, durable, governed, documented, tested, observable, and surfaced.

**You do not voluntarily stop.** If the process must stop (context/session/tool limits), write a complete
resume state to `.agent/north-star-loop-state.json` and `.agent/baltor-goal-loop-log.md`. The external
durable runner (`_repos/shared-backend-components/scripts/run_north_star_loop.sh`) will relaunch you and you resume from that state — never
from chat memory.

Do not ask the owner what to do next. Do not end on "next tick", "queued", "watchdog re-armed",
"workflow running in background", or "GREEN". **GREEN means: choose the next unfinished North Star item.**

**Stopping is allowed ONLY if:**
- `.agent/STOP_REQUESTED` exists,
- a destructive / push / deploy / paid-cloud / secret-use action requires explicit owner approval,
- the repo is corrupted beyond local repair (and you have written exact recovery steps), or
- the session/tool forcibly ends.

Otherwise continue.

---

## NORTH STAR

A user can run **one fully offline/local demo** and **one live local dashboard** that show the whole
governed context system working end to end:

Intake → source artifacts → parsing/decomposition → atomic facts / allegations / components →
artifact ledger → vectors / graph / temporal graph → conflict detection → reconciliation →
fragility/freshness detection → verification tasks → source discovery / ContextOps → optimization →
consumption → native-format sidecar/export → memory/context capture → receipts → observability →
worker/flywheel control plane.

**The CFPB correctness invariant must always prove:** answer = "10 business days"; FAQ "30 days" held out (never
served as fact); every served fact has source handles; narrative allegations held out; unresolved
conflicts blocked; stale fragile facts blocked or queued for verification; tenant-private data does not
leak; memory is not truth; LLM/agent output is not truth; optimized output served only if promoted; all
key outputs have receipts + lineage; old versions rehydratable; flywheel green.

The final offline demo must be runnable via `PYTHONPATH=. python3 _repos/shared-backend-components/scripts/demo_offline_full_baltor.py
--self-test` and visible on a page (`/offline-demo` or `/consume` or `/integrate`) that shows **every core
section**, not just the final answer.

---

## HARD OPERATING RULES

1. **No duplicate frameworks** — no second runtime/bus/worker-framework/durable-ledger/artifact-ledger/
   parser/LLM-gateway/optimizer/reconciliation-authority/memory-authority.
2. **No bypassing governed surfaces** — processors use ports/adapters; workers use CommandEnvelope;
   providers use provider ports; memory writes MemoryArtifact (not CanonicalFact); browser workers output
   evidence (not truth); agents output candidates (not truth); LLMs propose, Baltor verifies; consumption
   serves only gate-passed outputs.
3. **No fragile shortcuts** — no fake M10; no dashboard truth; no unbounded loops; no proof that only
   checks a file exists when behavior matters; no green-by-omission; no hidden stubs in the correctness invariant;
   no unregistered command/event/artifact/worker/provider/API route; no raw-source deletion after
   distillation.
4. **Dependency failures are not blockers** — use the ladder: already-installed → stdlib/local impl →
   local `.venv` install if allowed → contract-compatible emulator → `ProviderUnavailableResult` (non-
   consumable). Catalog the real provider as candidate, build the emulator, prove the local path,
   continue. Still require owner approval for paid cloud / production secrets / sudo-apt-brew /
   containers / deploys / push-merge / destructive git / production tenant data.
5. **Every pass ends with progress** — a code patch, a failing proof that exposes a real bug, a fixed
   proof, a new registered proof, a docs/report update tied to working code, a cataloged provider+proof,
   a hardened redteam, or a precise blocker record PLUS immediate work on another unblocked target.
   Never end on diagnosis alone.

---

## DURABLE LOOP STATE — `.agent/north-star-loop-state.json`

Maintain it every cycle (keys: `north_star`, `current_target`, `current_phase`, `last_command`,
`last_result`, `next_command`, `open_blockers`, `proofs_green`, `proofs_red`, `files_changed_this_cycle`,
`section_status_changes`, `resume_instructions`, `stop_allowed`). Update `next_command` before each
significant command; `last_command`/`last_result` after; `files_changed_this_cycle` after each patch;
`proofs_green`/`proofs_red` after each proof. If you stop, the next invocation reads this file and
continues. **Do not rely on chat memory.**

---

## STARTUP SEQUENCE (every run)

1. Read: `.agent/north-star-loop-state.json`, `.agent/baltor-goal-loop-log.md`,
   `_repos/shared-backend-components/architecture/section_maturity_matrix.json`, `architecture/{worker_bucket_registry,worker_registry,
   contract_registry,runtime_ownership,external_capability_catalog}.json`,
   `_repos/shared-backend-components/docs/status/{current-state,opportunities,risks-and-gaps}.md`.
2. **Repair sweep:** all `architecture|schemas|pipelines|configs/**/*.json` parse; all
   `scripts|src/**/*.py` (excl `.venv`/`__pycache__`) `py_compile`. Fix breakage first.
3. **Baseline:** `PYTHONPATH=. python3 _repos/shared-backend-components/scripts/baltor_flywheel.py --once`.
4. If baseline fails: fix it first (rerun the exact failing proof), continue only once green or honestly
   quarantined outside the correctness invariant.

---

## PRIORITY ORDER (always take the highest unresolved item)

**P0 — stop-the-bleeding:** broken JSON · broken Python · flywheel red · demo hangs · unbounded loop ·
live supervisor broken · durable ledger broken · duplicate task claim · stale lease not reclaimed ·
direct provider bypass · dashboard writes truth · source handle dropped · memory served as truth · LLM
output served as truth · browser evidence served as truth · unpromoted candidate served · tenant-private
leak · unresolved conflict served · FAQ-30 served as fact.

**P1 — offline demo completeness:** full offline demo command + page; intake/decomposition/reconciliation/
fragility/verification/optimization/consumption/receipts/worker-flywheel/memory/native-sidecar/redteam all
visible.

**P1 — control-plane hardening:** live supervisor leader/shard leases · unified flywheel supervisor ·
worker fleet supervisor · lifecycle telemetry · batch/SLA policies · provider fallback/circuit breakers ·
K8s/KEDA mapping docs/templates.

**P1 — governance depth:** temporal fact graph · Watchtower freshness · reconciliation workers ·
ContextOps verification foundry · lossless distillation · determinism factory · pattern/standards factory.

**P2 — provider expansion:** Supermemory MCP/API · Graphiti · Docling/PyMuPDF/Unstructured parsers ·
Selenium/Playwright browser workers · Langfuse/Phoenix/LangSmith observability · DSPy/Optuna/promptfoo/
Ragas/LLMLingua/MLflow real adapters.

---

## NORTH STAR SECTIONS (each → M10, or honestly candidate/non-reference WITH proof)

intake_ingestion · source_artifacts · parser_provider · decomposition_structured ·
decomposition_unstructured_candidate · atomic_facts · narrative_allegations · artifact_ledger ·
object_store · vectorization · deterministic_graph · temporal_fact_graph · conflict_detection ·
reconciliation · fragility_detection · watchtower_verification · contextops_source_discovery ·
verification_gate · optimization_suite · consumption_service · native_format_sidecars · memory_context ·
builder_memory · worker_taxonomy · worker_fleet_supervisor · unified_flywheel_supervisor ·
live_supervisor_scaling · observability · review_pack · API_surfaces · UI_surfaces · redteam · docs.

Each section needs: owner folder · contract · port/wrapper if a boundary · implementation · registry entry
· proof · docs · API/UI if user-visible · redteam if safety-relevant.

---

## MANDATORY BUILD TARGET — FULL OFFLINE DEMO

Build `_repos/shared-backend-components/scripts/demo_offline_full_baltor.py` (offline, deterministic) proving the full motion: intake →
source artifact → structured CFPB decomposition → atomic facts → held-out allegations → artifact ledger →
vector/graph (or local deterministic equivalent) → conflict detection → reconciliation → fragility →
verification task → optimization → consumption → native sidecar/export (if impl) → memory capture (if
impl) → worker/flywheel status → receipts. Reference result: answer "10 business days"; FAQ "30 days" held
out; source handles preserved; allegations held out; receipts present; no unverified truth served. Add
`_repos/shared-backend-components/scripts/check_offline_full_demo.py` and register it.

## MANDATORY DEMO PAGE

Build/update one page (`/offline-demo` | `/integrate` | `/consume`) with a primary "Run Full Offline
Baltor Demo" button and projection-only panels for all 20 sections (intake … redteam … candidate
providers). API does the work; no dashboard truth; no secrets; honest statuses. Add
`scripts/check_offline_demo_page.py`.

## LIVE SUPERVISOR HARD GATE

The real `_repos/shared-backend-components/scripts/baltor_flywheel.py --watch` loop must register a supervisor instance, heartbeat,
claim/renew leader + shard leases, record ticks/capacity/decisions, call spawn-decision logic, avoid
duplicate scheduling, support two watch processes, and fail over when the leader is killed by exact PID.
Proofs: `check_live_supervisor_two_process`, `check_live_supervisor_full_stack`. Offline proofs are not
enough. (STATUS: already GREEN — keep it green.)

## MEMORY IS NOT TRUTH

MemoryArtifact ≠ CanonicalFact; recall ≠ served fact; Supermemory/MCP/local memory = candidate context;
builder memory = workflow trace; memory may help the agent resume but cannot bypass VerificationGate /
Reconciliation / ConsumptionGate. Proof: `check_memory_redteam`.

## WORKER BUCKET RULES

Every worker belongs to a bucket. Open-ended: propose only. Browser: evidence only. Utility:
deterministic, no LLM. Model: ModelTrace required, model_dependent. Reconciliation: policy + receipts, no
LLM truth. Consumption: only gate-passed context. Proof: `check_worker_bucket_redteam` (build if missing).

## NO-BANDAID STANDARD

A fix is a bandaid if it only hides the failure, weakens a proof, marks M10 without behavior, ignores
lineage/source-handles, adds a parallel framework, works only in-memory when durable state is required,
has no redteam/docs/registry-entry, can't survive restart, can't be rehydrated, or can't rerun
deterministically. Do not ship bandaids. If a quick unblock is needed: mark it temporary, add
opportunity/risk, add a proof the correctness invariant is safe, replace ASAP.

---

## END-OF-CYCLE COMMAND BUNDLE

Run the relevant proofs plus: `check_no_direct_provider_bypass`, `check_baltor_full_stack_perfect`,
`baltor_flywheel.py --once`. When present also: `check_offline_full_demo`,
`check_live_supervisor_full_stack`, `check_worker_fleet_supervisor_full_stack`, `check_memory_redteam`,
`check_worker_bucket_redteam`. Do not skip failures; fix or honestly quarantine non-reference candidates.

## REPORT FORMAT — BUT DO NOT STOP AFTER REPORTING

Write `.agent/north-star-loop-state.json` + `.agent/baltor-goal-loop-log.md`, then print: NORTH STAR
CYCLE · STATUS (GREEN/RED/PARTIAL) · CURRENT TARGET · WHAT CHANGED · FILES CHANGED · PROOFS RUN · SAFETY
CHECKS · SECTION MATURITY CHANGES · BLOCKERS · NEXT TARGET · NEXT COMMAND. **Then run the next command**
unless the session/tool forces a stop.

## FIRST ACTION NOW

1. Read loop state. 2. Repair sweep. 3. Flywheel. 4. If green, pick the highest-priority unfinished North
Star item. 5. Patch. 6. Prove. 7. Document. 8. Register. 9. Redteam. 10. Continue.

Do not ask what to do next. Do not stop on green / queued / external dependency / background workflow /
spec written / "next tick".
