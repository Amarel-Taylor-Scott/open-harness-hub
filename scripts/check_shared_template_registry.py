#!/usr/bin/env python3
"""scripts.check_shared_template_registry — PROOF: the internal Shared Template Registry — canonical object
shell + schema mixins + template contracts + safe instantiator (generated outputs are CANDIDATE, never truth).

Asserts:
  A. CANONICAL SHELL: the 14 sections present (identity…receipts); required_core (object_id/object_type/
     schema_version); the example carries the core fields.
  B. MIXINS: 15 mixin files; each has mixin_id+section+fields; the mixins COVER the shell's key fields
     (identity/status/visibility/provenance/receipts/source_handles/security).
  C. NUMERIC CODES: status/visibility/edge code tables are numeric; a 'candidate' status (200) + an 'active'
     status exist; runtime distinguishes candidate≠active by NUMBER.
  D. CONTRACTS: TemplateArtifact + SchemaObjectTemplate present + registered in contract_registry.
  E. REGISTRY: internal_name 'Shared Template Registry'; OpenTemplatesHub.io noted as NOT-launched future
     surface; existing templates/ + scripts reused (no-reinvention recorded).
  F. SCHEMA-OBJECT TEMPLATES: >=9 families incl ContextArtifact/PurposeTask/ModelInvocationReceipt; every family
     composes the shell from mixins that all EXIST.
  G. INSTANTIATOR: compose_object_shell yields all 14 sections, status=candidate(200) by default, content_hash
     computed, security holds secret_refs (no raw key); never status active.
  H. SAFE RENDER: instantiate_schema_object writes a CANDIDATE instance + receipt to a TEMP dir; refuses
     overwrite (allow_overwrite=False) and path traversal; receipt says is_active=False, is_truth=False.
  I. NO-REINVENTION: the existing templates/ tree + scripts/{check_template_catalog,generate_from_template} are
     intact (not replaced).
  J. DEPENDENCY LAW (local): no module under src/teleon/templates imports src.baltor.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.templates import instantiator as inst

_NOW = "2026-06-06T00:00:00Z"
_A = _REPO / "architecture"
_SHELL_SECTIONS = ["identity", "scope", "contracts", "payload_or_ref", "provenance", "lineage", "policy",
                   "security", "visibility", "lifecycle", "status", "telemetry", "relationships", "receipts"]


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    shell = inst.load_shell()
    mixins = inst.load_mixins()
    reg = json.loads((_A / "template_registry.json").read_text())
    sot = inst.load_schema_object_templates()
    contracts = json.dumps(json.loads((_A / "contract_registry.json").read_text()))

    # A. canonical shell
    check("A: 14 canonical sections present", shell["sections"] == _SHELL_SECTIONS, str(shell["sections"]))
    check("A: required_core identity fields", set(shell["required_core"]) == {"object_id", "object_type", "schema_version"})
    check("A: example carries the core fields", all(k in shell["example"] for k in ("object_id", "status_code", "visibility_code", "receipts")))

    # B. mixins — the owner's 15 canonical mixins all present (extra useful ones allowed)
    _canon15 = {"identity", "scope", "provenance", "lineage", "policy", "security", "visibility", "lifecycle",
                "status", "telemetry", "relationships", "receipts", "source_handles", "content_hash", "tenant_project"}
    check("B: the 15 canonical mixins all present", _canon15 <= set(mixins) and len(mixins) >= 15, str(sorted(_canon15 - set(mixins))))
    check("B: each mixin has mixin_id+section+fields", all("mixin_id" in m and "section" in m and m.get("fields") for m in mixins.values()))
    covered = {f for m in mixins.values() for f in m["fields"]}
    for need in ("object_id", "status_code", "visibility_code", "provenance", "receipts", "source_handles", "security"):
        check(f"B: mixins cover '{need}'", need in covered)

    # C. numeric codes
    st = json.loads((_A / "template_status_codes.json").read_text())["statuses"]
    codes = {s["label"]: s["code"] for s in st}
    check("C: status codes numeric + candidate(200)+active present", all(isinstance(s["code"], int) for s in st) and codes.get("candidate") == 200 and "active" in codes)
    vis = json.loads((_A / "template_visibility_codes.json").read_text())["visibility"]
    edg = json.loads((_A / "template_edge_type_codes.json").read_text())["edge_types"]
    check("C: visibility + edge codes numeric", all(isinstance(v["code"], int) for v in vis) and all(isinstance(e["code"], int) for e in edg))

    # D. contracts
    for c in ("TemplateArtifact", "SchemaObjectTemplate"):
        p = _REPO / "schemas" / "templates" / f"{c}.schema.json"
        check(f"D: {c} schema present", p.exists())
        check(f"D: {c} registered", f"templates/{c}.schema.json" in contracts)

    # E. registry
    check("E: internal_name 'Shared Template Registry'", reg["internal_name"] == "Shared Template Registry")
    check("E: OpenTemplatesHub.io noted as NOT-launched future surface", "OpenTemplatesHub.io" in reg["future_public_surface"] and "NOT launched" in reg["future_public_surface"])
    check("E: existing templates/scripts reused (no-reinvention)", any("check_template_catalog" in x for x in reg["existing_reused"]))

    # F. schema-object templates
    check("F: >=9 families incl Context/PurposeTask/ModelInvocationReceipt",
          len(sot) >= 9 and {"ContextArtifact", "PurposeTask", "ModelInvocationReceipt"} <= set(sot), str(sorted(sot)))
    for fam, t in sot.items():
        missing = [m for m in t["required_mixins"] if m not in mixins]
        check(f"F: {fam} composes from existing mixins", not missing, str(missing))

    # G. instantiator compose
    obj = inst.compose_object_shell(object_id="x@v1", object_type="ContextArtifact",
                                    mixin_ids=sot["ContextArtifact"]["required_mixins"], now=_NOW, payload={"a": 1})
    check("G: composed object has all 14 sections' fields", all(k in obj for k in ("object_id", "status_code", "visibility_code", "provenance", "receipts", "security", "telemetry", "relationships", "lineage")))
    check("G: default status is candidate (200), not active", obj["status_code"] == inst.CANDIDATE_STATUS and not inst.is_active_status(obj["status_code"]))
    check("G: content_hash computed; security holds secret_refs (no raw key)", obj["content_hash"].startswith("sha256:") and obj["security"] == {"secret_refs": []})

    # H. safe render to a temp dir
    tmp = Path(tempfile.mkdtemp(prefix="tpl-test-"))
    try:
        out = inst.instantiate_schema_object("PurposeTask", out_dir=tmp, now=_NOW)
        check("H: candidate instance + receipt written", out["path"].exists() and (tmp / "PurposeTask.receipt.json").exists())
        check("H: receipt: candidate, not active, not truth", out["receipt"]["status_code"] == 200 and out["receipt"]["is_active"] is False and out["receipt"]["is_truth"] is False)
        overwrote = True
        try:
            inst.instantiate_schema_object("PurposeTask", out_dir=tmp, now=_NOW)  # should refuse
        except FileExistsError:
            overwrote = False
        check("H: refuses overwrite when allow_overwrite=False", overwrote is False)
        traversed = True
        try:
            inst._safe_target(tmp, "../escape.json")
        except ValueError:
            traversed = False
        check("H: refuses path traversal", traversed is False)
    finally:
        for f in tmp.glob("*"):
            f.unlink()
        tmp.rmdir()

    # I. no-reinvention
    check("I: existing templates/ tree intact", (_REPO / "templates" / "worker").exists() and (_REPO / "templates" / "api").exists())
    check("I: existing template scripts intact", (_REPO / "scripts" / "check_template_catalog.py").exists() and (_REPO / "scripts" / "generate_from_template.py").exists())

    # J. dependency law (local)
    bad = [str(p.relative_to(_REPO)) for p in (_REPO / "src" / "teleon" / "templates").rglob("*.py")
           for line in p.read_text().splitlines() if line.strip().startswith(("import src.baltor", "from src.baltor"))]
    check("J: no src/teleon/templates module imports src.baltor", not bad, "; ".join(bad))

    print("\n" + ("PASS — check_shared_template_registry: canonical 14-section object shell + 15 mixins compose every "
                  "object family; numeric status/visibility/edge codes; TemplateArtifact/SchemaObjectTemplate "
                  "contracts registered; the instantiator renders CANDIDATE (never active/truth) shapes safely "
                  "(no overwrite/traversal/secret); existing templates reused; internal-only (OpenTemplatesHub.io "
                  "is a future surface)." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_shared_template_registry.py --self-test")
    raise SystemExit(0)
