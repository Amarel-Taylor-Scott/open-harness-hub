#!/usr/bin/env python3
"""kernel_pack_gateway_push — push the executable kernel-card packs into a capability gateway's serving
corpus through the OWNER admin lane (append-only overlay -> reindex -> served on next process start).

Owner (2026-07-11): "Proceed with all appropriate next steps … we will be providing more primitives,
formats, and use cases." This is the reusable intake lane those arrive through: any module that exposes
`emit_cards()` (the BDH-pattern kernel families) registers below as ONE row; the push validates nothing
away — the gateway forces candidate=true/serves_truth=false on write and reindex is lossless
(overlay + tombstones, never destructive).

    PYTHONPATH=. python3 scripts/kernel_pack_gateway_push.py --self-test
    PYTHONPATH=. python3 scripts/kernel_pack_gateway_push.py --collect          # list the packs + counts
    TAEDRI_ADMIN_KEY=… python3 scripts/kernel_pack_gateway_push.py --live      # push + reindex + poll
    TAEDRI_ADMIN_KEY=… GATEWAY_BASE=http://127.0.0.1:9500 python3 scripts/kernel_pack_gateway_push.py --live

The administrator key is read from the environment ONLY (never a flag, never logged, never persisted here);
the legacy name OH_SAAS_OWNER_KEY is still accepted as a fallback.
After a LIVE reindex completes, the running machine serves the new index on its next process start —
restart it (e.g. the fly-ops workflow: `flyctl apps restart`) and verify with a search probe.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
OWNER_KEY_ENVIRONMENT_VARIABLE = "TAEDRI_ADMIN_KEY"         # matches capability_saas_gateway
LEGACY_OWNER_KEY_ENVIRONMENT_VARIABLE = "OH_SAAS_OWNER_KEY"  # accepted fallback (OpenHub-era name)
GATEWAY_BASE_ENVIRONMENT_VARIABLE = "GATEWAY_BASE"          # default: the hosted taedri gateway
DEFAULT_GATEWAY_BASE = "https://taedri.fly.dev"
ADMIN_BATCH_SIZE = 500                                      # << the gateway's 10k cap; small enough to retry
REINDEX_POLL_SECONDS = 15
REINDEX_TIMEOUT_SECONDS = 600                               # the full-corpus rebuild loads ~557K cards


def _pack_registry() -> list[tuple[str, Callable[[], list[dict[str, Any]]]]]:
    """One row per kernel family (the extension seam). Import lazily so one broken module never blocks
    the others — a failed import is reported, not fatal."""
    rows: list[tuple[str, Callable[[], list[dict[str, Any]]]]] = []
    for module_name in ("reasoning_control_and_proof_primitives", "brain_inspired_primitives",
                        "physics_tracking_primitives", "math_foundations_primitives",
                        "associative_memory_primitives"):
        try:
            module = __import__(f"scripts.{module_name}", fromlist=["emit_cards"])
            rows.append((module_name, module.emit_cards))
        except Exception as error:  # noqa: BLE001
            print(f"  [skip] {module_name}: import failed: {error}", file=sys.stderr)
    return rows


def collect_cards() -> dict[str, Any]:
    """Gather every family's cards; duplicate primitive_ids collapse last-wins (the packs are disjoint by
    prefix, so a collision indicates a real bug and is reported)."""
    cards: dict[str, dict[str, Any]] = {}
    families: dict[str, int] = {}
    collisions: list[str] = []
    for name, emitter in _pack_registry():
        family_cards = emitter()
        families[name] = len(family_cards)
        for card in family_cards:
            pid = str(card.get("primitive_id") or "")
            if pid in cards:
                collisions.append(pid)
            cards[pid] = card
    return {"cards": list(cards.values()), "families": families, "collisions": collisions, **BOUNDARY}


def _post(base: str, path: str, payload: dict | None, owner_key: str) -> tuple[int, dict]:
    request = urllib.request.Request(
        base.rstrip("/") + path, method="POST",
        data=json.dumps(payload).encode("utf-8") if payload is not None else b"{}",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {owner_key}"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status, json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as error:  # type: ignore[attr-defined]
        return error.code, json.loads(error.read().decode("utf-8") or "{}")


def _get(base: str, path: str, owner_key: str) -> tuple[int, dict]:
    request = urllib.request.Request(base.rstrip("/") + path,
                                     headers={"Authorization": f"Bearer {owner_key}"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as error:  # type: ignore[attr-defined]
        return error.code, json.loads(error.read().decode("utf-8") or "{}")


def push(base: str, owner_key: str, *, wait_for_reindex: bool = True,
         poll_seconds: float = REINDEX_POLL_SECONDS,
         timeout_seconds: float = REINDEX_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Push every pack in bounded batches, trigger reindex, poll to completion. Read-only on the packs;
    append-only on the gateway; the result is a receipt, never a truth claim."""
    collected = collect_cards()
    cards = collected["cards"]
    accepted = 0
    for start in range(0, len(cards), ADMIN_BATCH_SIZE):
        code, result = _post(base, "/v1/admin/primitives", {"cards": cards[start:start + ADMIN_BATCH_SIZE]},
                             owner_key)
        if code != 200 or not result.get("ok"):
            return {"ok": False, "stage": "add", "http": code, "error": result.get("error", "")[:200],
                    "accepted_before_failure": accepted, **BOUNDARY}
        accepted += int(result.get("accepted") or 0)
    code, reindex = _post(base, "/v1/admin/reindex", {}, owner_key)
    if code != 200 or not reindex.get("ok"):
        return {"ok": False, "stage": "reindex_start", "http": code,
                "error": reindex.get("error", "")[:200], "accepted": accepted, **BOUNDARY}
    status: dict[str, Any] = {}
    if wait_for_reindex:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            code, status_body = _get(base, "/v1/admin/reindex", owner_key)
            status = status_body.get("status") or {}
            if status.get("done") or status.get("error"):
                break
            time.sleep(poll_seconds)
    return {"ok": bool(status.get("done")), "accepted": accepted, "families": collected["families"],
            "collisions": collected["collisions"], "reindex": status,
            "note": "served on the gateway's next process start — restart the machine, then probe search",
            **BOUNDARY}


