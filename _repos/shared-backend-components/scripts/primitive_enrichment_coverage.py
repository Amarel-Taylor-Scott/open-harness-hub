#!/usr/bin/env python3
"""scripts.primitive_enrichment_coverage — the MAKE-SURE gate: every searchable primitive carries MULTIPLE
representation surfaces, verified over the FULL corpus (no sampling where exactness is cheap):

  * card FIELDS       — title · blackbox · input_edge+output_edge · blocking_keys      (full stream count)
  * DESCRIPTORS       — operations/datatypes/impact/frame via the persisted feature records (ID-set match)
  * EMBEDDINGS        — the persisted blackbox store (ID-set match, exact)
  * DESCRIPTIONS      — the persisted 3-register store: plain/technical/semantic       (ID-set match, exact)
  * DERIVABILITY      — register texts + capability-key axes derive non-empty (deterministic stride probe;
                        pure-function cost only — persistence is what the exact ID checks above cover)

Store coverage is an EXACT id-set comparison between the corpus and each store's ids.json — "all 112K have
embeddings" is proven, never asserted. Gap records are written per missing surface (candidate rows, never a
mutation of the cards). RUN mode ratchets: store coverage may never DROP below the previous receipt.

serves_truth=false — coverage numbers and gap records are measurements, never served truth.

    PYTHONPATH=. python3 scripts/primitive_enrichment_coverage.py --self-test
    PYTHONPATH=. python3 scripts/primitive_enrichment_coverage.py --run       # full corpus, receipt + gaps
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts import capability_embedding as _emb  # noqa: E402  REUSE: registers + capability key + embed text
from scripts import build_primitive_embeddings as _stored  # noqa: E402  REUSE: the store locations/loaders

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_SAMPLE_IDS_CAP = 5          # sample ids per missing surface in the receipt (full counts are always exact)
_DERIVABILITY_STRIDE = 50    # probe every Nth card for derivability (pure functions; presence is checked exactly)
#: the card FIELD surfaces checked on every card (full stream, no sampling)
_FIELD_SURFACES: tuple[str, ...] = ("title", "blackbox", "edges", "edges_clean", "blocking_keys")


def _has_field(card: dict[str, Any], surface: str) -> bool:
    if surface == "title":
        return bool(str(card.get("title") or "").strip())
    if surface == "blackbox":
        return bool(_emb.blackbox_text(card).strip())
    if surface == "edges":
        return bool(str(card.get("input_edge") or "").strip()) and bool(str(card.get("output_edge") or "").strip())
    if surface == "edges_clean":
        # hygiene, not just presence: an edge carrying a stringified dict OR list ("{'type': ...}", "[...]")
        # is present but NOT a clean type name — audit found 820 dict-shaped + 27 list-shaped (review finding)
        return _has_field(card, "edges") and not any(
            str(card.get(side) or "").lstrip().startswith(("{", "[")) for side in ("input_edge", "output_edge"))
    if surface == "blocking_keys":
        return bool(card.get("blocking_keys"))
    raise ValueError(f"unknown field surface {surface!r}")


def field_coverage(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Full-stream field presence per surface — exact counts + a few sample ids per gap."""
    out: dict[str, Any] = {}
    for surface in _FIELD_SURFACES:
        missing_ids: list[str] = []
        present = 0
        for c in cards:
            if _has_field(c, surface):
                present += 1
            elif len(missing_ids) < _SAMPLE_IDS_CAP:
                missing_ids.append(str(c.get("primitive_id")))
        out[surface] = {"present": present, "missing": len(cards) - present,
                        "coverage": round(present / len(cards), 6) if cards else 0.0,
                        "sample_missing_ids": missing_ids}
    return out


def _store_ids(kind: str) -> Optional[set]:
    """The persisted id set of one store — None when that store is absent on this checkout."""
    try:
        if kind == "blackbox_embeddings":
            return set(json.loads((_stored.default_store_dir() / "ids.json").read_text()))
        if kind == "register_embeddings":
            return set(json.loads((_stored.default_register_store_dir() / "ids.json").read_text()))
        if kind == "feature_records":
            ids = set()
            with (_stored.default_store_dir() / "features.jsonl").open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        ids.add(json.loads(line).get("primitive_id"))
            return ids
        raise ValueError(f"unknown store kind {kind!r}")
    except OSError:
        return None


