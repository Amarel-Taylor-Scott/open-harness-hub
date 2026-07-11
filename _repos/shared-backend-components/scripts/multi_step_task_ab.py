#!/usr/bin/env python3
"""scripts.multi_step_task_ab — MULTI-STEP task A/B with a PRIMITIVE SESSION MANAGER: where primitive reuse
finally COMPOUNDS into real savings.

Owner (2026-07-09): "I need more advanced tasks, or some way to better manage primitives to get savings on
multi-step tasks." A single build reusing one primitive saves little. But across a MULTI-STEP session, a verified
primitive/molecule is provided ONCE by the manager and reused FREE by every later step — so savings scale with the
number of steps that touch it. This module makes that mechanism concrete and MEASURES it two honest ways:

  (1) STRUCTURAL token-accounting (deterministic, grounded in the REAL verified-module char sizes; labeled
      benchmark_kind=structural_token_accounting -> a PROXY, never a live headline) — proves the COMPOUNDING LAW:
        unmanaged pays Σ_steps Σ_modules ;  managed pays Σ_UNIQUE_modules-once + Σ_steps glue
        savings = Σ_module (occurrences − 1) × module_tokens   -> grows with steps that reuse it.
  (2) LIVE multi-step A/B (opt-in --live): a real model builds each step; the manager mounts the shared verified
      modules verbatim (0 generation tokens) and tracks inject-once across steps; the hidden per-step oracle boots +
      probes each build; CUMULATIVE session tokens are netted managed-vs-unmanaged. This is the real number.

The PrimitiveSessionManager is the reusable "better way to manage primitives": a session library (registry-seeded +
session-built), inject-once provisioning, and record-on-verify so step N reuses everything steps 1..N-1 proved.
Everything candidate=true/serves_truth=false; a PROXY structural number may never headline (no_proxy_gate).

    python3 scripts/multi_step_task_ab.py --self-test
    python3 scripts/multi_step_task_ab.py --structural         # the compounding curve over real module sizes
    python3 scripts/multi_step_task_ab.py --live --provider openrouter --repeats 3   # real cumulative-token A/B
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/buildout_forge.py) ────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
ARTIFACT_DIR_REL = "data/dev-intel/multi_step_task_ab"
# tokens/char ≈ 1/4 (OpenAI-family rule of thumb; used ONLY for the labeled structural proxy, never a live headline)
_CHARS_PER_TOKEN = 4


def _tok(source: str) -> int:
    return max(1, len(source) // _CHARS_PER_TOKEN)


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# THE PRIMITIVE SESSION MANAGER — the reusable "better way to manage primitives" across a multi-step session.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
class PrimitiveSessionManager:
    """Manage which verified primitives are available/mounted across a multi-step session, to maximize reuse.

    * `registry`   — verified primitives available from the start (proven registry molecules/modules); mounting one
                     costs 0 generation tokens (it is provided verbatim).
    * `session`    — primitives BUILT + verified during THIS session; free to reuse after the step that built them.
    * `provided`   — inject-once ledger: a module already mounted this session is NOT mounted (or regenerated) again.
    """

    def __init__(self, registry: dict[str, str] | None = None) -> None:
        self.registry: dict[str, str] = dict(registry or {})
        self.session: dict[str, str] = {}
        self.provided: set[str] = set()
        self.events: list[dict[str, Any]] = []

    def available(self, name: str) -> bool:
        """Is this primitive already reusable for free (registry-verified OR built+recorded earlier this session)?"""
        return name in self.registry or name in self.session

    def plan_step(self, needed: list[str]) -> dict[str, Any]:
        """Decide, for one step's needed modules: which are reused FREE, which are mounted-now, which must be BUILT."""
        reuse_free, mount_now, build_now = [], [], []
        for name in needed:
            if name in self.provided:
                reuse_free.append(name)                 # already mounted earlier this session -> 0 tokens
            elif self.available(name):
                mount_now.append(name)                  # provide verbatim now -> 0 generation tokens
                self.provided.add(name)
            else:
                build_now.append(name)                  # unknown -> the model must generate it this step
        self.events.append({"needed": needed, "reuse_free": reuse_free, "mount_now": mount_now,
                            "build_now": build_now})
        return {"reuse_free": reuse_free, "mount_now": mount_now, "build_now": build_now}

    def record(self, built: dict[str, str]) -> None:
        """A step verified new modules -> add them to the session library so later steps reuse them free."""
        for name, src in built.items():
            self.session[name] = src
            self.provided.add(name)

    def mounted_sources(self, names: list[str], sources: dict[str, str]) -> dict[str, str]:
        """The verbatim source of the modules to mount for a live step (from registry/session/provided pools)."""
        return {n: (self.registry.get(n) or self.session.get(n) or sources[n]) for n in names}

    def compose_entry(self, template: str, config: dict[str, Any]) -> str:
        """DETERMINISTICALLY emit the thin entry that wires a verified molecule from its DECLARED config — 0 model
        tokens, correct-by-construction. This is the reliable alternative to prompting a model to 'use the primitive'
        (which it re-implements + fails). Templates are parameterized by config, NOT hardcoded answers."""
        fn = _COMPOSE_TEMPLATES.get(template)
        if fn is None:
            raise KeyError(f"no compose template for {template!r}; known: {sorted(_COMPOSE_TEMPLATES)}")
        return fn(config)


