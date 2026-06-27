#!/usr/bin/env python3
"""flywheel_orchestrator — rotate MULTIPLE self-improving flywheels with adaptive scheduling, for days unattended.

`--forever` runs cycle after cycle, picking the most-overdue flywheel each cycle, self-adjusting (HEALTH jumps to top
priority when a proof gate goes red; a flywheel that keeps erroring goes into cooldown), persisting state so a restart
resumes, and stopping ONLY on .agent/STOP_REQUESTED. Built so you can run it and forget about it for days.

Flywheels (DEVELOPMENT plane):
  * sweep    — one Kimi/GLM improvement+research batch (multi_model_improvement_loop) -> findings (candidates)
  * health   — run the core proof gates; signal `gates_red` if any fail (bumps itself to priority)
  * cleanup  — scan for stale/superseded docs (archive candidates) — report only (move is owner-gated)
  * status   — write a human heartbeat (data/dev-intel/flywheel-status.md) so "forget for days" stays legible

State: data/dev-intel/flywheel-state.json (cycle, per-flywheel last-cycle + error counts, health). serves_truth=false.

  --self-test           offline: scheduler picks, adjustments, cooldown, state roundtrip (no live calls)
  --run                 run ONE cycle (one flywheel)
  --forever [--max-cycles N]   run cycles until .agent/STOP_REQUESTED (the "run and forget" mode)
CLI: PYTHONPATH=. python3 scripts/flywheel_orchestrator.py --forever
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

STATE = REPO / "data" / "dev-intel" / "flywheel-state.json"
STATUS = REPO / "data" / "dev-intel" / "flywheel-status.md"
PID = REPO / "data" / "dev-intel" / "flywheel.pid"      # liveness: the --forever process writes its pid here
LOG = REPO / "data" / "dev-intel" / "flywheel.log"      # detached-run log (for --supervise)
STALE_AFTER_SEC = 900                                    # no heartbeat in 15 min => the loop is stuck/dead
STOP = REPO / ".agent" / "STOP_REQUESTED"
_HEALTH_CHECKS = ["check_plane_separation", "check_surface_map", "check_byo_compute", "check_teleon_control_plane",
                  "check_context_compressor", "check_medium_config", "check_execution_provider_factory",
                  "check_dag_pipeline", "check_teleon_example_descents", "check_descent_attempt_store",
                  # hub-automation core (all 22 hubs auto-populate via 3 channels; research descent; capability planner)
                  "check_hub_population_coverage", "check_openclaw_hermes", "check_research_catalog",
                  "check_capability_planner"]
_ERROR_COOLDOWN = 3          # after this many consecutive errors, a flywheel waits...
_COOLDOWN_CYCLES = 10        # ...this many cycles before retrying
_AUTOFIX = True              # auto-apply ONLY trivial, fully-reversible fixes unattended (--no-autofix to disable)
_AUTOFIX_CAP = 5            # at most this many auto-applied per cycle (small, reviewable batches)
_LOGJAM_COOLDOWN = 8        # cycles between logjam-breaks (don't re-fork options every cycle)
AUTO_APPLIED = REPO / "data" / "dev-intel" / "auto-applied.jsonl"


def _findings_count() -> int:
    f = REPO / "data" / "dev-intel" / "findings.jsonl"
    return sum(1 for _ in f.read_text(encoding="utf-8").splitlines() if _.strip()) if f.exists() else 0


# ── flywheel actions (each returns {summary, signal?}) ─────────────────────────────────────────────
def _fw_sweep() -> dict:
    # balanced every pass: TOP-DOWN architecture + coordination AND BOTTOM-UP modules (plus planes/wedges)
    from scripts.multi_model_improvement_loop import run_loop, enumerate_targets, load_cursor, _SWEEP_KINDS
    remaining = len([t for t in enumerate_targets(_SWEEP_KINDS) if t["id"] not in load_cursor()])
    if remaining == 0:                              # forward-looking: a finished pass re-sweeps
        from scripts.multi_model_improvement_loop import save_cursor
        save_cursor(set())
        remaining = len(enumerate_targets(_SWEEP_KINDS))
    run_loop(limit=6)
    return {"summary": f"swept a batch ({remaining} were remaining)", "signal": "ok"}


def _run_one_health(c: str) -> bool:
    try:
        r = subprocess.run([sys.executable, f"scripts/{c}.py", "--self-test"], cwd=REPO,
                           capture_output=True, text=True, timeout=180, env={**os.environ, "PYTHONPATH": "."})
        return r.returncode == 0
    except Exception:
        return False


def _health_verdict(run_fn, checks: list) -> tuple:
    """Apply the retry policy: a failing check is retried ONCE before counting it red. A health gate must not false-RED on
    a transient race (a check reading a file the sweep/hubs flywheel is mid-write) or a brief edit window — a false red
    fires a wasteful logjam-fork. A genuinely-broken check fails both runs and stays red. Pure (run_fn injected) -> testable."""
    results = {}
    for c in checks:
        ok = run_fn(c)
        if not ok:
            ok = run_fn(c)                  # one retry tolerates a concurrent-write race; a real failure persists
        results[c] = ok
    return results, [c for c, ok in results.items() if not ok]


def _fw_health() -> dict:
    results, failed = _health_verdict(_run_one_health, _HEALTH_CHECKS)
    return {"summary": f"{len(results) - len(failed)}/{len(results)} gates green" + (f"; RED: {failed}" if failed else ""),
            "signal": "gates_red" if failed else "ok", "failed": failed}


def _fw_cleanup() -> dict:
    try:
        from scripts.archive_legacy_docs import scan
        cands = scan(["docs", "research", "prompts"])
        return {"summary": f"{len(cands)} stale-doc archive candidate(s) (move is owner-gated)", "signal": "ok",
                "candidates": [c["path"] for c in cands]}
    except Exception as e:  # noqa: BLE001
        return {"summary": f"cleanup scan unavailable: {e}", "signal": "ok"}


def _fw_propose() -> dict:
    """Distill recent findings into SCORED, PRIORITIZED proposals (the comfort gate routes trivial->auto, riskier->
    propose, brand/pricing/structure->owner_gated). Report-only here; applying a proposal is the agent's call."""
    try:
        from scripts.proposal_backlog import distill_findings, prioritize, load
        n = distill_findings(40)
        prioritize()
        return {"summary": f"distilled {n} new proposal(s); backlog now {len(load())} (data/dev-intel/proposals-prioritized.md)", "signal": "ok"}
    except Exception as e:  # noqa: BLE001
        return {"summary": f"propose distill unavailable: {e}", "signal": "ok"}


