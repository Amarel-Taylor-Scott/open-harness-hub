#!/usr/bin/env python3
"""interface_manifests — make the relationships between separate repos FIRST-CLASS + VERSIONED + CHECKED.

Best practice for "separate components but with relationships": each repo publishes a versioned
`interface.json` (what it exposes, and what it consumes from whom), and every relationship is verified —
a repo may only consume a capability the provider actually exposes, and only from a surface the dependency
law allows. Separation (each repo owns its interface) + relationship (declared, versioned, consistency-checked).

- `--generate` : write a starter `_repos/<repo>/interface.json` per surface from the registry's `exposes`
  (`consumes` starts as `{provider: []}` — [] means "whole interface, narrow me"; the owner lists the
  specific capability ids actually used).
- `--check`    : validate each manifest (shape + semver) AND the two consistency laws:
    (1) every consumed capability is one the provider EXPOSES (no consuming what isn't published);
    (2) every consumed provider is in the surface's `may_depend_on` (agrees with the dependency law).
- `--self-test`: offline synthetic proof (a broken relationship is caught).

Single source: ../dev-rules-context/contracts/surface-registry.json. Reads contracts only, never repo source.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPOS = HERE.parent
REGISTRY = REPOS / "dev-rules-context" / "contracts" / "surface-registry.json"
INTERFACE_VERSION = "0.1.0"           # starter version for a freshly-generated manifest
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
# a version CONSTRAINT is flexible: exact (1.2.3), range (>=1.0, ^1.2, ~1.2.0), or any (*).
VERSION_CONSTRAINT_RE = re.compile(r"^(\*|([<>]=?|\^|~)?\d+(\.\d+){0,2})$")


def _parse_consume(value: object) -> tuple[list[str], bool, str | None]:
    """A consume entry is flexible (most-flexible-as-possible): either a plain LIST of capability ids, or an
    OBJECT {capabilities:[...], version:"<constraint>", optional:bool}. Returns (capabilities, optional, version).
    This lets a relationship pin an exact version, a range, or none, and mark itself optional (degrade, don't fail)."""
    if isinstance(value, dict):
        return list(value.get("capabilities", [])), bool(value.get("optional", False)), value.get("version")
    return list(value or []), False, None


def _valid_version_constraint(v: object) -> bool:
    return bool(v) and bool(VERSION_CONSTRAINT_RE.match(str(v)))


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text())


def _kind_of(exposed_id: str) -> str:
    if exposed_id.startswith("/"):
        return "api"
    if exposed_id.endswith("-spec") or exposed_id.endswith("/*"):
        return "spec"
    if exposed_id[:1].isupper():
        return "type"
    return "capability"


def build_manifest(reg: dict, surface: str) -> dict:
    spec = reg["surfaces"][surface]
    return {
        "surface": surface,
        "repo": spec.get("repo"),
        "interface_version": INTERFACE_VERSION,
        "exposes": [{"id": e, "kind": _kind_of(e), "stability": "declared",
                     "summary": reg.get("capability_catalog", {}).get(e, "")}   # single source: registry catalog
                    for e in spec.get("exposes", [])],
        # start empty per provider — [] = whole-interface dependency; owner narrows to specific exposed ids.
        "consumes": {dep: [] for dep in spec.get("may_depend_on", [])},
    }


def generate() -> dict:
    reg = load_registry()
    written = []
    for surface, spec in reg["surfaces"].items():
        folder = REPOS / surface
        if not folder.is_dir():
            continue
        path = folder / "interface.json"
        if not path.exists():   # never clobber an owner-refined manifest
            path.write_text(json.dumps(build_manifest(reg, surface), indent=2) + "\n")
            written.append(surface)
    return {"written": written, "total_surfaces": len(reg["surfaces"])}


def sync_summaries() -> dict:
    """Patch every EXISTING interface.json's `exposes[].summary` from the registry `capability_catalog`
    (single source), leaving `consumes` and every owner-refined field untouched. This is the non-clobber
    complement to --generate: --generate writes a NEW manifest with summaries filled; --sync refreshes the
    summaries on manifests an owner has already refined, so a catalog edit propagates without discarding
    their `consumes` narrowing. Idempotent + deterministic; only writes a file whose summaries changed."""
    reg = load_registry()
    catalog = reg.get("capability_catalog", {})
    updated, missing = [], set()
    for surface in reg["surfaces"]:
        p = REPOS / surface / "interface.json"
        if not p.exists():
            continue
        m = json.loads(p.read_text())
        changed = False
        for e in m.get("exposes", []):
            want = catalog.get(e.get("id"), "")
            if not want:
                missing.add(e.get("id"))
            if e.get("summary", "") != want:
                e["summary"] = want; changed = True
        if changed:
            p.write_text(json.dumps(m, indent=2) + "\n")
            updated.append(surface)
    return {"updated": updated, "uncatalogued_ids": sorted(missing)}


def _load_manifests(reg: dict) -> dict[str, dict]:
    out = {}
    for surface in reg["surfaces"]:
        p = REPOS / surface / "interface.json"
        if p.exists():
            try:
                out[surface] = json.loads(p.read_text())
            except Exception:  # noqa: BLE001
                out[surface] = {"_parse_error": True}
    return out


