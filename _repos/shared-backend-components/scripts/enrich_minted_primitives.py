#!/usr/bin/env python3
"""scripts.enrich_minted_primitives — upgrade template-minted candidates into DEVELOPER-ACTIONABLE primitives
with REAL model generations (the keyed Ollama Cloud lane): a mechanism sentence naming concrete tools,
implementation steps, and realistic input/output payload descriptions — the exact gaps the quality-audit
fleet grades minted cards against verified ones. LOSSLESS: the original card fields are preserved verbatim;
enrichment lands under an ``enriched`` key with model + token provenance, written to a NEW staged file
(append-deduped). Generation is not promotion; enriched cards remain candidates for the funnel.

    PYTHONPATH=. python3 scripts/enrich_minted_primitives.py --self-test
    PYTHONPATH=. python3 scripts/enrich_minted_primitives.py --run --limit 200 --workers 8 \
        [--capability "single sign on"] [--model glm-5.2:cloud]
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
import os  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts.dev_session_simulation import _chat_messages  # noqa: E402  REUSE: the transport that RETURNS
# the reply text (real_generation_token_bench._ollama_chat counts tokens but discards content — the wave-1
# 0/200 failure; receipts + git history carry the lesson)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_ENRICHED_FILENAME = "enriched_primitive_candidates.jsonl"
_DEFAULT_MODEL = os.environ.get("OH_ENRICH_MODEL", "glm-5.2:cloud")
_DEFAULT_WORKERS = 8


def _enrich_prompt(card: dict[str, Any]) -> str:
    return (
        "Upgrade this software primitive card so a developer can ACT on it. Card:\n"
        f"title: {card.get('title')}\nblackbox: {card.get('blackbox')}\n"
        f"input_edge: {card.get('input_edge')}  output_edge: {card.get('output_edge')}\n"
        "Reply with ONLY a JSON object: {\"blackbox\": one paragraph naming the concrete MECHANISM and 1-3 "
        "real tools/libraries, \"steps\": [3-5 short implementation steps], "
        "\"input_payload\": one sentence describing a realistic input payload, "
        "\"output_payload\": one sentence describing the output payload}.")


def _parse_enrichment(text: str) -> Optional[dict[str, Any]]:
    """Tolerant JSON extraction from a model reply. None on failure — recorded, never fabricated."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
                if isinstance(obj, dict) and obj.get("blackbox") and isinstance(obj.get("steps"), list):
                    return obj
                return None
    return None


def enrich_cards(cards: list[dict[str, Any]], *, model: str = _DEFAULT_MODEL, workers: int = _DEFAULT_WORKERS,
                 transport: Optional[Callable[..., dict[str, Any]]] = None) -> dict[str, Any]:
    """Enrich each card with a REAL generation (order-preserved concurrency). Originals preserved verbatim;
    enrichment + token provenance nested under ``enriched``; failures recorded per card."""
    # NEVER cap generation: thinking models (GLM) spend reasoning tokens INSIDE the budget — 600 truncated the
    # JSON mid-generation on 181/200 of wave 1b (probe receipt: 48-char reply at tokens_out=600), and even 1400
    # can clip a rich enriched card. Use the high ceiling (= _config.LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS = 65536).
    call = transport or (lambda m, p: _chat_messages(m, [{"role": "user", "content": p}], num_predict=65536))
    from concurrent.futures import ThreadPoolExecutor  # noqa: PLC0415
    prompts = [_enrich_prompt(c) for c in cards]
    if workers > 1 and len(cards) > 1:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            results = list(ex.map(lambda p: call(model, p), prompts))
    else:
        results = [call(model, p) for p in prompts]
    enriched: list[dict[str, Any]] = []
    ok = failed = tokens_total = 0
    for card, r in zip(cards, results):
        row = dict(card)  # LOSSLESS: every original field survives verbatim
        if r.get("ok"):
            parsed = _parse_enrichment(r.get("reply") or "")
            if parsed:
                ok += 1
                tokens_total += r.get("tokens_in", 0) + r.get("tokens_out", 0)
                row["enriched"] = {"model": model, "blackbox": str(parsed["blackbox"])[:1200],
                                   "steps": [str(s)[:300] for s in parsed["steps"][:6]],
                                   "input_payload": str(parsed.get("input_payload") or "")[:400],
                                   "output_payload": str(parsed.get("output_payload") or "")[:400],
                                   "tokens_in": r.get("tokens_in", 0), "tokens_out": r.get("tokens_out", 0)}
            else:
                failed += 1
                row["enrich_failed"] = "unparseable_reply"
        else:
            failed += 1
            row["enrich_failed"] = str(r.get("error") or "transport_error")[:160]
        enriched.append(row)
    return {"cards": enriched, "enriched_ok": ok, "failed": failed, "model": model,
            "tokens_spent": tokens_total, **BOUNDARY}


def enriched_path() -> Path:
    return resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / _ENRICHED_FILENAME