def _fw_logjam(state: dict) -> dict:
    """Break a LOGJAM when the loop stalls: deliberate (Kimi/GLM + best judgment) for DIVERGENT options and FORK each
    into the scored backlog; if no clean option, capture the stall as a prioritized owner decision. Stall-triggered."""
    from scripts.stall_breaker import detect_stall, break_logjam
    reasons = detect_stall(state)
    if not reasons:
        return {"summary": "no logjam detected (forward motion ok)", "signal": "ok"}
    res = break_logjam(reasons)
    return {"summary": f"LOGJAM broken — forked {res['forked']} option(s) into the backlog [{'; '.join(reasons)}]", "signal": "ok"}


def _fw_yc() -> dict:
    """The SELF-DIRECTING flywheel: score YC readiness for the WHOLE portfolio (proof, working demo, traction,
    founder-market fit, who-needs-it, not-a-wrapper, competition, ask, RFS-fit — composing demo readiness) and FILE the
    open gaps into the proposal backlog (highest-weight first), so the loop steers the whole system toward YC."""
    try:
        from scripts.yc_readiness import compute_readiness, file_gaps, render
        r = compute_readiness()
        n = file_gaps()
        render()
        return {"summary": f"YC readiness {r['score']} ({'YC-READY' if r['ready'] else 'not yet'}); filed {n} gap(s) into the backlog",
                "signal": "ok", "score": r["score"]}
    except Exception as e:  # noqa: BLE001
        return {"summary": f"yc readiness unavailable: {e}", "signal": "ok"}


def _due_hub(cyc: int, hub_last: dict, settings_by_hub: dict) -> str | None:
    """The most-overdue ENABLED hub by its OWN cadence (a never-populated hub is due; a cadence-14 hub runs half as
    often as cadence-7). None if none is due. Pure -> testable offline."""
    best, best_overdue = None, 0.0
    for h, s in settings_by_hub.items():
        if not s.get("enabled", True):
            continue
        cad = max(1, int(s.get("cadence", 7)))
        overdue = (cyc - hub_last.get(h, cyc - cad)) / cad   # never-seen -> exactly 1.0 (due)
        if overdue >= 1.0 and overdue > best_overdue:
            best, best_overdue = h, overdue
    return best


def _fw_hubs(state: dict) -> dict:
    """Continuously POPULATE the Open*Hubs: run Teleon's 'keep this hub fresh' capability for the most-overdue hub by
    its PER-HUB cadence (honors the settings plane: enabled + cadence), using the REAL tool repository (github / HN /
    chromium JS scrape) + the strategy. The descent makes discovery cheaper over time; governed (verify gate serves)."""
    try:
        from scripts.hub_engine_runner import _engines, _tools, hub_query
        from src.openhubforai.discovery import OpenClaw, default_plugins
        from src.openhubforai.hub_settings import load_settings
        from src.teleon.hub_freshness import keep_hub_fresh
        oc = OpenClaw(default_plugins())
        hubs = sorted({p.target_hub for p in oc.plugins})
        settings_by_hub = {h: {"enabled": (s := load_settings(h)).enabled, "cadence": s.cadence} for h in hubs}
        hub_last = state.setdefault("hub_last", {})
        hub = _due_hub(state["cycle"], hub_last, settings_by_hub)
        if hub is None:
            return {"summary": "no hub due this cycle (per-hub cadence)", "signal": "ok"}
        hub_last[hub] = state["cycle"]
        r = keep_hub_fresh(hub, f"continuously update with public sources :: {hub_query(hub)}",
                           hub_engines=_engines(), openclaw=oc, tools=_tools())
        if r.get("skipped"):
            return {"summary": f"hub freshness: {hub} skipped ({r.get('reason')})", "signal": "ok"}
        return {"summary": f"hub freshness: {hub} +{r['ingested']} ingested ({r.get('verified', 0)} verified), "
                           f"descend->{r['bounded_tool']} ({r['pct_saved']}% cheaper)", "signal": "ok"}
    except Exception as e:  # noqa: BLE001
        return {"summary": f"hub freshness unavailable: {e}", "signal": "ok"}


