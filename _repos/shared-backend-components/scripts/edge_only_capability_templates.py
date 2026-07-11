#!/usr/bin/env python3
"""edge_only_capability_templates — standardized capability-CLASS templates so ANY package (across
crates.io/npm/PyPI/pystdlib) snaps onto a canonical typed-edge + usage-recipe shape.

Owner (2026-07-11): "we need more use cases, ideas, templates, standards." Curating packages one-by-one
doesn't scale; a capability CLASS does. Each template fixes the canonical typed input/output edge, the
recipe SHAPE (import + minimal call), the dimensions worth scraping, and cross-ecosystem example packages.
Onboarding a new package then = pick its class + fill the handle → a valid edge-only card skeleton, so the
format is a STANDARD, not a pile of one-offs. Classes compose: an http_client (→JsonBytes) feeds a
serialize (JsonBytes→) which feeds a validate (→ValidatedModel) — a real typed pipeline across packages.

    python3 scripts/edge_only_capability_templates.py --self-test
    python3 scripts/edge_only_capability_templates.py --list
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_SBC.parent.parent),
           str(_SBC.parent.parent / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
try:
    from src.teleon.experiments.ids import canonical_id
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"edge_only_capability_templates requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

#: canonical capability classes. Each: typed edges (composition vocabulary), a recipe shape, the dimensions
#: worth scraping, and real example packages across ecosystems (the multi-registry use-case breadth).
CAPABILITY_TEMPLATES: dict[str, dict[str, Any]] = {
    "serialize": {"input_edge": "TypedValue+Format", "output_edge": "SerializedBytes",
                  "recipe_shape": "import {pkg}; bytes = {pkg}.{dump}(value)",
                  "dims": ["formats", "streaming", "zero_copy"],
                  "examples": {"crates.io": "serde", "pypi": "orjson", "npm": "superjson", "pystdlib": "json"}},
    "deserialize": {"input_edge": "SerializedBytes+Schema", "output_edge": "TypedValue",
                    "recipe_shape": "import {pkg}; value = {pkg}.{load}(bytes)",
                    "dims": ["formats", "streaming", "strictness"],
                    "examples": {"crates.io": "serde_json", "pypi": "json", "npm": "JSON", "pystdlib": "json"}},
    "http_client": {"input_edge": "HttpRequestSpec", "output_edge": "JsonBytes",
                    "recipe_shape": "import {pkg}; resp = {pkg}.get(url); data = resp.json()",
                    "dims": ["async", "http2", "retries", "downloads"],
                    "examples": {"crates.io": "reqwest", "pypi": "httpx", "npm": "axios", "pystdlib": "urllib"}},
    "validate": {"input_edge": "RawMapping+Schema", "output_edge": "ValidatedModel",
                 "recipe_shape": "import {pkg}; model = {pkg}.validate(data, schema)",
                 "dims": ["coercion", "error_detail", "json_schema"],
                 "examples": {"crates.io": "validator", "pypi": "pydantic", "npm": "zod", "pystdlib": "dataclasses"}},
    "parse_text": {"input_edge": "Pattern+InputText", "output_edge": "MatchResult",
                   "recipe_shape": "import {pkg}; m = {pkg}.search(pattern, text)",
                   "dims": ["unicode", "backtracking", "streaming"],
                   "examples": {"crates.io": "regex", "pypi": "re", "npm": "RegExp", "pystdlib": "re"}},
    "datetime": {"input_edge": "TimeComponents+TimeZone", "output_edge": "NormalizedDateTime",
                 "recipe_shape": "import {pkg}; dt = {pkg}.parse(s)",
                 "dims": ["timezones", "iso8601", "duration_math"],
                 "examples": {"crates.io": "chrono", "pypi": "pendulum", "npm": "date-fns", "pystdlib": "datetime"}},
    "concurrency": {"input_edge": "Task+RuntimeConfig", "output_edge": "CompletedOutput",
                    "recipe_shape": "import {pkg}; result = {pkg}.run(task)",
                    "dims": ["async", "work_stealing", "structured"],
                    "examples": {"crates.io": "tokio", "pypi": "asyncio", "npm": "p-map", "pystdlib": "concurrent.futures"}},
    "crypto_hash": {"input_edge": "Bytes+Algorithm", "output_edge": "HexDigest",
                    "recipe_shape": "import {pkg}; d = {pkg}.{algo}(bytes).hexdigest()",
                    "dims": ["algorithms", "constant_time", "fips"],
                    "examples": {"crates.io": "sha2", "pypi": "hashlib", "npm": "crypto", "pystdlib": "hashlib"}},
    "encode": {"input_edge": "Bytes", "output_edge": "EncodedText",
               "recipe_shape": "import {pkg}; s = {pkg}.encode(bytes)",
               "dims": ["url_safe", "streaming"],
               "examples": {"crates.io": "base64", "pypi": "base64", "npm": "buffer", "pystdlib": "base64"}},
    "compress": {"input_edge": "Bytes+Level", "output_edge": "CompressedBytes",
                 "recipe_shape": "import {pkg}; out = {pkg}.compress(bytes, level)",
                 "dims": ["algorithm", "ratio", "speed"],
                 "examples": {"crates.io": "flate2", "pypi": "zlib", "npm": "pako", "pystdlib": "gzip"}},
    "tabular": {"input_edge": "CsvText+Dialect", "output_edge": "RowRecords",
                "recipe_shape": "import {pkg}; rows = list({pkg}.reader(f))",
                "dims": ["dialects", "streaming", "typed_columns"],
                "examples": {"crates.io": "csv", "pypi": "csv", "npm": "papaparse", "pystdlib": "csv"}},
    "math_stats": {"input_edge": "NumberSequence", "output_edge": "Statistic",
                   "recipe_shape": "import {pkg}; m = {pkg}.mean(xs)",
                   "dims": ["vectorized", "precision", "distributions"],
                   "examples": {"crates.io": "statrs", "pypi": "statistics", "npm": "simple-statistics", "pystdlib": "statistics"}},
    "cli_parse": {"input_edge": "ArgvVector+ArgSpec", "output_edge": "ParsedArgs",
                  "recipe_shape": "import {pkg}; args = {pkg}.parse(spec)",
                  "dims": ["subcommands", "derive", "help_gen"],
                  "examples": {"crates.io": "clap", "pypi": "argparse", "npm": "commander", "pystdlib": "argparse"}},
    "logging": {"input_edge": "LogEvent+Level", "output_edge": "EmittedRecord",
                "recipe_shape": "import {pkg}; {pkg}.info(msg)", "dims": ["structured", "sinks", "levels"],
                "examples": {"crates.io": "tracing", "pypi": "structlog", "npm": "pino", "pystdlib": "logging"}},
    "database": {"input_edge": "Query+Connection", "output_edge": "ResultRows",
                 "recipe_shape": "import {pkg}; rows = {pkg}.execute(query)", "dims": ["async", "pooling", "orm"],
                 "examples": {"crates.io": "sqlx", "pypi": "psycopg", "npm": "pg", "pystdlib": "sqlite3"}},
    "template_render": {"input_edge": "TemplateSource+Context", "output_edge": "RenderedText",
                        "recipe_shape": "import {pkg}; out = {pkg}.render(tmpl, ctx)", "dims": ["autoescape", "async"],
                        "examples": {"crates.io": "tera", "pypi": "jinja2", "npm": "handlebars", "pystdlib": "string"}},
    "config": {"input_edge": "ConfigSource", "output_edge": "TypedConfig",
               "recipe_shape": "import {pkg}; cfg = {pkg}.load(source)", "dims": ["env", "layered", "typed"],
               "examples": {"crates.io": "config", "pypi": "dynaconf", "npm": "dotenv", "pystdlib": "configparser"}},
    "filesystem": {"input_edge": "PathString", "output_edge": "PathObject",
                   "recipe_shape": "import {pkg}; p = {pkg}.Path(s)", "dims": ["async", "glob", "atomic"],
                   "examples": {"crates.io": "walkdir", "pypi": "pathlib", "npm": "fs-extra", "pystdlib": "pathlib"}},
    "embedding": {"input_edge": "Text", "output_edge": "Vector",
                  "recipe_shape": "import {pkg}; v = {pkg}.embed(text)", "dims": ["dim", "onnx", "batch"],
                  "examples": {"crates.io": "candle", "pypi": "fastembed", "npm": "transformers", "pystdlib": "hashlib"}},
    "testing": {"input_edge": "TestSubject+Assertion", "output_edge": "TestVerdict",
                "recipe_shape": "import {pkg}; {pkg}.assert_that(x)", "dims": ["fixtures", "property", "mock"],
                "examples": {"crates.io": "proptest", "pypi": "pytest", "npm": "vitest", "pystdlib": "unittest"}},
    "image": {"input_edge": "ImageBytes+Op", "output_edge": "ProcessedImage",
              "recipe_shape": "import {pkg}; out = {pkg}.open(bytes)", "dims": ["formats", "resize", "simd"],
              "examples": {"crates.io": "image", "pypi": "pillow", "npm": "sharp", "pystdlib": "colorsys"}},
}


def apply_template(cls: str, *, registry: str, name: str, version_req: str = "*",
                   license_spdx: str = "MIT") -> dict[str, Any]:
    """Snap a package onto a capability class → a valid edge-only card SKELETON (candidate, edges from the
    template, recipe shape pre-filled with the package name; symbols still need API verification)."""
    t = CAPABILITY_TEMPLATES[cls]
    pid = canonical_id("prim:pkg", registry, name)
    return {
        "primitive_id": pid, "title": f"{name} ({registry}) — {cls}",
        "primitive_kind": f"package_reference.{registry.replace('.', '_')}",
        "kind": "edge_only.package_link", "capability_class": cls,
        "input_edge": t["input_edge"], "output_edge": t["output_edge"],
        "has_code_body": False, "hosts_raw_code": False, "search_ready": True,
        "usage_recipes": [{"route": "template", "snippet": t["recipe_shape"].format(pkg=name, dump="dump",
                                                                                    load="load", algo="sha256"),
                           "verified": False}],
        "package": {"registry": registry, "name": name, "version_req": version_req, "license": license_spdx},
        "scrapable_dimensions": t["dims"],
        "promotion_blockers": ["recipe_symbols_unverified", "review_required"],
        "readiness": "R2_template_applied", "source_family": "capability_template",
        "template_class": cls, **BOUNDARY,
    }


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    checks.append(("templates span the major capability classes (>=12)",
                   len(CAPABILITY_TEMPLATES) >= 12))

    checks.append(("every template has typed edges + a recipe shape + scrapable dims + examples",
                   all(t["input_edge"] and t["output_edge"] and "{pkg}" in t["recipe_shape"]
                       and t["dims"] and t["examples"] for t in CAPABILITY_TEMPLATES.values())))

    checks.append(("every template gives cross-ecosystem examples (crates.io + pypi + npm)",
                   all({"crates.io", "pypi", "npm"} <= set(t["examples"]) for t in CAPABILITY_TEMPLATES.values())))

    # templates COMPOSE by shared typed-edge COMPONENT (exact); subtype chains (JsonBytes⊆SerializedBytes)
    # compose via the compatibility lattice separately.
    def _components(edge: str) -> set[str]:
        return {p for p in edge.split("+") if p}
    ser_out = _components(CAPABILITY_TEMPLATES["serialize"]["output_edge"])       # {SerializedBytes}
    deser_in = _components(CAPABILITY_TEMPLATES["deserialize"]["input_edge"])     # {SerializedBytes, Schema}
    checks.append(("classes compose by shared typed-edge component (serialize→deserialize on SerializedBytes)",
                   "SerializedBytes" in (ser_out & deser_in)))

    # applying a template yields a valid card skeleton with the class edges + a pre-filled recipe
    card = apply_template("serialize", registry="crates.io", name="serde", license_spdx="MIT OR Apache-2.0")
    checks.append(("apply_template → valid edge-only skeleton (class edges, recipe pre-filled, unverified)",
                   card["input_edge"] == "TypedValue+Format" and "serde" in card["usage_recipes"][0]["snippet"]
                   and card["usage_recipes"][0]["verified"] is False
                   and "recipe_symbols_unverified" in card["promotion_blockers"]))

    checks.append(("skeletons are candidate-only + edge-only (no code body)",
                   card["candidate"] is True and card["serves_truth"] is False
                   and card["has_code_body"] is False))

    # determinism
    checks.append(("apply_template deterministic",
                   json.dumps(apply_template("serialize", registry="crates.io", name="serde"), sort_keys=True)
                   == json.dumps(apply_template("serialize", registry="crates.io", name="serde"), sort_keys=True)))

    ok = all(v for _, v in checks)
    print("edge_only_capability_templates — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    n_examples = sum(len(t["examples"]) for t in CAPABILITY_TEMPLATES.values())
    print(f"  {len(CAPABILITY_TEMPLATES)} capability-class templates → {n_examples} example use-cases across "
          f"crates.io/pypi/npm/pystdlib. Onboard a package = pick a class + fill the handle.")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if args.list:
        for cls, t in CAPABILITY_TEMPLATES.items():
            print(f"{cls:14} {t['input_edge']:26} -> {t['output_edge']:20} e.g. {t['examples']}")
        return 0
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
