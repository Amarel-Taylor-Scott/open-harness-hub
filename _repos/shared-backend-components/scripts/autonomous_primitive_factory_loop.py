#!/usr/bin/env python3
"""scripts.autonomous_primitive_factory_loop — a FULLY AUTONOMOUS, HEADLESS primitive-factory loop.

NO Claude Code, NO human, NO agent input. A thin orchestrator that CHAINS the existing (already-headless)
stages into one forever-loop, each stage crash-isolated as a bounded SUBPROCESS so a hung stage can never
wedge the loop:

    scrape/digest  ->  deconstruct  ->  manufacture (Hy3-heavy)  ->  synthesize+prove executors (Hy3)

One CYCLE runs, in order:
  1. scrape       continuous_primitive_scrape_loop.py --once      (governed source snapshots -> candidate feeds)
  2. deconstruct  primitive_deconstruction_plane_pipeline.py --run (fully-defined candidate rows)
  3. manufacture  hy3_overnight_flywheel.py --run --minutes M      (Hy3-FIRST minting; security-gated, candidate-only)
  4. synth        (this module) --synth-stage                      (Hy3-first + omniroute-fallback executor synthesis
                                                                    over freshly-minted needs_executor specs)

It reuses — never rebuilds — those stages. Heavy Hy3: stages 3+4 default Hy3-first (hy3 LANES[0] and the synth
lane order both lead with tencent/hy3:free); the synth stage additionally appends the local `omniroute` gateway
(236-provider auto-fallback) as a documented FALLBACK lane so the loop never stalls on rate limits.

The loop CYCLES FOREVER until the STOP file `.agent/STOP_AUTONOMOUS_FACTORY` exists (checked before every stage
AND every cycle), or a `--max-cycles N` / `--minutes M` budget is hit. Per-cycle EXPONENTIAL BACKOFF when a
cycle produces nothing. Every receipt is candidate-only (`serves_truth=false`); ids via `canonical_id`; receipts
under `data/dev-intel/autonomous_primitive_factory/`. Generated code is NEVER executed except through the
synthesizer's own gated sandbox.

    python3 scripts/autonomous_primitive_factory_loop.py --self-test     # OFFLINE, deterministic, mutation-gated
    # headless daemon (no Claude Code / no human):
    nohup python3 scripts/autonomous_primitive_factory_loop.py --run --minutes 600 --cycle-minutes 20 &
    touch .agent/STOP_AUTONOMOUS_FACTORY     # halt the whole loop      (touch .agent/STOP_HY3_FLYWHEEL = pause minting only)
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (mirrors the sibling flywheel scripts) ───────────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install, pythonpath, resource  # noqa: E402

_install()

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402
from dataclasses import dataclass, field  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"autonomous_primitive_factory_loop requires canonical_id; import failed: {exc}")

# ── constants (single source of truth; every literal named with a rationale) ──────────────────────────────────
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
RECORD_TYPE = "autonomous_primitive_factory_cycle"
_SBC = _sbc_boot                                    # shared-backend-components root == subprocess cwd for the stages
_MODULE_REL = f"scripts/{Path(__file__).name}"      # how a stage subprocess names THIS module (computed, never typed)
_DATA_SUBDIR = "data/dev-intel/autonomous_primitive_factory"
_STOP_RESOURCE = ".agent/STOP_AUTONOMOUS_FACTORY"   # the loop-wide kill switch (repo-root .agent)

#: Hy3 is the primary manufacturing/synthesis brain (free, 256K ctx, agentic). It leads every LLM lane order.
_HY3_PRIMARY_LANE: tuple[str, str] = ("openrouter", "tencent/hy3:free")
#: local OmniRoute gateway — 236-provider auto-fallback (incl. Hy3); the documented FALLBACK so we never stall.
_DEFAULT_FALLBACK_PROVIDER = "omniroute"
_OMNIROUTE_BASE_URL_DEFAULT = "http://localhost:20128/v1"

#: per-stage hard subprocess timeouts (seconds) — one hung/slow stage can NEVER wedge the loop. scrape+deconstruct
#: run deterministically (no --use-llm) so they are fast; manufacture is time-boxed by --minutes (+ join slack);
#: synth is bounded by BOTH the synthesizer's per-call 175s LLM timeout AND this hard cap.
_SCRAPE_TIMEOUT_S = 900
_DECONSTRUCT_TIMEOUT_S = 900
_SYNTH_TIMEOUT_S = 1800
_MANUFACTURE_SLACK_S = 180                          # added to cycle_minutes so the worker threads can join cleanly

#: exponential backoff between UNPRODUCTIVE cycles (a stage yielding nothing must back off, never crash/spin).
_BACKOFF_BASE_S = 30.0
_BACKOFF_CAP_S = 900.0

#: hy3 --run needs a high iteration cap so --minutes is the real bound (matches its overnight usage).
_MANUFACTURE_ITERATIONS_CAP = 100000


# ── cycle configuration (all knobs in one place) ──────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class CycleConfig:
    source_limit: int = 60                          # sources scraped/digested per cycle
    scrape_questions: int = 220                     # question bank per source (scrape stage)
    question_count: int = 360                       # deconstruction questions (deconstruct stage)
    cycle_minutes: float = 20.0                     # per-cycle Hy3 manufacturing budget (the dominant time sink)
    workers: int = 8                                # concurrent Hy3 manufacturing lanes in flight
    synth_limit: int = 12                           # needs_executor specs drained into executors per cycle
    fallback_provider: str = _DEFAULT_FALLBACK_PROVIDER
    hy3_first: bool = True
    manufacture_iterations: int = _MANUFACTURE_ITERATIONS_CAP


# ── stage definitions (data, not code paths duplicated per call site) ─────────────────────────────────────────
@dataclass(frozen=True)
class _Stage:
    name: str
    _argv: Callable[[CycleConfig], list[str]]       # python argv (sans interpreter), relative to the SBC cwd
    _timeout: Callable[[CycleConfig], int]
    yield_keys: tuple[str, ...]                     # summary keys whose sum>0 means "this stage produced something"
    lane_key: Optional[str] = None                  # summary key holding lanes used (by_lane dict | lane_order list)

    def build_argv(self, cfg: CycleConfig) -> list[str]:
        return self._argv(cfg)

    def timeout(self, cfg: CycleConfig) -> int:
        return self._timeout(cfg)


STAGES: tuple[_Stage, ...] = (
    _Stage(
        "scrape",
        lambda c: ["scripts/continuous_primitive_scrape_loop.py", "--once", "--source-limit", str(c.source_limit),
                   "--question-count", str(c.scrape_questions), "--max-components", "5",
                   "--max-sources-per-partition", "25"],
        lambda c: _SCRAPE_TIMEOUT_S, ("primitive_database_feed_rows",)),
    _Stage(
        "deconstruct",
        lambda c: ["scripts/primitive_deconstruction_plane_pipeline.py", "--run", "--question-count",
                   str(c.question_count), "--max-atlas-rows", "250", "--overlays-per-primitive", "4"],
        lambda c: _DECONSTRUCT_TIMEOUT_S, ("fully_defined_primitive_candidates",)),
    _Stage(
        "manufacture",
        lambda c: ["scripts/hy3_overnight_flywheel.py", "--run", "--iterations", str(c.manufacture_iterations),
                   "--minutes", str(c.cycle_minutes), "--workers", str(c.workers)],
        lambda c: int(c.cycle_minutes * 60) + _MANUFACTURE_SLACK_S, ("minted", "metadata_records"), "by_lane"),
    _Stage(
        "synth",
        lambda c: [_MODULE_REL, "--synth-stage", "--limit", str(c.synth_limit),
                   "--fallback-provider", c.fallback_provider],
        lambda c: _SYNTH_TIMEOUT_S, ("promoted", "validated", "certified"), "lane_order"),
)
_STAGE_NAMES: tuple[str, ...] = tuple(s.name for s in STAGES)


# ── Hy3-FIRST + omniroute-fallback chat (used by the synth stage; also proven offline in the self-test) ────────
def _lane_label(lane: tuple[str, str]) -> str:
    return f"{lane[0]}/{lane[1]}"


def build_hy3_first_chat(fallback_provider: str = _DEFAULT_FALLBACK_PROVIDER, *,
                         caller: Optional[Callable[[str, str, str, str], Any]] = None,
                         lanes: Optional[tuple[tuple[str, str], ...]] = None) -> Callable[[str, str], tuple[str, str]]:
    """A chat_fn(system, user) -> (text, lane) that tries Hy3 FIRST, then the other free flywheel lanes, then the
    local `omniroute` gateway as the last-resort fallback (so a rate-limited free tier never stalls the loop).
    `caller`/`lanes` are injectable so the ordering + fallback are proven offline with zero network."""
    if lanes is None:
        from scripts.hy3_overnight_flywheel import LANES as lanes  # noqa: PLC0415
    if caller is None:
        from scripts.hy3_overnight_flywheel import _real_chat  # noqa: PLC0415
        caller = _real_chat()
    order = ([_HY3_PRIMARY_LANE]
             + [ln for ln in lanes if ln != _HY3_PRIMARY_LANE]
             + [(fallback_provider, "auto")])

    def chat(system: str, user: str) -> tuple[str, str]:
        for prov, model in order:
            try:
                out = caller(prov, model, system, user)
            except Exception:  # noqa: BLE001 — a dead lane must never kill the run; rotate to the next
                continue
            text = out.get("text") if isinstance(out, dict) else str(out)
            if (text or "").strip():
                return text, _lane_label((prov, model))
        return "", "none"

    chat.lane_order = order  # type: ignore[attr-defined]  # exposed for the receipt + the self-test
    return chat


# ── JSON summary extraction from a stage's stdout (string-aware balanced-brace scan; last object wins) ─────────
def _json_object_spans(text: str) -> list[str]:
    spans: list[str] = []
    depth = start = 0
    started = in_str = esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start, started = i, True
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and started:
                spans.append(text[start:i + 1])
                started = False
    return spans


def _last_json_object(text: str) -> dict[str, Any]:
    for span in reversed(_json_object_spans(text or "")):
        try:
            obj = json.loads(span)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(obj, dict):
            return obj
    return {}


def _as_int(v: Any) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _lanes_from(summary: dict[str, Any], key: Optional[str]) -> list[str]:
    if not key:
        return []
    raw = summary.get(key)
    if isinstance(raw, dict):
        return sorted(str(k) for k in raw)
    if isinstance(raw, list):
        return [str(x) for x in raw]
    return []


# ── child environment for the stage subprocesses (PYTHONPATH + omniroute + best-effort .env) ──────────────────
def _source_dotenv(env: dict[str, str]) -> None:
    dotenv = _SBC.parent.parent / ".env"            # repo-root .env (gitignored); best-effort, never required
    if not dotenv.exists():
        return
    try:
        for line in dotenv.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env.setdefault(k.strip(), v.strip())
    except OSError:
        pass


def _child_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = pythonpath(".")
    env.setdefault("OMNIROUTE_BASE_URL", _OMNIROUTE_BASE_URL_DEFAULT)  # documented fallback gateway is reachable
    _source_dotenv(env)
    return env


# ── the REAL stage runner: one bounded, crash-isolated subprocess -> a uniform result dict ────────────────────
#: result contract shared by the real runner AND the self-test stubs (orchestration depends only on this shape):
#:   {"stage", "rc", "produced", "counts", "lanes", "promoted", "timed_out", "tail"}
def real_stage_runner(stage: _Stage, cfg: CycleConfig, *, cwd: Optional[str] = None,
                      env: Optional[dict[str, str]] = None,
                      runner: Callable[..., Any] = subprocess.run) -> dict[str, Any]:
    argv = [sys.executable, *stage.build_argv(cfg)]
    timeout = stage.timeout(cfg)
    timed_out = False
    try:
        proc = runner(argv, capture_output=True, text=True, timeout=timeout,
                      cwd=cwd or str(_SBC), env=env or _child_env(), check=False)
        rc, out, err = proc.returncode, (proc.stdout or ""), (proc.stderr or "")
    except subprocess.TimeoutExpired as e:                    # hard kill: a hung stage cannot wedge the loop
        rc, out, err, timed_out = 124, (e.stdout if isinstance(e.stdout, str) else "") or "", "timeout", True
    summary = _last_json_object(out) if rc == 0 else {}
    counts = {k: _as_int(summary.get(k)) for k in stage.yield_keys}
    return {"stage": stage.name, "rc": rc, "produced": sum(counts.values()), "counts": counts,
            "lanes": _lanes_from(summary, stage.lane_key), "promoted": _as_int(summary.get("promoted")),
            "timed_out": timed_out, "tail": (out + (("\n" + err) if err else ""))[-400:]}


# ── stop / state / receipt IO ─────────────────────────────────────────────────────────────────────────────────
def _stop_present(stop_path: Path) -> bool:
    return stop_path.exists()


def _loop_should_continue(*, stop_present: bool, ran: int, max_cycles: Optional[int],
                          elapsed_min: float, minutes_budget: Optional[float]) -> tuple[bool, str]:
    """The SINGLE gate deciding whether the daemon runs another cycle. Pure -> unit-testable + mutation-gated:
    if this ever ignored the STOP flag or the budgets, the self-test goes red."""
    if stop_present:
        return False, "stop_file"
    if max_cycles is not None and ran >= max_cycles:
        return False, "max_cycles"
    if minutes_budget and elapsed_min >= minutes_budget:
        return False, "minutes_budget"
    return True, "continue"


def _backoff_seconds(empty_streak: int) -> float:
    """Exponential backoff after N consecutive unproductive cycles, capped. Strictly increasing until the cap."""
    return min(_BACKOFF_BASE_S * (2 ** max(0, empty_streak - 1)), _BACKOFF_CAP_S)


def _load_state(state_path: Path) -> dict[str, Any]:
    if state_path.exists():
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 — a corrupt state file never blocks the loop; start fresh
            pass
    return {"cycle": 0}


def _save_state(state_path: Path, state: dict[str, Any]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({**state, **BOUNDARY}, sort_keys=True), encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def build_receipt(cfg: CycleConfig, cycle_no: int, run_id: str, stage_results: dict[str, dict[str, Any]],
                  stages_ran: list[str], halted: bool, *, started_ts: float, ended_ts: float) -> dict[str, Any]:
    """A candidate-only cycle receipt. PURE given its args (timestamps injected) so it builds byte-identical
    twice — the determinism gate the repo law requires."""
    produced_total = sum(_as_int(r.get("produced")) for r in stage_results.values())
    promoted = sum(_as_int(r.get("promoted")) for r in stage_results.values())
    lanes_used = sorted({lane for r in stage_results.values() for lane in r.get("lanes", [])})
    return {
        "record_type": RECORD_TYPE,
        "cycle_id": canonical_id("autonomous-primitive-factory-cycle", run_id, str(cycle_no)),
        "run_id": run_id,
        "cycle": cycle_no,
        "started_ts": round(started_ts, 3),
        "ended_ts": round(ended_ts, 3),
        "seconds": round(ended_ts - started_ts, 3),
        "stages_ran": list(stages_ran),
        "halted_by_stop": bool(halted),
        "produced_total": produced_total,
        "promoted": promoted,
        "hy3_first": bool(cfg.hy3_first),
        "primary_lane": _lane_label(_HY3_PRIMARY_LANE),
        "fallback_provider": cfg.fallback_provider,
        "lanes_used": lanes_used,
        "stages": {name: {k: r.get(k) for k in ("rc", "produced", "counts", "lanes", "promoted", "timed_out")}
                   for name, r in stage_results.items()},
        **BOUNDARY,
    }


# ── one cycle: run every stage in order, STOP-checked BEFORE each, crash-isolated ─────────────────────────────
def run_cycle(cfg: CycleConfig, cycle_no: int, run_id: str, *,
              stage_runner: Callable[[_Stage, CycleConfig], dict[str, Any]], stop_path: Path,
              clock: Callable[[], float]) -> tuple[dict[str, Any], list[str], bool]:
    started = clock()
    results: dict[str, dict[str, Any]] = {}
    ran: list[str] = []
    halted = False
    for stage in STAGES:
        if _stop_present(stop_path):                 # STOP halts the loop BEFORE the next stage
            halted = True
            break
        try:
            res = stage_runner(stage, cfg)
        except Exception as e:  # noqa: BLE001 — a stage failure NEVER stops the loop (crash isolation)
            res = {"stage": stage.name, "rc": -1, "produced": 0, "counts": {}, "lanes": [], "promoted": 0,
                   "timed_out": False, "error": f"{type(e).__name__}: {e}"[:200]}
        results[stage.name] = res
        ran.append(stage.name)
    receipt = build_receipt(cfg, cycle_no, run_id, results, ran, halted, started_ts=started, ended_ts=clock())
    return receipt, ran, halted


# ── the forever daemon ────────────────────────────────────────────────────────────────────────────────────────
def run_forever(cfg: CycleConfig, *, stage_runner: Callable[[_Stage, CycleConfig], dict[str, Any]], stop_path: Path,
                receipts_dir: Path, state_path: Path, clock: Callable[[], float] = time.time,
                sleep_fn: Callable[[float], None] = time.sleep, log: Callable[[str], None] = lambda _s: None,
                max_cycles: Optional[int] = None, minutes_budget: Optional[float] = None,
                run_id: Optional[str] = None) -> dict[str, Any]:
    receipts_dir.mkdir(parents=True, exist_ok=True)
    start = clock()
    run_id = run_id or f"autonomous-primitive-factory-{int(start)}"
    state = _load_state(state_path)
    cycle = _as_int(state.get("cycle"))
    ran = 0
    empty_streak = 0
    backoffs: list[float] = []
    last: Optional[dict[str, Any]] = None
    while True:
        cont, why = _loop_should_continue(stop_present=_stop_present(stop_path), ran=ran, max_cycles=max_cycles,
                                          elapsed_min=(clock() - start) / 60.0, minutes_budget=minutes_budget)
        if not cont:
            log(f"halt: {why} (cycles this process={ran})")
            break
        receipt, _stages_ran, halted = run_cycle(cfg, cycle, run_id, stage_runner=stage_runner,
                                                 stop_path=stop_path, clock=clock)
        _append_jsonl(receipts_dir / "cycle_receipts.jsonl", receipt)
        _write_json(receipts_dir / "latest_status.json", {**receipt, "cycles_ran_this_process": ran + 1})
        cycle += 1
        ran += 1
        _save_state(state_path, {"cycle": cycle, "run_id": run_id})
        last = receipt
        log(f"[cycle {receipt['cycle']}] produced={receipt['produced_total']} promoted={receipt['promoted']} "
            f"stages={receipt['stages_ran']} lanes={len(receipt['lanes_used'])} "
            f"halted={receipt['halted_by_stop']}")
        if halted:
            log("STOP detected mid-cycle — halting.")
            break
        if receipt["produced_total"] > 0:
            empty_streak = 0
        else:
            empty_streak += 1
            wait = _backoff_seconds(empty_streak)
            backoffs.append(wait)
            log(f"unproductive cycle — backoff {wait:.0f}s (empty streak {empty_streak})")
            sleep_fn(wait)
    return {"record_type": f"{RECORD_TYPE}_summary", "cycles_ran": ran, "final_cycle": cycle, "run_id": run_id,
            "backoffs": backoffs, "last": last, **BOUNDARY}


# ── the synth STAGE body (runs in its own subprocess so the parent hard-times-it-out) ─────────────────────────
def synth_stage_entry(*, limit: int, specs_path: Optional[str], fallback_provider: str,
                      out_path: Optional[Path] = None) -> dict[str, Any]:
    """Drain freshly-minted `needs_executor` specs into fixture-proven executors, Hy3-first with an omniroute
    fallback. Delegates disposition to the synthesizer (LLM proposes, the deterministic system + gated sandbox
    dispose); this only wires the Hy3+omniroute chat and the fresh-spec source."""
    import scripts.spec_to_executor_synthesizer as synth  # noqa: PLC0415

    chat = build_hy3_first_chat(fallback_provider)
    lane_order = [_lane_label(ln) for ln in chat.lane_order]  # type: ignore[attr-defined]
    specs = synth._load_specs(specs_path, limit)
    if not specs:
        return {"specs": 0, "promoted": 0, "validated": 0, "certified": 0, "candidate": 0, "quarantined": 0,
                "by_outcome": {}, "lane_order": lane_order, "hy3_first": True,
                "fallback_provider": fallback_provider, **BOUNDARY}
    summ = synth.run(specs, chat, out_path=out_path)
    return {**{k: summ.get(k) for k in ("specs", "promoted", "validated", "certified", "candidate",
                                        "quarantined", "by_outcome", "pool_path")},
            "lane_order": lane_order, "hy3_first": True, "fallback_provider": fallback_provider, **BOUNDARY}


# ── offline, deterministic, MUTATION-GATED self-test ──────────────────────────────────────────────────────────
def _stub_runner(*, counts_by_stage: dict[str, int], stop_path: Optional[Path] = None,
                 touch_stop_after: Optional[str] = None, lanes_by_stage: Optional[dict[str, list[str]]] = None,
                 promoted: int = 0) -> Callable[[_Stage, CycleConfig], dict[str, Any]]:
    """A STUB stage runner: no subprocess, no network, no LLM — returns the real runner's result shape so the
    orchestration is exercised in isolation. Can plant a STOP file right after a chosen stage (STOP-honoring gate)."""
    def runner(stage: _Stage, _cfg: CycleConfig) -> dict[str, Any]:
        if touch_stop_after and stage.name == touch_stop_after and stop_path is not None:
            stop_path.parent.mkdir(parents=True, exist_ok=True)
            stop_path.write_text("stop")
        produced = counts_by_stage.get(stage.name, 0)
        return {"stage": stage.name, "rc": 0, "produced": produced,
                "counts": {stage.yield_keys[0]: produced}, "lanes": (lanes_by_stage or {}).get(stage.name, []),
                "promoted": promoted if stage.name == "synth" else 0, "timed_out": False, "tail": "stub"}
    return runner


def _counter_clock() -> Callable[[], float]:
    box = {"t": 0.0}

    def _clk() -> float:
        box["t"] += 1.0
        return box["t"]
    return _clk


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []

    def ck(name: str, ok: bool) -> None:
        checks.append((name, bool(ok)))

    cfg = CycleConfig()
    productive = {"scrape": 4, "deconstruct": 3, "manufacture": 5, "synth": 2}

    # 1) a FULL cycle runs all 4 stages IN ORDER; the receipt is candidate-only and aggregates production/promotion
    with tempfile.TemporaryDirectory() as td:
        stop = Path(td) / "STOP"
        run = _stub_runner(counts_by_stage=productive, lanes_by_stage={"manufacture": ["openrouter/tencent/hy3:free"],
                                                                       "synth": ["openrouter/tencent/hy3:free",
                                                                                 "omniroute/auto"]}, promoted=2)
        receipt, ran, halted = run_cycle(cfg, 0, "rid", stage_runner=run, stop_path=stop, clock=_counter_clock())
    ck("a full cycle runs all 4 stages IN ORDER (scrape->deconstruct->manufacture->synth)",
       ran == list(_STAGE_NAMES) and not halted)
    ck("receipt is candidate-only (serves_truth=false)", receipt["candidate"] is True and receipt["serves_truth"] is False)
    ck("receipt aggregates produced_total + promoted across stages",
       receipt["produced_total"] == sum(productive.values()) and receipt["promoted"] == 2)
    ck("receipt records Hy3-first + omniroute fallback + the lanes used",
       receipt["hy3_first"] is True and receipt["primary_lane"] == "openrouter/tencent/hy3:free"
       and receipt["fallback_provider"] == "omniroute" and "omniroute/auto" in receipt["lanes_used"])

    # 2) the STOP file halts the loop BEFORE the next stage (mutation gate: remove the check -> all 4 run -> red)
    with tempfile.TemporaryDirectory() as td:
        stop = Path(td) / "STOP"
        run = _stub_runner(counts_by_stage=productive, stop_path=stop, touch_stop_after="scrape")
        receipt2, ran2, halted2 = run_cycle(cfg, 0, "rid", stage_runner=run, stop_path=stop, clock=_counter_clock())
    ck("STOP planted after stage 1 halts the loop BEFORE stage 2 (only 'scrape' ran)",
       ran2 == ["scrape"] and halted2 is True)
    ck("the stop predicate refuses to continue when STOP is present",
       _loop_should_continue(stop_present=True, ran=0, max_cycles=None, elapsed_min=0.0,
                             minutes_budget=None) == (False, "stop_file"))

    # 3) --max-cycles is honored exactly; the cycle counter persists (resumable across restarts)
    with tempfile.TemporaryDirectory() as td:
        rd, sp = Path(td) / "receipts", Path(td) / "state.json"
        summ = run_forever(cfg, stage_runner=_stub_runner(counts_by_stage=productive), stop_path=Path(td) / "NONE",
                           receipts_dir=rd, state_path=sp, clock=_counter_clock(), sleep_fn=lambda _s: None,
                           max_cycles=2, run_id="rid")
        lines = (rd / "cycle_receipts.jsonl").read_text().splitlines()
        saved_cycle = json.loads(sp.read_text())["cycle"]
    ck("--max-cycles 2 runs exactly 2 cycles and writes 2 receipts", summ["cycles_ran"] == 2 and len(lines) == 2)
    ck("cycle counter persists to state (resumable)", saved_cycle == 2)
    ck("the budget predicate stops at the cycle cap",
       _loop_should_continue(stop_present=False, ran=2, max_cycles=2, elapsed_min=0.0,
                             minutes_budget=None) == (False, "max_cycles"))

    # 4) receipts are DETERMINISTIC (byte-identical build twice given the same inputs)
    sr = {"scrape": {"produced": 4, "promoted": 0, "lanes": [], "counts": {}, "rc": 0, "timed_out": False},
          "synth": {"produced": 2, "promoted": 2, "lanes": ["omniroute/auto"], "counts": {}, "rc": 0, "timed_out": False}}
    r1 = build_receipt(cfg, 7, "rid", sr, ["scrape", "synth"], False, started_ts=10.0, ended_ts=12.5)
    r2 = build_receipt(cfg, 7, "rid", sr, ["scrape", "synth"], False, started_ts=10.0, ended_ts=12.5)
    ck("cycle receipt is deterministic (byte-identical twice)",
       json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True))
    ck("deterministic receipt is still candidate-only + canonical-id'd",
       r1["candidate"] is True and r1["serves_truth"] is False and r1["cycle_id"].startswith("autonomous-primitive-factory-cycle-"))

    # 5) a cycle that yields NOTHING triggers exponential BACKOFF (not a crash), and never spins
    with tempfile.TemporaryDirectory() as td:
        sleeps: list[float] = []
        summ_e = run_forever(cfg, stage_runner=_stub_runner(counts_by_stage={}), stop_path=Path(td) / "NONE",
                             receipts_dir=Path(td) / "r", state_path=Path(td) / "s.json", clock=_counter_clock(),
                             sleep_fn=sleeps.append, max_cycles=3, run_id="rid2")
    ck("3 empty cycles ran without crashing and each backed off",
       summ_e["cycles_ran"] == 3 and sleeps == [_backoff_seconds(1), _backoff_seconds(2), _backoff_seconds(3)])
    ck("backoff is strictly increasing then capped (mutation gate on the backoff curve)",
       _backoff_seconds(1) < _backoff_seconds(2) < _backoff_seconds(3) and _backoff_seconds(999) == _BACKOFF_CAP_S)

    # 6) HEAVY Hy3: the synth chat is Hy3-FIRST with omniroute as the LAST-RESORT fallback (proven offline)
    seen: list[tuple[str, str]] = []

    def _cap_hy3(prov: str, model: str, _s: str, _u: str) -> dict[str, Any]:
        seen.append((prov, model))
        return {"text": "OK"} if (prov, model) == _HY3_PRIMARY_LANE else {"text": ""}

    chat = build_hy3_first_chat("omniroute", caller=_cap_hy3,
                                lanes=(("openrouter", "tencent/hy3:free"), ("nvidia", "z-ai/glm-5.2")))
    text, lane = chat("s", "u")
    ck("chat lane order LEADS with Hy3 and ENDS with the omniroute fallback",
       chat.lane_order[0] == _HY3_PRIMARY_LANE and chat.lane_order[-1] == ("omniroute", "auto"))
    ck("Hy3 answers first -> its lane is chosen (Hy3-heavy)", lane == "openrouter/tencent/hy3:free" and text == "OK")

    def _cap_only_omni(prov: str, _m: str, _s: str, _u: str) -> dict[str, Any]:
        return {"text": "FB"} if prov == "omniroute" else {"text": ""}

    text_fb, lane_fb = build_hy3_first_chat("omniroute", caller=_cap_only_omni)("s", "u")
    ck("when every free lane is empty, omniroute is the working fallback (never stalls)",
       lane_fb == "omniroute/auto" and text_fb == "FB")

    # 7) stage wiring integrity + STOP/data conventions
    ck("stages chain scrape->deconstruct->manufacture->synth", list(_STAGE_NAMES) == ["scrape", "deconstruct", "manufacture", "synth"])
    ck("manufacture reuses hy3_overnight_flywheel --run (Hy3-first minting)",
       "hy3_overnight_flywheel.py" in " ".join(STAGES[2].build_argv(cfg)) and "--run" in STAGES[2].build_argv(cfg))
    ck("synth stage runs THIS module's gated --synth-stage (never execs generated code itself)",
       STAGES[3].build_argv(cfg)[0] == _MODULE_REL and "--synth-stage" in STAGES[3].build_argv(cfg))
    ck("scrape+deconstruct reuse the real scrape/deconstruct CLIs",
       "continuous_primitive_scrape_loop.py" in " ".join(STAGES[0].build_argv(cfg))
       and "primitive_deconstruction_plane_pipeline.py" in " ".join(STAGES[1].build_argv(cfg)))
    ck("STOP file is .agent/STOP_AUTONOMOUS_FACTORY; receipts under data/dev-intel/autonomous_primitive_factory",
       _STOP_RESOURCE.endswith("STOP_AUTONOMOUS_FACTORY") and _DATA_SUBDIR.endswith("autonomous_primitive_factory"))
    ck("stdout summary parser returns the LAST json object (counts survive stage preamble/epilogue lines)",
       _last_json_object('preamble\n{"a": 1}\n{"minted": 9, "by_lane": {"openrouter/x": 3}}\nwritten: /x')
       == {"minted": 9, "by_lane": {"openrouter/x": 3}})

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - autonomous_primitive_factory_loop: a headless forever-loop CHAINS scrape -> deconstruct -> "
          "Hy3 manufacture -> Hy3+omniroute executor-synthesis, each stage a bounded crash-isolated subprocess; "
          "STOP-gated (before every stage), --max-cycles/--minutes bounded, exponential backoff on empty cycles, "
          "candidate-only deterministic receipts. Offline, no Claude Code / human / agent input. serves_truth=false.")
    return 0


# ── CLI ───────────────────────────────────────────────────────────────────────────────────────────────────────
def _run_daemon(args: argparse.Namespace) -> int:
    cfg = CycleConfig(source_limit=args.source_limit, scrape_questions=args.scrape_questions,
                      question_count=args.question_count, cycle_minutes=args.cycle_minutes, workers=args.workers,
                      synth_limit=args.synth_limit, fallback_provider=args.fallback_provider)
    stop_path = resource(_STOP_RESOURCE)
    receipts_dir = resource(_DATA_SUBDIR)
    state_path = receipts_dir / "state.json"
    print(f"autonomous_primitive_factory_loop: HEADLESS (no Claude Code / human / agent). "
          f"Hy3-first={cfg.hy3_first} fallback={cfg.fallback_provider} | cycle_minutes={cfg.cycle_minutes} "
          f"workers={cfg.workers} synth_limit={cfg.synth_limit} | budget: minutes={args.minutes or '∞'} "
          f"max_cycles={args.max_cycles or '∞'} | STOP: touch {stop_path}", flush=True)
    summ = run_forever(cfg, stage_runner=real_stage_runner, stop_path=stop_path, receipts_dir=receipts_dir,
                       state_path=state_path, log=lambda s: print(s, flush=True),
                       max_cycles=(args.max_cycles or None), minutes_budget=(args.minutes or None))
    print(json.dumps({k: summ[k] for k in ("cycles_ran", "final_cycle", "run_id", "backoffs")}, indent=2))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true", help="offline, deterministic, mutation-gated proof")
    ap.add_argument("--run", action="store_true", help="the real headless forever daemon")
    ap.add_argument("--synth-stage", action="store_true", help="internal: run ONE Hy3+omniroute synth pass (a stage subprocess)")
    ap.add_argument("--status", action="store_true", help="print the latest cycle receipt")
    # daemon budgets + knobs
    ap.add_argument("--minutes", type=float, default=0.0, help="total daemon wall-clock budget (0 = forever)")
    ap.add_argument("--max-cycles", type=int, default=0, help="stop after N cycles (0 = unbounded)")
    ap.add_argument("--cycle-minutes", type=float, default=CycleConfig.cycle_minutes, help="per-cycle Hy3 manufacturing budget")
    ap.add_argument("--source-limit", type=int, default=CycleConfig.source_limit)
    ap.add_argument("--scrape-questions", type=int, default=CycleConfig.scrape_questions)
    ap.add_argument("--question-count", type=int, default=CycleConfig.question_count)
    ap.add_argument("--workers", type=int, default=CycleConfig.workers)
    ap.add_argument("--synth-limit", type=int, default=CycleConfig.synth_limit)
    ap.add_argument("--fallback-provider", default=_DEFAULT_FALLBACK_PROVIDER)
    # synth-stage args
    ap.add_argument("--limit", type=int, default=CycleConfig.synth_limit, help="synth-stage: needs_executor specs to drain")
    ap.add_argument("--specs", default=None, help="synth-stage: explicit JSONL of needs_executor spec cards")
    args = ap.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.synth_stage:
        res = synth_stage_entry(limit=args.limit, specs_path=args.specs, fallback_provider=args.fallback_provider)
        print(json.dumps(res, indent=2, sort_keys=True))
        return 0
    if args.status:
        latest = resource(_DATA_SUBDIR) / "latest_status.json"
        print(latest.read_text(encoding="utf-8") if latest.exists() else json.dumps({"status": "no cycles yet"}))
        return 0
    if args.run:
        return _run_daemon(args)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
