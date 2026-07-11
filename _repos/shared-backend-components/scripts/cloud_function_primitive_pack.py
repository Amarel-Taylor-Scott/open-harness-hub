#!/usr/bin/env python3
"""scripts.cloud_function_primitive_pack — PROJECT-RELEVANT primitives for the cloud_function family, with oracle
fixtures (candidate-only). Closes the certification gap the real project A/B exposed.

Owner (2026-07-09): the live project A/B failed with 0 primitive reuse because dispatch returned IBAN/email/dedup
for an order-handler — we had no project-relevant primitives. These are exactly the sub-task primitives a
cloud_function_http_json handler needs (validate an order event, idempotency check, build an HTTP JSON error,
health response), so lane B (harness_plus_primitives) finally has something useful to inject and we can measure
REAL project-level lift. Self-contained; executor body = inspect.getsource; candidate=true/serves_truth=false.

    python3 scripts/cloud_function_primitive_pack.py --self-test
    python3 scripts/cloud_function_primitive_pack.py --emit
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
import inspect  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"cloud_function_primitive_pack requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CF_ID_PREFIX = "prim-cf"
CF_RECORD_TYPE = "cloud_function_primitive_candidate"
PACK_FILENAME = "cloud_function_primitive_cards.jsonl"
PACK_DIR_REL = "data/dev-intel/primitive_factory/specialized_packs"
PACKAGED_AT = "2026-07-09T00:00:00Z"


def validate_order_event(event: dict) -> dict:
    """Cloud function: validate an order event; returns {valid, errors}. Requires order_id + positive numeric amount."""
    errors = []
    if not event.get("order_id"):
        errors.append("missing_order_id")
    amount = event.get("amount")
    if amount is None or not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:
        errors.append("invalid_amount")
    return {"valid": len(errors) == 0, "errors": errors}


def idempotency_seen(key: str, seen: list) -> bool:
    """Cloud function: idempotency check — has this event key already been processed?"""
    return key in seen


def http_json_error(code: int, message: str) -> dict:
    """Cloud function: build an HTTP JSON error response with a status code."""
    return {"status": code, "error": message}


def health_response() -> dict:
    """Cloud function: standard health/status response."""
    return {"status": 200, "healthy": True}


_PRIMITIVES: list[dict[str, Any]] = [
    {"fn": validate_order_event, "cat": "cloud_function",
     "fixtures": [(({"order_id": "A1", "amount": 10},), {"valid": True, "errors": []}),
                  (({"order_id": "B2"},), {"valid": False, "errors": ["invalid_amount"]}),
                  (({"amount": 5},), {"valid": False, "errors": ["missing_order_id"]}),
                  (({"order_id": "C3", "amount": -1},), {"valid": False, "errors": ["invalid_amount"]})]},
    {"fn": idempotency_seen, "cat": "cloud_function",
     "fixtures": [(("A1", ["A1", "B2"]), True), (("C3", ["A1"]), False), (("X", []), False)]},
    {"fn": http_json_error, "cat": "cloud_function",
     "fixtures": [((400, "invalid_payload"), {"status": 400, "error": "invalid_payload"}),
                  ((404, "not_found"), {"status": 404, "error": "not_found"})]},
    {"fn": health_response, "cat": "cloud_function",
     "fixtures": [((), {"status": 200, "healthy": True})]},
]


def build_cards() -> list[dict[str, Any]]:
    cards = []
    for spec in _PRIMITIVES:
        fn: Callable = spec["fn"]
        name = fn.__name__
        cid = canonical_id(CF_ID_PREFIX, name, spec["cat"])
        cards.append({"record_type": CF_RECORD_TYPE, "kind": "cloud_function_deterministic_primitive",
                      "card_id": cid, "primitive_id": cid, "category": spec["cat"],
                      "title": f"{name} — cloud_function project primitive",
                      "blackbox": (inspect.getdoc(fn) or "").replace("\n", " ").strip(),
                      "domains": ["cloud_function_primitive", "project_relevant", "deterministic"],
                      "candidate": True, "serves_truth": False,
                      "executor": {"language": "python", "entry": name, "python_body": inspect.getsource(fn),
                                   "n_fixtures": len(spec["fixtures"]),
                                   "oracle_fixtures": [{"input": repr(a), "expected": repr(e)}
                                                       for a, e in spec["fixtures"]]},
                      "packaged_at": PACKAGED_AT})
    return cards


def emit() -> dict[str, Any]:
    cards = build_cards()
    out_dir = resource(PACK_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / PACK_FILENAME).open("w", encoding="utf-8") as fh:
        for c in cards:
            fh.write(json.dumps(c, sort_keys=True) + "\n")
    return {"pack_path": str(out_dir / PACK_FILENAME), "n_cards": len(cards)}


def self_test() -> bool:
    """ORACLE-gated: every fixture reproduces; a broken impl/fixture goes RED."""
    total = 0
    for spec in _PRIMITIVES:
        fn = spec["fn"]
        for args, expected in spec["fixtures"]:
            got = fn(*args)
            assert got == expected, f"{fn.__name__}{args!r}: got {got!r}, expected {expected!r}"
            total += 1
    cards = build_cards()
    assert len({c["card_id"] for c in cards}) == len(cards)
    print(f"OK cloud_function_primitive_pack self-test: {len(_PRIMITIVES)} project primitives "
          f"(validate_order_event/idempotency_seen/http_json_error/health_response), {total} oracle fixtures pass, "
          f"serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Project-relevant cloud_function primitives.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--emit", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.emit:
        print(json.dumps(emit(), indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
