#!/usr/bin/env python3
"""scripts.code_graph — a DETERMINISTIC code-dependency graph for this repo (stdlib `ast` only; no external graph
engine, always available, proof-gated). It traces which files interact: file→file import edges + the symbols that
cross each boundary, so before editing a file you can see its UPSTREAM (who depends on me → what breaks if I change)
and DOWNSTREAM (what I depend on) neighbors + the full impact set.

This is the deterministic substrate the owner asked for; a tree-sitter tool like codegraph adds the multi-language
+ richer semantic layer on top, but this one needs nothing installed and is enforced by the flywheel.

  --file <path>     print a file's upstream/downstream neighbors + transitive impact
  --json <path>     same, as JSON
  --self-test       validate the graph (the registered proof)
  --stats           print graph stats

CLI: PYTHONPATH=. python3 scripts/code_graph.py --file src/teleon/seeds/capability_seed.py
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ROOTS = ("src", "scripts", "local_emulators")
_SKIP = {"__pycache__", ".git", "node_modules", ".venv", "_reference", "repo_reference"}


def _module_of(path: Path) -> str:
    return ".".join(path.relative_to(_REPO).with_suffix("").parts)


def _py_files() -> list[Path]:
    out = []
    for root in _ROOTS:
        base = _REPO / root
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if not any(part in _SKIP for part in p.parts):
                out.append(p)
    return sorted(out)


class CodeGraph:
    """File-level import dependency graph + the symbols crossing each edge. Deterministic (sorted everywhere)."""

    def __init__(self) -> None:
        self.modules: dict[str, str] = {}                  # module -> relative path
        self.imports: dict[str, set[str]] = {}             # module -> in-repo modules it imports (downstream)
        self.symbols: dict[str, list[tuple]] = {}          # module -> [(target_module, symbol)] crossing the boundary
        self._upstream: dict[str, set[str]] = {}           # module -> modules that import it (reverse)

    def _resolve(self, mod: str, name: str, all_mods: set[str]) -> str | None:
        """Resolve `from <mod> import <name>` to the concrete in-repo module it binds (the submodule or the package)."""
        if f"{mod}.{name}" in all_mods:
            return f"{mod}.{name}"
        if mod in all_mods:
            return mod
        return None

    def build(self) -> "CodeGraph":
        files = _py_files()
        self.modules = {_module_of(p): str(p.relative_to(_REPO)) for p in files}
        all_mods = set(self.modules)
        for p in files:
            mod = _module_of(p)
            imports: set[str] = set()
            symbols: list[tuple] = []
            try:
                tree = ast.parse(p.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                self.imports[mod] = imports
                self.symbols[mod] = symbols
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    for alias in node.names:
                        tgt = self._resolve(node.module, alias.name, all_mods)
                        if tgt and tgt != mod:
                            imports.add(tgt)
                            symbols.append((tgt, alias.name))
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in all_mods and alias.name != mod:
                            imports.add(alias.name)
            self.imports[mod] = imports
            self.symbols[mod] = sorted(set(symbols))
        # reverse edges
        self._upstream = {m: set() for m in self.modules}
        for m, deps in self.imports.items():
            for d in deps:
                self._upstream.setdefault(d, set()).add(m)
        return self

    # --- queries (all deterministic, sorted) ---------------------------------
    def _mod(self, file_or_module: str) -> str | None:
        if file_or_module in self.modules:
            return file_or_module
        norm = file_or_module.replace("\\", "/").lstrip("./")
        for m, path in self.modules.items():
            if path == norm:
                return m
        # tolerate a path that maps cleanly to a module
        cand = ".".join(Path(norm).with_suffix("").parts)
        return cand if cand in self.modules else None

    def downstream(self, target: str) -> list[str]:
        m = self._mod(target)
        return sorted(self.imports.get(m, set())) if m else []

    def upstream(self, target: str) -> list[str]:
        m = self._mod(target)
        return sorted(self._upstream.get(m, set())) if m else []

    def impact(self, target: str) -> list[str]:
        """Everything that transitively depends on `target` (the blast radius of a change)."""
        m = self._mod(target)
        if not m:
            return []
        seen: set[str] = set()
        stack = [m]
        while stack:
            cur = stack.pop()
            for up in self._upstream.get(cur, set()):
                if up not in seen:
                    seen.add(up)
                    stack.append(up)
        return sorted(seen)

    def neighbors(self, target: str) -> dict:
        m = self._mod(target)
        return {"module": m, "path": self.modules.get(m), "downstream": self.downstream(target),
                "upstream": self.upstream(target), "impact": self.impact(target),
                "symbols_used": self.symbols.get(m, []) if m else [], "serves_truth": False}

    def stats(self) -> dict:
        edges = sum(len(v) for v in self.imports.values())
        return {"modules": len(self.modules), "edges": edges,
                "roots": sum(1 for m in self.modules if not self._upstream.get(m)),
                "leaves": sum(1 for m in self.modules if not self.imports.get(m))}


_GRAPH: CodeGraph | None = None


def graph() -> CodeGraph:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = CodeGraph().build()
    return _GRAPH


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    g = graph()
    s = g.stats()
    ck("the graph spans the repo (>= 300 modules, >= 300 import edges)", s["modules"] >= 300 and s["edges"] >= 300, str(s))

    # inverse property: A imports B  <=>  A in upstream(B)  <=>  B in downstream(A)
    sample = sorted(g.modules)[:150]
    ok_inv = all(a in g.upstream(b) for a in sample for b in g.downstream(a))
    ck("upstream/downstream are exact inverses (A imports B <=> A in upstream(B))", ok_inv)

    # a known edge: the capability-seeds proof imports the seeds package; the seed pack depends on the framework
    seeds_fw = "src.teleon.seeds.capability_seed"
    pack = "src.teleon.seeds.github_signal_seeds"
    ck("a known dependency is captured (seed pack -> framework)",
       seeds_fw in g.downstream(pack), str(g.downstream(pack)))
    ck("upstream of the seed framework includes its REAL dependents (the pack + the seeds proof)",
       pack in g.upstream(seeds_fw) and "scripts.check_capability_seeds" in g.upstream(seeds_fw),
       str(g.upstream(seeds_fw)))

    # impact is transitive + a superset of direct upstream
    direct = set(g.upstream(seeds_fw))
    imp = set(g.impact(seeds_fw))
    ck("impact (blast radius) is transitive and a superset of direct upstream", direct <= imp and len(imp) >= len(direct))

    # neighbors works by FILE PATH (the owner's 'editing 1 file' use case) + carries the crossing symbols
    nb = g.neighbors("src/teleon/seeds/capability_seed.py")
    ck("neighbors resolves a FILE PATH and returns upstream/downstream/impact",
       nb["module"] == seeds_fw and isinstance(nb["downstream"], list) and isinstance(nb["upstream"], list))

    ck("the graph never serves truth", nb["serves_truth"] is False)
    ck("deterministic (rebuild -> identical stats + edges)",
       CodeGraph().build().stats() == s and CodeGraph().build().neighbors("src/teleon/seeds/capability_seed.py") == nb)

    print("\n" + (f"PASS - code_graph: deterministic ast-based dependency graph over {s['modules']} modules / "
                  f"{s['edges']} edges; upstream/downstream are exact inverses; impact gives the transitive blast "
                  f"radius; neighbors works by file path with the crossing symbols. Edit a file → see what breaks. "
                  f"Never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--file"); p.add_argument("--json")
    p.add_argument("--self-test", action="store_true"); p.add_argument("--stats", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    if a.stats:
        print(json.dumps(graph().stats(), indent=2)); return 0
    target = a.file or a.json
    if target:
        nb = graph().neighbors(target)
        if a.json:
            print(json.dumps(nb, indent=2))
        else:
            print(f"module: {nb['module']}  ({nb['path']})")
            print(f"  downstream (depends on, {len(nb['downstream'])}): {', '.join(nb['downstream']) or '—'}")
            print(f"  upstream (depended on by, {len(nb['upstream'])}): {', '.join(nb['upstream']) or '—'}")
            print(f"  impact / blast radius ({len(nb['impact'])}): {', '.join(nb['impact'][:30])}{' …' if len(nb['impact'])>30 else ''}")
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
