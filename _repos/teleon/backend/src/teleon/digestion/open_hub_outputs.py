"""src.teleon.digestion.open_hub_outputs — turn a SkillDigestRun into CANDIDATE records for the portfolio:
a SkillArtifact candidate (OpenSkillsHub) composed from the canonical object shell, and a Teleon PurposeTask /
runtime candidate. Everything is a candidate (never active); the original skill stays the fallback. Pure +
deterministic. Composes the Template Registry (canonical shell) + the digester; no src.baltor import.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path
from typing import Any

from src.teleon.digestion import digester as _dg
from src.teleon.templates import instantiator as _tpl

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])


def _skill_mixins() -> list[str]:
    doc = json.loads((_resource("architecture") / "schema_object_templates.json").read_text())
    for t in doc["templates"]:
        if t["object_family"] == "SkillArtifact":
            return t["required_mixins"]
    return ["identity", "scope", "provenance", "policy", "status", "relationships"]


def emit_open_hub_candidates(digest: dict, *, now: str) -> dict[str, Any]:
    """From a SkillDigestRun, emit candidate records. Unsafe digests emit NO candidate (quarantined)."""
    skill_id = digest["skill_id"]
    if digest["promotion_decision"] == "quarantine":
        return {"status": "quarantined", "reasons": digest.get("unsafe_flags", []),
                "openskillshub_skill_candidate": None, "teleon_runtime_candidate": None, "target_hubs": []}

    det = digest["determinism_extraction"]
    payload = {"why_ingested": f"digested skill {skill_id}: {len(det['deterministic_substeps'])} deterministic "
                               f"substeps → cheaper runtime cascade {digest['recommended_runtime_paths']}",
               "required_tools": digest["required_tools"], "required_models": digest["required_models"],
               "determinism_summary": det["deterministic_substeps"], "source_ref": digest["source_ref"],
               "duplicates": [], "eval_required": True}
    # OpenSkillsHub SkillArtifact candidate — composed from the canonical object shell (Template Registry)
    skill_artifact = _tpl.compose_object_shell(object_id=f"skill:{skill_id}", object_type="SkillArtifact",
                                               mixin_ids=_skill_mixins(), now=now, payload=payload)
    skill_artifact["provenance"] = {"generated_by": "skill_digestion_lab", "source_ref": digest["source_ref"],
                                    "source_hash": digest["source_hash"], "generated_at": now}
    skill_artifact["relationships"] = [{"relation": "fallback_for", "target": digest["fallback_skill_ref"]}]
    skill_artifact["is_truth"] = False  # an emitted candidate is advisory, never served truth
    # Teleon runtime candidate (the cheaper distilled path)
    teleon_candidate = _dg.build_runtime_candidate(digest, now=now)
    return {"status": "candidate", "openskillshub_skill_candidate": skill_artifact,
            "teleon_runtime_candidate": teleon_candidate, "fallback_skill_ref": digest["fallback_skill_ref"],
            "proof_to_promote": digest["proof_to_promote"], "target_hubs": ["openskillshub", "teleon"]}


__all__ = ["emit_open_hub_candidates"]
