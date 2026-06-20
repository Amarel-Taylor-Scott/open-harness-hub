#!/usr/bin/env python3
"""scripts.check_multi_source_ingestion — proof (MULTI-SOURCE MODE): api / csv / json sources flow through the
SAME governed ingestion → source_record/source_field → atomic_fact/narrative_allegation path with the correct
per-type source handles; structured fields are promotion-eligible facts, free-text is held-out allegations;
ingestion is deterministic with per-field hash isolation; tenant scope is preserved; produced facts are
gate-compatible; and a source whose parser is unavailable (pdf) or unknown returns an EXPLICIT non-consumable
reason with the raw stored — never a faked result. Source types are registered.

CLI: python3 scripts/check_multi_source_ingestion.py --self-test
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.ingest.source_adapters import REGISTRY, SourceAdapter, normalize
from scripts.runtime.verification_gate import VerificationGate

_REPO = Path(__file__).resolve().parents[1]


def _types(r) -> dict:
    return dict(Counter(a["artifact_type"] for a in r.get("artifacts", [])))


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # every adapter is behind the SourceAdapterPort
    check("api/csv/json adapters satisfy SourceAdapterPort", all(isinstance(REGISTRY[t], SourceAdapter) for t in ("api", "csv", "json")))

    # ── API (structured, official, global) ──
    api = normalize("api", [{"complaint_id": "C1", "product": "Credit card", "consumer_complaint_narrative": "Charged twice. No refund."}],
                    tenant_id="demo", source_id="cfpb-api", scope="global_public", authority="official")
    t = _types(api)
    check("API ingest is consumable + produces source_record/field/atomic_fact/narrative_allegation",
          api["consumable"] and t.get("atomic_fact", 0) >= 1 and t.get("narrative_allegation", 0) >= 1 and t.get("source_field", 0) >= 1, str(t))
    af = next(a for a in api["artifacts"] if a["artifact_type"] == "atomic_fact")
    al = next(a for a in api["artifacts"] if a["artifact_type"] == "narrative_allegation")
    check("API atomic_fact has #field handle + is promotion-eligible", "#" in af["source_handle"] and af["promotion_eligible"] is True)
    check("API narrative is a held-out allegation (#field.sN, not promotion-eligible)",
          ".s" in al["source_handle"] and al["promotion_eligible"] is False and al["claim_status"] == "unverified_allegation")

    # ── CSV (tenant_private table) ──
    csv = normalize("csv", "id,amount,note\n1,35,Unfair fee. No refund.\n", tenant_id="acme", source_id="export1", scope="tenant_private")
    fact = next(a for a in csv["artifacts"] if a["artifact_type"] == "atomic_fact")
    alleg = next(a for a in csv["artifacts"] if a["artifact_type"] == "narrative_allegation")
    check("CSV fact handle is ctx://tenant/.../source/...#row.<n>.col.<col>", "#row.0.col." in fact["source_handle"], fact["source_handle"])
    check("CSV free-text cell is a held-out allegation", ".s0" in alleg["source_handle"] and alleg["promotion_eligible"] is False)
    check("CSV artifacts carry tenant_private scope", all(a["scope"] == "tenant_private" for a in csv["artifacts"]))

    # ── JSON (webhook, tenant_private) ──
    js = normalize("json", {"complaint": {"id": "C1", "deadline_days": 10, "narrative": "They charged twice."}},
                   tenant_id="acme", source_id="wh1", scope="tenant_private", authority="customer_private")
    jf = next(a for a in js["artifacts"] if a["artifact_type"] == "atomic_fact")
    check("JSON fact uses a JSON-pointer handle (#/path/to/field)", jf["source_handle"].split("#")[1].startswith("/"), jf["source_handle"])

    # ── determinism + per-field hash isolation ──
    a1 = normalize("api", [{"complaint_id": "C1", "product": "Credit card"}], tenant_id="demo", source_id="s", scope="global_public")
    a2 = normalize("api", [{"complaint_id": "C1", "product": "Credit card"}], tenant_id="demo", source_id="s", scope="global_public")
    check("same payload → identical artifacts (deterministic content hashes)", a1 == a2)
    a3 = normalize("api", [{"complaint_id": "C1", "product": "Mortgage"}], tenant_id="demo", source_id="s", scope="global_public")
    h1 = {a["source_handle"]: a["content_hash"] for a in a1["artifacts"]}
    h3 = {a["source_handle"]: a["content_hash"] for a in a3["artifacts"]}
    prod_h = next(k for k in h1 if k.endswith("#product"))
    cid_h = next(k for k in h1 if k.endswith("#complaint_id"))
    check("changed field changes only its impacted artifact hash (not sibling fields)",
          h1[prod_h] != h3[prod_h] and h1[cid_h] == h3[cid_h])

    # ── gate-compatibility: a produced structured fact passes the verification gate ──
    gate = VerificationGate()
    res = gate.evaluate(af, context={"now": 1_000_000, "requested_scope": "global_public"}, now="2026-06-05T00:00:00Z")
    check("a multi-source atomic_fact is gate-verifiable (allow)", res["decision"].decision == "allow", str(res["decision"].reasons))
    res_al = gate.evaluate(al, context={"now": 1_000_000, "requested_scope": "global_public"}, now="2026-06-05T00:00:00Z")
    check("a multi-source allegation is held out by the gate", res_al["decision"].decision == "hold_out")

    # ── honest non-consumable: pdf parser unavailable + unknown type ──
    pdf = normalize("pdf", b"%PDF-1.4 fake bytes", tenant_id="demo", source_id="reg.pdf", scope="global_public")
    check("PDF (parser unavailable) is NON-consumable with a reason + raw stored, never faked",
          pdf["consumable"] is False and "parser_unavailable" in pdf["reason"] and len(pdf["source_artifacts"]) == 1
          and not any(a["artifact_type"] == "atomic_fact" for a in pdf["artifacts"]))
    unk = normalize("mystery", {"x": 1}, tenant_id="demo", source_id="u1")
    check("unknown source_type is NON-consumable with raw stored, not served", unk["consumable"] is False and unk["source_artifacts"])

    # ── source types registered ──
    reg = json.loads((_REPO / "architecture" / "contract_registry.json").read_text())
    names = {s["name"] for s in reg.get("source_types", [])}
    check("source types registered in contract_registry.json", {"api", "csv", "json", "pdf"} <= names, str(names))
    check("pdf/html registered as candidate (parser unavailable)",
          all(s["status"] == "candidate" for s in reg["source_types"] if s["name"] in ("pdf", "html")))

    print(f"\n{'PASS — check_multi_source_ingestion: api/csv/json flow through the governed path (correct per-type handles, facts promotion-eligible, allegations held out, deterministic, tenant-scoped, gate-compatible); pdf/unknown return explicit non-consumable reasons; source types registered.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: governed multi-source ingestion.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
