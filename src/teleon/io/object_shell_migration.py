"""src.teleon.io.object_shell_migration — LOSSLESS migration of an object family to the canonical ObjectShell.

Distillation is never replacement: migrating an object to the shared 14-section shell PRESERVES the original verbatim
in `payload` (rehydratable to byte-identity), records the migration in `lineage` (migrated_from + original payload
hash), and carries the original's content_hash / derived-from / policy / timestamp forward. The shell is a wrapper, not
a rewrite — `rehydrate()` returns the exact original. Reuses the EXISTING canonical shell builder
(src/teleon/templates/instantiator.compose_object_shell) — no duplicate shell.
"""
from __future__ import annotations

from src.teleon.templates.instantiator import compose_object_shell, _content_hash


def migrate_to_shell(obj: dict, *, object_type: str, id_field: str, source_schema: str, now: str) -> dict:
    """Wrap any object as an ObjectShell, losslessly. The original is preserved in payload; lineage records the
    migration + the original payload hash; content_hash/derived_from/policy/created_at are carried forward."""
    shell = compose_object_shell(object_id=str(obj.get(id_field) or obj.get("object_id") or "(unknown)"),
                                 object_type=object_type, mixin_ids=None, now=now, payload=obj)
    derived = obj.get("derived_from") or obj.get("source_handles") or []
    if isinstance(derived, str):
        derived = [derived]
    shell["content_hash"] = obj.get("content_hash") or shell["content_hash"]  # keep the artifact's own integrity hash
    shell["source_handles"] = list(derived)
    shell["relationships"] = [{"type": "derived_from", "ref": d} for d in derived]
    shell["policy"] = obj.get("policy") or {}
    shell["created_at"] = obj.get("created_at") or now
    shell["lineage"] = {
        "migrated_from": source_schema,
        "migration": "ObjectShell",
        "original_preserved": True,          # the original lives verbatim in payload (rehydratable)
        "original_payload_hash": _content_hash(obj),
        "derived_from": derived,
        "lineage_event_id": obj.get("lineage_event_id"),
    }
    return shell


def rehydrate(shell: dict) -> dict:
    """Return the original object preserved by the migration — proving the wrap was lossless."""
    return shell["payload"]


def migrate_context_artifact(context_artifact: dict, *, now: str) -> dict:
    return migrate_to_shell(context_artifact, object_type="ContextArtifact",
                            id_field="context_artifact_id", source_schema="schemas/context-artifact.schema.json", now=now)


__all__ = ["migrate_to_shell", "rehydrate", "migrate_context_artifact"]
