# Full Proof-Suite Run — 2026-06-11

Run-don't-read execution of **every** `scripts/check_*.py` self-test plus the catalog/index/law
gates. Method: `PYTHONPATH=. python3 scripts/<check>.py --self-test` for all **393** check scripts
(every one supports `--self-test`), 12-way parallel, 120 s per-check timeout. Because every run used
`PYTHONPATH=.`, there are **no path-bootstrap (harness) artifacts** in these results — every PASS is a
real pass and every FAIL is a real assertion failure. Source files were **READ-ONLY**; the owner's
live plane (`:9301` Baltor demo, `:9410` events, `:8000` web — all confirmed up) was **not** started,
stopped, or touched. Repo HEAD at run time: `58d1f36a`.

## Headline verdict

**388 / 393 check scripts GREEN (98.7%).** All 5 failures are triaged below: **0** are real
committed *code* bugs in the proof-suite's own logic; **4** are a pre-existing committed contract drift
in the regenerated `web/` design (stale wiring assertions, active-edit `web/` zone), and **1** is an
environment/opt-in-gated runtime check that correctly fails offline. The mandated supplementary gates
(`validate.py`, `check_portfolio_dependency_law.py`) PASS; `build_component_id_index --check-fresh`
reports an expected catalog-staleness advisory.