def _record_autoapplied(records: list[dict]) -> None:
    AUTO_APPLIED.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTO_APPLIED, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps({**r, "auto_applied_by": "flywheel:autofix"}, sort_keys=True) + "\n")


def _fw_autofix() -> dict:
    """Auto-apply ONLY trivial, FULLY-REVERSIBLE fixes unattended: archive header-marked stale/superseded docs
    (lossless git mv -> archive/legacy/ + manifest + tombstone redirects; reversible via the manifest). NOTHING ELSE
    is auto-applied without the agent — code changes require the agent + the proof gates (change-verification law).
    Capped per cycle; every move recorded to an audit ledger."""
    from scripts.archive_legacy_docs import scan, apply_archive, reconcile_references, write_archive_readme
    cands = scan(["docs", "research", "prompts"])
    if not cands:
        return {"summary": "no trivial reversible fixes pending (no header-marked stale docs)", "signal": "ok"}
    batch = cands[:_AUTOFIX_CAP]
    moved = apply_archive(batch)                 # lossless: git mv + manifest, never delete
    tomb = reconcile_references()                # tombstone redirects so references never dangle
    write_archive_readme()
    _record_autoapplied(moved)
    return {"summary": f"auto-archived {len(moved)} stale doc(s) — lossless + reversible"
                       + (f", {len(tomb)} tombstoned" if tomb else "") + (f" ({len(cands) - len(batch)} more next cycle)" if len(cands) > len(batch) else ""),
            "signal": "ok", "applied": [m["original_path"] for m in moved]}


def _fw_checkpoint() -> dict:
    """Track-3 housekeeping: commit a CHECKPOINT of the working tree so the session's work never piles up uncommitted.
    SAFE by construction — commits ONLY when the last health signal was green, NEVER on the default branch, and NEVER
    pushes. Commits are reversible (git reset); messages are tagged so they're easy to squash later."""
    def git(*a):
        return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True, timeout=60,
                              env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    if load_state().get("health") != "ok":
        return {"summary": "checkpoint skipped (gates not confirmed green)", "signal": "ok"}
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if branch in ("main", "master", "HEAD", ""):
        return {"summary": f"checkpoint skipped (never auto-commit '{branch or 'detached'}')", "signal": "ok"}
    changed = [ln for ln in git("status", "--porcelain").stdout.splitlines() if ln.strip()]
    if not changed:
        return {"summary": "checkpoint: nothing to commit", "signal": "ok"}
    # only checkpoint when there's SUBSTANTIVE work — don't spam commits for the loop's own ledger churn
    substantive = [ln for ln in changed if not ln[3:].startswith("data/dev-intel/")]
    if not substantive:
        return {"summary": f"checkpoint skipped (only loop-ledger churn: {len(changed)} file(s))", "signal": "ok"}
    git("add", "-A")
    msg = (f"chore(loop): checkpoint {len(changed)} change(s) [auto]\n\n"
           "Auto-checkpoint by the flywheel loop (gates green). Squash freely.\n\n"
           "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>")
    r = git("commit", "-m", msg)
    ok = r.returncode == 0
    return {"summary": (f"checkpointed {len(changed)} change(s) on {branch}" if ok
                        else f"checkpoint commit failed: {(r.stderr or r.stdout).strip()[:80]}"), "signal": "ok"}


def _fw_status(state: dict) -> dict:
    findings = REPO / "data" / "dev-intel" / "findings.jsonl"
    n_find = sum(1 for _ in findings.read_text(encoding="utf-8").splitlines() if _.strip()) if findings.exists() else 0
    radar = REPO / "data" / "dev-intel" / "research-radar.jsonl"
    n_radar = sum(1 for _ in radar.read_text(encoding="utf-8").splitlines() if _.strip()) if radar.exists() else 0
    lines = ["# Flywheel heartbeat (development plane; serves_truth=false)", "",
             f"cycle: **{state['cycle']}** · health: **{state.get('health', 'unknown')}**",
             f"findings recorded: {n_find} · research-radar hits: {n_radar}", "",
             "## Flywheels (last cycle run / errors)"]
    for name in FLYWHEELS:
        lines.append(f"- {name}: last @ cycle {state['last'].get(name, '—')} · errors {state['errors'].get(name, 0)}")
    lines += ["", f"last flywheel: {state.get('last_flywheel', '—')} — {state.get('last_summary', '')}",
              "", "Stop with: `touch .agent/STOP_REQUESTED`"]
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"summary": f"heartbeat written ({n_find} findings, {n_radar} radar hits)", "signal": "ok"}


def _green(mod: str) -> bool:
    """Run a script's --self-test in a subprocess; True iff it exits 0. Never raises."""
    try:
        return subprocess.run([sys.executable, f"scripts/{mod}.py", "--self-test"], cwd=REPO, capture_output=True,
                              text=True, timeout=150, env={**os.environ, "PYTHONPATH": "."}).returncode == 0
    except Exception:  # noqa: BLE001
        return False