def _self_test() -> int:
    import tempfile
    checks: list[tuple[str, bool]] = []

    # (1) collection: all four families emit; ids unique across packs; every card candidate-only + edged
    collected = collect_cards()
    checks.append(("5 families collect with unique ids; every card candidate-only with typed edges",
                   len(collected["families"]) == 5 and not collected["collisions"]
                   and len(collected["cards"]) == sum(collected["families"].values())
                   and all(card["candidate"] and not card["serves_truth"]
                           and card.get("input_edge") and card.get("output_edge")
                           for card in collected["cards"])))

    # (2) hermetic end-to-end against an in-process gateway: wrong key 403; right key accepts every card;
    #     overlay-only reindex (fixture empties the corpus files) completes and the serving index holds a
    #     card from EACH family (MUTATION-SENSITIVE: a dropped batch or family goes red)
    saved_key = os.environ.get(OWNER_KEY_ENVIRONMENT_VARIABLE)
    os.environ[OWNER_KEY_ENVIRONMENT_VARIABLE] = "test_owner_key_selftest"
    server = None
    try:
        with tempfile.TemporaryDirectory() as sandbox:
            from scripts.capability_saas_gateway import start_gateway  # noqa: PLC0415
            from scripts.capability_retrieval_mcp_server import _synthetic_search_index  # noqa: PLC0415
            server, _thread, port, gateway = start_gateway(
                port=0, data_dir=Path(sandbox) / "saas",
                fixtures={"index": _synthetic_search_index(), "reindex_corpus_files": []})
            base = f"http://127.0.0.1:{port}"
            denied_code, _denied = _post(base, "/v1/admin/primitives",
                                         {"cards": [{"primitive_id": "prim:x"}]}, "wrong_key")
            report = push(base, "test_owner_key_selftest", poll_seconds=0.2, timeout_seconds=30)
            served = json.loads((Path(sandbox) / "saas" / "serving_index.json").read_text())
            served_text = json.dumps(served)
            checks.append(("wrong key -> 403; push accepts every collected card",
                           denied_code == 403 and report["ok"]
                           and report["accepted"] == len(collected["cards"])))
            checks.append(("overlay reindex completes and serves one id from EACH family "
                           "(rcp + bio + trk + math + mem)",
                           report["reindex"].get("indexed_cards") == len(collected["cards"])
                           and all(prefix in served_text
                                   for prefix in ("prim:rcp", "prim:bio", "prim:trk", "prim:math",
                                                  "prim:mem"))))
    finally:
        if server is not None:
            server.shutdown()
        if saved_key is None:
            os.environ.pop(OWNER_KEY_ENVIRONMENT_VARIABLE, None)
        else:
            os.environ[OWNER_KEY_ENVIRONMENT_VARIABLE] = saved_key

    ok = all(v for _, v in checks)
    print("kernel_pack_gateway_push — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    print(f"  packs: {collected['families']} -> {len(collected['cards'])} cards. candidate-only; "
          "the gateway forces the truth bit on write.")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()
    if args.collect:
        collected = collect_cards()
        print(json.dumps({"families": collected["families"], "total": len(collected["cards"]),
                          "collisions": collected["collisions"]}, indent=2))
        return 0
    if args.live:
        owner_key = (os.environ.get(OWNER_KEY_ENVIRONMENT_VARIABLE)
                     or os.environ.get(LEGACY_OWNER_KEY_ENVIRONMENT_VARIABLE) or "")
        if not owner_key:
            print(f"refusing: set {OWNER_KEY_ENVIRONMENT_VARIABLE} in the environment (never a flag)")
            return 2
        base = os.environ.get(GATEWAY_BASE_ENVIRONMENT_VARIABLE) or DEFAULT_GATEWAY_BASE
        report = push(base, owner_key)
        print(json.dumps(report, indent=2))
        return 0 if report.get("ok") else 1
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
