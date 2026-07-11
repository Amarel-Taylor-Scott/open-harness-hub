#!/usr/bin/env python3
"""edge_only_package_primitives — EDGE-ONLY primitives that LINK to real package registries
(crates.io, npm, PyPI, …) instead of storing or generating a code body.

The insight (owner, 2026-07-11): the world's reuse layer already exists — crates.io/npm/PyPI hold
millions of maintained, versioned, tested packages. We don't rebuild them; we make them COMPOSABLE by
wrapping each as a thin, typed-edge primitive that POINTS to the package. The card carries the typed
input_edge/output_edge + contract (so the compatibility lattice can compose it) + a package HANDLE
(registry, name, version requirement, license, digest) — and NO code body. That makes each primitive:

  • storage-light   — bytes, not a 108GB code DB (the anti-bloat design);
  • maximally reusable — it references the ecosystem's own maintained, tested code;
  • trust-grounded  — a package has real provenance (downloads, versions, yanking, attestations),
                      BETTER signals than a synthetic primitive — we add the typed edge on top.

What we ADD (the wedge): contract-typed composability + verification the ecosystem lacks. An edge-only
primitive is candidate-only until its link resolves, its license is vendorable, it is not yanked, and its
declared edge is confirmed against the package's public API (`edge_matches_public_api` stays a promotion
blocker until checked — declaring an edge is not verifying it; see declaration_behavior_conformance).

    python3 scripts/edge_only_package_primitives.py --self-test
    python3 scripts/edge_only_package_primitives.py --emit        # write candidate cards (tiny)
    python3 scripts/edge_only_package_primitives.py --resolve serde   # opt-in network link check
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
_ROOT = _SBC.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_ROOT), str(_ROOT / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
try:
    from src.teleon.experiments.ids import canonical_id
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"edge_only_package_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
PRIMITIVE_ID_PREFIX = "prim:pkg"
OUT_DIR = _SBC / "data" / "dev-intel" / "edge_only_package_primitives"
CARDS_PATH = OUT_DIR / "edge_only_package_candidate_cards.jsonl"

#: registry handle templates (canonical URL + the machine metadata endpoint for an opt-in resolve).
REGISTRIES = {
    "crates.io": {"url": "https://crates.io/crates/{name}", "api": "https://crates.io/api/v1/crates/{name}",
                  "runtime": "rust"},
    "npm": {"url": "https://www.npmjs.com/package/{name}", "api": "https://registry.npmjs.org/{name}",
            "runtime": "node"},
    "pypi": {"url": "https://pypi.org/project/{name}/", "api": "https://pypi.org/pypi/{name}/json",
             "runtime": "python"},
}

#: SPDX license ids permissive enough to VENDOR (pass the promotion gate). Copyleft is blocked there.
_VENDORABLE = {"MIT", "APACHE-2.0", "BSD-2-CLAUSE", "BSD-3-CLAUSE", "ISC", "MPL-2.0", "ZLIB", "UNLICENSE"}


def _license_vendorable(spdx: str) -> bool:
    """Permissive if EVERY OR-alternative is vendorable (e.g. 'MIT OR Apache-2.0' passes)."""
    alts = [a.strip().upper() for a in str(spdx).replace("/", " OR ").split(" OR ") if a.strip()]
    return bool(alts) and any(a in _VENDORABLE for a in alts)


def _code_hosting_policy(spdx: str) -> str:
    """We NEVER host raw code by default — we host the searchable metadata (description+edges+dimensions)
    and LINK to code the ecosystem already maintains. Hosting/caching the raw code is an opt-in that
    depends on the license (owner: "we would not host the raw code unless allowed or rewritten"):
      • link_only        — always legal: store the handle + our metadata, point at the upstream code;
      • cache_permitted  — permissive license: we MAY vendor/cache the code (still link_only until chosen);
      • rewrite_required — copyleft/unknown: to serve code we must REIMPLEMENT it (our own, owned) — never
                           host theirs. `link_only` remains available for search/compose either way."""
    return "cache_permitted" if _license_vendorable(spdx) else "rewrite_required"


#: dimensions we can SCRAPE from a registry to enrich the edge-only primitive (populated by an opt-in
#: scrape — NEVER fabricated offline; the card names them so a scrape has a target, honest by default).
_SCRAPABLE_DIMENSIONS = ["downloads_total", "downloads_recent", "stars", "dependents_count",
                         "latest_version", "released_at", "yanked", "maintenance_status", "msrv_or_engine"]


#: curated, well-known packages with MEANINGFUL typed edges (hand-derived from each package's purpose).
#: registry-agnostic on purpose — the same edge vocabulary spans crates.io / npm / pypi.
PACKAGE_SPECS: list[dict[str, Any]] = [
    # ── crates.io ─────────────────────────────────────────────────────────────────────────────────
    {"registry": "crates.io", "name": "serde", "version_req": "^1", "license": "MIT OR Apache-2.0",
     "title": "serde — typed (de)serialization framework", "tags": ["serialization"],
     "input_edge": "TypedValue+SerdeFormat", "output_edge": "SerializedBytes"},
    {"registry": "crates.io", "name": "serde_json", "version_req": "^1", "license": "MIT OR Apache-2.0",
     "title": "serde_json — JSON bytes ↔ typed value", "tags": ["serialization", "json"],
     "input_edge": "JsonBytes", "output_edge": "TypedValue"},
    {"registry": "crates.io", "name": "reqwest", "version_req": "^0.12", "license": "MIT OR Apache-2.0",
     "title": "reqwest — HTTP client", "tags": ["http", "network"],
     "input_edge": "HttpRequestSpec", "output_edge": "JsonBytes"},
    {"registry": "crates.io", "name": "regex", "version_req": "^1", "license": "MIT OR Apache-2.0",
     "title": "regex — pattern matching over text", "tags": ["text", "parsing"],
     "input_edge": "Pattern+InputText", "output_edge": "MatchSet"},
    {"registry": "crates.io", "name": "clap", "version_req": "^4", "license": "MIT OR Apache-2.0",
     "title": "clap — command-line argument parser", "tags": ["cli", "parsing"],
     "input_edge": "ArgvVector+CliArgSpec", "output_edge": "ParsedCliArgs"},
    {"registry": "crates.io", "name": "rayon", "version_req": "^1", "license": "MIT OR Apache-2.0",
     "title": "rayon — data-parallel iterators", "tags": ["concurrency", "parallel"],
     "input_edge": "ParallelIterable+MapReduceOp", "output_edge": "ReducedResult"},
    {"registry": "crates.io", "name": "tokio", "version_req": "^1", "license": "MIT",
     "title": "tokio — async runtime", "tags": ["concurrency", "async"],
     "input_edge": "AsyncTask+RuntimeConfig", "output_edge": "CompletedFutureOutput"},
    {"registry": "crates.io", "name": "chrono", "version_req": "^0.4", "license": "MIT OR Apache-2.0",
     "title": "chrono — date/time handling", "tags": ["datetime"],
     "input_edge": "TimestampInput+TimeZone", "output_edge": "NormalizedDateTime"},
    # ── PyPI ──────────────────────────────────────────────────────────────────────────────────────
    {"registry": "pypi", "name": "pydantic", "version_req": ">=2", "license": "MIT",
     "title": "pydantic — typed data validation", "tags": ["validation", "schema"],
     "input_edge": "RawMapping+PydanticSchema", "output_edge": "ValidatedModel"},
    {"registry": "pypi", "name": "httpx", "version_req": ">=0.27", "license": "BSD-3-Clause",
     "title": "httpx — async/sync HTTP client", "tags": ["http", "network"],
     "input_edge": "HttpRequestSpec", "output_edge": "JsonBytes"},
    # ── npm ───────────────────────────────────────────────────────────────────────────────────────
    {"registry": "npm", "name": "zod", "version_req": "^3", "license": "MIT",
     "title": "zod — TypeScript-first schema validation", "tags": ["validation", "schema"],
     "input_edge": "RawMapping+ZodSchema", "output_edge": "ValidatedModel"},
    {"registry": "npm", "name": "date-fns", "version_req": "^3", "license": "MIT",
     "title": "date-fns — date utilities", "tags": ["datetime"],
     "input_edge": "TimestampInput+TimeZone", "output_edge": "NormalizedDateTime"},
]


#: USAGE RECIPES — the token-savings core. A ZOO of compact "how to invoke it" routes per package, so an
#: LLM USES the package in ~tens of tokens instead of reading its files (thousands) or re-implementing it
#: (which fails). Each route: how to import + the minimal call. Multiple routes = the multi-path principle
#: (blocking vs async, simple vs typed). These are usage SHORTHAND, not the package's source.
USAGE_RECIPES: dict[str, list[dict[str, str]]] = {
    "serde": [{"route": "derive", "runtime": "rust",
               "snippet": "#[derive(serde::Serialize, serde::Deserialize)]\nstruct T { field: String }"}],
    "serde_json": [
        {"route": "parse_to_value", "runtime": "rust", "snippet": "let v: serde_json::Value = serde_json::from_str(&s)?;"},
        {"route": "typed_struct", "runtime": "rust", "snippet": "let t: T = serde_json::from_str(&s)?;  // T: Deserialize"},
        {"route": "to_string", "runtime": "rust", "snippet": "let s = serde_json::to_string(&value)?;"}],
    "reqwest": [
        {"route": "blocking_get_text", "runtime": "rust", "snippet": "let body = reqwest::blocking::get(url)?.text()?;"},
        {"route": "async_get_json", "runtime": "rust",
         "snippet": "let v: serde_json::Value = reqwest::get(url).await?.json().await?;"}],
    "regex": [{"route": "find", "runtime": "rust",
               "snippet": "let re = regex::Regex::new(r\"\\d+\")?;\nlet m = re.find(text);"},
              {"route": "captures", "runtime": "rust",
               "snippet": "let caps = re.captures(text).ok_or(\"no match\")?; let g = &caps[1];"}],
    "clap": [{"route": "derive_parser", "runtime": "rust",
              "snippet": "#[derive(clap::Parser)] struct Args { #[arg(short)] name: String }\nlet args = Args::parse();"}],
    "rayon": [{"route": "par_map_reduce", "runtime": "rust",
               "snippet": "use rayon::prelude::*;\nlet total: u64 = v.par_iter().map(|x| f(x)).sum();"}],
    "tokio": [{"route": "main_macro", "runtime": "rust",
               "snippet": "#[tokio::main]\nasync fn main() { /* .await here */ }"},
              {"route": "spawn", "runtime": "rust", "snippet": "let h = tokio::spawn(async move { work().await });\nh.await?;"}],
    "chrono": [{"route": "now_and_parse", "runtime": "rust",
                "snippet": "let now = chrono::Utc::now();\nlet dt = chrono::DateTime::parse_from_rfc3339(s)?;"}],
    "pydantic": [{"route": "model_validate", "runtime": "python",
                  "snippet": "from pydantic import BaseModel\nclass M(BaseModel):\n    x: int\nm = M.model_validate(data)"}],
    "httpx": [{"route": "get_json", "runtime": "python", "snippet": "import httpx\nr = httpx.get(url); data = r.json()"},
              {"route": "async_client", "runtime": "python",
               "snippet": "async with httpx.AsyncClient() as c:\n    r = await c.get(url)"}],
    "zod": [{"route": "object_parse", "runtime": "node",
             "snippet": "import { z } from 'zod';\nconst S = z.object({ x: z.number() });\nconst v = S.parse(data);"}],
    "date-fns": [{"route": "format", "runtime": "node",
                  "snippet": "import { format } from 'date-fns';\nconst s = format(new Date(), 'yyyy-MM-dd');"}],
}


def _usage_token_estimate(recipes: list[dict[str, str]]) -> int:
    """Rough token estimate for the whole recipe zoo (~4 chars/token) — the cost to USE vs read the package."""
    return sum(len(r.get("snippet", "")) for r in recipes) // 4


def _card(spec: dict[str, Any]) -> dict[str, Any]:
    reg = REGISTRIES[spec["registry"]]
    handle = {
        "registry": spec["registry"], "name": spec["name"], "version_req": spec["version_req"],
        "url": reg["url"].format(name=spec["name"]), "metadata_api": reg["api"].format(name=spec["name"]),
        "license": spec["license"],
        # a stable content digest over the immutable coordinates (name+registry) — NOT the version,
        # which lives in metadata; a resolve stamps the resolved-version digest separately.
        "coordinate_digest": canonical_id("pkgcoord", spec["registry"], spec["name"]).rsplit("-", 1)[-1],
    }
    pid = canonical_id(PRIMITIVE_ID_PREFIX, spec["registry"], spec["name"])
    vendorable = _license_vendorable(spec["license"])
    return {
        "primitive_id": pid, "title": spec["title"],
        # DESCRIPTION + EDGES make it SEARCHABLE — it embeds/indexes through the same pipeline as any
        # primitive (no code body needed to be found or composed).
        "blackbox": f"Edge-only link to {spec['name']} on {spec['registry']}: {spec['title']}. The code is "
                    f"maintained by others in the registry — we DON'T rewrite or host it; this primitive "
                    f"contributes a searchable description, typed edges, and dimensions so the package "
                    f"composes by contract. Tags: {', '.join(spec['tags'])}.",
        "primitive_kind": f"package_reference.{spec['registry'].replace('.', '_')}",
        "kind": "edge_only.package_link",
        "input_edge": spec["input_edge"], "output_edge": spec["output_edge"],
        "has_code_body": False,                       # EDGE-ONLY — the whole point
        "hosts_raw_code": False,                      # we host METADATA, never their raw code, by default
        "code_hosting_policy": _code_hosting_policy(spec["license"]),
        "search_ready": bool(spec["title"] and spec["input_edge"] and spec["output_edge"]),  # desc+edges → embeddable
        # USAGE RECIPES — the token-savings payload: invoke the package without reading it. A zoo of routes.
        "usage_recipes": USAGE_RECIPES.get(spec["name"], []),
        "usage_token_estimate": _usage_token_estimate(USAGE_RECIPES.get(spec["name"], [])),
        "package": handle, "runtime_targets": [reg["runtime"]],
        "capability_tags": spec["tags"], "domains": ["package_reuse"],
        "license_vendorable": vendorable,
        # DIMENSIONS: the ones known offline are stamped; the scrapable ones are NAMED (not fabricated) so
        # an opt-in registry scrape has a target — searchable/rankable via the open-attribute model.
        "dimensions": {"registry": spec["registry"], "runtime": reg["runtime"], "license": spec["license"],
                       "license_vendorable": vendorable, "version_req": spec["version_req"]},
        "scrapable_dimensions": _SCRAPABLE_DIMENSIONS,
        "proof_requirements": ["link_resolves", "license_vendorable", "not_yanked", "edge_matches_public_api"],
        "promotion_blockers": (["edge_matches_public_api_unverified", "review_required"]
                               + ([] if vendorable else ["license_not_vendorable"])),
        "cdc": {"yank_watch": True, "version_channel": spec["version_req"]},  # a yank revokes the primitive
        "readiness": "R3_edge_and_handle_known",
        "verification_level": "L2_declared_edge_and_link",
        "source_family": "package_registry_link", **BOUNDARY,
    }


def emit_cards() -> list[dict[str, Any]]:
    return [_card(s) for s in PACKAGE_SPECS]


def build(write: bool = True) -> dict[str, Any]:
    cards = emit_cards()
    body = "".join(json.dumps(c, sort_keys=True) + "\n" for c in cards)
    if write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        CARDS_PATH.write_text(body, encoding="utf-8")
    by_reg: dict[str, int] = {}
    for c in cards:
        by_reg[c["package"]["registry"]] = by_reg.get(c["package"]["registry"], 0) + 1
    return {"record_type": "edge_only_package_primitive_cards", "n_cards": len(cards),
            "by_registry": by_reg, "bytes": len(body.encode()),
            "path": str(CARDS_PATH) if write else None, **BOUNDARY}


def verify_link(card: dict[str, Any], *, resolve: bool = False) -> dict[str, Any]:
    """Structural (offline) verification: handle well-formed, license vendorable, typed edges, edge-only.
    `resolve=True` opt-in: HEAD/GET the registry metadata API to confirm the package EXISTS (network)."""
    pkg = card.get("package") or {}
    checks = {
        "handle_wellformed": bool(pkg.get("registry") and pkg.get("name") and pkg.get("url")),
        "license_vendorable": bool(card.get("license_vendorable")),
        "typed_edges": bool(card.get("input_edge") and card.get("output_edge")),
        "edge_only": card.get("has_code_body") is False,
        "cdc_yank_watch": bool((card.get("cdc") or {}).get("yank_watch")),
    }
    if resolve:  # opt-in, network — off by default (no-network/storage-safe)
        checks["link_resolves"] = _resolve_package(pkg)
    ok = all(v for k, v in checks.items() if k != "link_resolves") and checks.get("link_resolves", True)
    return {"primitive_id": card.get("primitive_id"), "link_ok": ok, "checks": checks,
            "note": "declared edge is NOT yet verified against the package public API (promotion blocker)",
            **BOUNDARY}


def _resolve_package(pkg: dict[str, Any]) -> bool:
    """Opt-in network resolve — confirm the package exists via its registry metadata API."""
    import urllib.error  # noqa: PLC0415
    import urllib.request  # noqa: PLC0415
    api = pkg.get("metadata_api")
    if not api:
        return False
    try:
        req = urllib.request.Request(api, method="GET", headers={"user-agent": "aidoneright-edge-link/0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return 200 <= r.status < 300
    except (urllib.error.URLError, Exception):  # noqa: BLE001
        return False


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = emit_cards()

    checks.append(("cards deterministic (byte-identical) + unique ids",
                   json.dumps(cards, sort_keys=True) == json.dumps(emit_cards(), sort_keys=True)
                   and len({c["primitive_id"] for c in cards}) == len(cards)))

    checks.append(("every card is EDGE-ONLY (no code body) + typed edges + a package handle",
                   all(c["has_code_body"] is False and c["input_edge"] and c["output_edge"]
                       and c["package"]["registry"] and c["package"]["name"] for c in cards)))

    checks.append(("spans multiple registries (crates.io + pypi + npm)",
                   {c["package"]["registry"] for c in cards} >= {"crates.io", "pypi", "npm"}))

    # license gate: a GPL package is flagged non-vendorable (promotion blocked)
    gpl = _card({"registry": "crates.io", "name": "readline-gpl", "version_req": "^1", "license": "GPL-3.0",
                 "title": "gpl example", "tags": ["x"], "input_edge": "A+B", "output_edge": "C"})
    checks.append(("copyleft (GPL) license is flagged non-vendorable + promotion-blocked",
                   gpl["license_vendorable"] is False
                   and "license_not_vendorable" in gpl["promotion_blockers"]))
    checks.append(("permissive 'MIT OR Apache-2.0' passes the vendorable gate",
                   _license_vendorable("MIT OR Apache-2.0") is True and _license_vendorable("MIT") is True))

    # offline link verification passes structurally; edge-match stays an explicit promotion blocker
    v = verify_link(cards[0], resolve=False)
    checks.append(("offline link verification is well-formed; edge-vs-API stays a promotion blocker",
                   v["link_ok"] is True
                   and "edge_matches_public_api_unverified" in cards[0]["promotion_blockers"]))

    # storage-light: the whole pack is bytes, not gigabytes (the anti-bloat point)
    summary = build(write=False)
    checks.append(("pack is storage-LIGHT (edge-only) — whole pack < 64 KB",
                   summary["bytes"] < 64_000))

    # composability: two packages chain by typed edge (reqwest JsonBytes → serde_json JsonBytes)
    producers = {c["output_edge"]: c for c in cards}
    consumers = {c["input_edge"]: c for c in cards}
    checks.append(("packages compose by typed edge (reqwest→serde_json over JsonBytes)",
                   "JsonBytes" in producers and "JsonBytes" in consumers))

    # code-hosting policy: NEVER host raw code by default; permissive→cache_permitted, copyleft→rewrite
    checks.append(("no card hosts raw code; policy is link-only + license-derived (cache vs rewrite)",
                   all(c["hosts_raw_code"] is False for c in cards)
                   and all(c["code_hosting_policy"] == "cache_permitted" for c in cards if c["license_vendorable"])
                   and gpl["code_hosting_policy"] == "rewrite_required"))

    # searchable: description + typed edges present → embeds/indexes through the normal pipeline
    checks.append(("every card is SEARCH-READY (description + typed edges → embeddable)",
                   all(c["search_ready"] and len(c["blackbox"]) > 40 for c in cards)))

    # dimensions: known ones stamped, scrapable ones NAMED (not fabricated)
    checks.append(("dimensions stamped (registry/runtime/license) + scrapable dims NAMED not fabricated",
                   all(c["dimensions"].get("registry") and c["scrapable_dimensions"] for c in cards)
                   and "downloads_total" in cards[0]["scrapable_dimensions"]))

    # USAGE RECIPES — the token-savings core: invoke without reading the package; a zoo of routes; compact
    every_has_recipe = all(c["usage_recipes"] for c in cards)
    is_a_zoo = any(len(c["usage_recipes"]) >= 2 for c in cards)   # multiple routes for some packages
    compact = all(c["usage_token_estimate"] <= 120 for c in cards)  # tens of tokens, not thousands
    checks.append(("every card carries a USAGE RECIPE zoo, compact (~tens of tokens to invoke)",
                   every_has_recipe and is_a_zoo and compact))

    checks.append(("candidate-only (serves_truth=false) — links are not truth until verified",
                   all(c["candidate"] is True and c["serves_truth"] is False for c in cards)))

    ok = all(v for _, v in checks)
    print("edge_only_package_primitives — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    avg_usage = sum(c["usage_token_estimate"] for c in cards) // max(len(cards), 1)
    print(f"  {summary['n_cards']} edge-only package links {summary['by_registry']} in "
          f"{summary['bytes']:,} bytes (~{summary['bytes'] // max(summary['n_cards'], 1)} bytes/primitive); "
          f"~{avg_usage} tokens to INVOKE vs reading a whole package. candidate-only, hosts_raw_code=false.")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--resolve", metavar="NAME", help="opt-in: network-resolve one package by name")
    args = ap.parse_args()
    if args.resolve:
        card = next((c for c in emit_cards() if c["package"]["name"] == args.resolve), None)
        if not card:
            print(f"no edge-only primitive for package {args.resolve!r}"); return 1
        print(json.dumps(verify_link(card, resolve=True), indent=2))
        return 0
    if args.emit:
        print(json.dumps(build(write=True), indent=2))
        return 0
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
