#!/usr/bin/env python3
"""scripts.hy3_primitive_certifier — grow the VERIFIED primitive set beyond 75 using the real Hy3 keys
(candidate-until-certified). Hy3 writes a deterministic function + its own oracle fixtures; we CERTIFY it (real
security scan -> sandbox oracle -> determinism) or reject with a reason.

Owner (2026-07-09): 75 is not big — we have thousands of candidate primitives and real Hy3 API keys; use them.
This is the scalable certification loop: a task description -> Hy3 (tencent/hy3:free, via the gitignored OpenRouter
pool) returns STRICT JSON {name, python_body, fixtures} -> robust parse (Hy3 buries the answer after heavy
reasoning; take the LAST balanced-brace object with the required keys) -> the SAME real gates the campaign uses
(no code runs before the security scan; isolated `python -I -S` sandbox vs the model's own fixtures; determinism)
-> certified into a growing pack, else rejected+preserved. Everything candidate=true/serves_truth=false until it
passes; nothing self-promotes.

    python3 scripts/hy3_primitive_certifier.py --self-test
    python3 scripts/hy3_primitive_certifier.py --run --limit 20 --model tencent/hy3:free
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
import json  # noqa: E402
import re  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"hy3_primitive_certifier requires canonical_id; import failed: {exc}")
from scripts.primitive_token_savings_ab import security_scan, sandbox_run, _load_pool, live_model  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
PACK_DIR_REL = "data/dev-intel/primitive_factory/specialized_packs"
RECEIPT_DIR_REL = "data/dev-intel/hy3_certifier"
PACK_FILENAME = "hy3_certified_primitive_cards.jsonl"

# ── task descriptions Hy3 implements + fixtures (common deterministic dev utilities; extend freely). ─────────
TASK_SPECS: list[str] = [
    "reverse the order of words in a sentence", "find the longest common prefix of a list of strings",
    "check whether two strings are anagrams of each other", "count the number of vowels in a string",
    "convert a string to title case", "find the first non-repeating character in a string (or empty if none)",
    "compute the mode (most common element) of a list of integers",
    "merge two already-sorted lists into one sorted list", "compute the dot product of two equal-length vectors",
    "transpose a rectangular matrix (list of lists)", "flatten an arbitrarily nested list of integers",
    "compute the nth triangular number", "check whether an integer is a perfect square",
    "convert an integer to its binary string without a 0b prefix", "count set bits (popcount) of an integer",
    "compute the greatest common divisor of a list of integers", "return the running maximum of a list",
    "group a list of strings by their first letter into a dict", "compute the Jaccard similarity of two sets",
    "encode a list of integers as run-length pairs [value, count]",
    "check whether parentheses in a string are balanced", "compute the factorial of n modulo 1000000007",
    "return the k smallest elements of a list, ascending", "rotate a string right by n characters",
    "compute the Hamming weight difference between two equal-length bit strings",
    "convert a Roman numeral string to an integer", "compute the sum of proper divisors of an integer",
    "determine whether a year is a leap year", "convert seconds to an H:MM:SS string",
    "compute the average of a list of numbers rounded to 2 decimals",
    "return the unique elements of a list preserving order", "check whether a list is sorted ascending",
    "compute the Levenshtein edit distance between two strings", "title-case only words longer than 3 letters",
    "return the indices where a target appears in a list", "compute the median of a list of numbers",
    "convert a snake_case string to kebab-case", "count words in a string ignoring extra whitespace",
    "return the intersection of two lists preserving first list order",
    "compute the cumulative product of a list of integers",
]


def build_prompt(task: str) -> str:
    return (f"Write a single deterministic, pure-standard-library Python function that will: {task}.\n"
            f"Return ONLY strict JSON (no prose, no markdown) with exactly these keys:\n"
            f'{{"name": "<snake_case_fn_name>", "python_body": "<the complete def ...:\\n    ... function '
            f'source, self-contained, imports inside the function if needed>", "fixtures": [[[<args...>], '
            f'<expected>], ...]}}\n'
            f"Provide at least 3 fixtures. Args are a JSON array of positional arguments. Deterministic only; "
            f"no I/O, no randomness, no network, no os/sys/subprocess.")


def parse_hy3(text: str) -> dict[str, Any] | None:
    """Take the LAST balanced-brace JSON object carrying name+python_body+fixtures (Hy3 buries it in reasoning)."""
    best = None
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                blob = text[start:i + 1]
                try:
                    obj = json.loads(blob)
                except Exception:  # noqa: BLE001
                    continue
                if isinstance(obj, dict) and obj.get("python_body") and obj.get("name") and obj.get("fixtures"):
                    best = obj
    return best


def _to_fixtures(raw: Any) -> list[tuple]:
    out = []
    for item in raw or []:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            args, expected = item
            out.append((tuple(args) if isinstance(args, list) else (args,), expected))
    return out


def certify_draft(name: str, body: str, fixtures: list[tuple]) -> dict[str, Any]:
    """Same real gates as the campaign: security scan -> sandbox oracle -> determinism."""
    if not re.match(r"\s*def\s+\w+", body):
        return {"name": name, "certified": False, "stage_failed": "shape", "reason": "not_a_def"}
    banned = security_scan(body)
    if banned:
        return {"name": name, "certified": False, "stage_failed": "security", "reason": f"banned:{banned}"}
    if not fixtures:
        return {"name": name, "certified": False, "stage_failed": "fixtures", "reason": "no_fixtures"}
    entry = re.search(r"def\s+(\w+)", body).group(1)
    r1 = sandbox_run(body, entry, fixtures)
    if not (r1["ran"] and r1["n_total"] > 0 and r1["n_pass"] == r1["n_total"]):
        return {"name": name, "certified": False, "stage_failed": "oracle",
                "reason": r1.get("error") or f"{r1['n_pass']}/{r1['n_total']}"}
    r2 = sandbox_run(body, entry, fixtures)
    if (r2["n_pass"], r2["n_total"]) != (r1["n_pass"], r1["n_total"]):
        return {"name": name, "certified": False, "stage_failed": "determinism", "reason": "non_deterministic"}
    return {"name": name, "entry": entry, "certified": True, "n_fixtures": r1["n_total"],
            "receipts": ["security", "oracle", "determinism"], **BOUNDARY}


def run(limit: int, model: str = "tencent/hy3:free") -> dict[str, Any]:
    pool = _load_pool()
    if not pool:
        return {"error": "no_openrouter_pool", "certified": 0}
    tasks = TASK_SPECS[:limit]
    certified, rejected = [], []
    cards = []
    for task in tasks:
        gen = live_model(build_prompt(task), pool, model)
        if not gen["code"]:
            rejected.append({"task": task, "stage_failed": "generation", "reason": gen["error"]})
            continue
        obj = parse_hy3(gen["code"])
        if not obj:
            rejected.append({"task": task, "stage_failed": "parse", "reason": "no_json_object"})
            continue
        name = re.sub(r"\W+", "_", str(obj["name"]))[:60] or "hy3_fn"
        rc = certify_draft(name, obj["python_body"], _to_fixtures(obj["fixtures"]))
        if rc["certified"]:
            certified.append(rc)
            cid = canonical_id("prim-hy3cert", name, str(rc["n_fixtures"]))
            cards.append({"record_type": "hy3_certified_primitive", "card_id": cid, "primitive_id": cid,
                          "title": f"{name} — hy3-generated + certified", "task": task,
                          "executor": {"language": "python", "entry": rc["entry"], "python_body": obj["python_body"],
                                       "n_fixtures": rc["n_fixtures"], "receipts": rc["receipts"]},
                          "lifecycle": "certified", **BOUNDARY})
        else:
            rejected.append({"task": task, **rc})
    if cards:
        out_dir = resource(PACK_DIR_REL)
        out_dir.mkdir(parents=True, exist_ok=True)
        with (out_dir / PACK_FILENAME).open("a", encoding="utf-8") as fh:  # append: accumulate across runs
            for c in cards:
                fh.write(json.dumps(c, sort_keys=True) + "\n")
    return {"record_type": "hy3_certification_run", "model": model, "attempted": len(tasks),
            "certified": len(certified), "rejected": len(rejected),
            "yield": round(len(certified) / len(tasks), 3) if tasks else 0.0,
            "certified_names": [c["name"] for c in certified],
            "rejection_reasons": _tally(r.get("stage_failed", "?") for r in rejected), **BOUNDARY}


def _tally(it: Any) -> dict[str, int]:
    out: dict[str, int] = {}
    for x in it:
        out[x] = out.get(x, 0) + 1
    return out


def self_test() -> bool:
    """Mutation-gated (offline): the parser recovers a buried JSON draft; the REAL gates certify a correct draft
    and REJECT a wrong-fixture / dangerous / non-def draft. No network."""
    buried = ('Let me think about this...\n{"reasoning": "ignore me"}\nHere is the answer:\n'
              '{"name": "add_one", "python_body": "def add_one(x):\\n    return x + 1\\n", '
              '"fixtures": [[[1], 2], [[0], 1], [[-5], -4]]}\nDone.')
    obj = parse_hy3(buried)
    assert obj and obj["name"] == "add_one", f"parser must recover the buried draft: {obj}"
    fx = _to_fixtures(obj["fixtures"])
    assert certify_draft("add_one", obj["python_body"], fx)["certified"] is True, "correct draft must certify"

    # wrong fixture -> oracle fail.
    bad = certify_draft("add_one", "def add_one(x):\n    return x + 1\n", [((1,), 999)])
    assert bad["certified"] is False and bad["stage_failed"] == "oracle"
    # dangerous body -> security fail (no execution).
    ev = certify_draft("evil", "def evil(x):\n    import os\n    return os.getcwd()\n", [((1,), 1)])
    assert ev["stage_failed"] == "security"
    # not a def -> shape fail.
    assert certify_draft("x", "return 1", [((1,), 1)])["stage_failed"] == "shape"

    assert len(TASK_SPECS) >= 30
    print(f"OK hy3_primitive_certifier self-test: parser recovers buried JSON; real gates certify a correct draft "
          f"+ reject wrong-fixture/dangerous/non-def; {len(TASK_SPECS)} task specs ready; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Grow the verified set via Hy3 (generate function+fixtures -> certify).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--model", default="tencent/hy3:free")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.run:
        res = run(args.limit, args.model)
        out_dir = resource(RECEIPT_DIR_REL)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "hy3_certification_run.json").write_text(json.dumps(res, indent=2, sort_keys=True),
                                                            encoding="utf-8")
        print(json.dumps(res, indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
