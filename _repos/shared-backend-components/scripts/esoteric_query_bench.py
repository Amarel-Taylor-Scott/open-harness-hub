#!/usr/bin/env python3
"""scripts.esoteric_query_bench — UNIQUE/adversarial query-robustness probes no standard IR bench covers: a
ZOO of deterministic text corruptions (hash-seeded — zero randomness at run time) applied to known-item
queries over the FULL corpus, measuring how each retrieval path degrades under each corruption.

The probe zoo (each a pure transform; expanding = a new row, never a rewrite): keyboard-neighbor typo ·
word rotation · head/tail truncation · verbose padding · snake_case code-speak · leetspeak · vowel deletion ·
stopword deletion · word stutter · SMS abbreviation · noise-char injection. Known-item probe = a card must be
found from its OWN corrupted title (labels-free, so the full 112K corpus is testable without gold labelling).

Retrievers raced per probe: lexical inverted index · dense STORED blackbox lane · their RRF fusion — the
receipt shows, per corruption, which path survives (dense tends to survive character noise, lexical survives
word-order noise; fusion should dominate).

serves_truth=false — degradation numbers are measurements, never served truth.

    PYTHONPATH=. python3 scripts/esoteric_query_bench.py --self-test
    PYTHONPATH=. python3 scripts/esoteric_query_bench.py --run [--query-sample 150] [--k 5]
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
import zlib  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_DEFAULT_K = 5
_DEFAULT_QUERY_SAMPLE = 150
#: fixed QWERTY neighbor map for the keyboard-typo probe (single source; deterministic)
_KEYBOARD_NEIGHBOR = {"a": "s", "b": "v", "c": "x", "d": "f", "e": "r", "f": "g", "g": "h", "h": "j",
                      "i": "o", "j": "k", "k": "l", "l": "k", "m": "n", "n": "m", "o": "p", "p": "o",
                      "q": "w", "r": "t", "s": "d", "t": "y", "u": "i", "v": "b", "w": "e", "x": "c",
                      "y": "u", "z": "x"}
_LEET = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5"}
_SMS = {"please": "pls", "you": "u", "to": "2", "for": "4", "and": "&", "with": "w/", "are": "r",
        "be": "b", "see": "c", "at": "@"}
_STOPWORDS = {"a", "an", "the", "of", "in", "on", "to", "for", "and", "or", "with", "from", "by", "into"}
_VOWELS = set("aeiou")
_PAD_PREFIX = ("hey so i was working on something earlier and i think what i really need here, "
               "if that makes sense, is basically ")
_PAD_SUFFIX = (" — or at least something along those lines, ideally soon because this is blocking me, "
               "thanks a lot in advance!!")


def _crc(text: str) -> int:
    """The one deterministic seed: same text -> same integer, no run-time randomness anywhere."""
    return zlib.crc32(text.encode())


# ── the PROBE ZOO — every transform is pure, deterministic, and safe on short/unicode input ──────────────────
def _p_keyboard_typo(q: str) -> str:
    letters = [i for i, ch in enumerate(q) if ch.lower() in _KEYBOARD_NEIGHBOR]
    if not letters:
        return q
    i = letters[_crc(q) % len(letters)]
    repl = _KEYBOARD_NEIGHBOR[q[i].lower()]
    return q[:i] + (repl.upper() if q[i].isupper() else repl) + q[i + 1:]


def _p_word_rotate(q: str) -> str:
    words = q.split()
    if len(words) < 2:
        return q
    r = 1 + _crc(q) % (len(words) - 1)
    return " ".join(words[r:] + words[:r])


def _p_truncate_head(q: str) -> str:
    return " ".join(q.split()[:3])


def _p_truncate_tail(q: str) -> str:
    return " ".join(q.split()[-3:])


def _p_verbose_padding(q: str) -> str:
    return f"{_PAD_PREFIX}{q}{_PAD_SUFFIX}"


def _p_code_speak(q: str) -> str:
    return "_".join(w.lower() for w in q.split())


def _p_leetspeak(q: str) -> str:
    return "".join(_LEET.get(ch.lower(), ch) for ch in q)


def _p_vowel_drop(q: str) -> str:
    out = []
    for w in q.split():
        out.append("".join(ch for ch in w if ch.lower() not in _VOWELS) if len(w) > 4 else w)
    return " ".join(w for w in out if w)


def _p_stopword_drop(q: str) -> str:
    kept = [w for w in q.split() if w.lower() not in _STOPWORDS]
    return " ".join(kept) if kept else q


def _p_stutter(q: str) -> str:
    words = q.split()
    if not words:
        return q
    i = _crc(q) % len(words)
    return " ".join(words[:i + 1] + [words[i]] + words[i + 1:])


def _p_sms_abbrev(q: str) -> str:
    return " ".join(_SMS.get(w.lower(), w) for w in q.split())


def _p_char_noise(q: str) -> str:
    if not q:
        return q
    i = _crc(q) % (len(q) + 1)
    return q[:i] + "#" + q[i:]


#: fixed synonym + language tables (single-source; deterministic — the design-fleet rows, culled to the
#: measurable ones: negation_injection was rejected as measurement-ambiguous for a known-item harness)
_SYNONYM = {"remove": "delete", "records": "rows", "clean": "tidy", "merge": "combine", "build": "create",
            "fetch": "retrieve", "check": "verify", "fix": "repair", "batch": "bundle"}
_LANG_SWAP = {"the": "el", "and": "und", "for": "para", "with": "mit", "from": "von",
              "data": "datos", "records": "registros", "rows": "filas"}


def _p_emoji_decorate(q: str) -> str:
    return f"🚀 {q} 🙏"


def _p_synonym_flip(q: str) -> str:
    return " ".join(_SYNONYM.get(w.lower(), w) for w in q.split())


def _p_lang_swap(q: str) -> str:
    return " ".join(_LANG_SWAP.get(w.lower(), w) for w in q.split())


#: the zoo: name -> pure transform. A new probe = a new row here (multi-path law); never edit an existing one
#: (its receipts would silently change meaning).
PROBES: dict[str, Callable[[str], str]] = {
    "keyboard_typo": _p_keyboard_typo,
    "word_rotate": _p_word_rotate,
    "truncate_head": _p_truncate_head,
    "truncate_tail": _p_truncate_tail,
    "verbose_padding": _p_verbose_padding,
    "code_speak": _p_code_speak,
    "leetspeak": _p_leetspeak,
    "vowel_drop": _p_vowel_drop,
    "stopword_drop": _p_stopword_drop,
    "stutter": _p_stutter,
    "sms_abbrev": _p_sms_abbrev,
    "char_noise": _p_char_noise,
    "emoji_decorate": _p_emoji_decorate,
    "synonym_flip": _p_synonym_flip,
    "lang_swap": _p_lang_swap,
}


# ── the known-item harness (reuses path_graph_bench's retriever shapes; stored dense lane) ────────────────────
def _retrievers(cards: list[dict[str, Any]], k: int) -> dict[str, Callable[[str], list[str]]]:
    from scripts import rank_fusion_zoo as _f  # noqa: PLC0415
    from scripts import path_graph_bench as _bench  # noqa: PLC0415  REUSE: dense index + topk
    from scripts.build_primitive_search_index import build_index, search_with_stats  # noqa: PLC0415
    index = build_index(cards)
    dense = _bench.build_dense_index(cards)

    def _lex(q: str, kk: int = k) -> list[str]:
        hits, _stats = search_with_stats(q, kk, index)
        return [h["primitive_id"] for h in hits]

    def _den(q: str, kk: int = k) -> list[str]:
        return _bench.dense_topk(q, dense, kk)

    def _fuse(q: str) -> list[str]:
        return [r["primitive_id"] for r in _f.rrf({"lexical": _lex(q, k * 4), "dense": _den(q, k * 4)})][:k]

    return {"lexical": _lex, "dense": _den, "fusion": _fuse}


def measure(cards: list[dict[str, Any]], *, k: int = _DEFAULT_K,
            query_sample: int = _DEFAULT_QUERY_SAMPLE) -> dict[str, Any]:
    """Per-probe, per-retriever known-item recall@k over ``cards`` (deterministic stride sample of queries),
    against the CLEAN baseline — degradation = clean_recall - probe_recall."""
    from scripts import capability_embedding as _emb  # noqa: PLC0415
    step = max(1, len(cards) // max(1, query_sample))  # guard --query-sample 0 (review finding)
    sample = [c for c in cards[::step] if str(c.get("title") or _emb.blackbox_text(c))[:60].strip()][:query_sample]
    rets = _retrievers(cards, k)
    # CLEAN outcomes precomputed ONCE per card per retriever; each probe is then scored over the queries it
    # actually CHANGED, against the clean baseline ON THAT SAME SUBSET — identity-transformed queries no
    # longer dilute degradation with forced zeros (review finding, confirmed HIGH).
    base_qs = [str(c.get("title") or _emb.blackbox_text(c))[:60] for c in sample]
    # duplicate-title tie handling (review finding, MEDIUM): known-item credit is shared by TITLE-IDENTICAL
    # cards — when several cards carry the same title, retrieving any of them IS finding the content.
    title_of = {c.get("primitive_id"): " ".join(str(c.get("title") or "").lower().split()) for c in cards}

    def _found(gold_card: dict[str, Any], returned_ids: list) -> bool:
        gid = gold_card.get("primitive_id")
        if gid in returned_ids:
            return True
        gt = title_of.get(gid, "")
        return bool(gt) and any(title_of.get(i) == gt for i in returned_ids)

    clean_hit: dict[str, list[bool]] = {name: [] for name in rets}
    for c, base_q in zip(sample, base_qs):
        for name, fn in rets.items():
            clean_hit[name].append(_found(c, fn(base_q)))
    n = len(sample) or 1
    out: dict[str, Any] = {"clean": {"recall_at_k": {name: round(sum(v) / n, 4)
                                                     for name, v in clean_hit.items()},
                                     "transform_changed_query_rate": 0.0}}
    degradation: dict[str, Any] = {}
    for mode, transform in PROBES.items():
        idx = [i for i, q in enumerate(base_qs) if transform(q) != q]
        m = len(idx) or 1
        per = {name: 0 for name in rets}
        for i in idx:
            q = transform(base_qs[i])
            for name, fn in rets.items():
                if _found(sample[i], fn(q)):
                    per[name] += 1
        probe_recall = {name: round(hits / m, 4) for name, hits in per.items()}
        clean_sub = {name: round(sum(clean_hit[name][i] for i in idx) / m, 4) for name in rets}
        out[mode] = {"recall_at_k": probe_recall, "clean_recall_on_changed": clean_sub,
                     "n_changed": len(idx), "transform_changed_query_rate": round(len(idx) / n, 4)}
        degradation[mode] = {name: round(clean_sub[name] - probe_recall[name], 4) for name in rets}
    survivors = {mode: max(vals["recall_at_k"], key=lambda nm, v=vals: (v["recall_at_k"][nm], nm))
                 for mode, vals in out.items() if mode != "clean"}
    return {"record_type": "esoteric_query_benchmark", "corpus_cards": len(cards), "k": k,
            "query_sample": len(sample), "probes": sorted(PROBES),
            "recall_by_mode": out, "degradation_vs_clean": degradation,
            "best_retriever_per_probe": survivors,
            "note": "known-item probe (find a card from its own CORRUPTED title); every transform is pure + "
                    "hash-seeded (deterministic). Degradation is attributable per corruption; the best "
                    "retriever per probe shows which path survives which noise.", **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # (a) every probe is DETERMINISTIC (same input -> same output twice) and SAFE on short/empty/unicode input
    samples = ["deduplicate customer records from the batch", "ocr", "", "résumé parser für PDF", "a b"]
    checks.append(("every probe is deterministic on every sample (twice, byte-identical)",
                   all(fn(s) == fn(s) for fn in PROBES.values() for s in samples)))
    checks.append(("every probe is safe on short/empty/unicode input (returns a string, never raises)",
                   all(isinstance(fn(s), str) for fn in PROBES.values() for s in samples)))
    # (b) every probe actually CHANGES a normal query (a no-op probe measures nothing)
    normal = "deduplicate the customer records in this batch for me"
    changed = [name for name, fn in PROBES.items() if fn(normal) != normal]
    checks.append(("every probe transforms a normal query (no silent no-op rows)",
                   sorted(changed) == sorted(PROBES)))
    # (c) hermetic known-item run: clean recall is perfect on a tiny distinct corpus; corrupted modes are
    #     measured per probe per retriever; receipt is deterministic
    cards = [{"primitive_id": f"q:{w}", "title": f"{w} processor engine",
              "blackbox": f"A component that performs {w} on incoming data rows.",
              "input_edge": "In", "output_edge": "Out", **BOUNDARY}
             for w in ("deduplication", "translation", "encryption", "compression", "validation")]
    rec = measure(cards, k=2, query_sample=5)
    checks.append(("clean known-item recall is perfect on a tiny distinct corpus (the harness works)",
                   rec["recall_by_mode"]["clean"]["recall_at_k"]["lexical"] == 1.0))
    checks.append(("every probe reports recall for every retriever (full grid, no silent gaps)",
                   all(set(rec["recall_by_mode"][m]["recall_at_k"]) == {"lexical", "dense", "fusion"}
                       for m in rec["recall_by_mode"])))
    checks.append(("degradation is computed per probe vs clean (attributable)",
                   set(rec["degradation_vs_clean"]) == set(PROBES)))
    checks.append(("the receipt is deterministic (byte-identical twice)",
                   json.dumps(measure(cards, k=2, query_sample=5), sort_keys=True)
                   == json.dumps(measure(cards, k=2, query_sample=5), sort_keys=True)))
    checks.append(("receipt is candidate/serves_truth=false", rec["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - esoteric_query_bench: {len(PROBES)} deterministic hash-seeded corruption probes "
          f"(keyboard/rotation/truncation/padding/code-speak/leet/vowel-drop/stopword-drop/stutter/sms/noise) "
          f"raced over lexical + stored-dense + fusion on a known-item harness — every probe transforms, "
          f"every degradation attributable, byte-identical receipts. serves_truth=false.")
    return 0


def _run(k: int, query_sample: int) -> int:
    from scripts import path_graph_bench as _bench  # noqa: PLC0415  REUSE: the corpus loader
    cards = _bench._load_scale_corpus(None)  # noqa: SLF001
    print(f"esoteric probes over {len(cards)} cards, {len(PROBES)} corruptions x 3 retrievers ...")
    rec = measure(cards, k=k, query_sample=query_sample)
    out = resource("data") / "dev-intel" / "session_emulation" / "esoteric_query_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({"clean": rec["recall_by_mode"]["clean"]["recall_at_k"],
                      "degradation_vs_clean": rec["degradation_vs_clean"],
                      "best_retriever_per_probe": rec["best_retriever_per_probe"]}, indent=2, sort_keys=True))
    print(f"\nwritten: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="full-corpus probe race + receipt")
    ap.add_argument("--k", type=int, default=_DEFAULT_K)
    ap.add_argument("--query-sample", type=int, default=_DEFAULT_QUERY_SAMPLE)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.k, args.query_sample)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
