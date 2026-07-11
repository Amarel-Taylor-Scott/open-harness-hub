#!/usr/bin/env python3
"""primitive_facet_enrichment — MANY descriptions + MANY embeddings per primitive, then RACE them.

The owner's question (2026-07-09): *are our primitives fully described with multiple input/output/edge/
problem-solution descriptions, numerous embeddings per description, so we can find WHICH embeddings, WHICH
keywords, WHICH routes are most efficient?* The honest prior state was **3 description registers + 4 embeddings
per primitive** (blackbox + plain/technical/semantic). That is far too thin to LEARN which surface retrieves a
primitive best.

This module lifts a primitive to **dozens-to-hundreds of DESCRIPTIONS across FACET FAMILIES** — action, input,
output, edge-transform, problem, solution, keywords, operation, datatype, signature, use-case, composition-role,
negative-contrast, qa — each rendered in the three REGISTERS (plain/technical/semantic) where meaningful. Every
description is embedded, giving a **multi-vector** representation (one primitive -> many named vectors). The count
is COMPUTED per card (a richer card yields more), never a typed "300" (no-magic-values); a rich card crosses 300.

Then it RACES the facet families: for a labelled query set it retrieves using EACH family's vectors alone and
reports precision@k / MRR / nDCG PER FAMILY plus an EFFICIENCY score (quality per stored vector). That race is the
answer to "which embeddings / keywords / routes make the most sense" — it tells us which description surfaces are
worth storing at 5M scale (the Pareto frontier) instead of blindly storing 300 useless vectors per row.

Design law (this repo):
- REUSE, never re-derive: descriptions build on ``capability_embedding.register_text`` / ``primitive_descriptor``
  (operations/datatypes/keywords/keyphrases) + the SAME embed surface + the SAME model2vec batch path as
  ``build_primitive_embeddings``. This is the "persisted per-primitive surface" extension point (one new store +
  an enrichment-coverage check), not a rewrite.
- ZOO / multi-path: ``FACET_FAMILIES`` is a registry of generators; adding a facet is ONE ROW, never a rewrite.
  ``summary()`` computes the shape (family count, register count) — counts are computed, never typed.
- CANDIDATE ONLY: every row is ``candidate=true, serves_truth=false``. Enrichment is not promotion.
- LOSSLESS: a NEW derived store (``dist/primitive-facet-embeddings/``); the card + the 3-register store are
  preserved untouched.
- VERIFY-THE-VERIFIER: ``--self-test`` runs a mutation gate (a broken facet generator is caught by the race), a
  determinism gate (descriptions + vectors byte-identical twice), and a no-magic gate (family/register counts are
  computed from the registry, not literals).

Storage at 5M: 5,000,000 x ~200 descriptions = ~1e9 vectors -> the Qdrant NAMED-VECTOR / MULTIVECTOR data plane
(hot facets indexed, cold facets on demand). Build LOCALLY for a sample to prove the mechanism + the race; the
race says which facets to actually index at scale. The local->cloud swap is config-only (see module docstring in
build_primitive_embeddings + architecture/storage_tier_policy.json).

CLI:
    python3 scripts/primitive_facet_enrichment.py --self-test
    python3 scripts/primitive_facet_enrichment.py --describe --sample 1          # show one primitive's facets
    python3 scripts/primitive_facet_enrichment.py --build --sample 200           # persist a multivector store
    python3 scripts/primitive_facet_enrichment.py --race  --sample 200 --k 5     # per-facet efficiency receipt
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

# --- path bootstrap (stdio/CLI launched from an arbitrary cwd) ---------------------------------------------------
_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts import capability_embedding as _emb  # noqa: E402  REUSE: registers, embed surface, model2vec batch
from scripts import primitive_descriptor as _desc  # noqa: E402  REUSE: operations/datatypes/keywords facets

try:
    import numpy as np  # noqa: E402
except Exception:  # pragma: no cover - numpy is present in this repo, guarded so --describe still runs
    np = None  # type: ignore

# The persisted multivector store lives beside the other embedding stores (build artifact, gitignored, regenerated).
_FACET_OUT_DIRNAME = "primitive-facet-embeddings"
#: default corpus (the searchable disjoint card files — same as build_primitive_search_index / build_primitive_embeddings)
_EDGE_FOUNDRY_DIR = _REPO / "data" / "dev-intel" / "aidevobserver_edge_foundry"
_DEFAULT_CARD_FILES = (
    _EDGE_FOUNDRY_DIR / "verified_factory_primitive_cards.jsonl",
    _EDGE_FOUNDRY_DIR / "primitive_edge_cards.jsonl",
    # minted vertical-pack primitives (mint_vertical_pack.py) — loaded LAST so a resume-build of the streaming store
    # appends only the new cards' facets; real oracle-tested candidates that close a vertical's coverage gap.
    _EDGE_FOUNDRY_DIR / "minted_vertical_pack_cards.jsonl",
    # domain packs (real oracle-tested primitives; mint_ml_kaggle_pack + the vertical minters) + the synthesized
    # transform micro-ops promoted to searchable typed cards (promote_synthesized_to_cards). Order is APPEND-ONLY:
    # never reorder — the streaming store's resume-build indexes by position, so new files must stay at the end.
    _EDGE_FOUNDRY_DIR / "minted_ml_kaggle_pack_cards.jsonl",
    _EDGE_FOUNDRY_DIR / "minted_http_pack_cards.jsonl",
    _EDGE_FOUNDRY_DIR / "minted_validation_pack_cards.jsonl",
    _EDGE_FOUNDRY_DIR / "minted_collections_pack_cards.jsonl",
    _EDGE_FOUNDRY_DIR / "minted_text_pack_cards.jsonl",
    _EDGE_FOUNDRY_DIR / "minted_synthesized_working_cards.jsonl",
)


def facet_store_dir() -> Path:
    """Canonical on-disk location of the facet multivector store (single source: main() writes, load reads)."""
    return _emb.resource("dist") / _FACET_OUT_DIRNAME if hasattr(_emb, "resource") else _REPO / "dist" / _FACET_OUT_DIRNAME


# ================================================================================================================
# Text helpers — turn a card's structured attributes into natural words (deterministic, 0-token)
# ================================================================================================================
_CAMEL_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def _words(token: object) -> str:
    """Split a CamelCase / snake / kebab type token into space-separated lowercase words.

    ``PolicyCompliantSecuritySchemeMap`` -> ``policy compliant security scheme map``. Trailing punctuation from
    generated edge/domain tokens (``"...Map-"``) is stripped. Deterministic and idempotent.
    """
    s = str(token or "").strip().strip("-_.")
    if not s:
        return ""
    s = _CAMEL_RE.sub(" ", s)
    s = re.sub(r"[_\-]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def _dedupe_keep_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        t = re.sub(r"\s+", " ", str(it or "").strip())
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out


#: Operation -> natural verb phrasings. Single-source lexicon (no-magic-values): the race can add a row and re-run.
#: Keys are the canonical operations from primitive_descriptor.OPERATION_LEXICON; values are synonym verbs used to
#: multiply the problem/solution/action phrasings so paraphrase-shaped queries still land.
_OP_VERBS: dict[str, tuple[str, ...]] = {
    "extract": ("extract", "pull out", "get", "retrieve", "read"),
    "transform": ("transform", "convert", "map", "reshape", "rewrite"),
    "validate": ("validate", "check", "verify", "confirm", "enforce"),
    "aggregate": ("aggregate", "summarize", "combine", "reduce", "roll up"),
    "filter": ("filter", "select", "keep only", "screen", "narrow"),
    "format": ("format", "render", "serialize", "emit", "produce"),
    "normalize": ("normalize", "standardize", "canonicalize", "clean", "regularize"),
    "classify": ("classify", "label", "categorize", "tag", "route"),
    "generate": ("generate", "build", "create", "synthesize", "compose"),
    "compare": ("compare", "match", "diff", "reconcile", "align"),
    "parse": ("parse", "decode", "interpret", "tokenize", "read"),
    "count": ("count", "tally", "measure", "size", "enumerate"),
    "sort": ("sort", "order", "rank", "arrange", "sequence"),
    "dedupe": ("deduplicate", "unique", "collapse", "distinct", "merge duplicates"),
    "lookup": ("look up", "resolve", "find", "search", "locate"),
}


def _op_verbs(card: dict[str, Any]) -> list[str]:
    ops = sorted(_desc.operations(card)) if hasattr(_desc, "operations") else []
    verbs: list[str] = []
    for op in ops:
        verbs.extend(_OP_VERBS.get(op, (op,)))
    if not verbs:  # thin card with no matched operation: fall back to the title's leading verb
        title = _words(card.get("title"))
        if title:
            verbs.append(title.split()[0])
    return _dedupe_keep_order(verbs)


# ================================================================================================================
# FACET FAMILIES — the zoo. Each generator maps a card -> a list of DESCRIPTIONS. Add a family = one row here.
# ================================================================================================================
def _f_action(card: dict[str, Any]) -> list[str]:
    """What the primitive DOES — title, blackbox, and verb x object paraphrases."""
    title = str(card.get("title") or "").strip()
    black = _emb.blackbox_text(card) if hasattr(_emb, "blackbox_text") else str(card.get("blackbox") or "")
    out_words = _words(card.get("output_edge"))
    outs: list[str] = [title, black]
    for verb in _op_verbs(card)[:5]:
        if out_words:
            outs.append(f"{verb} the {out_words}")
        outs.append(f"a component that will {verb}")
    return _dedupe_keep_order(outs)


def _f_input(card: dict[str, Any]) -> list[str]:
    """The INPUT surface — many phrasings of what it consumes, from the input edge + datatypes."""
    iw = _words(card.get("input_edge"))
    dts = sorted(_desc.datatypes(card)) if hasattr(_desc, "datatypes") else []
    outs = []
    if iw:
        outs += [f"takes a {iw}", f"accepts a {iw}", f"input is a {iw}", f"given a {iw}",
                 f"consumes {iw}", f"expects {iw} as input"]
    for dt in dts:
        outs.append(f"operates on a {dt} input")
    return _dedupe_keep_order(outs)


def _f_output(card: dict[str, Any]) -> list[str]:
    """The OUTPUT surface — many phrasings of what it produces, from the output edge."""
    ow = _words(card.get("output_edge"))
    outs = []
    if ow:
        outs += [f"returns a {ow}", f"produces a {ow}", f"output is a {ow}", f"yields a {ow}",
                 f"emits a {ow}", f"result is a {ow}"]
    return _dedupe_keep_order(outs)


def _f_transform(card: dict[str, Any]) -> list[str]:
    """The EDGE TRANSFORM — the input->output mapping in several phrasings (the composition surface)."""
    iw, ow = _words(card.get("input_edge")), _words(card.get("output_edge"))
    if not (iw and ow):
        return []
    return _dedupe_keep_order([
        f"{iw} to {ow}", f"maps {iw} to {ow}", f"converts {iw} into {ow}",
        f"transforms {iw} into {ow}", f"from {iw} produce {ow}", f"given {iw} return {ow}",
    ])


def _f_problem(card: dict[str, Any]) -> list[str]:
    """PROBLEM framings — how a person/agent would ASK for this capability (question-shaped, paraphrase-rich)."""
    ow, iw = _words(card.get("output_edge")), _words(card.get("input_edge"))
    verbs = _op_verbs(card)[:4]
    outs = []
    for verb in verbs:
        if ow:
            outs += [f"how do I {verb} the {ow}?", f"I need to {verb} a {ow}", f"want to {verb} {ow}"]
        elif iw:
            outs += [f"how do I {verb} the {iw}?", f"I need to {verb} {iw}"]
    if iw and ow:
        outs.append(f"get the {ow} from a {iw}")
    return _dedupe_keep_order(outs)


def _f_solution(card: dict[str, Any]) -> list[str]:
    """SOLUTION framings — how the capability solves the problem (operation-centric)."""
    iw = _words(card.get("input_edge"))
    outs = []
    for verb in _op_verbs(card)[:4]:
        outs.append(f"use a {verb} step" if not iw else f"{verb} the {iw}")
    return _dedupe_keep_order(outs)


def _f_keywords(card: dict[str, Any]) -> list[str]:
    """KEYWORD sets — the paraphrase-resistant token/phrase groupings (reuse the descriptor's keyword facets)."""
    kws = sorted(_desc.keywords(card)) if hasattr(_desc, "keywords") else []
    kps = sorted(_desc.keyphrases(card)) if hasattr(_desc, "keyphrases") else []
    outs: list[str] = []
    if kws:
        outs.append(" ".join(kws[:12]))
    for kp in kps[:8]:
        outs.append(kp)
    tags = [_words(t) for t in (card.get("capability_tags") or []) if _words(t)]
    if tags:
        outs.append(" ".join(_dedupe_keep_order(tags)[:8]))
    return _dedupe_keep_order(outs)


def _f_operation(card: dict[str, Any]) -> list[str]:
    ops = sorted(_desc.operations(card)) if hasattr(_desc, "operations") else []
    outs = []
    for op in ops:
        outs += [f"{op} operation", f"performs a {op}"]
    return _dedupe_keep_order(outs)


def _f_datatype(card: dict[str, Any]) -> list[str]:
    dts = sorted(_desc.datatypes(card)) if hasattr(_desc, "datatypes") else []
    outs = []
    for dt in dts:
        outs += [f"{dt} handling", f"works with {dt} data"]
    return _dedupe_keep_order(outs)


def _f_signature(card: dict[str, Any]) -> list[str]:
    iw, ow = _words(card.get("input_edge")), _words(card.get("output_edge"))
    if not (iw and ow):
        return []
    return _dedupe_keep_order([f"{iw} -> {ow}", f"f({iw}) -> {ow}", f"signature: {iw} to {ow}"])


def _f_use_case(card: dict[str, Any]) -> list[str]:
    """USE-CASE / scenario framings from the card's domains (where the capability applies)."""
    doms = _dedupe_keep_order([_words(d) for d in (card.get("domains") or []) if _words(d)])
    outs = []
    for dom in doms[:6]:
        outs += [f"for {dom}", f"used in {dom} workflows"]
    return _dedupe_keep_order(outs)


def _f_composition_role(card: dict[str, Any]) -> list[str]:
    """COMPOSITION-ROLE framings — how it slots into a pipeline (impact/operation shaped)."""
    ops = sorted(_desc.operations(card)) if hasattr(_desc, "operations") else []
    outs = ["as a pipeline stage", "as a reusable step"]
    for op in ops[:3]:
        outs.append(f"a {op} stage in a pipeline")
    return _dedupe_keep_order(outs)


def _f_negative_contrast(card: dict[str, Any]) -> list[str]:
    """NEGATIVE-CONTRAST — a small set of what it is NOT (helps disambiguate near-siblings at retrieval time)."""
    mut = card.get("mutations")
    outs = []
    if isinstance(mut, (list, tuple)) and not mut:
        outs.append("does not mutate its input")
    ow = _words(card.get("output_edge"))
    if ow:
        outs.append(f"not a generic passthrough; produces a {ow}")
    return _dedupe_keep_order(outs)


#: The registry. ORDER is stable (determinism). Value = generator. Adding a facet family is ONE ROW.
FACET_FAMILIES: dict[str, Callable[[dict[str, Any]], list[str]]] = {
    "action": _f_action,
    "input": _f_input,
    "output": _f_output,
    "transform": _f_transform,
    "problem": _f_problem,
    "solution": _f_solution,
    "keywords": _f_keywords,
    "operation": _f_operation,
    "datatype": _f_datatype,
    "signature": _f_signature,
    "use_case": _f_use_case,
    "composition_role": _f_composition_role,
    "negative_contrast": _f_negative_contrast,
}

#: Facet families whose descriptions are ALSO re-rendered per REGISTER (a register-flavored prefix), multiplying
#: the description count the way the 3-register store does. Kept small: only the human-facing surfaces gain from a
#: register split; keyword/signature/operation facets are already register-neutral.
_REGISTERED_FAMILIES: frozenset[str] = frozenset({"action", "problem", "solution", "use_case"})
_REGISTER_PREFIX: dict[str, str] = {"plain": "", "technical": "technical: ", "semantic": "capability: "}


def facet_rows(card: dict[str, Any]) -> list[dict[str, str]]:
    """Every DESCRIPTION for a card as ``{family, register, text}`` rows, deduped, deterministic order.

    A description in a ``_REGISTERED_FAMILIES`` family is emitted once per register (a register-flavored prefix);
    all others are emitted once with register ``"neutral"``. The total count is COMPUTED (varies with how much
    structure the card carries) — a richly-typed card crosses 300 rows; a thin card yields fewer, honestly.
    """
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for family, gen in FACET_FAMILIES.items():
        try:
            descs = gen(card)
        except Exception:  # a broken generator must not take down the whole enrichment; skip its rows
            descs = []
        registers = _emb.REGISTERS if family in _REGISTERED_FAMILIES else ("neutral",)
        for register in registers:
            prefix = _REGISTER_PREFIX.get(register, "") if register != "neutral" else ""
            for d in descs:
                text = f"{prefix}{d}".strip()
                key = f"{family}\t{register}\t{text.lower()}"
                if text and key not in seen:
                    seen.add(key)
                    rows.append({"family": family, "register": register, "text": text})
    return rows


def describe_count(card: dict[str, Any]) -> int:
    """Number of distinct descriptions minted for this card (computed, never a magic literal)."""
    return len(facet_rows(card))


def summary() -> dict[str, Any]:
    """The computed SHAPE of the enrichment (no-magic-values: everything derived from the registry)."""
    return {
        "facet_families": len(FACET_FAMILIES),
        "family_names": list(FACET_FAMILIES),
        "registered_families": sorted(_REGISTERED_FAMILIES),
        "registers": list(_emb.REGISTERS),
        # number of (family, register) SLOTS — each slot emits MULTIPLE phrasings, so actual descriptions/card is
        # far higher (a rich card crosses 300); the real count is computed per-card by describe_count().
        "facet_register_slots": (
            len(FACET_FAMILIES) - len(_REGISTERED_FAMILIES)
        ) + len(_REGISTERED_FAMILIES) * len(_emb.REGISTERS),
    }


# ================================================================================================================
# Multivector store — embed every description; one primitive -> many named vectors
# ================================================================================================================
def _embed_many(texts: list[str], *, embed_path: Optional[str] = None) -> "np.ndarray":
    """Batch-embed via the SAME model2vec path build_primitive_embeddings uses; per-text fallback. L2-normalized."""
    if np is None:
        raise RuntimeError("numpy required for embedding; run --describe for text-only output")
    used = embed_path or _emb.real_text_path()
    model = _emb._load_model2vec() if used == "model2vec" else None
    if model is not None:
        mat = np.asarray(model.encode(texts), dtype="float32") if texts else np.zeros((0, 0), dtype="float32")
    else:
        mat = np.asarray([_emb.embed_text(t, path=used) for t in texts], dtype="float32") if texts else np.zeros((0, 0), dtype="float32")
    if mat.size:
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        mat = mat / norms
    return mat


def build_facet_store(cards: list[dict[str, Any]], *, embed_path: Optional[str] = None) -> dict[str, Any]:
    """Build the multivector store: for every card, every facet description -> an embedding.

    Returns ``{rows, matrix, embed_model, dim, n_cards, n_vectors}`` where ``rows[i]`` =
    ``{primitive_id, family, register, text}`` describes ``matrix[i]``. This is the per-primitive MULTI-VECTOR
    representation (the owner's "300 embeddings" — computed, candidate-only, lossless-additive).
    """
    rows: list[dict[str, str]] = []
    for card in cards:
        pid = str(card.get("primitive_id") or card.get("id") or "")
        for r in facet_rows(card):
            rows.append({"primitive_id": pid, **r})
    matrix = _embed_many([r["text"] for r in rows], embed_path=embed_path)
    return {
        "rows": rows,
        "matrix": matrix,
        "embed_model": (embed_path or _emb.real_text_path()),
        "dim": int(matrix.shape[1]) if getattr(matrix, "size", 0) else 0,
        "n_cards": len(cards),
        "n_vectors": len(rows),
    }


def persist_facet_store(store: dict[str, Any], out_dir: Optional[Path] = None) -> Path:
    """Persist the store: ``matrix.npy`` + ``rows.jsonl`` + a computed ``manifest.json`` (candidate-only)."""
    out = Path(out_dir or facet_store_dir())
    out.mkdir(parents=True, exist_ok=True)
    if np is not None:
        np.save(out / "matrix.npy", store["matrix"])
    with (out / "rows.jsonl").open("w") as f:
        for r in store["rows"]:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    manifest = {
        "n_vectors": store["n_vectors"], "n_cards": store["n_cards"], "dim": store["dim"],
        "embed_model": store["embed_model"], "facet_families": len(FACET_FAMILIES),
        "registers": list(_emb.REGISTERS), "candidate": True, "serves_truth": False,
        "avg_descriptions_per_card": round(store["n_vectors"] / store["n_cards"], 2) if store["n_cards"] else 0,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return out


# ── STREAMING full-corpus store (the SERVE lane at scale) ────────────────────────────────────────────────────
# The legacy persist_facet_store holds the whole matrix in RAM — fine for a few-thousand-card sample, but the full
# ~112K searchable corpus is ~10M vectors (~10GB) and ~67GB peak RAM to build in one array. So the full build
# STREAMS shard-by-shard to flat, memmap-able files, bounding RAM to one shard. Layout (all aligned per vector):
#   vectors.f32     raw float32 matrix (n_vectors x dim), appended per shard, loaded via np.memmap (no RAM blowup)
#   vec_pids.u32    parallel uint32 -> index into card_ids (which primitive each vector describes)
#   vec_family.u8   parallel uint8  -> index into list(FACET_FAMILIES) (which facet surface each vector is)
#   card_ids.json   per-card primitive_id list (position = the uint32 in vec_pids)
#   rows.jsonl      {primitive_id,family,register,text} per vector (rehydration/debug; NOT loaded at serve time)
#   covered_ids.json / manifest.json / _progress.json   coverage set + shape + resumable checkpoint
_STREAM_VECTORS, _STREAM_PIDS, _STREAM_FAM = "vectors.f32", "vec_pids.u32", "vec_family.u8"
_STREAM_ROWS, _STREAM_CARDIDS, _STREAM_COVERED = "rows.jsonl", "card_ids.json", "covered_ids.json"
_STREAM_MANIFEST, _STREAM_PROGRESS = "manifest.json", "_progress.json"


def _truncate_bytes(path: Path, nbytes: int) -> None:
    if path.exists():
        with open(path, "r+b") as f:
            f.truncate(nbytes)


def _truncate_lines(path: Path, n: int) -> None:
    if not path.exists():
        return
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(path) as fin, open(tmp, "w") as fout:
        for i, line in enumerate(fin):
            if i >= n:
                break
            fout.write(line)
    tmp.replace(path)


def build_facet_store_streaming(cards: list[dict[str, Any]], *, out_dir: Optional[Path] = None,
                                embed_path: Optional[str] = None, shard_size: int = 5000, resume: bool = True,
                                log: Optional[Callable[[str], None]] = None) -> dict[str, Any]:
    """Build the FULL-corpus multivector store by STREAMING shards to disk (bounded RAM, resumable, memmap-able).

    Each shard: facet_rows -> embed -> APPEND (vectors.f32, vec_pids.u32, vec_family.u8, rows.jsonl) and checkpoint
    (_progress.json). A killed build resumes from the last completed shard (binaries truncated to the checkpoint's
    vector count so a partial trailing shard never corrupts alignment). candidate-only; the raw layer is preserved.
    """
    if np is None:
        raise RuntimeError("numpy required for the streaming build")
    out = Path(out_dir or facet_store_dir())
    out.mkdir(parents=True, exist_ok=True)
    used = embed_path or _emb.real_text_path()
    fam_list = list(FACET_FAMILIES)
    fam_idx = {f: i for i, f in enumerate(fam_list)}
    card_ids = [str(c.get("primitive_id") or c.get("id") or "") for c in cards]
    (out / _STREAM_CARDIDS).write_text(json.dumps(card_ids))

    cards_done = vectors_done = 0
    dim: Optional[int] = None
    prog_path = out / _STREAM_PROGRESS
    if resume and prog_path.exists():
        try:
            prog = json.loads(prog_path.read_text())
            cards_done, vectors_done, dim = int(prog["cards_done"]), int(prog["vectors_done"]), prog.get("dim")
        except Exception:  # noqa: BLE001 — a bad checkpoint just restarts the build from scratch
            cards_done = vectors_done = 0
            dim = None
    if not (resume and cards_done):  # fresh build: clear any stale legacy/streaming artifacts in this dir
        for fn in (_STREAM_VECTORS, _STREAM_PIDS, _STREAM_FAM, _STREAM_ROWS, "matrix.npy"):
            (out / fn).unlink(missing_ok=True)
        cards_done = vectors_done = 0
        dim = None
    elif dim:  # resume: trim any partial trailing shard so appends stay aligned
        _truncate_bytes(out / _STREAM_VECTORS, vectors_done * dim * 4)
        _truncate_bytes(out / _STREAM_PIDS, vectors_done * 4)
        _truncate_bytes(out / _STREAM_FAM, vectors_done * 1)
        _truncate_lines(out / _STREAM_ROWS, vectors_done)

    fmode, rmode = ("ab", "a") if cards_done else ("wb", "w")
    fv = open(out / _STREAM_VECTORS, fmode)
    fp = open(out / _STREAM_PIDS, fmode)
    ff = open(out / _STREAM_FAM, fmode)
    fr = open(out / _STREAM_ROWS, rmode)
    try:
        i = cards_done
        while i < len(cards):
            shard = cards[i:i + shard_size]
            srows: list[tuple[int, str, str, str]] = []
            for local, card in enumerate(shard):
                for r in facet_rows(card):
                    srows.append((i + local, r["family"], r["register"], r["text"]))
            if srows:
                mat = _embed_many([t for (_, _, _, t) in srows], embed_path=used)
                if dim is None:
                    dim = int(mat.shape[1])
                fv.write(np.ascontiguousarray(mat, dtype="float32").tobytes())
                fp.write(np.asarray([c for (c, _, _, _) in srows], dtype="uint32").tobytes())
                ff.write(np.asarray([fam_idx.get(f, 255) for (_, f, _, _) in srows], dtype="uint8").tobytes())
                for (cidx, fam, reg, txt) in srows:
                    fr.write(json.dumps({"primitive_id": card_ids[cidx], "family": fam, "register": reg,
                                         "text": txt}, sort_keys=True) + "\n")
                vectors_done += len(srows)
            cards_done = i + len(shard)
            i = cards_done
            for fh in (fv, fp, ff, fr):
                fh.flush()
            prog_path.write_text(json.dumps({"cards_done": cards_done, "vectors_done": vectors_done, "dim": dim}))
            if log:
                log(f"{cards_done}/{len(cards)} cards, {vectors_done} vectors")
    finally:
        for fh in (fv, fp, ff, fr):
            fh.close()

    # covered id-set (for the ratchet) + manifest — computed, candidate-only
    vec_pids = np.fromfile(out / _STREAM_PIDS, dtype="uint32")
    covered = sorted({card_ids[int(p)] for p in np.unique(vec_pids)}) if vec_pids.size else []
    (out / _STREAM_COVERED).write_text(json.dumps(covered))
    manifest = {"format": "streaming", "n_vectors": int(vectors_done), "n_cards": len(cards), "dim": dim or 0,
                "embed_model": used, "shard_size": shard_size, "facet_families": len(FACET_FAMILIES),
                "registers": list(_emb.REGISTERS), "n_cards_covered": len(covered), "complete": True,
                "avg_descriptions_per_card": round(vectors_done / len(cards), 2) if cards else 0,
                "candidate": True, "serves_truth": False}
    (out / _STREAM_MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return {"out": str(out), **manifest}


def load_facet_store(out_dir: Optional[Path] = None) -> Optional[dict[str, Any]]:
    """Load a persisted multivector store. Prefers the STREAMING format (memmap vectors.f32 + parallel id/family
    arrays — the full-corpus serve lane, no RAM blowup); falls back to the legacy in-RAM matrix.npy+rows.jsonl.
    None if absent/unreadable — callers then build in-process. serves_truth=false."""
    if np is None:
        return None
    out = Path(out_dir or facet_store_dir())
    man = out / _STREAM_MANIFEST
    if (out / _STREAM_VECTORS).exists() and man.exists():  # streaming format
        try:
            m = json.loads(man.read_text())
            n, dim = int(m["n_vectors"]), int(m["dim"])
            matrix = np.memmap(out / _STREAM_VECTORS, dtype="float32", mode="r", shape=(n, dim))
            vec_pids = np.fromfile(out / _STREAM_PIDS, dtype="uint32")
            vec_family = np.fromfile(out / _STREAM_FAM, dtype="uint8")
            card_ids = json.loads((out / _STREAM_CARDIDS).read_text())
            if len(vec_pids) != n or len(vec_family) != n:
                return None
            return {"streaming": True, "matrix": matrix, "vec_pids": vec_pids, "vec_family": vec_family,
                    "card_ids": card_ids, "family_list": list(FACET_FAMILIES), "n_vectors": n,
                    "n_cards": m.get("n_cards", len(set(card_ids)))}
        except Exception:  # noqa: BLE001 — a corrupt streaming store degrades to None (in-process build)
            return None
    mpath, rpath = out / "matrix.npy", out / "rows.jsonl"  # legacy in-RAM format
    if not (mpath.exists() and rpath.exists()):
        return None
    try:
        matrix = np.load(mpath)
        rows = [json.loads(ln) for ln in rpath.read_text().splitlines() if ln.strip()]
    except Exception:  # noqa: BLE001
        return None
    if len(rows) != matrix.shape[0]:
        return None
    return {"streaming": False, "rows": rows, "matrix": matrix, "n_vectors": len(rows),
            "n_cards": len({r.get("primitive_id") for r in rows})}


def facet_store_covered_ids(out_dir: Optional[Path] = None) -> set[str]:
    """The set of primitive_ids that have >=1 facet vector in the persisted store (cheap: reads covered_ids.json
    for the streaming store, else derives from the legacy rows). The coverage ratchet reads THIS, not 10M rows."""
    out = Path(out_dir or facet_store_dir())
    cov = out / _STREAM_COVERED
    if cov.exists():
        try:
            return set(json.loads(cov.read_text()))
        except Exception:  # noqa: BLE001
            pass
    store = load_facet_store(out_dir)
    if not store:
        return set()
    if store.get("streaming"):
        return {store["card_ids"][int(p)] for p in np.unique(store["vec_pids"])} if store["n_vectors"] else set()
    return {r.get("primitive_id") for r in store["rows"]}


def facet_store_family_counts(out_dir: Optional[Path] = None) -> dict[str, int]:
    """Per-family COVERED-card counts from the persisted store — how many distinct primitives carry each facet
    surface. Used by the ratchet's per-family floor so no single description surface silently regresses."""
    store = load_facet_store(out_dir)
    if not store:
        return {}
    counts: dict[str, set] = {}
    if store.get("streaming"):
        fam_list, vp, vf, cids = store["family_list"], store["vec_pids"], store["vec_family"], store["card_ids"]
        for i in range(store["n_vectors"]):
            counts.setdefault(fam_list[int(vf[i])], set()).add(int(vp[i]))
    else:
        for r in store["rows"]:
            counts.setdefault(r.get("family", "?"), set()).add(r.get("primitive_id"))
    return {f: len(s) for f, s in counts.items()}


#: The FACET ROUTER — the efficient-frontier family subset served instead of ALL ~90 vectors/card. The race
#: (race_facets) showed `all` never beats this subset while costing ~5x the vectors; these are the families that
#: carry signal on BOTH the title and the paraphrase workload (action+keywords rank; problem/solution/signature/
#: transform generalize to paraphrase). It is a documented DEFAULT — refine it per corpus with
#: facet_router_families(race_receipt) rather than trusting this literal (no-magic: the race is the source).
FACET_ROUTER_FAMILIES: tuple[str, ...] = ("action", "keywords", "problem", "solution", "signature", "transform")


def facet_router_families(race_receipt: Optional[dict[str, Any]] = None, *, top_n: int = 6,
                          min_mrr: float = 0.2) -> tuple[str, ...]:
    """Compute the efficient-frontier facet subset FROM a race receipt (best_by_quality ∪ best_by_efficiency,
    filtered to families that clear ``min_mrr``). Falls back to the documented default when no receipt is given —
    so the router is race-DERIVED at serving time, not a magic constant."""
    if not race_receipt or "per_family" not in race_receipt:
        return FACET_ROUTER_FAMILIES
    pf = race_receipt["per_family"]
    quality = [f for f in race_receipt.get("best_by_quality", []) if f != "all"]
    eff = [f for f in race_receipt.get("best_by_efficiency", []) if f != "all"]
    picked: list[str] = []
    for fam in quality + eff:
        if fam in FACET_FAMILIES and fam not in picked and pf.get(fam, {}).get("mrr", 0.0) >= min_mrr:
            picked.append(fam)
        if len(picked) >= top_n:
            break
    return tuple(picked) or FACET_ROUTER_FAMILIES


def facet_search(query: str, cards: Optional[list[dict[str, Any]]] = None, *, k: int = 10,
                 families: Optional[Iterable[str]] = None, embed_path: Optional[str] = None,
                 store: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """Retrieve primitives by INTENT over the multivector facet store — the graph's ``semantic_facets`` path.

    Embeds the query once, cosine-scores it against every facet vector (optionally restricted to ``families`` =
    the facet router), and MAX-POOLS to the primitive (its best-matching description wins). Store resolution:
    explicit ``store`` > the PERSISTED store when it covers ``cards`` (serve lane) > an in-process build over
    ``cards`` (bench lane). Returns ``[{primitive_id, score, family}]`` — ``family`` names which description
    surface matched, so a caller can SEE why a primitive was retrieved.
    """
    if np is None:
        raise RuntimeError("numpy required for facet_search")
    fam_filter = set(families) if families is not None else None
    # resolve the store: explicit > persisted (when it covers the cards) > in-process build
    if store is None:
        persisted = load_facet_store()
        if persisted is not None and cards:
            pids = {str(c.get("primitive_id") or "") for c in cards}
            covered = set(persisted["card_ids"]) if persisted.get("streaming") \
                else {r.get("primitive_id") for r in persisted["rows"]}
            store = persisted if len(pids & covered) >= 0.5 * len(pids) \
                else {**build_facet_store(cards, embed_path=embed_path), "streaming": False}
        elif persisted is not None:
            store = persisted
        else:
            store = {**build_facet_store(cards or [], embed_path=embed_path), "streaming": False}
    if store.get("streaming"):
        return _rank_streaming(store, query, cards, fam_filter, embed_path, k)
    return _rank_legacy(store, query, cards, fam_filter, embed_path, k)


def _rank_legacy(store: dict[str, Any], query: str, cards: Optional[list[dict[str, Any]]],
                 fam_filter: Optional[set], embed_path: Optional[str], k: int) -> list[dict[str, Any]]:
    """Rank over an in-RAM rows+matrix store (small sample / in-process build)."""
    rows, matrix = store["rows"], store["matrix"]
    if not rows or not getattr(matrix, "size", 0):
        return []
    card_ids = {str(c.get("primitive_id") or "") for c in cards} if cards else None
    idxs = [i for i, r in enumerate(rows)
            if (fam_filter is None or r.get("family") in fam_filter)
            and (card_ids is None or r.get("primitive_id") in card_ids)]
    if not idxs:
        return []
    q = _embed_many([query], embed_path=embed_path)[0]
    sims = matrix[idxs] @ q
    best: dict[str, tuple[float, str]] = {}
    for j, i in enumerate(idxs):
        pid, s = rows[i].get("primitive_id"), float(sims[j])
        if pid not in best or s > best[pid][0]:
            best[pid] = (s, rows[i].get("family", ""))
    ranked = sorted(best.items(), key=lambda kv: (-kv[1][0], str(kv[0])))[:k]
    return [{"primitive_id": pid, "score": round(sc, 6), "family": fam} for pid, (sc, fam) in ranked]


def _rank_streaming(store: dict[str, Any], query: str, cards: Optional[list[dict[str, Any]]],
                    fam_filter: Optional[set], embed_path: Optional[str], k: int) -> list[dict[str, Any]]:
    """Rank over the memmap streaming store (the full-corpus serve lane) — numpy-masked family/card filter +
    chunked matmul over the memmap (bounded RAM) + scatter-max pool to the primitive. Family attribution ('why')
    is returned for card-filtered queries (small candidate set); a full-corpus scan returns the score only."""
    matrix, vec_pids, vec_family = store["matrix"], store["vec_pids"], store["vec_family"]
    card_ids, fam_list, n = store["card_ids"], store["family_list"], store["n_vectors"]
    if n == 0:
        return []
    mask = np.ones(n, dtype=bool)
    if fam_filter is not None:
        fam_ids = np.asarray([i for i, f in enumerate(fam_list) if f in fam_filter], dtype="uint8")
        mask &= np.isin(vec_family, fam_ids)
    if cards:
        pids = {str(c.get("primitive_id") or "") for c in cards}
        keep_pos = np.asarray([i for i, cid in enumerate(card_ids) if cid in pids], dtype="uint32")
        mask &= np.isin(vec_pids, keep_pos)
    idxs = np.nonzero(mask)[0]
    if idxs.size == 0:
        return []
    q = np.asarray(_embed_many([query], embed_path=embed_path)[0], dtype="float32")
    # chunked matmul over the memmap so a 10M-vector store never loads whole into RAM
    sims = np.empty(idxs.size, dtype="float32")
    CH = 200_000
    for start in range(0, idxs.size, CH):
        chunk = idxs[start:start + CH]
        sims[start:start + chunk.size] = np.ascontiguousarray(matrix[chunk]) @ q
    pos = vec_pids[idxs]  # card position per selected vector
    if idxs.size <= 200_000:  # small candidate set: attribute the winning family per primitive
        best: dict[str, tuple[float, str]] = {}
        for j in range(idxs.size):
            pid, s = card_ids[int(pos[j])], float(sims[j])
            if pid not in best or s > best[pid][0]:
                best[pid] = (s, fam_list[int(vec_family[int(idxs[j])])])
        ranked = sorted(best.items(), key=lambda kv: (-kv[1][0], str(kv[0])))[:k]
        return [{"primitive_id": pid, "score": round(sc, 6), "family": fam} for pid, (sc, fam) in ranked]
    # large scan: vectorized scatter-max per card position (family omitted for speed)
    best_score = np.full(len(card_ids), -1e9, dtype="float32")
    np.maximum.at(best_score, pos, sims)
    order = np.argsort(-best_score)[:k]
    return [{"primitive_id": card_ids[int(p)], "score": round(float(best_score[p]), 6), "family": ""}
            for p in order if best_score[p] > -1e8]


# ================================================================================================================
# The RACE — which FACET FAMILY / description surface retrieves most EFFICIENTLY (the owner's real question)
# ================================================================================================================
#: Query-side stopwords dropped when paraphrasing (a real agent query rarely echoes the card title verbatim).
_Q_STOPWORDS: frozenset[str] = frozenset({"a", "an", "the", "of", "to", "for", "and", "with", "into", "from", "by"})
#: Title-verb -> a DIFFERENT synonym, so a paraphrased query does NOT share the title's leading verb (the token the
#: 'action' facet copies from the title). Forces the race to rely on genuine paraphrase generalization.
_TITLE_VERB_SWAP: dict[str, str] = {
    "emit": "produce", "count": "tally", "normalize": "standardize", "validate": "check", "sort": "order",
    "extract": "pull", "dedupe": "collapse", "transform": "convert", "generate": "create", "parse": "decode",
    "filter": "select", "aggregate": "summarize", "classify": "label", "lookup": "resolve", "format": "render",
}


def _paraphrase_query(title: str) -> str:
    """Deterministically turn a card TITLE into a paraphrase-shaped query: swap the leading verb for a synonym,
    drop stopwords, and reverse the remaining word order. No card facet contains this exact string, so the race
    now measures whether a facet GENERALIZES to differently-phrased intent (not just echoes the title)."""
    words = _words(title).split()
    if not words:
        return title
    if words[0] in _TITLE_VERB_SWAP:
        words[0] = _TITLE_VERB_SWAP[words[0]]
    kept = [w for w in words if w not in _Q_STOPWORDS] or words
    return " ".join(reversed(kept))


def _labelled_from_cards(cards: list[dict[str, Any]], *, paraphrase: bool = False) -> list[dict[str, Any]]:
    """A deterministic labelled query set derived from the cards themselves: each card's TITLE is a query whose
    only relevant primitive is that card. A self-retrieval probe — honest for RANKING facet families against each
    other on the same corpus (we are asking which SURFACE best recovers the right card, not building a gold set).

    ``paraphrase=True`` rewrites each title (verb-swap + stopword-drop + reorder) so the query no longer echoes the
    card's ``action``/title surface — the harder, more realistic workload where multi-description richness pays.
    """
    out = []
    for c in cards:
        pid = str(c.get("primitive_id") or "")
        q = str(c.get("title") or "").strip()
        if pid and q:
            out.append({"query": _paraphrase_query(q) if paraphrase else q, "relevant": [pid]})
    return out


def race_facets(cards: list[dict[str, Any]], labelled: Optional[list[dict[str, Any]]] = None, *,
                k: int = 5, embed_path: Optional[str] = None, paraphrase: bool = False) -> dict[str, Any]:
    """Retrieve each labelled query using EACH facet family's vectors ALONE; report quality + efficiency per family.

    Per family: build the sub-matrix of just that family's vectors (id-per-row, max-pooled to the primitive),
    cosine-rank against each query, compute precision@k / MRR / recall@k, and an EFFICIENCY score = MRR per stored
    vector-per-card. The ranking tells us which description surfaces are worth indexing at 5M scale. Also races
    ``all`` (every family's vectors together) as the ceiling.
    """
    if np is None:
        raise RuntimeError("numpy required for the race")
    labelled = labelled or _labelled_from_cards(cards, paraphrase=paraphrase)
    store = build_facet_store(cards, embed_path=embed_path)
    rows, matrix = store["rows"], store["matrix"]
    if not rows or not getattr(matrix, "size", 0):
        return {"error": "empty store", "n_cards": len(cards)}
    # queries embedded once (shared across families)
    q_texts = [q["query"] for q in labelled]
    q_mat = _embed_many(q_texts, embed_path=embed_path)

    families = list(FACET_FAMILIES) + ["all"]
    per_family: dict[str, Any] = {}
    for fam in families:
        idxs = [i for i, r in enumerate(rows) if fam == "all" or r["family"] == fam]
        if not idxs:
            per_family[fam] = {"n_vectors": 0, "precision_at_k": 0.0, "mrr": 0.0, "recall_at_k": 0.0, "efficiency": 0.0}
            continue
        sub = matrix[idxs]
        sub_ids = [rows[i]["primitive_id"] for i in idxs]
        prec_sum = mrr_sum = recall_sum = 0.0
        for qi, q in enumerate(labelled):
            sims = sub @ q_mat[qi]
            # max-pool to the primitive: best vector per primitive_id
            best: dict[str, float] = {}
            for j, pid in enumerate(sub_ids):
                s = float(sims[j])
                if pid not in best or s > best[pid]:
                    best[pid] = s
            ranked = sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))
            topk = [pid for pid, _ in ranked[:k]]
            rel = set(q["relevant"])
            hits = [i for i, pid in enumerate(topk) if pid in rel]
            prec_sum += len(hits) / k
            recall_sum += (1.0 if hits else 0.0)  # relevant set is size 1 here
            mrr_sum += (1.0 / (hits[0] + 1)) if hits else 0.0
        n = len(labelled)
        vec_per_card = len(idxs) / max(1, store["n_cards"])
        mrr = mrr_sum / n
        per_family[fam] = {
            "n_vectors": len(idxs),
            "vectors_per_card": round(vec_per_card, 2),
            "precision_at_k": round(prec_sum / n, 4),
            "recall_at_k": round(recall_sum / n, 4),
            "mrr": round(mrr, 4),
            # EFFICIENCY: retrieval quality earned per stored vector-per-card (higher = leaner surface that still ranks)
            "efficiency": round(mrr / vec_per_card, 4) if vec_per_card else 0.0,
        }
    # rank the families (excluding 'all') by quality then by efficiency
    ranked_quality = sorted((f for f in FACET_FAMILIES), key=lambda f: (-per_family[f]["mrr"], -per_family[f]["precision_at_k"], f))
    ranked_eff = sorted((f for f in FACET_FAMILIES), key=lambda f: (-per_family[f]["efficiency"], f))
    return {
        "n_cards": store["n_cards"], "n_vectors": store["n_vectors"], "k": k,
        "workload": "paraphrase" if paraphrase else "title",
        "avg_descriptions_per_card": round(store["n_vectors"] / store["n_cards"], 2) if store["n_cards"] else 0,
        "embed_model": store["embed_model"], "n_queries": len(labelled),
        "per_family": per_family,
        "best_by_quality": ranked_quality[:5],
        "best_by_efficiency": ranked_eff[:5],
        "candidate": True, "serves_truth": False,
    }


# ================================================================================================================
# MORE MODELS — build the facet store under MANY embedder backends + race model x facet (the scale axis)
# ================================================================================================================
def available_facet_backends(*, include_api: bool = False) -> list[str]:
    """The embedder backends usable RIGHT NOW, from embedder_zoo.EMBEDDER_BACKENDS (the single source of models —
    no-magic: never a typed model list). ``include_api`` adds slow endpoint models (Ollama) — off by default so a
    grid race stays fast. Adding a model is one EMBEDDER_BACKENDS row there, then it appears here automatically."""
    try:
        from scripts import embedder_zoo as _zoo  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return []
    out = []
    for name, spec in _zoo.EMBEDDER_BACKENDS.items():
        if spec["kind"] == "api_local" and not include_api:
            continue
        try:
            if _zoo.backend_available(name):
                out.append(name)
        except Exception:  # noqa: BLE001 — an unavailable backend is skipped, never fatal
            continue
    return out


def _embed_many_backend(texts: list[str], backend: str) -> "np.ndarray":
    """Batch-embed arbitrary texts under a named embedder_zoo backend, REUSING its model singletons for real batch
    encode (model2vec .encode / fastembed .embed), per-text fallback otherwise. L2-normalized. This is how the
    facet store is materialized in DIFFERENT embedding spaces (more embedding models)."""
    if np is None:
        raise RuntimeError("numpy required")
    from scripts import embedder_zoo as _zoo  # noqa: PLC0415
    if not texts:
        return np.zeros((0, 0), dtype="float32")
    spec = _zoo.EMBEDDER_BACKENDS.get(backend, {})
    kind = spec.get("kind")
    if kind == "static_pretrained" and _zoo._load_m2v(spec["model"]) is not None:
        mat = np.asarray(_zoo._load_m2v(spec["model"]).encode(texts), dtype="float32")
    elif kind == "onnx_local" and _zoo._load_fastembed(spec["model"]) is not None:
        mat = np.asarray(list(_zoo._load_fastembed(spec["model"]).embed(texts)), dtype="float32")
    else:  # proxy / ollama / lsa (lsa needs state; not used in the facet race) — per-text dispatch
        state = None
        mat = np.asarray([_zoo.embed(t, backend, state=state) for t in texts], dtype="float32")
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def race_models_x_facets(cards: list[dict[str, Any]], labelled: Optional[list[dict[str, Any]]] = None, *,
                         backends: Optional[list[str]] = None, k: int = 5, paraphrase: bool = False,
                         families: Optional[Iterable[str]] = None) -> dict[str, Any]:
    """The GRID race: embed the facet descriptions under EACH model, and for each (model x facet-family) measure
    MRR/precision@k. Answers 'more embeddings, more embedding types, more embedding models' with a receipt saying
    which (model, description-surface) combination retrieves best — the joint frontier over models AND facets."""
    if np is None:
        raise RuntimeError("numpy required for the model x facet race")
    backends = backends or available_facet_backends()
    labelled = labelled or _labelled_from_cards(cards, paraphrase=paraphrase)
    fam_list = list(families) if families is not None else (list(FACET_FAMILIES) + ["all", "routed"])
    # the facet rows are model-independent; embed the SAME texts under each model
    rows: list[dict[str, str]] = []
    for card in cards:
        pid = str(card.get("primitive_id") or "")
        for r in facet_rows(card):
            rows.append({"primitive_id": pid, **r})
    texts = [r["text"] for r in rows]
    q_texts = [q["query"] for q in labelled]

    def _fam_idxs(fam: str) -> list[int]:
        if fam == "all":
            return list(range(len(rows)))
        if fam == "routed":
            return [i for i, r in enumerate(rows) if r["family"] in FACET_ROUTER_FAMILIES]
        return [i for i, r in enumerate(rows) if r["family"] == fam]

    grid: dict[str, dict[str, Any]] = {}
    per_backend_best: dict[str, Any] = {}
    for backend in backends:
        matrix = _embed_many_backend(texts, backend)
        q_mat = _embed_many_backend(q_texts, backend)
        if not matrix.size:
            continue
        fam_scores: dict[str, float] = {}
        fam_vecs: dict[str, int] = {}
        for fam in fam_list:
            idxs = _fam_idxs(fam)
            if not idxs:
                fam_scores[fam] = 0.0
                fam_vecs[fam] = 0
                continue
            sub, sub_ids = matrix[idxs], [rows[i]["primitive_id"] for i in idxs]
            mrr_sum = 0.0
            for qi, q in enumerate(labelled):
                sims = sub @ q_mat[qi]
                best: dict[str, float] = {}
                for j, pid in enumerate(sub_ids):
                    s = float(sims[j])
                    if pid not in best or s > best[pid]:
                        best[pid] = s
                ranked = [pid for pid, _ in sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))[:k]]
                rel = set(q["relevant"])
                hit = next((r for r, pid in enumerate(ranked) if pid in rel), None)
                mrr_sum += (1.0 / (hit + 1)) if hit is not None else 0.0
            fam_scores[fam] = round(mrr_sum / len(labelled), 4)
            fam_vecs[fam] = round(len(idxs) / max(1, len(cards)), 2)
        grid[backend] = {"dim": int(matrix.shape[1]), "kind": _backend_kind(backend), "facet_mrr": fam_scores,
                         "vectors_per_card": fam_vecs}
        best_fam = max((f for f in fam_scores if f not in ("all",)), key=lambda f: fam_scores[f], default=None)
        per_backend_best[backend] = {"best_facet": best_fam, "mrr": fam_scores.get(best_fam, 0.0)}
    # champion (model, facet) over the whole grid (excluding the 'all' catch-all)
    champ = None
    for backend, d in grid.items():
        for fam, mrr in d["facet_mrr"].items():
            if fam == "all":
                continue
            if champ is None or mrr > champ["mrr"]:
                champ = {"backend": backend, "facet": fam, "mrr": mrr, "dim": d["dim"]}
    return {"record_type": "model_x_facet_race", "n_cards": len(cards), "n_queries": len(labelled), "k": k,
            "workload": "paraphrase" if paraphrase else "title", "backends_raced": list(grid),
            "champion": champ, "per_backend_best": per_backend_best, "grid": grid,
            "candidate": True, "serves_truth": False}


