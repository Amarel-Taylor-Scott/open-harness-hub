#!/usr/bin/env python3
"""scripts.cluster_primitive_duplicates — near-duplicate CLUSTERING over the proven primitive corpus.

Honest de-dup accounting for the ~20K primitive corpus: how much of it is genuinely DISTINCT vs
redundant near-duplicates. The pipeline is fully deterministic + offline (no network / no LLM /
no wall-clock / no RNG):

  1. load a capped sample of the PROVEN corpus
     (data/dev-intel/proven_primitives/proven_*.jsonl + data/dev-intel/parametric_primitives/param_*.jsonl);
  2. extract a meaning-bearing token set per primitive (family / mutator / edges / template / binding / words);
  3. lsh_blocking → candidate pairs (MinHash banding, star-expanded per bucket to bound cost);
  4. compute Jaccard similarity within blocks; keep pairs ≥ threshold;
  5. union-find over the surviving pairs → near-duplicate CLUSTERS;
  6. pick ONE canonical representative per cluster (deterministic: lowest primitive_id).

Counts are reported HONESTLY and separately: n_scanned (rows read, ≤ cap) vs n_clusters (distinct
primitives) vs n_near_dupes (redundant rows collapsed) vs redundancy_pct. A row is never reported as
"distinct" merely because it exists — distinctness is the cluster count after collapse.

The blocking + similarity primitives are imported from the sibling ``scripts.primitive_similarity_portfolio``
when available; otherwise a local, standalone lexical fallback is used so ``--self-test`` needs no sibling.

CLI:
    python3 _repos/shared-backend-components/scripts/cluster_primitive_duplicates.py --self-test
    python3 _repos/shared-backend-components/scripts/cluster_primitive_duplicates.py --write
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
PROVEN_DIR = _resource("data") / "dev-intel" / "proven_primitives"
PARAM_DIR = _resource("data") / "dev-intel" / "parametric_primitives"
OUT_PATH = _resource("data") / "dev-intel" / "primitive_similarity" / "dedupe_clusters.json"

#: Fixed literal timestamp — NEVER wall-clock (determinism law).
FIXED_GENERATED_UTC = "2026-07-03T00:00:00Z"

#: Sample cap — recorded in the report so counts are never mistaken for the full corpus.
DEFAULT_CAP = 5000

#: MinHash / banding parameters. num_perm must be divisible by bands. rows = num_perm // bands.
#: More bands ⇒ more recall (more candidate blocks), fewer rows/band ⇒ looser blocks. 64/16 (rows=4)
#: is a standard near-dup setting; final membership is gated by the exact Jaccard threshold below.
NUM_PERM = 64
BANDS = 16

#: Jaccard threshold for calling two primitives near-duplicates. 0.80 = strong structural overlap
#: (same mutator+edges+template, differing only in incidental word tokens). A parametric variant that
#: differs in its binding key sits at ~0.71 (6 tokens, 1 differs) and stays SEPARATE at this bar — it
#: computes a genuinely distinct output; only true structural repeats collapse.
NEAR_DUP_THRESHOLD = 0.80

_WORD_RE = re.compile(r"[a-z0-9]+")


def _stable_int(seed: str) -> int:
    """Deterministic 64-bit int from a string (sha256, NOT builtin hash())."""
    return int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16], 16)


# --------------------------------------------------------------------------------------------------
# Local lexical fallback (standalone — used when the sibling portfolio is unavailable/incompatible).
# --------------------------------------------------------------------------------------------------
def _local_token_similarity(a: set[str], b: set[str]) -> float:
    """Jaccard similarity of two token sets. |A∩B| / |A∪B|; empty∩empty ⇒ 0.0."""
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _minhash_signature(tokens: set[str], num_perm: int) -> tuple[int, ...]:
    """Deterministic MinHash signature over a token set (num_perm permutations via salted sha256)."""
    if not tokens:
        return tuple([0] * num_perm)
    sig = []
    for i in range(num_perm):
        best = None
        for t in tokens:
            v = _stable_int(f"{i}:{t}")
            if best is None or v < best:
                best = v
        sig.append(best if best is not None else 0)
    return tuple(sig)


def _local_lsh_blocking(token_sets: dict[str, set[str]], num_perm: int = NUM_PERM,
                        bands: int = BANDS) -> set[tuple[str, str]]:
    """MinHash-banding LSH blocking → candidate pairs.

    Items are bucketed per band by their signature slice; within each bucket we STAR-expand from the
    bucket's lowest id (bounds cost to O(k) per bucket, deterministic center). Returns a set of
    (id_a, id_b) with id_a < id_b. Membership is later gated by the exact similarity threshold, so
    star-expansion only affects recall of candidate pairs, never final correctness of a merge.
    """
    if num_perm % bands != 0:
        raise ValueError(f"num_perm ({num_perm}) must be divisible by bands ({bands})")
    rows = num_perm // bands
    sigs = {pid: _minhash_signature(toks, num_perm) for pid, toks in token_sets.items()}
    pairs: set[tuple[str, str]] = set()
    for b in range(bands):
        buckets: dict[tuple, list[str]] = {}
        for pid, sig in sigs.items():
            key = (b, sig[b * rows:(b + 1) * rows])
            buckets.setdefault(key, []).append(pid)
        for members in buckets.values():
            if len(members) < 2:
                continue
            members.sort()
            center = members[0]
            for other in members[1:]:
                pairs.add((center, other))
    return pairs


# --------------------------------------------------------------------------------------------------
# Sibling adapter: prefer scripts.primitive_similarity_portfolio, fall back to local (smoke-tested).
# --------------------------------------------------------------------------------------------------
def _resolve_engine() -> tuple[str, object, object]:
    """Return (engine_name, lsh_blocking_fn, token_similarity_fn).

    Tries the sibling portfolio's ``lsh_blocking`` + ``token_similarity`` and only adopts them if a
    tiny smoke test passes against our contract; otherwise uses the local fallback. This keeps
    --self-test standalone while using the sibling when it is present and compatible.
    """
    try:
        from scripts import primitive_similarity_portfolio as _sib  # type: ignore
        sib_lsh = getattr(_sib, "lsh_blocking", None)
        sib_sim = getattr(_sib, "token_similarity", None)
        if callable(sib_lsh) and callable(sib_sim):
            # Smoke test the contract: two near-identical sets must block together + score high; a
            # disjoint set must not. Any exception/shape mismatch ⇒ reject and use local.
            a = {"x", "y", "z", "w"}
            b = {"x", "y", "z", "q"}
            c = {"m", "n", "o", "p"}
            sim_ok = abs(float(sib_sim(a, a)) - 1.0) < 1e-9 and float(sib_sim(a, c)) < 0.5
            blk = sib_lsh({"a": a, "b": b, "c": c})
            norm = {tuple(sorted(p)) for p in blk}
            blk_ok = ("a", "b") in norm and ("a", "c") not in norm and ("b", "c") not in norm
            if sim_ok and blk_ok:
                return "sibling:primitive_similarity_portfolio", sib_lsh, sib_sim
    except Exception:
        pass
    return "local_fallback", _local_lsh_blocking, _local_token_similarity


# --------------------------------------------------------------------------------------------------
# Token extraction (robust across proven-leaf / parametric / composite record shapes).
# --------------------------------------------------------------------------------------------------
def primitive_tokens(rec: dict) -> set[str]:
    """Meaning-bearing token set for a primitive record. Field-prefixed so cross-field collisions
    can't happen (e.g. a family named like an edge). Handles leaf, parametric, and composite shapes."""
    toks: set[str] = set()

    def add(prefix: str, value) -> None:
        if value is None:
            return
        toks.add(f"{prefix}:{str(value).strip().lower()}")

    add("fam", rec.get("family"))
    add("mut", rec.get("mutator"))
    add("in", rec.get("input_edge_type_id") or rec.get("input_edge"))
    add("out", rec.get("output_edge_type_id") or rec.get("output_edge"))
    add("tpl", rec.get("template"))

    binding = rec.get("binding")
    if isinstance(binding, dict):
        for k in sorted(binding):
            add("bind", f"{k}={binding[k]}")

    for lf in rec.get("leaf_families_used") or []:
        add("leaf", lf)

    # Free-text signal (capability / description) → word tokens.
    for field in ("capability", "description"):
        text = rec.get(field)
        if isinstance(text, str):
            for w in _WORD_RE.findall(text.lower()):
                if len(w) > 2:
                    toks.add(f"w:{w}")
    return toks


