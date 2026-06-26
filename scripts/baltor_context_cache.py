#!/usr/bin/env python3
"""Write safe local Markdown cache files from the Baltor context gateway.

This is intentionally small and conservative: it stores compact context-pack
facts, risks, source handles, and glossary packets. It does not mirror raw
source documents.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts._config import CONTEXT_GATEWAY_RUNTIME_SETTINGS
from scripts.db.runtime_settings import runtime_setting

try:
    from scripts.baltor_context_client import BaltorContextClient
except ModuleNotFoundError:  # Support `python3 scripts/baltor_context_cache.py`.
    from baltor_context_client import BaltorContextClient


CONTEXT_GATEWAY_RUNTIME_NAMESPACE = "baltor.context_gateway.runtime"


def _context_cache_setting(name: str) -> str:
    return runtime_setting(
        namespace=CONTEXT_GATEWAY_RUNTIME_NAMESPACE,
        definitions=CONTEXT_GATEWAY_RUNTIME_SETTINGS,
        name=name,
    )


DEFAULT_BASE_URL = _context_cache_setting("gateway_base_url")
DEFAULT_OUT_DIR = Path(_context_cache_setting("local_cache_dir"))
DEFAULT_AUDIT_LOG = _context_cache_setting("local_cache_audit_log")
DEFAULT_MANIFEST = _context_cache_setting("local_cache_manifest")
MANIFEST_KIND = "baltor.local-context-cache-manifest"
WRITE_EVENT = "baltor.context_cache.write"


def slug(value: object) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", str(value or "")).strip("-").lower()
    return text[:80] or "unknown"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_audit(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def read_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"kind": MANIFEST_KIND, "entries": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"kind": MANIFEST_KIND, "entries": []}
    if payload.get("kind") != MANIFEST_KIND:
        return {"kind": MANIFEST_KIND, "entries": []}
    if not isinstance(payload.get("entries"), list):
        payload["entries"] = []
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def context_markdown(search: dict[str, Any], glossary: dict[str, Any]) -> str:
    pack = search.get("context_pack") or {}
    lines = [
        f"# Baltor Context Cache: {search.get('result_id') or 'unknown'}",
        "",
        f"- Cached at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"- Run ID: {glossary.get('run_id') or 'unknown'}",
        f"- Query: {search.get('query') or ''}",
        f"- Pack type: {search.get('pack_type') or ''}",
        f"- Token budget estimate: {search.get('token_budget_used_estimate')}",
        "",
        "## Summary",
        "",
        str(pack.get("summary") or ""),
        "",
        "## Facts",
        "",
    ]
    for fact in pack.get("facts") or []:
        lines.extend([
            f"- {fact.get('claim')}",
            f"  - Handle: `{fact.get('handle')}`",
            f"  - Trust: `{fact.get('trust')}`",
            f"  - Refresh required: `{bool(fact.get('requires_refresh'))}`",
        ])
    lines.extend(["", "## Risks", ""])
    for risk in pack.get("risks") or []:
        lines.append(f"- {risk}")
    lines.extend(["", "## Source Handles", ""])
    for handle in pack.get("source_handles") or []:
        lines.append(f"- `{handle}`")
    lines.extend(["", "## Glossary Packets", ""])
    for packet in glossary.get("packets") or []:
        lines.extend([
            f"- `{packet.get('packet_id')}`: **{packet.get('term')}** ({packet.get('concern_type')})",
            f"  - Status: `{packet.get('status')}`",
            f"  - Review routes: `{', '.join(packet.get('review_routes') or [])}`",
            f"  - Source scoped only: `{(packet.get('safe_context_policy') or {}).get('source_scope_only')}`",
            f"  - Blocks global memory: `{(packet.get('safe_context_policy') or {}).get('block_global_memory_promotion')}`",
        ])
    lines.extend([
        "",
        "## Cache Policy",
        "",
        "- This file is a local cache, not a source of truth.",
        "- Do not paste raw source-system dumps into this cache.",
        "- Keep volatile facts dated and refresh before current use.",
        "- Keep glossary packets source-scoped until reviewed.",
        "",
    ])
    return "\n".join(lines)


def glossary_markdown(glossary: dict[str, Any]) -> str:
    lines = [
        f"# Baltor Glossary Cache: {glossary.get('run_id') or 'unknown'}",
        "",
        f"- Cached at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"- Packet count: {glossary.get('packet_count')}",
        "",
    ]
    for packet in glossary.get("packets") or []:
        entry = packet.get("proposed_glossary_entry") or {}
        lines.extend([
            f"## {packet.get('term')}",
            "",
            f"- Packet: `{packet.get('packet_id')}`",
            f"- Concern: `{packet.get('concern_type')}`",
            f"- Status: `{packet.get('status')}`",
            f"- Source: {packet.get('source')}",
            f"- Evidence: {packet.get('evidence')}",
            f"- Allowed meanings: {', '.join(packet.get('possible_meanings') or []) or '-'}",
            f"- Proposed scope: `{entry.get('scope')}`",
            f"- Canonical graph promotion allowed: `{entry.get('canonical_entity_allowed')}`",
            "",
        ])
    return "\n".join(lines)


def index_markdown(run_id: str, context_path: Path, glossary_path: Path) -> str:
    return "\n".join([
        "# Baltor Context Cache Index",
        "",
        f"- Updated at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"- Latest run: `{run_id}`",
        f"- Context pack: `{context_path.as_posix()}`",
        f"- Glossary packets: `{glossary_path.as_posix()}`",
        "",
    ])


def cache_policy() -> dict[str, bool]:
    return {
        "stores_raw_source_dump": False,
        "stores_source_handles": True,
        "glossary_packets_source_scoped": True,
        "blocks_global_memory_promotion": True,
    }


def update_cache_manifest(
    manifest_path: Path,
    *,
    base_url: str,
    run_id: str,
    query: str,
    context_path: Path,
    glossary_path: Path,
    audit_path: Path,
    fact_count: int,
    source_handle_count: int,
    glossary_packet_count: int,
) -> dict[str, Any]:
    manifest = read_manifest(manifest_path)
    entry = {
        "base_url": base_url,
        "cached_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_id": run_id,
        "query": query,
        "context_path": str(context_path),
        "glossary_path": str(glossary_path),
        "audit_log": str(audit_path),
        "fact_count": fact_count,
        "source_handle_count": source_handle_count,
        "glossary_packet_count": glossary_packet_count,
        "policy": cache_policy(),
    }
    entries = [item for item in manifest.get("entries", []) if item.get("run_id") != run_id or item.get("query") != query]
    entries.append(entry)
    manifest.update({
        "kind": MANIFEST_KIND,
        "updated_at": entry["cached_at"],
        "latest_run_id": run_id,
        "latest_context_path": str(context_path),
        "latest_glossary_path": str(glossary_path),
        "latest_audit_log": str(audit_path),
        "entry_count": len(entries),
        "policy": cache_policy(),
        "entries": entries[-50:],
    })
    write_json(manifest_path, manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--query", default="agency active vendor CCO ownership")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--audit-log", default="", help="JSONL audit log path; defaults to <out-dir>/cache-writes.jsonl")
    parser.add_argument("--manifest", default="", help="cache manifest path; defaults to <out-dir>/cache-manifest.json")
    parser.add_argument("--max-glossary-packets", type=int, default=20)
    args = parser.parse_args(argv)

    client = BaltorContextClient(args.base_url)
    search = client.search(args.query, run_id=args.run_id, token_budget=3000)
    if not search.get("ok"):
        raise SystemExit(json.dumps(search, indent=2))

    run_id = args.run_id or str((search.get("result_id") or "").replace("ctxr-", ""))
    glossary = client.glossary(run_id=args.run_id, max_packets=args.max_glossary_packets)
    if not glossary.get("ok"):
        raise SystemExit(json.dumps(glossary, indent=2))
    run_id = str(glossary.get("run_id") or run_id or "unknown")

    out_dir = Path(args.out_dir)
    context_path = out_dir / "runs" / f"{slug(run_id)}.context.md"
    glossary_path = out_dir / "glossary" / f"{slug(run_id)}.glossary.md"
    index_path = out_dir / "INDEX.md"
    write_text(context_path, context_markdown(search, glossary))
    write_text(glossary_path, glossary_markdown(glossary))
    write_text(index_path, index_markdown(run_id, context_path, glossary_path))
    audit_path = Path(args.audit_log) if args.audit_log else out_dir / DEFAULT_AUDIT_LOG
    manifest_path = Path(args.manifest) if args.manifest else out_dir / DEFAULT_MANIFEST
    fact_count = len((search.get("context_pack") or {}).get("facts") or [])
    source_handle_count = len((search.get("context_pack") or {}).get("source_handles") or [])
    glossary_packet_count = int(glossary.get("packet_count") or 0)
    manifest = update_cache_manifest(
        manifest_path,
        base_url=args.base_url,
        run_id=run_id,
        query=args.query,
        context_path=context_path,
        glossary_path=glossary_path,
        audit_path=audit_path,
        fact_count=fact_count,
        source_handle_count=source_handle_count,
        glossary_packet_count=glossary_packet_count,
    )
    append_audit(audit_path, {
        "event": WRITE_EVENT,
        "ts": int(time.time()),
        "base_url": args.base_url,
        "run_id": run_id,
        "query": args.query,
        "context_path": str(context_path),
        "glossary_path": str(glossary_path),
        "index_path": str(index_path),
        "manifest_path": str(manifest_path),
        "fact_count": fact_count,
        "source_handle_count": source_handle_count,
        "glossary_packet_count": glossary_packet_count,
        "policy": cache_policy(),
    })

    print(json.dumps({
        "ok": True,
        "run_id": run_id,
        "context_path": str(context_path),
        "glossary_path": str(glossary_path),
        "index_path": str(index_path),
        "audit_log": str(audit_path),
        "manifest_path": str(manifest_path),
        "manifest_kind": manifest.get("kind"),
        "manifest_entry_count": manifest.get("entry_count"),
        "fact_count": fact_count,
        "source_handle_count": source_handle_count,
        "glossary_packet_count": glossary_packet_count,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