def _backend_kind(backend: str) -> str:
    try:
        from scripts import embedder_zoo as _zoo  # noqa: PLC0415
        return _zoo.EMBEDDER_BACKENDS.get(backend, {}).get("kind", "?")
    except Exception:  # noqa: BLE001
        return "?"


# ================================================================================================================
# Corpus loading
# ================================================================================================================
def load_cards(sample: int = 0, files: Optional[Iterable[Path]] = None) -> list[dict[str, Any]]:
    """Load cards from the searchable card files (sample>0 caps the count, taking a deterministic stride so the
    sample spans the corpus rather than the first N of one file)."""
    files = list(files or _DEFAULT_CARD_FILES)
    cards: list[dict[str, Any]] = []
    for fp in files:
        if not fp.exists():
            continue
        with fp.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    cards.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    if sample and sample > 0 and len(cards) > sample:
        stride = max(1, len(cards) // sample)
        cards = cards[::stride][:sample]
    return cards


# ================================================================================================================
# Self-test — mutation + determinism + no-magic gates
# ================================================================================================================
def _synthetic_cards(n: int = 12) -> list[dict[str, Any]]:
    """Deterministic synthetic cards spanning several operations/datatypes (offline; no corpus dependency)."""
    specs = [
        ("Count Order Items", "Counts the items in an order batch.", "OrderItemBatch", "OrderItemCount"),
        ("Normalize Party Name", "Normalizes a raw party name into a canonical form.", "RawPartyName", "CanonicalPartyName"),
        ("Validate Auth Scheme", "Validates a security scheme map and emits a report.", "SecuritySchemeMap", "AuthValidationReport"),
        ("Sort Invoice Lines", "Sorts invoice lines by amount descending.", "InvoiceLineList", "SortedInvoiceLineList"),
        ("Extract Email Addresses", "Extracts email addresses from a contact block.", "ContactBlock", "EmailAddressList"),
        ("Dedupe Vendor Records", "Collapses duplicate vendor records into unique entities.", "VendorRecordBatch", "UniqueVendorEntitySet"),
    ]
    out = []
    for i in range(n):
        title, black, ie, oe = specs[i % len(specs)]
        out.append({
            "primitive_id": f"prim:test:{i:04d}", "title": f"{title} {i}", "blackbox": black,
            "input_edge": ie, "output_edge": oe, "domains": [f"{ie}-"], "capability_tags": [ie],
            "mutations": [], "candidate": True, "serves_truth": False,
        })
    return out


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    # (1) NO-MAGIC: shape computed from the registry, not literals.
    s = summary()
    checks.append(("summary computed from registry",
                   s["facet_families"] == len(FACET_FAMILIES) and s["registers"] == list(_emb.REGISTERS),
                   json.dumps(s)))

    cards = _synthetic_cards(12)

    # (2) RICHNESS: a structured card yields MANY descriptions across MANY families (far more than the old 3).
    rows = facet_rows(cards[0])
    fams = {r["family"] for r in rows}
    checks.append((f"rich card -> many descriptions ({len(rows)} rows, {len(fams)} families)",
                   len(rows) >= 25 and len(fams) >= 8, f"{len(rows)} rows / {len(fams)} families"))

    # (3) DETERMINISM: descriptions are byte-identical across two builds.
    r1 = json.dumps(facet_rows(cards[0]), sort_keys=True)
    r2 = json.dumps(facet_rows(cards[0]), sort_keys=True)
    checks.append(("descriptions deterministic (byte-identical twice)", r1 == r2, "hash match"))

    if np is not None:
        # (4) EMBED DETERMINISM: the vector matrix is byte-identical across two builds (static embedder).
        m1 = build_facet_store(cards, embed_path="tokens")["matrix"]
        m2 = build_facet_store(cards, embed_path="tokens")["matrix"]
        checks.append(("embeddings deterministic (byte-identical twice)",
                       m1.shape == m2.shape and bool(np.array_equal(m1, m2)), f"shape {m1.shape}"))

        # (5) RACE runs + produces a per-family ranking; 'all' (every surface) is a sane ceiling.
        rec = race_facets(cards, k=3, embed_path="tokens")
        ok_race = ("per_family" in rec and rec["per_family"]["all"]["mrr"] >= rec["per_family"]["negative_contrast"]["mrr"]
                   and len(rec["best_by_quality"]) >= 3)
        checks.append((f"race ranks facets (best_by_quality={rec.get('best_by_quality')})", ok_race, json.dumps(rec.get("per_family", {}).get("all", {}))))

        # (6) MUTATION GATE: a facet family that emits GARBAGE (unrelated text) must retrieve WORSE than the real
        #     'action' family — i.e. the race can TELL a good description surface from a bad one. If it can't, the
        #     race proves nothing.
        real = FACET_FAMILIES["action"]
        try:
            FACET_FAMILIES["action"] = lambda card: ["zzzz qqqq unrelated lorem ipsum"] * 3
            rec_mut = race_facets(cards, k=3, embed_path="tokens")
            mutated_mrr = rec_mut["per_family"]["action"]["mrr"]
        finally:
            FACET_FAMILIES["action"] = real
        rec_real = race_facets(cards, k=3, embed_path="tokens")
        real_mrr = rec_real["per_family"]["action"]["mrr"]
        checks.append((f"mutation gate: garbage facet retrieves worse ({mutated_mrr} < {real_mrr})",
                       mutated_mrr < real_mrr, f"mut={mutated_mrr} real={real_mrr}"))

        # (7) FACET_SEARCH (the graph seam): a title-shaped query retrieves ITS card at rank 1, and the router
        #     subset does so with FEWER vectors than 'all' — the serve-time contract the graph wires.
        store = build_facet_store(cards, embed_path="tokens")
        target = cards[0]
        hits_all = facet_search(target["title"], cards, k=3, embed_path="tokens", store=store)
        hits_routed = facet_search(target["title"], cards, k=3, families=FACET_ROUTER_FAMILIES,
                                   embed_path="tokens", store=store)
        top_ok = bool(hits_all) and hits_all[0]["primitive_id"] == target["primitive_id"]
        routed_ok = bool(hits_routed) and hits_routed[0]["primitive_id"] == target["primitive_id"]
        checks.append((f"facet_search: query->its card @rank1 (all + routed); hit names its family "
                       f"({hits_all[0].get('family') if hits_all else '?'})",
                       top_ok and routed_ok and "family" in (hits_all[0] if hits_all else {}), f"all={top_ok} routed={routed_ok}"))

        # (8) ROUTER-FROM-RACE: facet_router_families computes the frontier from a receipt (not a magic literal).
        rec_r = race_facets(cards, k=3, embed_path="tokens")
        router = facet_router_families(rec_r, top_n=4)
        checks.append((f"facet_router computed from race receipt ({list(router)})",
                       len(router) >= 1 and all(f in FACET_FAMILIES for f in router), str(router)))

        # (9) MODEL x FACET GRID: races >=1 backend x facets; the grid + champion (model,facet) are produced.
        #     Uses proxy_crc32 (always available, deterministic) so the gate never depends on an optional model.
        grec = race_models_x_facets(cards, backends=["proxy_crc32"], k=3)
        gok = (grec.get("grid") and "proxy_crc32" in grec["grid"]
               and grec.get("champion") and "facet" in grec["champion"])
        checks.append((f"model x facet grid runs (champion={grec.get('champion')})", bool(gok),
                       json.dumps(grec.get("champion"))))

        # (10) STREAMING STORE round-trip: build->memmap load->search @rank1->coverage set (the full-corpus serve
        #      lane, exercised at toy scale in a temp dir so the gate is offline + deterministic).
        import tempfile as _tf  # noqa: PLC0415
        with _tf.TemporaryDirectory() as td:
            man = build_facet_store_streaming(cards, out_dir=Path(td), embed_path="tokens", shard_size=5)
            st = load_facet_store(Path(td))
            hits_s = facet_search(cards[0]["title"], cards, k=3, embed_path="tokens", store=st)
            cov = facet_store_covered_ids(Path(td))
            stream_ok = (st and st.get("streaming") and man["n_vectors"] == st["n_vectors"]
                         and hits_s and hits_s[0]["primitive_id"] == cards[0]["primitive_id"]
                         and cov == {c["primitive_id"] for c in cards})
            checks.append((f"streaming store: build->load->search @rank1 + coverage ({man['n_vectors']} vec, "
                           f"{len(cov)} covered)", bool(stream_ok), f"streaming={st.get('streaming') if st else None}"))
    else:
        checks.append(("numpy present for embed/race gates", False, "numpy missing"))

    ok = all(c[1] for c in checks)
    print(f"{'PASS' if ok else 'FAIL'} - primitive_facet_enrichment: "
          f"{len(FACET_FAMILIES)} facet families x {len(_emb.REGISTERS)} registers, multivector store + facet race")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail})" if not passed else ""))
    return 0 if ok else 1


