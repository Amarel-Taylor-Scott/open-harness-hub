#!/usr/bin/env python3
"""scripts.saas_buildout_decomposer — the MISSING link in the owner's dev-kit loop: take a just-BUILT-OUT
multi-file project ("generate a SaaS that does X" -> a real multi-file buildout) and DECOMPOSE its own code
back into reusable primitive candidates, then TEST each by EXECUTION (candidate-only).

Owner (2026-07-09): "we should have harness/agentic development kits, develop large projects ... 'generate a
SaaS that does this' ... then it should build it out, then we can decompose it into primitives, then we can
test." Every existing module runs registry->build (real_buildout_ab_harness injects primitives_lib into a
build) or idea->primitive (primitive_buildout_orchestrator). NONE takes freshly-built project code and mines
ITS primitives. This closes that reverse arc:

    built-out project files  ->  ast decompose (top-level functions/classes, real source, purity signal)
      ->  primitive candidates  ->  EXECUTED test (security scan -> determinism probe -> optional oracle)
      ->  reuse cards (real_buildout_ab_harness exec-card shape)  ->  the NEXT buildout imports them verbatim.

Honest boundaries (no-proxy law):
  * decomposition is deterministic ast, 0 tokens, offline;
  * "test" here means EXECUTED — banned-import security scan (reused from primitive_token_savings_ab) + a
    determinism probe that runs each candidate TWICE in an isolated `python -I -S` subprocess and requires
    identical output, + an OPTIONAL correctness oracle when the caller supplies input->expected fixtures
    (reused sandbox_run). A determinism pass is NOT a correctness promise — correctness needs an oracle and
    promotion; every row stays candidate=true / serves_truth=false;
  * purity/classification is a heuristic SIGNAL (which candidates are certification targets), never truth.

    python3 scripts/saas_buildout_decomposer.py --self-test
    python3 scripts/saas_buildout_decomposer.py --demo          # decompose the reference orders-API buildout
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
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import ast  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402  (the determinism-probe RUNNER itself, not model code)
import tempfile  # noqa: E402
from typing import Any  # noqa: E402

from scripts.primitive_token_savings_ab import security_scan, sandbox_run  # noqa: E402  reuse the gate

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"saas_buildout_decomposer requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_project"  # no_proxy_gate: certification runs an EXECUTED determinism/oracle subprocess
DECOMP_ID_PREFIX = "prim-decomp"
DECOMP_RECORD_TYPE = "buildout_decomposed_primitive_candidate"
ARTIFACT_DIR_REL = "data/dev-intel/saas_buildout_decomposer"

# Names/modules whose use marks a function as an IO/side-effect boundary (NOT a pure certifiable primitive).
_IO_CALL_NAMES = frozenset({"open", "input", "print", "exec", "eval", "compile", "__import__"})
_IO_MODULES = frozenset({"os", "sys", "subprocess", "socket", "shutil", "requests", "urllib", "http",
                         "sqlite3", "threading", "multiprocessing", "random", "time", "pathlib", "secrets"})
_IO_ATTRS = frozenset({"write", "read", "send", "recv", "connect", "system", "popen", "makedirs", "remove"})


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# 1. DECOMPOSE — ast-walk the buildout files into primitive candidates (deterministic, 0-token, offline)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def _import_preamble(tree: ast.Module, source: str) -> str:
    """The file's top-level import lines, so an extracted function can run in isolation (the security scan +
    determinism probe then decide whether those imports are safe/deterministic)."""
    lines = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            seg = ast.get_source_segment(source, node)
            if seg:
                lines.append(seg)
    return "\n".join(lines)


def _classify(node: ast.AST) -> str:
    """Heuristic purity SIGNAL (not truth): 'pure_primitive' iff no IO/side-effect call, no global/nonlocal.
    'io_boundary' otherwise. Drives which candidates are certification targets."""
    for n in ast.walk(node):
        if isinstance(n, (ast.Global, ast.Nonlocal)):
            return "io_boundary"
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name) and f.id in _IO_CALL_NAMES:
                return "io_boundary"
            if isinstance(f, ast.Attribute):
                if f.attr in _IO_ATTRS:
                    return "io_boundary"
                if isinstance(f.value, ast.Name) and f.value.id in _IO_MODULES:
                    return "io_boundary"
    return "pure_primitive"


def _candidate(name: str, source: str, preamble: str, classification: str, kind: str,
               decomposed_from: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    cid = canonical_id(DECOMP_ID_PREFIX, name, decomposed_from, kind)
    return {"record_type": DECOMP_RECORD_TYPE, "kind": kind, "primitive_id": cid, "card_id": cid,
            "name": name, "impl_name": name, "classification": classification,
            "decomposed_from": decomposed_from,
            "executable_body": source, "import_preamble": preamble,
            "title": f"{name} — decomposed from {decomposed_from}",
            "certification_target": classification == "pure_primitive" and kind == "function",
            **(extra or {}), **BOUNDARY}


def decompose_project(files: dict[str, str]) -> dict[str, Any]:
    """Decompose a built-out multi-file project into primitive candidates. Top-level functions become function
    primitives (pure ones are certification targets); classes become stateful-module primitives (+ a pure-method
    count). Deterministic, offline. Every row candidate=true / serves_truth=false."""
    primitives: list[dict[str, Any]] = []
    modules: list[dict[str, Any]] = []
    for fname, source in sorted(files.items()):
        if not fname.endswith(".py"):
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            modules.append({"file": fname, "parse_error": str(exc), **BOUNDARY})
            continue
        preamble = _import_preamble(tree, source)
        n_fns = n_classes = 0
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                seg = ast.get_source_segment(source, node)
                if seg:
                    primitives.append(_candidate(node.name, seg, preamble, _classify(node), "function", fname))
                    n_fns += 1
            elif isinstance(node, ast.ClassDef):
                seg = ast.get_source_segment(source, node)
                methods = [m for m in node.body if isinstance(m, ast.FunctionDef)]
                pure_methods = [m.name for m in methods if _classify(m) == "pure_primitive"
                                and not m.name.startswith("_")]
                # a class that mutates self-state is a stateful primitive; otherwise a pure utility bundle
                mutates = any(isinstance(x, ast.Attribute) and isinstance(x.ctx, ast.Store)
                              for m in methods for x in ast.walk(m))
                if seg:
                    primitives.append(_candidate(
                        node.name, seg, preamble, "stateful" if mutates else "pure_primitive", "class", fname,
                        extra={"n_methods": len(methods), "pure_public_methods": pure_methods}))
                    n_classes += 1
        modules.append({"file": fname, "n_functions": n_fns, "n_classes": n_classes,
                        "n_lines": source.count("\n") + 1, **BOUNDARY})
    return {"record_type": "buildout_decomposition", "primitives": primitives, "modules": modules,
            "n_primitives": len(primitives),
            "n_certification_targets": sum(1 for p in primitives if p.get("certification_target")),
            **BOUNDARY}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# 2. TEST — EXECUTED certification of a decomposed candidate (security scan + determinism probe + opt. oracle)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def determinism_probe(code: str, entry: str, sample_inputs: list[tuple]) -> dict[str, Any]:
    """Run `entry(*args)` TWICE per sample in an isolated `python -I -S` subprocess and require identical output.
    A real executed property: a candidate that depends on a counter/clock/rng goes non-deterministic here.
    Never runs code that fails the security scan."""
    banned = security_scan(code)
    if banned:
        return {"ran": False, "n_identical": 0, "n_total": len(sample_inputs), "error": f"security_scan:{banned}"}
    harness = code + "\n\n_IN = " + repr(sample_inputs) + "\n_ok = 0\n"
    harness += ("for _args in _IN:\n"
                f"    try:\n        _a = {entry}(*_args)\n        _b = {entry}(*_args)\n"
                "        _ok += 1 if _a == _b else 0\n"
                "    except Exception:\n        pass\n")
    harness += "print('DET', _ok, len(_IN))\n"
    try:
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "cand.py"
            f.write_text(harness, encoding="utf-8")
            out = subprocess.run([sys.executable, "-I", "-S", str(f)], capture_output=True, text=True,
                                 timeout=10, cwd=td)
        line = [ln for ln in out.stdout.splitlines() if ln.startswith("DET")]
        if line:
            _, p, t = line[-1].split()
            return {"ran": True, "n_identical": int(p), "n_total": int(t), "error": None}
        return {"ran": True, "n_identical": 0, "n_total": len(sample_inputs),
                "error": (out.stderr or "no_output")[:80]}
    except subprocess.TimeoutExpired:
        return {"ran": False, "n_identical": 0, "n_total": len(sample_inputs), "error": "timeout"}


def certify_candidate(candidate: dict[str, Any], sample_inputs: list[tuple] | None = None,
                      fixtures: list[tuple] | None = None) -> dict[str, Any]:
    """EXECUTED test of one decomposed candidate. Runs the extracted source WITH its import preamble.
    - unsafe          : banned import -> never executed;
    - impure_skip     : classified io_boundary -> not a deterministic-primitive target (honest skip);
    - deterministic   : identical output across two isolated runs on every sample;
    - oracle_correct  : additionally passes caller-supplied input->expected fixtures (a real correctness bar).
    verdict is the strongest level reached. serves_truth stays false regardless."""
    code = (candidate.get("import_preamble", "") + "\n" + candidate["executable_body"]).strip() + "\n"
    entry = candidate["impl_name"]
    receipt: dict[str, Any] = {"primitive_id": candidate["primitive_id"], "name": entry,
                               "classification": candidate.get("classification"),
                               "benchmark_kind": BENCHMARK_KIND, **BOUNDARY}
    banned = security_scan(code)
    if banned:
        return {**receipt, "verdict": "unsafe", "security_banned": banned}
    if candidate.get("classification") != "pure_primitive" or candidate.get("kind") != "function":
        return {**receipt, "verdict": "impure_skip", "reason": "not a pure function primitive"}
    if not sample_inputs:
        return {**receipt, "verdict": "no_samples", "reason": "determinism needs sample inputs"}
    det = determinism_probe(code, entry, sample_inputs)
    deterministic = det["ran"] and det["n_total"] > 0 and det["n_identical"] == det["n_total"]
    receipt.update({"determinism": det, "deterministic": deterministic})
    if not deterministic:
        return {**receipt, "verdict": "nondeterministic"}
    if fixtures:
        oracle = sandbox_run(code, entry, fixtures)
        correct = oracle["ran"] and oracle["n_total"] > 0 and oracle["n_pass"] == oracle["n_total"]
        receipt.update({"oracle": oracle, "oracle_correct": correct})
        return {**receipt, "verdict": "oracle_correct" if correct else "deterministic_only"}
    return {**receipt, "verdict": "deterministic"}


def to_exec_card(candidate: dict[str, Any]) -> dict[str, Any]:
    """Render a decomposed+certified candidate in real_buildout_ab_harness's exec-card shape, so the NEXT
    buildout can inject it verbatim into primitives_lib (0 generated tokens). The loop closes here."""
    return {"primitive_id": candidate["primitive_id"], "impl_name": candidate["impl_name"],
            "title": candidate["title"], "executable_body": candidate["executable_body"],
            "decomposed_from": candidate.get("decomposed_from"), **BOUNDARY}


# ── reference buildout for the self-test: a real multi-file "orders API" SaaS slice (the shape a dev-kit emits)
_REF_VALIDATORS = (
    "def validate_order(payload):\n"
    '    """Validate an order payload; returns (ok, errors). Pure primitive mined from the buildout."""\n'
    "    errors = []\n"
    "    if not payload.get('order_id'):\n"
    "        errors.append('missing_order_id')\n"
    "    amount = payload.get('amount')\n"
    "    if amount is None or not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:\n"
    "        errors.append('invalid_amount')\n"
    "    return (len(errors) == 0, errors)\n"
)
_REF_STORE = (
    "class OrderStore:\n"
    '    """Idempotent in-memory order store (stateful primitive mined from the buildout)."""\n'
    "    def __init__(self):\n"
    "        self._d = {}\n"
    "    def add(self, order):\n"
    "        oid = order['order_id']\n"
    "        if oid in self._d:\n"
    "            return False\n"
    "        self._d[oid] = dict(order)\n"
    "        return True\n"
    "    def get(self, oid):\n"
    "        return self._d.get(oid)\n"
)
_REF_APP = (
    "import json\n"
    "from validators import validate_order\n"
    "from store import OrderStore\n"
    "def handle(event, store):\n"
    "    if event.get('type') == 'health':\n"
    "        return {'status': 200, 'healthy': True}\n"
    "    ok, errors = validate_order(event)\n"
    "    if not ok:\n"
    "        return {'status': 400, 'errors': errors}\n"
    "    created = store.add(event)\n"
    "    return {'status': 201 if created else 200, 'order_id': event['order_id']}\n"
)
REFERENCE_BUILDOUT: dict[str, str] = {"validators.py": _REF_VALIDATORS, "store.py": _REF_STORE, "app.py": _REF_APP}


def self_test() -> bool:
    """Mutation-gated + EXECUTED: decompose the reference multi-file buildout, prove the right primitives are
    mined + classified, and prove the determinism/oracle certification actually RUNS (a nondeterministic
    candidate FAILS the probe; a good one reaches oracle_correct)."""
    decomp = decompose_project(REFERENCE_BUILDOUT)
    by_name = {p["name"]: p for p in decomp["primitives"]}
    assert "validate_order" in by_name, f"must mine validate_order: {sorted(by_name)}"
    assert by_name["validate_order"]["classification"] == "pure_primitive", "validate_order is a pure primitive"
    assert by_name["validate_order"]["certification_target"] is True, "pure function is a certification target"
    assert "OrderStore" in by_name and by_name["OrderStore"]["classification"] == "stateful", \
        "OrderStore is a stateful primitive"
    assert by_name["handle"]["classification"] == "pure_primitive", "handle has no IO calls -> pure signal"

    # EXECUTED certification: validate_order reaches oracle_correct (deterministic + passes real fixtures).
    samples = [({"order_id": "A1", "amount": 10},), ({"order_id": "B2"},), ({"amount": 5},)]
    fixtures = [(({"order_id": "A1", "amount": 10},), (True, [])),
                (({"order_id": "B2"},), (False, ["invalid_amount"])),
                (({"amount": 5},), (False, ["missing_order_id"]))]
    cert = certify_candidate(by_name["validate_order"], sample_inputs=samples, fixtures=fixtures)
    assert cert["verdict"] == "oracle_correct", f"validate_order must certify oracle_correct: {cert}"
    assert cert["deterministic"] is True and cert["oracle_correct"] is True

    # MUTATION GATE: a counter-carrying (non-deterministic) candidate must FAIL the determinism probe.
    flaky = _candidate("flaky", "def flaky(x, _c=[0]):\n    _c[0] += 1\n    return x + _c[0]\n", "",
                       "pure_primitive", "function", "flaky.py")
    bad = certify_candidate(flaky, sample_inputs=[(1,)])
    assert bad["verdict"] == "nondeterministic", f"a counter-carrying candidate must fail determinism: {bad}"

    # SECURITY GATE: a banned-import candidate is never executed.
    unsafe = _candidate("evil", "def evil(x):\n    import os\n    return os.getpid()\n", "",
                        "pure_primitive", "function", "evil.py")
    assert certify_candidate(unsafe, sample_inputs=[(1,)])["verdict"] == "unsafe", "banned import must be refused"

    # loop-closing bridge: decomposed+certified -> exec-card shape the next buildout imports verbatim.
    card = to_exec_card(by_name["validate_order"])
    assert card["impl_name"] == "validate_order" and card["executable_body"] and card["serves_truth"] is False

    assert BENCHMARK_KIND == "real_project" and decomp["candidate"] is True and decomp["serves_truth"] is False
    print(f"OK saas_buildout_decomposer self-test: decomposed {decomp['n_primitives']} primitives from a "
          f"{len(REFERENCE_BUILDOUT)}-file buildout ({decomp['n_certification_targets']} certification targets); "
          f"validate_order EXECUTED to oracle_correct, a counter-carrying candidate FAILS determinism, a banned "
          f"import is refused; exec-card bridge ready; benchmark_kind=real_project; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Decompose a built-out project into EXECUTED-tested primitive candidates.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--demo", action="store_true", help="decompose + certify the reference orders-API buildout")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.demo:
        decomp = decompose_project(REFERENCE_BUILDOUT)
        by_name = {p["name"]: p for p in decomp["primitives"]}
        samples = [({"order_id": "A1", "amount": 10},), ({"order_id": "B2"},)]
        certs = [certify_candidate(p, sample_inputs=samples if p["name"] == "validate_order" else None)
                 for p in decomp["primitives"]]
        out_dir = resource(ARTIFACT_DIR_REL)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "reference_decomposition.json").write_text(
            json.dumps({"decomposition": decomp, "certifications": certs}, indent=2, sort_keys=True),
            encoding="utf-8")
        print(json.dumps({"n_primitives": decomp["n_primitives"],
                          "n_certification_targets": decomp["n_certification_targets"],
                          "verdicts": {c["name"]: c["verdict"] for c in certs}}, indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
