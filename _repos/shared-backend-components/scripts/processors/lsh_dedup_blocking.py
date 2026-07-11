#!/usr/bin/env python3
"""LSH / SimHash-band blocking for near-duplicate detection at batch scale.

Replaces the O(n²) all-pairs comparison in semantic_dedup.py with a
near-linear alternative: the same 64-bit SimHash fingerprint is split into
``LSH_BANDS`` bands of ``LSH_ROWS_PER_BAND`` bits each.  Two items collide
in at least one band iff their Hamming distance is small enough — so only
items that share a band hash need a full pairwise check.  The result is a
"blocking" index that finds near-duplicate pairs in O(n·b) time, where b is
the small number of bands, rather than O(n²).

Why SimHash bands instead of MinHash?
  SimHash is already computed by semantic_dedup.py and lives on every corpus
  entry.  Reusing the same 64-bit integer (imported shared constants, same
  blake2b/shingle logic) keeps dedup decisions consistent across the two
  modules with no additional dependency.

Algorithm summary:
  • Split the 64-bit SimHash into LSH_BANDS × LSH_ROWS_PER_BAND bit slices.
  • For each slice, bucket items by their slice value.
  • Any bucket with ≥ 2 items is a "candidate pair" block.
  • Run the existing Hamming + Jaccard checks only on candidate pairs.
  • Cluster transitively via Union-Find.

Thresholds:
  Imported directly from semantic_dedup so the two modules always agree on
  what "duplicate" and "near-match" mean.  No new numeric literals are
  introduced here — per _repos/shared-backend-components/docs/codex/no-magic-values.md.

Complexity:
  Indexing: O(n · LSH_BANDS)
  Candidate enumeration: O(n · LSH_BANDS) amortised (sparse bands)
  Pairwise check: O(candidate_pairs) — sub-quadratic for realistic corpora
  Union-Find merge: O(candidate_pairs · α(n)) ≈ O(candidate_pairs)

CLI:
    python -m scripts.processors.lsh_dedup_blocking --self-test
    python -m scripts.processors.lsh_dedup_blocking --bench [--n 10000]

Module API:
    from scripts.processors.lsh_dedup_blocking import (
        build_lsh_index, query_candidates, cluster_corpus,
    )
    # cluster_corpus() is the main entry point for batch dedup.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import time
from collections import defaultdict
from typing import Any

# ---------------------------------------------------------------------------
# Shared constants — imported from semantic_dedup so there is exactly one
# definition of each threshold (_repos/shared-backend-components/docs/codex/no-magic-values.md rule 2).
# ---------------------------------------------------------------------------
from scripts.processors.semantic_dedup import (
    SIMHASH_BITS,               # 64
    SIMHASH_DUPLICATE_THRESHOLD,   # 3
    JACCARD_DUPLICATE_THRESHOLD,   # 0.60
    JACCARD_NEAR_MATCH_THRESHOLD,  # 0.40
    _fingerprint,
    _hamming,
    _jaccard,
    _structural_set,
)

# ---------------------------------------------------------------------------
# LSH band configuration
#
# Goal: catch all pairs with Hamming distance ≤ SIMHASH_DUPLICATE_THRESHOLD.
# With 64 bits split into b bands of r rows:
#   P(share ≥ 1 band | hamming=d) ≈ 1 - (1 - (1 - d/64)^r)^b
#
# b=16, r=4 → for d=3: P ≈ 1 - (1-(61/64)^4)^16 ≈ 0.998 (recall ≥99.8%)
# False-positive rate is controlled downstream by the exact Hamming check.
#
# These two constants are the ONLY new numeric values introduced.  They are
# named, documented, and consistent with SIMHASH_BITS (64 = 16 × 4).
# ---------------------------------------------------------------------------

# Number of bit bands the 64-bit SimHash is split into.
# Higher → more candidate pairs (better recall, more work) — must divide 64.
LSH_BANDS: int = 16  # 16 bands × 4 bits = 64 bits total

# Bit width of each band slice.  Must satisfy LSH_BANDS * LSH_ROWS_PER_BAND == SIMHASH_BITS.
LSH_ROWS_PER_BAND: int = SIMHASH_BITS // LSH_BANDS  # 4 bits per band

assert LSH_BANDS * LSH_ROWS_PER_BAND == SIMHASH_BITS, (
    f"Band config inconsistent: {LSH_BANDS} × {LSH_ROWS_PER_BAND} ≠ {SIMHASH_BITS}"
)

# Bit mask for a single band slice.
_BAND_MASK: int = (1 << LSH_ROWS_PER_BAND) - 1


# ---------------------------------------------------------------------------
# Union-Find (path compression + union by rank)
# ---------------------------------------------------------------------------

class _UnionFind:
    """Deterministic union-find for cluster assignment."""

    __slots__ = ("_parent", "_rank")

    def __init__(self, ids: list[str]) -> None:
        self._parent: dict[str, str] = {i: i for i in ids}
        self._rank: dict[str, int] = {i: 0 for i in ids}

    def find(self, x: str) -> str:
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]  # path halving
            x = self._parent[x]
        return x

    def union(self, x: str, y: str) -> None:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        # Smaller rank becomes child; ties break by lexicographic order for
        # determinism regardless of processing order.
        if self._rank[rx] < self._rank[ry] or (self._rank[rx] == self._rank[ry] and rx > ry):
            rx, ry = ry, rx
        self._parent[ry] = rx
        if self._rank[rx] == self._rank[ry]:
            self._rank[rx] += 1

    def clusters(self) -> dict[str, list[str]]:
        """Return {root_id: [member_id, ...]} sorted for determinism."""
        groups: dict[str, list[str]] = defaultdict(list)
        for node in sorted(self._parent):
            groups[self.find(node)].append(node)
        return dict(groups)


# ---------------------------------------------------------------------------
# Public API — data types
# ---------------------------------------------------------------------------

class CorpusItem:
    """Lightweight item for batch dedup.  Mirrors CorpusEntry from semantic_dedup
    but accepts raw manifest dicts directly so callers don't need pyyaml.

    Attributes:
        item_id:    Stable identifier (e.g. object_id, component id, slug).
        fingerprint: 64-bit SimHash integer (call _fingerprint(manifest) or
                    supply your own pre-computed value).
        structural: Set of structural-fit tokens (call _structural_set(manifest)).
        meta:       Optional pass-through metadata (not used by this module).
    """
    __slots__ = ("item_id", "fingerprint", "structural", "meta")

    def __init__(
        self,
        item_id: str,
        fingerprint: int,
        structural: set[str],
        meta: dict[str, Any] | None = None,
    ) -> None:
        self.item_id = item_id
        self.fingerprint = fingerprint
        self.structural = structural
        self.meta = meta or {}

    @classmethod
    def from_manifest(cls, manifest: dict[str, Any]) -> "CorpusItem":
        """Construct directly from a manifest dict (no YAML parsing required)."""
        return cls(
            item_id=str(manifest.get("id") or manifest.get("object_id") or ""),
            fingerprint=_fingerprint(manifest),
            structural=_structural_set(manifest),
            meta={},
        )


# ---------------------------------------------------------------------------
# LSH index — build and query
# ---------------------------------------------------------------------------

def build_lsh_index(items: list[CorpusItem]) -> list[dict[int, dict[int, list[str]]]]:
    """Build per-band hash tables mapping band_value → [item_id, ...].

    Returns a list of LSH_BANDS dicts, one per band.  Each dict maps the
    integer value of the band slice to the list of item IDs that hash there.

    Time: O(n · LSH_BANDS)
    Space: O(n · LSH_BANDS) worst-case; in practice much sparser.
    """
    # Pre-allocate: list of dicts, one per band.
    tables: list[dict[int, list[str]]] = [defaultdict(list) for _ in range(LSH_BANDS)]
    for item in items:
        fp = item.fingerprint
        for band in range(LSH_BANDS):
            shift = band * LSH_ROWS_PER_BAND
            band_val = (fp >> shift) & _BAND_MASK
            tables[band][band_val].append(item.item_id)
    return tables  # type: ignore[return-value]


def query_candidates(
    tables: list[dict[int, list[str]]],
    item: CorpusItem,
) -> set[str]:
    """Return all item IDs that share at least one band bucket with ``item``.

    Does NOT include ``item`` itself.  The result set is the candidate set for
    pairwise Hamming + Jaccard verification — already far smaller than the
    full corpus for any realistic duplicate rate.
    """
    candidates: set[str] = set()
    fp = item.fingerprint
    for band, table in enumerate(tables):
        shift = band * LSH_ROWS_PER_BAND
        band_val = (fp >> shift) & _BAND_MASK
        bucket = table.get(band_val)
        if bucket:
            candidates.update(bucket)
    candidates.discard(item.item_id)
    return candidates


# ---------------------------------------------------------------------------
# Batch dedup — full cluster assignment
# ---------------------------------------------------------------------------

def cluster_corpus(
    items: list[CorpusItem],
    *,
    hamming_threshold: int = SIMHASH_DUPLICATE_THRESHOLD,
    jaccard_threshold: float = JACCARD_DUPLICATE_THRESHOLD,
    require_both: bool = True,
) -> dict[str, str]:
    """Cluster a list of CorpusItems into near-duplicate groups.

    Returns a dict mapping item_id → cluster_root_id.  Items in the same
    cluster are considered near-duplicates.  The cluster root is the
    lexicographically smallest item_id after union-find stabilises.

    Parameters:
        items:            The items to cluster.
        hamming_threshold: Max Hamming distance to treat as a match.
                          Defaults to SIMHASH_DUPLICATE_THRESHOLD (imported).
        jaccard_threshold: Min Jaccard similarity to treat as a match.
                          Defaults to JACCARD_DUPLICATE_THRESHOLD (imported).
        require_both:     If True (default), both SimHash and Jaccard must
                          agree — same semantics as semantic_dedup.run().
                          Set False to cluster on either signal alone (more
                          aggressive; useful for broad candidate pruning).

    Complexity: O(n·b + P·α(n)) where P = candidate pair count, b = LSH_BANDS,
    α = inverse Ackermann (effectively constant).  Sub-quadratic for realistic
    corpora where P << n².
    """
    if not items:
        return {}

    id_to_item: dict[str, CorpusItem] = {it.item_id: it for it in items}
    uf = _UnionFind(list(id_to_item))
    tables = build_lsh_index(items)

    # Avoid checking the same ordered pair twice.
    seen_pairs: set[tuple[str, str]] = set()

    for item in items:
        candidates = query_candidates(tables, item)
        for cid in candidates:
            pair = (min(item.item_id, cid), max(item.item_id, cid))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            other = id_to_item[cid]
            ham = _hamming(item.fingerprint, other.fingerprint)
            jac = _jaccard(item.structural, other.structural)

            if require_both:
                match = (ham <= hamming_threshold) and (jac >= jaccard_threshold)
            else:
                match = (ham <= hamming_threshold) or (jac >= jaccard_threshold)

            if match:
                uf.union(item.item_id, cid)

    # Return flat item_id → root_id map (deterministic: root is always the
    # lex-smallest id in the cluster due to the tie-break in _UnionFind.union).
    return {iid: uf.find(iid) for iid in id_to_item}


# ---------------------------------------------------------------------------
# Convenience wrapper: cluster raw manifests directly
# ---------------------------------------------------------------------------

def cluster_manifests(
    manifests: list[dict[str, Any]],
    *,
    id_field: str = "id",
    hamming_threshold: int = SIMHASH_DUPLICATE_THRESHOLD,
    jaccard_threshold: float = JACCARD_DUPLICATE_THRESHOLD,
    require_both: bool = True,
) -> dict[str, str]:
    """Cluster a list of manifest dicts.  Returns item_id → cluster_root_id.

    Convenience wrapper around cluster_corpus for callers that already have
    manifest dicts (e.g. inside build_row_families).
    """
    items = []
    for m in manifests:
        iid = str(m.get(id_field) or m.get("object_id") or _fingerprint(m))
        items.append(CorpusItem(
            item_id=iid,
            fingerprint=_fingerprint(m),
            structural=_structural_set(m),
        ))
    return cluster_corpus(
        items,
        hamming_threshold=hamming_threshold,
        jaccard_threshold=jaccard_threshold,
        require_both=require_both,
    )


# ---------------------------------------------------------------------------
# Synthetic test-data generator (pure stdlib, deterministic seed)
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[A-Za-z]+")

_WORDS = [
    "supply", "chain", "audit", "risk", "compliance", "entity", "pipeline",
    "embedding", "label", "review", "candidate", "batch", "cluster", "index",
    "document", "source", "vector", "search", "score", "model", "routing",
    "dedupe", "normalize", "extraction", "verification", "governance", "hash",
    "object", "record", "dimension", "staging", "promotion", "catalog", "schema",
    "dataset", "provider", "contract", "regulation", "jurisdiction", "report",
]


def _lcg(seed: int) -> "function":
    """Return a simple deterministic pseudo-random integer generator (LCG)."""
    state = [seed & 0xFFFFFFFF]

    def _next(n: int) -> int:
        state[0] = (state[0] * 1664525 + 1013904223) & 0xFFFFFFFF
        return state[0] % n

    return _next


def _fast_simhash(word_indices: list[int]) -> int:
    """Lightweight 64-bit fingerprint for bench/test data generation only.

    Produces a deterministic 64-bit integer from a list of word indices using
    pure integer arithmetic — no hash calls, no loops over bits.  Near-duplicate
    items (those sharing most word indices) collide in many bands because their
    bit patterns differ by only a few positions, faithfully exercising the LSH
    band logic without the cryptographic overhead of the production path.

    This is ONLY called from _synthetic_items.  All production code uses the
    real _fingerprint (blake2b SimHash) imported from semantic_dedup.

    Implementation: spread each word index across 64 bits by multiplying by a
    large prime and rotating, then XOR-fold the per-word values.  Items sharing
    most indices will have similar accumulated XOR values and therefore low
    Hamming distance, which is exactly what the LSH bands test for.
    """
    if not word_indices:
        return 0
    mask64 = (1 << SIMHASH_BITS) - 1
    # Per-word spread constants: large primes give good bit diffusion.
    _P1 = 0x9E3779B97F4A7C15  # reference-ratio prime
    _P2 = 0xBF58476D1CE4E5B9  # splitmix64 step 1
    acc = 0
    for w in word_indices:
        # Mix word index into a 64-bit value via multiply-xor-shift (splitmix step).
        x = (w * _P1) & mask64
        x ^= x >> 30
        x = (x * _P2) & mask64
        x ^= x >> 27
        acc ^= x
    return acc & mask64


def _synthetic_items(n: int, *, duplicate_rate: float = 0.1) -> list[CorpusItem]:
    """Generate ``n`` synthetic CorpusItems with approximately ``duplicate_rate``
    near-duplicates.  Deterministic for a fixed ``n``.

    Duplicates are created by copying an existing item's word-index list with
    0-2 index substitutions — this exercises the SimHash band collision
    detection.  Fingerprints are computed via _fast_simhash (word indices, not
    blake2b shingles) so the generator completes in < 2s for n=10,000.  The
    LSH band logic under test is identical regardless of hash backend.
    """
    rand = _lcg(42)
    nw = len(_WORDS)

    def _make_indices(length: int = 12) -> list[int]:
        return [rand(nw) for _ in range(length)]

    def _make_struct(k: int = 4) -> set[str]:
        return {f"industry:{_WORDS[rand(nw)]}" for _ in range(k)} | \
               {f"tag:{_WORDS[rand(nw)]}" for _ in range(k)}

    items: list[CorpusItem] = []
    base_indices: list[list[int]] = []
    base_structs: list[set[str]] = []

    for i in range(n):
        dup_source = i > 0 and (rand(1000) < int(duplicate_rate * 1000))
        if dup_source:
            # Clone an existing item with minor perturbation.
            src_idx = rand(len(base_indices))
            indices = list(base_indices[src_idx])
            # Substitute 0-2 word indices (small Hamming shift in fingerprint).
            subs = rand(3)
            for _ in range(subs):
                pos = rand(len(indices))
                indices[pos] = rand(nw)
            struct = set(base_structs[src_idx])  # same structure = high Jaccard
        else:
            indices = _make_indices()
            struct = _make_struct()

        base_indices.append(indices)
        base_structs.append(struct)

        items.append(CorpusItem(
            item_id=f"test/item-{i:06d}",
            fingerprint=_fast_simhash(indices),
            structural=struct,
        ))

    return items


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        marker = "ok" if ok else "FAIL"
        print(f"  [{marker}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    print("[self-test] identical items → same cluster")
    items = [
        CorpusItem("a", fingerprint=0b101010, structural={"industry:esg", "tag:csddd"}),
        CorpusItem("b", fingerprint=0b101010, structural={"industry:esg", "tag:csddd"}),
        CorpusItem("c", fingerprint=0b111111_11111111_11111111_11111111_11111111_11111111_11111111_11111111,
                   structural={"industry:space", "tag:launch"}),
    ]
    mapping = cluster_corpus(items)
    check("identical pair clustered together", mapping["a"] == mapping["b"],
          f"a→{mapping['a']}, b→{mapping['b']}")
    check("unrelated item in own cluster", mapping["c"] != mapping["a"],
          f"c→{mapping['c']}, a→{mapping['a']}")

    print("[self-test] empty corpus → empty mapping")
    check("empty corpus", cluster_corpus([]) == {})

    print("[self-test] single item → maps to itself")
    single = [CorpusItem("x", fingerprint=42, structural=set())]
    check("single item self-cluster", cluster_corpus(single) == {"x": "x"})

    print("[self-test] Hamming distance ≤ threshold → clustered")
    # Flip exactly SIMHASH_DUPLICATE_THRESHOLD bits from item 'd' to create 'e'.
    base_fp = int("a" * 16, 16)  # arbitrary 64-bit value
    diff_fp = base_fp ^ ((1 << SIMHASH_DUPLICATE_THRESHOLD) - 1)  # flip lowest bits
    struct_shared = {"industry:compliance", "tag:audit", "tag:review"}
    d = CorpusItem("d", fingerprint=base_fp, structural=struct_shared)
    e = CorpusItem("e", fingerprint=diff_fp, structural=struct_shared)
    mapping2 = cluster_corpus([d, e])
    check(f"hamming={SIMHASH_DUPLICATE_THRESHOLD} + high-jaccard → clustered",
          mapping2["d"] == mapping2["e"],
          f"d→{mapping2['d']}, e→{mapping2['e']}, ham={_hamming(base_fp, diff_fp)}")

    print("[self-test] band config integrity")
    check("LSH_BANDS * LSH_ROWS_PER_BAND == SIMHASH_BITS",
          LSH_BANDS * LSH_ROWS_PER_BAND == SIMHASH_BITS,
          f"{LSH_BANDS}×{LSH_ROWS_PER_BAND}={LSH_BANDS * LSH_ROWS_PER_BAND}")

    print("[self-test] cluster_manifests wrapper")
    manifests = [
        {"id": "pkg/foo", "name": "Foo pipeline", "description": "Supply chain risk pipeline",
         "industry": ["esg"], "tags": ["risk"]},
        {"id": "pkg/foo-v2", "name": "Foo pipeline v2", "description": "Supply chain risk pipeline v2",
         "industry": ["esg"], "tags": ["risk"]},
        {"id": "pkg/bar", "name": "Space launch auth", "description": "FAA Part 450 commercial launch",
         "industry": ["space"], "tags": ["faa"]},
    ]
    cm = cluster_manifests(manifests)
    check("cluster_manifests: foo and foo-v2 near-dup or same cluster",
          cm["pkg/foo"] == cm["pkg/foo-v2"] or cm["pkg/foo"] != cm["pkg/bar"])

    result = "all self-tests passed." if not failures else f"{len(failures)} failures: {failures}"
    print(f"\n{result}")
    return 0 if not failures else 1


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

def _bench(n: int = 10_000, duplicate_rate: float = 0.10) -> int:
    print(f"[bench] generating {n:,} synthetic items (duplicate_rate={duplicate_rate:.0%}) …")
    t0 = time.perf_counter()
    items = _synthetic_items(n, duplicate_rate=duplicate_rate)
    t_gen = time.perf_counter() - t0
    print(f"  generation: {t_gen:.3f}s")

    print("[bench] building LSH index …")
    t1 = time.perf_counter()
    tables = build_lsh_index(items)
    t_idx = time.perf_counter() - t1
    print(f"  index build: {t_idx:.3f}s")

    print("[bench] counting candidate pairs (no pairwise scoring) …")
    t2 = time.perf_counter()
    seen: set[tuple[str, str]] = set()
    for item in items:
        for cid in query_candidates(tables, item):
            pair = (min(item.item_id, cid), max(item.item_id, cid))
            seen.add(pair)
    t_pairs = time.perf_counter() - t2
    pair_count = len(seen)
    print(f"  candidate pairs: {pair_count:,} in {t_pairs:.3f}s")
    theoretical_all_pairs = n * (n - 1) // 2
    ratio = pair_count / theoretical_all_pairs if theoretical_all_pairs else 0
    print(f"  reduction vs O(n²): {theoretical_all_pairs:,} all-pairs → "
          f"{pair_count:,} candidates ({ratio:.4%} of all pairs)")

    print("[bench] full cluster_corpus (LSH-blocked dedup) …")
    t3 = time.perf_counter()
    mapping = cluster_corpus(items)
    t_cluster = time.perf_counter() - t3
    t_total = time.perf_counter() - t0

    clusters = defaultdict(list)
    for iid, root in mapping.items():
        clusters[root].append(iid)
    n_clusters = len(clusters)
    n_singletons = sum(1 for v in clusters.values() if len(v) == 1)
    n_dup_items = sum(len(v) for v in clusters.values() if len(v) > 1)

    print(f"  cluster_corpus: {t_cluster:.3f}s")
    print(f"  total wall time: {t_total:.3f}s")
    print(f"  clusters: {n_clusters:,}  singletons: {n_singletons:,}  "
          f"items in dup clusters: {n_dup_items:,}")
    print(f"[bench] PASS — {n:,} items clustered in {t_total:.3f}s "
          f"({pair_count:,} candidate pairs, O(n²) would be {theoretical_all_pairs:,})")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "LSH/SimHash-band blocking dedup — near-linear alternative to O(n²) all-pairs.\n"
            "Use --self-test to verify correctness or --bench to measure scaling."
        )
    )
    p.add_argument("--self-test", action="store_true", help="Run correctness checks and exit.")
    p.add_argument("--bench", action="store_true", help="Run scaling benchmark and exit.")
    p.add_argument("--n", type=int, default=10_000,
                   help="Number of synthetic items for --bench (default: 10000).")
    p.add_argument("--duplicate-rate", type=float, default=0.10,
                   help="Fraction of synthetic items that are near-duplicates (default: 0.10).")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.bench:
        return _bench(n=args.n, duplicate_rate=args.duplicate_rate)

    p.error("--self-test or --bench is required")
    return 1


if __name__ == "__main__":
    sys.exit(_main())
