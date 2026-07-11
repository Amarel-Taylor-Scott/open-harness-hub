#!/usr/bin/env python3
"""scripts.primitive_buildout_orchestrator — use OUR LLM endpoints (Ollama / OpenWebUI-Gemma-4 / OpenRouter,
with automatic provider fallback) to GENERATE more executable primitives, then keep ONLY the ones that
ACTUALLY WORK by executing an oracle-backed test in a sandboxed subprocess. Generation is cheap; the gate is
execution — a primitive whose test does not pass is never staged.

The loop:  idea  ->  model generates {impl, oracle test}  ->  AST safety scan (stdlib-algorithm allowlist,
no os/sys/subprocess/open/eval/network)  ->  sandboxed subprocess run with a timeout  ->  keep iff the test
passes  ->  stage as an executable candidate card (canonical id, tier, real source as the body).

Also improves the DECOMPOSITION QUESTION BANK: asks the model to extend the question series used to break a
source into primitives, deduped and appended to a governed bank.

Standalone (no harness). Live lanes are opt-in; the default --self-test is fully offline (stub model) and
proves the generate -> safety-scan -> execute -> stage gate end to end, including that unsafe code is refused
and a failing test is rejected (never staged, never fabricated).

    python3 scripts/primitive_buildout_orchestrator.py --self-test
    python3 scripts/primitive_buildout_orchestrator.py --run --provider ollama --model gemma-4-coding --count 20
    python3 scripts/primitive_buildout_orchestrator.py --run --ideas-file ideas.jsonl --improve-questions
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap ─────────────────────────────────────────────────────────────────────────────────
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
import re  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"primitive_buildout_orchestrator requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-exec-gen"
CARD_RECORD_TYPE = "generated_executable_primitive_candidate"
STAGED_FILENAME = "executable_primitive_candidates.jsonl"  # shares the executable pool
_VERIFIED_CORPUS_FILENAMES = frozenset({"verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl"})
QUESTION_BANK_FILENAME = "primitive_decomposition_questions.jsonl"

#: import allowlist for GENERATED code — pure-algorithm stdlib only. Anything else fails the safety scan.
_IMPORT_ALLOWLIST = frozenset(
    "math heapq collections itertools functools bisect random re string typing dataclasses "
    "fractions decimal statistics array".split())
#: banned names anywhere in the AST (calls or attributes) — no side effects, no escape.
_BANNED_NAMES = frozenset(
    "eval exec compile open __import__ input globals locals vars getattr setattr delattr "
    "os sys subprocess socket shutil pathlib requests urllib importlib ctypes".split())

#: seed ideas across the three tiers (used when no ideas file/web-research is supplied). Each is a testable
#: algorithmic task the model can implement AND for which an oracle test exists.
_SEED_IDEAS: tuple[dict[str, str], ...] = (
    {"tier": "common", "name": "run length encode", "spec": "RLE-encode a string to [(char,count)]"},
    {"tier": "common", "name": "chunk overlap windows", "spec": "sliding windows of size k over a list"},
    {"tier": "rare", "name": "kadane max subarray", "spec": "max contiguous subarray sum"},
    {"tier": "rare", "name": "quickselect kth smallest", "spec": "kth smallest element in O(n) average"},
    {"tier": "rare", "name": "interval scheduling", "spec": "max non-overlapping intervals by finish time"},
    {"tier": "super_rare", "name": "z algorithm", "spec": "Z-array: longest substring from i matching prefix"},
    {"tier": "super_rare", "name": "manacher palindrome", "spec": "longest palindromic substring in O(n)"},
    {"tier": "super_rare", "name": "kruskal mst", "spec": "minimum spanning tree total weight via union-find"},
    {"tier": "super_rare", "name": "kahn longest path dag", "spec": "longest path length in a DAG"},
)


# ── LLM lane with provider fallback (fully utilizes our endpoints) ────────────────────────────────────────────

def multi_provider_transport(providers: list[str], model: str) -> Callable[[str, str], dict[str, Any]]:
    """Return call(system, user)->{ok,text,provider}; tries each provider in order, first success wins."""
    from scripts import _llm_client  # noqa: PLC0415
    resolved = [(name, _llm_client.resolve_provider(name)) for name in providers]

    def _call(system: str, user: str) -> dict[str, Any]:
        last_err = ""
        for name, provider in resolved:
            try:
                resp = _llm_client.chat(model, system, user, provider)  # inherit the high-ceiling default; never truncate generation
                if not resp.get("error") and (resp.get("text") or "").strip():
                    return {"ok": True, "text": resp["text"], "provider": name}
                last_err = str(resp.get("error") or "empty")[:120]
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)[:120]
        return {"ok": False, "error": last_err}
    return _call


# ── generation + parsing ─────────────────────────────────────────────────────────────────────────────────────

_GEN_SYSTEM = (
    "You are an expert algorithms engineer. You write a correct, self-contained Python implementation of a "
    "task AND an oracle-backed test that would FAIL if the implementation were wrong (compare against a "
    "brute-force oracle on small deterministic inputs; use random.Random(seed) only). Use only the Python "
    "standard library. Reply ONLY with JSON.")


def _gen_prompt(idea: dict[str, str]) -> str:
    return (
        f"Task ({idea.get('tier')} tier): {idea.get('name')} — {idea.get('spec')}.\n\n"
        "Reply ONLY as JSON:\n"
        '{"name": "...", "tier": "common|rare|super_rare", "mechanism": "one sentence naming the technique", '
        '"input": "typed noun", "output": "typed noun", '
        '"impl_code": "def ...():\\n    ...  # the implementation, stdlib only", '
        '"test_code": "def _test():\\n    assert ...  # oracle-backed, deterministic; calls the impl"}\n'
        "The test MUST call the implementation and assert against an independent oracle or known values.")


def parse_generation(text: str) -> Optional[dict[str, Any]]:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
                if isinstance(obj, dict) and obj.get("impl_code") and obj.get("test_code"):
                    return obj
                return None
    return None


# ── safety scan (AST allowlist) — GENERATED code is untrusted ─────────────────────────────────────────────────

def safe_to_execute(code: str) -> tuple[bool, str]:
    """AST-scan generated code: parseable, imports within the stdlib-algorithm allowlist, no banned names,
    no dunder attribute access. Returns (ok, reason)."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"syntax_error: {exc}"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in _IMPORT_ALLOWLIST:
                    return False, f"import_not_allowed: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in _IMPORT_ALLOWLIST:
                return False, f"import_from_not_allowed: {node.module}"
        elif isinstance(node, ast.Name) and node.id in _BANNED_NAMES:
            return False, f"banned_name: {node.id}"
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return False, f"dunder_attr: {node.attr}"
    return True, "ok"


