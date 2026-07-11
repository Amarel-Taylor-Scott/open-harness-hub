#!/usr/bin/env python3
"""mint_vertical_pack — mint REAL, oracle-tested primitives to close a vertical's coverage gap.

The linker's token savings scale with COVERAGE (semantic_linker_token_bench: break-even ~40%, 76% at full). To take
a vertical to 100% we mint the primitives its residual capabilities need — but "minted" MUST mean a real, executable,
oracle-passing capability, never a stub that games the coverage metric (the standing no-proxy discipline). Reuse
first: only mint a capability the registry genuinely lacks (checked against the corpus before minting).

Each spec = {title, blackbox, input_edge, output_edge, body, oracle}. `mint_one` runs the body through ast.parse
(valid_syntax) + exec + the behavioral oracle (working); a card is emitted with verification_level='execution' ONLY
if the oracle passes — otherwise it is recorded as a FAILED candidate, never promoted. Cards are candidate=true,
serves_truth=false. IDs are deterministic (canonical bytes via zlib.crc32 — no hashlib, no truncation-only).

    PYTHONPATH=. python3 scripts/mint_vertical_pack.py --self-test
    PYTHONPATH=. python3 scripts/mint_vertical_pack.py --mint-auth   # mint the auth vertical's request->OpenApiDocument gap
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
import zlib
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_EDGE_FOUNDRY_DIR = _REPO / "data" / "dev-intel" / "aidevobserver_edge_foundry"


def _mint_id(prefix: str, *parts: str) -> str:
    """Deterministic id over canonical bytes (crc32, not hashlib; not truncation-only)."""
    canonical = "␟".join(str(p) for p in parts).encode("utf-8")
    return f"{prefix}:{zlib.crc32(canonical) & 0xFFFFFFFF:08x}"


def mint_one(spec: dict[str, Any]) -> dict[str, Any]:
    """Validate one primitive spec (ast.parse -> exec -> oracle) and shape its candidate card.

    Returns {card, valid_syntax, working, error}. ``working`` is True ONLY if the oracle passed on the real exec —
    a card whose oracle fails is candidate/verification_level='draft' and MUST NOT be treated as covering anything.
    """
    body, oracle = spec["body"], spec["oracle"]
    valid_syntax = working = False
    error = None
    run = None
    try:
        ast.parse(body)
        valid_syntax = True
        ns: dict[str, Any] = {}
        exec(compile(body, "<mint>", "exec"), ns)  # noqa: S102 — minting our OWN authored bodies, sandboxed ns
        run = ns.get("run")
        if callable(run):
            working = bool(oracle(run))
    except Exception as exc:  # noqa: BLE001 — a failed mint is recorded, never crashes the batch
        error = f"{type(exc).__name__}: {exc}"

    pid = _mint_id("prim:av", spec["title"], spec["input_edge"], spec["output_edge"])
    card = {
        "primitive_id": pid, "title": spec["title"], "blackbox": spec["blackbox"],
        "input_edge": spec["input_edge"], "output_edge": spec["output_edge"],
        "capability_tags": spec.get("capability_tags", []), "domains": spec.get("domains", []),
        "effects": spec.get("effects", []), "mutations": [],
        "trust": "candidate", "candidate": True, "serves_truth": False,
        "verification_level": "execution" if working else "draft",
        "source_family": "minted_vertical_pack", "source_evidence_status": "authored",
        "kind": "capability", "primitive_kind": "action",
        # carry the VERIFIED BODY so the card is WORKING (executable), not a descriptor
        "source_code": body, "body_sha": f"crc32:{zlib.crc32(body.encode()) & 0xFFFFFFFF:08x}",
        "has_working_body": working,
    }
    return {"card": card, "valid_syntax": valid_syntax, "working": working, "error": error}


def mint_pack(specs: list[dict[str, Any]], *, out_path: Optional[Path] = None) -> dict[str, Any]:
    """Mint a batch; write ONLY oracle-passing cards to the pack jsonl (append). Returns a receipt."""
    results = [mint_one(s) for s in specs]
    working = [r for r in results if r["working"]]
    out = Path(out_path or (_EDGE_FOUNDRY_DIR / "minted_vertical_pack_cards.jsonl"))
    out.parent.mkdir(parents=True, exist_ok=True)
    existing_ids = set()
    if out.exists():
        existing_ids = {json.loads(l).get("primitive_id") for l in out.read_text().splitlines() if l.strip()}
    appended = 0
    with out.open("a") as f:
        for r in working:
            if r["card"]["primitive_id"] not in existing_ids:
                f.write(json.dumps(r["card"], sort_keys=True) + "\n")
                appended += 1
    return {"specs": len(specs), "valid_syntax": sum(r["valid_syntax"] for r in results),
            "working": len(working), "appended": appended, "out": str(out),
            "failed": [{"title": s["title"], "error": r["error"]} for s, r in zip(specs, results) if not r["working"]],
            "cards": [r["card"] for r in working]}


# ================================================================================================================
# The AUTH vertical gap — a REAL request-body -> OpenApiDocument parser (the corpus has the URI loader + the
# validator + the emitter; it lacks a parser that turns a raw request body into a structured OpenAPI document).
# ================================================================================================================
def _auth_specs() -> list[dict[str, Any]]:
    return [{
        "title": "Parse OpenAPI Document From Request Body",
        "blackbox": "Parses an OpenAPI document from a raw JSON request body into a structured OpenAPI document.",
        "input_edge": "OpenApiRequestBody", "output_edge": "OpenApiDocument",
        "capability_tags": ["OpenApiDocument", "openapi", "parse", "decode"],
        "domains": ["openapi", "auth"],
        "body": ("import json\n"
                 "def run(body):\n"
                 "    if isinstance(body, (dict, list)):\n"
                 "        return body\n"
                 "    if isinstance(body, (bytes, bytearray)):\n"
                 "        body = body.decode('utf-8')\n"
                 "    return json.loads(body)\n"),
        # oracle: parses a JSON body into the equivalent document; idempotent on an already-parsed dict
        "oracle": lambda run: (run('{"openapi": "3.0.0", "info": {"title": "x"}}') == {"openapi": "3.0.0", "info": {"title": "x"}}
                               and run(b'{"a": 1}') == {"a": 1}
                               and run({"already": "parsed"}) == {"already": "parsed"}),
    }]


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    # (1) a GOOD spec mints working=True with verification_level=execution.
    good = mint_one(_auth_specs()[0])
    checks.append((f"good spec -> working (id {good['card']['primitive_id']}, vlevel {good['card']['verification_level']})",
                   good["working"] and good["card"]["verification_level"] == "execution"
                   and good["card"]["output_edge"] == "OpenApiDocument", json.dumps(good.get("error"))))

    # (2) MUTATION gate: a spec whose body returns the WRONG thing fails the oracle -> working=False, vlevel=draft
    #     (a stub can NEVER be minted as covering — the no-proxy discipline, enforced).
    bad = mint_one({"title": "Bad Parser", "blackbox": "returns nothing useful.", "input_edge": "OpenApiRequestBody",
                    "output_edge": "OpenApiDocument", "body": "def run(body):\n    return None\n",
                    "oracle": _auth_specs()[0]["oracle"]})
    checks.append(("mutation gate: wrong-behavior body fails oracle -> NOT working (vlevel draft)",
                   not bad["working"] and bad["card"]["verification_level"] == "draft", ""))

    # (3) SYNTAX gate: an unparseable body -> valid_syntax False, working False.
    broke = mint_one({"title": "Broken", "blackbox": "x", "input_edge": "A", "output_edge": "B",
                      "body": "def run(:\n bad", "oracle": lambda r: True})
    checks.append(("syntax gate: unparseable body -> not valid_syntax, not working",
                   not broke["valid_syntax"] and not broke["working"], ""))

    # (4) DETERMINISTIC id: same spec -> same id twice.
    checks.append(("mint id deterministic", mint_one(_auth_specs()[0])["card"]["primitive_id"] == good["card"]["primitive_id"], ""))

    ok = all(c[1] for c in checks)
    print(f"{'PASS' if ok else 'FAIL'} - mint_vertical_pack: ast.parse + exec + ORACLE gate (working=oracle-passing, "
          f"never a stub); candidate-only, deterministic ids, mutation/syntax gated")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Mint real oracle-tested primitives to close a vertical's coverage gap.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mint-auth", action="store_true", help="mint the auth vertical's request->OpenApiDocument parser gap")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.mint_auth:
        rec = mint_pack(_auth_specs())
        print(json.dumps({k: v for k, v in rec.items() if k != "cards"}, indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
