#!/usr/bin/env python3
"""scripts.real_session_prompt_mining — REAL-WORLD PROOF: this machine holds thousands of actual Claude Code
session transcripts (~/.claude/projects/<project>/*.jsonl). This module mines the GENUINE developer prompts
out of them (excluding tool results, command output, injected reminders, pastes, and one-word acks), runs
them against the primitive corpus, and reports where the system already serves real usage and where it needs
MORE PRIMITIVES / smarter pipelines — grounded in what this machine's developer actually asked for, not in
synthetic templates.

PRIVACY BY CONSTRUCTION: mined prompt TEXTS are written only to a GITIGNORED dist/ file; the committed
receipt carries AGGREGATES ONLY (counts, reach rates, score distributions, query-class and facet-cluster
histograms) — the self-test asserts no raw prompt text can appear in the receipt. Unlabelled real prompts
mean REACH metrics (score floors), honestly labelled — relevance judgments stay roadmap #2.

    PYTHONPATH=. python3 scripts/real_session_prompt_mining.py --self-test
    PYTHONPATH=. python3 scripts/real_session_prompt_mining.py --mine [--max-files 2000]
    PYTHONPATH=. python3 scripts/real_session_prompt_mining.py --coverage [--max-prompts 4000]
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
from typing import Any, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_DEFAULT_PROJECTS_DIR = Path(os.path.expanduser("~/.claude/projects"))
_TAIL_BYTES = 262144          # per-file byte-bounded tail (a 160MB log costs the same as 256KB)
_MIN_PROMPT_CHARS = 15        # drop bare acks ("yes", "ok", "continue")
_MAX_PROMPT_CHARS = 2000      # drop pasted documents/handoffs (they are not ASKS)
#: cosine floors for "the corpus has something semantically near" (reach, not gold) — PER EMBED SPACE,
#: because absolute cosines are not comparable across spaces (tokens-proxy related pairs sit ~0.3+; static
#: model2vec related pairs sit lower in the 1-card limit but 0.35+ at 10^5-corpus top-1). Calibrated knobs,
#: labelled in every receipt.
_SEMANTIC_REACH_FLOORS: dict[str, float] = {"tokens": 0.30, "model2vec": 0.35, "ollama": 0.35}
_MINED_DIRNAME = "real-session-prompts"   # under dist/ — GITIGNORED; raw prompts never enter the repo
#: markers of injected/non-ask user lines (harness artifacts, not developer prompts)
_EXCLUDE_MARKERS: tuple[str, ...] = ("<local-command-stdout>", "<command-name>", "<system-reminder",
                                     "task-notification", "[Request interrupted", "tool_use_error",
                                     "Caveat: The messages below")


def _texts_of_user_line(rec: dict[str, Any]) -> list[str]:
    """The genuine text content of one transcript 'user' line — str content or text blocks; tool_result
    blocks and harness artifacts are excluded."""
    if rec.get("type") != "user":
        return []
    content = (rec.get("message") or {}).get("content")
    texts: list[str] = []
    if isinstance(content, str):
        texts.append(content)
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(str(block.get("text") or ""))
    out = []
    for t in texts:
        t = t.strip()
        if not (_MIN_PROMPT_CHARS <= len(t) <= _MAX_PROMPT_CHARS):
            continue
        if any(m in t for m in _EXCLUDE_MARKERS):
            continue
        out.append(t)
    return out


def mine_prompts(projects_dir: Path = _DEFAULT_PROJECTS_DIR, *, max_files: int = 2000,
                 tail_bytes: int = _TAIL_BYTES) -> dict[str, Any]:
    """Stream the real session files (deterministic path order, byte-bounded tails) and extract deduped
    genuine developer prompts. Returns {prompts, files_scanned, lines_seen, excluded}."""
    files = sorted(projects_dir.glob("*/*.jsonl"))[:max_files]
    seen: set = set()
    prompts: list[str] = []
    lines_seen = excluded = 0
    for f in files:
        try:
            with f.open("rb") as fh:
                fh.seek(0, 2)
                size = fh.tell()
                fh.seek(max(0, size - tail_bytes))
                blob = fh.read().decode("utf-8", errors="replace")
        except OSError:
            continue
        for line in blob.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            lines_seen += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            for text in _texts_of_user_line(rec):
                key = " ".join(text.lower().split())
                if key in seen:
                    excluded += 1
                    continue
                seen.add(key)
                prompts.append(text)
    return {"prompts": prompts, "files_scanned": len(files), "lines_seen": lines_seen,
            "deduped_or_excluded": excluded, **BOUNDARY}


def mined_path() -> Path:
    return resource("dist") / _MINED_DIRNAME / "prompts.jsonl"


def write_mined(prompts: list[str]) -> Path:
    p = mined_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for t in prompts:
            fh.write(json.dumps({"prompt": t, **BOUNDARY}, sort_keys=True) + "\n")
    return p


def coverage_of_real_prompts(cards: list[dict[str, Any]], prompts: list[str], *, k: int = 5,
                             embed_path: Optional[str] = None) -> dict[str, Any]:
    """REACH of the corpus over real prompts (unlabelled — floors, not gold): semantic reach (stored-lane
    top-1 cosine >= floor), lexical returned-anything rate, per-prompt query-class histogram, and the GAP
    CLUSTERS: low-reach prompts grouped by their extracted operation/datatype facets (counts only — no raw
    prompt text ever enters the receipt)."""
    from scripts import capability_embedding as _emb  # noqa: PLC0415
    from scripts import path_router_zoo as _router  # noqa: PLC0415  REUSE: the query classifier
    from scripts import primitive_descriptor as _desc  # noqa: PLC0415  REUSE: facets
    from scripts.build_primitive_search_index import build_index, search_with_stats  # noqa: PLC0415
    index = build_index(cards)
    path = embed_path or _emb.real_text_path()
    floor = _SEMANTIC_REACH_FLOORS.get(path, max(_SEMANTIC_REACH_FLOORS.values()))
    semantic_hits = lexical_hits = 0
    scores: list[float] = []
    class_hist: dict[str, int] = {}
    gap_facets: dict[str, int] = {}
    for q in prompts:
        cls = _router.query_class(q)
        class_hist[cls] = class_hist.get(cls, 0) + 1
        hits = _emb.intent_query(q, cards, k=1, path=path)
        top = float(hits[0]["score"]) if hits else 0.0
        scores.append(top)
        if top >= floor:
            semantic_hits += 1
        else:  # a GAP: name it by facets, never by text
            qc = {"title": q, "blackbox": q, "input_edge": "", "output_edge": ""}
            for facet in sorted(_desc.operations(qc) | _desc.datatypes(qc)) or ["(no_facet)"]:
                gap_facets[facet] = gap_facets.get(facet, 0) + 1
        lex, _stats = search_with_stats(q, k, index)
        if lex:
            lexical_hits += 1
    n = len(prompts) or 1
    scores.sort()
    return {"record_type": "real_session_prompt_coverage", "prompts": len(prompts),
            "corpus_cards": len(cards), "k": k, "embed_path": path,
            "semantic_reach_rate": round(semantic_hits / n, 4),
            "semantic_reach_floor": floor,
            "lexical_returned_rate": round(lexical_hits / n, 4),
            "top1_score_quartiles": [round(scores[int(len(scores) * q)] if scores else 0.0, 4)
                                     for q in (0.25, 0.5, 0.75)] if scores else [],
            "query_class_histogram": dict(sorted(class_hist.items(), key=lambda kv: -kv[1])),
            "gap_facet_clusters": dict(sorted(gap_facets.items(), key=lambda kv: -kv[1])[:15]),
            "note": "REAL developer prompts mined from this machine's own sessions. Unlabelled -> REACH "
                    "metrics (floors), not relevance gold. Gap clusters are FACET COUNTS of low-reach "
                    "prompts — the 'we need more primitives HERE' list — and no raw prompt text ever "
                    "appears in this receipt (privacy by construction; texts live in gitignored dist/).",
            **BOUNDARY}


# ── the AGENT lane (owner directive: "include agent transcripts and activities and actions") ─────────────────
def _agent_files(projects_dir: Path, *, max_files: int) -> list[Path]:
    """The NESTED transcripts (subagents/workflows) — agent activity, distinct from human session files."""
    return sorted(p for p in projects_dir.rglob("*.jsonl")
                  if len(p.relative_to(projects_dir).parts) > 2)[:max_files]


def mine_agent_activity(projects_dir: Path = _DEFAULT_PROJECTS_DIR, *, max_files: int = 2700,
                        tail_bytes: int = _TAIL_BYTES) -> dict[str, Any]:
    """Mine the AGENT transcripts: (a) the task PROMPTS given to agents (real workload shapes), and (b) the
    ACTIONS agents actually performed — tool_use blocks in assistant lines — as a tool histogram + the
    action BIGRAMS (which tool follows which). Deterministic; byte-bounded tails; texts stay off-receipt."""
    files = _agent_files(projects_dir, max_files=max_files)
    seen: set = set()
    agent_prompts: list[str] = []
    tool_hist: dict[str, int] = {}
    bigrams: dict[str, int] = {}
    lines_seen = 0
    for f in files:
        prev_tool: Optional[str] = None
        try:
            with f.open("rb") as fh:
                fh.seek(0, 2)
                size = fh.tell()
                fh.seek(max(0, size - tail_bytes))
                blob = fh.read().decode("utf-8", errors="replace")
        except OSError:
            continue
        for line in blob.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            lines_seen += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            for text in _texts_of_user_line(rec):
                key = " ".join(text.lower().split())
                if key not in seen:
                    seen.add(key)
                    agent_prompts.append(text)
            if rec.get("type") == "assistant":
                content = (rec.get("message") or {}).get("content")
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            name = str(block.get("name") or "unknown")
                            tool_hist[name] = tool_hist.get(name, 0) + 1
                            if prev_tool is not None:
                                bg = f"{prev_tool} -> {name}"
                                bigrams[bg] = bigrams.get(bg, 0) + 1
                            prev_tool = name
    return {"agent_prompts": agent_prompts, "files_scanned": len(files), "lines_seen": lines_seen,
            "tool_action_histogram": dict(sorted(tool_hist.items(), key=lambda kv: -kv[1])),
            "top_action_bigrams": dict(sorted(bigrams.items(), key=lambda kv: -kv[1])[:20]),
            "distinct_tools": len(tool_hist), "total_actions": sum(tool_hist.values()), **BOUNDARY}


def agent_mined_path() -> Path:
    return resource("dist") / _MINED_DIRNAME / "agent_prompts.jsonl"


def agent_activity_receipt(activity: dict[str, Any], coverage: Optional[dict[str, Any]]) -> dict[str, Any]:
    """The committed AGENT receipt: activity aggregates + (optional) reach coverage of the agent prompts —
    no raw prompt text (same privacy construction as the human lane)."""
    return {"record_type": "real_agent_activity", "files_scanned": activity["files_scanned"],
            "agent_prompts_mined": len(activity["agent_prompts"]), "lines_seen": activity["lines_seen"],
            "total_actions": activity["total_actions"], "distinct_tools": activity["distinct_tools"],
            "tool_action_histogram": dict(list(activity["tool_action_histogram"].items())[:20]),
            "top_action_bigrams": activity["top_action_bigrams"],
            "agent_prompt_coverage": ({k: coverage[k] for k in
                                       ("prompts", "semantic_reach_rate", "semantic_reach_floor",
                                        "lexical_returned_rate", "query_class_histogram",
                                        "gap_facet_clusters")} if coverage else None),
            "note": "AGENT transcripts (subagent/workflow lanes): the prompts agents were given + the tool "
                    "ACTIONS they performed (histogram + bigram sequences) — real machine-side workload "
                    "demand. Raw texts live in gitignored dist/ only.", **BOUNDARY}


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    sentinel = "please dedupe the customer records exported from postgres"
    with tempfile.TemporaryDirectory() as d:
        proj = Path(d) / "proj-a"
        proj.mkdir(parents=True)
        lines = [
            {"type": "user", "message": {"role": "user", "content": sentinel}},
            {"type": "user", "message": {"role": "user", "content": sentinel}},  # dup -> dropped
            {"type": "user", "message": {"role": "user",
                                         "content": [{"type": "text", "text": "build an ocr pipeline for scanned invoices please"}]}},
            {"type": "user", "message": {"role": "user",
                                         "content": [{"type": "tool_result", "content": "12345 rows"}]}},
            {"type": "user", "message": {"role": "user", "content": "ok"}},  # too short
            {"type": "user", "message": {"role": "user", "content": "<local-command-stdout>noise</local-command-stdout>"}},
            {"type": "assistant", "message": {"role": "assistant", "content": "sure thing"}},
            {"type": "user", "message": {"role": "user", "content": "x" * 3000}},  # paste -> dropped
        ]
        with (proj / "s1.jsonl").open("w") as fh:
            for r in lines:
                fh.write(json.dumps(r) + "\n")
        mined = mine_prompts(Path(d), max_files=10)
        checks.append(("only GENUINE asks are mined (dups, tool results, acks, stdout, pastes all excluded)",
                       mined["prompts"] == [sentinel, "build an ocr pipeline for scanned invoices please"]))
        checks.append(("mining is deterministic (same files -> same prompts)",
                       mine_prompts(Path(d), max_files=10)["prompts"] == mined["prompts"]))
    cards = [{"primitive_id": "r:dedup", "title": "Deduplicate records",
              "blackbox": "Remove duplicate customer records by clustering near identical rows.",
              "input_edge": "Batch", "output_edge": "Deduped", **BOUNDARY}]
    served_q = "remove duplicate customer records from the export"  # comfortably above the tokens floor
    rec = coverage_of_real_prompts(cards, [served_q, "zorple the quantum flux banana"], k=2,
                                   embed_path="tokens")  # hermetic: the calibrated proxy space
    checks.append(("reach: a served prompt clears the floor; an unservable one lands in a gap facet cluster",
                   rec["prompts"] == 2 and 0 < rec["semantic_reach_rate"] <= 1.0
                   and sum(rec["gap_facet_clusters"].values()) >= 1))
    checks.append(("query classes are histogrammed via the live router classifier",
                   sum(rec["query_class_histogram"].values()) == 2))
    checks.append(("PRIVACY GATE: no raw prompt text ever appears in the receipt",
                   sentinel not in json.dumps(rec) and "banana" not in json.dumps(rec)))
    checks.append(("coverage receipt is deterministic (byte-identical twice)",
                   json.dumps(coverage_of_real_prompts(cards, [sentinel], k=2, embed_path="tokens"),
                              sort_keys=True)
                   == json.dumps(coverage_of_real_prompts(cards, [sentinel], k=2, embed_path="tokens"),
                                 sort_keys=True)))
    checks.append(("receipts are candidate/serves_truth=false", rec["serves_truth"] is False))

    # the AGENT lane: nested transcripts yield task prompts + tool ACTION histogram + bigram sequences
    with tempfile.TemporaryDirectory() as d:
        deep = Path(d) / "proj" / "subagents" / "workflows"
        deep.mkdir(parents=True)
        agent_lines = [
            {"type": "user", "message": {"role": "user", "content": "review the auth module for injection bugs"}},
            {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "Read", "input": {"file_path": "a.py"}},
                {"type": "tool_use", "name": "Grep", "input": {"pattern": "sql"}}]}},
            {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "name": "Read", "input": {"file_path": "b.py"}}]}},
        ]
        with (deep / "agent-1.jsonl").open("w") as fh:
            for r in agent_lines:
                fh.write(json.dumps(r) + "\n")
        act = mine_agent_activity(Path(d), max_files=10)
        checks.append(("agent lane mines task prompts + tool actions + bigram sequences (deterministic)",
                       act["agent_prompts"] == ["review the auth module for injection bugs"]
                       and act["tool_action_histogram"] == {"Read": 2, "Grep": 1}
                       and act["top_action_bigrams"] == {"Read -> Grep": 1, "Grep -> Read": 1}
                       and mine_agent_activity(Path(d), max_files=10) == act))
        arec = agent_activity_receipt(act, None)
        checks.append(("the agent receipt carries aggregates only (privacy gate holds for the agent lane too)",
                       "injection bugs" not in json.dumps(arec) and arec["total_actions"] == 3
                       and arec["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - real_session_prompt_mining: genuine developer prompts mined from real Claude Code "
          "transcripts (tool results / acks / stdout / pastes / dups excluded; byte-bounded tails), REACH "
          "coverage with floors + query-class histogram + facet-named gap clusters, and the privacy gate "
          "proves no raw prompt text can enter a committed receipt. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mine", action="store_true", help="mine real prompts -> gitignored dist/ file")
    ap.add_argument("--coverage", action="store_true", help="REACH of the corpus over the mined prompts")
    ap.add_argument("--agents", action="store_true",
                    help="mine AGENT transcripts (prompts + tool actions) + coverage of agent prompts")
    ap.add_argument("--max-files", type=int, default=2000)
    ap.add_argument("--max-prompts", type=int, default=4000)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.mine:
        mined = mine_prompts(max_files=args.max_files)
        p = write_mined(mined["prompts"])
        print(json.dumps({kk: mined[kk] for kk in ("files_scanned", "lines_seen", "deduped_or_excluded")},
                         indent=2))
        print(f"mined {len(mined['prompts'])} genuine prompts -> {p} (gitignored)")
        return 0
    if args.agents:
        from scripts import path_graph_bench as _bench  # noqa: PLC0415
        from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415  (parity with --coverage)
        activity = mine_agent_activity(max_files=args.max_files)
        p = agent_mined_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            for t in activity["agent_prompts"]:
                fh.write(json.dumps({"prompt": t, **BOUNDARY}, sort_keys=True) + "\n")
        cards = _bench._load_scale_corpus(None)  # noqa: SLF001
        step = max(1, len(activity["agent_prompts"]) // max(1, args.max_prompts))
        sample = activity["agent_prompts"][::step][:args.max_prompts]
        print(f"agent lane: {activity['files_scanned']} files, {len(activity['agent_prompts'])} prompts, "
              f"{activity['total_actions']} actions; coverage over {len(sample)} prompts x {len(cards)} cards ...")
        cov = coverage_of_real_prompts(cards, sample) if sample else None
        rec = agent_activity_receipt(activity, cov)
        out = resource("data") / "dev-intel" / "session_emulation" / "real_agent_activity_receipt.json"
        out.write_text(json.dumps(rec, indent=2, sort_keys=True))
        print(json.dumps({kk: rec[kk] for kk in ("agent_prompts_mined", "total_actions", "distinct_tools",
                                                 "tool_action_histogram")}, indent=2))
        print(f"\nwritten: {out} (texts -> {p}, gitignored)")
        return 0
    if args.coverage:
        from scripts import path_graph_bench as _bench  # noqa: PLC0415
        from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
        rows = read_jsonl_tolerant(mined_path())
        prompts = [r["prompt"] for r in rows if r.get("prompt")]
        if not prompts:
            print(f"no mined prompts at {mined_path()} — run --mine first")
            return 1
        step = max(1, len(prompts) // max(1, args.max_prompts))
        sample = prompts[::step][:args.max_prompts]
        cards = _bench._load_scale_corpus(None)  # noqa: SLF001
        print(f"real-prompt coverage: {len(sample)} of {len(prompts)} mined prompts over {len(cards)} cards ...")
        rec = coverage_of_real_prompts(cards, sample)
        out = resource("data") / "dev-intel" / "session_emulation" / "real_session_prompt_receipt.json"
        out.write_text(json.dumps(rec, indent=2, sort_keys=True))
        print(json.dumps({kk: rec[kk] for kk in ("prompts", "semantic_reach_rate", "lexical_returned_rate",
                                                 "top1_score_quartiles", "gap_facet_clusters")}, indent=2))
        print(f"\nwritten: {out}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