def primitive_id(rec: dict, fallback_seed: str) -> str:
    """Stable id for a record; synthesize a deterministic one if absent (never hash())."""
    pid = rec.get("primitive_id")
    if isinstance(pid, str) and pid:
        return pid
    return f"prim:unknown:{fallback_seed}:{_stable_int(fallback_seed):x}"


# --------------------------------------------------------------------------------------------------
# Corpus loading.
# --------------------------------------------------------------------------------------------------
def load_corpus_sample(cap: int = DEFAULT_CAP) -> list[dict]:
    """Load ≤ cap primitive records from proven_*.jsonl + param_*.jsonl in deterministic file order."""
    records: list[dict] = []
    shards: list[Path] = []
    if PROVEN_DIR.is_dir():
        shards += sorted(PROVEN_DIR.glob("proven_*.jsonl"))
    if PARAM_DIR.is_dir():
        shards += sorted(PARAM_DIR.glob("param_*.jsonl"))
    for shard in shards:
        if len(records) >= cap:
            break
        for line in shard.read_text(encoding="utf-8").splitlines():
            if len(records) >= cap:
                break
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict):
                rec.setdefault("_shard", shard.name)
                records.append(rec)
    return records


# --------------------------------------------------------------------------------------------------
# Union-find.
# --------------------------------------------------------------------------------------------------
class _UnionFind:
    def __init__(self, ids: list[str]) -> None:
        self.parent = {i: i for i in ids}

    def find(self, x: str) -> str:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # path compression
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            # Attach larger id under smaller → the lowest id stays root (deterministic canonical).
            lo, hi = (ra, rb) if ra < rb else (rb, ra)
            self.parent[hi] = lo


