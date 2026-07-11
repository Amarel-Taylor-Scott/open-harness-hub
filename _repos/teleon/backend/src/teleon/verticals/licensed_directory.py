"""licensed_directory — the GENERAL 'licensed/credentialed entity directory freshness' capability. The provider-directory
pipeline (validate identifier -> normalize -> match -> cross-source agreement -> auto_update/human_review -> audit) is
profession-AGNOSTIC; this module instantiates it for ANY profession (physician, lawyer, engineer, CPA, financial advisor,
pharmacist, …) by swapping THREE things from _repos/shared-backend-components/architecture/licensed_professions.json: the authoritative SOURCES, the
IDENTIFIER (+ its validator), and the tracked FIELDS. One pipeline, hundreds of verticals. Insurance is excluded
(non-compete). Public/synthetic metadata only. serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import re
from functools import lru_cache
from pathlib import Path

from src.teleon.verticals import provider_directory as PD

_REGISTRY = _resource("architecture") / "licensed_professions.json"
_COST_RANK = {"free": 0, "browser": 1, "keyed": 2, "keyed_premium": 3, "stealth": 4}


@lru_cache(maxsize=1)
def _registry() -> dict:
    return json.loads(_REGISTRY.read_text())


def professions() -> list:
    return sorted(_registry()["professions"])


def profession(profession_id: str) -> dict | None:
    """The profession's config, or None if unknown or EXCLUDED (insurance)."""
    reg = _registry()
    if profession_id in reg.get("excluded", []):
        return None
    return reg["professions"].get(profession_id)


def authority_for(profession_id: str):
    """A source->weight function from THIS profession's sources (default 0.5) — what makes resolve profession-specific."""
    weights = {s["name"]: s["authority"] for s in (profession(profession_id) or {}).get("sources", [])}
    return lambda name: weights.get(name, 0.5)


def validate_identifier(profession_id: str, value) -> bool:
    """Dispatch to the profession's identifier validator: NPI Luhn (physicians/dentists/optometrists), numeric (CRD),
    alphanumeric (bar#/PE#/license#), or none. The framework picks the validator from config — no per-profession code."""
    p = profession(profession_id)
    if p is None:
        return False
    kind, v = p["id_validator"], str(value or "").strip()
    if kind == "npi_luhn":
        return PD.validate_npi(v)
    if kind == "numeric":
        return v.isdigit() and 1 <= len(v) <= 20
    if kind == "alphanumeric":
        return bool(re.fullmatch(r"[A-Za-z0-9\-]{2,30}", v))
    return True   # "none"


def source_descent(profession_id: str) -> list:
    """The profession's authoritative sources, cost-ordered (free public registries first, then your own browser …) —
    the same descent shape as the physician vertical, with this profession's registries."""
    src = (profession(profession_id) or {}).get("sources", [])
    return sorted(src, key=lambda s: (_COST_RANK.get(s["cost_tier"], 9), -s["authority"], s["name"]))


def resolve(profession_id: str, record: dict, source_observations: dict) -> dict:
    """The SAME resolve pipeline, parameterized for this profession (its tracked fields + source authority). Returns the
    structured recommendation + audit trail; honest error for an unknown/excluded profession."""
    p = profession(profession_id)
    if p is None:
        return {"error": f"unknown or excluded profession {profession_id!r}", "serves_truth": False}
    rec = PD.resolve_record(record, source_observations, fields=tuple(p["tracked_fields"]),
                            authority_fn=authority_for(profession_id))
    rec["profession"] = profession_id
    rec["identifier_valid"] = validate_identifier(profession_id, record.get(p["id_field"]))
    return rec