def verify_primitive(impl_code: str, test_code: str, *, timeout: int = 10,
                     runner: Optional[Callable[[str], tuple[int, str]]] = None) -> dict[str, Any]:
    """Execute impl + oracle test in a SANDBOXED subprocess. Keeps ONLY if the test passes. Safety-scanned
    first. runner is injectable for the offline self-test."""
    combined = impl_code + "\n\n" + test_code + "\n\n_test()\nprint('PRIMITIVE_OK')\n"
    ok, reason = safe_to_execute(combined)
    if not ok:
        return {"works": False, "stage": "safety_scan", "reason": reason}
    run = runner or _default_sandbox_runner
    try:
        rc, out = run(combined) if runner else run(combined)  # runner may take (code, timeout)
    except TypeError:
        rc, out = run(combined, timeout)  # type: ignore[misc]
    works = rc == 0 and "PRIMITIVE_OK" in out
    return {"works": works, "stage": "executed", "reason": ("passed" if works else out[-200:])}


def _default_sandbox_runner(code: str, timeout: int = 10) -> tuple[int, str]:
    """Run code in a fresh subprocess with -I (isolated), a temp cwd, and a timeout. Pure-algorithm code only
    (enforced by safe_to_execute upstream)."""
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "gen.py"
        f.write_text(code)
        try:
            proc = subprocess.run([sys.executable, "-I", str(f)], capture_output=True, text=True,  # noqa: S603
                                  timeout=timeout, cwd=td, check=False)
        except subprocess.TimeoutExpired:
            return 124, "timeout"
        return proc.returncode, (proc.stdout + proc.stderr)


# ── card + staging ───────────────────────────────────────────────────────────────────────────────────────────

