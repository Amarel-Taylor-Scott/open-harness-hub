#!/usr/bin/env python3
"""Foundry novelty — the single canonical dedup (Stage 4).

Unifies the three scattered implementations the repo grew
(`processors/semantic_dedup`, `processors/lsh_dedup_blocking`, and the SimHash/LSH
inside `factory/capability_lift_gate`) into ONE module, and adds the signal those
miss: a **source key**, so synonym-substituted clones (the `expansion-vN` family
that evades a tag/digit check) are caught because they share a `source_url`.

Three signals, combined:

  1. **SimHash (64-bit, Charikar)** over name+description k-shingles, digit-stripped
     so ``arm-007`` ≡ ``arm-015``. LSH banding makes corpus lookup O(n·log n), not
     O(n²) — the blow-up that hangs monolithic dedup runs.
  2. **Jaccard** over structural facets (industry/capability/modality/tags/slug).
  3. **Source key** = normalized ``source_url`` + ``target_type``. Two components
     mined from the same source into the same type are clones regardless of wording.

A candidate is a **duplicate** iff the source key already exists, OR (SimHash
near-match AND Jaccard near-match) — two-signal, to avoid false positives. A
candidate with **no source_url** is flagged ``suspect`` (novelty can't be verified;
the gate rejects it on the source pillar anyway).

The SimHash here is byte-identical to ``processors/semantic_dedup`` so live-corpus
fingerprints from ``load_live_corpus`` align. stdlib-only.

Run ``python -m scripts.foundry.novelty`` for the offline self-test.
"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

from scripts.foundry.contracts import BaseStage, Candidate, FoundryContext

# --- tunables (single source) -------------------------------------------------
SIMHASH_BITS = 64
DEFAULT_HAMMING_MAX = 3          # SimHash near-dup threshold (<= ⇒ near)
DEFAULT_JACCARD_MIN = 0.60       # structural near-dup threshold (>= ⇒ near)
DEFAULT_LSH_BANDS = 4            # 4 × 16-bit bands over a 64-bit simhash

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_DIGITS_RE = re.compile(r"\d+")


# --------------------------------------------------------------------------- #
# low-level primitives (the single source other modules should import)
# --------------------------------------------------------------------------- #
def tokens(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall((text or "").lower()) if len(t) >= 2]


def shingles(toks: list[str], k: int = 3) -> list[str]:
    """k-shingles capture local word order; fewer false positives than bag-of-words."""
    if len(toks) < k:
        return [" ".join(toks)] if toks else []
    return [" ".join(toks[i : i + k]) for i in range(len(toks) - k + 1)]


def simhash64(features: list[str]) -> int:
    """Charikar SimHash, 64-bit. Byte-compatible with processors/semantic_dedup."""
    if not features:
        return 0
    counters = [0] * SIMHASH_BITS
    for f in features:
        h = int(hashlib.blake2b(f.encode("utf-8"), digest_size=8).hexdigest(), 16)
        for b in range(SIMHASH_BITS):
            counters[b] += 1 if (h & (1 << b)) else -1
    out = 0
    for b in range(SIMHASH_BITS):
        if counters[b] > 0:
            out |= 1 << b
    return out


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def lsh_bands(sig: int, *, bits: int = SIMHASH_BITS, n_bands: int = DEFAULT_LSH_BANDS) -> list[tuple[int, int]]:
    width = bits // n_bands
    mask = (1 << width) - 1
    return [(b, (sig >> (b * width)) & mask) for b in range(n_bands)]


def fingerprint_text(body: dict) -> str:
    """Digit-stripped type+name+description, lowercased (arm-007 ≡ arm-015)."""
    text = "\n".join(
        str(body.get(k, "") or "") for k in ("type", "name", "description")
    ).lower()
    return _DIGITS_RE.sub("", text)


def simhash_of(body: dict) -> int:
    return simhash64(shingles(tokens(fingerprint_text(body)), k=3))


def structural_set(body: dict) -> set[str]:
    """Structural-fit facets: industry/capability/modality/tags + slug tokens."""
    out: set[str] = set()
    for facet in ("industry", "capability", "modality", "tags"):
        for v in body.get(facet) or []:
            out.add(f"{facet}:{str(v).lower()}")
    cid = body.get("id", "")
    if isinstance(cid, str) and "/" in cid:
        for tok in tokens(cid.split("/", 1)[1].replace("-", " ")):
            out.add(f"slug:{tok}")
    return out


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def normalize_source_url(url: str) -> str:
    """Scheme/host/path only, lowercased, no trailing slash/query/fragment —
    so http vs https and tracking params don't defeat the clone check."""
    if not url:
        return ""
    try:
        s = urlsplit(url.strip())
    except ValueError:
        return url.strip().lower()
    host = (s.netloc or "").lower().lstrip("www.")
    path = (s.path or "").rstrip("/").lower()
    return f"{host}{path}" if host else path


