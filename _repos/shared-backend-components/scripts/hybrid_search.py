#!/usr/bin/env python3
"""scripts.hybrid_search — TRULY hybrid, multi-attribute, vector+lexical search over registry records.

What the simple record_search lacked. Each record is decomposed into COLUMNS — name · tags · keywords · use_cases ·
labels · variations(spec) · enrichment — and indexed two ways:
  * VECTOR  (semantic) on the meaning-bearing columns (name, use_cases, spec, enrichment) — a deterministic lexical
    embedding (char-trigram signed hash, INDEX_DIM=256, OFFLINE + real; the SAME embed as
    _repos/teleon/backend/src/teleon/synthesis/component_search, which is pgvector-ready and swaps to a learned/nomic model via its port).
  * LEXICAL (keyword) token sets on ALL columns.
search() fuses per-column cosine + per-column token-overlap with per-column WEIGHTS (name highest) → one hybrid
score. Honest: vectors are the deterministic lexical floor today; semantic vectors (scripts/embeddings.Embedder /
nomic) + pgvector are the production swap (storage_tier_policy object_embedding stream). serves_truth=false.

  --self-test
  --index                 build the hybrid index from data/dev-intel/registry_records.jsonl
  --search "<query>" [-k N] [--explain]
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
RECORDS = _resource("data") / "dev-intel" / "registry_records.jsonl"
ENRICH = _resource("data") / "dev-intel" / "record_enrichments.jsonl"
INDEX = _resource("data") / "dev-intel" / "hybrid_index.json"
_WORD = re.compile(r"[a-z0-9]+")

try:                                                        # reuse the component_search embedding (pgvector-ready)
    sys.path.insert(0, str(_resource("src")))
    from teleon.synthesis.component_search import INDEX_DIM, embed as _embed  # type: ignore
except Exception:                                           # offline floor — same char-trigram signed-hash, hashlib (stable)
    import hashlib
    INDEX_DIM = 256

    def _embed(text: str) -> list[float]:
        v = [0.0] * INDEX_DIM
        s = re.sub(r"[^a-z0-9]+", " ", (text or "").lower())
        for i in range(max(1, len(s) - 2)):
            h = int(hashlib.md5(s[i:i + 3].encode()).hexdigest()[:8], 16)
            v[h % INDEX_DIM] += 1.0 if (h >> 8) & 1 else -1.0
        return v

#: the COLUMNS we search, and their weights (name highest). VEC = also semantically vectorized.
WEIGHTS = {"name": 3.0, "use_cases": 2.5, "tags": 2.0, "keywords": 2.0, "spec": 1.5, "enrichment": 1.5, "labels": 1.0}
VEC_COLUMNS = ("name", "use_cases", "spec", "enrichment")


def _toks(s: str) -> list[str]:
    return [t for t in _WORD.findall((s or "").lower()) if len(t) >= 2]


def columns(rec: dict, enrich: dict | None = None) -> dict[str, str]:
    """Decompose a record into searchable COLUMNS; merge enrich_loop's deterministic+LLM fields when present."""
    name = rec.get("name", "")
    tags = rec.get("searchability_tags", [])
    inline = (rec.get("enrichment") or {}).get("a", "")
    ef = (enrich or {}).get("fields", {})
    uc = (rec.get("capabilities", []) or []) + (ef.get("use_cases") or [])
    meta = " ".join([inline, ef.get("meta_description", ""), " ".join(ef.get("alternatives") or [])]).strip()
    return {
        "name": name,
        "tags": " ".join(tags),
        "keywords": " ".join(sorted(set(tags + _toks(name) + (ef.get("keywords") or [])))),
        "use_cases": " ".join(uc) + " " + meta,                                 # capabilities + LLM use_cases + meta
        "labels": " ".join([rec.get("object_type", ""), rec.get("registry", ""), rec.get("kind", ""),
                            rec.get("variant_axis", "")] + (ef.get("labels") or [])),
        "spec": rec.get("spec", ""),                                            # the variation's intent
        "enrichment": meta,
    }


def _norm(v: list[float]) -> float:
    return math.sqrt(sum(x * x for x in v)) or 1.0


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b)) / (_norm(a) * _norm(b))


def _read() -> list[dict]:
    if not RECORDS.exists():
        return []
    out = []
    for ln in RECORDS.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
    return out


def _load_enrich() -> dict:
    out: dict[str, dict] = {}
    if ENRICH.exists():
        for ln in ENRICH.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                try:
                    e = json.loads(ln)
                    out[e["record_id"]] = e               # last wins (most recent enrichment)
                except (json.JSONDecodeError, KeyError):
                    pass
    return out