def _camel(*words: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", " ".join(words))
    return ("".join(p[:1].upper() + p[1:] for p in parts if p) or "Edge")[:48]


def _to_card(gen: dict[str, Any], *, provider: str) -> Optional[dict[str, Any]]:
    name = str(gen.get("name") or "").strip()
    impl = str(gen.get("impl_code") or "")
    tier = gen.get("tier") if gen.get("tier") in ("common", "rare", "super_rare") else "rare"
    if not name or "def " not in impl and "class " not in impl:
        return None
    title = f"{gen.get('mechanism') or name} [{re.sub(r'[^a-z0-9]+', '_', name.lower())}]"
    blackbox = (f"Generated executable primitive ({tier} tier): {gen.get('mechanism') or name}. "
                f"Input: {gen.get('input')}. Output: {gen.get('output')}. Verified by executing an "
                f"oracle-backed test in a sandbox; runs at 0 generation tokens when reused.")
    pid = canonical_id(CARD_PREFIX, title, impl)
    return {"record_type": CARD_RECORD_TYPE, "schema_version": 1, "kind": "route.primitive",
            "primitive_id": pid, "tier": tier, "title": title[:160], "blackbox": blackbox[:1200],
            "mechanism": str(gen.get("mechanism") or name)[:300],
            "input_edge": _camel(name, "input"), "output_edge": _camel(name, "result"),
            "capability_tags": [f"tier:{tier}", "executable", "generated", "coding_task"],
            "executable_body": impl, "oracle_test": str(gen.get("test_code") or ""), "language": "python",
            "contract": {"input": str(gen.get("input") or "")[:200], "output": str(gen.get("output") or "")[:200]},
            "provenance": {"minter": "scripts.primitive_buildout_orchestrator", "provider": provider,
                           "verified_by": "sandboxed_oracle_execution"},
            "promotion_blockers": ["license_review"], **BOUNDARY}


def staged_path() -> Path:
    return resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / STAGED_FILENAME


def stage_cards(cards: list[dict[str, Any]], target_path: Optional[Path] = None) -> dict[str, Any]:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    p = target_path or staged_path()
    if p.name != STAGED_FILENAME:
        raise ValueError(f"refusing to write to {p.name!r}")
    if p.is_symlink() or (p.exists() and p.resolve().name in _VERIFIED_CORPUS_FILENAMES):
        raise ValueError("refused: symlink or verified-corpus target")
    existing = {str(r.get("primitive_id")) for r in (read_jsonl_tolerant(p) if p.exists() else [])}
    appended = 0
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        for c in cards:
            if str(c["primitive_id"]) in existing:
                continue
            existing.add(str(c["primitive_id"]))
            fh.write(json.dumps(c, sort_keys=True) + "\n")
            appended += 1
    return {"appended": appended, "on_file": len(existing), "path": str(p), **BOUNDARY}


# ── orchestration ────────────────────────────────────────────────────────────────────────────────────────────

def orchestrate(ideas: list[dict[str, str]], transport: Callable[[str, str], dict[str, Any]], *,
                sandbox_runner: Optional[Callable[..., tuple[int, str]]] = None) -> dict[str, Any]:
    """Generate -> safety-scan -> execute -> keep-if-works, for each idea. Returns verified cards + a per-idea
    ledger. Nothing that fails to run is staged; nothing is fabricated."""
    cards: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    for idea in ideas:
        resp = transport(_GEN_SYSTEM, _gen_prompt(idea))
        if not resp.get("ok"):
            ledger.append({"idea": idea["name"], "outcome": "generation_failed", "detail": resp.get("error")})
            continue
        gen = parse_generation(resp["text"])
        if not gen:
            ledger.append({"idea": idea["name"], "outcome": "unparseable"})
            continue
        verdict = verify_primitive(gen["impl_code"], gen["test_code"], runner=sandbox_runner)
        if not verdict["works"]:
            ledger.append({"idea": idea["name"], "outcome": f"rejected_{verdict['stage']}",
                           "detail": verdict["reason"][:120]})
            continue
        card = _to_card(gen, provider=resp.get("provider", "stub"))
        if card:
            cards.append(card)
            ledger.append({"idea": idea["name"], "outcome": "verified_working", "id": card["primitive_id"]})
        else:
            ledger.append({"idea": idea["name"], "outcome": "card_build_failed"})
    return {"verified_cards": cards, "ledger": ledger, "n_ideas": len(ideas), "n_verified": len(cards),
            **BOUNDARY}


def improve_questions(current: list[str], transport: Callable[[str, str], dict[str, Any]]) -> dict[str, Any]:
    """Ask the model to EXTEND the decomposition question bank; dedupe against current. Additive, never a
    rewrite."""
    system = ("You improve a bank of QUESTIONS used to break a source (notebook/repo/paper) into reusable "
              "primitives. Propose sharper, more decompositional questions. Reply ONLY as JSON.")
    user = ("Current questions:\n" + json.dumps(current[:40], indent=1) + "\n\n"
            'Propose 10 NEW distinct questions that better surface reusable primitives (mechanism, edges, '
            'edge-cases, remix axes). Reply ONLY as JSON: {"questions": ["...", ...]}')
    resp = transport(system, user)
    if not resp.get("ok"):
        return {"added": 0, "questions": current, "error": resp.get("error")}
    parsed = parse_generation(resp["text"]) or {}
    proposed = parsed.get("questions") if isinstance(parsed, dict) else None
    if not isinstance(proposed, list):
        # tolerant: try a bare array
        try:
            arr = json.loads(resp["text"][resp["text"].find("["):resp["text"].rfind("]") + 1])
            proposed = arr if isinstance(arr, list) else []
        except Exception:  # noqa: BLE001
            proposed = []
    seen = {q.strip().lower() for q in current}
    added = [q for q in (str(x).strip() for x in proposed) if q and q.lower() not in seen]
    return {"added": len(added), "questions": current + added, "new": added}


# ── self-test (offline: stub model, injected sandbox runner) ──────────────────────────────────────────────────

_GOOD_IMPL = "def kadane(xs):\n    best = cur = xs[0]\n    for x in xs[1:]:\n        cur = max(x, cur + x)\n        best = max(best, cur)\n    return best"
_GOOD_TEST = ("def _test():\n    import random\n    def oracle(xs):\n        return max(sum(xs[i:j]) for i in "
              "range(len(xs)) for j in range(i+1, len(xs)+1))\n    r = random.Random(1)\n"
              "    for _ in range(50):\n        xs = [r.randint(-5,5) for _ in range(r.randint(1,8))]\n"
              "        assert kadane(xs) == oracle(xs)")


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # safety scan: allow pure stdlib algorithm code; refuse os/open/eval/network
    ok1, _ = safe_to_execute("import heapq\ndef f():\n    return heapq.heapify([])")
    ok2, r2 = safe_to_execute("import os\ndef f():\n    os.system('x')")
    ok3, r3 = safe_to_execute("def f():\n    open('/etc/passwd')")
    checks.append(("safety scan allows stdlib-algorithm imports", ok1))
    checks.append(("safety scan REFUSES os/subprocess", (not ok2) and "os" in r2))
    checks.append(("safety scan REFUSES open()", (not ok3) and "open" in r3))

    # verify_primitive with the REAL sandbox subprocess: a correct primitive passes
    good = verify_primitive(_GOOD_IMPL, _GOOD_TEST)
    checks.append(("a correct primitive PASSES the real sandbox oracle test", good["works"]))
    # a WRONG implementation fails (oracle catches it) — never staged
    bad_impl = "def kadane(xs):\n    return sum(xs)"
    bad = verify_primitive(bad_impl, _GOOD_TEST)
    checks.append(("a WRONG primitive is REJECTED by its oracle test", not bad["works"]))
    # unsafe code is refused before execution
    unsafe = verify_primitive("import socket\ndef kadane(xs):\n    return 0", _GOOD_TEST)
    checks.append(("unsafe generated code is refused at the safety scan (never executed)",
                   not unsafe["works"] and unsafe["stage"] == "safety_scan"))

    # orchestrate with a STUB model transport (deterministic) + the real sandbox
    def _stub(system: str, user: str) -> dict[str, Any]:
        if "kadane" in user or "max contiguous" in user:
            return {"ok": True, "provider": "stub",
                    "text": json.dumps({"name": "kadane max subarray", "tier": "rare",
                                        "mechanism": "Kadane running max", "input": "list[int]",
                                        "output": "int", "impl_code": _GOOD_IMPL, "test_code": _GOOD_TEST})}
        # a wrong one for a different idea -> must be rejected
        return {"ok": True, "provider": "stub",
                "text": json.dumps({"name": "broken thing", "tier": "common", "mechanism": "x",
                                    "input": "list", "output": "int", "impl_code": bad_impl,
                                    "test_code": _GOOD_TEST})}
    result = orchestrate([{"tier": "rare", "name": "kadane max subarray", "spec": "max contiguous subarray sum"},
                          {"tier": "common", "name": "broken thing", "spec": "will fail"}], _stub)
    checks.append(("orchestrate keeps the working primitive and REJECTS the broken one",
                   result["n_verified"] == 1
                   and any(l["outcome"] == "verified_working" for l in result["ledger"])
                   and any(l["outcome"].startswith("rejected") for l in result["ledger"])))
    checks.append(("verified card carries the executable body + oracle test + tier + boundary",
                   result["verified_cards"][0]["executable_body"].startswith("def kadane")
                   and result["verified_cards"][0]["oracle_test"]
                   and result["verified_cards"][0]["serves_truth"] is False))

    # staging: write-safe + append-dedupe
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td) / STAGED_FILENAME
        a = stage_cards(result["verified_cards"], target_path=tp)
        b = stage_cards(result["verified_cards"], target_path=tp)
        checks.append(("staging is append-dedupe + write-safe", a["appended"] == 1 and b["appended"] == 0))
    refused = False
    try:
        stage_cards(result["verified_cards"], target_path=Path(tempfile.gettempdir())
                    / "verified_factory_primitive_cards.jsonl")
    except ValueError:
        refused = True
    checks.append(("staging REFUSES a verified corpus filename", refused))

    # question-bank improvement (stub)
    def _q_stub(system: str, user: str) -> dict[str, Any]:
        return {"ok": True, "text": '{"questions":["What is the invariant?","What breaks at scale?"]}'}
    qi = improve_questions(["What are the components?"], _q_stub)
    checks.append(("question-bank improvement is additive + deduped", qi["added"] == 2 and len(qi["questions"]) == 3))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - primitive_buildout_orchestrator: our LLM endpoints (Ollama/Gemma-4/OpenRouter, provider "
          "fallback) GENERATE executable primitives; every one must pass an oracle test in an AST-safety-scanned "
          "sandbox subprocess to be staged (wrong -> rejected, unsafe -> refused, never fabricated); the "
          "decomposition question bank is improved additively. serves_truth=false.")
    return 0


