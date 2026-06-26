#!/usr/bin/env python3
"""scripts.render_receipt — build a render receipt (rename-safe audit of how a concept was shown).

Composes the alias_resolver: given a canonical concept id + an audience, it resolves the display
label and emits a `baltor.render-receipt` that stores BOTH the stable canonical_id AND the
rendered_label + alias profile/version. Because the receipt anchors on canonical_id, a customer can
rename "Context Hardening" later without breaking this audit record (docs/standards/presentation-layer.md §17).

Deterministic + offline; stdlib + jsonschema + PyYAML. CLI:
    python3 scripts/render_receipt.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts import alias_resolver

_REPO = Path(__file__).resolve().parents[1]
RENDER_RECEIPT_SCHEMA = _REPO / "schemas" / "presentation" / "render-receipt.schema.json"


def build_render_receipt(
    canonical_id: str,
    *,
    audience: str = "default",
    alias_type: str = "label",
    surface: str = "unspecified",
    created_at: str,
) -> dict[str, Any]:
    """Resolve the label for (canonical_id, audience) and wrap it in a render receipt."""
    resolved = alias_resolver.resolve(canonical_id, alias_type=alias_type, audience=audience)
    pack = alias_resolver.load_pack(audience) if audience and audience != "default" else alias_resolver.load_pack("default")
    profile = pack.get("id", "alias_pack.default")
    version = pack.get("version", "0.0.0")
    return {
        "kind": "baltor.render-receipt",
        "render_receipt_id": f"rrcpt.{canonical_id}.{audience}.{version}",
        "canonical_id": canonical_id,
        "rendered_label": resolved["value"],
        "alias_type": alias_type,
        "alias_profile": profile,
        "alias_profile_version": version,
        "resolution_source": resolved["source"],
        "audience": audience,
        "surface": surface,
        "created_at": created_at,
    }


def _validator():
    from jsonschema import Draft202012Validator
    return Draft202012Validator(json.loads(RENDER_RECEIPT_SCHEMA.read_text(encoding="utf-8")))


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    ts = "2026-06-04T00:00:00Z"
    sec = build_render_receipt("stage.anti_fragility", audience="security", surface="admin_ui", created_at=ts)
    check("rendered_label reflects the audience", sec["rendered_label"] == "Context Hardening", str(sec["rendered_label"]))
    check("anchors on the STABLE canonical_id", sec["canonical_id"] == "stage.anti_fragility")
    check("records alias profile + version", sec["alias_profile"] == "alias_pack.security" and sec["alias_profile_version"] == "1.0.0", str(sec))

    v = _validator()
    check("render receipt is schema-valid", not list(v.iter_errors(sec)), "; ".join(e.message for e in v.iter_errors(sec)))

    # rename-safety: two audiences → different labels, SAME canonical_id (audit stays linkable)
    deflt = build_render_receipt("stage.anti_fragility", audience="default", created_at=ts)
    check("different rendered labels, same canonical anchor",
          deflt["rendered_label"] == "Anti-Fragility" and deflt["canonical_id"] == sec["canonical_id"])

    # governance carries through: a marketing receipt never renders a blocked term
    mkt = build_render_receipt("rail.continuous_verification", audience="marketing", created_at=ts)
    check("no blocked term rendered", alias_resolver.check_value(mkt["rendered_label"]), str(mkt["rendered_label"]))

    check("build is deterministic", build_render_receipt("stage.optimization", audience="security", created_at=ts) ==
          build_render_receipt("stage.optimization", audience="security", created_at=ts))

    print(f"\n{'all render_receipt self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build a render receipt (rename-safe audit of a rendered concept).")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