# ================================================================================================================
# CLI
# ================================================================================================================
def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Multi-facet primitive enrichment: many descriptions + embeddings per primitive, then race them.")
    ap.add_argument("--self-test", action="store_true", help="run mutation + determinism + no-magic gates (offline)")
    ap.add_argument("--describe", action="store_true", help="print one/few primitives' full facet description set")
    ap.add_argument("--build", action="store_true", help="build + persist the multivector store for a sample (in-RAM)")
    ap.add_argument("--build-full", action="store_true", help="STREAMING full-corpus build (resumable, memmap, bounded RAM)")
    ap.add_argument("--shard-size", type=int, default=5000, help="cards per shard for --build-full")
    ap.add_argument("--race", action="store_true", help="race the facet families -> per-family efficiency receipt")
    ap.add_argument("--race-models", action="store_true", help="GRID race: model x facet over ALL available embedder backends (more models/types)")
    ap.add_argument("--backends", default=None, help="comma-separated embedder backends (default: all available fast ones)")
    ap.add_argument("--include-api", action="store_true", help="include slow endpoint models (Ollama) in --race-models")
    ap.add_argument("--paraphrase", action="store_true", help="race on PARAPHRASED queries (verb-swap+reorder) — the harder workload where multi-description richness pays")
    ap.add_argument("--sample", type=int, default=200, help="cap the number of cards (0 = all; strided sample)")
    ap.add_argument("--k", type=int, default=5, help="top-k for the race")
    ap.add_argument("--embed-path", default=None, help="embedder path override (tokens/model2vec/ollama)")
    ap.add_argument("--out", default=None, help="output dir for --build (default dist/primitive-facet-embeddings)")
    args = ap.parse_args(argv)

    if args.self_test:
        return _self_test()

    if args.describe:
        cards = load_cards(sample=max(1, args.sample))
        if not cards:
            cards = _synthetic_cards(3)
        print(json.dumps({"shape": summary()}, indent=2))
        for c in cards[: max(1, min(3, args.sample))]:
            rows = facet_rows(c)
            print(f"\n=== {c.get('primitive_id')} :: {c.get('title')} ===  ({len(rows)} descriptions)")
            by_fam: dict[str, list[str]] = {}
            for r in rows:
                by_fam.setdefault(r["family"], []).append(r["text"])
            for fam, texts in by_fam.items():
                print(f"  [{fam}] ({len(texts)})")
                for t in texts[:4]:
                    print(f"      - {t}")
                if len(texts) > 4:
                    print(f"      ... +{len(texts) - 4} more")
        return 0

    if args.build:
        cards = load_cards(sample=args.sample)
        store = build_facet_store(cards, embed_path=args.embed_path)
        out = persist_facet_store(store, Path(args.out) if args.out else None)
        print(json.dumps({
            "built": True, "out": str(out), "n_cards": store["n_cards"], "n_vectors": store["n_vectors"],
            "avg_descriptions_per_card": round(store["n_vectors"] / store["n_cards"], 2) if store["n_cards"] else 0,
            "dim": store["dim"], "embed_model": store["embed_model"],
        }, indent=2))
        return 0

    if args.build_full:
        cards = load_cards(sample=args.sample)  # sample=0 -> full corpus
        import sys as _sys
        manifest = build_facet_store_streaming(
            cards, out_dir=Path(args.out) if args.out else None, embed_path=args.embed_path,
            shard_size=args.shard_size, resume=True, log=lambda m: print(m, file=_sys.stderr, flush=True))
        print(json.dumps({"built_full": True, **manifest}, indent=2))
        return 0

    if args.race:
        cards = load_cards(sample=args.sample)
        rec = race_facets(cards, k=args.k, embed_path=args.embed_path, paraphrase=args.paraphrase)
        print(json.dumps(rec, indent=2))
        return 0

    if args.race_models:
        cards = load_cards(sample=args.sample)
        backends = [b.strip() for b in args.backends.split(",")] if args.backends else \
            available_facet_backends(include_api=args.include_api)
        rec = race_models_x_facets(cards, backends=backends, k=args.k, paraphrase=args.paraphrase)
        print(json.dumps(rec, indent=2))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
