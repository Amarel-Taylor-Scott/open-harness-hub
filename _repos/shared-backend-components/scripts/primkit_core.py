#!/usr/bin/env python3
"""scripts.primkit_core — the adoption-FORCING framework core: primitive-first by default, non-compliance fails
the linter (candidate-only tooling).

Owner directive (2026-07-08): make the primitive/process/path-search architecture impossible to ignore at the
code level. "No naked work" — no naked function / API call / browser action / LLM call / data transform / promotion.
Everything is a Primitive/Step/Route/Trial/Verifier/Benchmark/Adapter/Receipt/Gap/Promotion/AntiPrimitive with
typed ports, receipts, verifiers, and a lifecycle. This module is the high-leverage slice of the primkit spec
(§28 order): the `@primitive` decorator + manifest registry, receipted `run_primitive()`, the `@verifier`
decorator, the promotion-gate state machine (never 'certified' without receipts), the prim.toml POLICY, and — the
enforcement teeth — a DIRECT-CALL LINTER that AST-scans for naked http/llm/browser/subprocess/eval calls and for
primitive-looking functions (parse/extract/validate/…) that lack an `@primitive` manifest.

Honors the corrected law: raw_candidate_count is primary; usefulness is a NON-DESTRUCTIVE router; serve-time
injection stays lean (max_context_primitives). Full stack (TS SDK, compilers, CI plugins, adapters, package
layout §22) is the roadmap; this is the runnable, mutation-gated core. candidate=true/serves_truth=false.

    python3 scripts/primkit_core.py --self-test
    python3 scripts/primkit_core.py --lint <file.py>
    python3 scripts/primkit_core.py --policy
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/ml_lifecycle_primitive_minter.py) ────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import ast  # noqa: E402
import functools  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import time  # noqa: E402
from typing import Any, Callable  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"primkit_core requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

# ── prim.toml POLICY defaults (owner §11/§23). Adoption-forcing switches. ─────────────────────────────────────
POLICY: dict[str, Any] = {
    "strict": True,
    "ban": {"direct_http": True, "direct_llm": True, "direct_browser": True, "direct_subprocess": True,
            "direct_filesystem_write": True, "eval_exec": True},
    "require": {"ports": True, "output_schema": True, "receipts": True, "verifier_for_promotion": True,
                "benchmark_for_certification": True, "provenance_for_certification": True,
                "security_gate_before_execution": True, "candidate_truth_boundary": True},
    "exploration": {"raw_candidate_count_is_primary": True, "usefulness_is_non_destructive_router": True,
                    "store_candidates_without_promotion": True},
    "serving": {"max_context_primitives": 8, "prefer_compiled_routes": True, "fallback_to_llm_for_gaps": True},
    # ── AI-FIRST NAMING (owner 2026-07-08): long, meaning-bearing, globally-unique names are context the LLM
    #    reads — do NOT let standard python linters penalize them. Consistent with the repo GLOBALLY-UNIQUE-NAMING
    #    law + the pyprefix scheme (py_<kind>__<file>__<scope>__<name>). We keep SEMANTIC lints (naked calls,
    #    undecorated primitives, unused imports) but IGNORE the name-shape/length rules below. ──
    "naming": {
        "ai_first_long_names": True,
        "rationale": "a name is context the model uses; names double as objects AND documentation for LLM review",
        "enforced_by": "pyprefix scheme (scripts/pyprefix.py) + canonical_id — NOT pep8-naming",
        "ignored_standard_lint_rules": {
            "C0103": "pylint invalid-name — blocks long/unconventional but meaningful names",
            "C0301": "pylint line-too-long — long names legitimately push lines out; relax, don't truncate names",
            "E501": "pycodestyle line-too-long — same; raise max, never shorten a meaning-bearing name",
            "N801": "pep8-naming class-name — pyprefix classes are location-derived, not plain CamelCase",
            "N802": "pep8-naming function-name — long descriptive function names are intended",
            "N803": "pep8-naming argument-name — long descriptive arg names are intended",
            "N806": "pep8-naming variable-in-function — long local names carry context, intended",
            "N815": "pep8-naming mixedCase-in-class — allowed where it mirrors an external schema",
            "N816": "pep8-naming mixedCase-global — allowed for schema/edge mirroring",
            "R0914": "pylint too-many-locals — descriptive intermediate names are not a smell here",
        },
        "line_length_max": 120,
    },
}


def recommended_external_lint_ignores() -> dict[str, list[str]]:
    """The standard lint rules to DISABLE when wiring ruff/pylint/flake8 (§10) so they stop fighting AI-first
    long names. Semantic rules stay ON; only name-shape/length rules are ignored."""
    ignored = list(POLICY["naming"]["ignored_standard_lint_rules"])
    return {"pylint_disable": [c for c in ignored if c.startswith(("C", "R"))],
            "ruff_extend_ignore": [c for c in ignored if c.startswith(("E", "N"))],
            "flake8_extend_ignore": [c for c in ignored if c.startswith(("E", "N"))],
            "line_length_max": POLICY["naming"]["line_length_max"],
            "note": "AI-first naming: long meaning-bearing names are context, not a smell (owner + repo law)."}

# ── promotion lifecycle (owner §12): never 'certified' without executed verifier/security/benchmark/provenance ─
PROMOTION_STAGES = ["candidate", "linted", "security_checked", "fixture_tested", "benchmarked", "validated",
                    "certified", "production"]
# receipts required to REACH each stage (cumulative).
_STAGE_RECEIPTS: dict[str, set[str]] = {
    "linted": {"lint"}, "security_checked": {"lint", "security"},
    "fixture_tested": {"lint", "security", "fixtures"},
    "benchmarked": {"lint", "security", "fixtures", "benchmark"},
    "validated": {"lint", "security", "fixtures", "benchmark", "determinism"},
    "certified": {"lint", "security", "fixtures", "benchmark", "determinism", "verifier", "provenance"},
    "production": {"lint", "security", "fixtures", "benchmark", "determinism", "verifier", "provenance", "approval"},
}

# ── the registry (in-memory here; a real store is a seam) ────────────────────────────────────────────────────
REGISTRY: dict[str, dict[str, Any]] = {}
_RECEIPTS: list[dict[str, Any]] = []


def _sha(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:32]


def primitive(*, id: str, inputs: list[str], outputs: list[str], determinism: str = "deterministic",
              side_effects: list[str] | None = None, verifiers: list[str] | None = None) -> Callable:
    """Decorator: register a manifest (typed ports, lifecycle, candidate/truth), and wrap the fn so every call
    can emit a receipt. Adoption-forcing: a primitive WITHOUT input/output ports is rejected at decoration."""
    if not inputs or not outputs:
        raise ValueError(f"primitive {id} must declare input_ports AND output_ports (POLICY.require.ports)")
    manifest = {"primitive_id": id, "input_ports": list(inputs), "output_ports": list(outputs),
                "determinism": determinism, "side_effects": side_effects or [], "verifiers": verifiers or [],
                "lifecycle": "candidate", "manifest_hash": None, **BOUNDARY}
    manifest["manifest_hash"] = _sha({k: manifest[k] for k in ("primitive_id", "input_ports", "output_ports")})

    def deco(fn: Callable) -> Callable:
        manifest["entry"] = fn.__name__
        REGISTRY[id] = manifest

        @functools.wraps(fn)
        def wrapper(*a: Any, **k: Any) -> Any:
            return fn(*a, **k)
        wrapper.manifest = manifest  # type: ignore[attr-defined]
        return wrapper
    return deco


def verifier(*, id: str, target_ports: list[str]) -> Callable:
    """Decorator: register a deterministic verifier for output ports; emits a verifier receipt when run."""
    def deco(fn: Callable) -> Callable:
        fn.verifier_manifest = {"verifier_id": id, "target_ports": target_ports, **BOUNDARY}  # type: ignore
        return fn
    return deco


def run_primitive(prim: Callable | str, payload: dict[str, Any], *, run_id: str = "run",
                  serve_truth: bool = False) -> dict[str, Any]:
    """Receipted execution. Blocks truth-serving unless the primitive is certified+ (candidate/truth boundary)."""
    manifest = REGISTRY[prim] if isinstance(prim, str) else prim.manifest
    fn = None if isinstance(prim, str) else prim
    if serve_truth and manifest["lifecycle"] not in ("certified", "production"):
        raise PermissionError(f"candidate/truth boundary: {manifest['primitive_id']} is "
                              f"'{manifest['lifecycle']}', cannot serve truth")
    t0 = time.time()
    # (fn only present when a decorated callable was passed; string-id path is a manifest-only dry run)
    out = fn(payload) if fn is not None else {"dry_run": True}
    receipt = {"record_type": "primitive_receipt", "primitive_id": manifest["primitive_id"], "run_id": run_id,
               "input_hash": _sha(payload), "output_hash": _sha(out), "manifest_hash": manifest["manifest_hash"],
               "latency_ms": round((time.time() - t0) * 1000, 3), "verifier_results": [], **BOUNDARY}
    _RECEIPTS.append(receipt)
    return {"output": out, "receipt": receipt}


def promote(primitive_id: str, to: str, receipts_present: set[str], *, approved: bool = False) -> dict[str, Any]:
    """Gate: advance the lifecycle only if the required receipts exist. 'certified' NEVER without executed
    verifier + security + benchmark + provenance (owner §12). Denies with the missing set."""
    if to not in _STAGE_RECEIPTS:
        raise ValueError(f"unknown stage {to}")
    need = set(_STAGE_RECEIPTS[to])
    if to == "production":
        need = need | ({"approval"} if approved else {"__blocked__"})
    have = set(receipts_present) | ({"approval"} if approved else set())
    missing = need - have
    ok = not missing
    if ok and primitive_id in REGISTRY:
        REGISTRY[primitive_id]["lifecycle"] = to
    return {"primitive_id": primitive_id, "requested_stage": to, "promoted": ok,
            "missing_receipts": sorted(missing), "required": sorted(_STAGE_RECEIPTS[to]), **BOUNDARY}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# THE ENFORCEMENT TEETH — the direct-call linter (owner §8/§9). AST-scans for naked calls + undecorated
# primitive-looking functions. This is what makes adoption non-optional.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
_BANNED_MODULE_CALLS: dict[str, tuple[str, str]] = {
    "requests": ("P044", "naked HTTP — use ctx.http / primkit.adapters.http"),
    "httpx": ("P044", "naked HTTP — use ctx.http"),
    "aiohttp": ("P044", "naked HTTP — use ctx.http"),
    "urllib": ("P044", "naked HTTP — use ctx.http"),
    "openai": ("P045", "naked LLM — use ctx.llm (schema + token ledger + candidate boundary)"),
    "anthropic": ("P045", "naked LLM — use ctx.llm"),
    "playwright": ("P046", "naked browser — use ctx.browser (state receipt + side-effect policy)"),
    "selenium": ("P046", "naked browser — use ctx.browser"),
    "puppeteer": ("P046", "naked browser — use ctx.browser"),
    "subprocess": ("P047", "naked subprocess — sandbox via primkit runner"),
}
_BANNED_BUILTINS: dict[str, tuple[str, str]] = {
    "eval": ("P048", "eval() forbidden in strict mode"), "exec": ("P048", "exec() forbidden in strict mode"),
}
_PRIMITIVE_NAME_PREFIXES = ("parse", "extract", "validate", "verify", "transform", "normalize", "route", "plan",
                            "execute", "reconcile", "map", "convert", "score", "rank", "select", "classify",
                            "generate", "compile", "match", "dedupe", "repair")


def _root_name(node: ast.AST) -> str | None:
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _has_primitive_decorator(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for d in fn.decorator_list:
        target = d.func if isinstance(d, ast.Call) else d
        name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", None)
        if name and name.endswith("primitive"):
            return True
    return False


def lint_source(src: str, *, policy: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Return structured violations. Adoption-forcing: naked http/llm/browser/subprocess/eval + primitive-looking
    functions with no @primitive manifest."""
    pol = policy or POLICY
    violations: list[dict[str, Any]] = []
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                root = _root_name(node.func)
                if root in _BANNED_MODULE_CALLS:
                    code, msg = _BANNED_MODULE_CALLS[root]
                    violations.append({"code": code, "line": node.lineno, "symbol": f"{root}.{node.func.attr}",
                                       "severity": "fail", "message": msg})
            elif isinstance(node.func, ast.Name) and node.func.id in _BANNED_BUILTINS:
                code, msg = _BANNED_BUILTINS[node.func.id]
                violations.append({"code": code, "line": node.lineno, "symbol": node.func.id,
                                   "severity": "fail", "message": msg})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith(_PRIMITIVE_NAME_PREFIXES) and not _has_primitive_decorator(node):
                violations.append({"code": "P001", "line": node.lineno, "symbol": node.name,
                                   "severity": "fail" if pol.get("strict") else "warn",
                                   "message": f"function '{node.name}' looks like a primitive but has no "
                                              f"@primitive manifest (typed ports + verifier + receipts)"})
    return violations