def _fw_surfaces() -> dict:
    try:
        import scripts.build_capability_assurance_surface as _cas; _cas.build()
    except Exception:  # noqa: BLE001
        pass
    """Keep the public SURFACES current: rebuild the intro site (computed counts + the task/hub catalogs auto-update)
    and the 22 hub pages, then run their self-tests. Catches drift (a registry grew but a page didn't) and keeps the
    demo fresh every cycle. Report-only (a red self-test signals; the agent/sweep improves the copy)."""
    results = {}
    for mod in ("build_intro_site", "build_hub_sites", "build_agentic_loop_viz"):
        try:
            subprocess.run([sys.executable, f"scripts/{mod}.py"], cwd=REPO, capture_output=True, text=True,
                           timeout=150, env={**os.environ, "PYTHONPATH": "."})    # rebuild from current registries
        except Exception:  # noqa: BLE001
            pass
        results[mod] = _green(mod)                                                 # validate structure
    failed = [m for m, ok in results.items() if not ok]
    return {"summary": f"surfaces rebuilt + validated ({len(results) - len(failed)}/{len(results)} green)"
                       + (f"; RED: {failed}" if failed else ""),
            "signal": "gates_red" if failed else "ok", "failed": failed}


def _fw_adapters() -> dict:
    """Keep components INTERCHANGEABLE behind agnostic wrappers: run the drop-in test (a future provider must drop in
    with zero component change) + the adapter-layers coverage audit, and file any port GAP as a comfort-gated proposal
    (idempotent — deduped by title). The loop's mechanism for 'create wrappers for selectable components'."""
    dropin, audit = _green("check_agnostic_adapters"), _green("check_adapter_layers")
    tax, reg_ok = _green("check_capability_taxonomy"), _green("check_tool_registry")
    gaps, filed, n_tools, thin = [], 0, 0, []
    _EXPAND_TARGET = 12  # candidate tools/plane to aim for on the way to "hundreds"; thinnest planes get a discovery nudge
    try:
        import json as _json
        from collections import Counter as _Counter
        layers = _json.loads((REPO / "architecture" / "adapter_layers.json").read_text(encoding="utf-8"))["layers"]
        gaps = [L["layer"] for L in layers if L.get("status") == "gap"]
        # also the TOOL PLANES (categories) not yet wrapped — the supervisor needs every category behind a plane
        planes = _json.loads((REPO / "architecture" / "tool_planes.json").read_text(encoding="utf-8"))["planes"]
        gaps += [f"{p['plane']}-plane" for p in planes if p.get("status") in ("gap", "partial")]
        from scripts.proposal_backlog import Proposal, propose
        if gaps:
            for g in gaps:
                propose(Proposal(title=f"agnostic adapter gap: add a {g} port + adapters + drop-in test", kind="opportunity",
                                 rationale="docs/architecture/agnostic-adapters.md + tool_planes.json — every tool category needs an agnostic plane the supervisor selects from"))
            filed = len(gaps)
        # registry expansion: the moat is a continuously-growing deterministic-replacement registry. Report coverage +
        # nudge discovery on the thinnest planes (STABLE title => idempotent; dynamic detail in the rationale).
        reg = _json.loads((REPO / "architecture" / "tool_registry.json").read_text(encoding="utf-8"))["tools"]
        n_tools = len(reg)
        per = _Counter(t["plane"] for t in reg)
        thin = sorted((p for p in per if per[p] < _EXPAND_TARGET), key=lambda p: per[p])
        if thin:
            propose(Proposal(title="expand the deterministic-replacement tool_registry (more candidate tools per plane)",
                             kind="opportunity",
                             rationale=f"tool_registry has {n_tools} tools; aim ~{_EXPAND_TARGET}/plane toward hundreds. "
                                       f"Thinnest now: {', '.join(f'{p}={per[p]}' for p in thin[:6])}. Feed via the discovery "
                                       "flywheels (license-classified, serves_truth=false, drop-in as one row)."))
        # ladders-for-everything coverage: which planes still lack a capability ladder (owner: ladders for EVERY subcomponent)
        all_planes = {p["plane"] for p in planes}
        laddered = {L.get("plane") for L in _json.loads((REPO / "architecture" / "capability_ladders.json").read_text(encoding="utf-8"))["ladders"]}
        no_ladder = sorted(all_planes - laddered)
        if no_ladder:
            propose(Proposal(title="add capability ladders for the remaining planes (a ladder for every subcomponent)",
                             kind="opportunity",
                             rationale=f"{len(laddered & all_planes)}/{len(all_planes)} planes have a descent ladder; "
                                       f"add next: {', '.join(no_ladder[:8])}. Each = cost-ordered deterministic-first rungs "
                                       "(architecture/capability_ladders.json)."))
    except Exception:  # noqa: BLE001
        no_ladder = []
    ok = dropin and audit and tax and reg_ok
    return {"summary": f"adapters: drop-in {'green' if dropin else 'RED'} + coverage {'green' if audit else 'RED'}; "
                       f"{len(gaps)} port gap(s){' filed' if filed else ''}; tool_registry {n_tools} tools"
                       f"{f', {len(thin)} plane(s) below target' if thin else ''}"
                       f"{f'; {len(no_ladder)} plane(s) need a ladder' if no_ladder else ''}",
            "signal": "gates_red" if not ok else "ok", "gaps": gaps}


def _fw_harvest() -> dict:
    """Scheduled tool DISCOVERY: harvest a small batch of real tools into the staged massive layer (resumable cursor,
    rate-limit-honest) + PROMOTE the license-clean ones past the boundary. Grows the registry unattended. Network-gated
    (honest no-op offline) + bounded per tick (a few queries) to respect rate limits."""
    try:
        from src.teleon.research.source_search import network_allowed
        if not network_allowed():
            return {"summary": "harvest skipped (network not allowed)", "signal": "ok"}
        import scripts.harvest_tools as _H
        import scripts.promote_tools as _PR
        h = _H.harvest(max_queries=5)
        p = _PR.promote()
        return {"summary": f"harvest +{h['new_staged']} staged ({h['total_staged']} total, cursor {h['cursor']}/{h['of']}"
                           f"{', rate-limited' if h['rate_limited'] else ''}); promote +{p['promoted']} ({p['total_promoted']} total)",
                "signal": "ok"}
    except Exception as e:  # noqa: BLE001
        return {"summary": f"harvest unavailable: {type(e).__name__}", "signal": "ok"}