The one check I OWN that was genuinely **drifted and failing** —
`check_adversarial_auth_all_realms.py` (hardcoded `== 12` realms vs the registry's now-25) — was
**fixed to compute the realm set from the single source** and now PASSES (verified 3×).

## TASK 1 — fixes made (no-magic-values law)

### `scripts/check_adversarial_auth_all_realms.py` — FIXED (FAIL → PASS)

Single source of the realm set: **`architecture/identity_realm_registry.json` → `realms[]`** — the same
file `scripts/identity_local_service.py:220,228` loads to build its runtimes and serve
`/api/identity/realms`. The registry grew from 12 → **25** realms (parent + Baltor + Teleon + 9 live
hubs + 13 private-bench, `updated: 2026-06-09`), but the check hardcoded `== 12`.

- **L2-7 (docstring):** "all 9 live hubs / backs all 12 realms" → "every LIVE Open*Hub … the single
  source — never hand-count the realms here".
- **L33-35 (new):** added `REGISTRY_PATH = REPO_ROOT / "architecture" / "identity_realm_registry.json"`
  with a no-magic-values rationale comment.
- **L57-67:** replaced `ck("all 12 front-end realms present", len(realms) == 12, …)` with a
  registry-driven **drift gate in both directions**:
  `declared = [r["realm_id"] for r in json.loads(REGISTRY_PATH.read_text())["realms"]]` then
  `ck(f"all {len(declared)} registry-declared front-end realms served (no drift)", set(realms) == set(declared), …)`.
  Adding/removing a realm now never breaks this check, and a realm served-but-undeclared (or vice-versa)
  now fails loudly.
- **L124-128 (PASS banner):** "9 live hubs" literal → computed `({len(declared)}: … every live hub)`.

Pattern matches the sibling `check_identity_local_service_runtime.py:90-93`, which already computes
`declared = {r["realm_id"] for r in registry["realms"]}` and asserts `served == declared`. Both checks
now independently agree on **25**. **Verified: PASS on 3 consecutive runs** (exit 0 each time).

### Audit of the rest of the grep set — no other drifted-count check found

`grep -rln 'realms|== 12|== 9|172|count ==' scripts/check_*.py` returned 21 files; a broader
`== <multi-digit>` sweep was also run. Every other hit is **legitimate** and was left unchanged
(conservative, per the task):

- **`check_ai_done_right_surface_family.py`** — *computes* `hub_count = len(LIVE_OPEN_HUBS | PRIVATE_BENCH)`
  and asserts internal consistency; `LIVE_OPEN_HUBS`/`PRIVATE_BENCH` are the **expected-roster drift
  gate** that `products.js` is validated against (CLAUDE.md: "computed by the family check, never
  hand-counted"). PASSES (9 live + 13 private; products.js matches). Not a hardcoded scalar in logic.
- **`check_identity_local_service_runtime.py`, `check_harness_hub_auth_wiring.py`,
  `check_auth_kit_realm_isolation.py`** — already read the registry / `defaults.port`; no literal counts.
- **`check_free_limited_endpoint_intel.py`, `check_inference_gateway_redteam.py`,
  `check_ollama_free_limited_compatibility.py`** — `class_code == 100/300/600/700/990`, `edge_type_code
  == 1300` are values from a **fixed governance taxonomy**, not counts that drift.
- **`check_information_retention_report.py`, `check_cfpb_*`, `check_registry_backend.py`,
  `check_worker_telemetry_schema.py`, `check_github_signal_flywheel.py`, `check_teleon_lift.py`, etc.** —
  numbers like `held_out_count == 1`, `input_count == 4`, `unsafe_count == 0`, `stars_delta_7d == 1500`,
  `p95_latency_ms == 48000`, and HTTP `== 200/201/202/405/503` are **assertions about fixture data the
  test itself constructs** or protocol constants, not external counts. No drift possible.

## TASK 2 — full proof-suite results

### Supplementary gates

| Gate | Result | Notes |
|---|---|---|
| `scripts/validate.py` (full catalog) | **PASS (exit 0)** — "all manifests valid." | Advisory findings below (non-fatal). |
| `scripts/check_portfolio_dependency_law.py --self-test` | **PASS (exit 0)** | Baltor→Teleon→OHH holds; extraction debt tracked. |
| `scripts/build_component_id_index.py --check-fresh` | **advisory (exit 1)** | `fresh:false`, reason "manifest path set changed", `component_count: 2655`. Catalog is being actively edited (16 manifests newer than the bridge); a routine `--update` refresh resolves it. Not a code bug; active-edit catalog zone. |
| `check_no_magic_values*.py` | **n/a** | No such check script exists in the repo (the law is enforced by validate.py's setting-drift advisory + per-check assertions, not a dedicated script). |

### `validate.py` advisory findings (explicitly non-blocking; build still exits 0)

1. **82 unresolved `implementations[].path` callables** (`warning: … not-yet-built stubs; pass
   `--check-impl-paths` to make these fatal`). Catalog rows point at modules that don't exist yet
   (`scripts.processors.*`, `scripts.processors.platform.*`, `scripts.db.cdc_event_emitter`,
   `scripts.db.object_embedding_batch_loader`, …). Advisory by design — these are candidate/stub rows,
   active-edit catalog zone.
2. **Database-backed catalog drift:** 16 catalog manifests newer than
   `dist/catalog-manifest-bridge/manifest_import_records.jsonl` — refresh the bridge output.
3. **Hard-coded setting drift (no-magic-values advisory):** 2 repeated model-literal groups + 4 repeated
   backend-literal groups should move to `scripts._config` / `setting_profile` rows. Migration
   candidates named: `pgvector/pgvector:pg16`, `vector.pgvector@v1`, `Qdrant`,
   `https://github.com/pgvector/pgvector`, `CLAUDE-CODE.md`. These live in `validate_compose.py`,
   `external_capability_catalog.json`, `openhubs_backend_candidate_registry.json` — **not** check
   scripts, and they are repeated-literal *advisories*, not the drifted-count class I own. Flagged for
   the owner / next wave.

### The 5 check-script FAILs (full triage)

| Check | Status | Failing assertion(s) | Triage |
|---|---|---|---|
| `check_harness_hub_auth_wiring` | FAIL (exit 1) | `A: index.html loads identity.js`; `A: identity.js loads before app.js` | **Pre-existing committed design-drift (active-edit `web/` zone).** |
| `check_events_beacon_wiring` | FAIL (exit 1) | `A: index.html loads events.js`; `A: events.js loads after data.js` | **Pre-existing committed design-drift (active-edit `web/` zone).** |
| `check_oh_states_kit` | FAIL (exit 1) | `A: index.html loads oh-states.js` | **Pre-existing committed design-drift (active-edit `web/` zone).** |
| `check_baltor_design_system` | FAIL (exit 1) | `A: SPA root is the Baltor dir-d (teal) scope` | **Pre-existing committed design-drift (active-edit `web/` zone).** |
| `check_model_plane` | FAIL (exit 1) | `A: embedding backend is PROMOTABLE (no hash fallback)`; `C: OIPS live execution switch on (OH_INFERENCE_ALLOW_NETWORK=1)` | **Environment/opt-in-gated — expected offline.** |

#### The 4 `web/` wiring failures — one shared root cause (NOT my ownership to fix)

`web/harness-hub/index.html` and `web/baltor/index.html` are **GENERATED by
`scripts/port_full_design_to_web.py`** ("transplanted design (DESIGN-CONTRACT): do not hand-edit").
Both were regenerated **2026-06-11 00:28–00:29** (today) and are **committed at HEAD** (`git diff HEAD`
is clean). The regenerated SPA loads the new kit structure — `kit/oh-identity.js`, `kit/products.js`,
`kit/oh-registry.js`, `ohh-live.js`, `oh-artifacts.jsx` — and the new SPA root scope. The 4 checks
still assert the **old hand-wired layout**: `index.html` loading `identity.js`, `events.js`,
`oh-states.js`, `data.js`, and a `dir-d` Baltor root.

- **Root cause:** the design-port regeneration **superseded** the old per-file script wiring. The old
  files still exist but are now referenced **only by `legacy.html`** — they were orphaned from
  `index.html` by the port. The 4 wiring checks were never updated to the new contract, so they were
  **already failing at the committed HEAD** (confirmed: `git show HEAD:web/harness-hub/index.html` does
  not contain `src="identity.js"`/`events.js`/`oh-states.js`/`data.js` — count 0).
- **Why not fixed here:** (1) These are not the *drifted hardcoded-value* class TASK 1 owns — they
  assert a **DOM/design contract** that a design decision changed. (2) The correct fix is a
  design-system contract decision (re-point the assertions to `kit/oh-identity.js`/`ohh-live.js` and the
  new root scope, OR have the design-port restore the old wiring, OR point the checks at `legacy.html`)
  in the **active-edit `web/` / `port_full_design_to_web.py` zone** — change-verification forbids a
  unilateral single-agent design call. **Deferred to the design-port agent / owner.**
- **Proposed fix (for the design-port owner):**
  - `scripts/check_harness_hub_auth_wiring.py:69-78` (block A) — the identity client moved into the kit;
    assert `index.html` loads `kit/oh-identity.js` (present) instead of bare `identity.js`, and drop the
    `identity.js`-before-`app.js` ordering (the new SPA has no separate `app.js` load).
  - `scripts/check_events_beacon_wiring.py:52-58` (block A) — events now flow through `ohh-live.js` /
    `kit`; assert the new emitter file rather than `events.js`-after-`data.js`.
  - `scripts/check_oh_states_kit.py:33` — `oh-states.js` is no longer loaded by `index.html`; assert the
    kit equivalent (or `legacy.html`).
  - `scripts/check_baltor_design_system.py:37` — assert the new `web/baltor/index.html` root scope class
    that `port_full_design_to_web.py` now emits.
  - Alternatively, if the old wiring is still the intended contract, the regression is in
    `port_full_design_to_web.py` dropping the script tags — fix it there and re-run the port.

  (I did NOT apply these because the new-vs-old contract is a design decision owned by the `web/` agent;
  blast radius = brand/structure → needs owner intent or design-agent corroboration, not a solo call.)

#### `check_model_plane` — environment-gated, expected offline (NOT a bug)

`scripts/check_model_plane.py:52,70` requires (A) a **promotable real embedding backend** (it observed
the offline fallback `hash/hash-bow-v1`) and (C) `os.environ["OH_INFERENCE_ALLOW_NETWORK"] == "1"` so
the OIPS gateway executes real models. Neither is present in this offline, no-network, no-models run —
so the check **correctly** fails. This is effectively **needs-env/live-execution**, not a committed
defect (block D, `/api/health reports promotable embeddings`, passed). It will go green when run with a
real embedding model installed and `OH_INFERENCE_ALLOW_NETWORK=1`. The model/inference plane is also an
**active-edit zone** (deferred regardless).

### The 388 GREEN

Every other check passed, including the substrate gates relevant to this task:
`check_adversarial_auth_all_realms` (fixed, **25 realms**), `check_identity_local_service_runtime`,
`check_auth_kit_realm_isolation`, `check_harness_hub_auth_wiring`*, `check_service_handshake_slice`,
`check_ai_done_right_surface_family`, `check_portfolio_dependency_law`,
`check_no_direct_supermemory_imports`, `check_llm_secret_hygiene`,
`check_cfpb_lossless_distillation`, `check_information_retention_report`,
`check_rule_replay_engine`, `check_rule_shadow_mode`, and ~375 more. (\* the auth-wiring check's *B/C/D*
realm-registry blocks pass; only its *A* DOM-load assertions fail per the design-drift above.)

## Health verdict

**388 / 393 proof-suite checks GREEN (98.7%)** + `validate.py` PASS + portfolio-law PASS.
No real committed *logic* bug exists in the proof suite. The one drifted-value check I own is fixed and
green. The remaining 5 reds are 4× pre-existing `web/` design-contract drift (deferred to the
active-edit design-port agent, with line-precise proposed fixes above) and 1× environment-gated model
plane check (expected offline). Catalog/index advisories are routine refresh debt in active-edit zones.

### What I changed

- `scripts/check_adversarial_auth_all_realms.py` — drifted `== 12` realm count → registry-computed
  drift gate (single source: `architecture/identity_realm_registry.json`). FAIL → PASS, verified 3×.

### Deferred (documented, NOT edited — other agents' / owner's call)

- `web/`-design wiring drift in `check_harness_hub_auth_wiring`, `check_events_beacon_wiring`,
  `check_oh_states_kit`, `check_baltor_design_system` (active-edit `web/` + `port_full_design_to_web.py`).
- `check_model_plane` env/opt-in gate (active-edit model/inference plane).
- `validate.py` advisories: 82 stub impl-paths, 16-manifest bridge drift, 6 repeated-literal setting
  migrations, `build_component_id_index` not-fresh — routine catalog refresh / next-wave.
