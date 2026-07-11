#!/usr/bin/env python3
"""Append-only Gemma lane for longer multistep primitive-group candidates.

This lane is deliberately separate from the deterministic primitive loops and
from the registry promotion path. It reads fully-defined primitive candidates as
seeds, asks Open WebUI Gemma for one larger reusable primitive group per seed,
validates candidate boundaries, and writes a timestamped run directory.

It is safe to run while another agent is active in this checkout:

* no existing primitive registry/catalog files are overwritten;
* every run writes under a unique ``runs/<run_id>/`` directory;
* a local exclusive lock prevents two copies of this lane from writing the same
  run at the same time;
* outputs are candidate-only and ``serves_truth=false``.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

_SBC = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "scripts" / "_repo_paths.py").exists()),
    Path(__file__).resolve().parents[1],
)
if str(_SBC) not in sys.path:
    sys.path.insert(0, str(_SBC))

from scripts._config import OPENWEBUI_DEFAULT_MODEL  # noqa: E402
from scripts._repo_paths import install as _install  # noqa: E402

_install()

from scripts._repo_paths import resource as _resource  # noqa: E402
from scripts.openwebui_cdp_client import cdp_chat  # noqa: E402


RECORD_TYPE = "gemma_long_multistep_primitive_lane"
DEFAULT_OUT_ROOT = _resource("data") / "dev-intel" / "gemma_primitive_lane"
DEFAULT_DECON_ROOT = _resource("data") / "dev-intel" / "primitive_deconstruction_plane_pipeline"
LOCK_NAME = "gemma_long_multistep_lane.lock"
SYSTEM_PROMPT = (
    "You write compact, high-leverage primitive-group candidate JSON only. "
    "Return exactly one JSON object and no markdown. Never claim truth. "
    "Every object must keep candidate=true and serves_truth=false."
)
REQUIRED_FIELDS = (
    "primitive_id",
    "kind",
    "title",
    "purpose",
    "visible_input_edge",
    "visible_output_edge",
    "input_edge_description",
    "output_edge_description",
    "contract",
    "group_contract",
    "hidden_member_edges",
    "remix_axes",
    "examples",
    "proof_requirements",
    "benchmark_hooks",
    "promotion_blockers",
    "reuse_profile",
    "candidate",
    "serves_truth",
)


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def _sha(value: Any, *, n: int = 16) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:n]


def _slug(value: str, *, limit: int = 72) -> str:
    chars: list[str] = []
    for char in str(value).lower():
        if char.isalnum():
            chars.append(char)
        elif chars and chars[-1] != "-":
            chars.append("-")
    return "".join(chars).strip("-")[:limit] or "item"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: expected JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise AssertionError(f"{path}:{line_no}: expected JSON object")
        rows.append(value)
    return rows


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_stable_json(row) + "\n")
            count += 1
    return count


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_stable_json(row) + "\n")
        handle.flush()


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class LaneLock:
    def __init__(self, path: Path):
        self.path = path
        self.fd: int | None = None

    def __enter__(self) -> "LaneLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(2):
            try:
                self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
                break
            except FileExistsError as exc:
                owner: dict[str, Any] = {}
                try:
                    owner = json.loads(self.path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    owner = {}
                pid = int(owner.get("pid") or 0)
                recoverable = pid == os.getpid() or not _pid_is_alive(pid)
                if recoverable and attempt == 0:
                    try:
                        self.path.unlink()
                    except FileNotFoundError:
                        pass
                    continue
                raise AssertionError(f"Gemma lane lock is already held: {self.path}") from exc
        if self.fd is None:
            raise AssertionError(f"Gemma lane lock was not acquired: {self.path}")
        os.write(self.fd, _stable_json({"pid": os.getpid(), "created_at": _utc()}).encode("utf-8"))
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def latest_deconstruction_run_dir(root: Path = DEFAULT_DECON_ROOT) -> Path:
    status = _read_json(root / "latest_status.json")
    run_dir = ((status.get("outputs") or {}).get("run_dir") if isinstance(status.get("outputs"), dict) else "") or ""
    if run_dir:
        return Path(str(run_dir))
    runs = sorted((root / "runs").glob("primitive-deconstruction-plane-*"))
    if not runs:
        raise AssertionError("no primitive deconstruction runs found")
    return runs[-1]


def _base_seed_id(row: dict[str, Any]) -> str:
    primitive_id = str(row.get("primitive_id") or row.get("payload_id") or "")
    if "/overlay/" in primitive_id:
        primitive_id = primitive_id.split("/overlay/", 1)[0]
    return primitive_id or f"seed/{_sha(row)}"


def _seed_key(row: dict[str, Any]) -> str:
    return _base_seed_id(row)


def load_seed_rows(source_run_dir: Path, *, limit: int, offset: int, skip_processed: bool, out_root: Path) -> list[dict[str, Any]]:
    candidates_path = source_run_dir / "fully_defined_primitive_candidates.jsonl"
    rows = _read_jsonl(candidates_path)
    seen: set[str] = set()
    if skip_processed:
        seen = processed_seed_ids(out_root)
    selected: list[dict[str, Any]] = []
    base_seen: set[str] = set()
    for row in rows:
        key = _seed_key(row)
        if key in seen or key in base_seen:
            continue
        base_seen.add(key)
        selected.append(row)
    selected = selected[max(0, offset):]
    return selected[:limit] if limit > 0 else selected


def processed_seed_ids(out_root: Path) -> set[str]:
    seen: set[str] = set()
    for path in sorted((out_root / "runs").glob("*/candidate_groups.jsonl")):
        for row in _read_jsonl(path):
            seed_id = str(row.get("seed_id") or "")
            if seed_id:
                seen.add(seed_id)
    for path in sorted((out_root / "runs").glob("*/rejected.jsonl")):
        for row in _read_jsonl(path):
            seed_id = str(row.get("seed_id") or "")
            if seed_id:
                seen.add(seed_id)
    return seen


def _compact_seed(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "primitive_id": row.get("primitive_id"),
        "title": row.get("title"),
        "source_kind": row.get("source_kind"),
        "component_family": row.get("component_family"),
        "input_edge": row.get("input_edge"),
        "output_edge": row.get("output_edge"),
        "input_edge_description": row.get("input_edge_description"),
        "output_edge_description": row.get("output_edge_description"),
        "hidden_member_edges": row.get("hidden_member_edges") or row.get("group_contract", {}).get("hidden_member_edges"),
        "examples": row.get("examples") or row.get("example_refs_sample"),
        "proof_requirements": row.get("proof_requirements"),
        "benchmark_hooks": row.get("benchmark_hooks"),
        "remix_axes": row.get("remix_axes") or row.get("mutation_affordances") or row.get("variation_overlay"),
        "promotion_blockers": row.get("promotion_blockers"),
    }


def build_prompt(seed: dict[str, Any], *, min_hidden_edges: int, min_examples: int) -> str:
    payload = {
        "task": "expand_seed_into_long_multistep_primitive_group",
        "seed": _compact_seed(seed),
        "hard_requirements": {
            "return_shape": "exactly_one_json_object",
            "kind": "primitive_group",
            "candidate": True,
            "serves_truth": False,
            "min_hidden_member_edges": min_hidden_edges,
            "min_examples": min_examples,
            "contracts_must_be_specific": True,
            "visible_edges_must_hide_many_steps": True,
            "include_benchmark_hooks": True,
            "include_remix_axes": True,
            "include_promotion_blockers": True,
            "include_estimated_saved_output_tokens": True,
        },
        "required_fields": list(REQUIRED_FIELDS),
        "field_guidance": {
            "primitive_id": "stable candidate id derived from the seed, prefixed prim:gemma:long:",
            "visible_input_edge": "one explicit external input edge, not a prose sentence",
            "visible_output_edge": "one explicit external output edge, not a prose sentence",
            "hidden_member_edges": "array of internal member edge strings such as A -> B; at least the requested minimum",
            "contract": "object with summary,input,output,errors,side_effects,preconditions,postconditions",
            "group_contract": "object with visible_input, visible_output, hidden_member_edges, composition_notes",
            "reuse_profile": "object with reuse_class, estimated_saved_output_tokens, reusable_build_tasks, implementation_surfaces, compile_strategy, linking_instructions",
            "examples": "array of objects with language, scenario, inputs, expected_output, acceptance_check",
            "benchmark_hooks": "array of objects with metric, baseline_prompt_shape, primitive_prompt_shape, measurement",
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)


def extract_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise AssertionError("assistant content did not contain a JSON object")
    value = json.loads(text[start:end + 1])
    if not isinstance(value, dict):
        raise AssertionError("assistant JSON was not an object")
    return value


def validate_candidate(row: dict[str, Any], *, min_hidden_edges: int, min_examples: int) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in row:
            errors.append(f"missing:{field}")
    if row.get("candidate") is not True:
        errors.append("candidate_not_true")
    if row.get("serves_truth") is not False:
        errors.append("serves_truth_not_false")
    if str(row.get("kind") or "") != "primitive_group":
        errors.append("kind_not_primitive_group")
    hidden = row.get("hidden_member_edges")
    if not isinstance(hidden, list) or len(hidden) < min_hidden_edges:
        errors.append("hidden_member_edges_too_small")
    examples = row.get("examples")
    if not isinstance(examples, list) or len(examples) < min_examples:
        errors.append("examples_too_small")
    if not isinstance(row.get("contract"), dict):
        errors.append("contract_not_object")
    group_contract = row.get("group_contract")
    if not isinstance(group_contract, dict):
        errors.append("group_contract_not_object")
    else:
        if group_contract.get("visible_input") != row.get("visible_input_edge"):
            errors.append("group_contract_visible_input_mismatch")
        if group_contract.get("visible_output") != row.get("visible_output_edge"):
            errors.append("group_contract_visible_output_mismatch")
    reuse = row.get("reuse_profile")
    if not isinstance(reuse, dict):
        errors.append("reuse_profile_not_object")
    elif int(reuse.get("estimated_saved_output_tokens") or 0) <= 0:
        errors.append("estimated_saved_output_tokens_missing")
    return errors


def normalize_candidate(row: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Apply deterministic shape repairs that do not invent substantive content."""
    normalized = dict(row)
    notes: list[str] = []
    group_contract = normalized.get("group_contract")
    if isinstance(group_contract, dict):
        group_contract = dict(group_contract)
        if group_contract.get("visible_input") != normalized.get("visible_input_edge"):
            group_contract["visible_input"] = normalized.get("visible_input_edge")
            notes.append("group_contract.visible_input_aligned_to_visible_input_edge")
        if group_contract.get("visible_output") != normalized.get("visible_output_edge"):
            group_contract["visible_output"] = normalized.get("visible_output_edge")
            notes.append("group_contract.visible_output_aligned_to_visible_output_edge")
        hidden = normalized.get("hidden_member_edges")
        if isinstance(hidden, list) and group_contract.get("hidden_member_edges") != hidden:
            group_contract["hidden_member_edges"] = hidden
            notes.append("group_contract.hidden_member_edges_aligned_to_top_level")
        normalized["group_contract"] = group_contract
    return normalized, notes


