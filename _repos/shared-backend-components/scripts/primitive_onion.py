#!/usr/bin/env python3
"""scripts.primitive_onion — read a primitive like an ONION: only the layer you need, peel deeper on demand,
and deterministically REMIX its edges. The token-reduction heart of "the LLM shouldn't read every layer."

Owner vision: an agent composing a solution should read the primitive's DOCSTRING (its input/output signature)
— not its whole implementation — and only PEEL deeper (blackbox → contract → provenance) when it needs to
troubleshoot or verify. It should also be able to REMIX a primitive's inputs/outputs to get the slight
variation it needs, following the standard, deterministically (no LLM, no drift). The card is ALREADY layered
by field; this exposes those layers as an access API so composition reads ~29 tokens instead of ~654.

Layers (outer → inner):
  L0 signature   — primitive_id, title, input_edge, output_edge   (the DOCSTRING: what it takes / returns)
  L1 blackbox    — blackbox, kind, edge_contract                  (what it does, one line)
  L2 contract    — contract, effects, mutations, proof_requirements (the behavioural details)
  L3 provenance  — source_ref(s), quality_score, readiness, verification_level (trust / where it came from)

API:
  signature(card)                 -> L0 dict (compose by reading THIS; tiny)
  peel(card, through="contract")  -> cumulative L0..through dict + token_cost (progressive disclosure)
  token_cost(card, through)       -> est tokens to read up to a layer (the savings vs the full card)
  layers_outer_to_inner()/inner_to_outer() -> the peel order for troubleshooting in either direction
  remix_edges(card, input_edge=, output_edge=) -> a deterministic VARIANT with adjusted edges, a fresh
                                   canonical id, and LINEAGE back to the origin (lossless; version in metadata)

serves_truth=false — reading/remixing a candidate primitive never promotes it.

    PYTHONPATH=. python3 scripts/primitive_onion.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Optional  # noqa: E402

#: the onion, outer → inner. Each layer is (name, the card fields it discloses). Single source of the layering.
LAYERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("signature", ("primitive_id", "title", "input_edge", "output_edge")),
    ("blackbox", ("blackbox", "kind", "edge_contract")),
    ("contract", ("contract", "effects", "mutations", "proof_requirements")),
    ("provenance", ("source_ref", "source_refs", "quality_score", "readiness", "verification_level")),
)
_LAYER_NAMES = tuple(name for name, _ in LAYERS)
CHARS_PER_TOKEN = 4  # same chars/4 proxy the benchmarks use


def _est_tokens(obj: Any) -> int:
    return len(json.dumps(obj)) // CHARS_PER_TOKEN


def layer_names() -> tuple[str, ...]:
    return _LAYER_NAMES


def layers_outer_to_inner() -> tuple[str, ...]:
    """Peel order for troubleshooting from the OUTSIDE in (signature → … → provenance)."""
    return _LAYER_NAMES


def layers_inner_to_outer() -> tuple[str, ...]:
    """Peel order for troubleshooting from the INSIDE out (provenance → … → signature)."""
    return tuple(reversed(_LAYER_NAMES))


def _layer_fields(name: str) -> tuple[str, ...]:
    for lname, fields in LAYERS:
        if lname == name:
            return fields
    raise KeyError(f"unknown layer {name!r}; layers are {_LAYER_NAMES}")


def layer(card: dict, name: str) -> dict:
    """Just the fields of ONE layer (present ones only)."""
    return {f: card[f] for f in _layer_fields(name) if f in card and card[f] not in (None, "", {}, [])}


def signature(card: dict) -> dict:
    """L0 — the DOCSTRING an agent reads to COMPOSE: id + title + input/output edges. Tiny (~tens of tokens)."""
    return layer(card, "signature")


def _through_index(through: str) -> int:
    if through not in _LAYER_NAMES:
        raise KeyError(f"unknown layer {through!r}; layers are {_LAYER_NAMES}")
    return _LAYER_NAMES.index(through)


def peel(card: dict, through: str = "contract") -> dict:
    """PROGRESSIVE DISCLOSURE: the cumulative view from the signature down THROUGH ``through`` (inclusive), plus
    the layers read and the token_cost. Reading `through='signature'` is the cheap compose path; peel deeper
    only to troubleshoot/verify — so the agent never pays for the whole card unless it needs it."""
    idx = _through_index(through)
    revealed: dict = {}
    read: list[str] = []
    for name in _LAYER_NAMES[: idx + 1]:
        revealed.update(layer(card, name))
        read.append(name)
    return {"primitive_id": card.get("primitive_id"), "through": through, "layers_read": read,
            "revealed": revealed, "token_cost": _est_tokens(revealed),
            "full_card_tokens": _est_tokens(card), "serves_truth": False}


def token_cost(card: dict, through: str = "signature") -> int:
    """Tokens to read up to ``through`` — quantifies the progressive-disclosure saving vs the full card."""
    return peel(card, through)["token_cost"]


def remix_edges(card: dict, *, input_edge: Optional[str] = None, output_edge: Optional[str] = None) -> dict:
    """A DETERMINISTIC variant of ``card`` with adjusted input/output edges (the "slight variation needed"),
    following the standard: a FRESH canonical id derived from the new edges (never reuse the origin's id),
    LINEAGE back to the origin (``remixed_from`` — lossless, the origin is preserved), version bumped in
    METADATA (never in the id/name), candidate=true / serves_truth=false. Same inputs -> same variant (no
    LLM, no RNG)."""
    if input_edge is None and output_edge is None:
        raise ValueError("remix_edges needs a new input_edge and/or output_edge")
    variant = dict(card)
    new_in = input_edge if input_edge is not None else card.get("input_edge")
    new_out = output_edge if output_edge is not None else card.get("output_edge")
    variant["input_edge"] = new_in
    variant["output_edge"] = new_out
    try:
        from src.teleon.experiments.ids import canonical_id  # noqa: PLC0415  the ONE id authority
        variant["primitive_id"] = canonical_id("prim", str(card.get("primitive_id")), str(new_in), str(new_out))
    except Exception:  # noqa: BLE001 — never crash a remix; fall back to a stable local id
        import hashlib  # noqa: PLC0415
        h = hashlib.sha256(f"{card.get('primitive_id')}|{new_in}|{new_out}".encode()).hexdigest()[:16]
        variant["primitive_id"] = f"prim-{h}"
    variant["remixed_from"] = card.get("primitive_id")           # lineage: the origin is preserved, not replaced
    variant["schema_version"] = int(card.get("schema_version", 1)) + 1  # version in METADATA, never the id
    variant["candidate"] = True
    variant["serves_truth"] = False
    return variant


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    full = {
        "primitive_id": "prim:vf:abc123", "title": "Normalize opportunity records", "kind": "route.primitive",
        "input_edge": "RawOpportunity", "output_edge": "NormalizedOpportunity",
        "blackbox": "normalizes multi-source opportunity records " * 6,
        "edge_contract": "typed", "contract": {"in": "RawOpportunity", "out": "NormalizedOpportunity", "rules": ["x"] * 30},
        "effects": ["normalize"], "mutations": ["field_map"], "proof_requirements": ["roundtrip"] * 10,
        "source_ref": {"path": "src/x.py"}, "quality_score": 0.8, "readiness": "candidate", "verification_level": "L2",
    }

    # signature is the tiny docstring; the full card is much larger — the whole point.
    sig_tok = token_cost(full, "signature")
    full_tok = _est_tokens(full)
    checks.append(("signature (docstring) carries id+title+edges", set(signature(full)) == {"primitive_id", "title", "input_edge", "output_edge"}))
    checks.append(("progressive disclosure: signature << full card (compose cheap, peel on demand)",
                   sig_tok * 4 < full_tok))

    # peel is cumulative + monotonically more expensive the deeper you go.
    costs = [token_cost(full, name) for name in _LAYER_NAMES]
    checks.append(("peel is cumulative + costs strictly increase outer->inner", costs == sorted(costs) and len(set(costs)) == len(costs)))
    checks.append(("peel through contract reveals contract but signature-only does not",
                   "contract" in peel(full, "contract")["revealed"] and "contract" not in peel(full, "signature")["revealed"]))

    # bidirectional troubleshooting order.
    checks.append(("outer->inner starts at signature, inner->outer starts at provenance",
                   layers_outer_to_inner()[0] == "signature" and layers_inner_to_outer()[0] == "provenance"))
    checks.append(("the two orders are exact reverses", tuple(reversed(layers_outer_to_inner())) == layers_inner_to_outer()))

    # deterministic edge remix: new id, lineage kept, version in metadata, origin untouched.
    v1 = remix_edges(full, output_edge="EnrichedOpportunity")
    v2 = remix_edges(full, output_edge="EnrichedOpportunity")
    checks.append(("remix adjusts the edge", v1["output_edge"] == "EnrichedOpportunity" and v1["input_edge"] == full["input_edge"]))
    checks.append(("remix is deterministic (same inputs -> same variant id)", v1["primitive_id"] == v2["primitive_id"]))
    checks.append(("remix mints a FRESH id (never the origin's) + keeps LINEAGE",
                   v1["primitive_id"] != full["primitive_id"] and v1["remixed_from"] == full["primitive_id"]))
    checks.append(("version bumps in METADATA, not the id (no .vN/@N)",
                   v1["schema_version"] == 2 and ".v" not in v1["primitive_id"] and "@" not in v1["primitive_id"]))
    checks.append(("the ORIGIN is preserved (remix is lossless, not a mutation)", full["output_edge"] == "NormalizedOpportunity"))
    checks.append(("remix is candidate/serves_truth=false", v1["candidate"] and v1["serves_truth"] is False))
    try:
        remix_edges(full)
        checks.append(("remix with no new edge is rejected", False))
    except ValueError:
        checks.append(("remix with no new edge is rejected", True))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - primitive_onion: read a primitive as layers — signature (docstring) to compose cheap, peel "
          "deeper only to troubleshoot (either direction); deterministic edge remix mints a fresh id, keeps "
          "lineage, versions in metadata, preserves the origin. The LLM reads only what it needs. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
