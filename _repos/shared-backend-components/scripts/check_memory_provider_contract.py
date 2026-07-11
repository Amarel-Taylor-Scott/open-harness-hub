#!/usr/bin/env python3
"""scripts.check_memory_provider_contract — proof (MEMORY PROVIDER CONTRACTS MODE): the seven memory/context
provider contract schemas exist, validate via the stdlib schema validator, each ships a valid example that
PASSES and an invalid example that FAILS, and the governance boundary holds:

* MemoryArtifact — the boundary — REQUIRES external_source_handle + tenant_id + scope + container +
  claim_status + content + provider_id + lineage + created_at, so NO recall becomes an artifact without an
  upstream handle, a tenant, a (project/container) scope, and a claim_status. (remembered != verified;
  retrieved != served; profiled != canonical; candidate memory != promoted fact.)
* claim_status is enum-bounded (candidate|promoted|held_out) — a bogus 'served' is rejected; a MemorySearchResult
  entry can only be candidate|held_out (recall can NEVER mint a 'promoted' fact on its own).
* MemoryProfile is {static:[...], dynamic:[...]} and every entry REFERENCES a MemoryArtifact/handle
  (artifact_id + external_source_handle), never an inline asserted fact.
* MemoryProviderStatus.credential_ref is an env://… (or secret://…) REFERENCE, never an inline secret VALUE —
  asserted as a POSITIVE (env:// passes the ref rule) and a NEGATIVE (a non-ref value is detected and FAILS).
  The deterministic emulator status is available=true with NO credential needed (correctness invariant runs offline).

Deterministic, stdlib-only, offline. CLI: python3 _repos/shared-backend-components/scripts/check_memory_provider_contract.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.runtime.schema_validator import validate as _validate

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_SCHEMA_DIR = _resource("schemas") / "memory"
_EX_DIR = _SCHEMA_DIR / "examples"

#: every memory contract schema this lane owns (filename stem under schemas/memory).
_SCHEMAS = ["MemoryArtifact", "MemoryWriteRequest", "MemorySearchRequest", "MemorySearchResult",
            "MemoryProfile", "MemoryTrace", "MemoryProviderStatus"]
#: the governance fields MemoryArtifact MUST require (no recall becomes an artifact without these).
_MEMORY_ARTIFACT_REQUIRED = {"external_source_handle", "tenant_id", "scope", "container", "claim_status",
                             "content", "provider_id", "lineage", "created_at"}
#: claim_status enum on the boundary artifact.
_CLAIM_STATUS_ENUM = {"candidate", "promoted", "held_out"}
#: a credential_ref must be a REFERENCE, never an inline value.
_CREDENTIAL_REF_PREFIXES = ("env://", "secret://")
#: example keys that are NOT plain schema-rejection cases (handled by a dedicated assertion instead).
_SPECIAL_INVALIDS = {"invalid_credential_ref_is_a_value"}


def _is_credential_ref(value: str) -> bool:
    return isinstance(value, str) and value.startswith(_CREDENTIAL_REF_PREFIXES)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    schemas: dict[str, dict] = {}
    examples: dict[str, dict] = {}
    for stem in _SCHEMAS:
        sp = _SCHEMA_DIR / f"{stem}.schema.json"
        ep = _EX_DIR / f"{stem}.example.json"
        check(f"{stem} schema file exists", sp.is_file(), str(sp))
        check(f"{stem} example file exists", ep.is_file(), str(ep))
        if sp.is_file():
            schemas[stem] = json.loads(sp.read_text())
        if ep.is_file():
            examples[stem] = json.loads(ep.read_text())

    # every schema declares $id memory/<Stem>, type object, additionalProperties false, required + properties,
    # and uses only the stdlib-validator keyword set.
    allowed = {"type", "required", "properties", "enum", "additionalProperties", "items", "$id", "title", "description"}

    def _keys_ok(node) -> bool:
        if not isinstance(node, dict):
            return True
        for k, v in node.items():
            if k == "properties" and isinstance(v, dict):
                if not all(_keys_ok(sub) for sub in v.values()):
                    return False
                continue
            if k == "items" and isinstance(v, dict):
                if not _keys_ok(v):
                    return False
                continue
            if k not in allowed:
                return False
        return True

    for stem, sc in schemas.items():
        check(f"{stem} $id is memory/{stem}", sc.get("$id") == f"memory/{stem}", str(sc.get("$id")))
        check(f"{stem} is an object with additionalProperties:false",
              sc.get("type") == "object" and sc.get("additionalProperties") is False)
        check(f"{stem} declares required + properties", bool(sc.get("required")) and bool(sc.get("properties")))
        check(f"{stem} uses only stdlib-validator keywords", _keys_ok(sc))

    # valid example(s) pass, invalid example(s) fail (excluding the special non-schema invalids).
    for stem, ex in examples.items():
        sc = schemas[stem]
        valids = [(k, v) for k, v in ex.items() if k == "valid" or k.startswith("valid_")]
        check(f"{stem} has at least one 'valid' example", len(valids) >= 1)
        for k, v in valids:
            errs = _validate(v, sc)
            check(f"{stem} {k} example validates clean", errs == [], str(errs[:4]))
        invalids = [(k, v) for k, v in ex.items()
                    if k.startswith("invalid") and k not in _SPECIAL_INVALIDS]
        check(f"{stem} ships at least one invalid example", len(invalids) >= 1)
        for k, v in invalids:
            errs = _validate(v, sc)
            check(f"{stem} {k} is correctly REJECTED", errs != [])

    # ---- MemoryArtifact governance boundary ----
    ma = schemas.get("MemoryArtifact", {})
    req = set(ma.get("required", []))
    check("MemoryArtifact requires external_source_handle/tenant_id/scope/container/claim_status/content/provider_id/lineage/created_at",
          _MEMORY_ARTIFACT_REQUIRED <= req, str(sorted(_MEMORY_ARTIFACT_REQUIRED - req)))
    base = examples.get("MemoryArtifact", {}).get("valid", {})
    if base and ma:
        # each required field individually missing → rejected (each field is load-bearing).
        for f in sorted(_MEMORY_ARTIFACT_REQUIRED):
            broken = {k: v for k, v in base.items() if k != f}
            check(f"MemoryArtifact rejects an artifact missing '{f}'", _validate(broken, ma) != [])
        # claim_status enum is enforced: candidate/promoted/held_out OK, a 'served' claim is rejected.
        cs_enum = set(ma.get("properties", {}).get("claim_status", {}).get("enum", []))
        check("MemoryArtifact claim_status enum == {candidate,promoted,held_out}", cs_enum == _CLAIM_STATUS_ENUM, str(sorted(cs_enum)))
        for good in sorted(_CLAIM_STATUS_ENUM):
            ok_art = dict(base); ok_art["claim_status"] = good
            check(f"MemoryArtifact accepts claim_status='{good}'", _validate(ok_art, ma) == [])
        bad_claim = dict(base); bad_claim["claim_status"] = "served"
        check("MemoryArtifact rejects claim_status='served' (remembered != served)", _validate(bad_claim, ma) != [])
        # scope enum: a real tenant_private scope is valid; a bogus scope is rejected.
        bad_scope = dict(base); bad_scope["scope"] = "world_readable"
        check("MemoryArtifact rejects an out-of-enum scope", _validate(bad_scope, ma) != [])
        # the boundary carries NO field asserting it is a served/canonical fact by itself.
        forbidden_assertion_fields = {"is_canonical", "is_served", "served", "canonical", "is_verified", "verified"}
        present_forbidden = forbidden_assertion_fields & set(ma.get("properties", {}))
        check("MemoryArtifact has NO field asserting it is canonical/served/verified by itself",
              present_forbidden == set(), str(sorted(present_forbidden)))

    # ---- MemorySearchResult: a recall result can only be candidate|held_out (never mints 'promoted') ----
    sr = schemas.get("MemorySearchResult", {})
    if sr:
        item = sr.get("properties", {}).get("results", {}).get("items", {})
        entry_enum = set(item.get("properties", {}).get("claim_status", {}).get("enum", []))
        check("MemorySearchResult result claim_status enum == {candidate,held_out} (recall != promotion)",
              entry_enum == {"candidate", "held_out"}, str(sorted(entry_enum)))

    # ---- MemoryProfile: {static:[...], dynamic:[...]}, each entry REFERENCES an artifact/handle ----
    mp = schemas.get("MemoryProfile", {})
    if mp:
        props = mp.get("properties", {})
        mp_req = set(mp.get("required", []))
        check("MemoryProfile has static + dynamic arrays (required)",
              {"static", "dynamic"} <= mp_req
              and props.get("static", {}).get("type") == "array"
              and props.get("dynamic", {}).get("type") == "array")
        for side in ("static", "dynamic"):
            entry_req = set(props.get(side, {}).get("items", {}).get("required", []))
            check(f"MemoryProfile {side} entries reference a MemoryArtifact/handle (artifact_id + external_source_handle required)",
                  {"artifact_id", "external_source_handle"} <= entry_req, str(sorted({"artifact_id", "external_source_handle"} - entry_req)))

    # ---- MemoryProviderStatus: credential_ref is an env://… REFERENCE, never a VALUE ----
    ps = schemas.get("MemoryProviderStatus", {})
    ps_ex = examples.get("MemoryProviderStatus", {})
    if ps:
        st_enum = set(ps.get("properties", {}).get("status", {}).get("enum", []))
        check("MemoryProviderStatus status enum == {active,candidate,emulated,unavailable}",
              st_enum == {"active", "candidate", "emulated", "unavailable"}, str(sorted(st_enum)))
    # POSITIVE: the candidate example's credential_ref is an env:// reference.
    good_status = ps_ex.get("valid", {})
    check("MemoryProviderStatus valid example credential_ref is an env:// reference (not a value)",
          _is_credential_ref(good_status.get("credential_ref", "")))
    # POSITIVE: the emulator example is available=true with NO credential (correctness invariant runs offline, zero creds).
    emu = ps_ex.get("valid_emulated_no_creds", {})
    check("MemoryProviderStatus emulator status: emulated + available=true + no credential_ref (offline correctness invariant)",
          emu.get("status") == "emulated" and emu.get("available") is True and "credential_ref" not in emu)
    # NEGATIVE: a status whose credential_ref is an inline VALUE (no env://) is detected and FAILS the ref rule.
    bad_ref = ps_ex.get(next(iter(_SPECIAL_INVALIDS)), {})
    check("MemoryProviderStatus credential_ref-as-a-value is DETECTED (the ref rule actually bites)",
          ("credential_ref" in bad_ref) and not _is_credential_ref(bad_ref.get("credential_ref", "")))
    # the special-invalid example validates against the bare schema (proving the ref rule needs THIS check, not the schema).
    if ps and bad_ref:
        check("MemoryProviderStatus credential_ref-as-a-value passes the bare schema (so the dedicated ref check is load-bearing)",
              _validate(bad_ref, ps) == [])

    print(f"\n{'PASS — check_memory_provider_contract: 7 memory schemas exist + validate; each has a passing valid example and a rejected invalid example; MemoryArtifact requires external_source_handle/tenant_id/scope/container/claim_status (each load-bearing); claim_status enum enforced (no served), recall results can only be candidate|held_out; MemoryProfile static/dynamic entries reference artifacts/handles; MemoryProviderStatus.credential_ref is an env:// reference not a value, emulator runs offline with no creds.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: memory/context provider contract schemas are complete + governance-enforcing.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