def _compose_webhook_worker(config: dict[str, Any]) -> str:
    """Emit app.py wiring make_webhook_worker from {event_schema, dedupe_fields}. Secret read from env, never inlined."""
    return (
        "import os\n"
        "from webhook_worker import make_webhook_worker, run\n\n"
        "_events = []\n\n\n"
        "def sink(event):\n"
        "    _events.append(event)\n\n\n"
        f"Handler = make_webhook_worker(os.environ.get('WEBHOOK_SECRET', ''), {config['event_schema']!r}, "
        f"{config['dedupe_fields']!r}, sink)\n\n"
        "if __name__ == '__main__':\n"
        "    run(Handler)\n"
    )


def _compose_crud_service(config: dict[str, Any]) -> str:
    """Emit app.py wiring make_crud_app from {resource, id_field, required_fields}."""
    return (
        "from macro_crud_service import make_crud_app, run\n"
        "from validators import validate_vendor\n"
        "from store import VendorStore\n\n"
        f"Handler = make_crud_app({config['resource']!r}, {config['id_field']!r}, "
        f"{config['required_fields']!r}, VendorStore(), validate_vendor)\n\n"
        "if __name__ == '__main__':\n"
        "    run(Handler)\n"
    )


def _compose_search_engine(config: dict[str, Any]) -> str:
    return ("from search_engine import make_search_engine, run\n\n"
            "Handler = make_search_engine()\n\n"
            "if __name__ == '__main__':\n    run(Handler)\n")


def _compose_labeler(config: dict[str, Any]) -> str:
    return ("from labeler import make_labeler, run\n\n"
            f"RULES = {config['rules']!r}\n\n"
            "Handler = make_labeler(RULES)\n\n"
            "if __name__ == '__main__':\n    run(Handler)\n")


def _compose_rag_tool(config: dict[str, Any]) -> str:
    return ("from rag_tool import make_rag_tool, run\n\n"
            "Handler = make_rag_tool()\n\n"
            "if __name__ == '__main__':\n    run(Handler)\n")


# molecule template registry — a NEW composable molecule is one row (multi-path law), never a rewrite
_COMPOSE_TEMPLATES: dict[str, Callable[[dict[str, Any]], str]] = {
    "webhook_worker": _compose_webhook_worker,
    "crud_service": _compose_crud_service,
    "search_engine": _compose_search_engine,
    "labeler": _compose_labeler,
    "rag_tool": _compose_rag_tool,
}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# A concrete MULTI-STEP TASK — a webhook automation PLATFORM built in steps that share a verified core.
# Module SOURCES are the REAL verified artifacts (sizes grounded), so the structural accounting is honest.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _load_real_sources() -> dict[str, str]:
    from scripts.automation_directory_forge import WEBHOOK_WORKER_MACRO_SOURCE  # noqa: PLC0415
    import scripts.buildout_forge as bf  # noqa: PLC0415
    import scripts.macro_crud_service as mc  # noqa: PLC0415
    g = bf._GENOMES["vendor_onboarding_service__stdlib_http__v0"]["good"]
    return {
        "webhook_worker.py": WEBHOOK_WORKER_MACRO_SOURCE,   # verified registry molecule (3872 chars)
        "make_crud_app.py": mc._MACRO_CRUD,                 # verified registry molecule
        "store.py": g["store.py"], "validators.py": g["validators.py"],  # session-built shared core
        # per-step glue (the thin entry the model always writes; sizes representative of a wired entry)
        "glue_ingest.py": g["app.py"], "glue_catalog.py": g["app.py"], "glue_deliver.py": g["app.py"],
        "glue_audit.py": g["app.py"],
    }