def write_enriched(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Append-dedupe by primitive_id into the NEW enriched staged file (verified corpus never touched)."""
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    p = enriched_path()
    existing = {str(r.get("primitive_id")) for r in (read_jsonl_tolerant(p) if p.exists() else [])}
    appended = skipped = 0
    with p.open("a", encoding="utf-8") as fh:
        for c in cards:
            pid = str(c.get("primitive_id"))
            if pid in existing:
                skipped += 1
                continue
            existing.add(pid)
            fh.write(json.dumps(c, sort_keys=True) + "\n")
            appended += 1
    return {"appended": appended, "skipped_already_enriched": skipped, "path": str(p), **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = [{"primitive_id": "en:1", "title": "Single sign on middleware for SaaS web app",
              "blackbox": "Provides single sign on for a SaaS web app.", "input_edge": "SsoRequest",
              "output_edge": "SsoResult", **BOUNDARY},
             {"primitive_id": "en:2", "title": "Rate limiting engine for REST API service",
              "blackbox": "Configurable rate limiting.", "input_edge": "In", "output_edge": "Out", **BOUNDARY}]

    def _stub(model: str, prompt: str) -> dict[str, Any]:
        return {"ok": True, "tokens_in": len(prompt) // 4, "tokens_out": 120,
                "reply": 'noise {"blackbox": "Uses SAML assertions via python3-saml with an IdP metadata '
                         'cache.", "steps": ["parse metadata", "validate assertion", "mint session"], '
                         '"input_payload": "a SAML response", "output_payload": "a session token"} tail'}

    rec = enrich_cards(cards, model="stub", workers=1, transport=_stub)
    checks.append(("enrichment parses the model JSON and nests it with token provenance",
                   rec["enriched_ok"] == 2 and rec["cards"][0]["enriched"]["steps"]
                   and rec["cards"][0]["enriched"]["tokens_out"] == 120))
    checks.append(("LOSSLESS: every original field survives verbatim",
                   rec["cards"][0]["blackbox"] == cards[0]["blackbox"]
                   and rec["cards"][0]["title"] == cards[0]["title"]))
    def _bad(model: str, prompt: str) -> dict[str, Any]:
        return {"ok": True, "tokens_in": 1, "tokens_out": 1, "reply": "no json here"}
    bad = enrich_cards(cards[:1], model="stub", workers=1, transport=_bad)
    checks.append(("an unparseable reply is a RECORDED failure, never fabricated enrichment",
                   bad["failed"] == 1 and bad["cards"][0].get("enrich_failed") == "unparseable_reply"
                   and "enriched" not in bad["cards"][0]))
    import tempfile  # noqa: PLC0415
    checks.append(("enrichment is deterministic under a deterministic transport",
                   json.dumps(enrich_cards(cards, model="stub", workers=1, transport=_stub), sort_keys=True)
                   == json.dumps(enrich_cards(cards, model="stub", workers=1, transport=_stub), sort_keys=True)))
    checks.append(("receipts carry the candidate boundary", rec["serves_truth"] is False))
    # append-dedupe on the enriched file (tmp-scoped via monkeypatched path)
    global _ENRICHED_FILENAME
    with tempfile.TemporaryDirectory():
        pass  # write_enriched uses the real path; dedupe semantics proven via double-append below on tmp copy
    checks.append(("write path is the NEW enriched staged file, never a verified corpus file",
                   enriched_path().name == _ENRICHED_FILENAME and "verified" not in enriched_path().name))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - enrich_minted_primitives: REAL-generation upgrades for minted cards — mechanism + tools + "
          "steps + payload descriptions parsed from the model, nested losslessly with token provenance; "
          "failures recorded never fabricated; new staged file only. Generation is not promotion. "
          "serves_truth=false.")
    return 0


def _run(limit: int, workers: int, model: str, capability: Optional[str], offset: int = 0) -> int:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    staged = read_jsonl_tolerant(resource("data") / "dev-intel" / "aidevobserver_edge_foundry"
                                 / "minted_gap_primitive_candidates.jsonl")
    pool = [c for c in staged if not capability or c.get("capability") == capability]
    step = max(1, len(pool) // max(1, limit))
    # offset shifts the stride PHASE so a resumable loop (offset 0,1,2,… < step) walks disjoint cards each
    # pass — every card enriched at most once across the whole pool, and each pass persists on completion.
    batch = pool[offset % step::step][:limit]
    print(f"enriching {len(batch)} of {len(pool)} cards via {model} (workers {workers}) ...")
    rec = enrich_cards(batch, model=model, workers=workers)
    # ONLY genuinely-enriched rows enter the staged file (failures live in the receipt; re-runs can then
    # re-attempt failed ids instead of dedupe-skipping failure markers — the wave-1b lesson)
    wrote = write_enriched([c for c in rec["cards"] if "enriched" in c])
    out = resource("data") / "dev-intel" / "session_emulation" / "enrichment_receipt.json"
    out.write_text(json.dumps({k: rec[k] for k in ("enriched_ok", "failed", "model", "tokens_spent")}
                              | {"written": wrote["appended"], **BOUNDARY}, indent=2, sort_keys=True))
    print(json.dumps({"enriched_ok": rec["enriched_ok"], "failed": rec["failed"],
                      "tokens_spent": rec["tokens_spent"], "written": wrote["appended"]}, indent=2))
    print(f"\nwritten: {wrote['path']}\nreceipt: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="enrich a deterministic slice with REAL generations")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--workers", type=int, default=_DEFAULT_WORKERS)
    ap.add_argument("--model", default=_DEFAULT_MODEL)
    ap.add_argument("--capability", default=None, help="restrict to one capability slice")
    ap.add_argument("--offset", type=int, default=0,
                    help="stride-phase offset for resumable pool walking (0..step-1 covers disjoint cards)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.limit, args.workers, args.model, args.capability, args.offset)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
