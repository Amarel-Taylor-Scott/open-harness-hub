#!/usr/bin/env python3
"""scripts.check_supermemory_candidate_catalog — proof (CANDIDATE, NEVER ACTIVE): the REQUIRED catalog shape
for a memory/context provider — a Supermemory api adapter AND an MCP adapter must each be cataloged as
``status=candidate``, declare a working FALLBACK/STUB the correctness invariant runs on, and list contract_tests that
any replacement must keep green. Supermemory is a CANDIDATE provider behind Baltor wrappers — never the
active source of truth and never the wired runtime.

Two parts, so the self-test is non-vacuous regardless of integration order:

  1. FIXTURE (always asserted): build a deterministic temp capability-catalog containing exactly the two
     memory entries (memory.supermemory_api@candidate + mcp.supermemory@candidate) and assert the required
     shape holds — status candidate, a declared fallback/stub, a non-empty contract_tests list, and that an
     `active` memory provider entry (the local/emulator) is the wired one. A NEGATIVE fixture (status
     forced to `active`, or fallback removed) is correctly REJECTED, so the shape check actually bites.

  2. REAL CATALOG (asserted only IF present — MAIN adds the entries during integration): if
     architecture/external_capability_catalog.json already contains the two memory slots, assert THOSE
     real entries satisfy the same required shape. Do NOT hard-fail if the entries are absent yet.

Deterministic, stdlib-only, offline (tempfile fixture; injected ids; no RNG, no network). The correctness invariant
needs NO credentials — Supermemory stays a catalog candidate; the working provider is local/emulator.

CLI: python3 scripts/check_supermemory_candidate_catalog.py --self-test
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

#: the real catalog MAIN integrates into (asserted only when the memory entries already exist there).
_REAL_CATALOG = _REPO / "architecture" / "external_capability_catalog.json"

#: the two memory adapter ids that MUST be cataloged as candidates (single source — used by fixture + real).
_SUPERMEMORY_API_ADAPTER_ID = "memory.supermemory_api@candidate"
_SUPERMEMORY_MCP_ADAPTER_ID = "mcp.supermemory@candidate"
_CANDIDATE_ADAPTER_IDS = (_SUPERMEMORY_API_ADAPTER_ID, _SUPERMEMORY_MCP_ADAPTER_ID)

#: the status a Supermemory entry MUST carry. NEVER 'active' — Supermemory is not the wired source of truth.
_REQUIRED_STATUS = "candidate"

#: the contract proofs the memory slot's replacement must keep green (the candidate must list >=1 of these).
_MEMORY_CONTRACT_TESTS = (
    "check_memory_provider_contract",
    "check_supermemory_emulator",
    "check_local_memory_provider",
    "check_memory_results_become_artifacts",
    "check_memory_provider_full_stack",
)


def _entry_shape_problems(entry: dict, *, where: str) -> list[str]:
    """Return the list of shape violations for one cataloged memory candidate entry (empty == well-formed).

    Required shape for a memory/context CANDIDATE: status==candidate, a declared fallback/stub the reference
    path runs on, and a non-empty contract_tests list. Accepts either the top-level slot schema
    (fallback_adapters/contract_proofs) or a normalized {fallback, contract_tests} shape, so the same check
    serves the temp fixture AND the real architecture catalog.
    """
    problems: list[str] = []
    status = entry.get("status")
    if status != _REQUIRED_STATUS:
        problems.append(f"{where}: status={status!r} (must be {_REQUIRED_STATUS!r}, never active)")
    # a declared fallback/stub — the working offline provider the correctness invariant uses when the candidate is dead.
    fallback = entry.get("fallback") or entry.get("fallback_adapters") or entry.get("fallback_or_stub")
    if not fallback:
        problems.append(f"{where}: missing a declared fallback/stub (correctness invariant must run without the candidate)")
    # contract_tests the replacement must keep green.
    tests = entry.get("contract_tests") or entry.get("contract_proofs") or []
    if not isinstance(tests, list) or len(tests) < 1:
        problems.append(f"{where}: contract_tests must be a non-empty list")
    return problems


def _make_fixture_catalog(dirpath: Path) -> Path:
    """Write a deterministic temp capability-catalog: the active local/emulator memory provider (wired) plus
    the two Supermemory CANDIDATE entries. No RNG, no wall-clock — a fixed, JSON-roundtrippable document."""
    catalog = {
        "version": "fixture-1.0",
        "purpose": "deterministic fixture for check_supermemory_candidate_catalog (not the real catalog)",
        "status_enum": ["active", "candidate", "experimental", "deprecated", "quarantined", "replaced",
                        "foil", "reference"],
        "capability_slots": [
            {
                "capability_slot": "memory_provider",
                "category": "post_llm",
                "description": "Governed memory/context provider behind the MemoryProviderPort.",
                # the WIRED active provider is the working local store — Supermemory is NOT wired.
                "status": "active",
                "adapter_id": "memory.baltor_local@v1",
                "fallback_adapters": ["memory.supermemory_emulator@v1"],
                "contract_tests": list(_MEMORY_CONTRACT_TESTS),
                "adapters": [
                    {"adapter_id": "memory.baltor_local@v1", "role": "stub", "status": "active",
                     "import_module": None, "note": "working offline local provider; correctness invariant"},
                    {"adapter_id": "memory.supermemory_emulator@v1", "role": "fallback", "status": "active",
                     "import_module": None, "note": "deterministic offline emulator; correctness invariant"},
                    {"adapter_id": _SUPERMEMORY_API_ADAPTER_ID, "role": "candidate", "status": _REQUIRED_STATUS,
                     "import_module": None, "credential_ref": "env://SUPERMEMORY_API_KEY",
                     "note": "candidate contract stub; never imported as runtime; never source of truth"},
                ],
                # the candidate sub-entry the proof asserts (status candidate + fallback + contract_tests).
                "candidate_entry": {
                    "adapter_id": _SUPERMEMORY_API_ADAPTER_ID,
                    "status": _REQUIRED_STATUS,
                    "fallback": "memory.supermemory_emulator@v1",
                    "contract_tests": list(_MEMORY_CONTRACT_TESTS),
                    "credential_ref": "env://SUPERMEMORY_API_KEY",
                },
            },
            {
                "capability_slot": "mcp_tool_provider",
                "category": "post_llm",
                "description": "Governed memory MCP tools (memory/recall/context) behind the MemoryMCPProviderPort.",
                "status": _REQUIRED_STATUS,
                "adapter_id": _SUPERMEMORY_MCP_ADAPTER_ID,
                "fallback_adapters": ["memory.supermemory_emulator@v1"],
                "contract_tests": list(_MEMORY_CONTRACT_TESTS),
                "candidate_entry": {
                    "adapter_id": _SUPERMEMORY_MCP_ADAPTER_ID,
                    "status": _REQUIRED_STATUS,
                    "fallback": "memory.supermemory_emulator@v1",
                    "contract_tests": list(_MEMORY_CONTRACT_TESTS),
                    "credential_ref": "env://SUPERMEMORY_API_KEY",
                },
            },
        ],
    }
    path = dirpath / "fixture_external_capability_catalog.json"
    path.write_text(json.dumps(catalog, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _find_candidate_entries(catalog: dict) -> dict[str, dict]:
    """Locate the two Supermemory candidate entries in a catalog (fixture or real), keyed by adapter_id.

    A slot's `candidate_entry` is preferred (already normalized); otherwise we synthesize the normalized
    {status, fallback, contract_tests} view from the slot OR from a matching sub-adapter. Returns only the
    adapter_ids actually found (so the real-catalog branch can decide whether to assert)."""
    found: dict[str, dict] = {}
    for slot in catalog.get("capability_slots", []):
        if not isinstance(slot, dict):
            continue
        ce = slot.get("candidate_entry")
        slot_adapter = slot.get("adapter_id")
        sub_adapters = slot.get("adapters", []) if isinstance(slot.get("adapters"), list) else []
        for want in _CANDIDATE_ADAPTER_IDS:
            if want in found:
                continue
            # 1) explicit normalized candidate_entry on the slot
            if isinstance(ce, dict) and ce.get("adapter_id") == want:
                found[want] = ce
                continue
            # 2) the slot itself is the candidate (adapter_id == want, status candidate)
            if slot_adapter == want:
                found[want] = {
                    "adapter_id": want,
                    "status": slot.get("status"),
                    "fallback": slot.get("fallback_adapters") or slot.get("fallback_or_stub"),
                    "contract_tests": slot.get("contract_tests") or slot.get("contract_proofs"),
                }
                continue
            # 3) a matching sub-adapter inside the slot's adapters[] — inherit the slot's fallback/tests
            for sub in sub_adapters:
                if isinstance(sub, dict) and sub.get("adapter_id") == want:
                    found[want] = {
                        "adapter_id": want,
                        "status": sub.get("status"),
                        "fallback": slot.get("fallback_adapters") or slot.get("fallback_or_stub")
                        or [a.get("adapter_id") for a in sub_adapters if isinstance(a, dict)
                            and a.get("role") in ("stub", "fallback")],
                        "contract_tests": slot.get("contract_tests") or slot.get("contract_proofs"),
                    }
                    break
    return found


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── PART 1: deterministic temp FIXTURE (always asserted; non-vacuous regardless of integration order) ──
    tmp = Path(tempfile.mkdtemp(prefix="memcatalog_selftest_"))
    try:
        fpath = _make_fixture_catalog(tmp)
        catalog = json.loads(fpath.read_text(encoding="utf-8"))

        entries = _find_candidate_entries(catalog)
        check("fixture: both Supermemory candidate entries are present (api + mcp)",
              set(entries) == set(_CANDIDATE_ADAPTER_IDS), str(sorted(set(_CANDIDATE_ADAPTER_IDS) - set(entries))))
        for adapter_id, entry in entries.items():
            kind = "mcp" if adapter_id.startswith("mcp.") else "api"
            problems = _entry_shape_problems(entry, where=f"fixture/{kind}")
            check(f"fixture: {kind} candidate ({adapter_id}) is status=candidate + has fallback/stub + contract_tests",
                  problems == [], str(problems))

        # the WIRED active memory provider is the local/emulator — NOT Supermemory.
        mem_slot = next((s for s in catalog["capability_slots"] if s.get("capability_slot") == "memory_provider"), {})
        check("fixture: the WIRED active memory provider is the local/emulator (Supermemory is NOT active)",
              mem_slot.get("status") == "active" and mem_slot.get("adapter_id", "").startswith("memory.baltor_local"),
              f"wired={mem_slot.get('adapter_id')!r} status={mem_slot.get('status')!r}")

        # NEGATIVE: force a candidate to status=active → the shape check must REJECT it (it actually bites).
        forced_active = dict(entries[_SUPERMEMORY_API_ADAPTER_ID]); forced_active["status"] = "active"
        check("fixture NEGATIVE: a Supermemory entry forced to status=active is REJECTED",
              _entry_shape_problems(forced_active, where="neg") != [])
        # NEGATIVE: remove the fallback → rejected (correctness invariant must always have a working fallback).
        no_fallback = {k: v for k, v in entries[_SUPERMEMORY_MCP_ADAPTER_ID].items() if k != "fallback"}
        check("fixture NEGATIVE: a candidate with NO fallback/stub is REJECTED",
              _entry_shape_problems(no_fallback, where="neg") != [])
        # NEGATIVE: empty contract_tests → rejected.
        no_tests = dict(entries[_SUPERMEMORY_API_ADAPTER_ID]); no_tests["contract_tests"] = []
        check("fixture NEGATIVE: a candidate with empty contract_tests is REJECTED",
              _entry_shape_problems(no_tests, where="neg") != [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # ── PART 2: the REAL catalog (asserted only IF MAIN has already added the entries) ──
    if _REAL_CATALOG.is_file():
        real = json.loads(_REAL_CATALOG.read_text(encoding="utf-8"))
        real_entries = _find_candidate_entries(real)
        present = sorted(real_entries)
        if not present:
            check("real catalog: Supermemory entries not yet integrated (OK — MAIN adds them; fixture is the proof)",
                  True, "")
            print("  [info] architecture/external_capability_catalog.json has no memory.supermemory_* entries yet "
                  "(integration pending) — fixture assertions above are the non-vacuous proof.")
        else:
            for adapter_id, entry in real_entries.items():
                kind = "mcp" if adapter_id.startswith("mcp.") else "api"
                problems = _entry_shape_problems(entry, where=f"real/{kind}")
                check(f"real catalog: {kind} entry ({adapter_id}) is status=candidate + fallback/stub + contract_tests",
                      problems == [], str(problems))
            # if EITHER real entry exists, it must NEVER be active.
            for adapter_id, entry in real_entries.items():
                check(f"real catalog: {adapter_id} is NOT active (Supermemory is a candidate, never the wired truth)",
                      entry.get("status") != "active", f"status={entry.get('status')!r}")
    else:
        check("real catalog file absent (OK — fixture is the non-vacuous proof)", True)

    print(f"\n{'PASS — check_supermemory_candidate_catalog: a memory provider catalog entry must be status=candidate + declare a fallback/stub + list contract_tests (fixture asserts the shape and a forced-active/no-fallback/no-tests entry is rejected); the MCP candidate likewise; the wired active provider is the local/emulator; if the real architecture catalog already contains memory.supermemory_api@candidate / mcp.supermemory@candidate they are asserted well-formed and never active.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: Supermemory is cataloged as a CANDIDATE memory/MCP provider "
                                            "(status candidate + fallback/stub + contract_tests), never active.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