# --------------------------------------------------------------------------------------------------
# Clustering.
# --------------------------------------------------------------------------------------------------
def cluster_primitives(records: list[dict], threshold: float = NEAR_DUP_THRESHOLD,
                       num_perm: int = NUM_PERM, bands: int = BANDS) -> dict:
    """Cluster near-duplicate primitives. Returns the honest de-dup accounting + representatives.

    n_scanned = rows in; n_clusters = distinct primitives after collapse; n_near_dupes = rows collapsed
    away (n_scanned − n_clusters); redundancy_pct = n_near_dupes / n_scanned × 100.
    Representative per cluster = lowest primitive_id (deterministic).
    """
    engine_name, lsh_blocking_fn, token_similarity_fn = _resolve_engine()

    ids: list[str] = []
    token_sets: dict[str, set[str]] = {}
    for idx, rec in enumerate(records):
        seed = f"{rec.get('_shard', 'mem')}:{idx}"
        pid = primitive_id(rec, seed)
        # If two rows carry the same primitive_id, disambiguate deterministically so union-find and
        # bucketing address one node per row (true duplicates still merge via similarity==1.0).
        if pid in token_sets:
            pid = f"{pid}#dupe:{seed}"
        ids.append(pid)
        token_sets[pid] = primitive_tokens(rec)

    n_scanned = len(ids)
    uf = _UnionFind(ids)

    candidate_pairs = lsh_blocking_fn(token_sets, num_perm, bands) if _accepts_params(lsh_blocking_fn) \
        else lsh_blocking_fn(token_sets)
    n_candidate_pairs = len(candidate_pairs)
    n_merged_pairs = 0
    for a, b in candidate_pairs:
        if token_similarity_fn(token_sets[a], token_sets[b]) >= threshold:
            uf.union(a, b)
            n_merged_pairs += 1

    clusters: dict[str, list[str]] = {}
    for pid in ids:
        clusters.setdefault(uf.find(pid), []).append(pid)

    n_clusters = len(clusters)
    n_near_dupes = n_scanned - n_clusters
    redundancy_pct = round((n_near_dupes / n_scanned * 100.0), 2) if n_scanned else 0.0

    representatives = sorted(clusters.keys())
    # Largest cluster (ties broken by lowest representative id → deterministic).
    largest_rep = ""
    largest_members: list[str] = []
    for rep in representatives:
        members = sorted(clusters[rep])
        if len(members) > len(largest_members):
            largest_members = members
            largest_rep = rep
    largest_cluster = {
        "representative": largest_rep,
        "size": len(largest_members),
        "members": largest_members[:50],
        "members_truncated": len(largest_members) > 50,
    }

    return {
        "engine": engine_name,
        "cap": DEFAULT_CAP,
        "threshold": threshold,
        "num_perm": num_perm,
        "bands": bands,
        "n_scanned": n_scanned,
        "n_candidate_pairs": n_candidate_pairs,
        "n_merged_pairs": n_merged_pairs,
        "n_clusters": n_clusters,
        "n_near_dupes": n_near_dupes,
        "redundancy_pct": redundancy_pct,
        "largest_cluster": largest_cluster,
        "representatives": representatives,
    }