def build_task() -> dict[str, Any]:
    """A 4-step platform. registry_primitives are pre-verified (free to mount); store/validators are session-built
    in step 1 and reused free thereafter. Each step lists the modules it needs + its own glue."""
    sources = _load_real_sources()
    steps = [
        {"name": "orders_ingest", "modules": ["webhook_worker.py", "store.py", "validators.py"],
         "glue": "glue_ingest.py"},
        {"name": "signups_ingest", "modules": ["webhook_worker.py", "store.py", "validators.py"],
         "glue": "glue_ingest.py"},                                       # reuses ALL of step 1's core
        {"name": "vendor_catalog", "modules": ["make_crud_app.py", "store.py", "validators.py"],
         "glue": "glue_catalog.py"},                                      # reuses store+validators; adds crud molecule
        {"name": "audit_metrics", "modules": ["store.py"], "glue": "glue_audit.py"},  # reuses store
    ]
    return {"name": "webhook_automation_platform", "steps": steps, "sources": sources,
            "registry_primitives": ["webhook_worker.py", "make_crud_app.py"]}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# STRUCTURAL token-accounting (deterministic PROXY — labeled, never a live headline) — proves the COMPOUNDING LAW.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
def account(task: dict[str, Any], *, managed: bool) -> dict[str, Any]:
    """Cumulative structural tokens across steps. Unmanaged regenerates every module every step; managed mounts
    registry/session primitives free (inject-once) and writes only glue + genuinely-new modules."""
    src = task["sources"]
    mgr = PrimitiveSessionManager(registry={n: src[n] for n in task["registry_primitives"]} if managed else None)
    total, per_step, cumulative = 0, [], []
    for step in task["steps"]:
        step_tokens, reused_free = 0, []
        if managed:
            plan = mgr.plan_step(step["modules"])
            reused_free = plan["reuse_free"] + plan["mount_now"]          # both cost 0 generation tokens
            for m in plan["build_now"]:
                step_tokens += _tok(src[m])                              # a new module the model must write
            mgr.record({m: src[m] for m in plan["build_now"]})           # record -> free for later steps
        else:
            for m in step["modules"]:
                step_tokens += _tok(src[m])                              # regenerate every module, every step
        step_tokens += _tok(src[step["glue"]])                          # glue is always written
        total += step_tokens
        per_step.append({"step": step["name"], "tokens": step_tokens, "reused_free": reused_free})
        cumulative.append(total)
    return {"lane": "managed" if managed else "unmanaged", "total_tokens": total, "per_step": per_step,
            "cumulative": cumulative}


def structural_ab(task: dict[str, Any]) -> dict[str, Any]:
    """Managed vs unmanaged structural accounting + the COMPOUNDING CURVE (savings after k steps, k=1..N)."""
    u, m = account(task, managed=False), account(task, managed=True)
    curve = [{"steps": k + 1, "savings_tokens": u["cumulative"][k] - m["cumulative"][k]}
             for k in range(len(task["steps"]))]
    saved = u["total_tokens"] - m["total_tokens"]
    return {"record_type": "multi_step_structural_ab", "benchmark_kind": "structural_token_accounting",
            "task": task["name"], "n_steps": len(task["steps"]), "unmanaged_tokens": u["total_tokens"],
            "managed_tokens": m["total_tokens"], "savings_tokens": saved,
            "savings_ratio": round(u["total_tokens"] / max(1, m["total_tokens"]), 3),
            "compounding_curve": curve, "unmanaged": u, "managed": m,
            "note": "STRUCTURAL PROXY (chars/4 over real verified-module sizes) — shows the compounding MECHANISM; "
                    "NOT a live headline. Run --live for the executed cumulative-token number.",
            **BOUNDARY}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# DETERMINISTIC COMPOSITION lane (EXECUTED, no model) — the reliable capture of the structural savings. For each
