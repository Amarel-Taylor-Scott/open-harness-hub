#!/usr/bin/env python3
"""Backs `processor/draft-manifest-yaml-emitter`.

Writes draft manifests to `catalog/_inbox/{type}/{slug}.yaml` and runs
per-file schema validation. Never writes to live `_repos/shared-backend-components/catalog/{type}/` paths
(per AGENTS.md hard rule).

On success: returns the written path + validation status.
On schema-validation failure: writes the draft to
`catalog/_inbox/_failed/{type}/{slug}.yaml` with a sibling `.errors.json`
file listing every validation error so the manifest author can revise.

Idempotent + deterministic. Same dict input → same on-disk output (modulo
YAML key ordering, which is normalized).

CLI:
    python -m scripts.processors.draft_manifest_yaml_emitter --self-test
    python -m scripts.processors.draft_manifest_yaml_emitter --emit draft.yaml
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
from scripts._repo_paths import resource as _resource
CATALOG = _resource("catalog")
INBOX = CATALOG / "_inbox"
INBOX_FAILED = INBOX / "_failed"
SCHEMAS = _resource("schemas")

TYPE_TO_SCHEMA = {
    "harness": "harness.schema.json",
    "pipeline": "pipeline.schema.json",
    "benchmark": "benchmark.schema.json",
    "rule-pack": "rule-pack.schema.json",
    "knowledge-pack": "knowledge-pack.schema.json",
    "logic-pack": "logic-pack.schema.json",
    "tool": "tool.schema.json",
    "persona": "persona.schema.json",
    "adapter": "adapter.schema.json",
    "rubric": "rubric.schema.json",
    "dataset": "dataset.schema.json",
    "processor": "processor.schema.json",
    "pattern": "pattern.schema.json",
}

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


# ─── Helpers ────────────────────────────────────────────────────────────────


def _load_yaml_or_fail() -> Any:
    try:
        import yaml
        return yaml
    except ImportError:
        sys.stderr.write("pyyaml is required: pip install pyyaml\n")
        sys.exit(2)


def _load_jsonschema_or_fail() -> tuple[Any, Any]:
    try:
        import jsonschema
        from jsonschema import Draft202012Validator
        return jsonschema, Draft202012Validator
    except ImportError:
        sys.stderr.write("jsonschema is required: pip install jsonschema\n")
        sys.exit(2)


def _load_schemas() -> dict[str, dict]:
    common = json.loads((SCHEMAS / "_common.schema.json").read_text())
    schemas: dict[str, dict] = {"_common.schema.json": common}
    for name in TYPE_TO_SCHEMA.values():
        schemas[name] = json.loads((SCHEMAS / name).read_text())
    return schemas


def _make_validator(schemas: dict[str, dict], schema_name: str):
    _jsonschema, Draft202012Validator = _load_jsonschema_or_fail()
    schema = schemas[schema_name]
    base = SCHEMAS.as_uri() + "/"
    resolver = _jsonschema.RefResolver(
        base_uri=base,
        referrer=schema,
        store={base + name: doc for name, doc in schemas.items()},
    )
    return Draft202012Validator(schema, resolver=resolver)


def _live_catalog_ids() -> set[str]:
    yaml = _load_yaml_or_fail()
    ids: set[str] = set()
    for path in CATALOG.rglob("*.yaml"):
        if "_inbox" in path.parts:
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            continue
        if isinstance(data, dict) and "id" in data:
            ids.add(data["id"])
    return ids


def _safe_relative(path: Path) -> str:
    """Best-effort relative-to-ROOT path; falls back to absolute when path is outside ROOT (test mode)."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _dump_yaml_canonical(data: dict) -> str:
    """Stable YAML output: preserves dict-insertion order, blocks long lines, no aliases."""
    yaml = _load_yaml_or_fail()
    return yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=100,
    )


# ─── Emit ───────────────────────────────────────────────────────────────────


