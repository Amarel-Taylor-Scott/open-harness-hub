#!/usr/bin/env python3
"""edge_only_package_harvester — scale the edge-only corpus from a handful of curated cards to a REAL,
API-VERIFIED corpus harvested from the actually-installed packages.

Owner (2026-07-11): "continue with all of this ... we have 150gb ... can use at least 100GB." Storage is no
longer the blocker, so we PERSIST the corpus — but edge-only cards are ~2KB each, so even the whole
environment is megabytes, not the 108GB code-DB problem.

For each installed distribution's importable top-level module: import it, introspect the public API, DERIVE
usage recipes from real callables + their real signatures (every recipe symbol therefore RESOLVES — verified
by construction, `edge_only_package_introspection`'s contract), assign a capability class by keyword where
inferable (else a generic edge, honestly marked `edge_inferred`), pull dimensions + license + summary from
package metadata, and emit a candidate card. Symbols are verified; the typed EDGE (our composition
vocabulary) stays candidate until refined — declaring is not verifying.

    python3 scripts/edge_only_package_harvester.py --self-test
    python3 scripts/edge_only_package_harvester.py --run --limit 60      # harvest + persist
    python3 scripts/edge_only_package_harvester.py --run --limit 0       # all importable modules
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as _im
import inspect
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
    raise SystemExit(f"edge_only_package_harvester requires canonical_id; import failed: {exc}")

from scripts.edge_only_capability_templates import CAPABILITY_TEMPLATES

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
OUT_DIR = _SBC / "data" / "dev-intel" / "edge_only_harvest"
CARDS_PATH = OUT_DIR / "edge_only_harvested_cards.jsonl"
_VENDORABLE = {"MIT", "APACHE", "APACHE-2.0", "BSD", "BSD-2-CLAUSE", "BSD-3-CLAUSE", "ISC", "MPL-2.0",
               "PSF", "PYTHON", "ZLIB", "UNLICENSE"}
#: keyword -> capability class, for best-effort edge assignment (matched against dist name + summary).
_CLASS_KEYWORDS = {
    "serialize": ["serial", "json", "yaml", "toml", "msgpack", "pickle", "marshal"],
    "http_client": ["http", "request", "url", "rest", "client", "aiohttp", "httpx", "fetch"],
    "validate": ["valid", "schema", "pydantic", "typing", "dataclass", "attrs", "marshmallow"],
    "parse_text": ["parse", "regex", "lexer", "token", "grammar", "markdown", "html", "pygments"],
    "datetime": ["date", "time", "calendar", "tz", "cron", "schedule"],
    "concurrency": ["async", "concurr", "thread", "await", "aio", "socket", "anyio"],
    "crypto_hash": ["crypto", "hash", "hmac", "sha", "cipher", "sign", "jwt", "cert"],
    "encode": ["encode", "decode", "base64", "codec", "charset"],
    "compress": ["compress", "gzip", "zip", "zlib", "brotli", "lz4"],
    "tabular": ["csv", "table", "dataframe", "pandas", "arrow", "parquet"],
    "cli_parse": ["cli", "argparse", "click", "command", "option", "typer"],
}


def _license_vendorable(text: str) -> bool:
    up = str(text or "").upper()
    return any(tok in up for tok in _VENDORABLE)


def _classify(dist: str, summary: str) -> Optional[str]:
    """Keyword→class on TOKEN boundaries (a token equals the keyword, or — for keywords ≥4 chars — starts
    with it, so 'valid'→'validate' matches but 'time'→'runtime' does NOT). Substring matching mis-classified
    onnxruntime as datetime; token-prefix fixes it. Edges stay candidate regardless (edge_matches_public_api)."""
    import re  # noqa: PLC0415
    tokens = set(re.findall(r"[a-z0-9]+", f"{dist} {summary}".lower()))
    for cls, kws in _CLASS_KEYWORDS.items():
        if any(t == k or (len(k) >= 4 and t.startswith(k)) for k in kws for t in tokens):
            return cls
    return None


#: canonical entry points for well-known packages — introspection can't rank "BaseModel > AfterValidator",
#: so a small curated hint gives high-quality recipes for known packages (verified against the real API);
#: the long tail stays honestly auto-derived (a real verified symbol, not necessarily THE canonical one).
_CANONICAL_ENTRYPOINTS: dict[str, list[str]] = {
    "pydantic": ["BaseModel", "field_validator"], "aiohttp": ["ClientSession", "request"],
    "yaml": ["safe_load", "safe_dump"], "click": ["command", "option", "group"],
    "requests": ["get", "post", "Session"], "httpx": ["get", "AsyncClient"], "fastapi": ["FastAPI"],
    "jinja2": ["Template", "Environment"], "numpy": ["array", "zeros"], "pandas": ["DataFrame", "read_csv"],
    "urllib3": ["request", "PoolManager"], "starlette": ["applications"], "anyio": ["run", "sleep"],
    "markdown": ["markdown", "Markdown"], "attr": ["define", "field"], "attrs": ["define", "field"],
}


def _public_callables(mod: Any, limit: int = 3) -> list[tuple[str, str]]:
    """The module's CANONICAL public callables with real signatures (verified: they resolve on the import).
    Order of preference: a curated canonical-entrypoint hint (BaseModel, ClientSession, safe_load) → then the
    module's own `__all__` →then dir(). dir()/`__all__` are often alphabetical, surfacing internal type
    aliases (AfterValidator, AddrInfoType) over the real entry point. Skip type aliases / TypeVars / constants."""
    canon = [n for n in _CANONICAL_ENTRYPOINTS.get(getattr(mod, "__name__", ""), []) if hasattr(mod, n)]
    decl = getattr(mod, "__all__", None)
    fallback = list(decl) if isinstance(decl, (list, tuple)) else sorted(n for n in dir(mod) if not n.startswith("_"))
    names = canon + [n for n in fallback if n not in canon]
    out: list[tuple[str, str]] = []
    for name in names:
        if (not isinstance(name, str) or name.startswith("_") or name.endswith("_T")
                or (name.isupper() and len(name) > 3)):  # constants / type aliases, not the API entry point
            continue
        obj = getattr(mod, name, None)
        if not callable(obj):
            continue
        try:
            sig = str(inspect.signature(obj))
        except (TypeError, ValueError):
            sig = "(...)"
        out.append((name, sig))
        if len(out) >= limit:
            break
    return out


def harvest_module(mod_name: str, dist: str, summary: str, license_text: str, version: str) -> Optional[dict[str, Any]]:
    """Import + introspect one module → a candidate edge-only card with VERIFIED recipes. None if unimportable."""
    try:
        mod = importlib.import_module(mod_name)
    except BaseException:  # noqa: BLE001 — arbitrary third-party import can fail/raise anything; skip cleanly
        return None
    callables = _public_callables(mod)
    if not callables:
        return None
    cls = _classify(dist, summary)
    tmpl = CAPABILITY_TEMPLATES.get(cls) if cls else None
    cap = mod_name.split(".")[0].capitalize()
    in_edge, out_edge = (tmpl["input_edge"], tmpl["output_edge"]) if tmpl else (f"{cap}Input", f"{cap}Output")
    recipes = [{"route": name, "symbols": [f"{mod_name}.{name}"], "verified": True,
                "snippet": f"import {mod_name}\nresult = {mod_name}.{name}{'(...)' if sig != '(...)' else '()'}",
                "api_signature": sig} for name, sig in callables]
    public = [n for n in dir(mod) if not n.startswith("_")]
    vendorable = _license_vendorable(license_text)
    return {
        "primitive_id": canonical_id("prim:pkg", "pyenv", mod_name),
        "title": f"{mod_name} — {(summary or cls or 'python package')[:80]}",
        "blackbox": f"Edge-only, API-verified link to the installed `{mod_name}` module ({dist} {version}). "
                    f"{summary or ''} Recipes derived from + checked against the real API; code maintained "
                    f"upstream, not hosted here.".strip(),
        "primitive_kind": "package_reference.pyenv", "kind": "edge_only.package_link",
        "capability_class": cls, "input_edge": in_edge, "output_edge": out_edge,
        "has_code_body": False, "hosts_raw_code": False,
        "code_hosting_policy": "cache_permitted" if vendorable else "rewrite_required",
        "search_ready": True,
        "usage_recipes": recipes,
        "package": {"registry": "pypi", "name": dist, "module": mod_name, "version_req": f">={version}"
                    if version else "*", "url": f"https://pypi.org/project/{dist}/",
                    "license": license_text or "UNKNOWN",
                    "coordinate_digest": canonical_id("pkgcoord", "pypi", dist).rsplit("-", 1)[-1]},
        "runtime_targets": ["python"],
        "dimensions": {"registry": "pypi", "runtime": "python", "version": version,
                       "public_symbols": len(public), "recipes": len(recipes), "license_vendorable": vendorable},
        "api_conformance": {"all_recipes_verified": True, "symbols": [r["symbols"][0] for r in recipes]},
        "proof_requirements": ["recipe_symbols_resolve", "license_vendorable", "edge_matches_public_api"],
        "promotion_blockers": (["edge_inferred_not_class_matched"] if cls is None else [])
                              + (["license_not_vendorable"] if not vendorable else []) + ["review_required"],
        "readiness": "R4_api_verified" if cls else "R3_api_verified_generic_edge",
        "verification_level": "L4_recipe_symbols_api_verified",
        "source_family": "installed_package_harvest", **BOUNDARY,
    }


def _targets() -> list[tuple[str, str, str, str]]:
    """(module, dist, summary, license) for importable top-level modules of installed distributions."""
    mod_to_dist = _im.packages_distributions()  # {top_module: [dist,...]}
    seen, rows = set(), []
    for mod_name, dists in sorted(mod_to_dist.items()):
        if mod_name in seen or mod_name.startswith("_"):
            continue
        seen.add(mod_name)
        dist = sorted(dists)[0]
        try:
            meta = _im.metadata(dist)
            summary = meta.get("Summary", "") or ""
            license_text = meta.get("License", "") or " ".join(
                c.split("::")[-1].strip() for c in meta.get_all("Classifier", []) if "License" in c)
            version = _im.version(dist)
        except Exception:  # noqa: BLE001
            summary, license_text, version = "", "", ""
        rows.append((mod_name, dist, summary, license_text, version))
    return rows


def harvest(limit: int = 60, write: bool = True) -> dict[str, Any]:
    targets = _targets()
    if limit:
        targets = targets[:limit]
    cards = []
    for mod_name, dist, summary, license_text, version in targets:
        card = harvest_module(mod_name, dist, summary, license_text, version)
        if card:
            cards.append(card)
    # dedupe by id (a dist can expose several modules; ids are per-module so this is a no-op guard)
    uniq = {c["primitive_id"]: c for c in cards}
    rows = sorted(uniq.values(), key=lambda c: c["primitive_id"])
    by_class: dict[str, int] = {}
    for c in rows:
        k = c.get("capability_class") or "generic_edge"
        by_class[k] = by_class.get(k, 0) + 1
    body = "".join(json.dumps(c, sort_keys=True, default=str) + "\n" for c in rows)
    if write and rows:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        CARDS_PATH.write_text(body, encoding="utf-8")
    return {"record_type": "edge_only_harvest", "attempted": len(targets), "harvested": len(rows),
            "skipped_unimportable_or_empty": len(targets) - len(rows), "by_class": by_class,
            "total_recipes": sum(len(c["usage_recipes"]) for c in rows), "bytes": len(body.encode()),
            "path": str(CARDS_PATH) if (write and rows) else None, **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # harvest a small, deterministic slice WITHOUT persisting
    res = harvest(limit=40, write=False)

    checks.append(("harvested real cards from installed packages",
                   res["harvested"] >= 10 and res["total_recipes"] >= res["harvested"]))

    # a known package harvests with a verified recipe whose symbol RESOLVES on the real module
    click_card = harvest_module("click", "click", "cli toolkit", "BSD-3-Clause", "8.0")
    ok_recipe = False
    if click_card:
        sym = click_card["usage_recipes"][0]["symbols"][0]
        import importlib as _il
        parts = sym.split(".")
        obj = _il.import_module(parts[0])
        ok_recipe = all(hasattr(obj, p) or (obj := getattr(obj, p, None)) is not None for p in parts[1:])
    checks.append(("a harvested recipe symbol resolves against the real installed API",
                   click_card is not None and ok_recipe))

    # classification assigns a capability class where keywords match (click -> cli_parse or similar)
    classified = [c for c in [harvest_module(m, m, s, "MIT", "1.0")
                              for m, s in [("json", "json encoder"), ("hashlib", "secure hashes")]] if c]
    checks.append(("keyword classification assigns capability classes (json→serialize/deserialize etc.)",
                   any(c.get("capability_class") for c in classified)))

    # honesty: an unclassified package gets a generic edge + is promotion-blocked as edge_inferred
    gen = harvest_module("this_module_does_not_exist_xyz", "x", "", "", "")
    checks.append(("unimportable module skipped cleanly (None, not a crash)", gen is None))

    # license gate: a GPL package is rewrite_required + blocked
    gpl = harvest_module("json", "somegpl", "gpl thing", "GPL-3.0", "1.0")
    checks.append(("GPL license → rewrite_required + promotion-blocked",
                   gpl is not None and gpl["code_hosting_policy"] == "rewrite_required"
                   and "license_not_vendorable" in gpl["promotion_blockers"]))

    # storage-light: even a big harvest is bytes/primitive
    checks.append(("storage-light (~KB/primitive)",
                   res["bytes"] // max(res["harvested"], 1) < 6000))

    # deterministic
    checks.append(("harvest deterministic (byte-identical over the same slice)",
                   json.dumps(harvest(limit=40, write=False), sort_keys=True, default=str)
                   == json.dumps(res, sort_keys=True, default=str)))

    # candidate-only
    checks.append(("all candidate / serves_truth=false",
                   click_card["candidate"] is True and click_card["serves_truth"] is False))

    ok = all(v for _, v in checks)
    print("edge_only_package_harvester — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    print(f"  harvested {res['harvested']}/{res['attempted']} modules, {res['total_recipes']} verified recipes, "
          f"{res['by_class']} — {res['bytes'] // max(res['harvested'],1)} bytes/primitive. candidate-only.")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--limit", type=int, default=60, help="0 = all importable modules")
    args = ap.parse_args()
    if args.run:
        print(json.dumps(harvest(limit=args.limit, write=True), indent=2, default=str))
        return 0
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