#: name -> {cadence (run roughly every N cycles), fn}. The scheduler picks the most-overdue, with adjustments.
FLYWHEELS = {
    "sweep": {"cadence": 1, "fn": _fw_sweep},      # the main engine — every cycle by default
    "status": {"cadence": 3, "fn": None},          # heartbeat (needs state -> handled specially)
    "yc": {"cadence": 4, "fn": _fw_yc},            # SELF-DIRECTING: score whole-portfolio YC readiness -> file the gaps
    "propose": {"cadence": 5, "fn": _fw_propose},  # distill findings -> scored/prioritized backlog (comfort-gated)
    "hubs": {"cadence": 7, "fn": None},            # continuously POPULATE the Open*Hubs (one/cycle; needs state -> special)
    "health": {"cadence": 6, "fn": _fw_health},    # proof gates periodically (or on demand when red)
    "autofix": {"cadence": 8, "fn": _fw_autofix},  # auto-apply ONLY trivial reversible fixes (toggle: --no-autofix)
    "cleanup": {"cadence": 12, "fn": _fw_cleanup},
    "surfaces": {"cadence": 10, "fn": _fw_surfaces},  # keep the public sites fresh + validated (rebuild from registries)
    "adapters": {"cadence": 11, "fn": _fw_adapters},  # keep components swappable behind wrappers (drop-in test + gaps)
    "checkpoint": {"cadence": 15, "fn": _fw_checkpoint},  # track-3: auto-commit checkpoints when gates are green
    "harvest": {"cadence": 13, "fn": _fw_harvest},  # scheduled DISCOVERY: grow the staged tool registry + promote (network-gated)
    "logjam": {"cadence": 999, "fn": None},        # STALL-triggered only (needs state -> handled specially); not rotated
}


def load_state() -> dict:
    if STATE.exists():
        s = json.loads(STATE.read_text(encoding="utf-8"))
    else:
        s = {}
    s.setdefault("cycle", 0)
    s.setdefault("last", {})
    s.setdefault("errors", {})
    s.setdefault("health", "unknown")
    s.setdefault("health_red_streak", 0)   # consecutive health runs still RED -> a persistent logjam
    s.setdefault("no_progress", 0)          # consecutive sweeps with no new findings -> stalled
    s.setdefault("last_findings", None)     # findings count at the last sweep (to detect no-progress)
    s.setdefault("last_logjam", -999)       # cycle of the last logjam-break (cooldown so we don't re-fork every cycle)
    s.setdefault("hubs_cursor", 0)          # legacy round-robin index (superseded by per-hub cadence)
    s.setdefault("hub_last", {})            # hub_id -> cycle last populated (drives per-hub cadence in the hubs flywheel)
    return s


def save_state(s: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1), encoding="utf-8")


def pick_flywheel(state: dict) -> str:
    """Adaptive priority: (1) a red gate -> HEALTH (try to recover) until it's persistently red; (2) a persistent STALL
    -> LOGJAM (deliberate + fork options), rate-limited by a cooldown; (3) otherwise the most-overdue flywheel by
    cadence, skipping any in error cooldown. logjam is stall-triggered only (never rotated)."""
    from scripts.stall_breaker import detect_stall, _HEALTH_RED_RUNS
    cyc = state["cycle"]
    # (1) red gate -> run HEALTH to (re)verify + recover. While the streak is short, re-run every cycle (fast recovery).
    # Even at a PERSISTENT streak, periodically re-run health (every _LOGJAM_COOLDOWN cycles) so a STALE red (one already
    # fixed out of band) self-clears instead of starving recovery and letting logjam churn forks off a false stall.
    # Health is checked BEFORE logjam below, so we always re-verify the gate before escalating to a fork.
    if state.get("health") == "red" and (cyc - state["last"].get("health", -99)) >= 1:
        streak = state.get("health_red_streak", 0)
        if streak < _HEALTH_RED_RUNS or (cyc - state["last"].get("health", -99)) >= _LOGJAM_COOLDOWN:
            return "health"
    # (2) persistent stall (gates stuck red / a flywheel failing / no progress) -> break the logjam (cooldown-limited)
    if detect_stall(state) and (cyc - state.get("last_logjam", -999)) >= _LOGJAM_COOLDOWN:
        return "logjam"
    # (3) most-overdue rotation
    best, score = "sweep", -1.0
    for name, fw in FLYWHEELS.items():
        if name == "logjam":
            continue                               # stall-triggered only — not part of the rotation
        if name == "autofix" and not _AUTOFIX:
            continue                               # auto-apply disabled (--no-autofix)
        if state["errors"].get(name, 0) >= _ERROR_COOLDOWN and (cyc - state["last"].get(name, -999)) < _COOLDOWN_CYCLES:
            continue                               # in cooldown — back off
        overdue = (cyc - state["last"].get(name, -fw["cadence"])) / fw["cadence"]
        if overdue > score:
            best, score = name, overdue
    return best