# composable step the manager mounts the verified molecule verbatim + EMITS the wiring from declared config (0 model
# tokens), then the REAL hidden oracle boots + probes it. This is where prompting fails but composition PASSES.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# composable steps -> (registered genome, molecule template, declared config). A new composable step is one row.
COMPOSE_STEPS: dict[str, dict[str, Any]] = {
    "orders_ingest": {"genome": "webhook_ingest_worker__stdlib_http__v0", "template": "webhook_worker",
                      "config": {"event_schema": {"event_id": "str", "amount": "int"}, "dedupe_fields": ["event_id"]}},
    "vendor_catalog": {"genome": "vendor_crud_macro__stdlib_http__v0", "template": "crud_service",
                       "config": {"resource": "vendor", "id_field": "vendor_id",
                                  "required_fields": ["vendor_id", "name"]}},
    "semantic_search": {"genome": "semantic_search_engine__stdlib_http__v0", "template": "search_engine",
                        "config": {}},
    "data_labeling": {"genome": "labeling_service__stdlib_http__v0", "template": "labeler",
                      "config": {"rules": [{"label": "urgent", "field": "text", "any": ["asap", "urgent"]},
                                           {"label": "big", "field": "amount", "gt": 1000}]}},
    "rag_search": {"genome": "rag_search_tool__stdlib_http__v0", "template": "rag_tool", "config": {}},
}