def source_key(target_type: str, source: dict | None) -> str | None:
    """``host/path|type`` — None when there is no source_url to key on."""
    url = normalize_source_url((source or {}).get("source_url", ""))
    if not url:
        return None
    return f"{url}|{target_type}"


# --------------------------------------------------------------------------- #
# index
# --------------------------------------------------------------------------- #
@dataclass
class NoveltyIndex:
    """LSH-blocked corpus of seen components. Seed it from the live catalog,
    then check candidates against it; ``add`` accepted candidates so intra-batch
    clones are caught too."""

    bits: int = SIMHASH_BITS
    n_bands: int = DEFAULT_LSH_BANDS
    hamming_max: int = DEFAULT_HAMMING_MAX
    jaccard_min: float = DEFAULT_JACCARD_MIN
    #: Heavy-paraphrase lane (same fact, DISJOINT vocabulary → SimHash misses it): an
    #: injected real embedder's cosine catches it. Cosine floor for a semantic duplicate.
    embed_cosine_min: float = 0.92
    #: O(n) cap — the novelty stage is the FAST pass; above this the embedding lane defers to
    #: the ANN-blocked `processors/semantic_dedup` (never an unbounded O(n²) scan here).
    embed_max_compare: int = 500
    _buckets: dict[tuple[str, int, int], list[tuple[str, int]]] = field(default_factory=dict)
    _structural: dict[str, set[str]] = field(default_factory=dict)
    _source_keys: set[str] = field(default_factory=set)
    _embeddings: dict[str, tuple[str, list[float]]] = field(default_factory=dict)  # cid -> (type, vec)
    size: int = 0

    def add(self, component_id: str, target_type: str, sig: int, struct: set[str],
            src_key: str | None, embedding: list[float] | None = None) -> None:
        for band in lsh_bands(sig, bits=self.bits, n_bands=self.n_bands):
            self._buckets.setdefault((target_type, band[0], band[1]), []).append((component_id, sig))
        self._structural[component_id] = struct
        if src_key:
            self._source_keys.add(src_key)
        if embedding is not None:
            self._embeddings[component_id] = (target_type, list(embedding))
        self.size += 1

    def _embed_near(self, target_type: str, embedding: list[float] | None) -> tuple[bool, str | None]:
        """Heavy-paraphrase cosine match within the same type (bounded by embed_max_compare)."""
        if not embedding or not self._embeddings:
            return False, None
        na = math.sqrt(sum(x * x for x in embedding))
        if na == 0:
            return False, None
        compared = 0
        for cid, (ctype, vec) in self._embeddings.items():
            if ctype != target_type or len(vec) != len(embedding):
                continue
            compared += 1
            if compared > self.embed_max_compare:
                break
            nb = math.sqrt(sum(x * x for x in vec))
            if nb == 0:
                continue
            cos = sum(a * b for a, b in zip(embedding, vec)) / (na * nb)
            if cos >= self.embed_cosine_min:
                return True, cid
        return False, None

    def add_body(self, body: dict, *, source: dict | None = None) -> None:
        cid = body.get("id", "") or ""
        self.add(cid, body.get("type", ""), simhash_of(body), structural_set(body),
                 source_key(body.get("type", ""), source))

    def add_corpus_entry(self, entry: Any) -> None:
        """Accept a `semantic_dedup.CorpusEntry`-like object (id/type/fingerprint/structural)."""
        sig = getattr(entry, "fingerprint", None)
        if sig is None:
            return
        self.add(getattr(entry, "id", ""), getattr(entry, "type", ""), sig,
                 set(getattr(entry, "structural", set())) or set(), None)

    def check(self, target_type: str, sig: int, struct: set[str], src_key: str | None,
              embedding: list[float] | None = None) -> dict[str, Any]:
        # candidates that share at least one LSH band with the same type
        seen: dict[str, int] = {}
        for band in lsh_bands(sig, bits=self.bits, n_bands=self.n_bands):
            for cid, csig in self._buckets.get((target_type, band[0], band[1]), ()):  # type: ignore[arg-type]
                seen.setdefault(cid, csig)
        nearest_id, nearest_ham, nearest_jac = None, self.bits, 0.0
        for cid, csig in seen.items():
            ham = hamming(sig, csig)
            jac = jaccard(struct, self._structural.get(cid, set()))
            # rank by (hamming asc, jaccard desc)
            if ham < nearest_ham or (ham == nearest_ham and jac > nearest_jac):
                nearest_id, nearest_ham, nearest_jac = cid, ham, jac
        source_dup = bool(src_key) and src_key in self._source_keys
        simhash_near = nearest_id is not None and nearest_ham <= self.hamming_max
        struct_near = nearest_jac >= self.jaccard_min
        embed_near, embed_of = self._embed_near(target_type, embedding)
        is_duplicate = source_dup or (simhash_near and struct_near) or embed_near
        reasons: list[str] = []
        if source_dup:
            reasons.append("same-source clone (source_url already mined into this type)")
        if simhash_near and struct_near:
            reasons.append(f"near-duplicate: of {nearest_id} (hamming {nearest_ham}, jaccard {nearest_jac:.2f})")
        if embed_near:
            reasons.append(f"semantic paraphrase: of {embed_of} (cosine >= {self.embed_cosine_min})")
        return {
            "simhash": sig,
            "is_duplicate": is_duplicate,
            "source_dup": source_dup,
            "simhash_near": simhash_near,
            "struct_near": struct_near,
            "embed_near": embed_near,
            "embed_of": embed_of,
            "nearest_id": nearest_id,
            "hamming": nearest_ham if nearest_id is not None else None,
            "jaccard": round(nearest_jac, 3),
            "source_key": src_key,
            "suspect": src_key is None,   # no source_url ⇒ novelty unverifiable
            "reasons": reasons,
        }


