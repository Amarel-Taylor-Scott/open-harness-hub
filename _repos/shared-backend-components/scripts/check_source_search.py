#!/usr/bin/env python3
"""check_source_search — Teleon's own PyPI/GitHub search components are real, agnostic, governed, and HONEST.

Hermetic (no network — fixtures injected): the source-search PORT selects per-source adapters ('multiple versions of
search, some PyPI some GitHub'); discover() merges + dedupes by (source,name); when every reachable source is unavailable
it RAISES rather than fabricating (the honest-unavailable stance); network gating is enforced; and the discovery runner
governs hits (license-classify from the single source + dedupe vs the registry + candidate/serves_truth=false, never
auto-promoted). serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_source_search.py --self-test
"""
from __future__ import annotations

import src.teleon.research.source_search as ss
from scripts.discover_tools import build_candidates
from src.teleon.research.source_search import (GitHubSearch, PyPISearch, SourceSearchPort, SourceSearchUnavailable,
                                               ToolHit, discover, select_source_search)


class _Fake(SourceSearchPort):
    def __init__(self, source, hits=None, fail=False):
        self.source, self._hits, self._fail = source, hits or [], fail

    def search(self, query, *, limit=10):
        if self._fail:
            raise SourceSearchUnavailable(f"{self.source} down")
        return self._hits[:limit]


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # the agnostic plane: per-source selection + a future source drops in as another subclass
    ck("select 'pypi' -> PyPISearch", [type(x) for x in select_source_search("pypi")] == [PyPISearch])
    ck("select 'github' -> GitHubSearch", [type(x) for x in select_source_search("github")] == [GitHubSearch])
    ck("select 'auto' -> both versions", {x.source for x in select_source_search("auto")} == {"pypi", "github"})
    try:
        select_source_search("npm"); ck("unknown source raises", False)
    except ValueError:
        ck("unknown source raises", True)

    orig = ss.select_source_search
    try:
        # discover() merges + dedupes by (source,name) across versions
        ss.select_source_search = lambda s="auto": [
            _Fake("github", [ToolHit("github", "a/x", "u", "", "MIT", 9), ToolHit("github", "a/x", "u")]),
            _Fake("pypi", [ToolHit("pypi", "x", "u", "", "MIT")]),
        ]
        merged = discover("q")
        ck("discover dedupes within a source", sum(h.key == "github:a/x" for h in merged) == 1)
        ck("discover merges across sources (github+pypi)", {h.source for h in merged} == {"github", "pypi"})

        # honest-unavailable: ALL sources down -> raise (never fabricate); SOME down -> partial result
        ss.select_source_search = lambda s="auto": [_Fake("github", fail=True), _Fake("pypi", fail=True)]
        try:
            discover("q"); ck("all-unavailable raises (no fabrication)", False)
        except SourceSearchUnavailable:
            ck("all-unavailable raises (no fabrication)", True)
        ss.select_source_search = lambda s="auto": [_Fake("github", fail=True),
                                                    _Fake("pypi", [ToolHit("pypi", "y", "u", "", "BSD-3-Clause")])]
        ck("partial-availability returns what worked", [h.name for h in discover("q")] == ["y"])
    finally:
        ss.select_source_search = orig

    # the DESCENT climbs: a failing API source escalates to its browser-render tier (escalate=True), else stays honest
    orig2, orig_esc = ss.select_source_search, dict(ss._ESCALATION)
    def _raises(fn):
        try:
            fn(); return False
        except SourceSearchUnavailable:
            return True
    try:
        ss.select_source_search = lambda s="auto": [_Fake("pypi", fail=True)]
        class _Esc(SourceSearchPort):
            source = "pypi"
            def search(self, q, *, limit=10):
                return [ToolHit("pypi", "escalated_hit", "u")]
        ss._ESCALATION = {"pypi": _Esc}
        ck("escalate=False does NOT climb (stays honest-unavailable)", _raises(lambda: discover("q", source="pypi")))
        ck("escalate=True climbs API->browser tier", [h.name for h in discover("q", source="pypi", escalate=True)] == ["escalated_hit"])
        class _EscFail(SourceSearchPort):
            source = "pypi"
            def search(self, q, *, limit=10):
                raise SourceSearchUnavailable("bot challenge")
        ss._ESCALATION = {"pypi": _EscFail}
        ck("all tiers down -> raises with no fabrication", _raises(lambda: discover("q", source="pypi", escalate=True)))
    finally:
        ss.select_source_search, ss._ESCALATION = orig2, orig_esc
    ck("PyPI browser-escalation tier exists (don't give up — climb)", hasattr(ss, "PyPIBrowserSearch") and callable(ss.search_via_browser))

    # network gating is real (offline -> Unavailable, not a silent empty)
    orig_net = ss.network_allowed
    try:
        ss.network_allowed = lambda: False
        for adapter in (PyPISearch(), GitHubSearch()):
            try:
                adapter.search("q"); ck(f"{adapter.source} gated on network", False)
            except SourceSearchUnavailable:
                ck(f"{adapter.source} gated on network", True)
    finally:
        ss.network_allowed = orig_net

    # governance: license classified from the single source + registry dedupe + candidate/serves_truth
    cands = build_candidates([ToolHit("github", "acme/new", "u", "", "Apache-2.0"),
                              ToolHit("github", "acme/agpl", "u", "", "AGPL-3.0")], {"faiss"}, plane="vector_store")
    ck("discovered permissive -> vendorable candidate", any(c["id"] == "new" and c["vendorable"] for c in cands))
    ck("discovered copyleft -> technique-only candidate", any(c["id"] == "agpl" and not c["vendorable"] for c in cands))
    ck("candidates are governed (status=candidate, serves_truth=false, not auto-promoted)",
       all(c["status"] == "candidate" and c["serves_truth"] is False for c in cands))

    print("\n" + ("PASS - check_source_search: PyPI+GitHub search components are agnostic, dedupe, honest-unavailable, "
                  "network-gated, and governed (discovery≠trust)." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
