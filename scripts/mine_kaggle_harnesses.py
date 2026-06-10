#!/usr/bin/env python3
"""Mine Kaggle competition notebooks for harness / pipeline / rule-pack
patterns and emit DRAFT manifests under catalog/_inbox/.

Detector strategy:
  1. List kernels for a competition via the Kaggle public API.
  2. Filter to kernels whose license is redistribution-compatible.
  3. Download the kernel source.
  4. Apply a small bundled detector pack (grep + classifier) that
     identifies wrapper functions adding preprocessing, retrieval,
     tool-calling, or output post-processing around an LLM call.
  5. For each detected pattern, emit a draft manifest with the
     attribution chain (source URL, author, license) filled in.

The script is INTENTIONALLY conservative: every output goes to
catalog/_inbox/<date>-<kernel>/ and must be reviewed by a curator
before being moved to catalog/<type>/.

Usage:
  pip install kaggle
  mkdir -p ~/.kaggle && cp ~/Downloads/kaggle.json ~/.kaggle/
  python scripts/mine_kaggle_harnesses.py \
      --competitions gemma-4-good-hackathon lmsys-chatbot-arena \
      --since 2026-04-01 --until 2026-05-31
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "catalog" / "_inbox"

ALLOWED_LICENSES = {
    "Apache-2.0", "Apache 2.0", "apache-2.0",
    "MIT", "mit",
    "BSD-3-Clause", "bsd-3-clause", "BSD-2-Clause",
    "CC0-1.0", "CC0",
    "CC-BY-4.0", "CC BY 4.0",
    "CC-BY-SA-4.0", "CC BY-SA 4.0",
}

DETECTORS: list[tuple[str, str, str]] = [
    # (id, regex, kind)
    ("harness_wrapper_call_model",
     r"def\s+(\w+)\s*\([^)]*\)\s*:[^\n]*\n(?:[^\n]*\n){0,80}?[^\n]*(?:openai\.|anthropic\.|gemini\.|llama\.|gemma_\w+|model\.generate|client\.chat\.completions|gen_chat|llm\.|run_inference)",
     "harness"),
    ("rag_retrieval_wrapper",
     r"def\s+(\w+_retrieve|\w+_search|\w+_rag)\s*\([^)]*\)\s*:[^\n]*\n(?:[^\n]*\n){0,40}?[^\n]*(bm25|cosine|faiss|index\.search|embed|encoder\.encode)",
     "rule_pack_rag"),
    ("grep_rule_table",
     r"(GREP_RULES|grep_rules|PII_PATTERNS|REGEX_RULES)\s*=\s*\[",
     "rule_pack_grep"),
    ("citation_graph_edges",
     r"(CITATION_EDGES|citation_edges|_citations\.json|build_citation_graph)",
     "knowledge_pack_citation"),
    ("tool_registry",
     r"(TOOLS|TOOL_REGISTRY|tool_dispatch|FUNCTION_TOOLS|tools\s*=\s*\[)",
     "tool_registry"),
    ("rubric_dimensions",
     r"(RUBRIC|RUBRIC_DIMENSIONS|rubric_dimensions|scoring_rubric)",
     "rubric"),
    ("pipeline_dag",
     r"(PIPELINE_STEPS|pipeline\s*=\s*\[|class\s+\w*Pipeline\b)",
     "pipeline"),
]


def kaggle_available() -> bool:
    return shutil.which("kaggle") is not None


def list_kernels(competition: str, since: str | None, until: str | None) -> list[dict]:
    """Use kaggle CLI to list kernels for a competition."""
    if not kaggle_available():
        print("kaggle CLI not on PATH; skipping live listing.", file=sys.stderr)
        return []
    cmd = ["kaggle", "kernels", "list", "--competition", competition, "--csv", "--page-size", "100"]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=60)
    except subprocess.CalledProcessError as e:
        print(f"kaggle list failed for {competition}: {e.output}", file=sys.stderr)
        return []
    lines = [line for line in out.splitlines() if line.strip()]
    if len(lines) < 2:
        return []
    header = [h.strip() for h in lines[0].split(",")]
    kernels: list[dict] = []
    for row in lines[1:]:
        # CSV may include commas inside quoted fields; use csv module for safety.
        import csv
        reader = csv.reader([row])
        cells = next(reader)
        if len(cells) != len(header):
            continue
        record = dict(zip(header, cells))
        if since and record.get("lastRunTime", "") < since:
            continue
        if until and record.get("lastRunTime", "") > until:
            continue
        kernels.append(record)
    return kernels


def pull_kernel(ref: str, dest: Path) -> Path | None:
    """Pull a kernel's source to `dest` and return the kernel.py path."""
    if not kaggle_available():
        return None
    cmd = ["kaggle", "kernels", "pull", ref, "-p", str(dest), "-m"]
    try:
        subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=120)
    except subprocess.CalledProcessError as e:
        print(f"pull failed for {ref}: {e.output}", file=sys.stderr)
        return None
    candidates = list(dest.glob("*.py")) + list(dest.glob("*.ipynb"))
    return candidates[0] if candidates else None