def enrich_one(
    seed: dict[str, Any],
    *,
    model: str,
    cdp_url: str,
    max_tokens: int,
    timeout: int,
    min_hidden_edges: int,
    min_examples: int,
) -> dict[str, Any]:
    prompt = build_prompt(seed, min_hidden_edges=min_hidden_edges, min_examples=min_examples)
    started = time.time()
    result = cdp_chat(
        prompt,
        system=SYSTEM_PROMPT,
        model=model,
        cdp_url=cdp_url or None,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    elapsed = round(time.time() - started, 3)
    content = str(result.get("assistant_content") or "")
    parsed = extract_json_object(content)
    parsed, normalization_notes = normalize_candidate(parsed)
    errors = validate_candidate(parsed, min_hidden_edges=min_hidden_edges, min_examples=min_examples)
    seed_id = _seed_key(seed)
    return {
        "record_type": "gemma_long_multistep_primitive_generation",
        "generation_id": f"glmp:{_sha({'seed': seed_id, 'content': content, 'model': model}, n=20)}",
        "seed_id": seed_id,
        "seed_title": seed.get("title"),
        "provider": "openwebui",
        "model": result.get("model") or model,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "assistant_content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "assistant_content": content,
        "parsed_candidate": parsed,
        "normalization_notes": normalization_notes,
        "validation_errors": errors,
        "status": "accepted_candidate" if not errors else "rejected_candidate",
        "usage": result.get("usage") or {},
        "finish_reason": result.get("finish_reason"),
        "http_status": result.get("http_status"),
        "duration_seconds": elapsed,
        "candidate": True,
        "serves_truth": False,
    }


def build_feed_rows(run_id: str, accepted: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for receipt in accepted:
        payload = receipt["parsed_candidate"]
        payload_id = payload.get("primitive_id") or receipt["generation_id"]
        rows.append(
            {
                "record_type": "primitive_database_feed_row",
                "feed_id": f"feed/gemma-long/{_slug(str(payload_id))}-{_sha({'run': run_id, 'payload': payload_id}, n=10)}",
                "run_id": run_id,
                "target_registry": "primitive_candidates",
                "operation": "stage_candidate",
                "payload_id": payload_id,
                "payload_digest": "sha256:" + hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest(),
                "payload": payload,
                "source_generation_id": receipt["generation_id"],
                "promotion_state": "staged_requires_source_license_proof_benchmark_and_human_review",
                "candidate": True,
                "serves_truth": False,
            }
        )
    return rows


def summarize(run_id: str, run_dir: Path, seed_rows: list[dict[str, Any]], receipts: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [row for row in receipts if row.get("status") == "accepted_candidate"]
    rejected = [row for row in receipts if row.get("status") != "accepted_candidate"]
    usage = {
        "prompt_tokens": sum(int((row.get("usage") or {}).get("prompt_tokens") or 0) for row in receipts),
        "completion_tokens": sum(int((row.get("usage") or {}).get("completion_tokens") or 0) for row in receipts),
        "total_tokens": sum(int((row.get("usage") or {}).get("total_tokens") or 0) for row in receipts),
    }
    hidden_edges = [
        len((row.get("parsed_candidate") or {}).get("hidden_member_edges") or [])
        for row in accepted
    ]
    examples = [
        len((row.get("parsed_candidate") or {}).get("examples") or [])
        for row in accepted
    ]
    estimated_saved = sum(
        int(((row.get("parsed_candidate") or {}).get("reuse_profile") or {}).get("estimated_saved_output_tokens") or 0)
        for row in accepted
    )
    return {
        "record_type": RECORD_TYPE,
        "run_id": run_id,
        "created_at": _utc(),
        "run_dir": str(run_dir),
        "seed_rows": len(seed_rows),
        "accepted_candidates": len(accepted),
        "rejected_candidates": len(rejected),
        "usage": usage,
        "avg_hidden_member_edges": round(sum(hidden_edges) / max(len(hidden_edges), 1), 3),
        "avg_examples": round(sum(examples) / max(len(examples), 1), 3),
        "estimated_saved_output_tokens": estimated_saved,
        "outputs": {
            "seed_rows": "seed_rows.jsonl",
            "candidate_groups": "candidate_groups.jsonl",
            "generation_receipts": "generation_receipts.jsonl",
            "rejected": "rejected.jsonl",
            "primitive_database_feed": "primitive_database_feed.jsonl",
            "benchmark_receipt": "benchmark_receipt.json",
        },
        "governance": {
            "append_only_run_dir": True,
            "registry_promotion": False,
            "candidate": True,
            "serves_truth": False,
        },
        "candidate": True,
        "serves_truth": False,
    }


def run_once(
    *,
    out_root: Path,
    source_run_dir: Path,
    model: str,
    cdp_url: str,
    limit: int,
    offset: int,
    max_tokens: int,
    timeout: int,
    sleep_between_calls: float,
    min_hidden_edges: int,
    min_examples: int,
    dry_run: bool,
    skip_processed: bool,
) -> dict[str, Any]:
    run_id = f"gemma-long-multistep-{_stamp()}-{os.getpid()}"
    run_dir = out_root / "runs" / run_id
    with LaneLock(out_root / LOCK_NAME):
        seeds = load_seed_rows(source_run_dir, limit=limit, offset=offset, skip_processed=skip_processed, out_root=out_root)
        if not seeds:
            out_root.mkdir(parents=True, exist_ok=True)
            summary = {
                "record_type": RECORD_TYPE,
                "run_id": run_id,
                "created_at": _utc(),
                "run_dir": "",
                "source_run_dir": str(source_run_dir),
                "seed_rows": 0,
                "accepted_candidates": 0,
                "rejected_candidates": 0,
                "primitive_database_feed_rows": 0,
                "status": "no_unprocessed_seeds",
                "dry_run": dry_run,
                "candidate": True,
                "serves_truth": False,
            }
            _append_jsonl(out_root / "long_multistep_loop_ledger.jsonl", summary)
            return summary
        run_dir.mkdir(parents=True, exist_ok=False)
        _write_jsonl(run_dir / "seed_rows.jsonl", seeds)
        receipts: list[dict[str, Any]] = []
        if dry_run:
            for seed in seeds:
                receipts.append(
                    {
                        "record_type": "gemma_long_multistep_primitive_generation",
                        "generation_id": f"glmp:planned:{_sha(_seed_key(seed), n=16)}",
                        "seed_id": _seed_key(seed),
                        "seed_title": seed.get("title"),
                        "status": "planned",
                        "usage": {},
                        "validation_errors": [],
                        "candidate": True,
                        "serves_truth": False,
                    }
                )
        else:
            for index, seed in enumerate(seeds, start=1):
                try:
                    receipt = enrich_one(
                        seed,
                        model=model,
                        cdp_url=cdp_url,
                        max_tokens=max_tokens,
                        timeout=timeout,
                        min_hidden_edges=min_hidden_edges,
                        min_examples=min_examples,
                    )
                except Exception as exc:  # noqa: BLE001
                    receipt = {
                        "record_type": "gemma_long_multistep_primitive_generation",
                        "generation_id": f"glmp:error:{_sha({'seed': _seed_key(seed), 'error': str(exc)}, n=16)}",
                        "seed_id": _seed_key(seed),
                        "seed_title": seed.get("title"),
                        "status": "error",
                        "error": f"{type(exc).__name__}: {exc}",
                        "usage": {},
                        "validation_errors": ["call_or_parse_error"],
                        "candidate": True,
                        "serves_truth": False,
                    }
                receipts.append(receipt)
                _append_jsonl(run_dir / "generation_receipts.jsonl", receipt)
                if index < len(seeds) and sleep_between_calls > 0:
                    time.sleep(sleep_between_calls)
        accepted = [row for row in receipts if row.get("status") == "accepted_candidate"]
        rejected = [row for row in receipts if row.get("status") != "accepted_candidate"]
        _write_jsonl(run_dir / "generation_receipts.jsonl", receipts)
        _write_jsonl(
            run_dir / "candidate_groups.jsonl",
            [
                {
                    **row["parsed_candidate"],
                    "seed_id": row["seed_id"],
                    "generation_id": row["generation_id"],
                    "record_type": "gemma_long_multistep_primitive_group_candidate",
                    "candidate": True,
                    "serves_truth": False,
                }
                for row in accepted
            ],
        )
        _write_jsonl(run_dir / "rejected.jsonl", rejected)
        feed = build_feed_rows(run_id, accepted)
        _write_jsonl(run_dir / "primitive_database_feed.jsonl", feed)
        summary = summarize(run_id, run_dir, seeds, receipts)
        summary["source_run_dir"] = str(source_run_dir)
        summary["primitive_database_feed_rows"] = len(feed)
        summary["dry_run"] = dry_run
        _write_json(run_dir / "benchmark_receipt.json", summary)
        _append_jsonl(out_root / "long_multistep_loop_ledger.jsonl", summary)
        return summary


def _self_test() -> int:
    fixture = {
        "primitive_id": "primitive/website/analytics-event",
        "title": "Website Analytics Event",
        "source_kind": "website",
        "component_family": "analytics_event",
        "input_edge": "SourceBackedComponent+source_ref+payload",
        "output_edge": "PrimitiveCandidatePayload+candidate+proof_obligation",
        "hidden_member_edges": ["SourceRef -> ComponentBreakdown", "ComponentBreakdown -> PrimitiveContract"],
        "candidate": True,
        "serves_truth": False,
    }
    candidate = {
        "primitive_id": "prim:gemma:long:website-analytics-event",
        "kind": "primitive_group",
        "title": "Website Analytics Event Primitive Group",
        "purpose": "Compile a website analytics source component into an instrumented primitive candidate bundle.",
        "visible_input_edge": "WebsiteSourceSnapshot+AnalyticsPolicy+PrivacyBoundary",
        "visible_output_edge": "AnalyticsPrimitiveBundle+BenchmarkReceipt+PromotionReviewPacket",
        "input_edge_description": "input",
        "output_edge_description": "output",
        "contract": {"summary": "s", "input": "i", "output": "o", "errors": []},
        "group_contract": {
            "visible_input": "WebsiteSourceSnapshot",
            "visible_output": "AnalyticsPrimitiveBundle",
            "hidden_member_edges": ["A -> B", "B -> C", "C -> D", "D -> E", "E -> F"],
            "composition_notes": "wire sequentially",
        },
        "hidden_member_edges": ["A -> B", "B -> C", "C -> D", "D -> E", "E -> F"],
        "remix_axes": ["runtime", "privacy", "framework"],
        "examples": [
            {"language": "python", "scenario": "cli", "inputs": {}, "expected_output": {}, "acceptance_check": "ok"},
            {"language": "typescript", "scenario": "web", "inputs": {}, "expected_output": {}, "acceptance_check": "ok"},
            {"language": "sql", "scenario": "warehouse", "inputs": {}, "expected_output": {}, "acceptance_check": "ok"},
        ],
        "proof_requirements": ["schema test", "privacy test", "benchmark"],
        "benchmark_hooks": [{"metric": "tokens", "baseline_prompt_shape": "raw", "primitive_prompt_shape": "edge", "measurement": "delta"}],
        "promotion_blockers": ["license review"],
        "reuse_profile": {"estimated_saved_output_tokens": 2400},
        "candidate": True,
        "serves_truth": False,
    }
    with tempfile.TemporaryDirectory(prefix="gemma-long-lane-test-") as temp:
        root = Path(temp)
        source_run = root / "source"
        _write_jsonl(source_run / "fully_defined_primitive_candidates.jsonl", [fixture])
        extracted = extract_json_object("prefix " + json.dumps(candidate) + " suffix")
        extracted, notes = normalize_candidate(extracted)
        assert notes == [
            "group_contract.visible_input_aligned_to_visible_input_edge",
            "group_contract.visible_output_aligned_to_visible_output_edge",
        ]
        assert validate_candidate(extracted, min_hidden_edges=5, min_examples=3) == []
        summary = run_once(
            out_root=root / "out",
            source_run_dir=source_run,
            model=OPENWEBUI_DEFAULT_MODEL,
            cdp_url="",
            limit=1,
            offset=0,
            max_tokens=64,
            timeout=5,
            sleep_between_calls=0,
            min_hidden_edges=5,
            min_examples=3,
            dry_run=True,
            skip_processed=True,
        )
        assert summary["seed_rows"] == 1
        assert summary["dry_run"] is True
        assert summary["candidate"] is True and summary["serves_truth"] is False
        assert (Path(summary["run_dir"]) / "seed_rows.jsonl").exists()
    print("PASS - Gemma long multistep lane is append-only, lock-protected, and candidate-only.")
    return 0


def _watch(args: argparse.Namespace) -> int:
    ticks = 0
    while True:
        ticks += 1
        source_run_dir = Path(args.source_run_dir) if args.source_run_dir else latest_deconstruction_run_dir()
        summary = run_once(
            out_root=Path(args.out_root),
            source_run_dir=source_run_dir,
            model=args.model,
            cdp_url=args.cdp_url,
            limit=args.limit,
            offset=args.offset,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
            sleep_between_calls=args.sleep_between_calls,
            min_hidden_edges=args.min_hidden_edges,
            min_examples=args.min_examples,
            dry_run=args.dry_run,
            skip_processed=not args.no_skip_processed,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        if args.max_ticks and ticks >= args.max_ticks:
            return 0
        time.sleep(args.interval)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--max-ticks", type=int, default=0)
    parser.add_argument("--interval", type=int, default=1800)
    parser.add_argument("--source-run-dir", default="")
    parser.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))
    parser.add_argument("--model", default=OPENWEBUI_DEFAULT_MODEL)
    parser.add_argument("--cdp-url", default="")
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--max-tokens", type=int, default=2200)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--sleep-between-calls", type=float, default=55.0)
    parser.add_argument("--min-hidden-edges", type=int, default=7)
    parser.add_argument("--min-examples", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-skip-processed", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.watch:
        return _watch(args)
    if not args.once:
        parser.error("pass --once, --watch, or --self-test")
    source_run_dir = Path(args.source_run_dir) if args.source_run_dir else latest_deconstruction_run_dir()
    summary = run_once(
        out_root=Path(args.out_root),
        source_run_dir=source_run_dir,
        model=args.model,
        cdp_url=args.cdp_url,
        limit=args.limit,
        offset=args.offset,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
        sleep_between_calls=args.sleep_between_calls,
        min_hidden_edges=args.min_hidden_edges,
        min_examples=args.min_examples,
        dry_run=args.dry_run,
        skip_processed=not args.no_skip_processed,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
