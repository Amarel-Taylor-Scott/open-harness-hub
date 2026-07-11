#!/usr/bin/env python3
"""scripts.real_world_situation_primitive_specs — generate primitive specs for the MESSY REAL WORLD, not the ideal
case: legacy versions, vendor quirks, broken encodings, malformed input, migrations, deprecated APIs, partial
failures — crossed with the full technology landscape (databases, languages, cloud, web/API, data-formats,
frameworks, hosting). The SITUATION axis is the differentiator: our clean primitives work on tidy inputs; these
target the conditions real systems actually hit.

It crosses (primitive_family x tech_system x situation) into `needs_executor` specs with RICH intents describing the
exact non-ideal condition, then feeds them to `spec_to_executor_synthesizer` (Hy3-first) → security gate → sandbox →
fixture-prove → promote. Deterministic coprime-strided sampling spreads coverage across the huge grid; resumable via
--start. candidate/serves_truth=false throughout.

    python3 scripts/real_world_situation_primitive_specs.py --self-test
    python3 scripts/real_world_situation_primitive_specs.py --emit 200 --start 0     # print specs (no LLM)
    python3 scripts/real_world_situation_primitive_specs.py --synthesize 100         # live Hy3 -> working primitives
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
_DATA_SUBDIR = "data/dev-intel/real_world_situation_primitive_specs"
_COPRIME = 2147483647  # coprime stride to spread sampling across the grid deterministically

# ── the technology landscape (grouped; the generator crosses these, so this need not be exhaustive) ────────────
TECH: dict[str, list[str]] = {
    "database": ["mysql", "postgresql", "oracle", "sql_server", "sqlite", "mongodb", "redis", "cassandra",
                 "dynamodb", "bigquery", "snowflake", "clickhouse", "duckdb", "mariadb", "cockroachdb"],
    "language": ["python", "javascript", "typescript", "java", "csharp", "go", "rust", "php", "ruby", "kotlin",
                 "scala", "sql", "bash", "powershell", "perl", "cobol", "vba"],
    "cloud": ["aws_s3", "aws_lambda", "aws_dynamodb", "aws_sqs", "aws_iam", "gcp_gcs", "gcp_bigquery",
              "gcp_pubsub", "gcp_cloud_run", "azure_blob", "azure_functions", "azure_ad", "cloudflare_workers"],
    "web_api": ["rest", "graphql", "grpc", "soap", "openapi", "websocket", "oauth2", "jwt", "webhook", "odata"],
    "data_format": ["json", "xml", "csv", "parquet", "avro", "protobuf", "yaml", "edi_x12", "hl7_v2", "fhir",
                    "iso20022", "fixed_width", "ndjson", "ini", "toml"],
    "framework": ["django", "flask", "rails", "spring", "express", "react", "angular", "dotnet", "laravel",
                  "fastapi", "nextjs"],
    "hosting": ["nginx", "apache", "kubernetes", "docker", "terraform", "systemd", "iis"],
}

# ── the SITUATION axis — the messy real-world conditions (the value-add), each with a concrete description ──────
SITUATIONS: dict[str, str] = {
    "legacy_version": "an OLD version with known quirks (e.g. MySQL 5.5/5.6 zero-dates '0000-00-00' and latin1, "
                      "Python 2 str/unicode, Java 6, PHP 5, .NET Framework, IE11) — handle the legacy behavior correctly",
    "vendor_quirk": "a vendor-specific quirk (MySQL zero-dates & implicit defaults, Oracle empty-string-IS-NULL, "
                    "SQLite dynamic typing, S3 read-after-write eventual consistency, Excel-damaged CSV, DST gaps)",
    "broken_encoding": "broken/mixed text encoding — mojibake, double-encoded UTF-8, latin1-labelled-as-utf8, BOM, "
                       "smart-quotes, NBSP — detect and repair deterministically",
    "malformed_input": "malformed/dirty input — truncated, extra or missing fields, wrong types, embedded NUL, "
                       "trailing commas, unescaped delimiters — parse defensively and report what was wrong",
    "version_mismatch": "a version/schema mismatch — API v1 vs v2 field renames, added/removed columns, a mixed-"
                        "version cluster — reconcile without losing data",
    "migration": "a MIGRATION from an old format/version to a new one (MySQL 5->8 datetime/charset, Python 2->3, "
                 "REST->GraphQL, XML->JSON, on-prem->cloud) — convert losslessly with a receipt of what changed",
    "deprecated_api": "a DEPRECATED API/method still in production — map the old call/shape onto the supported one",
    "partial_failure": "a partial failure — timeout, 429 rate-limit with Retry-After, half-written record, "
                       "connection reset — produce a safe, resumable, idempotent result",
    "injection_hardened": "adversarial input — SQL/command/path/template injection, XXE, SSRF-shaped values — "
                         "neutralize or reject deterministically without executing anything",
    "unicode_edge": "Unicode edge cases — emoji/ZWJ, RTL/bidi, combining marks, surrogate pairs, NFC/NFD "
                    "normalization, homoglyphs — handle correctly",
    "large_scale": "scale/streaming constraints — must be memory-bounded, paginated, streaming, backpressure-aware "
                   "over huge inputs, not load-everything-into-RAM",
}

# ── primitive families that make sense for real-world/legacy work (all D0/D1-leaning, fixture-provable) ────────
FAMILIES: dict[str, str] = {
    "parser": "parse the input into a typed structure",
    "normalizer": "normalize the value to a canonical form",
    "validator": "validate and return a structured verdict + reasons",
    "mapper": "map/transform from the source shape to the target shape",
    "migrator": "convert from the old version/format to the new one, losslessly, with a change receipt",
    "encoding_fixer": "detect and repair the encoding, returning clean text + what was fixed",
    "error_mapper": "map the vendor/legacy error code or message onto a normalized error taxonomy",
    "quirk_workaround": "apply the deterministic workaround for the known quirk",
    "sanitizer": "sanitize the input against the adversarial condition, returning safe output or a rejection",
    "version_detector": "detect the version/dialect from a sample and return it",
    "connection_string_builder": "build a correct connection/config string for this system+situation",
    "schema_differ": "diff the old vs new schema and emit the field-level changes",
}

DETERMINISM = {"injection_hardened": "D0_pure", "partial_failure": "D2_bounded_external",
               "large_scale": "D1_seeded"}  # default D0_pure otherwise


def _grid() -> list[tuple[str, str, str, str]]:
    """(family, tech_group, tech, situation) — the full cross-product."""
    out: list[tuple[str, str, str, str]] = []
    for fam in FAMILIES:
        for group, techs in TECH.items():
            for tech in techs:
                for sit in SITUATIONS:
                    out.append((fam, group, tech, sit))
    return out


def grid_size() -> int:
    return len(_grid())


def _spec(idx: int, fam: str, group: str, tech: str, sit: str) -> dict[str, Any]:
    name = f"{fam}__{tech}__{sit}"
    intent = (f"A DETERMINISTIC {fam} for {tech} ({group}) under the real-world condition '{sit}': "
              f"{SITUATIONS[sit]}. The function should {FAMILIES[fam]} for {tech}, correctly handling this "
              f"non-ideal condition (NOT just the happy path). Pure stdlib; deterministic; fixture-provable.")
    det = DETERMINISM.get(sit, "D0_pure")
    return {"name": name, "needs_executor": True, "determinism_level": det, "family": fam, "tech": tech,
            "tech_group": group, "situation": sit, "intent": intent,
            "input_schema": {"in": f"{tech}_{fam}_input"}, "output_schema": {"out": f"{tech}_{fam}_output"},
            "edges": {"input_edge": f"{tech}:{sit}:raw", "output_edge": f"{tech}:{fam}:handled"},
            "grid_index": idx, **BOUNDARY}


def sample_specs(n: int, start: int = 0) -> list[dict[str, Any]]:
    """Deterministic coprime-strided sample of n specs across the grid (spreads coverage), resumable via start."""
    grid = _grid()
    g = len(grid)
    out: list[dict[str, Any]] = []
    for k in range(n):
        idx = ((start + k) * _COPRIME) % g
        out.append(_spec(idx, *grid[idx]))
    return out


def synthesize(specs: list[dict[str, Any]], out_path: Optional[Path] = None) -> dict[str, Any]:
    from scripts.spec_to_executor_synthesizer import run as _synth_run, _hy3_chat_fn  # noqa: PLC0415
    out_path = out_path or (resource(_DATA_SUBDIR) / "situation_synthesis_receipts.jsonl")
    return _synth_run(specs, _hy3_chat_fn(), out_path=out_path)


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    g = grid_size()
    checks.append((f"large real-world grid ({len(FAMILIES)} fam x tech x {len(SITUATIONS)} situations = {g:,})",
                   g >= 5000 and len(SITUATIONS) >= 10))
    specs = sample_specs(50, start=0)
    checks.append(("sample yields distinct, situation-bearing specs (not ideal-only)",
                   len({s["name"] for s in specs}) == 50
                   and all(s["situation"] in SITUATIONS and s["needs_executor"] for s in specs)))
    checks.append(("intents name the exact non-ideal condition + tech + family",
                   all(s["tech"] in s["intent"] and SITUATIONS[s["situation"]][:20] in s["intent"] for s in specs)))
    checks.append(("legacy MySQL-version + migration situations are representable",
                   any(s["tech"] == "mysql" and s["situation"] in ("legacy_version", "migration", "vendor_quirk")
                       for s in sample_specs(2000, start=0))))
    checks.append(("determinism budgets are truth-eligible (D0/D1/D2)",
                   all(s["determinism_level"] in ("D0_pure", "D1_seeded", "D2_bounded_external") for s in specs)))
    checks.append(("deterministic + resumable: same (n,start) -> identical grid indices",
                   [s["grid_index"] for s in sample_specs(20, start=100)]
                   == [s["grid_index"] for s in sample_specs(20, start=100)]))
    checks.append(("candidate-only", all(s["serves_truth"] is False for s in specs)))
    ok = all(v for _, v in checks)
    for nm, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {nm}")
    print(("PASS" if ok else "FAIL") + f" - real_world_situation_primitive_specs: {g:,}-point grid "
          f"({len(FAMILIES)} families x {sum(len(v) for v in TECH.values())} tech systems x {len(SITUATIONS)} "
          "real-world SITUATIONS incl legacy/migration/broken-encoding/vendor-quirk); coprime-sampled specs feed the "
          "Hy3 synthesizer -> fixture-proven primitives for messy reality. serves_truth=false.")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Generate real-world/legacy/non-ideal-situation primitive specs.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--emit", type=int, metavar="N", help="print N sampled specs (no LLM)")
    ap.add_argument("--synthesize", type=int, metavar="N", help="synthesize N specs via Hy3 (live)")
    ap.add_argument("--start", type=int, default=0, help="resumable grid offset")
    ap.add_argument("--grid-size", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.grid_size:
        print(f"grid size: {grid_size():,}")
        return 0
    if args.emit is not None:
        for s in sample_specs(args.emit, start=args.start):
            print(json.dumps({k: s[k] for k in ("name", "tech", "situation", "determinism_level", "intent")}))
        return 0
    if args.synthesize is not None:
        specs = sample_specs(args.synthesize, start=args.start)
        print(f"synthesizing {len(specs)} real-world/legacy specs via Hy3 (start={args.start}) …")
        summ = synthesize(specs)
        print(json.dumps({k: summ.get(k) for k in ("specs", "promoted", "validated", "certified", "candidate",
              "quarantined", "by_outcome", "pool_path")}, indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
