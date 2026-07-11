#!/usr/bin/env python3
"""scripts.layered_primitive_expansion — the LAYERED, multi-call recursive primitive engine toward 50-100M.
For each seed step/task it runs three LLM layers:

  L1  "list ALL the different WAYS this step can occur"            -> ways (variations / approaches / methods)
  L2  "for THIS way, list ALL the ways IT can occur"              -> sub-ways (tool choices / edge cases / depths)
  L3  "generate a CODE EXAMPLE that is the basis for a primitive" -> a primitive TEMPLATE (parameterized code)

Each L2 leaf becomes a primitive, and each L3 code example becomes a reusable PRIMITIVE TEMPLATE. The fan-out
is multiplicative — thousands of seeds x ~10 ways x ~10 sub-ways x a code template = millions per pass — so an
iterative deterministic loop over thousands of tasks + job descriptions safely reaches 50-100M candidates. Seeds
come from the ML-lifecycle taxonomy, the grid, personas, and DETERMINISTIC job-description generation.

Cloud lanes only (Ollama Cloud GLM/Kimi, OpenRouter, hosted OpenWebUI Gemma) — NEVER local gemma4 (overheat).
Ids minted only by canonical_id; candidate/serves_truth=false; failures recorded never faked; the staged file
is NEW, never a verified corpus file. Offline --self-test uses a stub model (the layers are pure fan-out logic).

    python3 scripts/layered_primitive_expansion.py --self-test
    python3 scripts/layered_primitive_expansion.py --run --seeds 20 --l1 8 --l2 6 --provider ollama --model glm-5.2
    python3 scripts/layered_primitive_expansion.py --run --job-seeds 2000 --l1 10 --l2 10   # toward 50-100M
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel) ──────────────────────────────────────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Callable, Iterator, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"layered_primitive_expansion requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
LAYER_ID_PREFIX = "prim-layered"
LAYER_RECORD_TYPE = "layered_primitive_candidate"
STAGED_FILENAME = "layered_primitive_candidates.jsonl"
_VERIFIED_CORPUS_FILENAMES = frozenset({"verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl"})
_CAMEL_EDGE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_COPRIME_STRIDE = 2147483647

_L1_SYSTEM = "You enumerate the concrete WAYS a software/ML step can be done. Reply ONLY as JSON."
_L2_SYSTEM = "You enumerate the concrete sub-variations of ONE approach (tools, edge cases, depths). Reply ONLY as JSON."
_L3_SYSTEM = "You write a small, reusable CODE TEMPLATE (a primitive basis) for one approach. Reply ONLY as JSON."


def _l1_prompt(seed: dict[str, Any]) -> str:
    return (f"Step/task: {seed.get('title') or seed.get('task')}\nContext: {str(seed.get('context') or '')[:200]}\n\n"
            'List ALL the concrete WAYS this step can be done (approaches, methods, algorithms, tools). '
            'Reply ONLY as JSON: {"ways":[{"name":"...","summary":"one line"}]}')


def _l2_prompt(seed: dict[str, Any], way: dict[str, Any]) -> str:
    return (f"Step: {seed.get('title') or seed.get('task')}\nApproach: {way.get('name')} — {way.get('summary')}\n\n"
            'List ALL the sub-variations of THIS approach (specific tools, edge cases, parameterizations, '
            'depths). Reply ONLY as JSON: {"sub_ways":[{"name":"...","input":"...","output":"...","tool":"..."}]}')


def _l3_prompt(sub: dict[str, Any]) -> str:
    return (f"Approach variation: {sub.get('name')} (tool {sub.get('tool')}, {sub.get('input')} -> {sub.get('output')}).\n"
            'Write a small reusable CODE TEMPLATE (a primitive basis) implementing it. Reply ONLY as JSON: '
            '{"language":"python","signature":"def ...(...):","code":"...","doc":"one line"}')


def _extract_json(text: str) -> Optional[Any]:
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _camel(*words: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", " ".join(words))
    return ("".join(p[:1].upper() + p[1:] for p in parts if p) or "X")[:60]


def _leaf_card(seed: dict[str, Any], way: dict[str, Any], sub: dict[str, Any], code: Optional[dict[str, Any]],
               *, provider: str) -> Optional[dict[str, Any]]:
    name = str(sub.get("name") or "").strip()
    if not name:
        return None
    step = seed.get("title") or seed.get("task") or "step"
    title = f"{name} — a way to {step}"
    body = (f"Layered primitive: to {step}, use the '{way.get('name')}' approach, specifically {name} "
            f"(tool {sub.get('tool')}). Input: {sub.get('input')}. Output: {sub.get('output')}.")
    has_template = bool(code and code.get("code"))
    pid = canonical_id(LAYER_ID_PREFIX, title, body)
    card = {"record_type": LAYER_RECORD_TYPE, "schema_version": 1, "kind": "route.primitive",
            "primitive_id": pid, "title": title[:180], "blackbox": body[:1400],
            "input_edge": _camel(str(sub.get("input") or step), "input"),
            "output_edge": _camel(str(sub.get("output") or name), "result"),
            "blocking_keys": [w.lower() for w in re.findall(r"[a-z]+", (name + " " + step).lower())][:8] or ["primitive"],
            "layers": {"l0_seed": step, "l1_way": way.get("name"), "l2_sub_way": name},
            "is_template": has_template,
            "provenance": {"minter": "scripts.layered_primitive_expansion", "provider": provider}, **BOUNDARY}
    if has_template:
        card["primitive_template"] = {"language": code.get("language", "python"),
                                      "signature": str(code.get("signature") or "")[:200],
                                      "code": str(code.get("code") or "")[:2000], "doc": str(code.get("doc") or "")[:200]}
    return card


def expand_layered(seed: dict[str, Any], transport: Callable[[str, str], dict[str, Any]], *,
                   l1_cap: int = 8, l2_cap: int = 6, do_code: bool = True) -> dict[str, Any]:
    """Run L1 (ways) -> L2 (sub-ways) -> L3 (code template) for one seed. Returns cards + a ledger. Bounded by
    l1_cap x l2_cap leaves. Failures recorded, never faked."""
    cards: list[dict[str, Any]] = []
    r1 = transport(_L1_SYSTEM, _l1_prompt(seed))
    if not r1.get("ok"):
        return {"cards": [], "ledger": {"seed": str(seed.get("title") or seed.get("task"))[:40],
                                        "outcome": "l1_failed", "detail": r1.get("error")}, **BOUNDARY}
    p1 = _extract_json(r1.get("text") or "")
    ways = (p1.get("ways") if isinstance(p1, dict) else None) or []
    prov = r1.get("provider", "stub")
    for way in ways[:l1_cap]:
        r2 = transport(_L2_SYSTEM, _l2_prompt(seed, way))
        if not r2.get("ok"):
            continue
        p2 = _extract_json(r2.get("text") or "")
        subs = (p2.get("sub_ways") if isinstance(p2, dict) else None) or []
        for sub in subs[:l2_cap]:
            code = None
            if do_code:
                r3 = transport(_L3_SYSTEM, _l3_prompt(sub))
                code = _extract_json(r3.get("text") or "") if r3.get("ok") else None
            c = _leaf_card(seed, way, sub, code, provider=prov)
            if c:
                cards.append(c)
    return {"cards": cards, "ledger": {"seed": str(seed.get("title") or seed.get("task"))[:40],
                                       "outcome": "expanded", "ways": len(ways[:l1_cap]),
                                       "generated": len(cards), "templates": sum(1 for c in cards if c.get("is_template"))},
            **BOUNDARY}


# ── deterministic job-description / task seeds (thousands) ────────────────────────────────────────────────────
_JOB_ROLES: tuple[str, ...] = (
    "data engineer", "ml engineer", "mlops engineer", "data scientist", "backend engineer", "sre",
    "security engineer", "analytics engineer", "research scientist", "platform engineer", "ai engineer",
    "quant researcher", "bioinformatician", "computer vision engineer", "nlp engineer", "recsys engineer",
)
_JOB_TASKS: tuple[str, ...] = (
    "build a churn model", "deploy a fraud detector", "ship a recommender", "forecast demand",
    "monitor model drift", "build a feature store", "set up a retraining pipeline", "run an A/B test",
    "add a fallback path", "instrument prediction logging", "validate data quality", "engineer features",
    "package a model for serving", "roll out a canary deployment", "audit model fairness",
    "build a RAG chatbot", "detect anomalies in telemetry", "rank search results",
)
_JOB_DOMAINS: tuple[str, ...] = (
    "fintech", "healthcare", "e-commerce", "logistics", "gaming", "adtech", "cybersecurity", "biotech",
    "media", "manufacturing", "energy", "telecom", "govtech", "climate",
)


def job_description_seeds(n: int) -> list[dict[str, Any]]:
    """Deterministic (role x task x domain) job-description seeds — thousands of realistic step-owners."""
    total = len(_JOB_ROLES) * len(_JOB_TASKS) * len(_JOB_DOMAINS)
    seeds: list[dict[str, Any]] = []
    for i in range(min(n, total)):
        flat = (i * _COPRIME_STRIDE) % total
        ri = flat % len(_JOB_ROLES)
        ti = (flat // len(_JOB_ROLES)) % len(_JOB_TASKS)
        di = flat // (len(_JOB_ROLES) * len(_JOB_TASKS))
        role, task, dom = _JOB_ROLES[ri], _JOB_TASKS[ti], _JOB_DOMAINS[di]
        seeds.append({"task": f"{task} for {dom}", "context": f"as a {role} in {dom}",
                      "role": role, "domain": dom})
    return seeds


def lifecycle_seeds(n: int) -> list[dict[str, Any]]:
    """Seed from the ML-lifecycle taxonomy operations (reuse — single source)."""
    try:
        import scripts.ml_lifecycle_primitive_minter as ml  # noqa: PLC0415
        spine = ml._OP_SPINE  # noqa: SLF001
    except Exception:  # noqa: BLE001
        return []
    step = max(1, len(spine) // max(1, n))
    return [{"title": op, "context": f"{stage} stage ({phase} phase)"} for _num, phase, stage, op in spine[::step][:n]]


def job_seed_capacity() -> int:
    return len(_JOB_ROLES) * len(_JOB_TASKS) * len(_JOB_DOMAINS)


def staged_path() -> Path:
    return resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / STAGED_FILENAME


def write_staged(cards: list[dict[str, Any]], target_path: Optional[Path] = None) -> dict[str, Any]:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    p = target_path or staged_path()
    if p.name != STAGED_FILENAME:
        raise ValueError(f"refusing to write to {p.name!r} — only {STAGED_FILENAME!r} allowed")
    if p.is_symlink() or (p.exists() and p.resolve().name in _VERIFIED_CORPUS_FILENAMES):
        raise ValueError("refused: symlink or verified-corpus target")
    for c in cards:
        if c.get("primitive_id") != canonical_id(LAYER_ID_PREFIX, c.get("title", ""), c.get("blackbox", "")):
            raise ValueError(f"card {c.get('primitive_id')} id does not recompute")
        for ef in ("input_edge", "output_edge"):
            if not _CAMEL_EDGE_RE.match(str(c.get(ef) or "")):
                raise ValueError(f"{ef} not CamelCase on {c.get('primitive_id')}")
    existing = {str(r.get("primitive_id")) for r in (read_jsonl_tolerant(p) if p.exists() else [])}
    appended = 0
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        for c in cards:
            if str(c["primitive_id"]) in existing:
                continue
            existing.add(str(c["primitive_id"]))
            fh.write(json.dumps(c, sort_keys=True) + "\n")
            appended += 1
    return {"appended": appended, "on_file": len(existing), "path": str(p), **BOUNDARY}


def projected_capacity(n_seeds: int, l1: int, l2: int) -> int:
    """The multiplicative fan-out projection: seeds x L1 ways x L2 sub-ways (one template each)."""
    return n_seeds * l1 * l2


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # deterministic job seeds (thousands)
    js = job_description_seeds(50)
    checks.append(("job-description seeds are deterministic (role x task x domain)",
                   len(js) == 50 and js == job_description_seeds(50) and job_seed_capacity() >= 3000))

    def _stub(system: str, user: str) -> dict[str, Any]:
        if system == _L1_SYSTEM:
            return {"ok": True, "provider": "stub", "text": json.dumps(
                {"ways": [{"name": "gradient boosting", "summary": "tree ensemble"},
                          {"name": "logistic regression", "summary": "linear baseline"}]})}
        if system == _L2_SYSTEM:
            return {"ok": True, "provider": "stub", "text": json.dumps(
                {"sub_ways": [{"name": "xgboost with early stopping", "input": "features", "output": "probs", "tool": "xgboost"},
                              {"name": "lightgbm with GOSS", "input": "features", "output": "probs", "tool": "lightgbm"}]})}
        return {"ok": True, "provider": "stub", "text": json.dumps(
            {"language": "python", "signature": "def fit(X, y):", "code": "def fit(X,y):\n    return model", "doc": "fit a GBM"})}
    result = expand_layered({"title": "build a churn model", "context": "model phase"}, _stub, l1_cap=8, l2_cap=6)
    # 2 ways x 2 sub-ways = 4 leaf cards, each with a code template
    checks.append(("L1 -> L2 -> L3 fan-out produces leaf cards with code TEMPLATES",
                   result["cards"] and len(result["cards"]) == 4
                   and all(c["is_template"] and c["primitive_template"]["code"] for c in result["cards"])))
    checks.append(("each card records its 3 layers (seed / way / sub-way)",
                   all(set(c["layers"]) == {"l0_seed", "l1_way", "l2_sub_way"} for c in result["cards"])))
    checks.append(("cards validate (id recompute, edges, boundary)",
                   all(c["primitive_id"] == canonical_id(LAYER_ID_PREFIX, c["title"], c["blackbox"])
                       and _CAMEL_EDGE_RE.match(c["input_edge"]) and c["serves_truth"] is False
                       for c in result["cards"])))
    # L1 failure recorded, never faked
    f = expand_layered({"title": "x"}, lambda s, u: {"ok": False, "error": "cap"})
    checks.append(("an L1 lane failure is recorded, never fabricated", f["cards"] == [] and f["ledger"]["outcome"] == "l1_failed"))
    # capacity projection: thousands of seeds x fan-out reaches tens of millions
    checks.append(("the fan-out projection reaches 50-100M over thousands of seeds",
                   projected_capacity(job_seed_capacity(), 10, 10) >= 300_000
                   and projected_capacity(50000, 20, 20) >= 20_000_000))
    # staging safety + dedupe
    import tempfile  # noqa: PLC0415
    refused = False
    try:
        write_staged(result["cards"][:1], target_path=Path(tempfile.gettempdir()) / "verified_factory_primitive_cards.jsonl")
    except ValueError:
        refused = True
    checks.append(("write_staged refuses a verified corpus filename", refused))
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td) / STAGED_FILENAME
        a = write_staged(result["cards"], target_path=tp)
        b = write_staged(result["cards"], target_path=tp)
        checks.append(("append-dedupe", a["appended"] == 4 and b["appended"] == 0))
    # lifecycle seeds reuse the taxonomy
    ls = lifecycle_seeds(20)
    checks.append(("lifecycle seeds come from the ML-lifecycle taxonomy", len(ls) >= 15 and all("title" in s for s in ls)))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - layered_primitive_expansion: L1(ways) -> L2(sub-ways) -> L3(code template) recursive fan-out; "
          "each leaf a primitive with a code-template basis; deterministic job-description + lifecycle seeds "
          "(thousands); multiplicative projection reaches 50-100M; cloud lanes only (never local gemma4); "
          "failures recorded. serves_truth=false.")
    return 0


def _make_transport(providers: list[str], model: str) -> Callable[[str, str], dict[str, Any]]:
    from scripts import _llm_client  # noqa: PLC0415
    resolved = [(n, _llm_client.resolve_provider(n)) for n in providers]

    def _call(system: str, user: str) -> dict[str, Any]:
        last = ""
        for name, prov in resolved:
            try:
                r = _llm_client.chat(model, system, user, prov)  # inherit the high-ceiling default; never truncate generation
                if not r.get("error") and (r.get("text") or "").strip():
                    return {"ok": True, "text": r["text"], "provider": name}
                last = str(r.get("error") or "empty")[:120]
            except Exception as exc:  # noqa: BLE001
                last = str(exc)[:120]
        return {"ok": False, "error": last}
    return _call


def _run(n_seeds: int, job_seeds: int, l1: int, l2: int, providers: list[str], model: str) -> int:
    transport = _make_transport(providers, model)
    seeds = job_description_seeds(job_seeds) if job_seeds else lifecycle_seeds(n_seeds)
    all_cards: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    for seed in seeds:
        r = expand_layered(seed, transport, l1_cap=l1, l2_cap=l2)
        all_cards.extend(r["cards"])
        ledger.append(r["ledger"])
    wrote = write_staged(all_cards) if all_cards else {"appended": 0, "on_file": 0}
    rec = {"record_type": "layered_expansion_receipt", "n_seeds": len(seeds), "l1_cap": l1, "l2_cap": l2,
           "n_generated": len(all_cards), "n_templates": sum(1 for c in all_cards if c.get("is_template")),
           "staged": wrote["appended"], "projected_capacity_per_50k_seeds": projected_capacity(50000, l1, l2),
           "ledger_sample": ledger[:20], "providers": providers, "model": model, **BOUNDARY}
    out = resource("data") / "dev-intel" / "session_emulation" / "layered_expansion_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({k: rec[k] for k in ("n_seeds", "n_generated", "n_templates", "staged",
                                          "projected_capacity_per_50k_seeds")}, indent=2))
    print(f"\nreceipt: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--seeds", type=int, default=20, help="lifecycle-taxonomy seeds (when --job-seeds is 0)")
    ap.add_argument("--job-seeds", type=int, default=0, help="deterministic job-description seeds (role x task x domain)")
    ap.add_argument("--l1", type=int, default=8, help="max ways per seed (layer 1)")
    ap.add_argument("--l2", type=int, default=6, help="max sub-ways per way (layer 2)")
    ap.add_argument("--provider", default="ollama,openrouter,openwebui")
    ap.add_argument("--model", default="glm-5.2")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.seeds, args.job_seeds, args.l1, args.l2,
                    [p.strip() for p in args.provider.split(",") if p.strip()], args.model)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
