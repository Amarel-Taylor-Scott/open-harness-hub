"""Pre-LLM hygiene workers.

These are deterministic, dependency-light passes that improve corpus quality
before any model sees the content: normalization, PII detection, duplicate
fingerprints, and graph metrics.
"""
from __future__ import annotations

import hashlib
import html
import re
import unicodedata
from collections import defaultdict
from typing import Any

from scripts.context_workers.common import WORD_RE, chunk_text, compact, stable_hash
from scripts.context_workers.registry import TaskContext, TaskResult, registry

CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
WHITESPACE_RE = re.compile(r"[ \t]+")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
IPV4_RE = re.compile(r"\b(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}\b")
CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _source_chunks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    chunks = payload.get("chunks")
    if isinstance(chunks, list) and chunks:
        return chunks
    return chunk_text(str(payload.get("text") or ""))


def _luhn_ok(value: str) -> bool:
    digits = [int(ch) for ch in re.sub(r"\D", "", value)]
    if len(digits) < 13:
        return False
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


@registry.register(
    "context.text.normalize",
    lane="normalize",
    description="Normalize text deterministically before chunking: unicode, entities, whitespace, controls, and line endings.",
    emits=("normalized_text", "normalization_report"),
    capabilities=("text_normalization", "local_rules", "stable_ids"),
    task_types=("text.normalize", "document.normalize"),
    image="baltor-worker-cpu",
    output_contract="normalized_text.v1",
)
def text_normalize(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    original = str(payload.get("text") or "")
    text = original.replace("\r\n", "\n").replace("\r", "\n")
    text = html.unescape(text)
    text = unicodedata.normalize("NFC", text)
    control_count = len(CONTROL_RE.findall(text))
    text = CONTROL_RE.sub("", text)
    text = "\n".join(WHITESPACE_RE.sub(" ", line).rstrip() for line in text.split("\n"))
    text = re.sub(r"\n{4,}", "\n\n\n", text).strip()
    report = {
        "input_chars": len(original),
        "output_chars": len(text),
        "changed": text != original,
        "control_chars_removed": control_count,
        "input_sha256": _sha256(original),
        "output_sha256": _sha256(text),
    }
    return TaskResult.success({"normalized_text": text, "normalization_report": report})


@registry.register(
    "context.pii.detect",
    lane="verify",
    description="Detect common PII patterns before model calls or external routing.",
    emits=("pii_findings", "pii_summary"),
    capabilities=("pii_detection", "regex_extraction", "privacy_filter"),
    task_types=("pii.detect", "privacy.scan"),
    image="baltor-worker-audit",
    output_contract="pii_findings.v1",
)
def pii_detect(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    chunks = _source_chunks(payload)
    patterns = [
        ("email", EMAIL_RE, "medium"),
        ("phone", PHONE_RE, "medium"),
        ("ssn", SSN_RE, "high"),
        ("ipv4", IPV4_RE, "low"),
        ("credit_card", CREDIT_CARD_RE, "high"),
    ]
    findings = []
    for chunk in chunks:
        chunk_id = str(chunk.get("id") or stable_hash("chunk", str(chunk.get("text") or ""), 1))
        text = str(chunk.get("text") or "")
        for kind, pattern, risk in patterns:
            for match in pattern.finditer(text):
                value = match.group(0)
                if kind == "credit_card" and not _luhn_ok(value):
                    continue
                findings.append({
                    "id": stable_hash("pii", f"{kind}:{value}:{chunk_id}:{match.start()}", len(findings) + 1),
                    "type": kind,
                    "risk": risk,
                    "source_chunk": chunk_id,
                    "start": match.start(),
                    "end": match.end(),
                    "value_hash": _sha256(value)[:16],
                    "redacted": kind.upper(),
                    "evidence": text[max(0, match.start() - 40):match.end() + 40],
                })
    counts: dict[str, int] = defaultdict(int)
    for item in findings:
        counts[str(item["type"])] += 1
    return TaskResult.success({
        "pii_findings": findings,
        "pii_summary": {
            "finding_count": len(findings),
            "types": dict(sorted(counts.items())),
            "max_risk": "high" if any(item["risk"] == "high" for item in findings) else "medium" if findings else "none",
        },
    })


def _token_shingles(text: str, n: int = 5) -> list[str]:
    words = [w.lower() for w in WORD_RE.findall(text)]
    if len(words) < n:
        return [" ".join(words)] if words else []
    return [" ".join(words[i:i + n]) for i in range(0, len(words) - n + 1)]


def _simhash(tokens: list[str], bits: int = 64) -> str:
    vector = [0] * bits
    for token in tokens:
        digest = int(hashlib.sha1(token.encode("utf-8", errors="ignore")).hexdigest(), 16)
        for bit in range(bits):
            vector[bit] += 1 if digest & (1 << bit) else -1
    value = 0
    for bit, weight in enumerate(vector):
        if weight >= 0:
            value |= 1 << bit
    return f"{value:016x}"


@registry.register(
    "context.dedupe.fingerprint",
    lane="normalize",
    description="Generate exact and near-duplicate fingerprints for chunks and documents.",
    emits=("fingerprints", "dedupe_summary"),
    capabilities=("deduplication", "stable_ids", "text_fingerprinting"),
    task_types=("dedupe.fingerprint", "document.fingerprint"),
    image="baltor-worker-cpu",
    output_contract="fingerprints.v1",
)
def dedupe_fingerprint(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    chunks = _source_chunks(payload)
    fingerprints = []
    exact_seen: dict[str, str] = {}
    duplicate_pairs = []
    for index, chunk in enumerate(chunks, 1):
        text = compact(str(chunk.get("text") or ""))
        exact = _sha256(text)
        shingles = _token_shingles(text)
        simhash = _simhash(shingles or [text])
        item = {
            "id": stable_hash("fp", chunk.get("id") or text, index),
            "chunk_id": chunk.get("id") or stable_hash("chunk", text, index),
            "char_count": len(text),
            "word_count": len(WORD_RE.findall(text)),
            "sha256": exact,
            "simhash64": simhash,
            "shingle_count": len(shingles),
        }
        if exact in exact_seen:
            duplicate_pairs.append({"left": exact_seen[exact], "right": item["chunk_id"], "type": "exact_duplicate"})
        exact_seen[exact] = str(item["chunk_id"])
        fingerprints.append(item)
    return TaskResult.success({
        "fingerprints": fingerprints,
        "dedupe_summary": {
            "chunk_count": len(chunks),
            "exact_duplicate_pairs": duplicate_pairs,
            "exact_duplicate_count": len(duplicate_pairs),
        },
    })


@registry.register(
    "context.graph.metrics",
    lane="graph",
    description="Compute deterministic graph metrics: degree, connected components, isolates, and top bridge candidates.",
    emits=("graph_metrics",),
    capabilities=("graph_metrics", "lineage_edges", "local_rules"),
    task_types=("graph.metrics", "graph.rank"),
    image="baltor-worker-cpu",
    output_contract="graph_metrics.v1",
)
def graph_metrics(ctx: TaskContext, payload: dict[str, Any]) -> TaskResult:
    nodes = payload.get("nodes") or payload.get("document_nodes") or []
    edges = payload.get("edges") or payload.get("document_edges") or []
    node_ids = [str(node.get("id")) for node in nodes if node.get("id")]
    adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    directed_degree: dict[str, dict[str, int]] = {node_id: {"in": 0, "out": 0} for node_id in node_ids}
    for edge in edges:
        source = str(edge.get("from") or "")
        target = str(edge.get("to") or "")
        if not source or not target:
            continue
        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set()).add(source)
        directed_degree.setdefault(source, {"in": 0, "out": 0})["out"] += 1
        directed_degree.setdefault(target, {"in": 0, "out": 0})["in"] += 1

    seen: set[str] = set()
    components = []
    for node_id in sorted(adjacency):
        if node_id in seen:
            continue
        stack = [node_id]
        group = []
        seen.add(node_id)
        while stack:
            current = stack.pop()
            group.append(current)
            for neighbor in adjacency.get(current, set()):
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(sorted(group))

    metrics = []
    denom = max(1, len(adjacency) - 1)
    for node_id in sorted(adjacency):
        degree = len(adjacency[node_id])
        metrics.append({
            "node_id": node_id,
            "degree": degree,
            "in_degree": directed_degree.get(node_id, {}).get("in", 0),
            "out_degree": directed_degree.get(node_id, {}).get("out", 0),
            "degree_centrality": round(degree / denom, 6),
            "is_isolate": degree == 0,
        })
    top_nodes = sorted(metrics, key=lambda item: (-item["degree"], item["node_id"]))[:20]
    return TaskResult.success({
        "graph_metrics": {
            "node_count": len(adjacency),
            "edge_count": len(edges),
            "component_count": len(components),
            "component_sizes": sorted([len(group) for group in components], reverse=True),
            "isolate_count": sum(1 for item in metrics if item["is_isolate"]),
            "node_metrics": metrics,
            "top_degree_nodes": top_nodes,
        }
    })