def check(reg: dict | None = None, manifests: dict | None = None) -> list[str]:
    """Return relationship/consistency violations (empty == sound). Accepts injected data for testing."""
    reg = reg or load_registry()
    manifests = manifests if manifests is not None else _load_manifests(reg)
    problems: list[str] = []
    exposed_ids = {s: {e["id"] for e in m.get("exposes", [])} for s, m in manifests.items()}
    for surface, m in manifests.items():
        if m.get("_parse_error"):
            problems.append(f"{surface}: interface.json is not valid JSON"); continue
        if not SEMVER_RE.match(str(m.get("interface_version", ""))):
            problems.append(f"{surface}: interface_version {m.get('interface_version')!r} is not semver")
        allowed = set(reg["surfaces"].get(surface, {}).get("may_depend_on", []))
        for provider, entry in (m.get("consumes") or {}).items():
            if provider not in allowed:
                problems.append(f"{surface} consumes {provider} — not in its may_depend_on (dependency-law breach)")
            caps, optional, version = _parse_consume(entry)
            if version is not None and not _valid_version_constraint(version):
                problems.append(f"{surface} consumes {provider} with malformed version constraint {version!r}")
            for cap in caps:  # every consumed capability must be one the provider EXPOSES
                if provider in exposed_ids and cap not in exposed_ids[provider]:
                    if optional:
                        continue  # optional relationship: a missing capability degrades, it does not break
                    problems.append(f"{surface} consumes {provider}:{cap!r} — provider does NOT expose it (broken relationship)")
    return problems


def self_test() -> int:
    reg = {"surfaces": {
        "substrate": {"repo": "s", "exposes": ["registry"], "may_depend_on": []},
        "teleon": {"repo": "t", "exposes": ["/api/teleon"], "may_depend_on": ["substrate"]},
    }, "forbidden_edges": []}
    good = {
        "substrate": {"surface": "substrate", "interface_version": "0.1.0", "exposes": [{"id": "registry"}], "consumes": {}},
        "teleon": {"surface": "teleon", "interface_version": "0.1.0", "exposes": [{"id": "/api/teleon"}], "consumes": {"substrate": ["registry"]}},
    }
    checks = [("sound relationships pass", check(reg, good) == [])]
    bad_cap = json.loads(json.dumps(good)); bad_cap["teleon"]["consumes"]["substrate"] = ["ghost-capability"]
    checks.append(("consuming an unexposed capability fails", any("does NOT expose" in p for p in check(reg, bad_cap))))
    bad_dep = json.loads(json.dumps(good)); bad_dep["substrate"]["consumes"] = {"teleon": ["/api/teleon"]}
    checks.append(("consuming outside may_depend_on fails", any("dependency-law breach" in p for p in check(reg, bad_dep))))
    bad_ver = json.loads(json.dumps(good)); bad_ver["teleon"]["interface_version"] = "v1"
    checks.append(("non-semver version fails", any("not semver" in p for p in check(reg, bad_ver))))
    checks.append(("manifest built from registry has exposes+consumes", set(build_manifest(reg, "teleon")) >= {"exposes", "consumes", "interface_version"}))
    # FLEXIBILITY: object-form consume with a version RANGE is accepted when the capability exists.
    flex_ok = json.loads(json.dumps(good)); flex_ok["teleon"]["consumes"]["substrate"] = {"capabilities": ["registry"], "version": ">=0.1"}
    checks.append(("version-range consume passes", check(reg, flex_ok) == []))
    flex_bad = json.loads(json.dumps(good)); flex_bad["teleon"]["consumes"]["substrate"] = {"capabilities": ["registry"], "version": "not-a-version"}
    checks.append(("malformed version constraint fails", any("malformed version" in p for p in check(reg, flex_bad))))
    # FLEXIBILITY: an OPTIONAL consume of an unexposed capability DEGRADES (does not break the relationship).
    opt = json.loads(json.dumps(good)); opt["teleon"]["consumes"]["substrate"] = {"capabilities": ["future-cap"], "optional": True}
    checks.append(("optional missing capability degrades, not fails", check(reg, opt) == []))
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - interface_manifests:\n  " + "\n  ".join(failed)); return 1
    print("PASS - interface_manifests: versioned per-repo interface.json; relationships CHECKED — a repo may "
          "consume only capabilities the provider EXPOSES and only surfaces its may_depend_on allows.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate + check versioned per-repo interface manifests.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--generate", action="store_true")
    ap.add_argument("--sync", action="store_true",
                    help="refresh exposes[].summary on EXISTING interface.json from the registry capability_catalog "
                         "(preserves consumes + owner refinements)")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.generate:
        r = generate()
        print(f"generated {len(r['written'])} interface.json (of {r['total_surfaces']} surfaces): {r['written']}")
    if args.sync:
        s = sync_summaries()
        print(f"synced summaries into {len(s['updated'])} interface.json: {s['updated']}")
        if s["uncatalogued_ids"]:
            print(f"  WARNING: {len(s['uncatalogued_ids'])} exposed id(s) missing from capability_catalog: {s['uncatalogued_ids']}")
    if args.check or not (args.generate or args.sync):
        problems = check()
        if problems:
            print("FAIL - interface relationships:\n  " + "\n  ".join(problems)); return 1
        print("PASS - interface relationships sound across all repos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