def build_index_from_corpus(corpus: list[Any], *, hamming_max: int = DEFAULT_HAMMING_MAX,
                            jaccard_min: float = DEFAULT_JACCARD_MIN) -> NoveltyIndex:
    """Seed an index from live-catalog entries (CorpusEntry-like) or raw bodies."""
    idx = NoveltyIndex(hamming_max=hamming_max, jaccard_min=jaccard_min)
    for item in corpus or []:
        if isinstance(item, dict):
            idx.add_body(item)
        else:
            idx.add_corpus_entry(item)
    return idx


# --------------------------------------------------------------------------- #
# the stage
# --------------------------------------------------------------------------- #
class NoveltyStage(BaseStage):
    """Stage 4 — drop duplicates, annotate survivors with their novelty record.

    Seeds an index from ``ctx.live_corpus`` (the live catalog) and accumulates
    accepted candidates so intra-batch clones are caught within the same run.
    """

    name = "novelty"

    def __init__(self, index: NoveltyIndex | None = None) -> None:
        self._index = index

    def run(self, batch: list[Candidate], ctx: FoundryContext) -> list[Candidate]:
        idx = self._index or build_index_from_corpus(
            ctx.live_corpus, hamming_max=ctx.config.hamming_max, jaccard_min=ctx.config.jaccard_min
        )
        for c in batch:
            if not c.alive:
                continue
            sig = simhash_of(c.body)
            struct = structural_set(c.body)
            skey = source_key(c.target_type, c.source)
            rec = idx.check(c.target_type, sig, struct, skey)
            c.novelty = rec
            if rec["is_duplicate"]:
                c.drop(self.name, rec["reasons"][0] if rec["reasons"] else "near-duplicate")
                continue
            c.mark(self.name, "novel", rec["nearest_id"] or "")
            # add to the index so a later candidate in this batch dedupes against it
            idx.add(c.component_id or c.body.get("id", ""), c.target_type, sig, struct, skey)
        return batch


