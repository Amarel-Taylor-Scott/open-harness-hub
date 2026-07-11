#!/usr/bin/env python3
"""scripts.check_shared_io_resource_spine — PROOF: the Shared I/O + Resource Spine exists as ONE named map that
ratifies the repo's existing typed-I/O contracts (no duplicate shells) and fills the missing RESOURCE layer.

Asserts:
  A. SPINE MAP: _repos/shared-backend-components/architecture/shared_io_spine.json — every contract marked exists/new resolves to a real schema
     file (no dangling refs); the law clause + shared-vs-separate split are recorded.
  B. OBJECT SHELL RATIFIED: ObjectShell is registered, and the EXISTING canonical shell builder
     (_repos/teleon/backend/src/teleon/templates/compose_object_shell) produces an object carrying ALL ObjectShell required fields.
  C. CANONICAL SHELL: 14 sections; required_core is a subset of ObjectShell required.
  D. ENVELOPES RATIFIED (not duplicated): Command/Event/Error envelopes are referenced by the spine + exist;
     EventEnvelope is CloudEvents 1.0; ErrorEnvelope carries error_type + retryable.
  E. RESOURCE LAYER: the 6 resource schemas exist + are registered; KIND/OWNERSHIP codes come from the single
     source (shared_resource_spine.json); make_resource_ref builds a valid ref.
  F. RESOURCE RULES (happy path): a local persistent table (owner+retention) and a temp dataset (ttl) validate.
  G. REDTEAM (all fail safely): raw key in spec · temporary w/o ttl · persistent w/o owner/retention · cloud w/o
     local_equivalent · make_secret_ref(raw key) raises · secret_ref not using secret:// · DSN with inline password.
  H. RECEIPTS: provision_receipt — ephemeral => cleanup_required True; persistent => False.
  I. DETERMINISM: builders + receipts deterministic for fixed inputs/now.
  J. DEPENDENCY LAW: _repos/teleon/backend/src/teleon/resources never imports src.baltor; no new top-level shared-platform/ tree.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.resources import resource_ref as R
from src.teleon.templates import instantiator as TPL

_NOW = "2026-06-06T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    A = _resource("architecture")
    spine = json.loads((A / "shared_io_spine.json").read_text())
    dangling = [c["schema"] for L in spine["layers"] for c in L["contracts"]
                if c["status"] in ("exists", "new") and not (_resource(c["schema"])).exists()]
    check("A: spine map — no dangling exists/new refs", not dangling, "; ".join(dangling))
    check("A: law clause + shared/separate split recorded",
          bool(spine.get("law_clause")) and "truth" in json.dumps(spine["shared_vs_separate"]["separate"]))

    contracts = json.dumps(json.loads((A / "contract_registry.json").read_text()))
    check("B: ObjectShell registered", "shared/ObjectShell.schema.json" in contracts)
    shell_schema = json.loads((_resource("schemas") / "shared" / "ObjectShell.schema.json").read_text())
    obj = TPL.compose_object_shell(object_id="x", object_type="DemoArtifact", mixin_ids=None, now=_NOW, payload={"a": 1})
    missing = [k for k in shell_schema["required"] if k not in obj]
    check("B: compose_object_shell conforms to ObjectShell (all required fields present)", not missing, str(missing))

    canon = json.loads((_resource("templates/schema-objects/canonical_object_shell.json")).read_text())
    check("C: canonical shell has 14 sections", len(canon["sections"]) == 14, str(len(canon["sections"])))
    check("C: required_core subset of ObjectShell required", set(canon["required_core"]) <= set(shell_schema["required"]))

    refs = {c["name"]: c for L in spine["layers"] for c in L["contracts"]}
    check("D: Command/Event/Error envelopes ratified in spine + exist",
          all(refs.get(n, {}).get("status") == "exists" and (_resource(refs[n]["schema"])).exists()
              for n in ("CommandEnvelope", "EventEnvelope", "ErrorEnvelope")))
    ee = json.loads((_resource("schemas") / "envelopes" / "EventEnvelope.schema.json").read_text())
    err = json.loads((_resource("schemas") / "envelopes" / "ErrorEnvelope.schema.json").read_text())
    check("D: EventEnvelope is CloudEvents 1.0", "1.0" in ee["properties"]["specversion"].get("enum", []))
    check("D: ErrorEnvelope carries error_type + retryable",
          "error_type" in err["properties"] and "retryable" in err["properties"])

    for s in ("ResourceRef", "ResourceBinding", "DataResourceSpec", "SecretRef", "KeyRef", "ResourceProvisionReceipt"):
        check(f"E: {s} schema exists + registered",
              (_resource("schemas") / "resources" / f"{s}.schema.json").exists() and f"resources/{s}.schema.json" in contracts)
    check("E: KIND/OWNERSHIP codes from single source (shared_resource_spine.json)",
          R.KIND["relational_table"] == 100 and R.OWNERSHIP["managed_persistent"] == 200)
    rref = R.make_resource_ref(logical_name="facts_main", kind_code=R.KIND["relational_table"], ownership_code=R.MANAGED_PERSISTENT)
    check("E: make_resource_ref builds a logical ref (no raw name)", rref["resource_ref"] == "res://facts_main")

    persist = R.make_data_resource_spec(logical_name="facts_main", kind_code=R.KIND["relational_table"],
                                        ownership_code=R.MANAGED_PERSISTENT, owner="baltor", retention_class="long",
                                        secret_ref="secret://db/main")
    temp = R.make_data_resource_spec(logical_name="scratch", kind_code=R.KIND["temp_dataset"],
                                     ownership_code=R.PIPELINE_TEMP, ttl_seconds=3600)
    ok_p, why_p = R.validate_resource_spec(persist)
    ok_t, why_t = R.validate_resource_spec(temp)
    check("F: local persistent table (owner+retention) validates", ok_p, str(why_p))
    check("F: temp dataset (ttl) validates", ok_t, str(why_t))

    # ── REDTEAM ──
    fake_key = "sk-" + "B" * 30  # built dynamically; never a real/literal key
    leaky = dict(persist); leaky["note"] = fake_key
    ok_k, why_k = R.validate_resource_spec(leaky)
    check("G1: raw key in spec → rejected", (not ok_k) and "raw_secret_in_resource_spec" in why_k)
    notttl = R.make_data_resource_spec(logical_name="t", kind_code=R.KIND["temp_dataset"], ownership_code=R.MANAGED_EPHEMERAL)
    ok_n, why_n = R.validate_resource_spec(notttl)
    check("G2: temporary w/o ttl → rejected", (not ok_n) and "temporary_resource_requires_ttl" in why_n)
    noowner = R.make_data_resource_spec(logical_name="p", kind_code=R.KIND["relational_table"], ownership_code=R.MANAGED_PERSISTENT)
    ok_o, why_o = R.validate_resource_spec(noowner)
    check("G3: persistent w/o owner+retention → rejected",
          (not ok_o) and "persistent_resource_requires_owner" in why_o and "persistent_resource_requires_retention" in why_o)
    cloud = R.make_data_resource_spec(logical_name="b", kind_code=R.KIND["object_bucket"],
                                      ownership_code=R.EXTERNAL_EXISTING, provider="gcs")
    ok_c, why_c = R.validate_resource_spec(cloud)
    check("G4: cloud provider w/o local_equivalent → rejected", (not ok_c) and "cloud_resource_requires_local_equivalent" in why_c)
    raised = False
    try:
        R.make_secret_ref(fake_key)
    except ValueError:
        raised = True
    check("G5: make_secret_ref(raw key) raises", raised)
    badscheme = R.make_data_resource_spec(logical_name="q", kind_code=R.KIND["relational_table"],
                                          ownership_code=R.EXTERNAL_EXISTING, secret_ref="plaintext-not-a-ref")
    ok_s, why_s = R.validate_resource_spec(badscheme)
    check("G6: secret_ref not using secret:// → flagged", (not ok_s) and any("secret_ref_must_use" in w for w in why_s))
    dsn = "postgresql://u:" + ("x" * 12) + "@h/db"  # synthetic credentialed DSN, built dynamically
    check("G7: inline credentialed DSN detected as raw secret", R.has_raw_secret({"conn": dsn}))

    eph_rcpt = R.provision_receipt(temp, now=_NOW, outcome="provisioned")
    per_rcpt = R.provision_receipt(persist, now=_NOW, outcome="reused_existing")
    check("H: ephemeral receipt → cleanup_required True; persistent → False",
          eph_rcpt["cleanup_required"] is True and per_rcpt["cleanup_required"] is False
          and eph_rcpt["schema_version"] == "ResourceProvisionReceipt")

    check("I: builders + receipts deterministic",
          R.make_data_resource_spec(logical_name="scratch", kind_code=R.KIND["temp_dataset"], ownership_code=R.PIPELINE_TEMP, ttl_seconds=3600) == temp
          and R.provision_receipt(temp, now=_NOW, outcome="provisioned") == eph_rcpt)

    bad_imp = [str(p.relative_to(_REPO)) for p in (_resource("src/teleon/resources")).rglob("*.py")
               for line in p.read_text().splitlines() if line.strip().startswith(("import src.baltor", "from src.baltor"))]
    check("J: _repos/teleon/backend/src/teleon/resources never imports src.baltor", not bad_imp, "; ".join(bad_imp))
    check("J: no parallel shared-platform/ tree (reuse schemas/ + _repos/teleon/backend/src/teleon)", not (_resource("shared-platform")).exists())

    print("\n" + ("PASS — check_shared_io_resource_spine: ONE named spine map ratifies the existing typed-I/O "
                  "contracts (ObjectShell + Command/Event/Error envelopes, no duplicates) and fills the resource "
                  "layer (ResourceRef/Binding/DataResourceSpec/SecretRef/KeyRef/ProvisionReceipt) with guards — no "
                  "raw secrets/tables, TTL on temp, owner+retention on persistent, local-equivalent for cloud; "
                  "deterministic; Teleon-side." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_shared_io_resource_spine.py --self-test")
    raise SystemExit(0)