def build_index(records: list[dict] | None = None) -> int:
    records = _read() if records is None else records
    enrich = _load_enrich()
    recs: dict[str, dict] = {}
    for rec in records:
        rid = rec.get("record_id")
        if not rid or not rec.get("name"):
            continue
        cols = columns(rec, enrich.get(rid))
        recs[rid] = {
            "meta": {"name": rec.get("name", ""), "type": rec.get("object_type", ""),
                     "registry": rec.get("registry", ""), "kind": rec.get("kind", "record")},
            "toks": {c: sorted(set(_toks(cols[c]))) for c in WEIGHTS},
            "vecs": {c: [round(x, 4) for x in _embed(cols[c])] for c in VEC_COLUMNS},
        }
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps({"dim": INDEX_DIM, "n": len(recs), "columns": list(WEIGHTS), "recs": recs},
                                separators=(",", ":")), encoding="utf-8")
    return len(recs)


def search(query: str, k: int = 10, explain: bool = False) -> list[dict]:
    if not INDEX.exists():
        build_index()
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    qt = set(_toks(query))
    qv = _embed(query)
    out = []
    for rid, rec in idx["recs"].items():
        per = {}
        total = 0.0
        for col, w in WEIGHTS.items():
            lex = (len(qt & set(rec["toks"].get(col, []))) / len(qt)) if qt else 0.0   # lexical overlap on the column
            vec = cosine(qv, rec["vecs"][col]) if col in VEC_COLUMNS else 0.0           # semantic on vector columns
            s = w * (0.6 * lex + 0.4 * max(vec, 0.0))
            if s:
                per[col] = round(s, 3)
            total += s
        if total > 0:
            row = {"record_id": rid, "score": round(total, 3), **rec["meta"]}
            if explain:
                row["by_column"] = dict(sorted(per.items(), key=lambda x: -x[1]))
            out.append(row)
    return sorted(out, key=lambda r: -r["score"])[:k]


def self_test() -> int:
    recs = [
        {"record_id": "r1", "kind": "record", "object_type": "tool", "name": "LangGraph agent orchestration",
         "registry": "tool_registry", "searchability_tags": ["langgraph", "agent", "graph"],
         "capabilities": ["orchestrate multi-agent workflows"], "source": {"seed": "github"}},
        {"record_id": "r2", "kind": "record", "object_type": "tool", "name": "email validation regex",
         "registry": "component", "searchability_tags": ["regex", "email", "validation"], "source": {"seed": "github"}},
        {"record_id": "v1", "kind": "variation", "object_type": "tool", "name": "LangGraph agent orchestration",
         "registry": "tool_registry", "searchability_tags": ["langgraph"], "variant_of": "r1",
         "spec": "deterministic cheaper variant that removes the LLM from routing", "variant_axis": "mutation"},
    ]
    cols = columns(recs[0])
    assert set(cols) == set(WEIGHTS) and "orchestrate" in cols["use_cases"], "columns incl. derived use_cases"
    assert len(_embed("hello world")) == INDEX_DIM and cosine(_embed("agent"), _embed("agent")) > 0.99, "embed+cosine"
    global INDEX
    orig = INDEX
    import tempfile
    try:
        INDEX = Path(tempfile.mkdtemp()) / "h.json"
        assert build_index(recs) == 3
        hits = search("multi-agent orchestration workflow", k=3, explain=True)
        assert hits[0]["record_id"] == "r1", f"semantic+lexical should rank the orchestration tool first: {hits[:2]}"
        assert "by_column" in hits[0] and hits[0]["by_column"], "explain shows per-column contributions"
        assert any(h["record_id"] == "r2" for h in search("email validation")), "regex record findable"
        assert any(h["record_id"] == "v1" for h in search("deterministic cheaper routing")), "variation findable by spec"
    finally:
        INDEX = orig
    print("hybrid_search self-test: OK (per-column decomposition, per-column vectors+lexical, weighted hybrid fusion, explain)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()

    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default

    if "--index" in argv:
        print(f"hybrid-indexed {build_index()} records ({len(VEC_COLUMNS)} vector columns + {len(WEIGHTS)} lexical) "
              f"→ {INDEX.relative_to(REPO)}"); return 0
    if "--search" in argv:
        for h in search(opt("--search") or "", int(opt("-k", "10")), explain="--explain" in argv):
            line = f"  [{h['score']}] {h['name'][:46]} ({h['type']}/{h['registry']})"
            if h.get("by_column"):
                line += "  via " + ",".join(f"{c}:{v}" for c, v in list(h["by_column"].items())[:3])
            print(line)
        return 0
    print("usage: hybrid_search.py --self-test | --index | --search '<q>' [-k N --explain]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