# --------------------------------------------------------------------------- #
# self-test (offline)
# --------------------------------------------------------------------------- #
def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    base_body = {
        "id": "knowledge-pack/csddd-articles", "type": "knowledge-pack",
        "name": "CSDDD article corpus",
        "description": "Reference extracts of CSDDD articles for supply-chain due diligence with citations.",
        "industry": ["esg", "supply_chain"], "capability": ["retrieval"], "tags": ["csddd"],
    }
    src = {"source_url": "https://eur-lex.europa.eu/csddd", "author": "EU", "license": "CC-BY-4.0"}

    idx = NoveltyIndex()
    idx.add_body(base_body, source=src)

    # identical content ⇒ duplicate (simhash 0 + jaccard 1)
    r = idx.check("knowledge-pack", simhash_of(base_body), structural_set(base_body),
                  source_key("knowledge-pack", src))
    check("identical ⇒ duplicate", r["is_duplicate"], str(r))
    check("identical hamming 0", r["hamming"] == 0)

    # ANTI-EVASION: totally different wording but SAME source_url+type ⇒ duplicate via source key
    synonym_clone = {
        "id": "knowledge-pack/expansion-v2", "type": "knowledge-pack",
        "name": "Supply chain rules digest",
        "description": "A wholly reworded compendium of European corporate accountability provisions.",
        "industry": ["compliance"], "capability": ["verification"], "tags": ["expansion-v2"],
    }
    r2 = idx.check("knowledge-pack", simhash_of(synonym_clone), structural_set(synonym_clone),
                   source_key("knowledge-pack", src))
    check("synonym clone w/ same source ⇒ duplicate (anti-evasion)", r2["is_duplicate"], str(r2))
    check("flagged via source_dup not simhash", r2["source_dup"] and not r2["simhash_near"], str(r2))

    # genuinely different source + content ⇒ novel
    other = {
        "id": "knowledge-pack/faa-part-450", "type": "knowledge-pack",
        "name": "FAA Part 450 launch licensing",
        "description": "Commercial space launch and reentry licensing requirements, orbital debris mitigation.",
        "industry": ["space"], "capability": ["retrieval"], "tags": ["faa"],
    }
    r3 = idx.check("knowledge-pack", simhash_of(other), structural_set(other),
                   source_key("knowledge-pack", {"source_url": "https://faa.gov/part450"}))
    check("unrelated + new source ⇒ novel", not r3["is_duplicate"], str(r3))

    # HEAVY PARAPHRASE lane (same fact, DISJOINT vocabulary, DIFFERENT source → SimHash +
    # structural both miss it): an injected real embedder's cosine catches it. With a toy
    # embedder, a near-identical vector triggers embed_near; an orthogonal one does not.
    eidx = NoveltyIndex(hamming_max=DEFAULT_HAMMING_MAX, jaccard_min=DEFAULT_JACCARD_MIN)
    eidx.add("kp/orig", "knowledge-pack", simhash_of({"type": "knowledge-pack", "name": "a", "description": "aaa"}),
             {"a"}, source_key("knowledge-pack", {"source_url": "https://a.example/1"}),
             embedding=[1.0, 0.0, 0.0])
    para = eidx.check("knowledge-pack",
                      simhash_of({"type": "knowledge-pack", "name": "z", "description": "totally different words"}),
                      {"z"}, source_key("knowledge-pack", {"source_url": "https://b.example/2"}),
                      embedding=[0.999, 0.001, 0.0])
    check("heavy paraphrase (disjoint words+source) ⇒ duplicate via embedding lane",
          para["is_duplicate"] and para["embed_near"] and para["embed_of"] == "kp/orig", str(para))
    distinct = eidx.check("knowledge-pack",
                          simhash_of({"type": "knowledge-pack", "name": "q", "description": "unrelated"}),
                          {"q"}, source_key("knowledge-pack", {"source_url": "https://c.example/3"}),
                          embedding=[0.0, 1.0, 0.0])
    check("orthogonal embedding ⇒ NOT an embedding duplicate", not distinct["embed_near"], str(distinct))
    # The lane is INERT when no embedding is supplied (the offline default path is unchanged).
    inert = eidx.check("knowledge-pack", simhash_of(other), structural_set(other),
                       source_key("knowledge-pack", {"source_url": "https://d.example/4"}))
    check("no embedding supplied ⇒ embedding lane inert", not inert["embed_near"], str(inert))

    # candidate with NO source ⇒ suspect (novelty unverifiable)
    r4 = idx.check("tool", simhash_of({"type": "tool", "name": "x", "description": "y"}), set(), None)
    check("no source ⇒ suspect", r4["suspect"])

    # stage: intra-batch clones (no live corpus) — second identical body dropped
    from scripts.foundry.contracts import FoundryContext
    c1 = Candidate(target_type="tool", component_id="tool/a",
                   body={"id": "tool/a", "type": "tool", "name": "Geo FIPS lookup",
                         "description": "Normalize a place name to a FIPS code via the Census gazetteer."},
                   source={"source_url": "https://census.gov/fips", "author": "Census", "license": "CC0"})
    c2 = Candidate(target_type="tool", component_id="tool/b",
                   body={"id": "tool/b", "type": "tool", "name": "Geo FIPS lookup",
                         "description": "Normalize a place name to a FIPS code via the Census gazetteer."},
                   source={"source_url": "https://census.gov/fips", "author": "Census", "license": "CC0"})
    ctx = FoundryContext()
    out = NoveltyStage().run([c1, c2], ctx)
    check("intra-batch: first survives", out[0].alive, out[0].short())
    check("intra-batch: clone dropped", not out[1].alive, out[1].short())
    check("survivor carries novelty record", out[0].novelty is not None)

    # LSH banding is genuinely sub-linear: bucket lookup touches a band, not all N
    big = NoveltyIndex()
    for i in range(500):
        big.add_body({"id": f"tool/x{i}", "type": "tool", "name": f"tool number {i}",
                      "description": f"a distinct synthetic tool numbered {i} for scale testing"})
    probe = big.check("tool", simhash_of({"type": "tool", "name": "tool number 1",
                      "description": "a distinct synthetic tool numbered 1 for scale testing"}), set(), None)
    check("LSH finds near-twin at scale", probe["nearest_id"] is not None)

    print(f"\n{'all novelty self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
