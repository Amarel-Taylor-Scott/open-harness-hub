#!/usr/bin/env python3
"""Harvest prompt-engineering-heavy GitHub repos into a spreadsheet (the aggregator).

Builds OHH's own corpus of REAL, verified repos — prompt packs, prompt-optimizer
libraries, structured-generation tools, agentic harnesses, eval/guardrail
frameworks, agent-config standards — by querying the GitHub Search API across a
prompt-engineering query taxonomy. No fabrication: every row is a repo the API
returned, with stars + license + topics as reported by GitHub.

Honest by design (per docs/concepts/capability-valleys.md + the governance moat):
  • license gate — permissive => ingest-candidate; NOASSERTION/none/copyleft => ideate/review.
  • SAFETY gate — repos that look like jailbreak / prompt-injection PAYLOAD collections
    are tagged reference-only · do-not-ingest (they'd poison the catalog).
  • camp — Camp-1 "template/prompt-pack" (pattern value, low catalog lift) vs the
    durable "engineering" families (optimizer / structured-gen / harness / eval / guardrail).

stdlib only. Works unauthenticated (10 searches/min) or with GH_TOKEN/GITHUB_TOKEN
(30/min, far faster to the 2000 target). Throttles on the live rate-limit headers.

    python3 -m scripts.acquisition.github_repo_harvester --target 2000
    python3 -m scripts.acquisition.github_repo_harvester --self-test   # offline
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "repo-catalog"
API = "https://api.github.com/search/repositories"

# Query taxonomy — topics + keyword qualifiers. Each returns up to 1000 results;
# breadth across many queries + dedupe is how we pass the per-query cap toward 2000.
TOPIC_QUERIES = [
    "topic:prompt-engineering", "topic:prompt", "topic:prompts", "topic:prompt-tuning",
    "topic:prompt-optimization", "topic:dspy", "topic:structured-generation", "topic:function-calling",
    "topic:json-schema", "topic:guardrails", "topic:llm-evaluation", "topic:llmops", "topic:llm-agents",
    "topic:ai-agents", "topic:agent", "topic:agents", "topic:rag", "topic:retrieval-augmented-generation",
    "topic:system-prompt", "topic:chatgpt-prompts", "topic:awesome-chatgpt-prompts", "topic:llm",
    "topic:large-language-models", "topic:prompt-injection", "topic:jailbreak", "topic:langchain",
    "topic:ollama", "topic:fine-tuning", "topic:in-context-learning", "topic:few-shot-learning",
]
KEYWORD_QUERIES = [
    '"prompt library" in:name,description', '"prompt pack" in:name,description',
    '"prompt templates" in:name,description', '"system prompts" in:name,description',
    '"llm harness" in:name,description', '"agent framework" in:name,description',
    '"prompt optimization" in:name,description', '"structured output" llm in:name,description',
    '"constrained decoding" in:name,description', '"awesome prompts" in:name,description',
    '"prompt engineering" in:name,description', '"system prompt" leaked in:name,description',
]

PERMISSIVE = {"MIT", "APACHE-2.0", "BSD-3-CLAUSE", "BSD-2-CLAUSE", "ISC", "MPL-2.0", "UNLICENSE", "CC0-1.0", "0BSD"}
COPYLEFT = {"GPL-2.0", "GPL-3.0", "AGPL-3.0", "LGPL-3.0", "LGPL-2.1"}
INJECTION_SIGNALS = ("jailbreak", "prompt injection", "prompt-injection", "dan ", "do anything now",
                     "uncensored", "bypass", "exploit prompt")

# family -> (camp, one-line lift hypothesis to confirm against a benchmark)
FAMILY = {
    "optimizer": ("engineering", "Auto-improves+benchmarks a component's prompt/weights (DSPy/GEPA/TextGrad) — measurable lift on a named eval."),
    "structured_generation": ("engineering", "Schema-aligned/constrained decoding makes output parse-reliable — deterministic_guarantee lift over free-form."),
    "harness": ("engineering", "Orchestration patterns (tool registry, approval gates, memory, rollback) — reusable harness lift, not a prompt."),
    "eval": ("engineering", "Benchmark/judge rig to MEASURE pipeline_score - bare_model_score — the gate itself."),
    "guardrail": ("engineering", "Validation/moderation/injection-hardening gate — a 'this component is injection-hardened' lift feature."),
    "rag": ("engineering", "Retrieval/grounding scaffold — grounded-citation lift where parametric knowledge is thin."),
    "agent_config": ("engineering", "Agent-config standard (AGENTS.md/CLAUDE.md/SKILL.md) — a structure to emit+consume, progressive disclosure."),
    "prompt_pack": ("template", "Prompt-template collection — Camp-1 pattern taxonomy; near-zero catalog lift, mine the structure not the text."),
    "system_prompt_collection": ("template", "Real production system-prompt structures — template/pattern reference (licensing-gray, ideation only)."),
    "general_llm": ("template", "General LLM/prompt repo — triage for which durable family (if any) it belongs to."),
}


def _classify(name: str, desc: str, topics: list[str]) -> str:
    blob = (name + " " + desc + " " + " ".join(topics)).lower()
    def has(*ks: str) -> bool:
        return any(k in blob for k in ks)
    if has("dspy", "textgrad", "gepa", "prompt-optim", "prompt optimization", "auto-prompt", "autoprompt", "ape "):
        return "optimizer"
    if has("outlines", "instructor", "guidance", "jsonformer", "lm-format-enforcer", "sglang", "lmql",
           "structured output", "structured-generation", "constrained decoding", "json schema", "function calling"):
        return "structured_generation"
    if has("agents.md", "agent.md", "claude.md", "cursorrules", "skill.md", "agent-config"):
        return "agent_config"
    if has("guardrail", "nemo-guardrails", "moderation", "injection", "jailbreak", "safety filter"):
        return "guardrail"
    if has("promptfoo", "deepeval", "ragas", "lm-eval", "llm eval", "evaluation", "benchmark", "leaderboard"):
        return "eval"
    if has("crewai", "autogen", "ag2", "smolagents", "aider", "openhands", "swe-agent", "agent framework",
           "multi-agent", "orchestrat", "harness", "langgraph"):
        return "harness"
    if has("retrieval-augmented", "rag", "retriever", "vector", "embedding search"):
        return "rag"
    if has("system-prompt", "system prompts", "leaked", "models-of-ai-tools"):
        return "system_prompt_collection"
    if has("awesome", "prompt library", "prompt pack", "prompt templates", "prompts", "chatgpt-prompts", "prompt-engineering"):
        return "prompt_pack"
    return "general_llm"


def _gate(license_id: str, name: str, desc: str, topics: list[str]) -> str:
    blob = (name + " " + desc + " " + " ".join(topics)).lower()
    if any(s in blob for s in INJECTION_SIGNALS):
        return "reference-only · do-not-ingest (injection/jailbreak)"
    lid = (license_id or "").upper()
    if lid in PERMISSIVE:
        return "ingest-candidate"
    if lid in COPYLEFT:
        return "ideate · copyleft-review"
    return "ideate · license-review"


def normalize(item: dict[str, Any]) -> dict[str, Any]:
    topics = item.get("topics") or []
    name = item.get("full_name", "")
    desc = (item.get("description") or "").replace("\n", " ").strip()
    lic = ((item.get("license") or {}).get("spdx_id")) or ""
    family = _classify(name, desc, topics)
    camp, lift = FAMILY[family]
    return {
        "repo_full_name": name,
        "url": item.get("html_url", ""),
        "family": family,
        "camp": camp,
        "gate": _gate(lic, name, desc, topics),
        "stars": item.get("stargazers_count", 0),
        "language": item.get("language") or "",
        "license": lic or "NOASSERTION",
        "topics": ";".join(topics[:10]),
        "description": desc[:300],
        "lift_hypothesis": lift,
        "source": item.get("_source", "github-api"),
        "harvested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


CSV_FIELDS = ["repo_full_name", "url", "family", "camp", "gate", "stars", "language",
              "license", "topics", "description", "lift_hypothesis", "source", "harvested_at"]


def _headers() -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "ohh-repo-harvester"}
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def _get(query: str, page: int) -> tuple[list[dict], dict]:
    qs = urllib.parse.urlencode({"q": query, "sort": "stars", "order": "desc", "per_page": 100, "page": page})
    req = urllib.request.Request(f"{API}?{qs}", headers=_headers())
    with urllib.request.urlopen(req, timeout=30) as resp:
        meta = {"remaining": int(resp.headers.get("X-RateLimit-Remaining", "1")),
                "reset": int(resp.headers.get("X-RateLimit-Reset", "0"))}
        return json.loads(resp.read().decode("utf-8")).get("items", []), meta


def harvest(*, target: int, max_pages: int, queries: list[str]) -> dict[str, Any]:
    rows: dict[str, dict] = {}
    calls = 0
    for query in queries:
        if len(rows) >= target:
            break
        for page in range(1, max_pages + 1):
            try:
                items, meta = _get(query, page)
            except urllib.error.HTTPError as e:
                if e.code in (403, 429):  # rate/secondary limit — back off and retry once
                    time.sleep(60)
                    try:
                        items, meta = _get(query, page)
                    except Exception:
                        break
                else:
                    break
            except Exception:
                break
            calls += 1
            if not items:
                break
            for it in items:
                row = normalize(it)
                rows.setdefault(row["repo_full_name"], row)
            # throttle on the live limit (unauth search = 10/min)
            if meta["remaining"] <= 1:
                wait = max(2, meta["reset"] - int(time.time()) + 1)
                time.sleep(min(wait, 75))
            else:
                time.sleep(1)
            if len(rows) >= target:
                break
    return {"rows": list(rows.values()), "calls": calls}


def _write(rows: list[dict], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda r: r["stars"], reverse=True)
    with (out_dir / "prompt-engineering-repos.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CSV_FIELDS})
    (out_dir / "prompt-engineering-repos.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""), encoding="utf-8")

    def _tally(key: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in rows:
            out[r[key]] = out.get(r[key], 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    summary = {"total_repos": len(rows), "by_family": _tally("family"),
               "by_camp": _tally("camp"), "ingest_candidates": sum(1 for r in rows if r["gate"] == "ingest-candidate"),
               "do_not_ingest": sum(1 for r in rows if r["gate"].startswith("reference-only")),
               "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _self_test() -> int:
    fixture = [
        {"full_name": "stanfordnlp/dspy", "html_url": "x", "description": "programming not prompting LMs",
         "topics": ["dspy", "prompt-optimization"], "license": {"spdx_id": "MIT"}, "stargazers_count": 20000, "language": "Python"},
        {"full_name": "f/awesome-chatgpt-prompts", "html_url": "x", "description": "prompt library",
         "topics": ["chatgpt-prompts"], "license": {"spdx_id": "CC0-1.0"}, "stargazers_count": 100000, "language": None},
        {"full_name": "evil/jailbreak-prompts", "html_url": "x", "description": "DAN jailbreak prompt collection",
         "topics": ["jailbreak"], "license": {"spdx_id": "NOASSERTION"}, "stargazers_count": 500, "language": None},
    ]
    rows = [normalize({**it, "_source": "github-api"}) for it in fixture]
    by_fam = {r["repo_full_name"]: r["family"] for r in rows}
    assert by_fam["stanfordnlp/dspy"] == "optimizer", by_fam
    assert rows[1]["camp"] == "template" and rows[1]["gate"] == "ingest-candidate"
    assert rows[2]["gate"].startswith("reference-only"), rows[2]  # jailbreak excluded from ingest
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        s = _write(rows, Path(tmp))
        assert s["total_repos"] == 3 and s["do_not_ingest"] == 1
        print(json.dumps(s, indent=2))
    return 0


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Harvest prompt-engineering GitHub repos into a spreadsheet.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--target", type=int, default=2000)
    p.add_argument("--max-pages", type=int, default=3, help="pages (×100) per query")
    p.add_argument("--out-dir", default=str(OUT_DIR))
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    queries = TOPIC_QUERIES + KEYWORD_QUERIES
    print(f"harvesting up to {args.target} repos across {len(queries)} queries "
          f"({'token' if (os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')) else 'UNAUTH 10/min'})…")
    result = harvest(target=args.target, max_pages=args.max_pages, queries=queries)
    summary = _write(result["rows"], Path(args.out_dir))
    summary["api_calls"] = result["calls"]
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
