#!/usr/bin/env python3
"""scripts.pipeline_runtime.source_graph — the versioned SOURCE artifact graph + content-hash diff.

A source document is a recursive tree of addressable, content-hashed artifacts: a ``source_record`` root,
one ``source_field`` per structured field, and (for free-text fields) a ``source_block`` with one
``sentence`` child per sentence. Each artifact has a STABLE identity (so it can be tracked across versions)
and a CONTENT hash (so a change is detectable). ``diff_source_graph`` returns added / removed / changed /
unchanged artifact ids purely from content_hash — this is what scopes a reprocessing plan to exactly the
artifacts (and their downstream dependents) that actually changed.

Security metadata is stamped on every artifact and is SEPARATE from content_hash (see tenant_catalog).

CLI: imported by check_cfpb_source_graph_diff.py.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from scripts.ingest.decompose_structured import CFPB_LABELS, CFPB_NARRATIVE_FIELDS, sentence_chunks
from scripts.security.tenant_catalog import TenantPolicy, security_metadata


def content_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:24]


@dataclass
class SourceArtifact:
    artifact_id: str           # STABLE identity (source_id + type + locator) — survives content edits
    tenant_id: str
    source_id: str
    source_version: str
    artifact_type: str
    parent_artifact_id: str | None
    content_hash: str          # fingerprint of the CONTENT only (not security/metadata)
    locator_json: dict = field(default_factory=dict)
    metadata_json: dict = field(default_factory=dict)
    security_json: dict = field(default_factory=dict)
    superseded_by: str | None = None

    def to_row(self) -> dict:
        return {**self.__dict__}


def _aid(source_id: str, artifact_type: str, locator: str) -> str:
    return f"{source_id}:{artifact_type}:{locator}"


def build_cfpb_source_graph(record: Mapping[str, Any], policy: TenantPolicy, *,
                            source_version: str = "v1") -> dict[str, SourceArtifact]:
    """Build the source artifact graph for one CFPB record under a tenant policy.
    Returns {artifact_id: SourceArtifact}: a source_record root, source_field per structured field,
    and a source_block + sentence children per narrative field."""
    source_id = str(record.get("complaint_id") or record.get("id") or "cfpb-record")
    sec = lambda pii=False: security_metadata(policy, classification="public", pii=pii)
    graph: dict[str, SourceArtifact] = {}

    # the root hashes its STRUCTURE (which fields are present), NOT child values — so a value edit
    # changes only the affected leaf, never the container (minimal, content-addressed diff scope).
    present_fields = sorted(k for k in record if record.get(k) not in (None, ""))
    root_id = _aid(source_id, "source_record", "root")
    graph[root_id] = SourceArtifact(
        artifact_id=root_id, tenant_id=policy.tenant_id, source_id=source_id, source_version=source_version,
        artifact_type="source_record", parent_artifact_id=None,
        content_hash=content_hash({"fields": present_fields}),
        locator_json={"handle": f"ctx://cfpb/{source_id}"}, metadata_json={"labels": CFPB_LABELS},
        security_json=sec())

    narrative = set(CFPB_NARRATIVE_FIELDS)
    for fname in sorted(record):
        value = record.get(fname)
        if value is None or value == "":
            continue
        if fname in narrative:
            # free-text field → source_block, with one sentence child per sentence
            block_id = _aid(source_id, "source_block", fname)
            graph[block_id] = SourceArtifact(
                artifact_id=block_id, tenant_id=policy.tenant_id, source_id=source_id,
                source_version=source_version, artifact_type="source_block", parent_artifact_id=root_id,
                content_hash=content_hash(str(value)),
                locator_json={"handle": f"ctx://cfpb/{source_id}#{fname}", "field": fname},
                metadata_json={"field": fname}, security_json=sec(pii=True))
            for i, sent in enumerate(sentence_chunks(str(value))):
                sid = _aid(source_id, "sentence", f"{fname}#s{i}")
                graph[sid] = SourceArtifact(
                    artifact_id=sid, tenant_id=policy.tenant_id, source_id=source_id,
                    source_version=source_version, artifact_type="sentence", parent_artifact_id=block_id,
                    content_hash=content_hash(sent),
                    locator_json={"handle": f"ctx://cfpb/{source_id}#{fname}&s={i}", "field": fname, "sentence": i},
                    metadata_json={"text": sent}, security_json=sec(pii=True))
        else:
            fid = _aid(source_id, "source_field", fname)
            graph[fid] = SourceArtifact(
                artifact_id=fid, tenant_id=policy.tenant_id, source_id=source_id,
                source_version=source_version, artifact_type="source_field", parent_artifact_id=root_id,
                content_hash=content_hash(str(value)),
                locator_json={"handle": f"ctx://cfpb/{source_id}#{fname}", "field": fname},
                metadata_json={"field": fname, "value": value}, security_json=sec())
    return graph


def diff_source_graph(old: dict[str, SourceArtifact], new: dict[str, SourceArtifact]) -> dict[str, list[str]]:
    """Compare two source graphs by content_hash. Returns added/removed/changed/unchanged artifact ids."""
    old_ids, new_ids = set(old), set(new)
    added = sorted(new_ids - old_ids)
    removed = sorted(old_ids - new_ids)
    changed, unchanged = [], []
    for aid in sorted(old_ids & new_ids):
        if old[aid].content_hash != new[aid].content_hash:
            changed.append(aid)
        else:
            unchanged.append(aid)
    return {"added": added, "removed": removed, "changed": changed, "unchanged": unchanged}


def descendants(graph: dict[str, SourceArtifact], artifact_id: str) -> list[str]:
    """All artifacts whose parent chain reaches artifact_id (e.g. a block's sentences)."""
    out, frontier = [], [artifact_id]
    children = {}
    for a in graph.values():
        children.setdefault(a.parent_artifact_id, []).append(a.artifact_id)
    while frontier:
        cur = frontier.pop()
        for c in children.get(cur, []):
            out.append(c)
            frontier.append(c)
    return out