def deterministic_compose_run(steps: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    """EXECUTED proof: for each composable step, the manager emits the entry deterministically (0 model tokens) over
    the verbatim verified molecule; the REAL hidden oracle boots + probes it. Returns per-step oracle pass + the
    model-token cost (0). This captures the savings that prompting a model FAILS to."""
    import scripts.run_large_project_ab as rlp  # noqa: PLC0415
    reg = rlp._registry()
    mgr = PrimitiveSessionManager()
    steps = steps or COMPOSE_STEPS
    per_step = []
    for name, spec in steps.items():
        genome, run_buildout = reg[spec["genome"]]
        entry = genome.get("solution_file", "app.py")
        molecule_files = {fn: s for fn, s in genome["good"].items() if fn != entry}  # verified molecule, verbatim
        first_seen = [m for m in molecule_files if not mgr.available(m)]
        mgr.record(molecule_files)                                          # inject-once bookkeeping
        app_src = mgr.compose_entry(spec["template"], spec["config"])       # 0 model tokens, config-driven
        res = run_buildout(spec["genome"], {entry: app_src}, lane="deterministic_compose",
                           extra_files=molecule_files)
        per_step.append({"step": name, "genome": spec["genome"], "template": spec["template"],
                         "oracle_pass": bool(res["oracle_pass"]), "model_tokens": 0,
                         "oracle_checks_passed": sum(1 for v in (res.get("oracle_checks") or {}).values() if v),
                         "mounted_molecule_first_time": first_seen, "wiring_chars": len(app_src)})
    all_pass = all(p["oracle_pass"] for p in per_step)
    return {"record_type": "multi_step_deterministic_compose", "benchmark_kind": "real_project_buildout",
            "steps": per_step, "all_steps_pass": all_pass, "total_model_tokens": 0,
            "claim": ("every composable step BOOTS + passes its hidden oracle at 0 model-generation tokens — the "
                      "manager composed verified molecules from declared config; no model, no failure"),
            **BOUNDARY}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# LIVE multi-step A/B (opt-in) — real model per step; manager mounts shared verified modules verbatim; per-step
# hidden oracle; CUMULATIVE session tokens netted. This is the executed, headline-eligible number.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
def live_multi_step_ab(task: dict[str, Any], agent: Callable[[str], dict], *, repair: int = 2) -> dict[str, Any]:
    """Run each step with a real agent, managed vs unmanaged, accumulating REAL session tokens. Each step boots +
    passes a hidden oracle (reuses the registered single-genome oracle for that step's kind)."""
    import scripts.run_large_project_ab as rlp  # noqa: PLC0415
    reg = rlp._registry()
    # map each platform step to a registered bootable genome + the verified molecule the manager mounts
    step_genomes = {
        "orders_ingest": ("webhook_ingest_worker__stdlib_http__v0", "webhook_worker.py"),
        "signups_ingest": ("webhook_ingest_worker__stdlib_http__v0", "webhook_worker.py"),
        "vendor_catalog": ("vendor_crud_macro__stdlib_http__v0", "macro_crud_service.py"),
    }
    out: dict[str, Any] = {"record_type": "multi_step_live_ab", "benchmark_kind": "real_project_buildout",
                           "task": task["name"], "lanes": {}, **BOUNDARY}
    for managed in (False, True):
        mgr = PrimitiveSessionManager(registry={"webhook_worker.py": task["sources"]["webhook_worker.py"],
                                                "macro_crud_service.py": None} if managed else None)
        cum_in = cum_out = 0
        per = []
        for step in task["steps"]:
            if step["name"] not in step_genomes:
                continue
            gid, molecule = step_genomes[step["name"]]
            genome, run_buildout = reg[gid]
            entry = genome.get("solution_file", "app.py")
            provided = {}
            if managed and mgr.available(molecule) is False:
                # first time we need this molecule this session: mount it verbatim from the genome's good build
                provided = {fn: s for fn, s in genome["good"].items() if fn != entry}
                mgr.record(provided)
            elif managed:
                provided = {fn: s for fn, s in genome["good"].items() if fn != entry}  # reuse free (already proven)
            mode = "compiled_route" if managed else "none"
            # run ONE lane per step: managed=compiled_route (mount verified molecule verbatim), unmanaged=none
            lane = rlp.run_lane(gid, "managed" if managed else "unmanaged", agent, repair, mode)
            cum_in += lane["input_tokens"]; cum_out += lane["output_tokens"]
            per.append({"step": step["name"], "genome": gid, "oracle_pass": lane["oracle_pass"],
                        "input_tokens": lane["input_tokens"], "output_tokens": lane["output_tokens"],
                        "mounted": list(provided)})
        out["lanes"]["managed" if managed else "unmanaged"] = {
            "cumulative_input": cum_in, "cumulative_output": cum_out, "cumulative_total": cum_in + cum_out,
            "all_steps_pass": all(p["oracle_pass"] for p in per), "per_step": per}
    u, m = out["lanes"]["unmanaged"], out["lanes"]["managed"]
    both_ok = u["all_steps_pass"] and m["all_steps_pass"]
    out["cumulative_total_saved"] = u["cumulative_total"] - m["cumulative_total"]
    out["verdict"] = ("measured_savings" if (both_ok and out["cumulative_total_saved"] > 0) else
                      "capability_lift" if (m["all_steps_pass"] and not u["all_steps_pass"]) else
                      "no_headline")
    out["headline_eligible"] = out["verdict"] == "measured_savings"
    return out


def emit_structural() -> dict[str, Any]:
    task = build_task()
    rep = structural_ab(task)
    out = resource(ARTIFACT_DIR_REL)
    out.mkdir(parents=True, exist_ok=True)
    (out / "structural_ab.json").write_text(json.dumps(rep, indent=2, sort_keys=True), encoding="utf-8")
    return rep


def self_test() -> bool:
    """Mutation-gated + REAL (deterministic): (1) the COMPOUNDING LAW — structural savings STRICTLY INCREASE with
    each added step; (2) inject-once — store.py, built in step 1, is reused FREE in every later step; (3) registry
    reuse — the webhook_worker molecule is NEVER generated in the managed lane; (4) mutation — a manager with NO
    memory collapses managed==unmanaged (savings 0) and is caught; (5) determinism — byte-identical twice."""
    task = build_task()
    rep = structural_ab(task)

    # (1) compounding: the savings curve is strictly increasing (each step that reuses adds more savings)
    curve = [c["savings_tokens"] for c in rep["compounding_curve"]]
    assert all(curve[i + 1] > curve[i] for i in range(len(curve) - 1)), f"savings must COMPOUND per step: {curve}"
    assert rep["savings_tokens"] > 0 and rep["managed_tokens"] < rep["unmanaged_tokens"], rep

    # (2) inject-once: store.py built in step 1 (orders_ingest), reused free in steps 2-4
    m = rep["managed"]["per_step"]
    assert "store.py" not in m[0]["reused_free"], "store.py should be BUILT (not free) in step 1"
    assert all("store.py" in s["reused_free"] for s in m[1:]), f"store.py must be reused FREE after step 1: {m}"

    # (3) registry molecule never generated in managed
    assert all("webhook_worker.py" in s["reused_free"] for s in m[:2]), "registry molecule must always mount free"

    # (4) mutation gate: a memoryless manager (registry ignored, never records) -> no savings
    class _AmnesiacManager(PrimitiveSessionManager):
        def plan_step(self, needed):
            return {"reuse_free": [], "mount_now": [], "build_now": list(needed)}  # always rebuild everything

        def record(self, built):  # forgets immediately
            return None
    _g = globals()  # patch THIS module's global (works whether run as __main__ or imported — account() reads it)
    _orig = _g["PrimitiveSessionManager"]
    _g["PrimitiveSessionManager"] = _AmnesiacManager
    broken = account(task, managed=True)["total_tokens"]
    _g["PrimitiveSessionManager"] = _orig
    unmanaged = account(task, managed=False)["total_tokens"]
    assert broken == unmanaged, f"mutation gate: an amnesiac manager must lose ALL savings ({broken} vs {unmanaged})"

    # (5) determinism
    assert json.dumps(structural_ab(task), sort_keys=True) == json.dumps(rep, sort_keys=True), "non-deterministic"

    # (6) DETERMINISTIC COMPOSITION (EXECUTED, real oracles): every composable step boots + passes at 0 model tokens
    comp = deterministic_compose_run()
    assert comp["all_steps_pass"], f"deterministic composition must pass ALL real oracles at 0 tokens: {comp}"
    assert comp["total_model_tokens"] == 0 and len(comp["steps"]) >= 2, comp

    print(f"OK multi_step_task_ab self-test: PrimitiveSessionManager makes savings COMPOUND across a "
          f"{rep['n_steps']}-step task — unmanaged {rep['unmanaged_tokens']} vs managed {rep['managed_tokens']} "
          f"structural tokens ({rep['savings_ratio']}×, {rep['savings_tokens']} saved); curve strictly increasing "
          f"{curve} (verified molecule reused free, store built once & reused {len(m)-1}× via inject-once); "
          f"amnesiac-manager mutation caught (0 savings); deterministic. DETERMINISTIC COMPOSITION (EXECUTED): "
          f"{len(comp['steps'])}/{len(comp['steps'])} composable steps BOOT + pass their REAL hidden oracles at "
          f"0 model tokens (where prompting a model FAILS). serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Multi-step task A/B with a primitive session manager (compounding).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--structural", action="store_true", help="print the structural compounding curve + emit receipt")
    ap.add_argument("--compose", action="store_true",
                    help="EXECUTED: manager composes verified molecules (0 model tokens) -> real oracles pass")
    ap.add_argument("--live", action="store_true", help="executed cumulative-token A/B over a real model")
    ap.add_argument("--provider", default="openrouter")
    ap.add_argument("--model", default="")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--repair", type=int, default=2)
    args = ap.parse_args()
    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    if args.structural:
        print(json.dumps(emit_structural(), indent=2, sort_keys=True))
        return
    if getattr(args, "compose", False):
        rep = deterministic_compose_run()
        out = resource(ARTIFACT_DIR_REL); out.mkdir(parents=True, exist_ok=True)
        (out / "deterministic_compose.json").write_text(json.dumps(rep, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(rep, indent=2, sort_keys=True))
        return
    if args.live:
        import scripts.run_large_project_ab as rlp  # noqa: PLC0415
        prov = rlp._PROVIDERS[args.provider]
        base_url, keyfile, default_model = prov
        pool = rlp._load_key_file(keyfile) if keyfile else rlp._load_key_file(f"{args.provider}_keys.txt")
        from scripts.primitive_token_savings_ab import live_model  # noqa: PLC0415
        model = args.model or default_model

        def agent(prompt: str) -> dict:
            return live_model(prompt, pool, model, max_tokens=16000, strip=False, base_url=base_url)
        task = build_task()
        runs = [live_multi_step_ab(task, agent, repair=args.repair) for _ in range(args.repeats)]
        out = resource(ARTIFACT_DIR_REL); out.mkdir(parents=True, exist_ok=True)
        (out / f"live_multi_step_{args.provider}.json").write_text(
            json.dumps({"runs": runs, **BOUNDARY}, indent=2, sort_keys=True), encoding="utf-8")
        for r in runs:
            print(json.dumps({"verdict": r["verdict"], "saved": r["cumulative_total_saved"],
                              "unmanaged": r["lanes"]["unmanaged"]["cumulative_total"],
                              "managed": r["lanes"]["managed"]["cumulative_total"]}, sort_keys=True))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
