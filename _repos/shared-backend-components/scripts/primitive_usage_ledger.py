#!/usr/bin/env python3
"""primitive_usage_ledger — track the text, primitives, embeddings, and prompts used every time a primitive is
SEARCHED, DOWNLOADED, and successfully IMPLEMENTED (the outcome graph that trains the whole retrieval stack).

Owner (2026-07-10): "track the text, and primitives and embeddings and input prompts that were used every time this
primitive gets searched for, downloaded, and successfully implemented."

Every event is an append-only, HASH-CHAINED receipt (tamper-evident, like the reuse fabric's receipts) capturing:
query text · the primitive(s) · the embedding MODEL + matched SURFACE (which vector won) · the input-PROMPT digest +
bounded preview (raw prompts are NOT stored in full — privacy + the no-raw-bodies discipline) · outcome · session ·
agent · ts. From this ledger we derive: per-primitive usage stats (search/download/implement counts + success rate),
TRAINING PAIRS (query -> successfully-implemented primitive) for `linker_scoring_zoo.train_weights` + the ranker/
router, and the model×surface evidence (which embedding actually led to a successful implementation). This is the
strongest feedback signal (the research bundle's hierarchy: displayed < selected < resolved < compiled < tests-pass <
merged < survived-production). serves_truth=false — telemetry is measurement, never served truth.

    PYTHONPATH=. python3 scripts/primitive_usage_ledger.py --self-test
    PYTHONPATH=. python3 scripts/primitive_usage_ledger.py --report   # per-primitive usage rollup from the real ledger
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
_LEDGER = _REPO / "data" / "dev-intel" / "primitive_usage_ledger" / "events.jsonl"

EVENT_TYPES = ("searched", "downloaded", "implemented")
_PROMPT_PREVIEW = 160  # bounded prompt snippet stored alongside the digest (raw prompt not persisted in full)


def _digest(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()[:16]


def _chain_hash(prev_hash: str, body: dict[str, Any]) -> str:
    """Tamper-evident chain: h_i = sha256(h_{i-1} + canonical(body_i)). Editing any past event breaks every hash after."""
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((prev_hash + canonical).encode("utf-8")).hexdigest()


def log_event(event_type: str, *, primitive_ids: list[str], query_text: str = "", embedding_model: str = "",
              matched_surface: str = "", input_prompt: str = "", outcome: str = "", session_id: str = "",
              agent: str = "", ts: str = "", ledger_path: Optional[Path] = None) -> dict[str, Any]:
    """Append one hash-chained usage event. `ts` is caller-provided (wall-clock in prod; fixed in tests) so the
    chain is reproducible. Returns the written record."""
    if event_type not in EVENT_TYPES:
        raise ValueError(f"event_type must be one of {EVENT_TYPES}")
    path = Path(ledger_path or _LEDGER)
    path.parent.mkdir(parents=True, exist_ok=True)
    prev_hash = "GENESIS"
    seq = 0
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                seq += 1
                try:
                    prev_hash = json.loads(line).get("hash", prev_hash)
                except json.JSONDecodeError:
                    pass
    body = {"seq": seq, "ts": ts, "event_type": event_type, "primitive_ids": list(primitive_ids),
            "query_text": query_text[:400], "embedding_model": embedding_model, "matched_surface": matched_surface,
            "input_prompt_digest": _digest(input_prompt) if input_prompt else "",
            "input_prompt_preview": input_prompt[:_PROMPT_PREVIEW], "outcome": outcome,
            "session_id": session_id, "agent": agent, "prev_hash": prev_hash,
            "candidate": True, "serves_truth": False}
    rec = {**body, "hash": _chain_hash(prev_hash, body)}
    with path.open("a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


# convenience wrappers (the three tracked moments)
def log_search(query_text, hits, *, embedding_model="", matched_surface="", input_prompt="", **kw):
    """A search: the query, which primitives came back, the embedding model + surface that matched, the prompt."""
    return log_event("searched", primitive_ids=[h.get("primitive_id") if isinstance(h, dict) else h for h in hits],
                     query_text=query_text, embedding_model=embedding_model, matched_surface=matched_surface,
                     input_prompt=input_prompt, **kw)


def log_download(primitive_id, *, query_text="", **kw):
    return log_event("downloaded", primitive_ids=[primitive_id], query_text=query_text, **kw)


def log_implement(primitive_id, *, success: bool, query_text="", input_prompt="", **kw):
    return log_event("implemented", primitive_ids=[primitive_id], query_text=query_text, input_prompt=input_prompt,
                     outcome=("success" if success else "failure"), **kw)


# ================================================================================================================
# Read side — chain integrity, per-primitive rollup, training pairs
# ================================================================================================================
def load_events(ledger_path: Optional[Path] = None) -> list[dict[str, Any]]:
    path = Path(ledger_path or _LEDGER)
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def verify_chain(ledger_path: Optional[Path] = None) -> dict[str, Any]:
    """Recompute the hash chain; report the first break (tamper-evidence). ok=True if intact."""
    events = load_events(ledger_path)
    prev = "GENESIS"
    for i, e in enumerate(events):
        body = {k: e[k] for k in e if k != "hash"}
        if e.get("prev_hash") != prev or _chain_hash(prev, body) != e.get("hash"):
            return {"ok": False, "broken_at": i, "n_events": len(events)}
        prev = e["hash"]
    return {"ok": True, "n_events": len(events)}


def primitive_usage(primitive_id: str, ledger_path: Optional[Path] = None) -> dict[str, Any]:
    """Rollup for one primitive: search/download/implement counts, success rate, and the queries/models/surfaces
    that led to a SUCCESSFUL implementation (the signal worth training on)."""
    from collections import Counter
    ev = [e for e in load_events(ledger_path) if primitive_id in e.get("primitive_ids", [])]
    searched = sum(e["event_type"] == "searched" for e in ev)
    downloaded = sum(e["event_type"] == "downloaded" for e in ev)
    impl = [e for e in ev if e["event_type"] == "implemented"]
    ok = sum(e.get("outcome") == "success" for e in impl)
    succ_q = Counter(e["query_text"] for e in impl if e.get("outcome") == "success")
    succ_m = Counter(e["embedding_model"] for e in ev if e.get("embedding_model") and e["event_type"] == "searched")
    succ_s = Counter(e["matched_surface"] for e in ev if e.get("matched_surface") and e["event_type"] == "searched")
    return {"primitive_id": primitive_id, "searched": searched, "downloaded": downloaded,
            "implemented": len(impl), "implement_success": ok,
            "success_rate": round(ok / len(impl), 3) if impl else 0.0,
            "top_success_queries": succ_q.most_common(5), "top_search_models": succ_m.most_common(5),
            "top_matched_surfaces": succ_s.most_common(5)}


def training_pairs(ledger_path: Optional[Path] = None) -> list[dict[str, Any]]:
    """(query -> {primitives successfully implemented}) pairs — the labelled data that trains the ranker/scorers.
    ONLY successful implementations count (the strong signal), never mere displays/searches."""
    from collections import defaultdict
    pos = defaultdict(set)
    for e in load_events(ledger_path):
        if e["event_type"] == "implemented" and e.get("outcome") == "success" and e.get("query_text"):
            for pid in e["primitive_ids"]:
                pos[e["query_text"]].add(pid)
    return [{"query": q, "relevant": sorted(ids)} for q, ids in sorted(pos.items())]


# ================================================================================================================
# Self-test (isolated temp ledger; fixed ts for a reproducible chain)
# ================================================================================================================
def _self_test() -> int:
    import tempfile
    checks: list[tuple[str, bool, str]] = []
    with tempfile.TemporaryDirectory() as td:
        led = Path(td) / "events.jsonl"

        # (1) log a realistic sequence: search -> download -> implement(success) for a primitive.
        log_search("hash a password", [{"primitive_id": "p:hash"}, {"primitive_id": "p:validate"}],
                   embedding_model="ollama_embeddinggemma", matched_surface="problem",
                   input_prompt="user asked to hash a new password before storing it", ts="t0", ledger_path=led)
        log_download("p:hash", query_text="hash a password", ts="t1", ledger_path=led)
        log_implement("p:hash", success=True, query_text="hash a password",
                      input_prompt="wire security.password-hash into create-user", ts="t2", ledger_path=led)
        log_implement("p:validate", success=False, query_text="validate the user", ts="t3", ledger_path=led)
        events = load_events(led)
        checks.append((f"logged {len(events)} events (search/download/implement) capturing query+model+surface+prompt",
                       len(events) == 4 and events[0]["embedding_model"] == "ollama_embeddinggemma"
                       and events[0]["matched_surface"] == "problem" and events[0]["input_prompt_digest"], ""))

        # (2) HASH CHAIN intact.
        v = verify_chain(led)
        checks.append((f"hash chain verifies intact ({v['n_events']} events)", v["ok"], json.dumps(v)))

        # (3) TAMPER detection: edit a past event -> chain breaks.
        lines = led.read_text().splitlines()
        rec0 = json.loads(lines[0]); rec0["query_text"] = "TAMPERED"; lines[0] = json.dumps(rec0, sort_keys=True)
        led.write_text("\n".join(lines) + "\n")
        vt = verify_chain(led)
        checks.append(("tamper detected: editing a past event breaks the chain", not vt["ok"], json.dumps(vt)))

        # rebuild a clean ledger for the rollup checks
        led2 = Path(td) / "events2.jsonl"
        log_search("hash a password", [{"primitive_id": "p:hash"}], embedding_model="fastembed_bge_large",
                   matched_surface="code", ts="t0", ledger_path=led2)
        log_implement("p:hash", success=True, query_text="hash a password", ts="t1", ledger_path=led2)
        log_implement("p:hash", success=True, query_text="salt and hash a password", ts="t2", ledger_path=led2)

        # (4) per-primitive ROLLUP: counts + success rate + top queries/models/surfaces.
        u = primitive_usage("p:hash", led2)
        checks.append((f"rollup: searched={u['searched']} implemented={u['implemented']} success_rate={u['success_rate']}",
                       u["implemented"] == 2 and u["implement_success"] == 2 and u["success_rate"] == 1.0
                       and ("fastembed_bge_large", 1) in u["top_search_models"], json.dumps(u["top_success_queries"])))

        # (5) TRAINING PAIRS: only successful implementations become labelled (query -> primitive) data.
        tp = training_pairs(led2)
        checks.append((f"training pairs from successful implements ({len(tp)} queries)",
                       any(p["query"] == "hash a password" and "p:hash" in p["relevant"] for p in tp), json.dumps(tp)))

    ok = all(c[1] for c in checks)
    print(f"{'PASS' if ok else 'FAIL'} - primitive_usage_ledger: hash-chained search/download/implement events "
          f"(query+embedding-model+surface+prompt-digest) -> per-primitive rollup + training pairs. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Track search/download/implement usage per primitive (hash-chained; trains the ranker).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true", help="per-primitive usage rollup from the real ledger")
    ap.add_argument("--verify", action="store_true", help="verify the real ledger's hash chain")
    ap.add_argument("--primitive", default=None, help="rollup a specific primitive_id")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.verify:
        print(json.dumps(verify_chain(), indent=2))
        return 0
    if args.report or args.primitive:
        if args.primitive:
            print(json.dumps(primitive_usage(args.primitive), indent=2))
        else:
            print(json.dumps({"events": len(load_events()), "chain": verify_chain(),
                              "training_pairs": len(training_pairs())}, indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
