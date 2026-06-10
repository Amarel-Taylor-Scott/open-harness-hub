#!/usr/bin/env python3
"""Backs `processor/semantic-dedup`.

Cheap, deterministic, no-LLM dedup pass that catches near-duplicates of
existing live-catalog components BEFORE sending a draft to the LLM judge.

At 2000x scale this is load-bearing — without it, the same Wikipedia
articles (re-walked at different depths, in different languages, or from
different categories) collapse into thousands of redundant drafts.

Two complementary signals:
  - **SimHash on (name + description)** — token-level fingerprint;
    near-identical paraphrases collide. 64-bit hash; Hamming distance ≤ 3
    = "likely duplicate."
  - **Jaccard similarity on (industry tag set ∪ slug tokens ∪ tags)** —
    structural fit; > 0.6 = "likely duplicate."

Both must agree for `is_duplicate: true`. If only one fires, returns
`is_near_match: true` with the candidate suggested — the curator decides.

CLI:
    python -m scripts.processors.semantic_dedup --self-test
    python -m scripts.processors.semantic_dedup --check draft.yaml

Module entrypoint:
    from scripts.processors.semantic_dedup import run
    res = run(draft_manifest={...}, live_corpus=...)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "catalog"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db.catalog_row_source import iter_components_from_rows, resolve_catalog_row_dir

SIMHASH_BITS = 64
SIMHASH_DUPLICATE_THRESHOLD = 3
JACCARD_DUPLICATE_THRESHOLD = 0.60
JACCARD_NEAR_MATCH_THRESHOLD = 0.40

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


# ─── SimHash ────────────────────────────────────────────────────────────────


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if len(t) >= 2]


def _shingles(tokens: list[str], k: int = 3) -> list[str]:
    """k-shingles capture local word order; reduces false positives over bag-of-words."""
    if len(tokens) < k:
        return [" ".join(tokens)] if tokens else []
    return [" ".join(tokens[i : i + k]) for i in range(len(tokens) - k + 1)]


def _simhash(features: list[str]) -> int:
    """Charikar SimHash, 64-bit. Each feature contributes ±1 per bit, summed; sign → bit."""
    if not features:
        return 0
    counters = [0] * SIMHASH_BITS
    for f in features:
        h = int(hashlib.blake2b(f.encode("utf-8"), digest_size=8).hexdigest(), 16)
        for b in range(SIMHASH_BITS):
            if h & (1 << b):
                counters[b] += 1
            else:
                counters[b] -= 1
    out = 0
    for b in range(SIMHASH_BITS):
        if counters[b] > 0:
            out |= (1 << b)
    return out


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def _fingerprint(manifest: dict) -> int:
    """SimHash over name + description shingles. Stable across runs."""
    name = manifest.get("name", "") or ""
    desc = manifest.get("description", "") or ""
    text = (name + "\n" + desc).strip()
    return _simhash(_shingles(_tokens(text), k=3))


# ─── Jaccard ────────────────────────────────────────────────────────────────


def _structural_set(manifest: dict) -> set[str]:
    """Set of structural-fit signals: industry tags + slug tokens + free tags."""
    out: set[str] = set()
    for ind in manifest.get("industry") or []:
        out.add(f"industry:{ind}")
    for cap in manifest.get("capability") or []:
        out.add(f"capability:{cap}")
    for mod in manifest.get("modality") or []:
        out.add(f"modality:{mod}")
    for tag in manifest.get("tags") or []:
        out.add(f"tag:{tag}")
    mid = manifest.get("id", "")
    if isinstance(mid, str) and "/" in mid:
        slug = mid.split("/", 1)[1]
        for tok in _tokens(slug.replace("-", " ")):
            out.add(f"slugtok:{tok}")
    return out


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


# ─── Corpus loading ─────────────────────────────────────────────────────────


@dataclass
class CorpusEntry:
    id: str
    type: str
    fingerprint: int
    structural: set[str]


def load_live_corpus(filter_type: str | None = None) -> list[CorpusEntry]:
    """Load every live catalog manifest as CorpusEntry objects.

    Prefer database-shaped catalog rows. YAML remains a seed/export bootstrap
    fallback when the manifest bridge rows have not been generated.
    """
    corpus: list[CorpusEntry] = []
    row_dir = resolve_catalog_row_dir()
    if row_dir is not None:
        for component in iter_components_from_rows(row_dir):
            data = component.manifest
            if filter_type and data["type"] != filter_type:
                continue
            corpus.append(
                CorpusEntry(
                    id=data["id"],
                    type=data["type"],
                    fingerprint=_fingerprint(data),
                    structural=_structural_set(data),
                )
            )
        return corpus

    try:
        import yaml
    except ImportError:
        sys.stderr.write("pyyaml is required: pip install pyyaml\n")
        sys.exit(2)
    for path in CATALOG.rglob("*.yaml"):
        if "_inbox" in path.parts:
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            continue
        if not isinstance(data, dict) or "id" not in data or "type" not in data:
            continue
        if filter_type and data["type"] != filter_type:
            continue
        corpus.append(
            CorpusEntry(
                id=data["id"],
                type=data["type"],
                fingerprint=_fingerprint(data),
                structural=_structural_set(data),
            )
        )
    return corpus


# ─── Dedup ──────────────────────────────────────────────────────────────────


def run(
    draft_manifest: dict,
    *,
    live_corpus: list[CorpusEntry] | None = None,
    only_same_type: bool = True,
) -> dict[str, Any]:
    """Compare a draft against the live corpus; return duplicate verdict + best matches.

    Returns:
        {
          "is_duplicate": bool,        # high confidence — both signals fired
          "is_near_match": bool,       # one signal fired (advisory)
          "best_match_id": str | None,
          "best_match_hamming": int,
          "best_match_jaccard": float,
          "top_5": [{id, hamming, jaccard, both_fired}, ...],
        }
    """
    if not isinstance(draft_manifest, dict):
        return {
            "is_duplicate": False,
            "is_near_match": False,
            "best_match_id": None,
            "best_match_hamming": SIMHASH_BITS,
            "best_match_jaccard": 0.0,
            "top_5": [],
        }

    if live_corpus is None:
        live_corpus = load_live_corpus(
            filter_type=draft_manifest.get("type") if only_same_type else None,
        )

    draft_fp = _fingerprint(draft_manifest)
    draft_struct = _structural_set(draft_manifest)

    candidates = []
    for entry in live_corpus:
        if only_same_type and entry.type != draft_manifest.get("type"):
            continue
        ham = _hamming(draft_fp, entry.fingerprint)
        jac = _jaccard(draft_struct, entry.structural)
        both = (ham <= SIMHASH_DUPLICATE_THRESHOLD) and (jac >= JACCARD_DUPLICATE_THRESHOLD)
        candidates.append((entry.id, ham, jac, both))

    # Rank: prefer entries where both signals fired; otherwise low hamming + high jaccard
    candidates.sort(key=lambda c: (not c[3], c[1], -c[2]))

    top_5 = [
        {"id": c[0], "hamming": c[1], "jaccard": round(c[2], 3), "both_fired": c[3]}
        for c in candidates[:5]
    ]

    if candidates:
        best = candidates[0]
        is_duplicate = best[3]
        is_near_match = (
            (best[1] <= SIMHASH_DUPLICATE_THRESHOLD)
            or (best[2] >= JACCARD_NEAR_MATCH_THRESHOLD)
        ) and not is_duplicate
        return {
            "is_duplicate": is_duplicate,
            "is_near_match": is_near_match,
            "best_match_id": best[0],
            "best_match_hamming": best[1],
            "best_match_jaccard": round(best[2], 3),
            "top_5": top_5,
        }

    return {
        "is_duplicate": False,
        "is_near_match": False,
        "best_match_id": None,
        "best_match_hamming": SIMHASH_BITS,
        "best_match_jaccard": 0.0,
        "top_5": [],
    }


# ─── Self-test (offline) ────────────────────────────────────────────────────


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        marker = "ok" if ok else "FAIL"
        print(f"  [{marker}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    base = {
        "id": "knowledge-pack/csddd-and-forced-labor-indicators",
        "type": "knowledge-pack",
        "name": "Global supply-chain due-diligence regulatory pack",
        "description": (
            "Reference pack of extracts from 12 jurisdictions plus 4 international frameworks "
            "covering CSDDD, CSRD, EUDR, UK MSA, German LkSG, France Loi Vigilance, etc."
        ),
        "industry": ["esg", "supply_chain", "compliance"],
        "capability": ["retrieval", "verification"],
        "modality": ["text"],
        "tags": ["csddd", "ilo", "modern-slavery", "supply-chain"],
    }
    corpus = [
        CorpusEntry(
            id=base["id"],
            type=base["type"],
            fingerprint=_fingerprint(base),
            structural=_structural_set(base),
        )
    ]

    print("[self-test] identical draft → is_duplicate=True")
    res = run(dict(base, id="knowledge-pack/csddd-and-forced-labor-indicators-v2"), live_corpus=corpus)
    check("is_duplicate true on identical content", res["is_duplicate"], str(res))

    print("[self-test] paraphrased same-topic draft → near-match or duplicate")
    paraphrase = {
        **base,
        "id": "knowledge-pack/csddd-paraphrase",
        "name": "Global supply-chain DD reference pack",
        "description": (
            "Reference distillation of 12 national legal frameworks covering "
            "CSDDD, CSRD, EUDR, UK Modern Slavery Act, LkSG, and others."
        ),
    }
    res = run(paraphrase, live_corpus=corpus)
    check("paraphrase flagged as duplicate or near-match",
          res["is_duplicate"] or res["is_near_match"], str(res))
    check("best match identifies source", res["best_match_id"] == base["id"])

    print("[self-test] unrelated draft → no duplicate")
    unrelated = {
        "id": "knowledge-pack/space-launch-faa-part-450",
        "type": "knowledge-pack",
        "name": "FAA Part 450 commercial space launch regulatory pack",
        "description": (
            "Reference pack covering FAA Part 450 licensing requirements for commercial "
            "space launch and reentry vehicles, vehicle safety, orbital debris mitigation."
        ),
        "industry": ["space", "space.launch"],
        "capability": ["retrieval"],
        "modality": ["text"],
        "tags": ["faa", "part-450", "commercial-space"],
    }
    res = run(unrelated, live_corpus=corpus)
    check("unrelated draft not duplicate", not res["is_duplicate"], str(res))
    check("unrelated draft not near-match", not res["is_near_match"], str(res))

    print("[self-test] empty corpus → no duplicate")
    res = run(base, live_corpus=[])
    check("empty corpus → no duplicate", not res["is_duplicate"] and not res["is_near_match"])
    check("best_match_id None on empty corpus", res["best_match_id"] is None)

    print("[self-test] simhash hamming reflexivity")
    check("identical text → hamming 0",
          _hamming(_fingerprint(base), _fingerprint(base)) == 0)

    print("[self-test] jaccard symmetry")
    a = _structural_set(base)
    b = _structural_set(paraphrase)
    check("jaccard symmetric",
          abs(_jaccard(a, b) - _jaccard(b, a)) < 1e-9)

    print(f"\n{'all self-tests passed.' if not failures else f'{len(failures)} failures: {failures}'}")
    return 0 if not failures else 1


# ─── CLI ────────────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Semantic dedup against live catalog (SimHash + Jaccard).")
    p.add_argument("--check", help="Path to a draft YAML to check")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()
    if not args.check:
        p.error("--check PATH or --self-test required")

    try:
        import yaml
    except ImportError:
        sys.stderr.write("pyyaml is required: pip install pyyaml\n")
        return 2
    draft = yaml.safe_load(Path(args.check).read_text(encoding="utf-8"))
    res = run(draft)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 1 if res["is_duplicate"] else 0


if __name__ == "__main__":
    sys.exit(_main())
