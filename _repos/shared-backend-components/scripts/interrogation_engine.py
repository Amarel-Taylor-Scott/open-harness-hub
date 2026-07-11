#!/usr/bin/env python3
"""scripts.interrogation_engine — generate the thousands of interrogation questions over EVERY object.

Reads _repos/shared-backend-components/architecture/interrogation_taxonomy.json (object_types x ~30 dimensions x spintax templates x substitution
pools) and expands them — for real repo objects (code-graph symbols / registry records) or a given target — into a
bounded, deduplicated, DETERMINISTIC candidate set. The combinatorial space is astronomical by design; this engine
SAMPLES + CAPS + LOGS what it dropped (no silent truncation — CLAUDE.md). Output is candidate questions
(serves_truth=false) that feed the multi-model panel + the kickstart/rehydration injector.

  --self-test                 offline: spintax expansion, placeholder fill, dedup, deterministic ids, cap+log
  --run [--limit N] [--target PATH] [--dimensions a,b] [--cap N]
                              generate against real objects (default: scan _repos/teleon/backend/src/teleon) -> interrogation_candidates.jsonl
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/interrogation_engine.py --run --limit 5
"""
from __future__ import annotations

import hashlib
import itertools
import json
import re
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
TAXO = _resource("architecture") / "interrogation_taxonomy.json"
OUT = _resource("data") / "dev-intel" / "interrogation_candidates.jsonl"
AXIS_KEYS = ("industry", "company", "architecture", "language", "future_tech", "era")
_SPINTAX = re.compile(r"\{([^{}]*\|[^{}]*)\}")          # a {a|b} group (requires a pipe; leaves {object_type} alone)
_DEF = re.compile(r"^\s*(?:class|def)\s+([A-Za-z_]\w*)", re.M)


def load_taxonomy() -> dict:
    return json.loads(TAXO.read_text(encoding="utf-8"))


def expand_spintax(s: str, cap: int = 24) -> list[str]:
    """Cartesian-expand {a|b|c} groups (capped). Non-pipe placeholders like {object_type} pass through untouched."""
    segments: list[list[str]] = []
    last = 0
    for m in _SPINTAX.finditer(s):
        segments.append([s[last:m.start()]])
        segments.append(m.group(1).split("|"))
        last = m.end()
    segments.append([s[last:]])
    out = []
    for combo in itertools.product(*segments):
        out.append("".join(combo))
        if len(out) >= cap:
            break
    return out


def fill(q: str, object_type: str, pools: dict, rot: int) -> str:
    q = q.replace("{object_type}", object_type)
    for i, ax in enumerate(pools):                       # taxonomy-driven: EVERY context pool is a fillable axis
        ph = "{" + ax + "}"
        if ph in q and pools[ax]:
            q = q.replace(ph, pools[ax][(rot + i * 7) % len(pools[ax])])   # +i*7 → axes vary INDEPENDENTLY (a context vector), not lock-step
    return q


def _has_axis(s: str, pools: dict) -> bool:
    return any("{" + a + "}" in s for a in pools)


def generate(targets: list[dict], taxo: dict, *, dims: list[str] | None = None, per_template_cap: int = 8,
             context_samples: int = 3, total_cap: int = 5000) -> tuple[list[dict], int]:
    pools = taxo["substitution_pools"]
    dimensions = taxo["dimensions"]
    chosen = dims or list(dimensions)
    seen: set[str] = set()
    out: list[dict] = []
    dropped = 0
    for t in targets:
        for dim in chosen:
            for tmpl in dimensions.get(dim, []):
                for base in expand_spintax(tmpl, cap=per_template_cap):
                    n = context_samples if _has_axis(base, pools) else 1
                    for r in range(n):
                        q = fill(base, t["type"], pools, r)
                        qid = hashlib.sha256(f"{t['ref']}|{dim}|{q}".encode()).hexdigest()[:16]
                        if qid in seen:
                            continue
                        seen.add(qid)
                        if len(out) >= total_cap:
                            dropped += 1
                            continue
                        out.append({"qid": qid, "object_ref": t["ref"], "object_type": t["type"],
                                    "dimension": dim, "question": q, "serves_truth": False})
    return out, dropped


def code_targets(limit: int, target: str | None) -> list[dict]:
    """Real repo objects to interrogate: top-level class/def names. A given --target PATH, else scan src/teleon."""
    out: list[dict] = []
    if target:
        p = _resource(target)
        files = [p] if p.is_file() else sorted(p.rglob("*.py"))[:limit]
    else:
        files = sorted((_resource("src") / "teleon").rglob("*.py"))[:limit]
    for f in files:
        rel = f.relative_to(REPO)
        out.append({"ref": str(rel), "type": "module"})
        try:
            for name in _DEF.findall(f.read_text(encoding="utf-8"))[:6]:
                out.append({"ref": f"{rel}::{name}", "type": "class" if name[:1].isupper() else "function"})
        except OSError:
            pass
        if len(out) >= limit:
            break
    return out[:limit]


