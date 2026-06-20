"""src.teleon.templates.instantiator — compose the canonical object shell from mixins + safely instantiate
schema-object starting shapes (CANDIDATE only). Pure + deterministic; no network, no secret substitution.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[3]
_SHELL = _REPO / "templates" / "schema-objects" / "canonical_object_shell.json"
_MIXINS = _REPO / "templates" / "schema-objects" / "mixins"
_A = _REPO / "architecture"
CANDIDATE_STATUS = 200      # generated outputs are CANDIDATE, never active (400)
INTERNAL_VISIBILITY = 100
_ACTIVE_STATUS = 400


def load_shell() -> dict:
    return json.loads(_SHELL.read_text(encoding="utf-8"))


def load_mixins() -> dict[str, dict]:
    return {p.stem.replace(".mixin", ""): json.loads(p.read_text(encoding="utf-8")) for p in _MIXINS.glob("*.mixin.json")}


def load_schema_object_templates() -> dict[str, dict]:
    doc = json.loads((_A / "schema_object_templates.json").read_text(encoding="utf-8"))
    return {t["object_family"]: t for t in doc["templates"]}


def _content_hash(payload: dict) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(payload or {}, sort_keys=True).encode()).hexdigest()


def compose_object_shell(*, object_id: str, object_type: str, mixin_ids: list[str] | None, now: str,
                         payload: dict | None = None, tenant_id: str | None = None, project_id: str | None = None,
                         status_code: int = CANDIDATE_STATUS, visibility_code: int = INTERNAL_VISIBILITY) -> dict:
    """Compose a canonical-shell object. Defaults to CANDIDATE status + internal visibility. Always carries all
    14 sections; never embeds a raw secret (security holds secret_refs only)."""
    payload = payload or {}
    mixins = load_mixins()
    use = mixin_ids if mixin_ids is not None else list(mixins)
    obj = {
        "object_id": object_id, "object_type": object_type, "schema_version": "v1",
        "tenant_id": tenant_id, "project_id": project_id,
        "input_contract": None, "output_contract": None,
        "payload": payload, "payload_ref": None, "content_hash": _content_hash(payload),
        "source_handles": [], "provenance": {"generated_by": "shared_template_registry", "generated_at": now},
        "lineage": {}, "policy": {}, "security": {"secret_refs": []},
        "visibility_code": visibility_code, "status_code": status_code,
        "telemetry": {}, "relationships": [], "receipts": [],
        "created_at": now, "updated_at": now,
        "_composed_from_mixins": sorted(m for m in use if m in mixins),
    }
    return obj


def _safe_target(out_dir: Path, name: str) -> Path:
    """Resolve out_dir/name, refusing path traversal outside out_dir."""
    out_dir = out_dir.resolve()
    target = (out_dir / name).resolve()
    if out_dir not in target.parents and target != out_dir:
        raise ValueError(f"unsafe template output path: {name}")
    return target


def instantiate_schema_object(object_family: str, *, out_dir: Path, now: str, object_id: str | None = None,
                              allow_overwrite: bool = False) -> dict:
    """Render a CANDIDATE schema-object starting shape for `object_family` into out_dir + a receipt. Refuses
    overwrite (unless allowed) and path traversal; never substitutes a secret value."""
    templates = load_schema_object_templates()
    if object_family not in templates:
        raise KeyError(f"no schema-object template for {object_family!r}")
    tpl = templates[object_family]
    oid = object_id or f"{object_family.lower()}.example@v1"
    obj = compose_object_shell(object_id=oid, object_type=object_family, mixin_ids=tpl["required_mixins"], now=now)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = _safe_target(out_dir, f"{object_family}.candidate.json")
    if target.exists() and not allow_overwrite:
        raise FileExistsError(f"refusing to overwrite {target.name} (allow_overwrite=False)")
    target.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    receipt = {
        "schema_version": "TemplateInstantiationReceipt.v1",
        "receipt_id": "tplrcpt_" + hashlib.blake2b(f"{object_family}|{oid}|{now}".encode(), digest_size=10).hexdigest(),
        "schema_template_id": tpl["schema_template_id"], "object_family": object_family, "object_id": oid,
        "output_path": str(target.relative_to(_REPO)) if str(target).startswith(str(_REPO)) else str(target),
        "status_code": CANDIDATE_STATUS, "status_label": "candidate", "is_active": False, "is_truth": False,
        "secret_substituted": False, "created_at": now,
    }
    (out_dir / f"{object_family}.receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return {"object": obj, "receipt": receipt, "path": target}


def is_active_status(code: int) -> bool:
    return code == _ACTIVE_STATUS


__all__ = ["compose_object_shell", "instantiate_schema_object", "load_shell", "load_mixins",
           "load_schema_object_templates", "is_active_status", "CANDIDATE_STATUS", "INTERNAL_VISIBILITY"]