def store_coverage(corpus_ids: set, *, stores: Optional[dict[str, Optional[set]]] = None) -> dict[str, Any]:
    """EXACT id-set comparison corpus vs each persisted store: coverage fraction, missing count + samples,
    and extra (stale) ids present in the store but not the corpus. ``stores`` injectable for hermetic tests."""
    stores = stores if stores is not None else {k: _store_ids(k) for k in
                                                ("blackbox_embeddings", "register_embeddings", "feature_records")}
    out: dict[str, Any] = {}
    for kind, ids in stores.items():
        if ids is None:
            out[kind] = {"status": "absent", "coverage": 0.0}
            continue
        missing = corpus_ids - ids
        out[kind] = {"status": "present", "persisted": len(ids),
                     "coverage": round((len(corpus_ids) - len(missing)) / len(corpus_ids), 6) if corpus_ids else 0.0,
                     "missing": len(missing), "sample_missing_ids": sorted(missing)[:_SAMPLE_IDS_CAP],
                     "stale_extra": len(ids - corpus_ids)}
    return out


def derivability_probe(cards: list[dict[str, Any]], *, stride: int = _DERIVABILITY_STRIDE) -> dict[str, Any]:
    """Deterministic stride probe: every Nth card must DERIVE non-empty register texts (all three), a non-empty
    embed surface, and a full capability key. Failures are named, never averaged away."""
    failures: list[dict[str, str]] = []
    probed = 0
    for c in cards[::max(1, stride)]:
        probed += 1
        pid = str(c.get("primitive_id"))
        if not _emb.card_embed_text(c).strip():
            failures.append({"primitive_id": pid, "surface": "embed_text"})
        for register in _emb.REGISTERS:
            if not _emb.register_text(c, register).strip():
                failures.append({"primitive_id": pid, "surface": f"register:{register}"})
        key = _emb.capability_key(c)
        if set(key) != set(_emb.CAPABILITY_AXES):
            failures.append({"primitive_id": pid, "surface": "capability_key"})
    return {"probed": probed, "stride": stride, "failures": failures[:50],
            "failure_count": len(failures), "all_derivable": not failures}


def measure(cards: list[dict[str, Any]], *, stores: Optional[dict[str, Optional[set]]] = None,
            stride: int = _DERIVABILITY_STRIDE) -> dict[str, Any]:
    """The full enrichment-coverage receipt over the given cards."""
    corpus_ids = {c.get("primitive_id") for c in cards if c.get("primitive_id")}
    return {"record_type": "primitive_enrichment_coverage", "total_cards": len(cards),
            "distinct_ids": len(corpus_ids),
            "field_coverage": field_coverage(cards),
            "store_coverage": store_coverage(corpus_ids, stores=stores),
            "derivability": derivability_probe(cards, stride=stride),
            "note": "store coverage is an EXACT id-set comparison (full corpus, never sampled); the "
                    "derivability probe is a deterministic stride over pure derivations. Gap records are "
                    "candidates — a missing surface is a repair ticket, never a silent drop.", **BOUNDARY}


