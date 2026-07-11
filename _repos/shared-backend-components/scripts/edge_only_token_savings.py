#!/usr/bin/env python3
"""edge_only_token_savings — PROVE the edge-only design saves BOTH input and output tokens, with real
measurement, and show it STACKS with model-layer reasoning compression (ThinkingCap).

Owner (2026-07-11): "we need ... to actually save both input and output tokens." There are TWO orthogonal
token planes; they multiply, not overlap:

  PLANE A — model level (OUTPUT / reasoning tokens): a reasoning model overthinks. BottleCap's ThinkingCap
    (Apache-2.0, HuggingFace, drop-in Qwen3.6-27B replacement) cuts reasoning tokens ~45.8% out-of-domain /
    57.7% in-domain at ~unchanged accuracy (their matched-Δ% benchmark: 5 seeds, paired per-question so the
    reduction is genuine concision, not "bailed on the hard ones"). This is a MODEL ROUTE we adopt — it
    shrinks whatever the model thinks, on ANY task.

  PLANE B — composition level (INPUT + OUTPUT tokens): an edge-only primitive gives the model a searchable
    description + typed edges + a VERIFIED usage recipe pointing at maintained code. So the model:
      • INPUT  — reads a ~tens-of-tokens recipe instead of the package's source (measured below, real);
      • OUTPUT — emits a one-line verified invocation instead of REIMPLEMENTING the capability (measured
                 from the real reference-implementation source where introspectable).

Total ≈ (1 − planeA_on_reasoning) stacked with planeB_on_the_task. Plane A is CITED (BottleCap's numbers);
Plane B is MEASURED here on the real installed stdlib. We label measured / estimated / cited so nothing is
over-claimed (the honest ledger — the same discipline ThinkingCap's own "how to read these numbers" applies).

    python3 scripts/edge_only_token_savings.py --self-test
    python3 scripts/edge_only_token_savings.py --report
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.edge_only_package_introspection import STDLIB_TARGETS, derive_all  # reuse the verified corpus

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
_CHARS_PER_TOKEN = 4  # standard rough heuristic; labeled as an estimate wherever tokens are reported

#: PLANE A — ThinkingCap, CITED from BottleCap's published benchmark (attribute, don't assert as ours).
THINKINGCAP_MODEL_PLANE = {
    "source": "BottleCap AI — ThinkingCap-Qwen3.6-27B (Apache-2.0, HuggingFace)",
    "reasoning_token_reduction_out_of_domain": 0.458,   # matched Δ% macro mean
    "reasoning_token_reduction_in_domain": 0.577,
    "accuracy_delta_out_of_domain_pp": -0.7,             # ≈ unchanged
    "accuracy_delta_in_domain_pp": +1.0,                 # slightly better (GSM8K 93.3→96.5)
    "methodology": "5 seeds, full datasets, matched per-question Δ% (not raw mean — avoids the "
                   "'bailed on hard questions' confound), significance-tested",
    "adopt_as": "model_route — drop-in reasoning-token compression on ANY task, stacks with plane B",
    "candidate": True, "serves_truth": False,
}


def _tokens(chars: int) -> int:
    return chars // _CHARS_PER_TOKEN


def _module_source_chars(name: str) -> int:
    """REAL: total source bytes of the module/package — the 'read the whole package' input baseline."""
    mod = importlib.import_module(name)
    f = getattr(mod, "__file__", None)
    if not f:
        return 0
    if os.path.basename(f).startswith("__init__"):  # a package → sum every .py under it
        total = 0
        for root, _dirs, files in os.walk(os.path.dirname(f)):
            for fn in files:
                if fn.endswith(".py"):
                    try:
                        total += os.path.getsize(os.path.join(root, fn))
                    except OSError:
                        pass
        return total
    try:
        return os.path.getsize(f)
    except OSError:
        return 0


def _resolve(dotted: str) -> Optional[Any]:
    parts = dotted.split(".")
    try:
        obj: Any = importlib.import_module(parts[0])
    except Exception:  # noqa: BLE001
        return None
    for attr in parts[1:]:
        if not hasattr(obj, attr):
            return None
        obj = getattr(obj, attr)
    return obj


def _reimpl_source_chars(symbols: list[str]) -> Optional[int]:
    """REAL reimplementation baseline where the reference impl is pure-Python (inspect.getsource). Returns
    None for C-accelerated symbols (no python source) — we then report INPUT savings only, never a guess."""
    total, any_python = 0, False
    for sym in symbols:
        obj = _resolve(sym)
        if obj is None:
            return None
        try:
            total += len(inspect.getsource(obj))
            any_python = True
        except (TypeError, OSError):
            return None  # C builtin — not introspectable; be honest, don't fabricate a reimpl size
    return total if any_python else None


def measure_module(name: str, card: dict[str, Any]) -> dict[str, Any]:
    """Measure both planes for one module. INPUT is always real; OUTPUT is real where the reference impl is
    pure-Python, else marked not-introspectable (input-only)."""
    recipes = card["usage_recipes"]
    recipe_chars = sum(len(r["snippet"]) for r in recipes)
    pkg_chars = _module_source_chars(name)
    symbols = sorted({s for r in recipes for s in r["symbols"]})
    reimpl_chars = _reimpl_source_chars(symbols)
    # the one-line invocation the model emits WITH the recipe = the shortest route's call line
    invoke_chars = min(len(r["snippet"]) for r in recipes)

    if pkg_chars and recipe_chars:
        inp = {"package_source_chars": pkg_chars, "recipe_chars": recipe_chars,
               "package_source_tokens_est": _tokens(pkg_chars), "recipe_tokens_est": _tokens(recipe_chars),
               "input_read_ratio": round(recipe_chars / pkg_chars, 5),
               "input_reduction_x": round(pkg_chars / recipe_chars, 1), "measured": True}
    else:
        inp = {"measured": False, "input_reduction_x": None,
               "reason": "pure C extension — no python source file to read as an input baseline"}
    if reimpl_chars:
        out = {"reimplementation_source_chars": reimpl_chars, "invocation_chars": invoke_chars,
               "reimpl_tokens_est": _tokens(reimpl_chars), "invocation_tokens_est": _tokens(invoke_chars),
               "output_emit_ratio": round(invoke_chars / reimpl_chars, 4),
               "output_reduction_x": round(reimpl_chars / invoke_chars, 1), "measured": True}
    else:
        out = {"measured": False, "reason": "reference impl is C-accelerated (no python source) — "
               "input savings apply; output reimpl size not introspectable (not estimated)"}
    return {"module": name, "input": inp, "output": out, **BOUNDARY}


def stacked_report() -> dict[str, Any]:
    cards = {c["package"]["name"]: c for c in derive_all()}
    per = [measure_module(n, cards[n]) for n in STDLIB_TARGETS if n in cards]
    input_x = [m["input"]["input_reduction_x"] for m in per if m["input"]["input_reduction_x"]]
    output_x = [m["output"]["output_reduction_x"] for m in per if m["output"].get("measured")]
    # macro means (equal-weight, ThinkingCap-style — report the distribution, not a single number)
    def _macro(xs: list[float]) -> Optional[float]:
        return round(sum(xs) / len(xs), 1) if xs else None
    a = THINKINGCAP_MODEL_PLANE["reasoning_token_reduction_out_of_domain"]
    return {
        "record_type": "edge_only_token_savings_report",
        "plane_A_model_reasoning": THINKINGCAP_MODEL_PLANE,
        "plane_B_composition_measured": {
            "modules": len(per),
            "input_reduction_x_macro": _macro(input_x),
            "input_reduction_x_range": [min(input_x), max(input_x)] if input_x else None,
            "output_reduction_x_macro": _macro(output_x),
            "output_measured_modules": len(output_x),
            "output_not_introspectable_modules": len(per) - len(output_x),
        },
        "stacking_note": (
            f"planes are orthogonal: plane A cuts ~{int(a*100)}% of REASONING tokens (any task); plane B cuts "
            f"INPUT (read a recipe not a package) and OUTPUT (invoke, don't reimplement). On a task that both "
            f"applies to, savings compound — e.g. a ThinkingCap model that ALSO invokes a verified recipe "
            f"spends fewer thinking tokens AND emits a one-liner instead of a reimplementation."),
        "labels": "plane A = CITED (BottleCap); plane B = MEASURED here on the real installed stdlib; "
                  "tokens_est = chars/4 heuristic",
        "per_module": per, **BOUNDARY,
    }


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    rep = stacked_report()
    b = rep["plane_B_composition_measured"]
    per = rep["per_module"]

    # INPUT savings are real and large on every module WITH python source; pure-C ones honestly marked
    with_src = [m for m in per if m["input"]["measured"]]
    checks.append(("INPUT savings measured + large on every python-source module; pure-C honestly marked",
                   len(with_src) >= 8
                   and all(m["input"]["input_reduction_x"] > 5 for m in with_src)
                   and all("pure C extension" in m["input"]["reason"]
                           for m in per if not m["input"]["measured"])))

    # macro input reduction is a big multiple (reading a recipe vs a package)
    checks.append(("macro INPUT reduction is a large multiple (>20x to read)",
                   b["input_reduction_x_macro"] is not None and b["input_reduction_x_macro"] > 20))

    # OUTPUT savings measured on the pure-Python modules; invocation ≪ reimplementation
    out_measured = [m for m in per if m["output"].get("measured")]
    checks.append(("OUTPUT savings measured where reimpl is introspectable (invoke ≪ reimplement)",
                   len(out_measured) >= 3
                   and all(m["output"]["output_reduction_x"] > 3 for m in out_measured)))

    # HONESTY: C-accelerated modules are marked not-introspectable, NOT given a fabricated reimpl size
    not_intro = [m for m in per if not m["output"].get("measured")]
    checks.append(("C-accelerated modules honestly marked input-only (no fabricated output baseline)",
                   all("not introspectable" in m["output"]["reason"] for m in not_intro)))

    # plane A is CITED, not asserted as ours; carries its methodology
    checks.append(("plane A (ThinkingCap) is CITED with source + matched-Δ methodology, not asserted as ours",
                   "BottleCap" in rep["plane_A_model_reasoning"]["source"]
                   and "matched" in rep["plane_A_model_reasoning"]["methodology"]))

    # the two planes are described as orthogonal/stacking (both input and output covered)
    checks.append(("report covers BOTH input and output, and states the planes stack",
                   b["input_reduction_x_macro"] and b["output_reduction_x_macro"]
                   and "compound" in rep["stacking_note"]))

    # deterministic
    checks.append(("report deterministic (byte-identical)",
                   json.dumps(stacked_report(), sort_keys=True, default=str)
                   == json.dumps(rep, sort_keys=True, default=str)))

    ok = all(v for _, v in checks)
    print("edge_only_token_savings — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    print(f"  PLANE B (measured): INPUT ~{b['input_reduction_x_macro']}x less to read "
          f"(range {b['input_reduction_x_range']}); OUTPUT ~{b['output_reduction_x_macro']}x less to emit "
          f"on {b['output_measured_modules']} introspectable modules.")
    print(f"  PLANE A (cited): ThinkingCap ~{int(THINKINGCAP_MODEL_PLANE['reasoning_token_reduction_out_of_domain']*100)}% "
          f"fewer reasoning tokens @ ~unchanged accuracy. Planes stack.")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.report:
        rep = stacked_report()
        print(json.dumps({k: rep[k] for k in rep if k != "per_module"}, indent=2, default=str))
        print("\nper-module (input reduction × / output reduction ×):")
        for m in rep["per_module"]:
            i = m["input"].get("input_reduction_x") or "—(pure C)"
            o = m["output"].get("output_reduction_x", "—(C, input-only)")
            print(f"  {m['module']:12} input {str(i):>10}x   output {o}")
        return 0
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
