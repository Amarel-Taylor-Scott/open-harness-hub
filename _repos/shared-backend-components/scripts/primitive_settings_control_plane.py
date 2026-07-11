#!/usr/bin/env python3
"""scripts.primitive_settings_control_plane — the DETERMINISTIC control plane over deterministic primitives
(owner-directed 2026-07-07): customizers, remixers, managers, and tunable SETTINGS inputs.

  * SETTINGS SCHEMA — every tunable primitive declares its knobs as data: {name: {type, default, choices |
    min/max, unit}}. Settings are values, never code.
  * CUSTOMIZER — customize(fn, settings, schema) -> a configured callable + a canonical settings fingerprint
    + a provenance record. Validation clamps ranges and rejects unknown keys.
  * REMIXERS — deterministic variant generators over settings space: full grid for small spaces,
    one-step neighbors for hill-climbing. Stable ordering, zero RNG. (Composition-level remixing —
    swap/drop/reorder — lives in real_buildout_ab_harness._remix_variants; referenced, not duplicated.)
  * TUNER — tune(...) runs the TEST-FEEDBACK LOOP deterministically: score every candidate settings dict
    against a test suite, hill-climb or grid, return the champion WITH the full ledger (every variant's
    score preserved — lossless; losers are fallbacks, not deletions).
  * LLM SHORT-SETTINGS LANE — settings_from_llm_plan(schema, plan_json): the LLM's entire contribution is a
    ~20-token JSON of knob values, validated/clamped against the schema (the UI token-plan pattern,
    generalized). Never code, never free text.
  * MANAGER — PrimitiveSettingsManager: a persisted, file-backed registry of (primitive, settings
    fingerprint, score, champion) with a RATCHET (a worse score never replaces a champion) and full history.

Related prior art in-repo (reuse-first, this generalizes them): graph_autotune (retrieval-graph champion
configs), path_router_zoo (learned per-class tables), ui_design_primitives (token plan -> deterministic
build). candidate=true, serves_truth=false.

    python3 scripts/primitive_settings_control_plane.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import functools  # noqa: E402
import inspect  # noqa: E402
import itertools  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402  THE data-plane id authority
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"primitive_settings_control_plane requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-ctlplane"
_GRID_LIMIT = 512  # full grid only for small spaces; larger spaces hill-climb from defaults
_DEFAULT_TUNE_BUDGET = 64

#: worked example schemas for pack primitives (extensible data — a new tunable primitive = a new entry)
SETTINGS_SCHEMAS: dict[str, dict[str, dict[str, Any]]] = {
    "ngram_key": {"n": {"type": "int", "default": 3, "min": 2, "max": 5, "unit": "chars/gram"}},
    "blocking_key": {"parts": {"type": "int", "default": 2, "min": 1, "max": 4, "unit": "tokens"}},
    "chunk_text": {"size": {"type": "int", "default": 400, "min": 100, "max": 2000, "unit": "chars"},
                   "overlap": {"type": "int", "default": 50, "min": 0, "max": 200, "unit": "chars"}},
    "threshold_match": {"threshold": {"type": "float", "default": 0.5, "min": 0.0, "max": 1.0,
                                      "unit": "similarity"}},
    "derive_type_scale": {"ratio": {"type": "float", "default": 1.25, "choices": [1.125, 1.2, 1.25, 1.333, 1.5],
                                    "unit": "modular ratio"}},
}


# ── settings validation + customizer ─────────────────────────────────────────────────────────────────────────
def validate_settings(settings: dict[str, Any], schema: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Clamp ranges, snap choices, apply defaults; UNKNOWN keys are rejected loudly (never silently kept)."""
    unknown = sorted(set(settings) - set(schema))
    if unknown:
        raise ValueError(f"unknown settings {unknown}; schema knows {sorted(schema)}")
    out = {}
    for name, spec in schema.items():
        v = settings.get(name, spec["default"])
        if spec["type"] == "int":
            v = int(v)
        elif spec["type"] == "float":
            v = float(v)
        if "choices" in spec:
            v = min(spec["choices"], key=lambda c: abs(c - v) if isinstance(v, (int, float)) else 0)
        if "min" in spec:
            v = max(spec["min"], v)
        if "max" in spec:
            v = min(spec["max"], v)
        out[name] = v
    return out


def settings_fingerprint(primitive_name: str, settings: dict[str, Any]) -> str:
    return canonical_id(CARD_PREFIX, primitive_name, json.dumps(settings, sort_keys=True))