def self_test() -> int:
    taxo = load_taxonomy()
    # spintax: 3x2 groups -> 6 variants; {object_type} untouched
    v = expand_spintax("Is this the {best|optimal|ideal} way to {build|design} this {object_type}?")
    assert len(v) == 6 and "{object_type}" in v[0], f"spintax expand wrong: {len(v)}"
    # placeholder fill: object_type + axis substitution by rotation
    f0 = fill("How would {industry} build this {object_type}?", "service", taxo["substitution_pools"], 0)
    f1 = fill("How would {industry} build this {object_type}?", "service", taxo["substitution_pools"], 1)
    assert "{" not in f0 and "service" in f0 and f0 != f1, "fill/rotation broken"
    pools = taxo["substitution_pools"]
    assert {"geography", "regulation", "scale", "hardware", "customer_type", "cost_profile", "deployment"} <= set(pools), "context arrays missing"
    assert {"storage", "computation", "transfer", "representation", "contextual_fitness", "architectural_replacement", "deletion"} <= set(taxo["dimensions"]), "architectural/contextual dims missing"
    # CONTEXT VECTOR: a multi-pool template fills every axis, independently, no leftover braces
    mv = fill("Does this {object_type} work in {geography} for {industry} at {scale}?", "service", pools, 0)
    assert "{" not in mv and mv.count("service") == 1, f"multi-axis fill leftover: {mv}"
    # context_samples multiplies context-bearing templates (the mutation layer)
    few, _ = generate([{"ref": "z", "type": "service"}], taxo, dims=["geo_fitness"], context_samples=1)
    many, _ = generate([{"ref": "z", "type": "service"}], taxo, dims=["geo_fitness"], context_samples=5)
    assert len(many) > len(few), "context_samples must multiply context-bearing questions"
    # generate: deterministic ids + dedup + cap honored & logged
    targets = [{"ref": "x.py::Foo", "type": "class"}, {"ref": "y.py::bar", "type": "function"}]
    g1, _ = generate(targets, taxo, dims=["quality", "industry"], total_cap=10_000)
    g2, _ = generate(targets, taxo, dims=["quality", "industry"], total_cap=10_000)
    assert [r["qid"] for r in g1] == [r["qid"] for r in g2], "ids must be deterministic across runs"
    assert len({r["qid"] for r in g1}) == len(g1), "qids must be unique (dedup)"
    capped, dropped = generate(targets, taxo, dims=["quality", "industry"], total_cap=5)
    assert len(capped) == 5 and dropped > 0, "cap must be honored AND dropped count logged (no silent truncation)"
    assert all(r["serves_truth"] is False for r in g1), "candidates must be serves_truth=false"
    # every dimension yields at least one question for a target
    allq, _ = generate([{"ref": "z", "type": "component"}], taxo)
    dims_hit = {r["dimension"] for r in allq}
    assert dims_hit == set(taxo["dimensions"]), f"missing dims: {set(taxo['dimensions']) - dims_hit}"
    print(f"interrogation_engine self-test: OK ({len(allq)} questions for one object across "
          f"{len(taxo['dimensions'])} dimensions; deterministic, deduped, capped+logged)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()

    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default

    if "--run" in argv:
        taxo = load_taxonomy()
        limit = int(opt("--limit", "8"))
        dims = (opt("--dimensions") or "").split(",") if opt("--dimensions") else None
        cs = int(opt("--context-samples", "6" if "--mutate" in argv else "3"))
        if "--mutate" in argv and not dims:   # focus on the contextual-mutation + architectural-decision layers
            dims = taxo["dimension_groups"]["contextual_mutation"] + taxo["dimension_groups"]["architectural_decision"]
        cap = int(opt("--cap", "5000"))
        targets = code_targets(limit, opt("--target"))
        rows, dropped = generate(targets, taxo, dims=dims, context_samples=cs, total_cap=cap)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with OUT.open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        print(f"interrogation_engine: {len(rows)} questions over {len(targets)} objects "
              f"({len({r['dimension'] for r in rows})} dimensions) -> {OUT.relative_to(REPO)}"
              + (f"  [capped: {dropped} dropped]" if dropped else ""))
        for r in rows[:5]:
            print(f"  [{r['dimension']}] {r['object_ref']}: {r['question']}")
        return 0

    print("usage: interrogation_engine.py --self-test | --run [--limit N --target PATH --dimensions a,b --cap N]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