def _write_gaps(cards: list[dict[str, Any]], receipt: dict[str, Any], out_path: Path) -> int:
    """One gap record per card per missing PERSISTED surface (full, not capped — the receipt has the counts)."""
    store_cov = receipt["store_coverage"]
    missing_by_kind = {}
    corpus_ids = {c.get("primitive_id") for c in cards if c.get("primitive_id")}
    for kind in store_cov:
        ids = _store_ids(kind)
        missing_by_kind[kind] = (corpus_ids - ids) if ids is not None else set()
    n = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for c in cards:
            pid = c.get("primitive_id")
            missing_fields = [s for s in _FIELD_SURFACES if not _has_field(c, s)]
            missing_stores = [k for k, ids in missing_by_kind.items() if pid in ids]
            if missing_fields or missing_stores:
                fh.write(json.dumps({"record_type": "enrichment_gap", "primitive_id": pid,
                                     "missing_fields": missing_fields, "missing_stores": missing_stores,
                                     **BOUNDARY}, sort_keys=True) + "\n")
                n += 1
    return n


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = [
        {"primitive_id": "e:full", "title": "Full card", "blackbox": "Does a complete thing to rows.",
         "input_edge": "In", "output_edge": "Out", "blocking_keys": ["thing"], **BOUNDARY},
        {"primitive_id": "e:thin", "title": "", "blackbox": "Thin card with no title or edges.",
         "input_edge": "", "output_edge": "", **BOUNDARY},
    ]
    # (a) field coverage: exact counts; the thin card is flagged by id, never averaged away
    fc = field_coverage(cards)
    checks.append(("field coverage counts exactly and names the gap ids",
                   fc["title"]["present"] == 1 and fc["title"]["sample_missing_ids"] == ["e:thin"]
                   and fc["edges"]["missing"] == 1 and fc["blocking_keys"]["missing"] == 1))
    # (b) store coverage: EXACT id-set math — a card missing from a store drops coverage below 1.0 and is named
    ids = {c["primitive_id"] for c in cards}
    sc = store_coverage(ids, stores={"blackbox_embeddings": {"e:full"},           # e:thin missing -> 0.5
                                     "register_embeddings": {"e:full", "e:thin"},  # complete -> 1.0
                                     "feature_records": None})                     # absent store labelled
    checks.append(("a card missing from a store is caught by exact id-set comparison (0.5, named)",
                   sc["blackbox_embeddings"]["coverage"] == 0.5
                   and sc["blackbox_embeddings"]["sample_missing_ids"] == ["e:thin"]))
    checks.append(("a complete store scores exactly 1.0 and an absent store is labelled, never faked",
                   sc["register_embeddings"]["coverage"] == 1.0
                   and sc["feature_records"]["status"] == "absent"))
    # (c) derivability: every register text + the capability key derive for well-formed cards
    dp = derivability_probe(cards, stride=1)
    checks.append(("derivability probe derives registers + capability key for every probed card",
                   dp["probed"] == 2 and dp["all_derivable"]))
    # (d) the full receipt + determinism + governance
    rec = measure(cards, stores={"blackbox_embeddings": ids, "register_embeddings": ids,
                                 "feature_records": ids}, stride=1)
    checks.append(("measure() is deterministic (byte-identical twice)",
                   json.dumps(rec, sort_keys=True) == json.dumps(
                       measure(cards, stores={"blackbox_embeddings": ids, "register_embeddings": ids,
                                              "feature_records": ids}, stride=1), sort_keys=True)))
    checks.append(("receipt is candidate/serves_truth=false", rec["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - primitive_enrichment_coverage: every primitive's MULTIPLE surfaces are verified — card "
          "fields by full stream count, persisted descriptors/embeddings/3-register descriptions by EXACT "
          "id-set comparison against the stores (a single missing card drops coverage and is named), "
          "derivability by deterministic probe. Gap records are candidate repair tickets. serves_truth=false.")
    return 0


def _run() -> int:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    base = resource("data") / "dev-intel" / "aidevobserver_edge_foundry"
    cards: list[dict[str, Any]] = []
    for fn in ("verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl"):
        cards += read_jsonl_tolerant(base / fn)
    print(f"measuring enrichment coverage over {len(cards)} cards (exact store id-set comparison) ...")
    receipt = measure(cards)
    out_dir = resource("data") / "dev-intel" / "session_emulation"
    prev_path = out_dir / "enrichment_coverage_receipt.json"
    # RATCHET: persisted-store coverage must never DROP vs the previous receipt (regression = hard failure)
    regressions: list[str] = []
    if prev_path.exists():
        prev = json.loads(prev_path.read_text())
        for kind, cov in receipt["store_coverage"].items():
            prev_cov = (prev.get("store_coverage", {}).get(kind) or {}).get("coverage", 0.0)
            if cov.get("coverage", 0.0) < prev_cov:
                regressions.append(f"{kind}: {cov.get('coverage')} < previous {prev_cov}")
    receipt["ratchet_regressions"] = regressions
    # STORE-TEXT staleness: recompute the corpus embed-surface digest and compare with the manifests' —
    # ids can match while the source texts drifted (review finding: id-set comparison alone cannot see it).
    # Manifests written before this field carry None -> status "unknown_legacy_manifest", never a fake pass.
    try:
        corpus_digest = _stored.corpus_text_digest(cards)
        freshness = {}
        for kind, dir_fn in (("blackbox_embeddings", _stored.default_store_dir),
                             ("register_embeddings", _stored.default_register_store_dir)):
            try:
                man = json.loads((dir_fn() / "manifest.json").read_text())
                stored_digest = man.get("corpus_text_hash")
                freshness[kind] = ("fresh" if stored_digest == corpus_digest
                                   else "unknown_legacy_manifest" if stored_digest is None else "STALE_TEXT")
            except OSError:
                freshness[kind] = "absent"
        receipt["store_text_freshness"] = freshness
    except Exception as exc:  # noqa: BLE001 — freshness is additive; a failure is reported, never hidden
        receipt["store_text_freshness"] = {"error": str(exc)[:200]}
    gaps_path = out_dir / "enrichment_gap_records.jsonl"
    receipt["gap_records_written"] = _write_gaps(cards, receipt, gaps_path)
    print(json.dumps({k: receipt[k] for k in ("total_cards", "field_coverage", "store_coverage",
                                              "derivability", "gap_records_written", "store_text_freshness",
                                              "ratchet_regressions")}, indent=2, sort_keys=True))
    print(f"\ngaps:    {gaps_path}")
    if regressions:
        # the BASELINE is preserved on regression (review finding: overwriting it made any retry go green);
        # the regressed receipt lands in a side file for forensics.
        side = out_dir / "enrichment_coverage_receipt.regressed.json"
        side.write_text(json.dumps(receipt, indent=2, sort_keys=True))
        print(f"RATCHET RED: {regressions}\nregressed receipt: {side} (baseline preserved: {prev_path})")
        return 1
    prev_path.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    print(f"written: {prev_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="full-corpus coverage receipt + gap records + ratchet")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