def run_cycle(state: dict) -> tuple[str, dict]:
    name = pick_flywheel(state)
    try:
        if name == "status":
            res = _fw_status(state)
        elif name == "logjam":
            res = _fw_logjam(state)              # stall-breaker: needs state to read the stall reasons
        elif name == "hubs":
            res = _fw_hubs(state)                # hub population: needs state for the round-robin cursor
        else:
            res = FLYWHEELS[name]["fn"]()
        state["errors"][name] = 0
        if name == "health":
            state["health"] = "red" if res.get("signal") == "gates_red" else "ok"
            # persistent red across runs is what escalates to a logjam (vs a transient red we just fix)
            state["health_red_streak"] = (state.get("health_red_streak", 0) + 1) if state["health"] == "red" else 0
    except Exception as e:  # noqa: BLE001 — a flywheel failure NEVER stops the orchestrator
        res = {"summary": f"ERROR: {type(e).__name__}: {e}", "signal": "error"}
        state["errors"][name] = state["errors"].get(name, 0) + 1
    # stall tracking: a sweep that adds no findings = no progress; breaking a logjam resets the stall + arms the cooldown
    if name == "sweep":
        fc = _findings_count()
        state["no_progress"] = (state.get("no_progress", 0) + 1) if fc == state.get("last_findings") else 0
        state["last_findings"] = fc
    if name == "logjam":
        state["last_logjam"] = state["cycle"]
        state["no_progress"] = 0                 # forked options count as forward motion (the agent acts on them)
    state["last"][name] = state["cycle"]
    state["last_flywheel"] = name
    state["last_summary"] = res.get("summary", "")
    state["last_beat_epoch"] = time.time()       # heartbeat — the monitor reads this for liveness/staleness
    state["cycle"] += 1
    save_state(state)
    return name, res


def _alive() -> tuple[bool, int | None]:
    """Is a --forever orchestrator process running? (pidfile + a live-pid check)."""
    if not PID.exists():
        return False, None
    try:
        pid = int(PID.read_text().strip())
    except Exception:
        return False, None
    try:
        os.kill(pid, 0)                          # signal 0 = liveness probe (no actual signal sent)
        return True, pid
    except OSError:
        return False, pid                        # stale pidfile (process gone)


def _stray_daemon_pids(keep: int | None = None) -> list[int]:
    """PIDs of running '--forever' orchestrator processes other than ``keep`` (and other than this process). A prior
    manual restart can leave strays the pidfile doesn't track; supervise() uses this to enforce a SINGLE instance.
    Matches by full argv (not pkill -f, which self-matches)."""
    try:
        out = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True, timeout=10).stdout
    except Exception:  # noqa: BLE001
        return []
    pids = []
    for line in out.splitlines():
        if "flywheel_orchestrator.py" in line and "--forever" in line:
            try:
                p = int(line.split(None, 1)[0])
            except (ValueError, IndexError):
                continue
            if p != os.getpid() and p != keep:
                pids.append(p)
    return pids


def monitor() -> dict:
    """Read-only MONITOR of the flywheels: is it running, which cycle, health, heartbeat age, and the ledgers."""
    st = load_state()
    alive, pid = _alive()
    beat = st.get("last_beat_epoch")
    age = round(time.time() - beat, 1) if beat else None

    def _count(p):
        f = REPO / "data" / "dev-intel" / p
        return sum(1 for _ in f.read_text(encoding="utf-8").splitlines() if _.strip()) if f.exists() else 0
    return {"running": alive, "pid": pid, "cycle": st.get("cycle", 0), "health": st.get("health", "unknown"),
            "last_flywheel": st.get("last_flywheel"), "last_summary": st.get("last_summary", ""),
            "heartbeat_age_sec": age, "stale": (age is not None and age > STALE_AFTER_SEC),
            "findings": _count("findings.jsonl"), "research_hits": _count("research-radar.jsonl"),
            "auto_applied": _count("auto-applied.jsonl"), "errors": st.get("errors", {})}


def supervise() -> int:
    """Ensure a --forever orchestrator is RUNNING (start it detached if down/stale), then print the monitor. This is
    the `/loop` entry: it starts the flywheels and watches them, restarting if the process died."""
    alive, pid = _alive()
    # single-instance guard: kill any stray --forever daemons the pidfile doesn't track (a prior manual restart can
    # leave duplicates that would double the work + race the shared state). Keep only the tracked-alive one.
    strays = _stray_daemon_pids(keep=pid if alive else None)
    for p in strays:
        try:
            os.kill(p, 9)
        except OSError:
            pass
    if strays:
        print(f"single-instance guard: killed {len(strays)} stray daemon(s) {strays}")
    if not alive:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        # -u + PYTHONUNBUFFERED: stdout is block-buffered when redirected to a file, which would make `./loop logs`
        # (and the problem-Monitor tailing the log) show stale output until a flush. Run unbuffered so updates are LIVE.
        proc = subprocess.Popen([sys.executable, "-u", str(Path(__file__).resolve()), "--forever"], cwd=str(REPO),
                                stdout=open(LOG, "a"), stderr=subprocess.STDOUT, start_new_session=True,
                                env={**os.environ, "PYTHONPATH": ".", "PYTHONUNBUFFERED": "1"})
        print(f"started flywheel orchestrator (pid {proc.pid}) — log: {LOG.relative_to(REPO)}"
              + (f" (previous pid {pid} was gone)" if pid else ""))
    else:
        print(f"flywheel orchestrator already running (pid {pid})")
    print(json.dumps(monitor(), indent=1))
    return 0