def run(
    draft_manifest: dict,
    target_type: str | None = None,
    target_slug: str | None = None,
    *,
    overwrite_inbox: bool = False,
    check_live_collision: bool = True,
) -> dict[str, Any]:
    """Emit a draft to `catalog/_inbox/`, validate against its schema.

    target_type / target_slug are extracted from the draft's `id` field if not supplied.

    Returns:
        {
          "written_path": str,
          "validation_status": "ok" | "failed" | "collision",
          "validation_errors": [str, ...],
          "id_collision_with_live": bool,
          "errors_path": str | None,   # set when validation failed
        }
    """
    yaml = _load_yaml_or_fail()

    if not isinstance(draft_manifest, dict):
        raise TypeError("draft_manifest must be a mapping")

    mid = draft_manifest.get("id", "")
    if not isinstance(mid, str) or "/" not in mid:
        return {
            "written_path": "",
            "validation_status": "failed",
            "validation_errors": [f"draft id missing or malformed: {mid!r}"],
            "id_collision_with_live": False,
            "errors_path": None,
        }

    inferred_type, inferred_slug = mid.split("/", 1)
    final_type = target_type or inferred_type
    final_slug = target_slug or inferred_slug

    if final_type not in TYPE_TO_SCHEMA:
        return {
            "written_path": "",
            "validation_status": "failed",
            "validation_errors": [f"unknown component type: {final_type!r}"],
            "id_collision_with_live": False,
            "errors_path": None,
        }

    if not SLUG_RE.match(final_slug) or len(final_slug) > 64:
        return {
            "written_path": "",
            "validation_status": "failed",
            "validation_errors": [
                f"slug must be lowercase-with-dashes and ≤64 chars: {final_slug!r}"
            ],
            "id_collision_with_live": False,
            "errors_path": None,
        }

    # Live-catalog id collision check
    id_collision = False
    if check_live_collision:
        if mid in _live_catalog_ids():
            id_collision = True
            return {
                "written_path": "",
                "validation_status": "collision",
                "validation_errors": [f"id {mid!r} already exists in live catalog"],
                "id_collision_with_live": True,
                "errors_path": None,
            }

    # Pre-emit normalization: ensure type field matches inferred-or-target type
    draft_normalized = dict(draft_manifest)
    draft_normalized["type"] = final_type

    # Validate against the schema
    schemas = _load_schemas()
    schema_name = TYPE_TO_SCHEMA[final_type]
    validator = _make_validator(schemas, schema_name)
    raw_errors = sorted(validator.iter_errors(draft_normalized), key=lambda e: list(e.path))
    validation_errors = [
        {
            "path": "/".join(str(p) for p in e.path) or "<root>",
            "message": e.message,
            "schema_path": "/".join(str(p) for p in e.schema_path),
        }
        for e in raw_errors
    ]

    if validation_errors:
        target_dir = INBOX_FAILED / final_type
        target_dir.mkdir(parents=True, exist_ok=True)
        written = target_dir / f"{final_slug}.yaml"
        errors_path = target_dir / f"{final_slug}.errors.json"
        if written.exists() and not overwrite_inbox:
            return {
                "written_path": "",
                "validation_status": "failed",
                "validation_errors": validation_errors,
                "id_collision_with_live": False,
                "errors_path": "",
                "note": f"would overwrite existing _failed/ draft: {written}",
            }
        written.write_text(_dump_yaml_canonical(draft_normalized), encoding="utf-8")
        errors_path.write_text(json.dumps(validation_errors, indent=2, ensure_ascii=False), encoding="utf-8")
        return {
            "written_path": _safe_relative(written),
            "validation_status": "failed",
            "validation_errors": validation_errors,
            "id_collision_with_live": False,
            "errors_path": _safe_relative(errors_path),
        }

    # Success — write to _inbox/{type}/
    target_dir = INBOX / final_type
    target_dir.mkdir(parents=True, exist_ok=True)
    written = target_dir / f"{final_slug}.yaml"
    if written.exists() and not overwrite_inbox:
        # Re-check: if same content, no-op. If different, collision in inbox.
        existing = yaml.safe_load(written.read_text(encoding="utf-8"))
        if existing == draft_normalized:
            return {
                "written_path": _safe_relative(written),
                "validation_status": "ok",
                "validation_errors": [],
                "id_collision_with_live": False,
                "errors_path": None,
                "note": "no-op (identical inbox draft already present)",
            }
        return {
            "written_path": "",
            "validation_status": "failed",
            "validation_errors": [
                f"different draft already in inbox at {written}; pass overwrite_inbox=True to replace"
            ],
            "id_collision_with_live": False,
            "errors_path": None,
        }

    written.write_text(_dump_yaml_canonical(draft_normalized), encoding="utf-8")
    return {
        "written_path": _safe_relative(written),
        "validation_status": "ok",
        "validation_errors": [],
        "id_collision_with_live": id_collision,
        "errors_path": None,
    }


