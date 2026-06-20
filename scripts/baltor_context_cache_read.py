#!/usr/bin/env python3
"""Read a local Baltor context cache manifest without contacting the gateway."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts._config import CONTEXT_GATEWAY_RUNTIME_SETTINGS
from scripts.db.runtime_settings import runtime_setting


CONTEXT_GATEWAY_RUNTIME_NAMESPACE = "baltor.context_gateway.runtime"

def _context_cache_setting(name: str) -> str:
    return runtime_setting(
        namespace=CONTEXT_GATEWAY_RUNTIME_NAMESPACE,
        definitions=CONTEXT_GATEWAY_RUNTIME_SETTINGS,
        name=name,
    )


DEFAULT_OUT_DIR = Path(_context_cache_setting("local_cache_dir"))
DEFAULT_MANIFEST = _context_cache_setting("local_cache_manifest")
MANIFEST_KIND = "baltor.local-context-cache-manifest.v1"


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"cache manifest not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("kind") != MANIFEST_KIND:
        raise SystemExit(f"unexpected cache manifest kind: {payload.get('kind')}")
    return payload


def summary_markdown(manifest: dict[str, Any], *, include_entries: int) -> str:
    entries = list(manifest.get("entries") or [])
    latest = entries[-1] if entries else {}
    lines = [
        "# Baltor Local Context Cache",
        "",
        f"- Manifest kind: `{manifest.get('kind')}`",
        f"- Updated at: `{manifest.get('updated_at') or ''}`",
        f"- Latest run: `{manifest.get('latest_run_id') or ''}`",
        f"- Entry count: `{manifest.get('entry_count') or len(entries)}`",
        f"- Latest context: `{manifest.get('latest_context_path') or ''}`",
        f"- Latest glossary: `{manifest.get('latest_glossary_path') or ''}`",
        f"- Latest audit log: `{manifest.get('latest_audit_log') or ''}`",
        "",
        "## Policy",
        "",
    ]
    policy = manifest.get("policy") or {}
    for key in sorted(policy):
        lines.append(f"- {key}: `{policy[key]}`")
    lines.extend(["", "## Latest Entry", ""])
    if latest:
        lines.extend([
            f"- Query: {latest.get('query')}",
            f"- Source handles: `{latest.get('source_handle_count')}`",
            f"- Facts: `{latest.get('fact_count')}`",
            f"- Glossary packets: `{latest.get('glossary_packet_count')}`",
            f"- Context path: `{latest.get('context_path')}`",
            f"- Glossary path: `{latest.get('glossary_path')}`",
        ])
    if include_entries > 0:
        lines.extend(["", "## Recent Entries", ""])
        for entry in entries[-include_entries:]:
            lines.append(
                f"- `{entry.get('run_id')}`: {entry.get('query')} "
                f"({entry.get('source_handle_count')} handles, {entry.get('glossary_packet_count')} glossary packets)"
            )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--manifest", default="")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--include-entries", type=int, default=5)
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest) if args.manifest else Path(args.out_dir) / DEFAULT_MANIFEST
    manifest = load_manifest(manifest_path)
    if args.format == "json":
        print(json.dumps({
            "ok": True,
            "manifest_path": str(manifest_path),
            "kind": manifest.get("kind"),
            "latest_run_id": manifest.get("latest_run_id"),
            "latest_context_path": manifest.get("latest_context_path"),
            "latest_glossary_path": manifest.get("latest_glossary_path"),
            "entry_count": manifest.get("entry_count"),
            "policy": manifest.get("policy"),
        }, indent=2, sort_keys=True))
    else:
        print(summary_markdown(manifest, include_entries=args.include_entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