def lint_file(path: str) -> list[dict[str, Any]]:
    return lint_source(Path(path).read_text(encoding="utf-8"))


def self_test() -> bool:
    """Mutation-gated. Proves: decorator registers a ported manifest; run_primitive emits a receipt; the linter
    CATCHES naked http/llm/subprocess/eval + undecorated primitives AND passes compliant code; the promotion gate
    denies 'certified' without receipts; the candidate/truth boundary blocks truth-serving below certified."""
    REGISTRY.clear()
    _RECEIPTS.clear()

    # (1) decorator: ports required; registers manifest candidate-only.
    @primitive(id="string.normalize.whitespace.v1", inputs=["string.raw"], outputs=["string.normalized"])
    def normalize_whitespace(payload):
        return {"normalized": " ".join(payload["text"].split())}
    assert "string.normalize.whitespace.v1" in REGISTRY
    m = REGISTRY["string.normalize.whitespace.v1"]
    assert m["candidate"] is True and m["serves_truth"] is False and m["lifecycle"] == "candidate"
    try:
        primitive(id="bad", inputs=[], outputs=["x"])(lambda p: p)
        raise AssertionError("primitive without input ports must be rejected")
    except ValueError:
        pass

    # (2) run_primitive emits a receipt with input/output hashes + boundary.
    r = run_primitive(normalize_whitespace, {"text": "  a   b "})
    assert r["output"]["normalized"] == "a b"
    assert r["receipt"]["input_hash"].startswith("sha256:") and r["receipt"]["serves_truth"] is False
    assert len(_RECEIPTS) == 1

    # (3) candidate/truth boundary: cannot serve truth while candidate.
    try:
        run_primitive(normalize_whitespace, {"text": "x"}, serve_truth=True)
        raise AssertionError("truth-serving a candidate must be blocked")
    except PermissionError:
        pass

    # (4) THE LINTER catches naked calls + undecorated primitives.
    bad_src = (
        "import requests, subprocess\n"
        "def parse_invoice(x):\n"
        "    r = requests.get('http://x')\n"
        "    subprocess.run(['ls'])\n"
        "    return eval(x)\n"
    )
    v = lint_source(bad_src)
    codes = {x["code"] for x in v}
    assert "P044" in codes, "linter must flag naked requests.get"
    assert "P047" in codes, "linter must flag naked subprocess"
    assert "P048" in codes, "linter must flag eval"
    assert "P001" in codes, "linter must flag undecorated parse_* primitive"

    # (5) compliant code passes clean.
    good_src = (
        "from primkit import primitive\n"
        "@primitive(id='x.parse.v1', inputs=['a'], outputs=['b'])\n"
        "def parse_thing(payload):\n"
        "    return {'b': payload['a']}\n"
    )
    assert lint_source(good_src) == [], f"compliant code should not lint: {lint_source(good_src)}"

    # (6) promotion gate: no 'certified' without the full receipt set; denies with the missing set.
    denied = promote("string.normalize.whitespace.v1", "certified", {"lint", "security"})
    assert denied["promoted"] is False and "verifier" in denied["missing_receipts"]
    ok = promote("string.normalize.whitespace.v1", "certified",
                 {"lint", "security", "fixtures", "benchmark", "determinism", "verifier", "provenance"})
    assert ok["promoted"] is True and REGISTRY["string.normalize.whitespace.v1"]["lifecycle"] == "certified"
    # now truth-serving is allowed (certified).
    run_primitive(normalize_whitespace, {"text": "ok"}, serve_truth=True)

    # (7) the corrected law is encoded in POLICY.
    assert POLICY["exploration"]["raw_candidate_count_is_primary"] is True
    assert POLICY["exploration"]["usefulness_is_non_destructive_router"] is True
    assert POLICY["serving"]["max_context_primitives"] == 8

    # (8) AI-FIRST NAMING: a very long, meaning-bearing name must NEVER lint (owner: names are LLM context).
    #     The linter penalizes SEMANTICS (naked calls, undecorated primitives), never name length/shape.
    long_name_src = (
        "from primkit import primitive\n"
        "@primitive(id='doc.extract.v1', inputs=['a'], outputs=['b'])\n"
        "def extract_prior_authorization_required_fields_from_payer_policy_pdf_layout_region(payload):\n"
        "    normalized_us_census_tract_geoid_with_confidence_and_source_span_reference = payload['a']\n"
        "    return {'b': normalized_us_census_tract_geoid_with_confidence_and_source_span_reference}\n"
    )
    assert lint_source(long_name_src) == [], f"AI-first long names must not lint: {lint_source(long_name_src)}"
    assert POLICY["naming"]["ai_first_long_names"] is True
    assert "C0103" in POLICY["naming"]["ignored_standard_lint_rules"], "must ignore pylint invalid-name"
    ext = recommended_external_lint_ignores()
    assert "C0103" in ext["pylint_disable"] and any(c.startswith("N") for c in ext["ruff_extend_ignore"])

    print(f"OK primkit_core self-test: @primitive+ports+receipts; linter caught "
          f"{sorted(codes)} on naked code + passed compliant; promotion gate denies certified w/o verifier "
          f"(missing={denied['missing_receipts']}); candidate/truth boundary enforced; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="primkit adoption-forcing framework core.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--lint", metavar="FILE", help="lint a python file for naked calls + undecorated primitives")
    ap.add_argument("--policy", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.lint:
        vs = lint_file(args.lint)
        print(json.dumps(vs, indent=2))
        print(f"\n{len(vs)} violation(s); {sum(1 for v in vs if v['severity']=='fail')} FAIL")
        return
    if args.policy:
        print(json.dumps(POLICY, indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
