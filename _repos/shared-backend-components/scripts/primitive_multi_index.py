#!/usr/bin/env python3
"""scripts.primitive_multi_index — index every primitive across NUMEROUS columns, not one. Each primitive is
decomposed into many searchable attributes and each attribute gets its own retrieval surfaces:

  * BASE textual columns (purpose · solution · input · output · mechanism · full) — each with a per-attribute
    SEMANTIC index (model2vec memmap matrix; search by input, by output, by purpose, ... independently or
    FUSED via search_multi) AND MinHash-LSH blocking at TWO granularities — SMALL (tight: 4 bands x 8 rows →
    near-duplicates, high precision) and LARGE (loose: 16 bands x 2 rows → loosely similar, high recall) —
    AND an EXACT token-set fingerprint key (formatting-invariant identity blocking);
  * BASE categorical columns (domain · tools · tags · pool · input_type · output_type · operations ·
    datatypes) — each with readable PER-TERM blocking keys (input_type/output_type keys are the RAW typed
    edge names, i.e. the composition join keys);
  * FACET columns loaded from EVERY ``vocabularies/*-role-matrix.yaml`` (the owner-supplied role
    decompositions: ML Engineer, AI-assisted Software/Platform/Data Engineer, ...) — lifecycle_stage,
    storage, compute, serving_pattern, model_family, math_area, industry, llm_assist_area, agent_primitive,
    saas_primitive, token_flow, ... — each facet is another column with per-term blocking keys. Adding a new
    role decomposition = adding a YAML file; the columns, blocks, and search surfaces follow with NO code
    change.

All blocking keys live in one indexed ``primitive_blocks`` table (attribute x granularity x band_key), so you
can block/cluster/dedupe/join on ANY column at ANY granularity with a single lookup — and across SEVERAL
columns at once with candidates_multi (union or intersect, ranked by cross-column agreement). The optional
``primitive_attribute_columns`` wide table materializes every column for direct SQL filtering. Deterministic
(shake_128-seeded MinHash lanes, no RNG), streamed, RESUMABLE (--append --chunk accumulates toward the full
multi-million-row database across flywheel ticks), scales without an LLM per card. The pgvector/faiss/
Postgres swap stays config-only. serves_truth=false.

    python3 scripts/primitive_multi_index.py --self-test
    python3 scripts/primitive_multi_index.py --facets                        # the loaded facet lexicons
    python3 scripts/primitive_multi_index.py --build-blocks [--limit N]      # fresh: columns + all block keys
    python3 scripts/primitive_multi_index.py --build-blocks --append --chunk 200000   # resume toward full DB
    python3 scripts/primitive_multi_index.py --build-columns --append --chunk 200000  # wide SQL column table
    python3 scripts/primitive_multi_index.py --build-semantic --attribute purpose
    python3 scripts/primitive_multi_index.py --build-semantic-all [--limit N]
    python3 scripts/primitive_multi_index.py --candidates <id> --attribute solution --granularity small
    python3 scripts/primitive_multi_index.py --candidates-multi <id> --attributes input_type,industry --mode intersect
    python3 scripts/primitive_multi_index.py --search "detect drift" --attribute solution --k 8
    python3 scripts/primitive_multi_index.py --search-multi "detect drift" --attributes purpose,solution,input
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
import hashlib  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import sqlite3  # noqa: E402
import struct  # noqa: E402
from typing import Any, Callable, Iterable, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
_SEM_DIRNAME = "primitive-semantic-index"
_N_PERM = 32
#: LSH granularities: (name, n_bands, rows_per_band). SMALL = tight (few candidates, near-dups); LARGE = loose.
_GRANULARITIES: tuple[tuple[str, int, int], ...] = (("small", 4, 8), ("large", 16, 2))
#: every blocking-key kind emitted into primitive_blocks. small/large = MinHash-LSH bands over textual columns;
#: exact = token-set fingerprint of a textual column; term = one readable key per canonical term of a
#: categorical/facet column (input_type/output_type term keys are the raw typed edge names).
BLOCK_KINDS: tuple[str, ...] = ("small", "large", "exact", "term")
_STOP = frozenset("a an the for of to in on with and or via using into from as is are be that this it one".split())
_ROLE_MATRIX_GLOB = "*-role-matrix.yaml"
#: mints the scheme fingerprint stored in the meta table so an --append against keys built under a different
#: attribute set / hash scheme fails loudly instead of silently mixing incompatible blocks.
_HASH_SCHEME = "shake128-lanes-v2"
_DEFAULT_CHUNK = 200_000  # rows per --append invocation: bounded flywheel tick, accumulates to the full DB
#: operation verbs recognized for the `operations` column (title-leading verbs of minted/foundry primitives).
_OP_VERBS = frozenset(
    "emit detect index rotate consume validate verify monitor transform normalize extract load sync route "
    "score rank embed classify cluster dedupe merge join filter aggregate encode decode parse render serve "
    "cache queue retry redact mask hash sign audit plan compile generate summarize translate migrate backfill "
    "replicate export import stream batch schedule scale deploy rollback retrain package register promote "
    "approve review label annotate sample split train evaluate calibrate explain compress chunk partition "
    "checkpoint reconcile screen enrich harvest mint remix compose search retrieve block".split())


# ── the BASE attribute columns — derived from a DB row (pool,title,blackbox,tags,input_edge,output_edge). ─────
def _attr_purpose(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> str:
    return title
def _attr_solution(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> str:
    return bb
def _attr_input(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> str:
    m = re.search(r"Input:\s*([^.]+)", bb)
    return f"{_uncamel(ie)} {m.group(1) if m else ''}".strip()
def _attr_output(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> str:
    m = re.search(r"Output:\s*([^.]+)", bb)
    return f"{_uncamel(oe)} {m.group(1) if m else ''}".strip()
def _attr_mechanism(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> str:
    return re.split(r"[.:]", bb, 1)[0]  # the first clause of the blackbox = the mechanism
def _attr_full(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> str:
    return f"{title} {bb}"

#: textual columns: LSH small+large + exact fingerprint + a per-attribute semantic index.
TEXTUAL_ATTRIBUTES: dict[str, Callable[..., str]] = {
    "purpose": _attr_purpose, "solution": _attr_solution, "input": _attr_input, "output": _attr_output,
    "mechanism": _attr_mechanism, "full": _attr_full,
}


def _terms_domain(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> list[str]:
    return [t.split(":", 1)[-1].replace("_", " ") for t in tags.split()
            if t.split(":", 1)[0] in ("domain", "industry", "entity", "op", "ml_stage", "ml_phase", "category")]
def _terms_tools(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> list[str]:
    return [t.split(":", 1)[-1] for t in tags.split() if t.split(":", 1)[0] in ("tool", "infra", "driver", "fork")]
def _terms_tags(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> list[str]:
    return tags.split()
def _terms_pool(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> list[str]:
    return [pool] if pool else []
def _terms_input_type(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> list[str]:
    return [ie] if ie else []  # the RAW typed edge name — the composition join key
def _terms_output_type(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> list[str]:
    return [oe] if oe else []
def _terms_operations(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> list[str]:
    toks = _tokens(f"{title} {bb}")
    return sorted({t for t in toks if t in _OP_VERBS})
def _terms_datatypes(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> list[str]:
    return sorted(set(_tokens(f"{_uncamel(ie)} {_uncamel(oe)}")))

#: categorical columns: readable per-term blocking keys (one block row per canonical term).
CATEGORICAL_ATTRIBUTES: dict[str, Callable[..., list[str]]] = {
    "domain": _terms_domain, "tools": _terms_tools, "tags": _terms_tags, "pool": _terms_pool,
    "input_type": _terms_input_type, "output_type": _terms_output_type,
    "operations": _terms_operations, "datatypes": _terms_datatypes,
}


def _uncamel(s: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s or "").replace("_", " ").lower()


# ── FACET columns from the role-matrix vocabularies (data seam: a new role decomposition = a new YAML). ──────
_FACET_CACHE: Optional[dict[str, dict[str, str]]] = None
_MATCHER_CACHE: Optional[tuple[dict, dict]] = None


def role_matrix_paths() -> list[Path]:
    return sorted(resource("vocabularies").glob(_ROLE_MATRIX_GLOB))


def load_facet_lexicons() -> dict[str, dict[str, str]]:
    """facet -> {surface form -> canonical term}, merged across every vocabularies/*-role-matrix.yaml.
    Global aliases attach to every facet that contains the alias's canonical term."""
    global _FACET_CACHE
    if _FACET_CACHE is not None:
        return _FACET_CACHE
    import yaml  # noqa: PLC0415
    facets: dict[str, dict[str, str]] = {}
    alias_maps: list[dict[str, str]] = []
    for path in role_matrix_paths():
        doc = yaml.safe_load(path.read_text()) or {}
        for facet, terms in (doc.get("facets") or {}).items():
            table = facets.setdefault(str(facet), {})
            for term in terms or []:
                canon = str(term).strip().lower()
                if canon:
                    table[canon] = canon
        alias_maps.append({str(a).strip().lower(): str(c).strip().lower()
                           for a, c in (doc.get("aliases") or {}).items()})
    for aliases in alias_maps:
        for alias, canon in aliases.items():
            for table in facets.values():
                if canon in table:
                    table[alias] = canon
    _FACET_CACHE = {f: facets[f] for f in sorted(facets)}
    return _FACET_CACHE


def _facet_word_tokens(text: str) -> list[str]:
    # facet matching keeps + (c++) and all stopwords so multi-word phrases like "a/b test" stay exact n-grams
    return re.findall(r"[a-z0-9+]+", (text or "").lower())


def _facet_matcher() -> tuple[dict, dict]:
    """(single: token -> {(facet, canonical)}, phrase: first-token -> [(facet, phrase-token-tuple, canonical)])"""
    global _MATCHER_CACHE
    if _MATCHER_CACHE is not None:
        return _MATCHER_CACHE
    single: dict[str, set[tuple[str, str]]] = {}
    phrase: dict[str, list[tuple[str, tuple[str, ...], str]]] = {}
    for facet, table in load_facet_lexicons().items():
        for surface, canon in table.items():
            toks = tuple(_facet_word_tokens(surface))
            if not toks:
                continue
            if len(toks) == 1:
                if len(toks[0]) > 1 and toks[0] not in _STOP:  # single-char/stopword surfaces are too noisy
                    single.setdefault(toks[0], set()).add((facet, canon))
            else:
                phrase.setdefault(toks[0], []).append((facet, toks, canon))
    _MATCHER_CACHE = (single, phrase)
    return _MATCHER_CACHE


def match_facets(text: str) -> dict[str, list[str]]:
    """facet -> sorted canonical terms found in the text (token + exact-phrase matching, alias-normalized)."""
    single, phrase = _facet_matcher()
    toks = _facet_word_tokens(text)
    found: dict[str, set[str]] = {}
    for i, tok in enumerate(toks):
        for facet, canon in single.get(tok, ()):
            found.setdefault(facet, set()).add(canon)
        for facet, ptoks, canon in phrase.get(tok, ()):
            if tuple(toks[i:i + len(ptoks)]) == ptoks:
                found.setdefault(facet, set()).add(canon)
    return {f: sorted(v) for f, v in sorted(found.items())}


def facet_attribute_names() -> list[str]:
    return list(load_facet_lexicons())


def all_attribute_names() -> list[str]:
    return list(TEXTUAL_ATTRIBUTES) + list(CATEGORICAL_ATTRIBUTES) + facet_attribute_names()


def extract_attribute_terms(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> dict[str, list[str]]:
    """Every CATEGORICAL + FACET column's canonical term list for one primitive row."""
    out = {name: fn(pool, title, bb, tags, ie, oe) for name, fn in CATEGORICAL_ATTRIBUTES.items()}
    facet_text = f"{title} {bb} {_uncamel(tags)} {_uncamel(ie)} {_uncamel(oe)}"
    matched = match_facets(facet_text)
    for facet in facet_attribute_names():
        out[facet] = matched.get(facet, [])
    return out


def extract_attributes(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> dict[str, str]:
    """ALL columns (textual + categorical + facet) as text — the numerous-columns view of one primitive."""
    out = {name: fn(pool, title, bb, tags, ie, oe) for name, fn in TEXTUAL_ATTRIBUTES.items()}
    for name, terms in extract_attribute_terms(pool, title, bb, tags, ie, oe).items():
        out[name] = "; ".join(terms)
    return out


# ── MinHash-LSH + fingerprints (deterministic; shake_128 lanes, no RNG) ───────────────────────────────────────
def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if t not in _STOP and len(t) > 1]


_LANE_CACHE: dict[str, tuple[int, ...]] = {}


def _token_lanes(token: str) -> tuple[int, ...]:
    """All _N_PERM MinHash lane values for one token from a single shake_128 draw (memoized: the token
    vocabulary is small relative to the corpus, so full-scale builds hash each distinct token once)."""
    lanes = _LANE_CACHE.get(token)
    if lanes is None:
        raw = hashlib.shake_128(token.encode()).digest(4 * _N_PERM)
        lanes = struct.unpack(f">{_N_PERM}I", raw)
        if len(_LANE_CACHE) < 2_000_000:  # bound memory on adversarially huge vocabularies
            _LANE_CACHE[token] = lanes
    return lanes


def minhash(tokens: Iterable[str], n_perm: int = _N_PERM) -> tuple[int, ...]:
    uniq = set(tokens)
    if not uniq:
        return tuple([0] * n_perm)
    sig = list(_token_lanes(uniq.pop()))[:n_perm]
    for t in uniq:
        lanes = _token_lanes(t)
        for i in range(n_perm):
            if lanes[i] < sig[i]:
                sig[i] = lanes[i]
    return tuple(sig)


def lsh_band_keys(sig: tuple[int, ...], n_bands: int, rows: int) -> list[str]:
    keys = []
    for b in range(n_bands):
        band = sig[b * rows:(b + 1) * rows]
        keys.append(hashlib.blake2b(struct.pack(f">{len(band)}I", *band), digest_size=8).hexdigest())
    return keys


def exact_fingerprint(tokens: Iterable[str]) -> str:
    """Order/formatting-invariant identity key: hash of the sorted unique token set."""
    return hashlib.blake2b(" ".join(sorted(set(tokens))).encode(), digest_size=8).hexdigest()


def block_rows(pool: str, title: str, bb: str, tags: str, ie: str, oe: str) -> list[tuple[str, str, int, str]]:
    """(attribute, granularity, band_index, band_key) rows for one primitive across EVERY column x key kind."""
    out: list[tuple[str, str, int, str]] = []
    for attr, fn in TEXTUAL_ATTRIBUTES.items():
        toks = _tokens(fn(pool, title, bb, tags, ie, oe))
        if not toks:
            continue
        sig = minhash(toks)
        for gname, nb, rows in _GRANULARITIES:
            for bi, key in enumerate(lsh_band_keys(sig, nb, rows)):
                out.append((attr, gname, bi, key))
        out.append((attr, "exact", 0, exact_fingerprint(toks)))
    for attr, terms in extract_attribute_terms(pool, title, bb, tags, ie, oe).items():
        for ti, term in enumerate(sorted(set(terms))):
            out.append((attr, "term", ti, term))
    return out


def _attributes_digest() -> str:
    spec = json.dumps([all_attribute_names(), list(BLOCK_KINDS), _GRANULARITIES, _N_PERM, _HASH_SCHEME])
    return hashlib.blake2b(spec.encode(), digest_size=8).hexdigest()


# ── build: the primitive_blocks table over the DB (fresh or resumable --append chunks) ───────────────────────
def _open_db(db_path: Optional[Path]) -> tuple[Optional[sqlite3.Connection], Optional[Path], Optional[str]]:
    from scripts.primitive_database import default_db_path  # noqa: PLC0415
    db_path = db_path or default_db_path()
    if not db_path.exists():
        return None, db_path, f"database not built: {db_path}"
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL")
    return con, db_path, None


def _meta_get(con: sqlite3.Connection, key: str) -> Optional[str]:
    try:
        row = con.execute("SELECT value FROM primitive_multi_index_meta WHERE key=?", (key,)).fetchone()
    except sqlite3.OperationalError:
        return None
    return row[0] if row else None


def _meta_set(con: sqlite3.Connection, **kv: Any) -> None:
    con.execute("CREATE TABLE IF NOT EXISTS primitive_multi_index_meta(key TEXT PRIMARY KEY, value TEXT)")
    con.executemany("INSERT OR REPLACE INTO primitive_multi_index_meta VALUES(?,?)",
                    [(k, str(v)) for k, v in kv.items()])


def build_blocks(db_path: Optional[Path] = None, *, limit: Optional[int] = None, append: bool = False,
                 chunk: Optional[int] = None) -> dict[str, Any]:
    """Fresh build (default: drops + rebuilds up to --limit rows) or --append (resumes from the stored cursor,
    processing --chunk more rows per call — the resumable path that accumulates toward the full database)."""
    con, db_path, err = _open_db(db_path)
    if err:
        return {"error": err, **BOUNDARY}
    digest = _attributes_digest()
    if append:
        stored = _meta_get(con, "blocks_attributes_digest")
        if stored is None:
            con.close()
            return {"error": "no resumable block build found — run a fresh --build-blocks first", **BOUNDARY}
        if stored != digest:
            con.close()
            return {"error": f"attribute/key scheme changed ({stored} -> {digest}) — rebuild fresh "
                             f"(--build-blocks without --append)", **BOUNDARY}
        start = int(_meta_get(con, "blocks_next_offset") or 0)
        n_rows = int(chunk or _DEFAULT_CHUNK)
        prior_blocks = int(_meta_get(con, "blocks_row_total") or 0)
    else:
        con.execute("DROP TABLE IF EXISTS primitive_blocks")
        con.execute("""CREATE TABLE primitive_blocks(
            primitive_id TEXT, attribute TEXT, granularity TEXT, band_index INTEGER, band_key TEXT)""")
        start, n_rows, prior_blocks = 0, int(limit or chunk or -1), 0
    sql = "SELECT primitive_id, pool, title, blackbox, tags, input_edge, output_edge FROM primitives ORDER BY rowid"
    sql += f" LIMIT {n_rows} OFFSET {start}" if n_rows >= 0 else ""
    batch: list[tuple] = []
    n = written = 0
    for pid, pool, title, bb, tags, ie, oe in con.execute(sql):
        for attr, gran, bi, key in block_rows(pool or "", title or "", bb or "", tags or "", ie or "", oe or ""):
            batch.append((str(pid), attr, gran, bi, key))
        n += 1
        if len(batch) >= 50000:
            con.executemany("INSERT INTO primitive_blocks VALUES(?,?,?,?,?)", batch)
            con.commit()
            written += len(batch)
            batch.clear()
    if batch:
        con.executemany("INSERT INTO primitive_blocks VALUES(?,?,?,?,?)", batch)
        written += len(batch)
    con.execute("CREATE INDEX IF NOT EXISTS ix_blocks_key ON primitive_blocks(attribute, granularity, band_key)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_blocks_pid ON primitive_blocks(primitive_id)")
    total_primitives = con.execute("SELECT COUNT(*) FROM primitives").fetchone()[0]
    _meta_set(con, blocks_attributes_digest=digest, blocks_next_offset=start + n,
              blocks_row_total=prior_blocks + written, blocks_hash_scheme=_HASH_SCHEME)
    con.commit()
    con.close()
    return {"mode": "append" if append else "fresh", "processed_this_run": n, "coverage_rows": start + n,
            "total_primitives": total_primitives, "block_rows": prior_blocks + written,
            "attributes": all_attribute_names(), "n_attributes": len(all_attribute_names()),
            "block_kinds": list(BLOCK_KINDS), "hash_scheme": _HASH_SCHEME, **BOUNDARY}


def build_columns(db_path: Optional[Path] = None, *, limit: Optional[int] = None, append: bool = False,
                  chunk: Optional[int] = None) -> dict[str, Any]:
    """Materialize the wide primitive_attribute_columns table — one row per primitive, one TEXT column per
    attribute (textual + categorical + facet) — for direct SQL filtering/grouping. Fresh or resumable."""
    con, db_path, err = _open_db(db_path)
    if err:
        return {"error": err, **BOUNDARY}
    names = all_attribute_names()
    digest = _attributes_digest()
    cols = ", ".join(f'"{c}" TEXT' for c in names)
    if append:
        stored = _meta_get(con, "columns_attributes_digest")
        if stored != digest:
            con.close()
            return {"error": "no matching resumable column build — run a fresh --build-columns first", **BOUNDARY}
        start, n_rows = int(_meta_get(con, "columns_next_offset") or 0), int(chunk or _DEFAULT_CHUNK)
    else:
        con.execute("DROP TABLE IF EXISTS primitive_attribute_columns")
        con.execute(f"CREATE TABLE primitive_attribute_columns(primitive_id TEXT PRIMARY KEY, {cols})")
        start, n_rows = 0, int(limit or chunk or -1)
    sql = "SELECT primitive_id, pool, title, blackbox, tags, input_edge, output_edge FROM primitives ORDER BY rowid"
    sql += f" LIMIT {n_rows} OFFSET {start}" if n_rows >= 0 else ""
    ins = (f'INSERT OR REPLACE INTO primitive_attribute_columns VALUES(?{",?" * len(names)})')
    batch, n = [], 0
    for pid, pool, title, bb, tags, ie, oe in con.execute(sql):
        attrs = extract_attributes(pool or "", title or "", bb or "", tags or "", ie or "", oe or "")
        batch.append((str(pid), *[attrs[c] for c in names]))
        n += 1
        if len(batch) >= 20000:
            con.executemany(ins, batch)
            con.commit()
            batch.clear()
    if batch:
        con.executemany(ins, batch)
    _meta_set(con, columns_attributes_digest=digest, columns_next_offset=start + n)
    con.commit()
    total = con.execute("SELECT COUNT(*) FROM primitive_attribute_columns").fetchone()[0]
    con.close()
    return {"mode": "append" if append else "fresh", "processed_this_run": n, "column_rows": total,
            "columns": ["primitive_id", *names], "n_columns": 1 + len(names), **BOUNDARY}


def candidates(primitive_id: str, *, attribute: str, granularity: str, db_path: Optional[Path] = None,
               limit: int = 50) -> list[str]:
    """Blocking candidates: other primitives sharing ANY band_key with this one on (attribute, granularity)."""
    from scripts.primitive_database import default_db_path  # noqa: PLC0415
    db_path = db_path or default_db_path()
    con = sqlite3.connect(str(db_path))
    rows = con.execute(
        "SELECT DISTINCT b2.primitive_id FROM primitive_blocks b1 JOIN primitive_blocks b2 "
        "ON b1.band_key=b2.band_key AND b1.attribute=b2.attribute AND b1.granularity=b2.granularity "
        "WHERE b1.primitive_id=? AND b1.attribute=? AND b1.granularity=? AND b2.primitive_id!=? LIMIT ?",
        (primitive_id, attribute, granularity, primitive_id, limit)).fetchall()
    con.close()
    return [r[0] for r in rows]


def candidates_multi(primitive_id: str, *, attributes: Optional[list[str]] = None, mode: str = "union",
                     granularities: Optional[list[str]] = None, db_path: Optional[Path] = None,
                     limit: int = 50) -> list[dict[str, Any]]:
    """Multi-column blocking: candidates sharing keys on SEVERAL attributes at once, ranked by how many
    distinct attributes agree. mode='intersect' keeps only candidates blocking on EVERY requested attribute."""
    from scripts.primitive_database import default_db_path  # noqa: PLC0415
    db_path = db_path or default_db_path()
    attrs = attributes or all_attribute_names()
    con = sqlite3.connect(str(db_path))
    conds, params = ["b1.primitive_id=?", "b2.primitive_id!=?"], [primitive_id, primitive_id]
    conds.append(f"b1.attribute IN ({','.join('?' * len(attrs))})")
    params.extend(attrs)
    if granularities:
        conds.append(f"b1.granularity IN ({','.join('?' * len(granularities))})")
        params.extend(granularities)
    having = "HAVING COUNT(DISTINCT b1.attribute) >= ?" if mode == "intersect" else ""
    sql = (f"SELECT b2.primitive_id, COUNT(DISTINCT b1.attribute) AS agreements "
           f"FROM primitive_blocks b1 JOIN primitive_blocks b2 "
           f"ON b1.band_key=b2.band_key AND b1.attribute=b2.attribute AND b1.granularity=b2.granularity "
           f"WHERE {' AND '.join(conds)} GROUP BY b2.primitive_id {having} "
           f"ORDER BY agreements DESC, b2.primitive_id LIMIT ?")
    if mode == "intersect":
        params.append(len(attrs))
    params.append(limit)
    rows = con.execute(sql, params).fetchall()
    con.close()
    return [{"primitive_id": r[0], "agreements": r[1], **BOUNDARY} for r in rows]


# ── per-attribute semantic indexes (numerous semantic indexes) + fused multi-attribute search ────────────────
def build_semantic(attribute: str, db_path: Optional[Path] = None, *, limit: Optional[int] = None) -> dict[str, Any]:
    """A model2vec memmap matrix over ONE textual attribute — a semantic index per column."""
    recs = build_semantic_many([attribute], db_path=db_path, limit=limit)
    return recs[0] if recs else {"error": "nothing built", **BOUNDARY}


def build_semantic_all(db_path: Optional[Path] = None, *, limit: Optional[int] = None) -> list[dict[str, Any]]:
    """Every textual attribute's semantic index in ONE streamed pass over the database."""
    return build_semantic_many(list(TEXTUAL_ATTRIBUTES), db_path=db_path, limit=limit)


def build_semantic_many(attributes: list[str], db_path: Optional[Path] = None, *,
                        limit: Optional[int] = None) -> list[dict[str, Any]]:
    import numpy as np  # noqa: PLC0415
    from scripts.capability_embedding import _load_model2vec  # noqa: PLC0415,SLF001
    bad = [a for a in attributes if a not in TEXTUAL_ATTRIBUTES]
    if bad:
        return [{"error": f"semantic indexes cover the textual columns {list(TEXTUAL_ATTRIBUTES)}; "
                          f"{bad} are categorical/facet columns — block on them with granularity='term'",
                 **BOUNDARY}]
    con, db_path, err = _open_db(db_path)
    if err:
        return [{"error": err, **BOUNDARY}]
    model = _load_model2vec()
    if model is None:
        con.close()
        return [{"error": "model2vec unavailable", **BOUNDARY}]
    n = con.execute("SELECT COUNT(*) FROM primitives").fetchone()[0]
    n = min(n, limit) if limit else n
    dim = int(np.asarray(model.encode(["probe"]), dtype="float32").shape[1])
    mats, ids = {}, []
    for attr in attributes:
        out_dir = resource("dist") / _SEM_DIRNAME / attr
        out_dir.mkdir(parents=True, exist_ok=True)
        mats[attr] = np.lib.format.open_memmap(out_dir / "embeddings.npy", mode="w+", dtype="float32",
                                               shape=(n, dim))
    sql = "SELECT primitive_id, pool, title, blackbox, tags, input_edge, output_edge FROM primitives ORDER BY rowid"
    if limit:
        sql += f" LIMIT {int(limit)}"
    texts: dict[str, list[str]] = {a: [] for a in attributes}
    bi_ids: list[str] = []
    row_i = 0

    def _flush() -> None:
        nonlocal row_i
        for attr in attributes:
            v = np.asarray(model.encode(texts[attr]), dtype="float32")
            nrm = np.linalg.norm(v, axis=1, keepdims=True)
            nrm[nrm == 0] = 1.0
            mats[attr][row_i:row_i + len(bi_ids)] = v / nrm
            texts[attr].clear()
        ids.extend(bi_ids)
        row_i += len(bi_ids)
        bi_ids.clear()

    for pid, pool, title, bb, tags, ie, oe in con.execute(sql):
        for attr in attributes:
            txt = TEXTUAL_ATTRIBUTES[attr](pool or "", title or "", bb or "", tags or "", ie or "", oe or "")
            texts[attr].append((txt or title or "")[:400])
        bi_ids.append(str(pid))
        if len(bi_ids) >= 4096:
            _flush()
    if bi_ids:
        _flush()
    con.close()
    recs = []
    for attr in attributes:
        mats[attr].flush()
        out_dir = resource("dist") / _SEM_DIRNAME / attr
        (out_dir / "ids.json").write_text(json.dumps(ids))
        recs.append({"attribute": attr, "index_dir": str(out_dir), "count": len(ids), "dim": dim, **BOUNDARY})
    return recs


def search_attribute(query: str, attribute: str, *, k: int = 8) -> list[dict[str, Any]]:
    import numpy as np  # noqa: PLC0415
    from scripts.capability_embedding import _load_model2vec  # noqa: PLC0415,SLF001
    d = resource("dist") / _SEM_DIRNAME / attribute
    if not (d / "embeddings.npy").exists():
        return []
    ids = json.loads((d / "ids.json").read_text())
    mat = np.load(d / "embeddings.npy", mmap_mode="r")
    q = np.asarray(_load_model2vec().encode([query]), dtype="float32")[0]
    q = q / (np.linalg.norm(q) or 1.0)
    best_s = np.full(k, -2.0, "float32"); best_i = np.full(k, -1, "int64")
    for start in range(0, mat.shape[0], 200000):
        sims = np.asarray(mat[start:start + 200000]) @ q
        for j in np.argpartition(-sims, min(k, sims.shape[0]) - 1)[:k]:
            if sims[j] > best_s[-1]:
                pos = np.searchsorted(-best_s, -sims[j])
                best_s = np.insert(best_s, pos, sims[j])[:k]; best_i = np.insert(best_i, pos, start + j)[:k]
    return [{"primitive_id": ids[int(i)], "score": round(float(s), 4), "attribute": attribute, **BOUNDARY}
            for s, i in zip(best_s, best_i) if i >= 0]


def rrf_fuse(ranklists: dict[str, list[str]], *, k: int = 8, c: int = 60) -> list[dict[str, Any]]:
    """Reciprocal-rank fusion across per-attribute ranklists (pure; the fused multi-column ranker)."""
    scores: dict[str, float] = {}
    hits: dict[str, list[str]] = {}
    for attr, pids in ranklists.items():
        for rank, pid in enumerate(pids):
            scores[pid] = scores.get(pid, 0.0) + 1.0 / (c + rank + 1)
            hits.setdefault(pid, []).append(attr)
    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
    return [{"primitive_id": pid, "score": round(s, 6), "matched_attributes": sorted(set(hits[pid])), **BOUNDARY}
            for pid, s in ordered]


def search_multi(query: str, *, attributes: Optional[list[str]] = None, k: int = 8) -> list[dict[str, Any]]:
    """Fused semantic search across SEVERAL per-attribute indexes at once (RRF over whichever exist on disk)."""
    attrs = attributes or list(TEXTUAL_ATTRIBUTES)
    ranklists = {a: [r["primitive_id"] for r in search_attribute(query, a, k=max(k * 3, 20))] for a in attrs}
    return rrf_fuse({a: pids for a, pids in ranklists.items() if pids}, k=k)


# ── self-test ─────────────────────────────────────────────────────────────────────────────────────────────────
def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    # facet lexicons load from EVERY role-matrix vocabulary (a new role doc = a new file, no code change)
    lex = load_facet_lexicons()
    checks.append(("loads >=2 role-matrix vocabularies with >=20 merged facets",
                   len(role_matrix_paths()) >= 2 and len(lex) >= 20))
    m = match_facets("xgboost fraud detection over kafka and postgres with a canary rollout and unit test")
    checks.append(("facet matching: model_family/industry/data_source phrases + alias postgres->postgresql",
                   "xgboost" in m.get("model_family", []) and "fraud detection" in m.get("industry", [])
                   and "kafka" in m.get("data_source", []) and "postgresql" in m.get("data_source", [])
                   and "unit test" in m.get("software_primitive", [])))
    # numerous columns: textual + categorical + facet, incl. raw typed-edge columns
    attrs = extract_attributes("grid", "Index invoices with an inverted index over postgres",
                               "uses an inverted index to index invoices over postgres. Input: invoice records. Output: a posting list.",
                               "op:index infra:postgres domain:finance tool:pandas", "InvoiceInput", "PostingResult")
    checks.append(("extracts numerous columns (>=25: textual + categorical + facets)",
                   set(attrs) == set(all_attribute_names()) and len(attrs) >= 25
                   and "invoice" in attrs["input"].lower() and "posting" in attrs["output"].lower()
                   and "finance" in attrs["domain"] and "postgres" in attrs["tools"]
                   and attrs["input_type"] == "InvoiceInput" and attrs["output_type"] == "PostingResult"
                   and "index" in attrs["operations"] and "postgresql" in attrs["data_source"]))
    # MinHash-LSH determinism + granularity behavior
    s1 = minhash(_tokens("detect data drift on serving inputs with a KS test"))
    s2 = minhash(_tokens("detect data drift on serving inputs with a KS test"))
    s3 = minhash(_tokens("rotate encryption keys in a hardware security module"))
    checks.append(("MinHash is deterministic (identical text -> identical signature)", s1 == s2))
    checks.append(("small (tight) blocks: identical share all 4 bands, disjoint share 0",
                   lsh_band_keys(s1, 4, 8) == lsh_band_keys(s2, 4, 8)
                   and not set(lsh_band_keys(s1, 4, 8)) & set(lsh_band_keys(s3, 4, 8))))
    checks.append(("large (loose) granularity yields MORE bands than small (more recall)",
                   len(lsh_band_keys(s1, 16, 2)) > len(lsh_band_keys(s1, 4, 8))))
    checks.append(("exact fingerprint is order/format-invariant and content-sensitive",
                   exact_fingerprint(["b", "a", "a"]) == exact_fingerprint(["a", "b"])
                   and exact_fingerprint(["a", "b"]) != exact_fingerprint(["a", "c"])))
    rows = block_rows("grid", "Detect drift", "KS drift monitor. Input: features. Output: alert.",
                      "op:monitor infra:kafka", "FeatureFrame", "DriftAlert")
    kinds = {r[1] for r in rows}
    checks.append(("block_rows emits ALL key kinds (small+large LSH, exact, per-term)",
                   kinds == set(BLOCK_KINDS)))
    checks.append(("typed-edge term keys are the RAW edge names (composition join keys)",
                   ("input_type", "term", 0, "FeatureFrame") in rows
                   and ("output_type", "term", 0, "DriftAlert") in rows))
    # pure fused ranker
    fused = rrf_fuse({"purpose": ["a", "b"], "solution": ["b", "c"]}, k=3)
    checks.append(("rrf_fuse ranks the cross-column agreer first and reports matched columns",
                   fused[0]["primitive_id"] == "b" and fused[0]["matched_attributes"] == ["purpose", "solution"]))
    # end-to-end over a fixture DB: fresh build, resumable append, single + multi-column candidates, columns
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "primitives.db"
        con = sqlite3.connect(str(db))
        con.execute("""CREATE TABLE primitives(primitive_id TEXT PRIMARY KEY, pool TEXT, title TEXT,
            blackbox TEXT, tags TEXT, input_edge TEXT, output_edge TEXT, serves_truth INTEGER)""")
        fixture = [
            ("a", "grid", "detect drift on inputs", "KS-test distribution drift monitor. Input: features. Output: alert.", "op:monitor", "FeatureFrame", "DriftAlert", 0),
            ("b", "grid", "detect drift on inputs (variant)", "KS-test distribution drift monitor. Input: features. Output: alert.", "op:monitor", "FeatureFrame", "DriftAlert", 0),
            ("c", "grid", "rotate keys", "HSM key rotation with envelope encryption. Input: keyset. Output: rotated keyset.", "op:encrypt", "KeySet", "RotatedKeySet", 0),
            ("d", "grid", "score drift severity", "Ranks drift alerts by severity. Input: alerts. Output: ranked alerts.", "op:rank", "DriftAlert", "RankedAlerts", 0)]
        con.executemany("INSERT INTO primitives VALUES(?,?,?,?,?,?,?,?)", fixture)
        con.commit(); con.close()
        rec = build_blocks(db_path=db, chunk=2)  # fresh, first 2 rows only
        rec2 = build_blocks(db_path=db, append=True, chunk=10)  # resume the rest
        checks.append(("fresh chunked build + --append resume covers the whole table via the stored cursor",
                       rec["coverage_rows"] == 2 and rec2["coverage_rows"] == 4
                       and rec2["block_rows"] > rec["block_rows"] and rec2["mode"] == "append"))
        con = sqlite3.connect(str(db))  # corrupt the stored scheme digest -> append must refuse, not mix
        con.execute("UPDATE primitive_multi_index_meta SET value='stale' WHERE key='blocks_attributes_digest'")
        con.commit(); con.close()
        refused = build_blocks(db_path=db, append=True, chunk=1)
        checks.append(("append refuses a changed key scheme instead of silently mixing blocks",
                       "error" in refused and "rebuild" in refused["error"]))
        build_blocks(db_path=db)  # restore: full fresh build for the candidate checks below
        cand = candidates("a", attribute="solution", granularity="small", db_path=db)
        checks.append(("LSH candidates: the near-duplicate 'b' blocks with 'a' on solution, 'c' does not",
                       "b" in cand and "c" not in cand))
        exact = candidates("a", attribute="solution", granularity="exact", db_path=db)
        checks.append(("exact-fingerprint blocking finds the identical-solution twin", "b" in exact))
        typed = candidates("a", attribute="input_type", granularity="term", db_path=db)
        checks.append(("typed-edge term blocking groups same-input-type primitives", typed == ["b"]))
        multi_u = candidates_multi("a", attributes=["solution", "input_type", "output_type"], mode="union", db_path=db)
        multi_i = candidates_multi("a", attributes=["solution", "input_type", "output_type"], mode="intersect", db_path=db)
        checks.append(("multi-column blocking: union ranks 'b' (3 agreements) first; intersect keeps ONLY 'b'",
                       multi_u and multi_u[0]["primitive_id"] == "b" and multi_u[0]["agreements"] == 3
                       and [r["primitive_id"] for r in multi_i] == ["b"]))
        crec = build_columns(db_path=db, chunk=3)
        crec2 = build_columns(db_path=db, append=True, chunk=10)
        checks.append(("wide column table materializes every attribute as a SQL column, resumably",
                       crec["n_columns"] == 1 + len(all_attribute_names()) and crec2["column_rows"] == 4))
        con = sqlite3.connect(str(db))
        got = con.execute('SELECT input_type, operations FROM primitive_attribute_columns '
                          'WHERE primitive_id=?', ("a",)).fetchone()
        con.close()
        checks.append(("SQL over the wide table returns per-column values",
                       got == ("FeatureFrame", "detect; monitor")))
    checks.append(("receipts carry the boundary", build_blocks(db_path=Path("/nope.db")).get("serves_truth") is False))
    checks.append(("semantic build refuses categorical columns with guidance (block on term keys instead)",
                   "error" in build_semantic("industry", db_path=Path("/nope.db"))))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - primitive_multi_index: {len(all_attribute_names())} columns per primitive "
          f"({len(TEXTUAL_ATTRIBUTES)} textual + {len(CATEGORICAL_ATTRIBUTES)} categorical + "
          f"{len(facet_attribute_names())} facet from {len(role_matrix_paths())} role-matrix vocabularies), "
          f"each with blocking keys across {list(BLOCK_KINDS)} plus per-attribute semantic indexes and fused "
          f"multi-column search. Deterministic, resumable, scalable. serves_truth=false.")
    return 0


def _print_receipt(rec: Any, name: str) -> int:
    out = resource("data") / "dev-intel" / "session_emulation" / f"{name}.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps(rec, indent=2, sort_keys=True))
    print(f"\nreceipt: {out}")
    bad = rec if isinstance(rec, dict) else (rec[0] if rec else {})
    return 1 if "error" in bad else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--facets", action="store_true", help="print the loaded facet lexicon summary")
    ap.add_argument("--build-blocks", action="store_true")
    ap.add_argument("--build-columns", action="store_true")
    ap.add_argument("--build-semantic", action="store_true")
    ap.add_argument("--build-semantic-all", action="store_true")
    ap.add_argument("--append", action="store_true", help="resume from the stored cursor (with --chunk rows)")
    ap.add_argument("--chunk", type=int, default=None)
    ap.add_argument("--attribute", default="purpose")
    ap.add_argument("--attributes", default=None, help="comma-separated column list for the multi variants")
    ap.add_argument("--granularity", default="small", choices=list(BLOCK_KINDS))
    ap.add_argument("--mode", default="union", choices=["union", "intersect"])
    ap.add_argument("--candidates", metavar="PRIMITIVE_ID", default=None)
    ap.add_argument("--candidates-multi", metavar="PRIMITIVE_ID", default=None)
    ap.add_argument("--search", metavar="QUERY", default=None)
    ap.add_argument("--search-multi", metavar="QUERY", default=None)
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)
    attrs = [a.strip() for a in args.attributes.split(",")] if args.attributes else None
    if args.self_test:
        return _self_test()
    if args.facets:
        lex = load_facet_lexicons()
        print(json.dumps({"role_matrix_files": [p.name for p in role_matrix_paths()],
                          "facets": {f: len(t) for f, t in lex.items()},
                          "all_columns": all_attribute_names(), **BOUNDARY}, indent=2, sort_keys=True))
        return 0
    if args.build_blocks:
        return _print_receipt(build_blocks(limit=args.limit, append=args.append, chunk=args.chunk),
                              "primitive_multi_index_receipt")
    if args.build_columns:
        return _print_receipt(build_columns(limit=args.limit, append=args.append, chunk=args.chunk),
                              "primitive_multi_index_columns_receipt")
    if args.build_semantic_all:
        return _print_receipt(build_semantic_all(limit=args.limit), "primitive_multi_index_semantic_receipt")
    if args.build_semantic:
        print(json.dumps(build_semantic(args.attribute, limit=args.limit), indent=2, sort_keys=True))
        return 0
    if args.candidates:
        for pid in candidates(args.candidates, attribute=args.attribute, granularity=args.granularity):
            print(" ", pid)
        return 0
    if args.candidates_multi:
        for r in candidates_multi(args.candidates_multi, attributes=attrs, mode=args.mode, limit=args.k):
            print(f"  {r['agreements']}  {r['primitive_id']}")
        return 0
    if args.search:
        for r in search_attribute(args.search, args.attribute, k=args.k):
            print(f"  {r['score']}  {r['primitive_id']}")
        return 0
    if args.search_multi:
        for r in search_multi(args.search_multi, attributes=attrs, k=args.k):
            print(f"  {r['score']}  {r['primitive_id']}  {','.join(r['matched_attributes'])}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
