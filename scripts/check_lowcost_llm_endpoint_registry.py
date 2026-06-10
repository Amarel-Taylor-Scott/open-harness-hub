#!/usr/bin/env python3
"""scripts.check_lowcost_llm_endpoint_registry — PROOF: the GOVERNED LOW-COST PAID LLM lane catalog
(cheaper Chinese / China-adjacent endpoints) is structurally sound, governed, and honest — deterministically.

This catalogs a lane DISTINCT from the FREE registry: every entry is low-cost PAID (cost_class lowcost_usd),
candidate (never active), output is never truth, secrets are refs only, and the DATA-CLASS + JURISDICTION
policy is load-bearing — low-cost / China-region lanes carry ONLY public + internal_non_sensitive data.

Asserts:
  A. FILE LOADS: architecture/lowcost_llm_endpoint_registry.json parses; has version/note/governance_law/
     lane_taxonomy/valid_data_classes/admit_tiers/entries.
  B. ENOUGH ENTRIES: >= 8 entries.
  C. REQUIRED FIELDS present on every entry.
  D. COST CLASS: every cost_class in {lowcost_usd, paid}.
  E. NEVER ACTIVE: no entry status == "active"; status in {candidate, probation, watchlist, exclude}.
  F. DATA-CLASS POLICY (load-bearing): NO entry's allowed_data_classes contains any forbidden class
     (customer / regulated / secrets / confidential / pii).
  G. REGION + RESIDENCY + SECRET_REF + ADMIT_TIER: every entry has non-empty provider_regions,
     data_residency, secret_ref (vault://, NOT a raw key), and a valid admit_tier.
  H. NO RAW KEYS anywhere in the file (regex sk- / AKIA / gsk-).
  I. GOVERNANCE_LAW states lowcost!=free + candidate!=active + a data-class policy + output!=truth.
  J. LANE TAXONOMY includes free/* AND lowcost/* AND paid/* AND selfhost/*.
  K. DeepSeek + Qwen present as admit_first.
  L. PRODUCTION DISABLED: production_allowed is false for every entry.
  M. ADMIT TIERS list exactly [admit_first, probation, watchlist, exclude]; valid_data_classes present;
     Together AI present as exclude.
  N. DETERMINISM: re-reading the file yields identical entries.

Deterministic + offline. stdlib only. Exit 0/1.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_REGISTRY = _REPO / "architecture" / "lowcost_llm_endpoint_registry.json"

# Data classes that low-cost / China-region lanes must NEVER carry. Single source for this check.
FORBIDDEN_DATA_CLASSES = ("customer", "regulated", "secrets", "confidential", "pii")
ALLOWED_COST_CLASSES = ("lowcost_usd", "paid")
EXPECTED_ADMIT_TIERS = ["admit_first", "probation", "watchlist", "exclude"]
EXPECTED_STATUSES = {"candidate", "probation", "watchlist", "exclude"}
REQUIRED_FIELDS = (
    "provider_id", "display_name", "adapter", "base_url", "model",
    "cost_per_mtok_usd", "context_window", "capabilities", "cost_class",
    "provider_regions", "data_residency", "allowed_data_classes",
    "production_allowed", "secret_ref", "admit_tier", "status", "data_use_note",
)
# Raw-key markers: OpenAI-style sk-, AWS AKIA, Groq gsk-. Word-boundary'd so prose like "secret_ref" is safe.
_RAW_KEY_RE = re.compile(r"\b(sk-[A-Za-z0-9]{12,}|AKIA[0-9A-Z]{12,}|gsk-[A-Za-z0-9]{12,})\b")


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    # ── A: file loads + top-level shape ──
    raw = _REGISTRY.read_text(encoding="utf-8")
    reg = json.loads(raw)  # raises -> non-zero via traceback if malformed
    for key in ("version", "note", "governance_law", "lane_taxonomy",
                "valid_data_classes", "admit_tiers", "entries"):
        check(f"A: top-level key present: {key}", key in reg)
    entries = reg.get("entries", [])
    check("A: entries is a non-empty list", isinstance(entries, list) and len(entries) > 0)

    # ── B: enough entries ──
    check("B: >= 8 entries", len(entries) >= 8, f"got {len(entries)}")

    # ── C: required fields on every entry ──
    missing = {e.get("provider_id", "?"): [f for f in REQUIRED_FIELDS if f not in e] for e in entries}
    missing = {k: v for k, v in missing.items() if v}
    check("C: every entry has all required fields", not missing, json.dumps(missing))

    # ── D: cost_class ──
    bad_cost = [e.get("provider_id") for e in entries if e.get("cost_class") not in ALLOWED_COST_CLASSES]
    check("D: every cost_class in {lowcost_usd, paid}", not bad_cost, str(bad_cost))

    # ── E: never active ──
    active = [e.get("provider_id") for e in entries if e.get("status") == "active"]
    check("E: no entry status == 'active'", not active, str(active))
    bad_status = [e.get("provider_id") for e in entries if e.get("status") not in EXPECTED_STATUSES]
    check("E: every status in {candidate, probation, watchlist, exclude}", not bad_status, str(bad_status))

    # ── F: data-class policy (LOAD-BEARING) ──
    leaks = {
        e.get("provider_id"): [c for c in e.get("allowed_data_classes", []) if c in FORBIDDEN_DATA_CLASSES]
        for e in entries
    }
    leaks = {k: v for k, v in leaks.items() if v}
    check("F: NO entry allows customer/regulated/secrets/confidential/pii", not leaks, json.dumps(leaks))
    # and allowed classes must be a subset of valid_data_classes
    valid_dc = set(reg.get("valid_data_classes", []))
    oob = {e.get("provider_id"): [c for c in e.get("allowed_data_classes", []) if c not in valid_dc]
           for e in entries}
    oob = {k: v for k, v in oob.items() if v}
    check("F: allowed_data_classes subset of valid_data_classes", not oob, json.dumps(oob))

    # ── G: region + residency + secret_ref(vault://) + admit_tier ──
    def _bad_g(e: dict) -> str:
        regions = e.get("provider_regions")
        if not (isinstance(regions, list) and regions):
            return "provider_regions empty"
        if not str(e.get("data_residency", "")).strip():
            return "data_residency empty"
        sref = e.get("secret_ref", "")
        if not (isinstance(sref, str) and sref.startswith("vault://")):
            return f"secret_ref not vault://: {sref!r}"
        if e.get("admit_tier") not in EXPECTED_ADMIT_TIERS:
            return f"admit_tier invalid: {e.get('admit_tier')!r}"
        return ""
    bad_g = {e.get("provider_id"): _bad_g(e) for e in entries}
    bad_g = {k: v for k, v in bad_g.items() if v}
    check("G: every entry has provider_regions + data_residency + vault:// secret_ref + valid admit_tier",
          not bad_g, json.dumps(bad_g))

    # ── H: no raw keys anywhere ──
    hits = _RAW_KEY_RE.findall(raw)
    check("H: no raw API keys in the file (sk-/AKIA/gsk-)", not hits, str(hits))

    # ── I: governance_law content ──
    law = reg.get("governance_law", "").lower()
    check("I: governance_law states lowcost != free", "lowcost != free" in law)
    check("I: governance_law states candidate != active", "candidate != active" in law)
    check("I: governance_law states a data-class policy", "data-class" in law or "data class" in law)
    check("I: governance_law states output != truth", "output != truth" in law)

    # ── J: lane taxonomy spans free/lowcost/paid/selfhost ──
    lanes = reg.get("lane_taxonomy", {})
    lane_keys = " ".join(lanes.keys()) if isinstance(lanes, dict) else str(lanes)
    check("J: lane_taxonomy includes free/*", "free/" in lane_keys)
    check("J: lane_taxonomy includes lowcost/*", "lowcost/" in lane_keys)
    check("J: lane_taxonomy includes paid/*", "paid/" in lane_keys)
    check("J: lane_taxonomy includes selfhost/*", "selfhost/" in lane_keys)
    # every entry's lane is one of the taxonomy keys (when lane present)
    if isinstance(lanes, dict):
        bad_lane = [e.get("provider_id") for e in entries
                    if "lane" in e and e.get("lane") not in lanes]
        check("J: every entry.lane is a declared taxonomy key", not bad_lane, str(bad_lane))

    # ── K: DeepSeek + Qwen present as admit_first ──
    by_id = {e.get("provider_id"): e for e in entries}
    def _is_admit_first(substr: str) -> bool:
        return any(substr in pid and e.get("admit_tier") == "admit_first" for pid, e in by_id.items())
    check("K: DeepSeek present as admit_first", _is_admit_first("deepseek"))
    check("K: Qwen present as admit_first", _is_admit_first("qwen"))

    # ── L: production disabled everywhere ──
    prod_on = [e.get("provider_id") for e in entries if e.get("production_allowed") is not False]
    check("L: production_allowed is false for every entry", not prod_on, str(prod_on))

    # ── M: admit tiers list + valid_data_classes + Together excluded ──
    check("M: admit_tiers == [admit_first, probation, watchlist, exclude]",
          reg.get("admit_tiers") == EXPECTED_ADMIT_TIERS, str(reg.get("admit_tiers")))
    check("M: valid_data_classes is a non-empty list",
          isinstance(reg.get("valid_data_classes"), list) and bool(reg.get("valid_data_classes")))
    together = [e for pid, e in by_id.items() if "together" in pid]
    check("M: Together AI present as exclude (not catalogued as free)",
          bool(together) and all(e.get("admit_tier") == "exclude" and e.get("status") == "exclude"
                                 for e in together),
          str([(e.get("provider_id"), e.get("admit_tier"), e.get("status")) for e in together]))

    # ── N: determinism ──
    reg2 = json.loads(_REGISTRY.read_text(encoding="utf-8"))
    check("N: re-read yields identical entries", reg2.get("entries") == entries)

    ok = not fails
    print("\n" + ("PASS — check_lowcost_llm_endpoint_registry: the low-cost PAID Chinese/China-adjacent lane "
                  f"catalogs {len(entries)} entries, each low-cost-paid (lowcost!=free) and candidate "
                  "(never active, production disabled); secrets are vault:// refs (no raw keys); the data-class "
                  "policy holds (no customer/regulated/secrets/confidential/pii on any low-cost entry); "
                  "region+residency+admit_tier present; lane taxonomy spans free/lowcost/paid/selfhost; "
                  "DeepSeek+Qwen are admit_first; Together is excluded; output is never truth; deterministic."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_lowcost_llm_endpoint_registry.py --self-test")
    raise SystemExit(0)
