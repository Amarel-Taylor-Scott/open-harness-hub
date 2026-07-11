#!/usr/bin/env python3
"""scripts.primitive_expansion_loop — grow the primitive corpus OUTWARD by asking an LLM about each primitive
and generating more around it. For a seed primitive we ask: what are its likely USE CASES, typical INPUTS and
OUTPUTS, the INDUSTRIES it serves, the NEIGHBORING primitives it composes with, and its RARE/ESOTERIC variants.
Each neighbor and esoteric variant becomes a new candidate; the neighbors become the next round's seeds — a
breadth-first exploration of primitive-space. We also deterministically seed VERY RARE / ESOTERIC primitives
(obscure data structures & algorithms × niche domains) so the frontier keeps reaching new territory.

This is the LLM-driven supply engine toward the 40M-primitive goal — complementary to the deterministic
combinatorial minters (grid / persona): those enumerate a KNOWN space; this DISCOVERS adjacent + esoteric
space the enumeration misses. Cloud lanes only (Ollama Cloud GLM/Kimi, OpenRouter, hosted OpenWebUI Gemma
after login); NEVER the local Ollama gemma4 (overheat risk). Ids minted only by canonical_id; every card is
candidate/serves_truth=false; the staged file is NEW, never a verified corpus file. Failures recorded, never
faked. Offline --self-test uses a stub model.

    python3 scripts/primitive_expansion_loop.py --self-test
    python3 scripts/primitive_expansion_loop.py --run --rounds 3 --seeds 40 --provider ollama --model glm-5.2
    python3 scripts/primitive_expansion_loop.py --run --esoteric --seeds 60   # seed rare/esoteric frontier
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/primitive_grid_remixer.py) ───────────────────────────
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
from typing import Any, Callable, Optional  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"primitive_expansion_loop requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
EXP_ID_PREFIX = "prim-expand"
EXP_RECORD_TYPE = "expanded_primitive_candidate"
STAGED_FILENAME = "expanded_primitive_candidates.jsonl"
_VERIFIED_CORPUS_FILENAMES = frozenset({"verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl"})
_CAMEL_EDGE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
# cloud lanes only (owner: NEVER local gemma4 — overheat). Fallback order.
_DEFAULT_PROVIDERS = ("ollama", "openrouter", "openwebui")

# ── esoteric seed vocabulary: obscure data structures / algorithms x niche domains. Deterministic seeding of
#    the rare frontier so expansion reaches territory the combinatorial grid never enumerates. ───────────────
_ESOTERIC_TECHNIQUES: tuple[str, ...] = (
    "van Emde Boas tree", "finger tree", "rope (cord) string", "persistent red-black tree", "wavelet tree",
    "FM-index", "Burrows-Wheeler transform", "succinct rank/select bitvector", "cuckoo filter", "xor filter",
    "bloomier filter", "HyperLogLog++ cardinality", "t-digest quantiles", "count-min sketch",
    "Zobrist hashing", "Ukkonen suffix-tree construction", "Aho-Corasick automaton", "suffix automaton",
    "2D Fenwick tree", "link-cut tree", "Euler-tour tree", "heavy-light decomposition", "centroid decomposition",
    "CRDT (RGA) sequence", "operational transform", "Hindley-Milner type inference", "union-find with rollback",
    "sparse table RMQ", "Cartesian tree treap", "skip list with fingers", "splay tree", "van Jacobson timers",
    "quotient filter", "HdrHistogram", "reservoir sampling with weights (A-Res)", "MinHash-LSH banding",
    "SimHash near-dup", "Roaring bitmap", "Elias-Fano encoding", "Golomb-Rice coding",
)
_NICHE_DOMAINS: tuple[str, ...] = (
    "genomic alignment", "real-time bidding", "network packet routing", "column-store compression",
    "time-series anomaly detection", "distributed consensus logs", "full-text search indexing",
    "graph database traversal", "seismic signal processing", "high-frequency order books",
    "content-addressable storage", "collaborative document editing", "spatial GIS queries",
    "compiler register allocation", "rendering scene graphs",
)

_EXPANSION_SYSTEM = ("You are a software-primitive analyst. Given a reusable primitive, you enumerate its "
                     "likely use cases, typical inputs/outputs, industries, the NEIGHBORING primitives it "
                     "composes with, and its RARE/ESOTERIC variants. Reply ONLY as JSON.")


def _expansion_prompt(primitive: dict[str, Any]) -> str:
    title = primitive.get("title") or primitive.get("name") or ""
    desc = str(primitive.get("blackbox") or primitive.get("mechanism") or "")[:400]
    return (f"Primitive: {title}\nDescription: {desc}\n\n"
            "Analyze it and reply ONLY as JSON:\n"
            '{"use_cases":["..."],"typical_input":"...","typical_output":"...","industries":["..."],'
            '"neighbor_primitives":[{"name":"...","mechanism":"one sentence naming concrete tools",'
            '"input":"...","output":"..."}],'
            '"esoteric_variants":[{"name":"a rare/advanced variant","mechanism":"...","input":"...","output":"..."}]}')


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


def _card(item: dict[str, Any], *, kind: str, parent_id: Optional[str], provider: str,
          industries: Optional[list] = None, use_cases: Optional[list] = None) -> Optional[dict[str, Any]]:
    name = str(item.get("name") or "").strip()
    mech = str(item.get("mechanism") or "").strip()
    if not name or not mech:
        return None
    title = f"{name} ({kind})"
    blackbox = (f"{mech} Input: {item.get('input')}. Output: {item.get('output')}. "
                + (f"Industries: {', '.join(str(i) for i in (industries or [])[:5])}. " if industries else "")
                + (f"Use cases: {', '.join(str(u) for u in (use_cases or [])[:3])}." if use_cases else ""))
    pid = canonical_id(EXP_ID_PREFIX, title, blackbox)
    return {"record_type": EXP_RECORD_TYPE, "schema_version": 1, "kind": "route.primitive",
            "primitive_id": pid, "title": title[:180], "blackbox": blackbox[:1400],
            "expansion_kind": kind, "input_edge": _camel(name, "input"),
            "output_edge": _camel(str(item.get("output") or "result"), "result"),
            "blocking_keys": [w.lower() for w in re.findall(r"[a-z]+", (name + " " + mech).lower())][:8] or ["primitive"],
            "industries": industries or [], "use_cases": use_cases or [],
            "provenance": {"minter": "scripts.primitive_expansion_loop", "expansion_kind": kind,
                           "parent_id": parent_id, "provider": provider}, **BOUNDARY}


def expand(seeds: list[dict[str, Any]], transport: Callable[[str, str], dict[str, Any]]) -> dict[str, Any]:
    """Ask the LLM about each seed and generate neighbor + esoteric cards. Returns cards + a ledger + the
    NEXT-round seeds (the neighbors). Failures recorded, never faked."""
    cards: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    next_seeds: list[dict[str, Any]] = []
    for seed in seeds:
        resp = transport(_EXPANSION_SYSTEM, _expansion_prompt(seed))
        if not resp.get("ok"):
            ledger.append({"seed": seed.get("title", "")[:40], "outcome": "failed", "detail": resp.get("error")})
            continue
        parsed = _extract_json(resp.get("text") or "")
        if not isinstance(parsed, dict):
            ledger.append({"seed": seed.get("title", "")[:40], "outcome": "unparseable"})
            continue
        prov = resp.get("provider", "stub")
        industries = parsed.get("industries") if isinstance(parsed.get("industries"), list) else []
        use_cases = parsed.get("use_cases") if isinstance(parsed.get("use_cases"), list) else []
        n_before = len(cards)
        for it in (parsed.get("neighbor_primitives") or []):
            c = _card(it, kind="neighbor", parent_id=seed.get("primitive_id"), provider=prov,
                      industries=industries, use_cases=use_cases)
            if c:
                cards.append(c)
                next_seeds.append({"primitive_id": c["primitive_id"], "title": c["title"], "blackbox": c["blackbox"]})
        for it in (parsed.get("esoteric_variants") or []):
            c = _card(it, kind="esoteric", parent_id=seed.get("primitive_id"), provider=prov, industries=industries)
            if c:
                cards.append(c)
        ledger.append({"seed": seed.get("title", "")[:40], "outcome": "expanded",
                       "generated": len(cards) - n_before, "industries": len(industries)})
    return {"cards": cards, "ledger": ledger, "next_seeds": next_seeds, "n_seeds": len(seeds),
            "n_generated": len(cards), **BOUNDARY}


def esoteric_seed_primitives(n: int) -> list[dict[str, Any]]:
    """Deterministically seed the RARE/ESOTERIC frontier: obscure technique x niche domain (coprime walk)."""
    total = len(_ESOTERIC_TECHNIQUES) * len(_NICHE_DOMAINS)
    stride = 2147483647
    seeds: list[dict[str, Any]] = []
    for i in range(min(n, total)):
        flat = (i * stride) % total
        ti, di = flat % len(_ESOTERIC_TECHNIQUES), flat // len(_ESOTERIC_TECHNIQUES)
        tech, dom = _ESOTERIC_TECHNIQUES[ti], _NICHE_DOMAINS[di]
        title = f"{tech} for {dom} (esoteric seed)"
        blackbox = f"An esoteric primitive applying {tech} to {dom}. A rare, advanced building block."
        seeds.append({"primitive_id": canonical_id(EXP_ID_PREFIX, title, blackbox), "title": title,
                      "blackbox": blackbox, "expansion_kind": "esoteric_seed", **BOUNDARY})
    return seeds


def load_seeds(n: int) -> list[dict[str, Any]]:
    """Seed primitives from the searchable corpus (real, verified-factory cards) — the frontier grows from
    what we already have."""
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    p = resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "verified_factory_primitive_cards.jsonl"
    rows = read_jsonl_tolerant(p) if p.exists() else []
    step = max(1, len(rows) // max(1, n))
    picks = rows[::step][:n]
    return [{"primitive_id": r.get("primitive_id"), "title": r.get("title") or r.get("primitive_id"),
             "blackbox": (r.get("blackbox") if isinstance(r.get("blackbox"), str) else
                          (r.get("blackbox", {}) or {}).get("does", ""))} for r in picks]


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
        if c.get("primitive_id") != canonical_id(EXP_ID_PREFIX, c.get("title", ""), c.get("blackbox", "")):
            raise ValueError(f"card {c.get('primitive_id')} id does not recompute")
        for ef in ("input_edge", "output_edge"):
            if ef in c and not _CAMEL_EDGE_RE.match(str(c.get(ef) or "")):
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


def run_expansion(seeds: list[dict[str, Any]], transport: Callable[[str, str], dict[str, Any]], *,
                  rounds: int) -> dict[str, Any]:
    """BFS expansion: expand seeds, the neighbors become next-round seeds, for `rounds` rounds."""
    all_cards: list[dict[str, Any]] = []
    full_ledger: list[dict[str, Any]] = []
    frontier = seeds
    for r in range(rounds):
        result = expand(frontier, transport)
        all_cards.extend(result["cards"])
        full_ledger.append({"round": r + 1, "seeds": result["n_seeds"], "generated": result["n_generated"]})
        frontier = result["next_seeds"][:len(seeds) * 2]  # bounded frontier growth
        if not frontier:
            break
    return {"cards": all_cards, "rounds_ledger": full_ledger, "n_generated": len(all_cards), **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # esoteric seeds are rare-technique based + deterministic
    es = esoteric_seed_primitives(30)
    checks.append(("esoteric seeds are generated deterministically from rare techniques",
                   len(es) == 30 and es == esoteric_seed_primitives(30)
                   and any("van Emde Boas" in s["title"] or "wavelet" in s["title"].lower()
                           or "FM-index" in s["title"] for s in es)))

    def _stub(system: str, user: str) -> dict[str, Any]:
        return {"ok": True, "provider": "stub",
                "text": json.dumps({"use_cases": ["dedup a stream"], "typical_input": "records",
                                    "typical_output": "clusters", "industries": ["finance", "logistics"],
                                    "neighbor_primitives": [
                                        {"name": "minhash signature", "mechanism": "MinHash over shingles",
                                         "input": "a set", "output": "a signature"},
                                        {"name": "lsh banding", "mechanism": "band the signature into buckets",
                                         "input": "signatures", "output": "candidate pairs"}],
                                    "esoteric_variants": [
                                        {"name": "b-bit minhash", "mechanism": "b-bit MinHash compression",
                                         "input": "a set", "output": "a compact signature"}]})}
    result = expand([{"primitive_id": "seed:1", "title": "dedupe records", "blackbox": "order-preserving dedup"}], _stub)
    checks.append(("expand generates neighbor + esoteric cards with industries + use cases",
                   result["n_generated"] == 3
                   and {c["expansion_kind"] for c in result["cards"]} == {"neighbor", "esoteric"}
                   and any(c["industries"] for c in result["cards"])))
    checks.append(("neighbors become the next-round seeds (BFS frontier)",
                   len(result["next_seeds"]) == 2))
    checks.append(("every generated card validates (id recompute + edges + boundary)",
                   all(c["primitive_id"] == canonical_id(EXP_ID_PREFIX, c["title"], c["blackbox"])
                       and _CAMEL_EDGE_RE.match(c["input_edge"]) and c["serves_truth"] is False
                       for c in result["cards"])))
    fail = expand([{"title": "x"}], lambda s, u: {"ok": False, "error": "rate_limited"})
    checks.append(("a lane failure is recorded, never fabricated", fail["n_generated"] == 0 and fail["ledger"]))
    unpars = expand([{"title": "x"}], lambda s, u: {"ok": True, "text": "no json"})
    checks.append(("an unparseable reply is a recorded miss", unpars["n_generated"] == 0
                   and unpars["ledger"][0]["outcome"] == "unparseable"))
    # BFS over rounds
    multi = run_expansion([{"primitive_id": "s", "title": "dedupe", "blackbox": "dedup"}], _stub, rounds=3)
    checks.append(("BFS expansion runs multiple rounds and accumulates cards",
                   len(multi["rounds_ledger"]) >= 1 and multi["n_generated"] >= 3))
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
        checks.append(("append-dedupe", a["appended"] == 3 and b["appended"] == 0))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - primitive_expansion_loop: send a primitive to an LLM -> use cases + inputs/outputs + "
          "industries + NEIGHBOR primitives + ESOTERIC variants -> new candidates; neighbors become the next "
          "BFS frontier; deterministic esoteric seeding of the rare frontier; failures recorded; cloud lanes "
          "only (never local gemma4). serves_truth=false.")
    return 0


def _make_transport(providers: list[str], model: str) -> Callable[[str, str], dict[str, Any]]:
    """Provider fallback chain. The synthetic provider 'openwebui_cdp' routes to the CDP browser bridge
    (Gemma-4 through the logged-in Chrome, Cloudflare-bypassed) — so a chain like ollama,openwebui_cdp survives
    the Ollama Cloud usage cap by falling through to Gemma."""
    from scripts import _llm_client  # noqa: PLC0415
    resolved = []
    for n in providers:
        if n == "openwebui_cdp":
            resolved.append((n, None))  # bridge marker
        else:
            resolved.append((n, _llm_client.resolve_provider(n)))

    def _call(system: str, user: str) -> dict[str, Any]:
        last = ""
        for name, prov in resolved:
            try:
                if name == "openwebui_cdp":
                    from scripts.openwebui_cdp_bridge import cdp_chat  # noqa: PLC0415
                    m = model if model.startswith("gemma") else "gemma-4-coding"
                    r = cdp_chat(m, system, user)
                    if r.get("ok") and (r.get("text") or "").strip():
                        return {"ok": True, "text": r["text"], "provider": name}
                    last = str(r.get("error") or "empty")[:120]
                    continue
                r = _llm_client.chat(model, system, user, prov)  # inherit the high-ceiling default; never truncate generation
                if not r.get("error") and (r.get("text") or "").strip():
                    return {"ok": True, "text": r["text"], "provider": name}
                last = str(r.get("error") or "empty")[:120]
            except Exception as exc:  # noqa: BLE001
                last = str(exc)[:120]
        return {"ok": False, "error": last}
    return _call


def _run(rounds: int, n_seeds: int, esoteric: bool, providers: list[str], model: str) -> int:
    transport = _make_transport(providers, model)
    seeds = esoteric_seed_primitives(n_seeds) if esoteric else load_seeds(n_seeds)
    result = run_expansion(seeds, transport, rounds=rounds)
    wrote = write_staged(result["cards"]) if result["cards"] else {"appended": 0, "on_file": 0}
    rec = {"record_type": "primitive_expansion_receipt", "rounds": rounds, "seed_mode": "esoteric" if esoteric else "corpus",
           "n_seeds": n_seeds, "n_generated": result["n_generated"], "staged": wrote["appended"],
           "rounds_ledger": result["rounds_ledger"], "providers": providers, "model": model, **BOUNDARY}
    out = resource("data") / "dev-intel" / "session_emulation" / "primitive_expansion_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({k: rec[k] for k in ("seed_mode", "n_seeds", "n_generated", "staged", "rounds_ledger")}, indent=2))
    print(f"\nreceipt: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--esoteric", action="store_true", help="seed the rare/esoteric frontier")
    ap.add_argument("--provider", default=",".join(_DEFAULT_PROVIDERS), help="comma-separated cloud fallback order")
    ap.add_argument("--model", default="glm-5.2")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.rounds, args.seeds, args.esoteric,
                    [p.strip() for p in args.provider.split(",") if p.strip()], args.model)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
