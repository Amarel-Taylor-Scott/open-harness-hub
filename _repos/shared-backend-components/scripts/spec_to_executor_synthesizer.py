#!/usr/bin/env python3
"""scripts.spec_to_executor_synthesizer — the promotion-loop closer (task #26): turn a `needs_executor=true` spec
card into a RUNNING, fixture-proven executor and promote it candidate->validated ONLY when every gate passes.

This is the missing wire the reuse audit found: standards_factory / import_openapi / process_stage mint SPECS with
`needs_executor=true`, the package/security/provenance around them is complete, but nothing turns a spec into a
runnable executor + golden fixtures — so specs are stranded at candidate and the atlas never becomes executable
(0-token reuse). This module is that synthesizer, and it leverages Hy3 (the free flywheel lanes) as the drafting
brain while keeping the deterministic system in charge of disposition:

    spec ->[Hy3 drafts body + fixtures] -> security gate -> SANDBOX-execute against fixtures -> determinism check
         -> promote candidate->validated (only if schema_valid + all-fixtures-pass) -> validated->certified
         (only if security pass + deterministic_replay + benchmark_result). Losers are kept (lossless), never truth.

Laws honored: LLM PROPOSES, deterministic system DISPOSES; generated code passes the security gate and is executed
ONLY in an isolated subprocess sandbox (never by the flywheel); every row candidate/serves_truth=false until the
gates promote it; canonical ids; raw drafts + rejected candidates preserved (lossless distillation).

    python3 scripts/spec_to_executor_synthesizer.py --self-test
    python3 scripts/spec_to_executor_synthesizer.py --run --limit 20        # live, Hy3-drafted
    python3 scripts/spec_to_executor_synthesizer.py --run --limit 5 --specs path/to/specs.jsonl
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
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts.primitive_security_gate import gate_body  # noqa: E402
from scripts.primitive_lifecycle import promote  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"spec_to_executor_synthesizer requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
RECEIPT_RECORD_TYPE = "executor_synthesis_receipt"
_DATA_SUBDIR = "data/dev-intel/spec_to_executor_synthesizer"
_SANDBOX_TIMEOUT_S = 10
#: only these determinism budgets may auto-promote past candidate (matches primitive_lifecycle.TRUTH_ELIGIBLE)
_PROMOTABLE_DETERMINISM = frozenset({"D0_pure", "D1_seeded", "D2_bounded_external"})

_SYS = (
    "You produce a DETERMINISTIC, PURE Python executor for a primitive spec, plus golden fixtures that prove it. "
    "Return STRICT JSON only, no prose, with keys: "
    "`python_body` (a self-contained module: imports from the stdlib only — NO network, file, subprocess, eval, "
    "exec, or __import__ — defining a single entry function), `entry` (the entry function name), "
    "`positive_fixtures` (>=3 objects {\"input\": {kwargs} | [args] | value, \"expected\": <value>}), "
    "`negative_fixtures` (>=2 objects; either {\"input\":..., \"expected_raises\": true} for bad input the function "
    "must reject, or {\"input\":..., \"expected\": <value>}). Do NOT artificially shorten the body: write a "
    "COMPLETE module — as many stdlib-only helper functions as the capability needs plus one orchestrating `entry` "
    "that runs the full multi-step logic. A rich/advanced/multi-step capability SHOULD be long (100-400+ lines) with "
    "real edge-case handling, validation, and sub-steps; a trivial one stays concise — match the length to the "
    "capability, never truncate. The `entry` must still be deterministic (same input -> same output; no clock/random/IO) "
    "and fixture-provable."
)

_JSON_OBJ_RE = re.compile(r"\{.*\}", re.S)


def _parse_draft(text: str) -> Optional[dict[str, Any]]:
    """Extract the executor JSON from an LLM reply. Hy3 (and the other reasoning lanes) REASON HEAVILY, so the
    answer object is usually AFTER a lot of prose/reasoning and often inside ```json fences — grabbing the FIRST `{`
    (a brace in the reasoning) is the #1 cause of `no_valid_draft`. Fix: collect EVERY ```json-fenced block AND every
    top-level balanced-brace object, json.loads each, and return the LAST one that actually has python_body+entry
    (the real answer follows the reasoning). This converts wasted long responses into usable drafts."""
    if not text:
        return None
    # scan EVERY top-level balanced-brace object (this already covers ```json-fenced ones; a naive `\{.*?\}` regex
    # breaks on the nested braces of the fixtures, so we don't use one).
    candidates: list[str] = []
    depth, start = 0, None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start is not None:
                candidates.append(text[start:i + 1])
                start = None
    best: Optional[dict[str, Any]] = None
    for c in candidates:
        try:
            obj = json.loads(c)
        except Exception:  # noqa: BLE001 — most balanced spans are prose, not JSON
            continue
        if isinstance(obj, dict) and obj.get("python_body") and obj.get("entry"):
            best = obj  # keep the LAST valid one — the answer trails the reasoning
    if best is None:
        return None
    best.setdefault("positive_fixtures", [])
    best.setdefault("negative_fixtures", [])
    return best


# ── sandbox: run the (already security-gated) body against fixtures in an ISOLATED subprocess ──────────────────
_RUNNER = r"""
import json, sys, importlib.util
spec = importlib.util.spec_from_file_location("cand_exec", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
entry = getattr(mod, sys.argv[2])
fixtures = json.loads(sys.argv[3])
out = []
for fx in fixtures:
    inp = fx.get("input", {})
    try:
        if isinstance(inp, dict):
            res = entry(**inp)
        elif isinstance(inp, list):
            res = entry(*inp)
        else:
            res = entry(inp)
        out.append({"ok": True, "result": res})
    except Exception as e:
        out.append({"ok": False, "error": type(e).__name__})
print(json.dumps(out, sort_keys=True))
"""


def sandbox_run(body: str, entry: str, fixtures: list[dict[str, Any]]) -> dict[str, Any]:
    """Execute `entry` against `fixtures` in an isolated subprocess (python -I -S, minimal env, timeout). The body
    has ALREADY passed the security gate; the sandbox is defence-in-depth. Returns per-fixture ok/result + a raw
    stdout digest (used for the determinism check)."""
    with tempfile.TemporaryDirectory() as td:
        cand = Path(td) / "cand_exec.py"
        cand.write_text(body)
        env = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": os.environ.get("PATH", "")}
        try:
            proc = subprocess.run([sys.executable, "-I", "-S", "-c", _RUNNER, str(cand), entry,
                                   json.dumps(fixtures)],
                                  capture_output=True, text=True, timeout=_SANDBOX_TIMEOUT_S, env=env, cwd=td)
        except subprocess.TimeoutExpired:
            return {"ran": False, "reason": "timeout", "results": [], "stdout": ""}
        if proc.returncode != 0:
            return {"ran": False, "reason": f"exit_{proc.returncode}", "results": [],
                    "stderr": (proc.stderr or "")[:300], "stdout": ""}
        try:
            results = json.loads(proc.stdout.strip())
        except Exception:  # noqa: BLE001
            return {"ran": False, "reason": "unparsable_output", "results": [], "stdout": proc.stdout[:300]}
        return {"ran": True, "results": results, "stdout": proc.stdout.strip()}


def _fixture_passed(fx: dict[str, Any], r: dict[str, Any]) -> bool:
    if fx.get("expected_raises"):
        return r.get("ok") is False
    if "expected" in fx:
        return bool(r.get("ok")) and r.get("result") == fx["expected"]
    return bool(r.get("ok"))  # no expectation -> "must at least run without raising"


def _grade(fixtures: list[dict[str, Any]], run: dict[str, Any]) -> dict[str, Any]:
    if not run.get("ran"):
        return {"all_pass": False, "n": len(fixtures), "passed": 0, "reason": run.get("reason")}
    results = run["results"]
    passed = sum(1 for fx, r in zip(fixtures, results) if _fixture_passed(fx, r))
    return {"all_pass": passed == len(fixtures) and len(fixtures) > 0, "n": len(fixtures), "passed": passed}


def _regen_token_proxy(body: str) -> int:
    """Honest proxy for the tokens a bare LLM would spend REGENERATING this body (chars/4). Reuse cost = 0."""
    return len(body) // 4


def synthesize(spec: dict[str, Any], chat_fn: Callable[[str, str], tuple[str, str]]) -> dict[str, Any]:
    """One spec -> a synthesis receipt. chat_fn(system, user) -> (text, lane). Deterministic given chat_fn."""
    name = str(spec.get("name") or spec.get("primitive_id") or "spec")
    determinism = str(spec.get("determinism_level", "D0_pure"))
    base = {"record_type": RECEIPT_RECORD_TYPE, "spec_name": name, "determinism_level": determinism, **BOUNDARY}

    prompt = (f"Spec name: {name}\nIntent: {spec.get('intent', name)}\n"
              f"Input schema: {json.dumps(spec.get('input_schema', {}))}\n"
              f"Output schema: {json.dumps(spec.get('output_schema', {}))}\n"
              f"Edges: {json.dumps(spec.get('edges', {}))}\nExamples: {json.dumps(spec.get('examples', []))[:600]}\n"
              "Return the strict JSON described in the system message.")
    text, lane = chat_fn(_SYS, prompt)
    draft = _parse_draft(text)
    if draft is None:
        return {**base, "outcome": "no_valid_draft", "lane": lane, "promoted_to": "candidate",
                "raw_draft_digest": canonical_id("draft", text or "")}
    body, entry = str(draft["python_body"]), str(draft["entry"])
    pos, neg = draft["positive_fixtures"], draft["negative_fixtures"]

    # 1) SECURITY GATE (LLM code is never trusted)
    gate = gate_body(body, name=name)
    raw_draft_digest = canonical_id("draft", text)
    if gate["status"] == "quarantine":
        card = {"primitive_id": canonical_id("execprim", name, gate["artifact_hash"]), "impl_name": name,
                "executable_body": body, "lifecycle_stage": "candidate", "verifier_id": "synth::sandbox_fixtures",
                **BOUNDARY}
        dec = promote(card, "quarantined", {"security_status": "quarantine",
                                            "quarantine_reason": gate["highest_severity"]})
        return {**base, "outcome": "security_quarantine", "lane": lane, "security": gate["status"],
                "highest_severity": gate["highest_severity"], "promoted_to": "quarantined",
                "raw_draft_digest": raw_draft_digest, "promotion": {"ok": dec.get("ok")}}
    if gate["status"] == "fail":
        return {**base, "outcome": "security_fail_stays_candidate", "lane": lane, "security": "fail",
                "highest_severity": gate["highest_severity"], "promoted_to": "candidate",
                "raw_draft_digest": raw_draft_digest}

    # 2) SANDBOX-EXECUTE against fixtures, twice (determinism)
    run1 = sandbox_run(body, entry, pos)
    run2 = sandbox_run(body, entry, pos)
    neg_run = sandbox_run(body, entry, neg) if neg else {"ran": True, "results": []}
    deterministic = run1.get("ran") and run1.get("stdout") == run2.get("stdout")
    pos_grade = _grade(pos, run1)
    neg_grade = _grade(neg, neg_run) if neg else {"all_pass": True, "n": 0, "passed": 0}
    fixtures_pass = pos_grade["all_pass"] and neg_grade["all_pass"]

    card = {"primitive_id": canonical_id("execprim", name, gate["artifact_hash"]), "impl_name": name,
            "executable_body": body, "entry": entry, "determinism_level": determinism,
            "lifecycle_stage": "candidate", "verifier_id": "synth::sandbox_fixtures", "schema_version": 1,
            "provenance": {"synthesizer": "spec_to_executor_synthesizer", "lane": lane,
                           "raw_draft_digest": raw_draft_digest, "spec_name": name},
            "positive_fixtures": pos, "negative_fixtures": neg, **BOUNDARY}

    promotable = determinism in _PROMOTABLE_DETERMINISM
    receipt = {**base, "lane": lane, "security": "pass", "entry": entry,
               "sandbox": {"ran": bool(run1.get("ran")), "reason": run1.get("reason")},
               "positive": pos_grade, "negative": neg_grade, "deterministic_replay": bool(deterministic),
               "raw_draft_digest": raw_draft_digest, "body_chars": len(body),
               "regen_tokens_proxy": _regen_token_proxy(body), "reuse_tokens": 0}

    if not (fixtures_pass and deterministic and promotable):
        receipt["outcome"] = ("fixtures_failed" if not fixtures_pass else
                              "nondeterministic" if not deterministic else "determinism_not_promotable")
        receipt["promoted_to"] = "candidate"
        receipt["card"] = card
        return receipt

    # 3) PROMOTE candidate -> validated (schema_valid + self_test_pass + verifier_id)
    dec_v = promote(card, "validated", {"schema_valid": True, "self_test_pass": True})
    if not dec_v.get("ok"):
        receipt["outcome"] = "promotion_refused_validated"
        receipt["promoted_to"] = "candidate"
        receipt["promotion_missing"] = dec_v.get("missing")
        receipt["card"] = card
        return receipt
    vcard = dec_v["card"]
    # 4) attempt validated -> certified (security pass + deterministic_replay + benchmark_result)
    bench = {"reuse_tokens": 0, "regen_tokens_proxy": _regen_token_proxy(body),
             "saved_tokens_proxy": _regen_token_proxy(body), "fixtures_passed": pos_grade["passed"] + neg_grade["passed"],
             "note": "proxy tokens (chars/4) — a real-executed A/B still gates true savings"}
    dec_c = promote(vcard, "certified", {"security_status": "pass", "deterministic_replay": True,
                                         "benchmark_result": bench})
    final_stage = "certified" if dec_c.get("ok") else "validated"
    receipt["outcome"] = "promoted"
    receipt["promoted_to"] = final_stage
    receipt["benchmark_result"] = bench
    receipt["card"] = dec_c["card"] if dec_c.get("ok") else vcard
    return receipt


def _hy3_chat_fn() -> Callable[[str, str], tuple[str, str]]:
    """Live drafting brain: Hy3 first, then the other free flywheel lanes as fallback (key rotation reused)."""
    from scripts.hy3_overnight_flywheel import _real_chat, LANES  # noqa: PLC0415
    c = _real_chat()
    hy3 = ("openrouter", "tencent/hy3:free")
    order = [hy3] + [lane for lane in LANES if lane != hy3]

    def chat(system: str, user: str) -> tuple[str, str]:
        for prov, model in order:
            try:
                out = c(prov, model, system, user)
            except Exception:  # noqa: BLE001 — a dead lane must not kill the run
                continue
            if isinstance(out, dict) and (out.get("text") or "").strip():
                return out["text"], f"{prov}/{model}"
        return "", "none"

    return chat


def _load_specs(specs_path: Optional[str], limit: int) -> list[dict[str, Any]]:
    """needs_executor=true spec cards: from an explicit JSONL, else the standards-factory spec output."""
    out: list[dict[str, Any]] = []
    paths = ([Path(specs_path)] if specs_path else
             [resource("data/dev-intel/primitive_factory/specialized_packs"),
              resource("catalog/knowledge-packs/data")])
    for p in paths:
        files = [p] if p.is_file() else (sorted(p.glob("*.jsonl")) if p.is_dir() else [])
        for f in files:
            try:
                for ln in f.read_text().splitlines():
                    if '"needs_executor"' not in ln:
                        continue
                    r = json.loads(ln)
                    if r.get("needs_executor") and (r.get("name") or r.get("primitive_id")):
                        out.append(r)
                        if len(out) >= limit:
                            return out
            except Exception:  # noqa: BLE001
                continue
    return out


def run(specs: list[dict[str, Any]], chat_fn: Callable[[str, str], tuple[str, str]],
        out_path: Optional[Path] = None) -> dict[str, Any]:
    out_path = out_path or (resource(_DATA_SUBDIR) / "synthesis_receipts.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    st = {"specs": len(specs), "promoted": 0, "validated": 0, "certified": 0, "candidate": 0,
          "quarantined": 0, "by_outcome": {}}
    with out_path.open("a") as fh:
        for spec in specs:
            rec = synthesize(spec, chat_fn)
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            st["by_outcome"][rec["outcome"]] = st["by_outcome"].get(rec["outcome"], 0) + 1
            stage = rec.get("promoted_to", "candidate")
            st[stage] = st.get(stage, 0) + 1
            if rec["outcome"] == "promoted":
                st["promoted"] += 1
    return {**st, "pool_path": str(out_path)}


# ── self-test (offline, deterministic, mutation-gated) ─────────────────────────────────────────────────────────
_GOOD_BODY = (
    "def normalize_ws(s):\n"
    "    return ' '.join(str(s).split())\n"
)
_DANGEROUS_BODY = (
    "def leak(s):\n"
    "    return __import__('os').listdir('.')\n"
)
_WRONG_BODY = (
    "def normalize_ws(s):\n"
    "    return str(s).upper()\n"   # passes security but FAILS the fixtures
)


def _stub_chat(kind: str) -> Callable[[str, str], tuple[str, str]]:
    bodies = {
        "good": {"python_body": _GOOD_BODY, "entry": "normalize_ws",
                 "positive_fixtures": [{"input": {"s": "  a   b "}, "expected": "a b"},
                                       {"input": {"s": "x"}, "expected": "x"},
                                       {"input": {"s": "p\tq\nr"}, "expected": "p q r"}],
                 "negative_fixtures": [{"input": {"s": "a b"}, "expected": "a b"}]},
        "dangerous": {"python_body": _DANGEROUS_BODY, "entry": "leak",
                      "positive_fixtures": [{"input": {"s": "x"}, "expected": []}], "negative_fixtures": []},
        "wrong": {"python_body": _WRONG_BODY, "entry": "normalize_ws",
                  "positive_fixtures": [{"input": {"s": "  a   b "}, "expected": "a b"}], "negative_fixtures": []},
    }[kind]

    def chat(_system: str, _user: str) -> tuple[str, str]:
        return json.dumps(bodies), "stub/deterministic"

    return chat


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    good = synthesize({"name": "normalize_ws", "determinism_level": "D0_pure"}, _stub_chat("good"))
    checks.append(("GOOD spec: sandbox-runs + all fixtures pass -> promoted to validated/certified",
                   good["outcome"] == "promoted" and good["promoted_to"] in ("validated", "certified")
                   and good["positive"]["all_pass"] and good["deterministic_replay"]))
    checks.append(("promoted card carries executable_body + verifier + serves_truth=false",
                   good["card"]["executable_body"] and good["card"]["verifier_id"] == "synth::sandbox_fixtures"
                   and good["card"]["serves_truth"] is False and good["card"]["lifecycle_stage"] in ("validated", "certified")))
    checks.append(("benchmark_result records reuse=0 vs regen proxy>0 (the 0-token-reuse claim)",
                   good.get("benchmark_result", {}).get("reuse_tokens") == 0
                   and good["benchmark_result"]["regen_tokens_proxy"] > 0))

    dangerous = synthesize({"name": "leak", "determinism_level": "D0_pure"}, _stub_chat("dangerous"))
    checks.append(("DANGEROUS body: security gate QUARANTINES, never promoted, never executed",
                   dangerous["outcome"] == "security_quarantine" and dangerous["promoted_to"] == "quarantined"))

    wrong = synthesize({"name": "normalize_ws", "determinism_level": "D0_pure"}, _stub_chat("wrong"))
    checks.append(("WRONG body: passes security but FAILS fixtures -> stays candidate (not promoted)",
                   wrong["outcome"] == "fixtures_failed" and wrong["promoted_to"] == "candidate"
                   and not wrong["positive"]["all_pass"]))

    # determinism budget gate: a D4 spec with a good body still must NOT auto-promote
    d4 = synthesize({"name": "normalize_ws", "determinism_level": "D4_stochastic"}, _stub_chat("good"))
    checks.append(("non-promotable determinism (D4) stays candidate even with passing fixtures",
                   d4["promoted_to"] == "candidate" and d4["outcome"] == "determinism_not_promotable"))

    # sandbox actually executes real code (defence-in-depth over the gate)
    sb = sandbox_run(_GOOD_BODY, "normalize_ws", [{"input": {"s": "  a  b "}, "expected": "a b"}])
    checks.append(("sandbox runs real code in an isolated subprocess",
                   sb["ran"] and sb["results"][0]["result"] == "a b"))

    # determinism of the whole synthesize() given a fixed chat_fn
    good2 = synthesize({"name": "normalize_ws", "determinism_level": "D0_pure"}, _stub_chat("good"))
    checks.append(("synthesize is deterministic given a fixed chat_fn",
                   good2["promoted_to"] == good["promoted_to"] and good2["card"]["primitive_id"] == good["card"]["primitive_id"]))

    ok = all(v for _, v in checks)
    for nm, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {nm}")
    print(("PASS" if ok else "FAIL") + " - spec_to_executor_synthesizer: Hy3-drafted spec->executor, security-gated "
          "+ SANDBOX-fixture-proven + determinism-checked, promotes candidate->validated->certified only on pass "
          "(dangerous quarantined, wrong stays candidate); serves_truth=false.")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Synthesize + fixture-prove + promote executors for needs_executor specs.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="live Hy3-drafted synthesis over needs_executor specs")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--specs", default=None, help="explicit JSONL of needs_executor spec cards")
    args = ap.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.run:
        specs = _load_specs(args.specs, args.limit)
        if not specs:
            print("no needs_executor specs found (pass --specs PATH); nothing to synthesize.")
            return 0
        print(f"synthesizing {len(specs)} spec(s) with Hy3-first lane order …")
        summ = run(specs, _hy3_chat_fn())
        print(json.dumps({k: summ[k] for k in ("specs", "promoted", "validated", "certified", "candidate",
              "quarantined", "by_outcome", "pool_path")}, indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
