"""capability_classifier — classify a package into a capability class from its NAME, summary, AND API symbol
names, so it earns a canonical typed edge (and therefore composes).

Owner (2026-07-11): the semantic pass found 76/125 harvested cards `unclassified` → few composable edges.
Keyword-on-the-name matching is weak; the strongest signal is what the package's public functions are CALLED:
`dumps`→serialize, `loads`→deserialize, `connect`→database, `render`→template, `sha256`→crypto. This scores
keywords + symbol-verbs across all classes and picks the best above a threshold; reused by the harvester and by
a reclassify pass over the already-persisted corpus (cheap — no re-import). Deterministic. candidate-only.

    python3 scripts/capability_classifier.py --self-test
    python3 scripts/capability_classifier.py --reclassify        # upgrade the persisted harvest in place
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.edge_only_capability_templates import CAPABILITY_TEMPLATES

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

#: per class: name/summary KEYWORDS + API SYMBOL-VERBS (matched against the recipe symbols' leaf names).
#: Symbol-verbs are the strong signal — a package exposing `dumps`/`loads` IS (de)serialization whatever it's named.
CLASS_SIGNALS: dict[str, dict[str, list[str]]] = {
    "serialize": {"kw": ["serial", "json", "yaml", "toml", "msgpack", "encode", "marshal"],
                  "sym": ["dumps", "dump", "serialize", "to_json", "to_bytes", "encode", "write"]},
    "deserialize": {"kw": ["parse", "decode", "deserial", "load"],
                    "sym": ["loads", "load", "parse", "deserialize", "from_json", "from_slice", "read", "decode"]},
    "http_client": {"kw": ["http", "request", "url", "rest", "client", "fetch", "api", "web"],
                    "sym": ["get", "post", "put", "delete", "request", "fetch", "head", "session"]},
    "validate": {"kw": ["valid", "schema", "typing", "dataclass", "attrs", "marshmallow", "model"],
                 "sym": ["validate", "model_validate", "parse_obj", "is_valid", "check", "define", "field"]},
    "parse_text": {"kw": ["parse", "regex", "lexer", "token", "grammar", "markdown", "html", "syntax"],
                   "sym": ["search", "match", "findall", "compile", "sub", "tokenize", "lex", "highlight"]},
    "datetime": {"kw": ["date", "time", "calendar", "timezone", "cron", "schedule", "duration"],
                 "sym": ["now", "utcnow", "strftime", "strptime", "fromtimestamp", "parse_from_rfc3339"]},
    "concurrency": {"kw": ["async", "concurr", "thread", "await", "aio", "socket", "coroutine", "parallel"],
                    "sym": ["run", "spawn", "gather", "sleep", "create_task", "join", "acquire", "loop"]},
    "crypto_hash": {"kw": ["crypto", "hash", "hmac", "cipher", "sign", "jwt", "cert", "secure"],
                    "sym": ["sha256", "md5", "sha1", "hexdigest", "hmac", "encrypt", "decrypt", "sign", "verify"]},
    "encode": {"kw": ["base64", "codec", "charset", "encoding"],
               "sym": ["b64encode", "b64decode", "urlencode", "quote", "unquote"]},
    "compress": {"kw": ["compress", "gzip", "zlib", "brotli", "lz4", "zstd", "deflate", "archive"],
                 "sym": ["compress", "decompress", "gzip", "deflate", "inflate"]},
    "tabular": {"kw": ["csv", "table", "dataframe", "arrow", "parquet", "columnar"],
                "sym": ["DictReader", "reader", "read_csv", "DataFrame", "writer"]},
    "math_stats": {"kw": ["math", "stat", "numeric", "linalg", "probability"],
                   "sym": ["mean", "median", "stdev", "variance", "correlation", "quantile"]},
    "cli_parse": {"kw": ["cli", "argparse", "command", "option", "typer", "console"],
                  "sym": ["parse_args", "add_argument", "ArgumentParser", "Parser", "command", "argument"]},
    "logging": {"kw": ["logging", "logger", "log", "trace", "telemetry"],
                "sym": ["getLogger", "info", "debug", "warning", "error", "log", "span"]},
    "database": {"kw": ["database", "sql", "postgres", "sqlite", "mysql", "orm", "query", "redis", "mongo"],
                 "sym": ["connect", "execute", "cursor", "fetchall", "fetchone", "commit", "query"]},
    "template_render": {"kw": ["template", "render", "jinja", "mustache", "handlebars"],
                        "sym": ["render", "from_string", "Template", "Environment", "get_template"]},
    "config": {"kw": ["config", "settings", "dotenv", "environment"],
               "sym": ["ConfigParser", "from_env", "read", "getenv", "load_dotenv"]},
    "filesystem": {"kw": ["filesystem", "path", "directory", "walk", "glob", "file"],
                   "sym": ["Path", "glob", "walk", "exists", "read_text", "mkdir", "listdir"]},
    "embedding": {"kw": ["embedding", "embed", "vector", "sentence", "transformer", "model2vec"],
                  "sym": ["embed", "encode", "transform", "vectorize"]},
    "testing": {"kw": ["testing", "pytest", "unittest", "mock", "fixture", "assertion", "property"],
                "sym": ["assert_that", "fixture", "mock", "raises", "mark", "parametrize"]},
    "image": {"kw": ["image", "pillow", "picture", "graphics", "png", "jpeg"],
              "sym": ["open", "resize", "convert", "save", "thumbnail", "crop"]},
}
_MIN_SCORE = 2  # need at least this much evidence to assign a class (else honest None)


def _leaf(sym: str) -> str:
    return str(sym).split(".")[-1]


def classify(name: str, summary: str = "", symbols: Optional[list[str]] = None) -> dict[str, Any]:
    """Score every class by keyword + symbol-verb evidence; return the best above threshold (else None).
    Symbol matches weigh double (a package's function names describe what it DOES)."""
    tokens = set(re.findall(r"[a-z0-9]+", f"{name} {summary}".lower()))
    sym_leaves = {_leaf(s) for s in (symbols or [])}
    sym_lower = {s.lower() for s in sym_leaves}
    best_cls, best_score, ranked = None, 0, []
    for cls, sig in CLASS_SIGNALS.items():
        kw_hits = sum(1 for k in sig["kw"] if any(t == k or (len(k) >= 4 and t.startswith(k)) for t in tokens))
        sym_hits = sum(1 for v in sig["sym"] if v in sym_leaves or v.lower() in sym_lower)
        score = kw_hits + 2 * sym_hits
        if score:
            ranked.append((score, cls))
        if score > best_score:
            best_score, best_cls = score, cls
    ranked.sort(key=lambda x: (-x[0], x[1]))
    assigned = best_cls if best_score >= _MIN_SCORE else None
    return {"capability_class": assigned, "score": best_score, "has_template": assigned in CAPABILITY_TEMPLATES
            if assigned else False, "ranked": ranked[:3], **BOUNDARY}


def reclassify_corpus(path: Optional[Path] = None, *, write: bool = True) -> dict[str, Any]:
    """Upgrade the persisted harvest in place: classify from name+blackbox+symbols, set the class, re-derive
    canonical edges from the class template. Cheap — no package re-import. Deterministic."""
    from scripts.deterministic_edge_derivation import derive_edges  # noqa: PLC0415
    path = path or (_SBC / "data" / "dev-intel" / "edge_only_harvest" / "edge_only_harvested_cards.jsonl")
    if not path.exists():
        return {"error": "harvest not found", "path": str(path), **BOUNDARY}
    cards = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    before_unclassified = sum(1 for c in cards if not c.get("capability_class"))
    upgraded = 0
    for c in cards:
        syms = [s for r in c.get("usage_recipes", []) for s in r.get("symbols", [])]
        res = classify(c.get("package", {}).get("name", ""), c.get("blackbox", ""), syms)
        cls = res["capability_class"]
        if cls and cls != c.get("capability_class"):
            c["capability_class"] = cls
            if res["has_template"]:
                e = derive_edges(c.get("package", {}).get("name", ""), capability_class=cls)
                c["input_edge"], c["output_edge"] = e["input_edge"], e["output_edge"]
            upgraded += 1
    after_unclassified = sum(1 for c in cards if not c.get("capability_class"))
    if write and upgraded:
        path.write_text("".join(json.dumps(c, sort_keys=True) + "\n" for c in cards), encoding="utf-8")
    return {"cards": len(cards), "unclassified_before": before_unclassified,
            "unclassified_after": after_unclassified, "upgraded": upgraded,
            "classified_rate": round(1 - after_unclassified / max(len(cards), 1), 3), **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # SYMBOL-driven: a package named nothing-obvious but exposing dumps/loads → (de)serialize
    s = classify("zorp", "a data thing", ["zorp.dumps", "zorp.loads"])
    checks.append(("symbol verbs classify despite an opaque name (dumps/loads → serialize/deserialize)",
                   s["capability_class"] in ("serialize", "deserialize") and s["score"] >= 2))

    # database by symbols (connect/execute/cursor) even if the name doesn't say 'sql'
    db = classify("acmestore", "", ["acmestore.connect", "acmestore.execute", "acmestore.cursor"])
    checks.append(("connect/execute/cursor → database", db["capability_class"] == "database"))

    # http by both name + symbols
    http = classify("httpx", "HTTP client", ["httpx.get", "httpx.post"])
    checks.append(("httpx → http_client with a template (canonical edges available)",
                   http["capability_class"] == "http_client" and http["has_template"]))

    # crypto by hexdigest/sha256
    cr = classify("blake3", "hashing", ["blake3.hexdigest"])
    checks.append(("hashing symbols → crypto_hash", cr["capability_class"] == "crypto_hash"))

    # the fix for the original bug: 'runtime' must NOT classify as datetime (no time-symbol, no time-keyword-token)
    rt = classify("onnxruntime", "runtime for onnx models", ["onnxruntime.InferenceSession"])
    checks.append(("onnxruntime does NOT become datetime (token boundaries + symbols)",
                   rt["capability_class"] != "datetime"))

    # honest None when there's no signal
    none = classify("xyzzy", "a mysterious widget", ["xyzzy.frobnicate"])
    checks.append(("no signal → honest None (not a forced guess)", none["capability_class"] is None))

    # deterministic
    checks.append(("classify deterministic",
                   json.dumps(classify("httpx", "HTTP client", ["httpx.get"]), sort_keys=True)
                   == json.dumps(classify("httpx", "HTTP client", ["httpx.get"]), sort_keys=True)))

    # new classes exist with templates (logging/database/template_render/embedding/…)
    checks.append(("new capability classes have canonical-edge templates",
                   all(c in CAPABILITY_TEMPLATES for c in
                       ("logging", "database", "template_render", "config", "filesystem", "embedding", "testing", "image"))))

    ok = all(v for _, v in checks)
    print("capability_classifier — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    print(f"  {len(CLASS_SIGNALS)} classes (keyword + symbol-verb signals); {len(CAPABILITY_TEMPLATES)} have "
          f"canonical-edge templates. min_score={_MIN_SCORE}.")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--reclassify", action="store_true")
    args = ap.parse_args()
    if args.reclassify:
        print(json.dumps(reclassify_corpus(), indent=2, default=str))
        return 0
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