def run_forever(*, max_cycles: int | None = None) -> int:
    state = load_state()
    PID.parent.mkdir(parents=True, exist_ok=True)
    PID.write_text(str(os.getpid()), encoding="utf-8")     # liveness for the monitor/supervisor
    ran = 0
    try:
        while True:
            if STOP.exists():
                print("STOP_REQUESTED — halting the flywheels (state preserved)."); return 0
            if max_cycles is not None and ran >= max_cycles:
                print(f"reached --max-cycles {max_cycles} (state preserved; re-run to continue)."); return 0
            name, res = run_cycle(state)
            print(f"[cycle {state['cycle']}] flywheel={name} · {res.get('summary', '')}", flush=True)
            ran += 1
    finally:
        try:
            if PID.exists() and PID.read_text().strip() == str(os.getpid()):
                PID.unlink()                                # clear our pidfile on exit (so the monitor sees it stopped)
        except Exception:
            pass


def _self_test() -> int:
    global _AUTOFIX
    import tempfile
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)
    ck("flywheels registered (sweep/status/yc/propose/hubs/health/autofix/cleanup/surfaces/adapters/checkpoint/logjam)",
       set(FLYWHEELS) == {"sweep", "status", "yc", "propose", "hubs", "health", "autofix", "cleanup", "surfaces", "adapters", "checkpoint", "harvest", "logjam"})
    ck("surfaces flywheel keeps the public sites fresh + validated", FLYWHEELS["surfaces"]["fn"] is _fw_surfaces)
    ck("adapters flywheel keeps components swappable behind wrappers (drop-in + gap proposals)", FLYWHEELS["adapters"]["fn"] is _fw_adapters)
    ck("hubs flywheel registered (continuously populates the Open*Hubs)", "hubs" in FLYWHEELS)
    ck("hubs flywheel honors PER-HUB cadence (_due_hub: most-overdue enabled hub; disabled skipped; not-due -> None)",
       _due_hub(20, {"A": 10, "B": 19}, {"A": {"enabled": True, "cadence": 7}, "B": {"enabled": True, "cadence": 7}, "C": {"enabled": False, "cadence": 7}}) == "A"
       and _due_hub(5, {"A": 4}, {"A": {"enabled": True, "cadence": 7}}) is None)
    # AUTO-APPLY flywheel: on by default, opt-out via --no-autofix, capped, audited
    ck("auto-apply flywheel registered + on by default", "autofix" in FLYWHEELS and _AUTOFIX is True)
    ck("auto-apply is capped per cycle (small reviewable batches)", _AUTOFIX_CAP <= 10)
    ck("propose flywheel registered (findings -> scored/prioritized backlog)", "propose" in FLYWHEELS and FLYWHEELS["propose"]["fn"] is _fw_propose)
    ck("SELF-DIRECTING yc flywheel registered (scores whole-portfolio YC readiness -> files gaps)", "yc" in FLYWHEELS and FLYWHEELS["yc"]["fn"] is _fw_yc)
    ck("track-3 checkpoint flywheel registered (auto-commit when green)", "checkpoint" in FLYWHEELS and FLYWHEELS["checkpoint"]["fn"] is _fw_checkpoint)
    overdue_autofix = {"cycle": 20, "last": {"sweep": 19, "status": 19, "yc": 19, "propose": 19, "hubs": 19, "health": 19, "cleanup": 19, "checkpoint": 19}, "errors": {}, "health": "ok"}
    ck("when due, autofix CAN be picked (auto progress unattended)", pick_flywheel(overdue_autofix) == "autofix", pick_flywheel(overdue_autofix))
    _AUTOFIX = False
    ck("--no-autofix disables auto-apply (never picked)", pick_flywheel(overdue_autofix) != "autofix")
    _AUTOFIX = True
    # fresh state -> sweep is most overdue
    s = {"cycle": 0, "last": {}, "errors": {}, "health": "unknown"}
    ck("a fresh cycle picks the main engine (sweep)", pick_flywheel(s) == "sweep")
    # ADJUSTMENT: health red -> health jumps to priority
    s2 = {"cycle": 5, "last": {"sweep": 4, "health": 0}, "errors": {}, "health": "red"}
    ck("ADJUSTMENT: a red gate bumps HEALTH to top priority", pick_flywheel(s2) == "health")
    # ADJUSTMENT: error cooldown skips a failing flywheel
    s3 = {"cycle": 2, "last": {"sweep": 1}, "errors": {"sweep": 3}, "health": "ok"}
    ck("ADJUSTMENT: a flywheel in error-cooldown is skipped (not picked)", pick_flywheel(s3) != "sweep")
    # cadence: cleanup becomes most-overdue eventually
    s4 = {"cycle": 30, "last": {"sweep": 29, "health": 28, "status": 29, "yc": 29, "propose": 29, "hubs": 29, "autofix": 29, "surfaces": 29, "adapters": 29, "checkpoint": 29, "harvest": 29, "cleanup": 0}, "errors": {}, "health": "ok"}
    ck("cadence makes a long-overdue flywheel (cleanup) eligible", pick_flywheel(s4) == "cleanup", pick_flywheel(s4))
    # STALL -> LOGJAM: persistent red gates (health red across enough runs) escalate from health-retry to a logjam-break
    s5 = {"cycle": 10, "last": {"health": 9}, "errors": {}, "health": "red", "health_red_streak": 3, "last_logjam": -999}
    ck("STALL: persistently-red gates escalate to a LOGJAM-break (deliberate + fork options)", pick_flywheel(s5) == "logjam", pick_flywheel(s5))
    # logjam is RATE-LIMITED: within the cooldown after a recent break, it is NOT re-fired (no churn / re-forking)
    s6 = {**s5, "last_logjam": 8}
    ck("LOGJAM is cooldown-limited (not re-fired every cycle -> no churn)", pick_flywheel(s6) != "logjam")
    # logjam is STALL-TRIGGERED ONLY: a healthy, fully-overdue state never rotates into it
    s7 = {"cycle": 50, "last": {}, "errors": {}, "health": "ok"}
    ck("LOGJAM is stall-triggered only (never picked without a stall)", pick_flywheel(s7) != "logjam")
    # STARVATION FIX: a persistent red whose health hasn't re-verified in a cooldown window RE-RUNS health (so a stale red,
    # already fixed out of band, self-clears) and is checked BEFORE logjam -> we never fork options off an already-fixed red.
    s8 = {"cycle": 20, "last": {"health": 9}, "errors": {}, "health": "red", "health_red_streak": 3, "last_logjam": 18}
    ck("STARVATION FIX: a persistent red re-verifies via HEALTH (not permanently starved by logjam)", pick_flywheel(s8) == "health", pick_flywheel(s8))
    # HEALTH gate is RACE-TOLERANT: a check that fails once then passes (a transient concurrent-write / edit window) is
    # NOT counted red -> no false logjam-fork; a check that always fails stays red (real breakage is never masked).
    _transient = iter([False, True])
    _, f_transient = _health_verdict(lambda c: next(_transient), ["t"])
    ck("HEALTH retry tolerates a transient race (fail-then-pass -> green, no false logjam)", f_transient == [])
    _, f_real = _health_verdict(lambda c: False, ["x"])
    ck("HEALTH a genuinely-broken check stays RED after the retry (breakage never masked)", f_real == ["x"])
    _, f_ok = _health_verdict(lambda c: True, ["a", "b"])
    ck("HEALTH all-pass -> no red", f_ok == [])
    # state roundtrip + status heartbeat
    with tempfile.TemporaryDirectory() as d:
        global STATE, STATUS
        _S, _U = STATE, STATUS
        try:
            STATE = Path(d) / "state.json"; STATUS = Path(d) / "status.md"
            st = load_state(); st["cycle"] = 7; save_state(st)
            ck("state roundtrips (resumable across restarts -> days unattended)", load_state()["cycle"] == 7)
            _fw_status(load_state())
            ck("status heartbeat is written (legible 'forget for days' log)", STATUS.exists() and "Flywheel heartbeat" in STATUS.read_text())
        finally:
            STATE, STATUS = _S, _U
    # MONITOR: the /loop watches the flywheels (liveness + heartbeat + ledgers)
    m = monitor()
    ck("monitor reports liveness + cycle + health + heartbeat-age + ledgers",
       all(k in m for k in ("running", "pid", "cycle", "health", "heartbeat_age_sec", "stale", "findings", "auto_applied", "errors")))
    ck("_alive() returns (bool, pid|None) for liveness", isinstance(_alive(), tuple) and isinstance(_alive()[0], bool))
    ck("supervise() is the /loop entry (start-if-down + monitor)", callable(supervise))
    ck("single-instance guard present (kills stray --forever daemons; excludes self)",
       callable(_stray_daemon_pids) and isinstance(_stray_daemon_pids(), list) and os.getpid() not in _stray_daemon_pids())
    ck("a no-heartbeat / stale loop is detectable (stale flag)", "stale" in m)
    print("\n" + ("PASS - flywheel_orchestrator: 12 flywheels (sweep/status/yc/propose/hubs/health/autofix/cleanup/surfaces/adapters/checkpoint/logjam) "
                  "on an ADAPTIVE scheduler — SELF-DIRECTING (YC readiness files its own gaps), auto-checkpoint commits when "
                  "green, health-red priority, error "
                  "cooldown, cadence, AND stall->logjam escalation (persistent red / repeated failure / no progress -> "
                  "deliberate + fork options, cooldown-limited). State-persisted + resilient, halting only on "
                  "STOP_REQUESTED — run --forever and forget it for days."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    global _AUTOFIX
    argv = sys.argv[1:] if argv is None else argv
    if "--no-autofix" in argv:
        _AUTOFIX = False
    max_cycles = None
    for i, a in enumerate(argv):
        if a == "--max-cycles" and i + 1 < len(argv):
            max_cycles = int(argv[i + 1])
    if "--self-test" in argv:
        return _self_test()
    if "--supervise" in argv:                    # the /loop entry: start the flywheels if down, then monitor
        return supervise()
    if "--monitor" in argv:                      # read-only status of the flywheels
        print(json.dumps(monitor(), indent=1))
        return 0
    if "--forever" in argv:
        return run_forever(max_cycles=max_cycles)
    if "--run" in argv:
        state = load_state()
        name, res = run_cycle(state)
        print(f"[cycle {state['cycle']}] flywheel={name} · {res.get('summary', '')}")
        return 0
    print("usage: flywheel_orchestrator.py --self-test | --supervise | --monitor | --run | --forever [--max-cycles N]")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
