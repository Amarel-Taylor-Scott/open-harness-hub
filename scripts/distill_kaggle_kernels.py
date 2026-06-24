"""distill_kaggle_kernels — distill the mined Kaggle kernels into candidate registry ENTRIES (the LLM population of #88).

Reads the mined findings (data/kaggle-mining-findings-*.json: kernel -> detected patterns) and DISTILLS them into
candidate registry entries:
  - DETERMINISTIC FLOOR (always): map each detected pattern -> a candidate entry (architecture/kaggle_mining_questions.json
    pattern_to_registry) + aggregate cross-kernel frequency -> the strongest candidates, with lineage.
  - LLM PATH (--live + OH_LLM_API_KEY): run the question bank through the ollama lane (Kimi/GLM/Claude) per kernel for
    richer distillation; honest-offline (floor only) when no lane.

LOSSLESS DISTILLATION CLAUSE: distillation is NEVER replacement — the candidate feed keeps the raw pattern
frequencies + the distilled candidates + lineage (which kernels produced each). serves_truth=false (every distilled
insight is a CANDIDATE; the promotion boundary + verification apply before adoption).

  python3 scripts/distill_kaggle_kernels.py            # write the candidate feed (floor)
  python3 scripts/distill_kaggle_kernels.py --live     # + LLM distill a sample (needs OH_LLM_API_KEY)
  python3 scripts/distill_kaggle_kernels.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_QB = _REPO / "architecture" / "kaggle_mining_questions.json"
_OUT = _REPO / "data" / "dev-intel" / "kaggle_distilled_candidates.json"
_FINDINGS_GLOB = "data/kaggle-mining-findings-*.json"
_TOP_LINEAGE = 3
_LLM_SAMPLE = 5


def _load_findings() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for f in sorted(glob.glob(str(_REPO / _FINDINGS_GLOB))):
        for kernel, pats in json.loads(Path(f).read_text()).items():
            if isinstance(pats, list):
                out[kernel] = pats
    return out


def distill_floor(findings: dict[str, list[str]], pattern_map: dict[str, str],
                  enrichment: dict[str, dict] | None = None) -> list[dict]:
    """Each known pattern -> a candidate registry entry, with cross-kernel frequency + example-kernel lineage.

    ``enrichment`` (architecture/kaggle_mining_questions.json -> pattern_enrichment) attaches MODEL-AUTHORED
    description + use_cases per pattern — the metadata the deterministic floor cannot produce (llm_used=False).
    Backward-compatible: a pattern with no enrichment simply omits those fields. serves_truth stays false.
    """
    enrichment = enrichment or {}
    freq = Counter(p for pats in findings.values() for p in pats)
    candidates = []
    for pattern, registry_candidate in pattern_map.items():
        n = freq.get(pattern, 0)
        if n == 0:
            continue
        lineage = [k for k, pats in findings.items() if pattern in pats][:_TOP_LINEAGE]
        cand = {
            "pattern": pattern, "registry_candidate": registry_candidate,
            "kernels": n, "example_kernels": lineage,
            "via": "deterministic_floor", "candidate": True, "serves_truth": False,
        }
        meta = enrichment.get(pattern)
        if meta and meta.get("description") and meta.get("use_cases"):
            cand["description"] = meta["description"]
            cand["use_cases"] = list(meta["use_cases"])
            cand["enriched"] = True
            cand["enrichment_via"] = "model_authored"
        candidates.append(cand)
    candidates.sort(key=lambda c: c["kernels"], reverse=True)
    return candidates


def _llm_distill_sample(findings: dict[str, list[str]], qb: dict) -> list[dict]:
    """OPTIONAL richer distillation via the ollama lane. Honest-offline: returns [] (with reason) when no lane."""
    if not os.environ.get("OH_LLM_API_KEY"):
        return []
    try:
        from scripts._llm_client import PROVIDERS, chat  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return []
    provider = PROVIDERS.get("ollama", {})
    model = (provider.get("models") or ["glm-5.2"])[0]
    questions = " ".join(q["prompt"] for q in qb.get("questions", []))
    out = []
    for kernel, pats in list(findings.items())[:_LLM_SAMPLE]:
        r = chat(model, "Distill this Kaggle kernel into candidate registry entries. Be terse, JSON-ish.",
                 f"kernel={kernel} detected_patterns={pats}\nQuestions: {questions}", provider)
        if not r.get("error"):
            out.append({"kernel": kernel, "distilled": r.get("text", "")[:1000], "via": f"llm:{model}",
                        "candidate": True, "serves_truth": False})
    return out


def _build(live: bool = False) -> dict:
    findings = _load_findings()
    qb = json.loads(_QB.read_text())
    floor = distill_floor(findings, qb.get("pattern_to_registry", {}), qb.get("pattern_enrichment", {}))
    llm = _llm_distill_sample(findings, qb) if live else []
    return {
        "version": "0.1.0",
        "principle": "LOSSLESS distillation of mined Kaggle kernels -> candidate registry entries; keeps raw freq + lineage; serves_truth=false; candidates only (promotion boundary applies).",
        "serves_truth": False,
        "generated_from": _FINDINGS_GLOB,
        "raw": {"total_kernels": len(findings), "total_pattern_hits": sum(len(p) for p in findings.values())},
        "enriched_candidates": sum(1 for c in floor if c.get("enriched")),
        "llm_used": bool(llm),
        "llm_note": "set OH_LLM_API_KEY + --live for Kimi/GLM/Claude per-kernel distillation" if not llm else "ollama lane",
        "distilled_candidates": floor,
        "llm_distilled": llm,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live", action="store_true", help="also LLM-distill a sample (needs OH_LLM_API_KEY)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    doc = _build(live=args.live and not args.self_test)

    if not args.self_test:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        _OUT.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"wrote {_OUT.relative_to(_REPO)}: {len(doc['distilled_candidates'])} candidate entries from "
              f"{doc['raw']['total_kernels']} kernels (llm_used={doc['llm_used']})")
        return 0

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    cands = doc["distilled_candidates"]
    ck("findings loaded (real mined kernels)", doc["raw"]["total_kernels"] >= 50, str(doc["raw"]["total_kernels"]))
    ck(">=5 candidate registry entries distilled", len(cands) >= 5, str(len(cands)))
    ck("every candidate maps to a registry", all(c["registry_candidate"] for c in cands))
    ck("every candidate carries lineage (example kernels)", all(c["example_kernels"] for c in cands))
    ck("every candidate is governed (candidate-only, non-truth)", all(c["candidate"] and not c["serves_truth"] for c in cands))
    ck("sorted by frequency (lossless aggregate)", all(cands[i]["kernels"] >= cands[i + 1]["kernels"] for i in range(len(cands) - 1)))
    ck("honest about the LLM lane", doc["llm_used"] is False and "OH_LLM_API_KEY" in doc["llm_note"])
    enriched = [c for c in cands if c.get("enriched")]
    ck("model-authored enrichment attached to candidates", len(enriched) >= 5, str(len(enriched)))
    ck("enriched candidates carry description + >=2 use_cases", all(c.get("description") and len(c.get("use_cases", [])) >= 2 for c in enriched))
    ck("enrichment is governed (model_authored, candidate-only)", all(c.get("enrichment_via") == "model_authored" and not c["serves_truth"] for c in enriched))
    ck("enriched count reported in doc", doc.get("enriched_candidates") == len(enriched))
    ck("serves_truth false", doc["serves_truth"] is False)

    if fails:
        print(f"\nFAIL - distill_kaggle_kernels: {len(fails)} of {checks} assertions failed")
        return 1
    top = ", ".join(f"{c['pattern']}({c['kernels']})" for c in cands[:4])
    print(f"PASS - distill_kaggle_kernels: {len(cands)} candidate registry entries distilled from "
          f"{doc['raw']['total_kernels']} kernels (lossless, lineage-tracked); top: {top}; {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
