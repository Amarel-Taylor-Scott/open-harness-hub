#!/usr/bin/env python3
"""Mine Meta Kaggle (metadata) + Meta Kaggle Code (kernel source) for
LLM-pipeline patterns at scale.

Pipeline:
  1. Load Competitions.csv → filter to LLM-relevant.
  2. Load KernelVersionCompetitionSources.csv → KernelVersionIds per comp.
  3. Stream KernelVersions.csv → keep only those KernelVersionIds; sort
     by TotalVotes desc; take top-N per competition.
  4. For each KernelVersionId, look up source file in Meta Kaggle Code
     tree at `{id // 1_000_000}/{(id // 1000) % 1000}/{id}.ipynb` or `.py`.
  5. Extract code cells (if .ipynb), run AST + regex detector.
  6. Aggregate: which patterns appear most often per competition + overall.

Output:
  /tmp/oh-mining/findings.json — full per-kernel detector hits.
  /tmp/oh-mining/findings-summary.md — top patterns + library usage.

Usage:
  python3 scripts/mine_meta_kaggle.py \\
      --meta-dir /tmp/meta-kaggle \\
      --code-dir /tmp/meta-kaggle-code \\
      --top-per-comp 30 \\
      --max-comps 30 \\
      --workers 8
"""
from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

csv.field_size_limit(sys.maxsize)


LLM_KEYWORDS = [
    "llm", "language model", "gemma", "chatbot", "gpt", "prompt", "lmsys",
    "detect-ai", "science exam", "misconception", "preference",
    "completion", "retrieval", "instruction", "finetuning", "rag ", "rag-",
    "generative", "arena", "reasoning", "recovery", "20-questions", "agent",
    "toxic-comment", "fine-tune", "deberta",
]