def detect_patterns(source: str) -> list[dict]:
    findings: list[dict] = []
    for det_id, pattern, kind in DETECTORS:
        for m in re.finditer(pattern, source, re.MULTILINE):
            findings.append({
                "detector": det_id,
                "kind":     kind,
                "match_at": m.start(),
                "snippet":  source[max(0, m.start() - 100): m.end() + 200].strip()[:600],
            })
    return findings


def emit_draft(kernel_ref: str, kernel_meta: dict, findings: list[dict]) -> Path:
    today = date.today().isoformat()
    safe_ref = kernel_ref.replace("/", "_")
    out = INBOX / f"{today}-{safe_ref}"
    out.mkdir(parents=True, exist_ok=True)

    license_ = kernel_meta.get("language") or kernel_meta.get("license") or "unknown"
    license_compatible = license_ in ALLOWED_LICENSES

    (out / "manifest_draft.md").write_text(
        "\n".join([
            f"# Draft import: {kernel_ref}",
            "",
            f"- **source_url**: https://www.kaggle.com/code/{kernel_ref}",
            f"- **author**: {kernel_meta.get('author', '?')}",
            f"- **license**: {license_}",
            f"- **license_compatible**: {license_compatible}",
            f"- **detected_patterns**: {len(findings)}",
            "",
            "## Findings",
            "",
            *[f"- `{f['detector']}` → propose `{f['kind']}` (at offset {f['match_at']})"
              for f in findings],
            "",
            "## Snippets",
            "",
            *[f"### {f['detector']}\n\n```python\n{f['snippet']}\n```\n" for f in findings],
        ])
    )

    (out / "findings.json").write_text(json.dumps({
        "kernel_ref": kernel_ref,
        "attribution": {
            "source_url":  f"https://www.kaggle.com/code/{kernel_ref}",
            "source_kind": "kaggle",
            "author":      kernel_meta.get("author"),
            "license":     license_,
            "license_compatible": license_compatible,
        },
        "findings": findings,
        "ingested_at": today,
    }, indent=2))

    return out


def mine(competitions: Iterable[str], since: str | None, until: str | None, dry_run: bool) -> int:
    total = 0
    for comp in competitions:
        print(f"\n=== {comp} ===")
        kernels = list_kernels(comp, since, until)
        print(f"  found {len(kernels)} kernels")
        if dry_run or not kernels:
            continue
        with tempfile.TemporaryDirectory() as tmp:
            for k in kernels:
                ref = k.get("ref") or k.get("kernelRef") or k.get("title")
                if not ref:
                    continue
                license_ = (k.get("language") or k.get("license") or "").strip()
                if license_ and license_ not in ALLOWED_LICENSES:
                    print(f"  skip (license {license_!r}): {ref}")
                    continue
                dest = Path(tmp) / ref.replace("/", "_")
                dest.mkdir(parents=True, exist_ok=True)
                path = pull_kernel(ref, dest)
                if not path:
                    continue
                source = path.read_text(errors="ignore")
                findings = detect_patterns(source)
                if not findings:
                    print(f"  no patterns in {ref}")
                    continue
                out = emit_draft(ref, k, findings)
                print(f"  emit draft → {out.relative_to(ROOT)} ({len(findings)} findings)")
                total += 1
    print(f"\nDone. {total} drafts emitted under {INBOX.relative_to(ROOT)}.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--competitions", nargs="+", default=[],
                    help="Kaggle competition slugs (e.g. gemma-4-good-hackathon).")
    ap.add_argument("--since", default=None, help="YYYY-MM-DD (filter by kernel lastRunTime).")
    ap.add_argument("--until", default=None, help="YYYY-MM-DD (filter by kernel lastRunTime).")
    ap.add_argument("--dry-run", action="store_true", help="List kernels but do not pull.")
    args = ap.parse_args()

    if not args.competitions:
        ap.print_help()
        return 1

    INBOX.mkdir(parents=True, exist_ok=True)
    return mine(args.competitions, args.since, args.until, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
