#!/usr/bin/env python3
"""scripts.alias_resolver — the Presentation/Alias layer (standardize concepts, customize copy).

Canonical Baltor concepts have STABLE ids (`stage.anti_fragility`, `object.context_pack`,
`rail.continuous_verification`); audience-facing LABELS are flexible and resolved here through a
deterministic fallback chain. Ids never depend on labels, so a customer can rename
"Anti-Fragility" → "Context Hardening" without breaking workflows, schemas, metrics, or receipts.
Legacy "Oracle" wording becomes a DEPRECATED ALIAS, not a canonical concept.

Resolution order (highest priority first):
    user_override → tenant pack → industry pack → audience pack → (locale) → default pack → canonical label

Governance ("do not alias away meaning"): a candidate value containing a BLOCKED term (e.g.
"oracle", "truth engine", "omniscient", "guaranteed truth") is SKIPPED and the chain continues —
the system never renders a misleading-truth claim, even if a pack tries. Blocked = global set ∪ the
audience pack's own blocked_terms.

Spec: docs/standards/presentation-layer.md. Deterministic + offline; stdlib + PyYAML.

CLI:
    python3 _repos/shared-backend-components/scripts/alias_resolver.py --self-test
    python3 _repos/shared-backend-components/scripts/alias_resolver.py stage.anti_fragility --audience security
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
CANONICAL_TERMS = _resource("data") / "presentation" / "canonical-terms.yaml"
ALIAS_PACK_DIR = _resource("data") / "alias-packs"
ALIAS_PACK_SCHEMA = _resource("schemas") / "presentation" / "alias-pack.schema.json"

#: Global governance — values implying omniscient/absolute truth or unsafe guarantees are blocked.
BLOCKED_TERMS = ("oracle", "truth engine", "omniscient", "guaranteed truth", "perfect context",
                 "unbreakable", "risk-free", "magic")


def load_canonical_terms() -> dict[str, str]:
    import yaml
    data = yaml.safe_load(CANONICAL_TERMS.read_text(encoding="utf-8"))
    return {t["id"]: t["canonical_label"] for t in data.get("terms", [])}


def load_pack(audience: str) -> dict[str, Any]:
    import yaml
    path = ALIAS_PACK_DIR / f"{audience}.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def check_value(value: str, *, extra_blocked: tuple[str, ...] = ()) -> bool:
    """True iff the value contains no blocked term (case-insensitive)."""
    low = (value or "").lower()
    return not any(b.lower() in low for b in (BLOCKED_TERMS + tuple(extra_blocked)))


def _alias_from_pack(pack: dict, cid: str, alias_type: str) -> str | None:
    a = (pack.get("aliases") or {}).get(cid)
    return a.get(alias_type) if isinstance(a, dict) else None


def resolve(
    canonical_id: str,
    *,
    alias_type: str = "label",
    audience: str | None = None,
    tenant_pack: dict | None = None,
    industry_pack: dict | None = None,
    user_override: dict | None = None,
) -> dict[str, Any]:
    """Resolve a canonical id → display value via the deterministic chain. Raises KeyError if the
    canonical id is unknown. Returns {canonical_id, value, source, alias_type}."""
    canon = load_canonical_terms()
    if canonical_id not in canon:
        raise KeyError(f"unknown canonical_id: {canonical_id!r}")

    audience_pack = load_pack(audience) if (audience and audience != "default") else {}
    extra_blocked = tuple(audience_pack.get("blocked_terms", []) or [])

    chain: list[tuple[str, str | None]] = []
    if user_override and canonical_id in user_override:
        chain.append(("user_override", user_override[canonical_id]))
    if tenant_pack:
        chain.append(("tenant", _alias_from_pack(tenant_pack, canonical_id, alias_type)))
    if industry_pack:
        chain.append(("industry", _alias_from_pack(industry_pack, canonical_id, alias_type)))
    if audience_pack:
        chain.append((f"audience:{audience}", _alias_from_pack(audience_pack, canonical_id, alias_type)))
    chain.append(("default", _alias_from_pack(load_pack("default"), canonical_id, alias_type)))

    for source, val in chain:
        if val and check_value(val, extra_blocked=extra_blocked):
            return {"canonical_id": canonical_id, "value": val, "source": source, "alias_type": alias_type}

    # Final fallback: the canonical label (only meaningful for the 'label' alias type).
    if alias_type == "label":
        return {"canonical_id": canonical_id, "value": canon[canonical_id], "source": "canonical", "alias_type": alias_type}
    return {"canonical_id": canonical_id, "value": None, "source": "none", "alias_type": alias_type}


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # ── alias packs are schema-valid ──
    import json
    from jsonschema import Draft202012Validator
    schema = json.loads(ALIAS_PACK_SCHEMA.read_text(encoding="utf-8"))
    v = Draft202012Validator(schema)
    for pack_name in ("default", "security"):
        errs = list(v.iter_errors(load_pack(pack_name)))
        check(f"{pack_name} alias pack is schema-valid", not errs, "; ".join(e.message for e in errs[:2]))

    # ── default resolution + audience override ──
    check("default → canonical label", resolve("stage.anti_fragility")["value"] == "Anti-Fragility")
    sec = resolve("stage.anti_fragility", audience="security")
    check("security audience → Context Hardening", sec["value"] == "Context Hardening" and sec["source"] == "audience:security", str(sec))

    # ── fallback chain priority: user > tenant > audience > default > canonical ──
    tenant = {"aliases": {"stage.anti_fragility": {"label": "Stabilization"}}}
    check("tenant pack beats audience", resolve("stage.anti_fragility", audience="security", tenant_pack=tenant)["value"] == "Stabilization")
    uo = {"stage.anti_fragility": "Resilience Layer"}
    check("user override beats tenant", resolve("stage.anti_fragility", audience="security", tenant_pack=tenant, user_override=uo)["value"] == "Resilience Layer")

    # ── label-independent ids: same id, different audiences → different labels, same canonical_id ──
    a = resolve("stage.optimization")
    b = resolve("stage.optimization", audience="security")
    check("same canonical id, different copy", a["value"] == "Optimization" and b["value"] == "Context Minimization" and a["canonical_id"] == b["canonical_id"])

    # ── fallback to default when audience pack lacks the term ──
    cp = resolve("object.context_pack", audience="security")
    check("audience missing term → default pack", cp["value"] == "Context Pack" and cp["source"] == "default", str(cp))

    # ── GOVERNANCE: a blocked value is skipped, never rendered ──
    check("check_value rejects a blocked term", not check_value("Verified Truth Engine"))
    check("check_value accepts a safe label", check_value("Continuous Assurance"))
    bad_override = {"stage.anti_fragility": "Truth Engine"}
    r = resolve("stage.anti_fragility", audience="security", user_override=bad_override)
    check("blocked user override is skipped → falls through (not rendered)", r["value"] == "Context Hardening" and r["source"] != "user_override", str(r))

    # ── unknown id raises; determinism ──
    raised = False
    try:
        resolve("stage.does_not_exist")
    except KeyError:
        raised = True
    check("unknown canonical id raises", raised)
    check("resolve is deterministic", resolve("stage.enhancement", audience="security") == resolve("stage.enhancement", audience="security"))

    print(f"\n{'all alias_resolver self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Resolve a canonical Baltor id → audience display label (Presentation/Alias layer).")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("canonical_id", nargs="?")
    p.add_argument("--audience", default=None)
    p.add_argument("--alias-type", default="label")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.canonical_id:
        print(resolve(args.canonical_id, alias_type=args.alias_type, audience=args.audience))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