def _accepts_params(fn) -> bool:
    """True if fn's signature accepts (token_sets, num_perm, bands) — else call with token_sets only."""
    try:
        import inspect
        params = inspect.signature(fn).parameters
        return len(params) >= 3 or any(
            p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD) for p in params.values())
    except (TypeError, ValueError):
        return False


# --------------------------------------------------------------------------------------------------
# Report.
# --------------------------------------------------------------------------------------------------
def build_report(cap: int = DEFAULT_CAP) -> dict:
    records = load_corpus_sample(cap)
    result = cluster_primitives(records)
    report = {"generated_utc": FIXED_GENERATED_UTC, "record_type": "primitive_dedupe_clusters",
              "sources": ["proven_primitives/proven_*.jsonl", "parametric_primitives/param_*.jsonl"]}
    report.update(result)
    return report


def write_report(cap: int = DEFAULT_CAP) -> Path:
    report = build_report(cap)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return OUT_PATH


# --------------------------------------------------------------------------------------------------
# Self-test (synthetic, offline, standalone).
# --------------------------------------------------------------------------------------------------
def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # --- Synthetic corpus: 3 obvious near-dupes of one primitive + 2 genuinely distinct ones. ---
    def leaf(pid, fam, mut, ie, oe, cap):
        return {"primitive_id": pid, "family": fam, "mutator": mut,
                "input_edge_type_id": ie, "output_edge_type_id": oe, "capability": cap}

    near_a = leaf("prim:leaf:agg_sum:b", "aggregation", "agg_sum", "RecordBatch", "Number", "sum a numeric field over records")
    near_b = leaf("prim:leaf:agg_sum:a", "aggregation", "agg_sum", "RecordBatch", "Number", "sum a numeric field across records")
    near_c = leaf("prim:leaf:agg_sum:c", "aggregation", "agg_sum", "RecordBatch", "Number", "sum a numeric field over the records")
    distinct_hash = leaf("prim:leaf:hash_sha256", "hashing", "hash_sha256", "Bytes", "Hex", "compute the sha256 hex digest of bytes")
    distinct_upper = leaf("prim:leaf:str_upper", "text", "str_upper", "String", "String", "uppercase a string value")
    records = [near_a, near_b, near_c, distinct_hash, distinct_upper]

    res = cluster_primitives(records)

    # Engine resolves (sibling or standalone local) without a network.
    check("engine resolved offline", res["engine"] in
          ("local_fallback", "sibling:primitive_similarity_portfolio"), res["engine"])

    # 1) Obvious near-dupes group together.
    check("scanned all 5 rows", res["n_scanned"] == 5, str(res["n_scanned"]))
    check("collapses to 3 distinct clusters", res["n_clusters"] == 3,
          f"n_clusters={res['n_clusters']} reps={res['representatives']}")
    check("2 rows collapsed as near-dupes", res["n_near_dupes"] == 2, str(res["n_near_dupes"]))

    # 2) Distinct primitives stay separate (hash + upper are their own reps).
    check("distinct hash kept separate", "prim:leaf:hash_sha256" in res["representatives"])
    check("distinct upper kept separate", "prim:leaf:str_upper" in res["representatives"])

    # 3) redundancy_pct computes correctly (2/5 = 40%).
    check("redundancy_pct = 40.0", res["redundancy_pct"] == 40.0, str(res["redundancy_pct"]))

    # 4) Representative is deterministic = the LOWEST primitive_id of the near-dup cluster (…:a).
    check("largest cluster has 3 members", res["largest_cluster"]["size"] == 3,
          str(res["largest_cluster"]["size"]))
    check("canonical rep = lowest id (agg_sum:a)",
          res["largest_cluster"]["representative"] == "prim:leaf:agg_sum:a",
          res["largest_cluster"]["representative"])

    # 5) Determinism: identical input ⇒ identical result.
    check("clustering is deterministic", cluster_primitives(records) == res)

    # 6) Similarity/blocking sanity via whichever engine resolved.
    _, lsh_fn, sim_fn = _resolve_engine()
    ta, tb = primitive_tokens(near_a), primitive_tokens(near_b)
    tz = primitive_tokens(distinct_hash)
    check("near-dup similarity ≥ threshold", sim_fn(ta, tb) >= NEAR_DUP_THRESHOLD, f"{sim_fn(ta, tb):.3f}")
    check("distinct similarity < threshold", sim_fn(ta, tz) < NEAR_DUP_THRESHOLD, f"{sim_fn(ta, tz):.3f}")

    # 7) Empty corpus is safe (no div-by-zero).
    empty = cluster_primitives([])
    check("empty corpus → 0 clusters, 0.0 redundancy",
          empty["n_clusters"] == 0 and empty["redundancy_pct"] == 0.0)

    # 8) Report shape carries the honest, separated counts + fixed (non-wall-clock) timestamp.
    report_keys = {"n_scanned", "n_clusters", "n_near_dupes", "redundancy_pct", "largest_cluster",
                   "representatives"}
    synth_report = {"generated_utc": FIXED_GENERATED_UTC}
    synth_report.update(res)
    check("report carries separated counts", report_keys.issubset(synth_report.keys()))
    check("timestamp is fixed literal (no wall-clock)",
          synth_report["generated_utc"] == "2026-07-03T00:00:00Z")

    print(f"\n{'all cluster_primitive_duplicates self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Near-duplicate clustering + honest de-dup accounting over the proven primitive corpus.")
    p.add_argument("--self-test", action="store_true", help="run the standalone synthetic self-test")
    p.add_argument("--write", action="store_true", help="write the dedupe-cluster report to disk")
    p.add_argument("--cap", type=int, default=DEFAULT_CAP, help=f"max rows to sample (default {DEFAULT_CAP})")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.write:
        report = build_report(args.cap)
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {OUT_PATH.relative_to(_REPO)}")
        print(f"  engine={report['engine']} n_scanned={report['n_scanned']} (cap={report['cap']}) "
              f"n_clusters={report['n_clusters']} n_near_dupes={report['n_near_dupes']} "
              f"redundancy_pct={report['redundancy_pct']} "
              f"largest_cluster={report['largest_cluster']['size']}")
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