# ─── Self-test (offline; writes to a temp inbox + cleans up) ────────────────


def _self_test() -> int:
    import tempfile
    import shutil

    global INBOX, INBOX_FAILED
    saved_inbox = INBOX
    saved_failed = INBOX_FAILED
    tmpdir = Path(tempfile.mkdtemp(prefix="oh-emitter-test-"))
    INBOX = tmpdir / "_inbox"
    INBOX_FAILED = INBOX / "_failed"

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        marker = "ok" if ok else "FAIL"
        print(f"  [{marker}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    try:
        print("[self-test] valid persona draft → ok")
        valid_draft = {
            "id": "persona/emitter-self-test-persona",
            "type": "persona",
            "version": "0.1.0",
            "name": "Emitter self-test persona",
            "description": "A throw-away persona used by the emitter self-test. It exists only to "
                           "verify that the emitter writes valid drafts to the inbox correctly.",
            "license": "MIT",
            "lifecycle": "experimental",
            "industry": ["cross_industry"],
            "capability": ["reasoning"],
            "modality": ["text"],
            "trust_boundary": "local",
            "tags": ["self-test"],
            "created": "2026-05-24",
            "updated": "2026-05-24",
            "system_prompt": "You are a self-test persona.",
            "role": "self_test",
            "domain": ["cross_industry"],
            "tone": "neutral",
            "refusal_style": "decline",
        }
        # Bypass live-collision check for the synthetic slug
        res = run(valid_draft, check_live_collision=False)
        check("validation_status=ok", res["validation_status"] == "ok", str(res))
        check("written_path under _inbox/persona", "_inbox/persona/" in res["written_path"])

        print("[self-test] invalid draft → failed + errors.json written")
        invalid_draft = {**valid_draft, "id": "persona/emitter-self-test-invalid",
                         "lifecycle": "not-a-valid-lifecycle"}
        res = run(invalid_draft, check_live_collision=False)
        check("validation_status=failed", res["validation_status"] == "failed")
        check("errors_path is set", bool(res.get("errors_path")))
        check("validation_errors non-empty", len(res["validation_errors"]) > 0)

        print("[self-test] malformed id → rejected before schema check")
        bad_id = {**valid_draft, "id": "not-a-valid-id"}
        res = run(bad_id, check_live_collision=False)
        check("rejected on malformed id", res["validation_status"] == "failed")

        print("[self-test] unknown type → rejected")
        bad_type = {**valid_draft, "id": "bogus-type/foo"}
        res = run(bad_type, check_live_collision=False)
        check("rejected on unknown type", res["validation_status"] == "failed")

    finally:
        INBOX = saved_inbox
        INBOX_FAILED = saved_failed
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"\n{'all self-tests passed.' if not failures else f'{len(failures)} failures: {failures}'}")
    return 0 if not failures else 1


# ─── CLI ────────────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Emit + validate draft manifests into catalog/_inbox/")
    p.add_argument("--emit", help="Path to a draft YAML to emit")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--overwrite-inbox", action="store_true")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()
    if not args.emit:
        p.error("--emit PATH or --self-test required")

    yaml = _load_yaml_or_fail()
    draft = yaml.safe_load(Path(args.emit).read_text(encoding="utf-8"))
    res = run(draft, overwrite_inbox=args.overwrite_inbox)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res["validation_status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(_main())