def customize(fn: Callable, settings: dict[str, Any],
              schema: Optional[dict[str, dict[str, Any]]] = None) -> dict[str, Any]:
    """DETERMINISTIC CUSTOMIZER: primitive + validated settings -> configured callable + fingerprint +
    provenance. Settings become keyword arguments; the base primitive is untouched (a variant, not an edit)."""
    schema = schema if schema is not None else SETTINGS_SCHEMAS.get(fn.__name__, {})
    valid = validate_settings(settings, schema)
    return {"callable": functools.partial(fn, **valid), "primitive": fn.__name__, "settings": valid,
            "fingerprint": settings_fingerprint(fn.__name__, valid),
            "provenance": "customized_variant", **BOUNDARY}


# ── deterministic remixers over settings space ───────────────────────────────────────────────────────────────
def _axis_values(spec: dict[str, Any]) -> list[Any]:
    if "choices" in spec:
        return list(spec["choices"])
    if spec["type"] == "int":
        lo, hi = spec["min"], spec["max"]
        step = max(1, (hi - lo) // 8)
        return list(range(lo, hi + 1, step))
    lo, hi = spec["min"], spec["max"]
    return [round(lo + (hi - lo) * i / 10, 4) for i in range(11)]


def settings_grid(schema: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Full deterministic grid (small spaces only — capped at _GRID_LIMIT, larger spaces raise to force
    hill-climbing instead of a silent truncation)."""
    axes = {name: _axis_values(spec) for name, spec in sorted(schema.items())}
    total = 1
    for vals in axes.values():
        total *= len(vals)
    if total > _GRID_LIMIT:
        raise ValueError(f"grid of {total} exceeds {_GRID_LIMIT}; use settings_neighbors hill-climbing")
    return [dict(zip(axes.keys(), combo)) for combo in itertools.product(*axes.values())]


def settings_neighbors(current: dict[str, Any], schema: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """One-step deterministic mutations: each knob moved one grid position up/down (the hill-climb moves)."""
    out = []
    for name in sorted(schema):
        vals = _axis_values(schema[name])
        cur = current.get(name, schema[name]["default"])
        idx = min(range(len(vals)), key=lambda i: abs(vals[i] - cur) if isinstance(cur, (int, float)) else 0)
        for j in (idx - 1, idx + 1):
            if 0 <= j < len(vals):
                out.append({**current, name: vals[j]})
    return out


# ── the deterministic TEST-FEEDBACK tuning loop ──────────────────────────────────────────────────────────────
def tune(fn: Callable, schema: dict[str, dict[str, Any]],
         score_fn: Callable[[Callable], float], *, budget: int = _DEFAULT_TUNE_BUDGET,
         strategy: str = "auto") -> dict[str, Any]:
    """Score settings variants against the TEST SUITE (score_fn evaluates a configured callable -> float,
    higher better). Grid when small, else deterministic hill-climb from defaults. Returns champion +
    the FULL ledger (losers preserved as labelled fallbacks — lossless)."""
    defaults = validate_settings({}, schema)
    ledger: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _eval(settings: dict[str, Any]) -> float:
        v = validate_settings(settings, schema)
        fp = settings_fingerprint(fn.__name__, v)
        if fp in seen:
            return next(r["score"] for r in ledger if r["fingerprint"] == fp)
        seen.add(fp)
        score = float(score_fn(functools.partial(fn, **v)))
        ledger.append({"settings": v, "fingerprint": fp, "score": round(score, 6)})
        return score

    try:
        candidates = settings_grid(schema) if strategy in ("auto", "grid") else None
    except ValueError:
        candidates = None
    if candidates is not None:
        for s in candidates[:budget]:
            _eval(s)
    else:  # hill-climb: evaluate defaults, then best neighbor until no improvement or budget spent
        current, best = defaults, _eval(defaults)
        while len(seen) < budget:
            neighbors = settings_neighbors(current, schema)
            scored = [(_eval(nb), json.dumps(nb, sort_keys=True), nb) for nb in neighbors]
            top_score, _key, top = max(scored)  # deterministic tie-break on the serialized settings
            if top_score <= best:
                break
            current, best = top, top_score
    champion = max(ledger, key=lambda r: (r["score"], r["fingerprint"]))
    return {"primitive": fn.__name__, "champion": champion, "evaluated": len(ledger),
            "ledger": sorted(ledger, key=lambda r: (-r["score"], r["fingerprint"])),
            "defaults": defaults, "strategy": "grid" if candidates is not None else "hill_climb",
            **BOUNDARY}


# ── the LLM SHORT-SETTINGS lane (never code; ~20 tokens of validated JSON) ───────────────────────────────────
def settings_from_llm_plan(schema: dict[str, dict[str, Any]], plan_json: str) -> dict[str, Any]:
    """Parse + validate a SHORT LLM-emitted settings JSON. Out-of-range values CLAMP (recorded), unknown
    keys REJECT. The LLM tunes knobs, the deterministic machinery does everything else."""
    try:
        raw = json.loads(plan_json)
    except ValueError as exc:
        return {"ok": False, "error": f"not valid JSON: {exc}", **BOUNDARY}
    if not isinstance(raw, dict):
        return {"ok": False, "error": "settings plan must be a JSON object", **BOUNDARY}
    try:
        valid = validate_settings(raw, schema)
    except ValueError as exc:
        return {"ok": False, "error": str(exc), **BOUNDARY}
    clamped = sorted(k for k in raw if k in valid and valid[k] != raw[k])
    return {"ok": True, "settings": valid, "clamped_keys": clamped,
            "plan_token_estimate": len(plan_json) // 4, **BOUNDARY}


# ── the MANAGER: persisted champion registry with a score RATCHET ────────────────────────────────────────────
class PrimitiveSettingsManager:
    """Deterministic manager of deterministic primitives: registers (primitive, settings, score) variants,
    keeps a champion per primitive under a RATCHET (a worse score never replaces the champion), preserves
    full history (losers are fallbacks), persists as JSONL."""

    def __init__(self, store_path: Optional[Path] = None) -> None:
        self.store_path = store_path or (resource("data") / "dev-intel" / "primitive_settings_control_plane"
                                         / "settings_registry.jsonl")
        self.rows: list[dict[str, Any]] = []
        if self.store_path.exists():
            self.rows = [json.loads(x) for x in self.store_path.read_text().splitlines() if x]

    def register(self, primitive: str, settings: dict[str, Any], score: float,
                 *, source: str = "deterministic_tune") -> dict[str, Any]:
        fp = settings_fingerprint(primitive, settings)
        prev = self.champion(primitive)
        promoted = prev is None or score > prev["score"]
        row = {"primitive": primitive, "settings": settings, "fingerprint": fp,
               "score": round(float(score), 6), "source": source, "champion": promoted, **BOUNDARY}
        if promoted and prev is not None:
            for r in self.rows:  # demote, never delete (lossless)
                if r["primitive"] == primitive and r.get("champion"):
                    r["champion"] = False
        self.rows.append(row)
        self._persist()
        return row

    def champion(self, primitive: str) -> Optional[dict[str, Any]]:
        rows = [r for r in self.rows if r["primitive"] == primitive and r.get("champion")]
        return rows[-1] if rows else None

    def history(self, primitive: str) -> list[dict[str, Any]]:
        return [r for r in self.rows if r["primitive"] == primitive]

    def recommend_bake(self, *, min_uses: int = 3) -> list[dict[str, Any]]:
        """Settings combos registered >= min_uses times are HOT -> bake them into frozen variants (plan
        tokens saved every future call); the long tail stays parameterized."""
        from collections import Counter  # noqa: PLC0415
        counts = Counter((r["primitive"], r["fingerprint"]) for r in self.rows)
        hot = []
        for (prim, fp), n in sorted(counts.items()):
            if n >= min_uses:
                row = next(r for r in self.rows if r["fingerprint"] == fp)
                hot.append({"primitive": prim, "settings": row["settings"], "uses": n,
                            "recommendation": "bake_variant"})
        return hot

    def _persist(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in self.rows))


def bake_variant(fn: Callable, settings: dict[str, Any], *, variant_label: str,
                 schema: Optional[dict[str, dict[str, Any]]] = None) -> dict[str, Any]:
    """THE TOKEN-ECONOMICS COUNTERPOINT (owner 2026-07-07): parameterized primitives cost plan tokens every
    call ('b(size=200, overlap=20)' ~ 10 tokens); a BAKED variant freezes the settings into a NEW named
    primitive ('b_tight') costing ~1 token at plan time. This emits a self-contained card whose
    executable_body = base source + a frozen wrapper — composable by the planned lane with zero settings
    tokens. Bake the HOT combos (see PrimitiveSettingsManager.recommend_bake); keep the parameterized form
    for the long tail."""
    schema = schema if schema is not None else SETTINGS_SCHEMAS.get(fn.__name__, {})
    valid = validate_settings(settings, schema)
    baked_name = f"{fn.__name__}__{variant_label}"
    sig = inspect.signature(fn)
    free = [p.name for p in sig.parameters.values() if p.name not in valid]
    kwargs = ", ".join([*free, *(f"{k}={v!r}" for k, v in sorted(valid.items()))])
    wrapper = (f"def {baked_name}({', '.join(free)}):\n"
               f'    """{fn.__name__} with baked settings {json.dumps(valid, sort_keys=True)} '
               f'(frozen variant; 0 settings tokens at plan time)."""\n'
               f"    return {fn.__name__}({kwargs})\n")
    body = inspect.getsource(fn) + "\n\n" + wrapper
    title = f"{fn.__name__} [{variant_label}]: baked {json.dumps(valid, sort_keys=True)}"
    return {"primitive_id": canonical_id(CARD_PREFIX, title, body), "impl_name": baked_name,
            "record_type": "baked_primitive_variant", "kind": "primitive", "title": title[:160],
            "executable_body": body, "language": "python", "baked_settings": valid,
            "base_primitive": fn.__name__, "plan_token_cost_estimate": 1,
            "input_edge": "PrimitiveInput", "output_edge": "PrimitiveOutput",
            "blackbox": f"Baked variant of {fn.__name__} with settings frozen: "
                        f"{json.dumps(valid, sort_keys=True)}. Plan-time cost ~1 token vs "
                        f"~{2 + 3 * len(valid)} for the parameterized form.", **BOUNDARY}


def all_cards() -> list[dict[str, Any]]:
    """The control plane's own primitives as cards (managers of primitives are primitives too)."""
    cards = []
    for fn in (validate_settings, customize, settings_grid, settings_neighbors, tune,
               settings_from_llm_plan):
        src = inspect.getsource(fn)
        title = (fn.__doc__ or fn.__name__).splitlines()[0][:160]
        cards.append({"primitive_id": canonical_id(CARD_PREFIX, title, src), "impl_name": fn.__name__,
                      "record_type": "settings_control_plane_primitive", "kind": "primitive",
                      "title": title, "executable_body": src, "language": "python",
                      "input_edge": "PrimitiveSettingsInput", "output_edge": "ConfiguredPrimitiveVariant",
                      "blackbox": f"Deterministic control-plane primitive: {title} Input: a primitive + "
                                  f"settings/schema/test-suite. Output: configured variant / tuned champion.",
                      "tier": "common", **BOUNDARY})
    return cards


# ── self-test ─────────────────────────────────────────────────────────────────────────────────────────────────
def threshold_match(score: float, threshold: float = 0.5) -> bool:
    """Fixture primitive: classify a similarity score as a match (the knob under tune)."""
    return score >= threshold


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    schema = SETTINGS_SCHEMAS["threshold_match"]
    checks.append(("validation: defaults applied, ranges clamped, choices snapped",
                   validate_settings({}, schema) == {"threshold": 0.5}
                   and validate_settings({"threshold": 7}, schema) == {"threshold": 1.0}
                   and validate_settings({"ratio": 1.26}, SETTINGS_SCHEMAS["derive_type_scale"])
                   == {"ratio": 1.25}))
    try:
        validate_settings({"nope": 1}, schema)
        checks.append(("unknown settings key REJECTED loudly", False))
    except ValueError:
        checks.append(("unknown settings key REJECTED loudly", True))
    cust = customize(threshold_match, {"threshold": 0.8})
    checks.append(("customizer: configured callable + canonical fingerprint; base primitive untouched",
                   cust["callable"](0.9) is True and cust["callable"](0.7) is False
                   and cust["fingerprint"].startswith(CARD_PREFIX)
                   and threshold_match(0.7) is True))  # base default unchanged
    grid = settings_grid(schema)
    checks.append(("remixer: full grid is deterministic and ordered",
                   len(grid) == 11 and grid == settings_grid(schema)
                   and grid[0] == {"threshold": 0.0}))
    nbrs = settings_neighbors({"threshold": 0.5}, schema)
    checks.append(("remixer: one-step neighbors move each knob one grid position",
                   {n["threshold"] for n in nbrs} == {0.4, 0.6}))
    # THE TEST-FEEDBACK LOOP: labeled similarity pairs; optimum threshold separates them at F1=1.0
    fixture = [(0.95, True), (0.9, True), (0.82, True), (0.55, False), (0.4, False), (0.1, False)]
    def suite_score(configured: Callable) -> float:
        tp = sum(1 for s, label in fixture if configured(s) and label)
        fp = sum(1 for s, label in fixture if configured(s) and not label)
        fn_ = sum(1 for s, label in fixture if not configured(s) and label)
        return (2 * tp) / (2 * tp + fp + fn_) if tp else 0.0
    result = tune(threshold_match, schema, suite_score)
    checks.append(("TUNER: deterministic feedback loop finds a perfect separator (F1=1.0) from the suite",
                   result["champion"]["score"] == 1.0
                   and 0.55 < result["champion"]["settings"]["threshold"] <= 0.82))
    checks.append(("TUNER ledger is LOSSLESS: every evaluated variant preserved, losers included",
                   result["evaluated"] == len(result["ledger"]) >= 11
                   and any(r["score"] < 1.0 for r in result["ledger"])))
    checks.append(("MUTATION GATE: flipped labels change the champion (the loop responds to tests)",
                   tune(threshold_match, schema,
                        lambda c: -suite_score(c) + 1)["champion"]["settings"]
                   != result["champion"]["settings"]))
    checks.append(("tuner is deterministic: identical inputs -> identical champion + ledger",
                   json.dumps(tune(threshold_match, schema, suite_score), sort_keys=True)
                   == json.dumps(result, sort_keys=True)))
    plan = settings_from_llm_plan(schema, '{"threshold": 0.75}')
    bad = settings_from_llm_plan(schema, '{"threshold": 99, "hack": 1}')
    checks.append(("LLM SHORT-SETTINGS lane: ~5-token plan accepted; out-of-range clamps; unknown rejects",
                   plan["ok"] and plan["settings"] == {"threshold": 0.75}
                   and plan["plan_token_estimate"] < 10 and not bad["ok"]))
    with tempfile.TemporaryDirectory() as td:
        mgr = PrimitiveSettingsManager(Path(td) / "reg.jsonl")
        mgr.register("threshold_match", {"threshold": 0.6}, 0.8)
        mgr.register("threshold_match", {"threshold": 0.7}, 0.95)
        worse = mgr.register("threshold_match", {"threshold": 0.9}, 0.5)
        champ = mgr.champion("threshold_match")
        checks.append(("MANAGER RATCHET: better score promotes; worse score NEVER replaces the champion",
                       champ["settings"] == {"threshold": 0.7} and worse["champion"] is False))
        checks.append(("MANAGER history lossless + persisted (reload sees all variants)",
                       len(PrimitiveSettingsManager(Path(td) / "reg.jsonl").history("threshold_match")) == 3))
    baked = bake_variant(threshold_match, {"threshold": 0.8}, variant_label="strict")
    scope: dict[str, Any] = {}
    exec(compile(baked["executable_body"], "baked", "exec"), scope)  # the card is self-contained source
    checks.append(("BAKED VARIANT: settings frozen into a new named primitive; self-contained source runs; "
                   "~1 plan token vs parameterized",
                   baked["impl_name"] == "threshold_match__strict"
                   and scope["threshold_match__strict"](0.9) is True
                   and scope["threshold_match__strict"](0.7) is False
                   and baked["plan_token_cost_estimate"] == 1))
    with tempfile.TemporaryDirectory() as td:
        mgr2 = PrimitiveSettingsManager(Path(td) / "r.jsonl")
        for _ in range(3):
            mgr2.register("threshold_match", {"threshold": 0.7}, 0.9, source="usage")
        mgr2.register("threshold_match", {"threshold": 0.2}, 0.4, source="usage")
        recs = mgr2.recommend_bake(min_uses=3)
        checks.append(("MANAGER recommends baking HOT settings combos only (>=3 uses)",
                       len(recs) == 1 and recs[0]["settings"] == {"threshold": 0.7} and recs[0]["uses"] == 3))
    checks.append(("cards + boundary", all(c.get("serves_truth") is False for c in all_cards())))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - primitive_settings_control_plane: customizers (validated settings -> configured "
          "variants), deterministic remixers (grid/neighbors), the test-feedback TUNER (lossless ledger, "
          "mutation-gated), the LLM short-settings lane (clamp/reject), and the ratcheting champion "
          "MANAGER. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--cards", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.cards:
        for c in all_cards():
            print(json.dumps(c, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
