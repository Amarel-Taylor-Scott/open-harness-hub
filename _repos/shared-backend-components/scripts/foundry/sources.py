#!/usr/bin/env python3
"""Foundry sources — Stage 1: acquire an authoritative, LICENSED source per gap.

Pillar 2 of the evidence bar: a component may exist only if a real, attributable,
redistributable source supplies what the bare model lacks. This stage finds that
source for each confirmed gap, captures provenance (``source_url`` + ``author`` +
``license`` + ``source_kind``), and **drops** anything unsourced or non-permissively
licensed — before any (expensive) construction.

A ``SourceScout`` does the finding. The offline default reads a recorded
``{gap_id: source}`` catalog (the source may carry a ``payload`` of material for
the constructor to mine). Production wires scouts over web search + the existing
walkers (`scripts.factory.run_factory` registry: Wikipedia / USCode / Wikidata /
NIST) and GitHub-as-source-surface — all behind the same protocol.

Run ``python -m scripts.foundry.sources`` for the offline self-test.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from scripts.factory.capability_lift_gate import PERMISSIVE_LICENSES
from scripts.foundry.contracts import BaseStage, Candidate, FoundryContext

# Valid attribution.source_kind enum (schemas/_common.schema.json). Scouts should
# map their real source kind into one of these; everything else → "other".
_VALID_SOURCE_KINDS = {"kaggle", "github", "huggingface", "arxiv", "manual", "other"}


@runtime_checkable
class SourceScout(Protocol):
    def find(self, gap: dict) -> dict | None:
        """Return a source dict (source_url/author/license/source_kind[/payload]) or None."""
        ...


class RecordedSourceScout:
    """Offline scout: a ``{gap_id: source_dict}`` catalog. Deterministic, no network."""

    def __init__(self, catalog: dict[str, dict] | None = None) -> None:
        self.catalog = catalog or {}

    def find(self, gap: dict) -> dict | None:
        return self.catalog.get(gap.get("id"))


def is_permissive(license_str: str) -> bool:
    lic = (license_str or "").lower()
    return any(term in lic for term in PERMISSIVE_LICENSES)


def normalize_source_kind(kind: str) -> str:
    return kind if kind in _VALID_SOURCE_KINDS else "other"


class SourceStage(BaseStage):
    """Attach a licensed source to each gap-candidate; drop the unsourced."""

    name = "sources"

    def __init__(self, scout: SourceScout | None = None, *, require_permissive: bool = True) -> None:
        self.scout = scout or RecordedSourceScout()
        self.require_permissive = require_permissive

    def run(self, batch: list[Candidate], ctx: FoundryContext) -> list[Candidate]:
        for c in batch:
            if not c.alive:
                continue
            src = dict(c.source) if (c.source and c.source.get("source_url")) else (self.scout.find(c.gap or {}) or {})
            if not src.get("source_url"):
                c.drop(self.name, "no licensed source found for gap")
                continue
            if not (src.get("author") and src.get("license")):
                c.drop(self.name, "source missing author/license (cannot govern)")
                continue
            if self.require_permissive and not is_permissive(src.get("license", "")):
                c.drop(self.name, f"non-permissive license: {src.get('license')}")
                continue
            src["source_kind"] = normalize_source_kind(src.get("source_kind", "other"))
            c.source = src
            c.mark(self.name, "sourced", src.get("source_url", ""))
        return batch


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    catalog = {
        "g1": {"source_url": "https://eur-lex.europa.eu/csddd", "author": "EU",
               "license": "CC-BY-4.0", "source_kind": "regulation",
               "payload": {"facts": [{"anchor": "Article 8"}]}},
        "g2": {"source_url": "https://example.com/proprietary", "author": "Acme",
               "license": "All Rights Reserved"},
        "g3": {"author": "nobody"},  # no url
    }
    scout = RecordedSourceScout(catalog)
    c1 = Candidate(gap={"id": "g1"})
    c2 = Candidate(gap={"id": "g2"})
    c3 = Candidate(gap={"id": "g3"})
    c4 = Candidate(gap={"id": "missing"})
    SourceStage(scout).run([c1, c2, c3, c4], FoundryContext())
    check("permissive source attached", c1.alive and c1.source.get("source_url"))
    check("source_kind normalized to enum", c1.source.get("source_kind") == "other", c1.source.get("source_kind"))
    check("payload carried for construction", (c1.source.get("payload") or {}).get("facts"))
    check("non-permissive license dropped", not c2.alive and "non-permissive" in c2.reasons[-1])
    check("no url dropped", not c3.alive)
    check("no source found dropped", not c4.alive and "no licensed source" in c4.reasons[-1])

    # require_permissive=False admits a restrictive license (with author+license present)
    c5 = Candidate(gap={"id": "g2"})
    SourceStage(scout, require_permissive=False).run([c5], FoundryContext())
    check("non-permissive admitted when not required", c5.alive)

    print(f"\n{'all sources self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