REGEX_DETECTORS: list[tuple[str, re.Pattern]] = [
    ("import_transformers",          re.compile(r"\bfrom transformers\b|\bimport transformers\b")),
    ("import_peft",                  re.compile(r"\bfrom peft\b|\bimport peft\b")),
    ("import_unsloth",               re.compile(r"\bfrom unsloth\b|\bimport unsloth\b")),
    ("import_bitsandbytes",          re.compile(r"\bbitsandbytes\b|BitsAndBytesConfig|load_in_4bit|load_in_8bit")),
    ("import_trl",                   re.compile(r"\bfrom trl\b|SFTTrainer|DPOTrainer")),
    ("import_vllm",                  re.compile(r"\bfrom vllm\b|\bimport vllm\b")),
    ("import_langchain",             re.compile(r"\bfrom langchain\b|\bimport langchain\b")),
    ("import_llama_index",           re.compile(r"\bllama_index\b|\bfrom llama\b")),
    ("import_haystack",              re.compile(r"\bfrom haystack\b")),
    ("import_dspy",                  re.compile(r"\bimport dspy\b|\bfrom dspy\b")),
    ("import_sentence_transformers", re.compile(r"sentence_transformers")),
    ("import_lightgbm",              re.compile(r"\bimport lightgbm\b|\bfrom lightgbm\b|LGBMClassifier|LGBMRegressor")),
    ("import_xgboost",               re.compile(r"\bxgboost\b|XGBClassifier|XGBRegressor")),
    ("import_sklearn_tfidf",         re.compile(r"TfidfVectorizer")),
    ("import_kerasnlp",              re.compile(r"\bkeras_nlp\b|\bkerasnlp\b")),
    ("model_load_4bit",              re.compile(r"load_in_4bit\s*=\s*True|BitsAndBytesConfig\(.*load_in_4bit")),
    ("model_load_8bit",              re.compile(r"load_in_8bit\s*=\s*True")),
    ("lora_config",                  re.compile(r"\bLoraConfig\b|get_peft_model")),
    ("sft_trainer",                  re.compile(r"\bSFTTrainer\b|\bSFTConfig\b")),
    ("dpo_trainer",                  re.compile(r"\bDPOTrainer\b|\bDPOConfig\b")),
    ("orpo_trainer",                 re.compile(r"\bORPOTrainer\b|\bORPOConfig\b")),
    ("rope_scaling",                 re.compile(r"rope_scaling|rope_theta")),
    ("max_seq_length",               re.compile(r"max_seq_length")),
    ("trust_remote_code",            re.compile(r"trust_remote_code\s*=\s*True")),
    ("generate_kwargs",              re.compile(r"\.generate\([^)]*max_new_tokens|temperature\s*=\s*\d|top_p\s*=|top_k\s*=")),
    ("chat_template",                re.compile(r"chat_template|apply_chat_template")),
    ("vector_index_faiss",           re.compile(r"\bfaiss\b|IndexFlatIP|IndexFlatL2")),
    ("vector_chroma",                re.compile(r"\bchromadb\b|chroma_client")),
    ("vector_qdrant",                re.compile(r"\bqdrant\b")),
    ("vector_weaviate",              re.compile(r"\bweaviate\b")),
    ("vector_pinecone",              re.compile(r"\bpinecone\b")),
    ("bm25",                         re.compile(r"\bBM25Okapi\b|\bBM25\b")),
    ("reranker",                     re.compile(r"CrossEncoder|rerank|BAAI/bge-reranker|cohere\.rerank")),
    ("cot_marker",                   re.compile(r"chain.of.thought|\"Let's think step by step\"|step by step")),
    ("react_marker",                 re.compile(r"Thought:|Observation:|Action:|Final Answer:")),
    ("system_prompt",                re.compile(r"system\s*[:=]\s*[\"']|\"role\"\s*:\s*\"system\"|messages\s*=\s*\[")),
    ("few_shot_examples",            re.compile(r"few[_-]shot|examples\s*=\s*\[")),
    ("function_calling",             re.compile(r"function_call|tools\s*=\s*\[|tool_calls")),
    ("self_consistency_voting",      re.compile(r"majority.vote|self.consistency")),
    ("eval_grader",                  re.compile(r"\bgrader\b|llm.judge|llm_as_judge")),
    ("synthetic_data_gen",           re.compile(r"synthetic|generate.dataset|create.synthetic|generate.augment")),
    ("ensemble_average",             re.compile(r"\bensemble\b|np\.mean\(.*\)|blend.predictions")),
    ("kfold_split",                  re.compile(r"KFold|StratifiedKFold|GroupKFold")),
    ("char_ngram",                   re.compile(r"analyzer\s*=\s*['\"]char['\"]|ngram_range\s*=\s*\((\d+),\s*\d+\)")),
    ("deberta_finetune",             re.compile(r"deberta", re.IGNORECASE)),
    ("save_lora_adapter",            re.compile(r"save_pretrained|push_to_hub")),
]


# ---- helpers ----------------------------------------------------------------

