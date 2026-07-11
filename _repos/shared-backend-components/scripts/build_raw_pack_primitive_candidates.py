#!/usr/bin/env python3
"""scripts.build_raw_pack_primitive_candidates — deterministic table→candidate converter (zero model tokens).

The owner's ``generated_primitive_packs/*_pack.md`` files are dimension-driven Markdown tables that already carry
title, input_edge, output_edge, effects, proof_requirements, and source_ref_families per row — they are
PRE-primitive skeletons. This builder maps each table row into the machine-enforced verifier candidate shape
(``_repos/shared-backend-components/scripts/verify_primitive_candidates.py``) with NO model call: it parses each pack's header to locate columns,
synthesizes the required contract/blackbox/mutators/promotion_blockers, resolves source_ref_families to real public
official-doc URLs, and stages rows under ``batch_runs/<label>/<pack_id>/extracted/extracted_candidates.jsonl`` ready
for the standard verify + registry-bridge pipeline. Deterministic + offline; every row candidate=true /
serves_truth=false. CLI: --self-test | --write [--date YYYY-MM-DD] [--label LABEL] [--packs-dir DIR].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PACKS_DIR = _resource("generated_primitive_packs")
BATCH_RUNS = _resource("data") / "dev-intel" / "primitive_factory" / "batch_runs"

# every source_ref_family the packs use → a real PUBLIC https official-doc URL (verifier rejects example/localhost).
FAMILY_URL: dict[str, dict[str, str]] = {
    "OpenAPI_spec": {"label": "openapi_spec", "url": "https://spec.openapis.org/oas/latest.html"},
    "AsyncAPI_spec": {"label": "asyncapi_spec", "url": "https://www.asyncapi.com/docs/reference/specification/latest"},
    "official_api_reference": {"label": "openapi_spec", "url": "https://spec.openapis.org/oas/latest.html"},
    "official_docs": {"label": "mdn_web_docs", "url": "https://developer.mozilla.org/en-US/docs/Web"},
    "government_data_portal": {"label": "data_gov", "url": "https://www.data.gov/"},
    "robots_and_terms": {"label": "robots_rfc9309", "url": "https://www.rfc-editor.org/rfc/rfc9309.html"},
    "runtime_trace": {"label": "opentelemetry", "url": "https://opentelemetry.io/docs/"},
    "cloud_provider_docs": {"label": "aws_docs", "url": "https://docs.aws.amazon.com/"},
    "policy_engine_docs": {"label": "open_policy_agent", "url": "https://www.openpolicyagent.org/docs/latest/"},
    "policy_version_pin": {"label": "open_policy_agent", "url": "https://www.openpolicyagent.org/docs/latest/"},
    "benchmark_fixture": {"label": "kaggle_docs", "url": "https://www.kaggle.com/docs"},
    "Kaggle_competition": {"label": "kaggle_competitions", "url": "https://www.kaggle.com/docs/competitions"},
    "Kaggle_benchmark_hub_listing": {"label": "kaggle_benchmarks", "url": "https://www.kaggle.com/benchmarks"},
    "OpenML_task": {"label": "openml_docs", "url": "https://docs.openml.org/"},
    "Terraform_Registry": {"label": "terraform_registry", "url": "https://registry.terraform.io/"},
    "Kubernetes_docs": {"label": "kubernetes_docs", "url": "https://kubernetes.io/docs/"},
    "cloud_marketplace_listing": {"label": "aws_marketplace", "url": "https://docs.aws.amazon.com/marketplace/"},
    "listing_source_ref": {"label": "aws_marketplace", "url": "https://docs.aws.amazon.com/marketplace/"},
    "MCP_registry": {"label": "model_context_protocol", "url": "https://modelcontextprotocol.io/"},
    "package_metadata": {"label": "python_packaging", "url": "https://packaging.python.org/en/latest/specifications/"},
    "runbooks": {"label": "google_sre_workbook", "url": "https://sre.google/workbook/table-of-contents/"},
    "GitHub_repo": {"label": "github_rest_api", "url": "https://docs.github.com/en/rest"},
    "npm_metadata": {"label": "npm_docs", "url": "https://docs.npmjs.com/"},
    "PyPI_metadata": {"label": "pypi_json_api", "url": "https://docs.pypi.org/api/json/"},
    "Schema.org": {"label": "schema_org", "url": "https://schema.org/docs/schemas.html"},
    "SEC_EDGAR": {"label": "sec_edgar_api", "url": "https://www.sec.gov/edgar/sec-api-documentation"},
}
FALLBACK_REF = {"label": "openapi_spec", "url": "https://spec.openapis.org/oas/latest.html"}
STANDARD_BLOCKERS = ["source_ref_resolution_pending", "behavior_fixture_missing", "effects_not_audited"]
_WORD = re.compile(r"[a-z0-9]+")


def _split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _semis(val: str) -> list[str]:
    return [p.strip() for p in val.split(";") if p.strip()]


def _slug(*texts: str) -> str:
    toks = []
    for t in texts:
        toks += _WORD.findall(str(t).lower())
    return "-".join(toks[:6]) or "row"


def _digest(*parts: str) -> str:
    return hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()


def _source_refs(families_cell: str) -> list[dict[str, str]]:
    out, seen = [], set()
    for fam in _semis(families_cell):
        ref = FAMILY_URL.get(fam)
        if ref and ref["url"] not in seen:
            out.append(dict(ref))
            seen.add(ref["url"])
    return out or [dict(FALLBACK_REF)]


def _edge_head(edge: str) -> str:
    return re.split(r"[+\[]", str(edge), maxsplit=1)[0].strip() or "Input"


def map_row(cells: dict[str, str], *, pack_id: str) -> dict[str, Any] | None:
    title = cells.get("title", "").strip()
    input_edge = cells.get("input_edge", "").strip()
    output_edge = cells.get("output_edge", "").strip()
    record_id = cells.get("record_id", "").strip() or cells.get("row_id", "")
    if not title or not input_edge or not output_edge or input_edge == output_edge:
        return None

    proofs = _semis(cells.get("proof_requirements", ""))
    if "candidate_boundary_gate" not in proofs:
        proofs.append("candidate_boundary_gate")
    if len(proofs) < 2:
        proofs = list(dict.fromkeys(proofs + ["input_contract_validation", "candidate_boundary_gate"]))
    effects = [{"type": e, "description": f"declared effect ({e}); audit before promotion"}
               for e in _semis(cells.get("effects", "")) or ["compute"]]
    wrapper = cells.get("wrapper_target") or cells.get("runtime_shape") or cells.get("runtime_target") or ""
    mutators = _semis(wrapper.replace(" ", "_")) or ["output_receipt_wrapper"]
    # dimension columns (everything not a canonical field) become the contract's descriptive context
    dims = {k: v for k, v in cells.items() if k not in {
        "row_id", "record_id", "pack_id", "title", "input_edge", "output_edge",
        "known_implementation_families", "source_ref_families", "effects", "proof_requirements",
        "candidate", "serves_truth"} and v}
    errors = _semis(cells.get("error_model", "")) or ["input_contract_violation", "source_unresolved"]

    card_id = "prim:rp:" + _digest(pack_id, record_id, input_edge, output_edge)[:20]
    contract = {
        "summary": title,
        "input": {_edge_head(input_edge): f"{input_edge} — construct exactly as named before invoking."},
        "output": {_edge_head(output_edge): f"{output_edge} — verify the receipt before consuming."},
        "errors": errors[:6],
        "dimensions": dims,
    }
    return {
        "record_type": "primitive_candidate",
        "primitive_id": card_id,
        "extracted_candidate_id": f"rp:{pack_id}:{_slug(record_id)}",
        "kind": "primitive",
        "primitive_kind": f"rawpack.{pack_id}",
        "title": title,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "contract": contract,
        "blackbox": f"{title}. Deterministic-first wrapper derived from the {pack_id} dimension pack; "
                    f"implementation is source-backed and unverified until fixtures run.",
        "effects": effects,
        "mutators": mutators,
        "proof_requirements": proofs,
        "promotion_blockers": STANDARD_BLOCKERS,
        "source_refs": _source_refs(cells.get("source_ref_families", "")),
        "dedupe_key": f"{input_edge}->{output_edge}::{_slug(pack_id, record_id)}".lower(),
        "source_model": "deterministic_table_conversion",
        "source_provider": "generated_primitive_packs",
        "candidate": True,
        "serves_truth": False,
    }


def parse_pack(path: Path) -> tuple[str, list[dict[str, Any]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header_idx = next((i for i, ln in enumerate(lines) if "row_id" in ln and "|" in ln), None)
    if header_idx is None:
        return path.stem, []
    header = _split_row(lines[header_idx])
    pack_id = path.stem.replace("primitive_", "").replace("_pack", "")
    rows: list[dict[str, Any]] = []
    for ln in lines[header_idx + 1:]:
        if "|" not in ln or set(ln.strip()) <= {"|", "-", " ", ":"}:
            continue
        vals = _split_row(ln)
        if len(vals) != len(header):
            continue
        cells = dict(zip(header, vals))
        if cells.get("row_id", "").strip() in {"", "row_id"}:
            continue
        # prefer the pack's own pack_id cell if present
        row_pack = cells.get("pack_id", "").strip() or pack_id
        card = map_row(cells, pack_id=row_pack)
        if card is not None:
            rows.append(card)
    return pack_id, rows


def build_all(packs_dir: Path = PACKS_DIR) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    per_pack: dict[str, list[dict[str, Any]]] = {}
    total_in = 0
    for path in sorted(packs_dir.glob("*_pack.md")):
        pack_id, rows = parse_pack(path)
        if rows:
            per_pack[pack_id] = rows
            total_in += len(rows)
    stats = {
        "record_type": "raw_pack_conversion_manifest",
        "packs_converted": len(per_pack),
        "rows_out": total_in,
        "per_pack": {k: len(v) for k, v in sorted(per_pack.items())},
        "candidate": True,
        "serves_truth": False,
    }
    return per_pack, stats


def write_staged(label: str, packs_dir: Path = PACKS_DIR) -> dict[str, Any]:
    per_pack, stats = build_all(packs_dir)
    for pack_id, rows in per_pack.items():
        out = BATCH_RUNS / label / pack_id / "extracted" / "extracted_candidates.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows),
                       encoding="utf-8")
    stats["label"] = label
    stats["staged_root"] = str((BATCH_RUNS / label).relative_to(REPO))
    return stats


def self_test() -> int:
    sample_header = "| row_id | record_id | pack_id | spec_family | operation_kind | business_object | auth_scheme | pagination_model | error_model | wrapper_target | title | input_edge | output_edge | known_implementation_families | source_ref_families | effects | proof_requirements | candidate | serves_truth |"
    sample_row = "| 1 | api_contract_primitives:a117e15b659b | api_contract_primitives | openapi | list_collection | customer | api_key_header | cursor | problem_json | planlock_json | list wrapper | OpenapiOperation[CustomerListCollection]+AuthPolicy | TypedCustomerResponse+ApiCallReceipt | parsers | OpenAPI_spec; official_api_reference | network_read; network_write_optional | source_ref_resolution; idempotency_test; candidate_boundary_gate | true | false |"
    header = _split_row(sample_header)
    cells = dict(zip(header, _split_row(sample_row)))
    card = map_row(cells, pack_id="api_contract_primitives")
    checks = [
        ("maps a real pack row", card is not None),
        ("kind is primitive", card and card["kind"] == "primitive"),
        ("input != output", card and card["input_edge"] != card["output_edge"]),
        ("contract is a dict with summary/input/output/errors", card and isinstance(card["contract"], dict)
         and {"summary", "input", "output", "errors"} <= set(card["contract"])),
        (">=1 public https source_ref", card and any(r["url"].startswith("https://") for r in card["source_refs"])),
        (">=2 proof_requirements incl candidate_boundary_gate", card and len(card["proof_requirements"]) >= 2
         and "candidate_boundary_gate" in card["proof_requirements"]),
        (">=1 effect and >=1 mutator", card and card["effects"] and card["mutators"]),
        ("promotion_blockers present", card and card["promotion_blockers"]),
        ("deterministic id", card and card["primitive_id"] == map_row(cells, pack_id="api_contract_primitives")["primitive_id"]),
        ("boundary held", card and card["candidate"] is True and card["serves_truth"] is False),
        ("no local path in card", card and "/home/" not in json.dumps(card)),
        ("every family maps to https", all(v["url"].startswith("https://") for v in FAMILY_URL.values())),
        ("unmappable row rejected", map_row({"title": "x"}, pack_id="p") is None),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - raw_pack_primitive_candidates:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - raw_pack_primitive_candidates: table row -> verifier candidate (contract synthesized, families "
          "-> public https refs, boundary held, deterministic ids).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)
    parser.add_argument("--label", default=None)
    parser.add_argument("--packs-dir", default=str(PACKS_DIR))
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    label = args.label or f"{date}-rawpack"
    stats = write_staged(label, Path(args.packs_dir))
    print(json.dumps(stats, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
