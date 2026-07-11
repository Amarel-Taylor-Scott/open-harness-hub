#!/usr/bin/env python3
"""Deterministic + LLM candidate review pipeline for AI-first code maintenance.

The deterministic layer is the authority for evidence: line findings, AST findings, structural graph
context, and operation-level signals. The LLM layer is optional and can only enrich a packet with
candidate reasoning such as purpose, UX/product risk, and remediation hypotheses. It never serves truth.

Artifacts:
  .agent/hybrid-repo-review/review-packets.jsonl
  .agent/hybrid-repo-review/llm-prompts.jsonl
  .agent/hybrid-repo-review/llm-candidates.jsonl      (only with --call-llm)
  .agent/hybrid-repo-review/summary.md
  .agent/hybrid-repo-review/manifest.json

Stdlib-only by default. Optional OpenAI-compatible calls use scripts._llm_client and are owner-gated by
--call-llm plus local env vars. No key means the call is skipped and recorded, not faked.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from scripts import pyprefix
from scripts import repo_line_review_loop as line_review
REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
DEFAULT_OUT = (REPO / ".agent") / "hybrid-repo-review"
INTERROGATORY_SPEC = _resource("architecture") / "gev_adversarial_interrogatories.json"

MAGIC_NUMBER_ALLOW = {-1, 0, 1, 2, 10, 100, 1000}
MAGIC_STRING_ALLOW = {"", " ", "\n", "\t", "utf-8", "__main__", "GET", "POST", "PUT", "PATCH", "DELETE"}
SEVERITY_RANK = {"error": 5, "high": 4, "medium": 3, "low": 2, "info": 1}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO.resolve()))
    except ValueError:
        return str(path)


def _hash_json(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _jsonl_write(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            count += 1
    return count


def _jsonl_read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _read_json_if_present(path: Path | None) -> dict | None:
    if not path or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _source_segment(src: str, node: ast.AST) -> str:
    return " ".join((ast.get_source_segment(src, node) or "").strip().split())[:240]


def _callee_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = _callee_name(node.value)
        return f"{left}.{node.attr}" if left else node.attr
    if isinstance(node, ast.Call):
        return _callee_name(node.func)
    return ""


def _chain_length(node: ast.If) -> int:
    length = 1
    cur = node
    while len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
        length += 1
        cur = cur.orelse[0]
    return length


def _logic_findings(path: Path) -> list[dict]:
    """AST heuristics for fragile/rigid logic that deterministic graph review should surface."""
    if path.suffix != ".py":
        return []
    rel = _rel(path)
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        return [{
            "path": rel, "line": getattr(exc, "lineno", 0) or 0, "kind": "python_syntax",
            "severity": "error", "message": str(exc), "excerpt": "",
            "deterministic_rule": "ast.parse",
        }]

    rows: list[dict] = []
    string_counts: Counter[str] = Counter()
    assignment_stems: dict[str, list[tuple[str, int]]] = defaultdict(list)
    adjacent_calls: list[tuple[str, int, str]] = []

    def emit(node: ast.AST, kind: str, severity: str, message: str, **extra: object) -> None:
        rows.append({
            "path": rel,
            "line": getattr(node, "lineno", 0),
            "kind": kind,
            "severity": severity,
            "message": message,
            "excerpt": _source_segment(src, node),
            "deterministic_rule": extra.pop("rule", kind),
            **extra,
        })

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                if node.value not in MAGIC_NUMBER_ALLOW:
                    emit(node, "magic_literal:number", "medium",
                         f"Numeric literal `{node.value}` should be a named constant/config if load-bearing")
            elif isinstance(node.value, str):
                if node.value not in MAGIC_STRING_ALLOW:
                    string_counts[node.value] += 1
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    match = re.match(r"^(.+?)(?:_?)(\d+)$", target.id)
                    if match:
                        assignment_stems[match.group(1)].append((target.id, node.lineno))
        elif isinstance(node, ast.Call):
            callee = _callee_name(node.func)
            if callee:
                adjacent_calls.append((callee, node.lineno, _source_segment(src, node)))
            if any(kw.arg is None for kw in node.keywords):
                emit(node, "dynamic_kwargs_contract", "high",
                     "Call uses **kwargs; argument renames require coordinated contract review")
            if callee in {"getattr", "setattr", "hasattr", "eval", "exec", "__import__", "globals", "locals"}:
                emit(node, "dynamic_reference_contract", "high",
                     f"Dynamic reference `{callee}` blocks exact rename/data-flow confidence until modeled")
        elif isinstance(node, ast.If):
            length = _chain_length(node)
            if length >= 4:
                emit(node, "rigid_branch_chain", "medium",
                     f"If/elif chain has {length} branches; consider table-driven rules or dispatch map",
                     branch_count=length)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            bool_defaults = [
                arg.arg for arg, default in zip(node.args.args[-len(node.args.defaults):], node.args.defaults)
                if isinstance(default, ast.Constant) and isinstance(default.value, bool)
            ] if node.args.defaults else []
            if len(bool_defaults) >= 2:
                emit(node, "boolean_flag_control_surface", "medium",
                     f"Function has {len(bool_defaults)} boolean default flags; review for mode object/enum",
                     boolean_args=bool_defaults)
            mutable_defaults = [
                arg.arg for arg, default in zip(node.args.args[-len(node.args.defaults):], node.args.defaults)
                if isinstance(default, (ast.List, ast.Dict, ast.Set))
            ] if node.args.defaults else []
            if mutable_defaults:
                emit(node, "mutable_default_argument", "high",
                     "Mutable default argument can leak state across calls", args=mutable_defaults)
        elif isinstance(node, ast.ExceptHandler):
            if node.type is None or _callee_name(node.type) in {"Exception", "BaseException"}:
                emit(node, "broad_exception_handler", "medium",
                     "Broad exception handler can hide contract or graph failures")

    for value, count in string_counts.items():
        if count >= 3 and len(value) <= 80:
            rows.append({
                "path": rel, "line": 0, "kind": "repeated_magic_string", "severity": "medium",
                "message": f"String literal repeated {count} times; consider named constant/vocabulary",
                "excerpt": value, "deterministic_rule": "string_literal_frequency", "count": count,
            })

    for stem, names in assignment_stems.items():
        if len(names) >= 2:
            rows.append({
                "path": rel, "line": names[0][1], "kind": "scalar_series_candidate", "severity": "medium",
                "message": f"Scalar series {', '.join(n for n, _ in names[:6])} suggests list/dict/table data",
                "excerpt": ", ".join(n for n, _ in names[:8]),
                "deterministic_rule": "numbered_assignment_stem",
                "names": [n for n, _ in names],
            })

    for idx in range(0, max(0, len(adjacent_calls) - 2)):
        a, b, c = adjacent_calls[idx:idx + 3]
        if a[0] == b[0] == c[0] and c[1] - a[1] <= 12:
            rows.append({
                "path": rel, "line": a[1], "kind": "repeat_loop_candidate", "severity": "medium",
                "message": f"Repeated adjacent call `{a[0]}` suggests loop/table-driven dispatch if intentional",
                "excerpt": " | ".join(x[2] for x in (a, b, c)),
                "deterministic_rule": "adjacent_repeated_calls",
                "callee": a[0],
            })
            break
    return rows


def _file_graph_context(path: str, structural_graph: dict | None, op_graph: dict | None) -> dict:
    ctx: dict[str, object] = {}
    if structural_graph:
        nodes = [n for n in structural_graph.get("nodes", []) if path.replace("/", ".").replace(".py", "") in n.get("module", "")]
        node_ids = {n["id"] for n in nodes}
        edges = [e for e in structural_graph.get("edges", []) if e.get("src") in node_ids or e.get("dst") in node_ids]
        ctx["structural"] = {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "kinds": dict(Counter(n.get("kind", "") for n in nodes)),
            "edge_types": dict(Counter(e.get("type", "") for e in edges)),
        }
    if op_graph:
        nodes = [n for n in op_graph.get("nodes", []) if _rel(Path(n.get("file", ""))) == path or n.get("file", "").endswith(path)]
        edges = [e for e in op_graph.get("edges", []) if any(e.get(k, "").startswith(path + ":") for k in ("src", "dst"))]
        ctx["operation"] = {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "kinds": dict(Counter(n.get("kind", "") for n in nodes).most_common(20)),
            "edge_types": dict(Counter(e.get("type", "") for e in edges)),
        }
    return ctx


def _blast_radius_context(graph_context: dict) -> dict:
    """Conservative blast-radius hint for a review packet.

    This avoids the most dangerous failure mode: treating a finding as local when graph evidence says the
    surrounding file/module has many direct edges. It is a hint, not proof; promotion still requires tests.
    """
    structural = graph_context.get("structural", {})
    operation = graph_context.get("operation", {})
    direct_node_count = int(structural.get("node_count", 0) or 0) + int(operation.get("node_count", 0) or 0)
    direct_edge_count = int(structural.get("edge_count", 0) or 0) + int(operation.get("edge_count", 0) or 0)
    if direct_edge_count >= 100 or direct_node_count >= 200:
        level = "wide"
    elif direct_edge_count >= 20 or direct_node_count >= 50:
        level = "medium"
    else:
        level = "local_or_unknown"
    return {
        "level": level,
        "direct_node_count": direct_node_count,
        "direct_edge_count": direct_edge_count,
        "structural_edge_types": structural.get("edge_types", {}),
        "operation_edge_types": operation.get("edge_types", {}),
        "note": "Packet-level hint only; run targeted graph audit and proof gate before applying a fix.",
    }


def _verification_lanes(kind: str, severity: str) -> list[dict]:
    """Deterministic, hybrid, nondeterministic, and review lanes for a packet."""
    lanes = [
        {
            "lane": "deterministic",
            "role": "authority_for_evidence",
            "tools": ["repo_line_review_loop", "pyprefix", "opgraph", "registered_proofs"],
            "required_before_accept": True,
        },
        {
            "lane": "hybrid",
            "role": "cross_tool_packetization_and_reconciliation",
            "tools": ["hybrid_repo_review_pipeline"],
            "required_before_accept": True,
        },
        {
            "lane": "nondeterministic",
            "role": "candidate_explanation_remediation_and_purpose_enrichment",
            "tools": ["optional_openai_compatible_llm"],
            "required_before_accept": False,
        },
    ]
    if severity in {"high", "error"} or kind.startswith("secret_pattern") or "dynamic" in kind:
        lanes.append({
            "lane": "human_or_owner_review",
            "role": "risk_acceptance_for_security_or_dynamic_contract_surface",
            "tools": ["review_packet"],
            "required_before_accept": True,
        })
    return lanes


def _interrogatory_templates_for_kind(kind: str) -> list[str]:
    """Template ids that should be applied to a packet kind.

    Reads the repo contract when present and falls back to the core GEV interrogatories. This keeps packet
    generation deterministic while making the challenge set centrally extensible.
    """
    base = ["graphability_interrogatory", "blast_radius_interrogatory", "enrichment_interrogatory", "verification_interrogatory"]
    if not INTERROGATORY_SPEC.exists():
        return base
    try:
        spec = json.loads(INTERROGATORY_SPEC.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return base
    out = list(base)
    for template in spec.get("interrogatory_templates", []):
        tid = template.get("id")
        applies = set(template.get("applies_to", []))
        if tid and kind in applies and tid not in out:
            out.append(tid)
    return out


def _packet_prompt(packet: dict) -> str:
    evidence = json.dumps(packet["deterministic_evidence"], indent=2, sort_keys=True)
    graph = json.dumps(packet.get("graph_context", {}), indent=2, sort_keys=True)
    return (
        "Review this deterministic code-evidence packet. Return JSON only with keys: "
        "purpose, poor_logic_risk, naming_or_contract_issue, ui_ux_or_product_impact, "
        "recommended_fix, proof_to_run, confidence, caveats. "
        "Do not claim truth beyond the evidence; mark uncertainty explicitly.\n\n"
        f"Packet id: {packet['id']}\n"
        f"Path: {packet['path']}\n"
        f"Kind: {packet['kind']}\n"
        f"Severity: {packet['severity']}\n"
        f"Message: {packet['message']}\n\n"
        f"Deterministic evidence:\n{evidence}\n\nGraph context:\n{graph}\n"
    )


def _build_packet(finding: dict, structural_graph: dict | None, op_graph: dict | None) -> dict:
    path = finding["path"]
    evidence = {
        "path": path,
        "line": finding.get("line", 0),
        "excerpt": finding.get("excerpt", ""),
        "deterministic_rule": finding.get("deterministic_rule") or finding.get("kind"),
        "message": finding.get("message", ""),
    }
    packet_core = {
        "path": path,
        "line": finding.get("line", 0),
        "kind": finding.get("kind", ""),
        "message": finding.get("message", ""),
        "evidence": evidence,
    }
    packet_id = "hybrid-review-" + _hash_json(packet_core)[:16]
    graph_context = _file_graph_context(path, structural_graph, op_graph)
    packet = {
        "id": packet_id,
        "created_at": _now(),
        "serves_truth": False,
        "status": "deterministic_evidence_ready",
        "path": path,
        "line": finding.get("line", 0),
        "kind": finding.get("kind", ""),
        "severity": finding.get("severity", "info"),
        "message": finding.get("message", ""),
        "deterministic_evidence": evidence,
        "graph_context": graph_context,
        "blast_radius": _blast_radius_context(graph_context),
        "verification_lanes": _verification_lanes(finding.get("kind", ""), finding.get("severity", "info")),
        "interrogatory_template_ids": _interrogatory_templates_for_kind(finding.get("kind", "")),
        "context_policy": {
            "maximize_context": [
                "long meaningful source identifiers",
                "source excerpt",
                "file and line",
                "structural graph context",
                "operation/data-flow graph context when available",
                "candidate purpose/UX/product enrichment from LLM review",
            ],
            "limit_confusion": [
                "deterministic evidence comes first",
                "LLM output remains candidate-only",
                "blast-radius hint is explicit",
                "dynamic refs and external entrypoints stay unresolved until modeled",
                "proof gate promotes accepted fixes",
            ],
        },
        "contracts": [
            "LLM output is candidate-only and must not be promoted without deterministic proof",
            "Identifier recommendations must follow py_<kind>_<file>__<scope>__<name>",
            "External entrypoints require explicit shim/exemption",
            "Runtime truth requires scripts/run_proofs.py or a narrower registered proof",
        ],
    }
    packet["llm_prompt"] = _packet_prompt(packet)
    return packet


def _select_findings(findings: list[dict], max_packets: int) -> list[dict]:
    dedup: dict[tuple[str, int, str, str], dict] = {}
    for f in findings:
        key = (f.get("path", ""), int(f.get("line", 0) or 0), f.get("kind", ""), f.get("message", ""))
        if key not in dedup:
            dedup[key] = f
    return sorted(dedup.values(), key=lambda f: (-SEVERITY_RANK.get(f.get("severity", "info"), 0), f.get("path", ""), f.get("line", 0)))[:max_packets]


def build_review(target: Path, out_dir: Path, max_packets: int = 200,
                 include_opgraph: bool = False, call_llm: bool = False,
                 provider_name: str = "ollama", model: str = "") -> dict:
    records = line_review.discover_files(target)
    deterministic_findings: list[dict] = []
    for rec in records:
        file_findings, _ = line_review.review_file(rec, emit_line_records=False)
        deterministic_findings.extend(file_findings)
        deterministic_findings.extend(_logic_findings(rec.path))

    structural_graph = pyprefix.build_graph(target)
    op_graph = pyprefix.build_operation_graph(target) if include_opgraph else None
    selected = _select_findings(deterministic_findings, max_packets)
    packets = [_build_packet(f, structural_graph, op_graph) for f in selected]

    prompts = [{
        "id": p["id"],
        "serves_truth": False,
        "model_role": "candidate_reviewer",
        "system": (
            "You are a candidate code-review assistant. Deterministic evidence is authoritative; "
            "your output is candidate-only. Prefer concrete fixes, contracts, proof commands, and "
            "AI-first long qualified names over terse human names."
        ),
        "user": p["llm_prompt"],
    } for p in packets]

    out_dir.mkdir(parents=True, exist_ok=True)
    _jsonl_write(out_dir / "review-packets.jsonl", packets)
    _jsonl_write(out_dir / "llm-prompts.jsonl", prompts)

    llm_candidates: list[dict] = []
    if call_llm:
        llm_candidates = _call_llm(prompts, provider_name=provider_name, model=model)
        _jsonl_write(out_dir / "llm-candidates.jsonl", llm_candidates)

    summary = {
        "created_at": _now(),
        "serves_truth": False,
        "target": str(target),
        "files": len(records),
        "deterministic_findings": len(deterministic_findings),
        "packets": len(packets),
        "llm_candidates": len(llm_candidates),
        "structural_graph_counts": structural_graph.get("counts", {}),
        "operation_graph_counts": (op_graph or {}).get("counts", {}),
        "finding_kinds": dict(Counter(f["kind"] for f in deterministic_findings).most_common(25)),
        "severity": dict(Counter(f["severity"] for f in deterministic_findings)),
        "artifacts": {
            "review_packets": str(out_dir / "review-packets.jsonl"),
            "llm_prompts": str(out_dir / "llm-prompts.jsonl"),
            "llm_candidates": str(out_dir / "llm-candidates.jsonl"),
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    _write_summary(out_dir, summary)
    return summary


def build_review_from_artifacts(target: Path, out_dir: Path, findings_jsonl: Path,
                                structural_graph_json: Path | None = None,
                                opgraph_json: Path | None = None,
                                max_packets: int = 200, call_llm: bool = False,
                                provider_name: str = "ollama", model: str = "") -> dict:
    """Build review packets from existing deterministic artifacts.

    This is the robust full-repo path: the expensive deterministic line sweep and graph generation can run
    separately/resumably, then this command packages their findings for optional LLM review without
    recomputing the whole repo in one monolithic process.
    """
    deterministic_findings = _jsonl_read(findings_jsonl)
    structural_graph = _read_json_if_present(structural_graph_json)
    op_graph = _read_json_if_present(opgraph_json)
    selected = _select_findings(deterministic_findings, max_packets)
    packets = [_build_packet(f, structural_graph, op_graph) for f in selected]
    prompts = [{
        "id": p["id"],
        "serves_truth": False,
        "model_role": "candidate_reviewer",
        "system": (
            "You are a candidate code-review assistant. Deterministic evidence is authoritative; "
            "your output is candidate-only. Prefer concrete fixes, contracts, proof commands, and "
            "AI-first long qualified names over terse human names."
        ),
        "user": p["llm_prompt"],
    } for p in packets]
    out_dir.mkdir(parents=True, exist_ok=True)
    _jsonl_write(out_dir / "review-packets.jsonl", packets)
    _jsonl_write(out_dir / "llm-prompts.jsonl", prompts)
    llm_candidates: list[dict] = []
    if call_llm:
        llm_candidates = _call_llm(prompts, provider_name=provider_name, model=model)
        _jsonl_write(out_dir / "llm-candidates.jsonl", llm_candidates)

    summary = {
        "created_at": _now(),
        "serves_truth": False,
        "target": str(target),
        "source_mode": "existing_artifacts",
        "source_findings": str(findings_jsonl),
        "files": len({f.get("path") for f in deterministic_findings}),
        "deterministic_findings": len(deterministic_findings),
        "packets": len(packets),
        "llm_candidates": len(llm_candidates),
        "structural_graph_counts": (structural_graph or {}).get("counts", {}),
        "operation_graph_counts": (op_graph or {}).get("counts", {}),
        "finding_kinds": dict(Counter(f["kind"] for f in deterministic_findings).most_common(25)),
        "severity": dict(Counter(f["severity"] for f in deterministic_findings)),
        "artifacts": {
            "review_packets": str(out_dir / "review-packets.jsonl"),
            "llm_prompts": str(out_dir / "llm-prompts.jsonl"),
            "llm_candidates": str(out_dir / "llm-candidates.jsonl"),
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    _write_summary(out_dir, summary)
    return summary


def _call_llm(prompts: list[dict], provider_name: str, model: str) -> list[dict]:
    try:
        from scripts import _llm_client
    except Exception:
        import _llm_client  # type: ignore
    provider = _llm_client.resolve_provider(provider_name)
    chosen_model = model or (provider.get("models") or [""])[0]
    if not provider.get("base_url") or not provider.get("key") or not chosen_model:
        return [{
            "id": p["id"],
            "serves_truth": False,
            "status": "skipped_no_config",
            "provider": provider_name,
            "model": chosen_model,
            "candidate": {},
            "error": "Missing provider base_url/key/model; no LLM call made.",
        } for p in prompts]
    out: list[dict] = []
    for p in prompts:
        res = _llm_client.chat(chosen_model, p["system"], p["user"], provider, max_tokens=1600, timeout=120)
        candidate = {}
        if res.get("text"):
            try:
                candidate = json.loads(res["text"])
            except json.JSONDecodeError:
                candidate = {"raw_text": res["text"][:4000], "parse_error": "model output was not JSON"}
        out.append({
            "id": p["id"],
            "serves_truth": False,
            "status": "candidate_generated" if candidate else "provider_error",
            "provider": provider_name,
            "model": chosen_model,
            "candidate": candidate,
            "usage": res.get("usage", {}),
            "error": res.get("error"),
        })
    return out


def _write_summary(out_dir: Path, summary: dict) -> None:
    lines = [
        "# Hybrid Repo Review Pipeline",
        "",
        f"- Updated: `{summary['created_at']}`",
        f"- Target: `{summary['target']}`",
        f"- Files: `{summary['files']}`",
        f"- Deterministic findings: `{summary['deterministic_findings']}`",
        f"- Review packets: `{summary['packets']}`",
        f"- LLM candidates: `{summary['llm_candidates']}`",
        f"- Serves truth: `{summary['serves_truth']}`",
        "",
        "## Structural Graph",
        "",
        "```json",
        json.dumps(summary.get("structural_graph_counts", {}), indent=2, sort_keys=True),
        "```",
        "",
        "## Operation Graph",
        "",
        "```json",
        json.dumps(summary.get("operation_graph_counts", {}), indent=2, sort_keys=True),
        "```",
        "",
        "## Top Finding Kinds",
        "",
        "```json",
        json.dumps(summary.get("finding_kinds", {}), indent=2, sort_keys=True),
        "```",
        "",
        "Artifacts:",
        "",
        "- `review-packets.jsonl`",
        "- `llm-prompts.jsonl`",
        "- `llm-candidates.jsonl` when `--call-llm` is enabled",
        "- `manifest.json`",
    ]
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _self_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "scripts").mkdir()
        sample = root / "scripts" / "sample.py"
        sample.write_text(
            "def run(items, debug=False, force=False, cache=[]):\n"
            "    threshold = 37\n"
            "    first1 = 'a'\n"
            "    first2 = 'b'\n"
            "    if threshold == 1:\n"
            "        return getattr(items, 'x')\n"
            "    elif threshold == 2:\n"
            "        return len(items)\n"
            "    elif threshold == 3:\n"
            "        return len(items)\n"
            "    elif threshold == 4:\n"
            "        return len(items)\n"
            "    return threshold\n",
            encoding="utf-8",
        )
        out = root / ".agent" / "hybrid"
        old_repo = line_review.REPO
        old_pyprefix_repo = pyprefix.REPO_ROOT
        try:
            line_review.REPO = root
            pyprefix.REPO_ROOT = root
            # Scan the fake repo's code-root SUBDIR (root/"scripts"), never `root` itself: passing `root`
            # makes discover_files treat target==REPO and fan out to the REAL repo's code roots via
            # `_resource(...)` (which is not override-aware), scanning ~10k files in ~90s instead of the
            # one temp file — busting the proof budget. A subdir target resolves to [subdir], staying local.
            summary = build_review(root / "scripts", out, max_packets=20, include_opgraph=True)
        finally:
            line_review.REPO = old_repo
            pyprefix.REPO_ROOT = old_pyprefix_repo
        packets = [json.loads(x) for x in (out / "review-packets.jsonl").read_text(encoding="utf-8").splitlines()]
        kinds = {p["kind"] for p in packets}
        artifact_out = root / ".agent" / "artifact-hybrid"
        artifact_summary = build_review_from_artifacts(
            root,
            artifact_out,
            out / "review-packets.jsonl",
            structural_graph_json=None,
            opgraph_json=None,
            max_packets=5,
        )
        ok = (
            summary["files"] == 1
            and summary["packets"] >= 4
            and "magic_literal:number" in kinds
            and "dynamic_reference_contract" in kinds
            and "boolean_flag_control_surface" in kinds
            and "mutable_default_argument" in kinds
            and summary["operation_graph_counts"]["nodes"] > 0
            and artifact_summary["source_mode"] == "existing_artifacts"
            and artifact_summary["packets"] == 5
            and all(p["serves_truth"] is False for p in packets)
        )
        if not ok:
            print("FAIL - hybrid_repo_review_pipeline self-test")
            print(json.dumps({"summary": summary, "kinds": sorted(kinds)}, indent=2))
            return 1
    print("PASS - hybrid_repo_review_pipeline: deterministic findings -> graph-context packets -> LLM candidate prompts; serves_truth=false")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build deterministic + LLM-candidate repo review packets.")
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--max-packets", type=int, default=200)
    parser.add_argument("--include-opgraph", action="store_true", help="Include operation graph counts/context; slower on large targets.")
    parser.add_argument("--findings-jsonl", default="", help="Use an existing deterministic findings JSONL instead of rescanning.")
    parser.add_argument("--structural-graph-json", default="", help="Existing pyprefix structural graph JSON to attach as context.")
    parser.add_argument("--opgraph-json", default="", help="Existing pyprefix operation graph JSON to attach as context.")
    parser.add_argument("--call-llm", action="store_true", help="Owner-gated optional LLM enrichment via scripts._llm_client.")
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    target = Path(args.target)
    if not target.is_absolute():
        target = (_resource(target)).resolve()
    out = Path(args.out)
    if not out.is_absolute():
        out = (_resource(out)).resolve()
    if args.findings_jsonl:
        findings_jsonl = Path(args.findings_jsonl)
        if not findings_jsonl.is_absolute():
            findings_jsonl = (_resource(findings_jsonl)).resolve()
        structural_graph_json = Path(args.structural_graph_json) if args.structural_graph_json else None
        if structural_graph_json and not structural_graph_json.is_absolute():
            structural_graph_json = (_resource(structural_graph_json)).resolve()
        opgraph_json = Path(args.opgraph_json) if args.opgraph_json else None
        if opgraph_json and not opgraph_json.is_absolute():
            opgraph_json = (_resource(opgraph_json)).resolve()
        summary = build_review_from_artifacts(
            target,
            out,
            findings_jsonl,
            structural_graph_json=structural_graph_json,
            opgraph_json=opgraph_json,
            max_packets=args.max_packets,
            call_llm=args.call_llm,
            provider_name=args.provider,
            model=args.model,
        )
    else:
        summary = build_review(target, out, max_packets=args.max_packets, include_opgraph=args.include_opgraph,
                               call_llm=args.call_llm, provider_name=args.provider, model=args.model)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