def _load_ideas(path: Optional[str], count: int) -> list[dict[str, str]]:
    if path and Path(path).exists():
        from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
        rows = read_jsonl_tolerant(Path(path))
        ideas = [{"tier": r.get("tier", "rare"), "name": r.get("name") or r.get("area") or "",
                  "spec": r.get("spec") or r.get("why") or ""} for r in rows if (r.get("name") or r.get("area"))]
        return ideas[:count] if count else ideas
    seeds = list(_SEED_IDEAS)
    return (seeds * ((count // len(seeds)) + 1))[:count] if count else seeds


def _run(args: argparse.Namespace) -> int:
    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    transport = multi_provider_transport(providers, args.model)
    ideas = _load_ideas(args.ideas_file, args.count)
    result = orchestrate(ideas, transport)
    wrote = stage_cards(result["verified_cards"]) if result["verified_cards"] else {"appended": 0, "on_file": 0}
    rec = {"record_type": "primitive_buildout_receipt", "providers": providers, "model": args.model,
           "n_ideas": result["n_ideas"], "n_verified": result["n_verified"], "staged": wrote["appended"],
           "ledger": result["ledger"][:200], **BOUNDARY}
    if args.improve_questions:
        rec["question_improvement"] = {k: v for k, v in
                                       improve_questions(["What are the reusable components?"], transport).items()
                                       if k in ("added", "new")}
    out = resource("data") / "dev-intel" / "session_emulation" / "primitive_buildout_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({k: rec[k] for k in ("providers", "n_ideas", "n_verified", "staged")}, indent=2))
    print(f"\nreceipt: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--providers", default="ollama,openwebui,openrouter", help="comma-separated fallback order")
    ap.add_argument("--model", default="gemma-4-coding")
    ap.add_argument("--count", type=int, default=len(_SEED_IDEAS))
    ap.add_argument("--ideas-file", default=None, help="jsonl of {tier,name,spec} (e.g. web-research output)")
    ap.add_argument("--improve-questions", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
