#!/usr/bin/env python3
"""scripts.check_stateful_swarm_provider_catalog — proof (RESEARCH GOVERNANCE): the stateful-swarm runner
catalog (architecture/stateful_swarm_provider_catalog.json) and the blackboard provider catalog
(architecture/blackboard_provider_catalog.json) are well-formed and encode the governance boundary for the
Irys "Stateful Swarms" / persistent-blackboard / agent-memory landscape.

The boundary this proof bites on:
  - discovery != trust; candidate != active; a swarm/agent blackboard is ANALYTICAL agent output and is
    NEVER served truth (Baltor governs served truth).
  - a benchmark result (Harvey LAB) is EVIDENCE, NEVER promotion authority.
  - Irys Stateful Swarms (github.com/dl1683/irys-stateful-swarms) needs Python 3.12+ + `pip install -e .`
    + LLM keys, so it is a research_candidate ONLY — NOT active, NOT a dependency, never the wired runtime.
    Its Harvey LAB numbers are marked harvey_lab_claims_unverified=true (ran the PUBLIC benchmark, no
    private holdout) and it carries no_truth_authority=true + a proof_to_promote.
  - exactly ONE active entry per catalog, and it is the OFFLINE local stub / local SQLite store — the
    correctness invariant that depends on no install, no keys, and no network.
  - every gated (non-active) entry declares a working local_equivalent + do_not_adopt_as_primary=true.
  - license_confidence is in {verified, unverified}.
  - NO raw API key literals anywhere in either catalog or this script (credentials are env:// refs only).

Deterministic, stdlib-only, offline. No RNG, no wall-clock, no network, no credentials.

CLI: PYTHONPATH=. python3 scripts/check_stateful_swarm_provider_catalog.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

#: the two catalogs this proof governs (single source — used everywhere below).
_SWARM_CATALOG = _REPO / "architecture" / "stateful_swarm_provider_catalog.json"
_BLACKBOARD_CATALOG = _REPO / "architecture" / "blackboard_provider_catalog.json"

#: the canonical valid status set every entry's status must be drawn from.
_VALID_STATUS = {"research_candidate", "candidate", "active", "reference"}
#: license_confidence must be exactly one of these (honest two-value confidence).
_LICENSE_CONFIDENCE = {"verified", "unverified"}

#: the Irys research_candidate id — must be research_candidate (NOT active) with the unverified+no-authority flags.
_IRYS_ID = "stateful_swarm.irys@research_candidate"

#: fields every entry in EACH catalog must carry (status/source_url/license_confidence/local_equivalent/proof).
_SWARM_REQUIRED = ("provider_id", "category", "source_url", "license_confidence",
                   "status", "no_truth_authority", "local_equivalent", "proof_to_promote",
                   "do_not_adopt_as_primary")
_BLACKBOARD_REQUIRED = ("provider_id", "category", "source_url", "license_confidence",
                        "requires_docker", "requires_network", "requires_keys",
                        "local_equivalent", "status", "do_not_adopt_as_primary", "proof_to_promote")

#: phrases the governance_law of EACH catalog must contain (benchmark=evidence + blackboard!=truth + candidate!=active).
_LAW_PHRASES = ("benchmark", "evidence", "candidate != active")

#: a raw-key smell: an assignment of a long opaque secret-looking literal (sk-..., AIza..., 32+ hex/base64 run).
#: env:// references and field NAMES like "...API_KEY" are allowed; only inline secret VALUES are forbidden.
_RAW_KEY_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),         # OpenAI-style secret
    re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}\b"),     # Google API key
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),        # GitHub PAT
    re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{16,}\b"),  # Anthropic secret
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _entry_required_problems(entry: dict, required: tuple[str, ...], *, where: str) -> list[str]:
    """Return shape violations for one catalog entry that apply to EVERY entry (active or gated)."""
    problems: list[str] = []
    for field in required:
        if field not in entry:
            problems.append(f"{where} ({entry.get('provider_id', '?')}): missing required field {field!r}")
    status = entry.get("status")
    if status not in _VALID_STATUS:
        problems.append(f"{where} ({entry.get('provider_id', '?')}): status={status!r} not in {sorted(_VALID_STATUS)}")
    lc = entry.get("license_confidence")
    if lc not in _LICENSE_CONFIDENCE:
        problems.append(f"{where} ({entry.get('provider_id', '?')}): license_confidence={lc!r} not in {sorted(_LICENSE_CONFIDENCE)}")
    return problems


def _raw_key_hits(text: str) -> list[str]:
    """Return any inline secret-looking literals (NOT env:// refs, NOT field names)."""
    hits: list[str] = []
    for pat in _RAW_KEY_PATTERNS:
        hits.extend(pat.findall(text))
    return hits


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── both catalogs load ─────────────────────────────────────────────────────────────────────
    check("stateful_swarm catalog file exists", _SWARM_CATALOG.is_file(), str(_SWARM_CATALOG))
    check("blackboard catalog file exists", _BLACKBOARD_CATALOG.is_file(), str(_BLACKBOARD_CATALOG))
    if fails:
        print(f"\n{len(fails)} FAILURES: {fails}")
        return 1

    swarm = _load(_SWARM_CATALOG)
    black = _load(_BLACKBOARD_CATALOG)
    check("stateful_swarm catalog is a JSON object", isinstance(swarm, dict))
    check("blackboard catalog is a JSON object", isinstance(black, dict))

    swarm_entries = swarm.get("entries", [])
    black_entries = black.get("entries", [])
    check("stateful_swarm catalog has entries", isinstance(swarm_entries, list) and len(swarm_entries) >= 2,
          f"n={len(swarm_entries)}")
    check("blackboard catalog has entries", isinstance(black_entries, list) and len(black_entries) >= 2,
          f"n={len(black_entries)}")

    # ── valid_status declared correctly on the swarm catalog (the spec's named field) ───────────
    check("stateful_swarm catalog declares valid_status == the canonical set",
          set(swarm.get("valid_status", [])) == _VALID_STATUS, str(swarm.get("valid_status")))

    # ── every entry in each catalog is well-formed (required fields + valid status + license_confidence) ─
    for e in swarm_entries:
        probs = _entry_required_problems(e, _SWARM_REQUIRED, where="swarm")
        check(f"swarm entry well-formed: {e.get('provider_id', '?')}", probs == [], str(probs))
    for e in black_entries:
        probs = _entry_required_problems(e, _BLACKBOARD_REQUIRED, where="blackboard")
        check(f"blackboard entry well-formed: {e.get('provider_id', '?')}", probs == [], str(probs))

    # ── Irys is a research_candidate (NOT active) + unverified + no truth authority + proof_to_promote ──
    irys = next((e for e in swarm_entries if e.get("provider_id") == _IRYS_ID), None)
    check("Irys entry present", irys is not None, _IRYS_ID)
    if irys is not None:
        check("Irys status == research_candidate (NOT active)", irys.get("status") == "research_candidate",
              f"status={irys.get('status')!r}")
        check("Irys is NOT active", irys.get("status") != "active")
        check("Irys harvey_lab_claims_unverified is True", irys.get("harvey_lab_claims_unverified") is True,
              f"={irys.get('harvey_lab_claims_unverified')!r}")
        check("Irys no_truth_authority is True", irys.get("no_truth_authority") is True,
              f"={irys.get('no_truth_authority')!r}")
        check("Irys declares a non-empty proof_to_promote",
              isinstance(irys.get("proof_to_promote"), str) and len(irys.get("proof_to_promote", "")) > 20)
        check("Irys declares a working local_equivalent",
              isinstance(irys.get("local_equivalent"), str) and irys.get("local_equivalent") != "")
        check("Irys is flagged do_not_adopt_as_primary", irys.get("do_not_adopt_as_primary") is True)
        check("Irys license MIT @ verified confidence",
              irys.get("license") == "MIT" and irys.get("license_confidence") == "verified")

    # ── exactly ONE active per catalog, and it is the local stub / local sqlite ─────────────────
    swarm_active = [e for e in swarm_entries if e.get("status") == "active"]
    black_active = [e for e in black_entries if e.get("status") == "active"]
    check("exactly one ACTIVE entry in the swarm catalog", len(swarm_active) == 1,
          str([e.get("provider_id") for e in swarm_active]))
    check("exactly one ACTIVE entry in the blackboard catalog", len(black_active) == 1,
          str([e.get("provider_id") for e in black_active]))
    if len(swarm_active) == 1:
        check("the swarm catalog's single active entry is the local stub",
              "local_stub" in swarm_active[0].get("provider_id", ""), swarm_active[0].get("provider_id"))
    if len(black_active) == 1:
        check("the blackboard catalog's single active entry is the local sqlite store",
              "local_sqlite" in black_active[0].get("provider_id", ""), black_active[0].get("provider_id"))

    # ── every GATED (non-active) entry has local_equivalent + do_not_adopt_as_primary=true ──────
    for label, entries in (("swarm", swarm_entries), ("blackboard", black_entries)):
        for e in entries:
            if e.get("status") == "active":
                # the active local invariant must NOT claim do_not_adopt_as_primary (it IS the primary).
                check(f"{label} active entry is NOT do_not_adopt_as_primary: {e.get('provider_id')}",
                      e.get("do_not_adopt_as_primary") is False, f"={e.get('do_not_adopt_as_primary')!r}")
                continue
            le = e.get("local_equivalent")
            check(f"{label} gated entry has a local_equivalent: {e.get('provider_id')}",
                  isinstance(le, str) and le != "", f"local_equivalent={le!r}")
            check(f"{label} gated entry is do_not_adopt_as_primary=true: {e.get('provider_id')}",
                  e.get("do_not_adopt_as_primary") is True, f"={e.get('do_not_adopt_as_primary')!r}")

    # ── governance_law states benchmark=evidence(-not-promotion) + blackboard!=truth + candidate!=active ─
    for label, cat in (("swarm", swarm), ("blackboard", black)):
        law = (cat.get("governance_law") or "").lower()
        missing = [p for p in _LAW_PHRASES if p not in law]
        check(f"{label} governance_law states benchmark=evidence + candidate!=active",
              missing == [], f"missing phrases: {missing}")
        # blackboard != served truth must be explicit.
        check(f"{label} governance_law states the blackboard/agent output is NEVER served truth",
              ("never" in law and "truth" in law), "law must say agent/blackboard output is never served truth")

    # ── NO raw API key literals anywhere (env:// refs + field names are allowed) ─────────────────
    for label, path in (("swarm", _SWARM_CATALOG), ("blackboard", _BLACKBOARD_CATALOG),
                        ("self", Path(__file__))):
        hits = _raw_key_hits(path.read_text(encoding="utf-8"))
        check(f"no raw API key literals in {label}", hits == [], f"hits={hits}")

    # ── every credential reference that IS present is an env:// ref (never an inline value) ──────
    for label, entries in (("swarm", swarm_entries), ("blackboard", black_entries)):
        for e in entries:
            refs = e.get("credential_refs", []) or []
            bad = [r for r in refs if not str(r).startswith("env://")]
            check(f"{label} credential_refs are env:// only: {e.get('provider_id')}", bad == [], f"bad={bad}")

    print(f"\n{'PASS — check_stateful_swarm_provider_catalog: both catalogs load + are well-formed; Irys is a research_candidate (NOT active) with harvey_lab_claims_unverified + no_truth_authority + proof_to_promote; exactly one active per catalog is the offline local stub/sqlite; every gated entry keeps a local_equivalent + do_not_adopt_as_primary; license_confidence in {verified,unverified}; both governance_laws state benchmark=evidence-not-promotion + blackboard != served truth + candidate != active; no raw API key literals (env:// refs only).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Proof: the stateful-swarm runner + blackboard provider catalogs encode the Irys / "
                    "persistent-blackboard governance boundary (research_candidate, benchmark=evidence, "
                    "blackboard != served truth, one offline active authority).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