def slurp_csv(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace").replace("\x00", "")


def load_competitions(meta_dir: Path) -> dict[str, dict]:
    text = slurp_csv(meta_dir / "Competitions.csv")
    comps: dict[str, dict] = {}
    for row in csv.DictReader(io.StringIO(text)):
        slug = (row.get("Slug") or "").lower()
        title = (row.get("Title") or "").lower()
        desc = (row.get("Description") or "").lower()[:500]
        if any(k in slug or k in title or k in desc for k in LLM_KEYWORDS):
            if any(x in slug for x in ("matrix-completion", "si650")):
                continue
            comps[row["Id"]] = {
                "id": row["Id"],
                "slug": row.get("Slug"),
                "title": row.get("Title"),
                "date": (row.get("EnabledDate") or "")[:10],
            }
    return comps


def load_competition_sources(meta_dir: Path, comp_ids: set[str]) -> dict[str, set[str]]:
    """Return CompetitionId -> set[KernelVersionId]."""
    text = slurp_csv(meta_dir / "KernelVersionCompetitionSources.csv")
    out: dict[str, set[str]] = defaultdict(set)
    for row in csv.DictReader(io.StringIO(text)):
        cid = row.get("SourceCompetitionId")
        if cid in comp_ids:
            out[cid].add(row["KernelVersionId"])
    return out


def stream_kernel_versions(meta_dir: Path, target_kvids: set[str]) -> list[dict]:
    """Stream KernelVersions.csv (4.4 GB); keep only targets."""
    path = meta_dir / "KernelVersions.csv"
    kept: list[dict] = []
    # Stream by reading lines via csv module on a binary→str pipe.
    with path.open("rb") as bf:
        # Process in chunks; KernelVersions doesn't have multi-line cells usually.
        text_iter = io.TextIOWrapper(bf, encoding="utf-8", errors="replace")
        # Replace NUL on the fly via a wrapper.
        class _NoNul:
            def __init__(self, w):
                self.w = w
            def __iter__(self):
                for line in self.w:
                    yield line.replace("\x00", "")
        reader = csv.DictReader(_NoNul(text_iter))
        for row in reader:
            if row.get("Id") in target_kvids:
                kept.append({
                    "kvid": row["Id"],
                    "script_id": row.get("ScriptId"),
                    "author_id": row.get("AuthorUserId"),
                    "title": row.get("Title"),
                    "votes": int(row.get("TotalVotes") or 0),
                    "lines": int(row.get("TotalLines") or 0),
                    "internet": row.get("IsInternetEnabled") == "True",
                })
    return kept


def code_path_for_kvid(code_dir: Path, kvid: int) -> Path | None:
    """Locate the Meta Kaggle Code source file by KernelVersionId."""
    top  = kvid // 1_000_000
    mid  = (kvid // 1000) % 1000
    # Both .py and .ipynb possible; .ipynb is the common case.
    for ext in ("ipynb", "py", "R"):
        p = code_dir / f"{top:03d}" / f"{mid:03d}" / f"{kvid}.{ext}"
        if p.exists():
            return p
        # Some layouts use unpadded directories:
        p2 = code_dir / str(top) / str(mid) / f"{kvid}.{ext}"
        if p2.exists():
            return p2
    return None


def extract_code(path: Path) -> str:
    raw = path.read_text(errors="ignore")
    if path.suffix == ".ipynb":
        try:
            nb = json.loads(raw)
            return "\n".join(
                "".join(c.get("source") or "")
                for c in nb.get("cells", [])
                if c.get("cell_type") == "code"
            )
        except json.JSONDecodeError:
            return raw
    return raw


def detect(source: str) -> tuple[list[str], set[str]]:
    """Return (regex_hits, imported_modules)."""
    hits: list[str] = []
    for name, pat in REGEX_DETECTORS:
        if pat.search(source):
            hits.append(name)
    # AST-based import extraction (catches anything regex might miss in import form)
    imports: set[str] = set()
    try:
        tree = ast.parse(source, "<kernel>", "exec")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.add(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
    except SyntaxError:
        pass
    return hits, imports


def process_kernel(args: tuple[Path, dict, str]) -> dict | None:
    code_dir_str, kv, comp_slug = args
    code_dir = Path(code_dir_str)
    kvid = int(kv["kvid"])
    path = code_path_for_kvid(code_dir, kvid)
    if path is None:
        return None
    try:
        source = extract_code(path)
    except Exception:
        return None
    if not source.strip():
        return None
    hits, imports = detect(source)
    return {
        "kvid":       kvid,
        "script_id":  kv["script_id"],
        "title":      kv["title"],
        "votes":      kv["votes"],
        "lines":      kv["lines"],
        "competition": comp_slug,
        "path":       str(path),
        "hits":       hits,
        "imports":    sorted(imports),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta-dir", default="/tmp/meta-kaggle")
    ap.add_argument("--code-dir", default="/tmp/meta-kaggle-code")
    ap.add_argument("--top-per-comp", type=int, default=30)
    ap.add_argument("--max-comps", type=int, default=30)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default="/tmp/oh-mining/findings.json")
    args = ap.parse_args()

    meta = Path(args.meta_dir)
    code = Path(args.code_dir)

    print("loading competitions …", flush=True)
    comps = load_competitions(meta)
    print(f"  {len(comps)} LLM-relevant competitions", flush=True)
    # Sort + clamp
    comps_list = sorted(comps.values(), key=lambda c: c.get("date") or "", reverse=True)[: args.max_comps]
    comp_ids = {c["id"] for c in comps_list}
    print(f"  using top {len(comps_list)} by recency", flush=True)

    print("loading KernelVersionCompetitionSources …", flush=True)
    comp_to_kvids = load_competition_sources(meta, comp_ids)
    all_kvids = set().union(*comp_to_kvids.values()) if comp_to_kvids else set()
    print(f"  {len(all_kvids):,} candidate kernel versions across these comps", flush=True)

    print("streaming KernelVersions.csv (4.4 GB) …", flush=True)
    kvs = stream_kernel_versions(meta, all_kvids)
    print(f"  matched {len(kvs):,} kernel-version rows", flush=True)
    # Map kvid → comp slug (first match wins)
    kvid_to_slug = {kv: comps[cid]["slug"] for cid, kvset in comp_to_kvids.items() for kv in kvset if cid in comps}

    # Top-N per competition by votes
    by_comp: dict[str, list[dict]] = defaultdict(list)
    for kv in kvs:
        by_comp[kvid_to_slug.get(kv["kvid"], "_other")].append(kv)
    targets: list[dict] = []
    for comp_slug, lst in by_comp.items():
        lst.sort(key=lambda r: r["votes"], reverse=True)
        targets.extend((kv, comp_slug) for kv in lst[: args.top_per_comp])
    print(f"  top-{args.top_per_comp}-per-comp → {len(targets):,} kernels to analyze", flush=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"detecting (workers={args.workers}) …", flush=True)
    work = [(str(code), kv, slug) for kv, slug in targets]
    results: list[dict] = []
    if args.workers <= 1:
        for w in work:
            r = process_kernel(w)
            if r:
                results.append(r)
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(process_kernel, w) for w in work]
            for i, fut in enumerate(as_completed(futures), 1):
                r = fut.result()
                if r:
                    results.append(r)
                if i % 100 == 0:
                    print(f"  {i:>5}/{len(futures)} processed", flush=True)
    print(f"  detected hits in {sum(1 for r in results if r['hits']):,} of {len(results):,} kernels", flush=True)

    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nwrote {out_path}", flush=True)

    # Summary
    pattern_count: Counter = Counter()
    comp_pattern: dict[str, Counter] = defaultdict(Counter)
    import_count: Counter = Counter()
    for r in results:
        for h in r["hits"]:
            pattern_count[h] += 1
            comp_pattern[r["competition"]][h] += 1
        for imp in r["imports"]:
            import_count[imp] += 1

    summary = [
        "# Meta Kaggle deep mining — summary",
        "",
        f"- kernels analyzed: **{len(results):,}**",
        f"- kernels with at least one hit: **{sum(1 for r in results if r['hits']):,}**",
        "",
        "## Top 30 patterns (overall)",
        "",
        "| pattern | kernels |",
        "|---|---|",
    ]
    for p, n in pattern_count.most_common(30):
        summary.append(f"| `{p}` | {n} |")
    summary.append("")
    summary.append("## Top 30 imports (overall)")
    summary.append("")
    summary.append("| module | kernels |")
    summary.append("|---|---|")
    for m, n in import_count.most_common(30):
        summary.append(f"| `{m}` | {n} |")
    summary.append("")
    summary.append("## Patterns per competition (top 3 per comp)")
    summary.append("")
    for comp, pc in sorted(comp_pattern.items()):
        top = ", ".join(f"`{p}`×{n}" for p, n in pc.most_common(3))
        summary.append(f"- **{comp}**: {top}")

    Path("/tmp/oh-mining/findings-summary.md").write_text("\n".join(summary) + "\n")
    print("wrote /tmp/oh-mining/findings-summary.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
