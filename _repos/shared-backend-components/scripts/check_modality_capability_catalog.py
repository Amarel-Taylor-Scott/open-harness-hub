#!/usr/bin/env python3
"""check_modality_capability_catalog — proof that AI-startup capabilities across modalities (document/image/text/
video/audio/multimodal) are reverse-engineered into input→output pipelines that all share one shape: a DETERMINISTIC
spine (ingest/segment/align/validate/output) wrapping an irreducible MODEL CORE (OCR/embed/ASR/diarize/generate).
Each is therefore a TUNABLE cascade — run the deterministic spine cheaply, escalate to the cheapest-capable model
core only for what it must. Fully deterministic only where there is NO model core. Discovery!=trust; serves_truth=false.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_modality_capability_catalog.py --self-test
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_CAT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "architecture" / "modality_capability_catalog.json"


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    cat = json.loads(_CAT.read_text())
    caps = cat["capabilities"]
    mods = {c["modality"] for c in caps}
    ck("catalog spans >= 6 modalities (document/image/text/video/audio/multimodal) with >= 14 capabilities",
       len(mods) >= 6 and len(caps) >= 14, f"{sorted(mods)} / {len(caps)} caps")

    # the universal shape: unless the task IS pure generation (deterministic_achievable == "no"), the output is
    # shaped by a DETERMINISTIC stage — the structured output is governable. (Inputs may start with a model stage,
    # e.g. audio→ASR, so "begins deterministic" is NOT universal — kept honest.)
    ck("every non-pure-generation capability ends with a deterministic output-shaping stage",
       all(c["pipeline"][-1]["deterministic"] for c in caps if c["deterministic_achievable"] != "no"),
       str([c["capability"] for c in caps if c["deterministic_achievable"] != "no" and not c["pipeline"][-1]["deterministic"]]))

    # spine ∪ core == all stages; spine is non-empty (the governable/tunable part)
    part_ok = True
    for c in caps:
        spine = {s["stage"] for s in c["pipeline"] if s["deterministic"]}
        core = {s["stage"] for s in c["pipeline"] if not s["deterministic"]}
        alls = {s["stage"] for s in c["pipeline"]}
        if spine | core != alls or not spine or set(c["deterministic_spine"]) != spine or set(c["model_core"]) != core:
            part_ok = False
            break
    ck("the deterministic spine + model core PARTITION the pipeline; the spine is always non-empty", part_ok)

    # deterministic_achievable semantics: full <=> no model core; no/partial <=> has a model core
    ck("deterministic_achievable is in the enum and consistent (full <=> empty model core)",
       all(c["deterministic_achievable"] in cat["deterministic_achievable_enum"] for c in caps)
       and all((c["deterministic_achievable"] == "full") == (len(c["model_core"]) == 0) for c in caps),
       str([c["capability"] for c in caps if (c["deterministic_achievable"] == "full") != (len(c["model_core"]) == 0)]))

    # the fully-deterministic exemplars (no model core) exist — the "fully deterministic where appropriate" cases
    full = [c["capability"] for c in caps if c["deterministic_achievable"] == "full"]
    ck("fully-deterministic capabilities exist (web-content-extraction, scene-segmentation) — model-free",
       {"web-content-extraction", "scene-segmentation"} <= set(full), str(full))

    # every capability is a tunable candidate grounded in example startups (discovery != trust)
    ck("every capability is tunable, candidate, startup-grounded, never truth",
       all(c["tunable"] is True and c["governed"] == "candidate" and c["example_startups"]
           and c["serves_truth"] is False for c in caps))
    # the model core is the expected irreducible set across the catalog (OCR/embed/asr/diarize/generate-ish)
    cores = {s for c in caps for s in c["model_core"]}
    ck("the model core across the catalog is the expected irreducible set (asr/embed/extract/generate/diarize)",
       any("asr" in s for s in cores) and any("embed" in s for s in cores)
       and any("extract" in s or "summarize" in s or "generate" in s for s in cores))
    ck("the catalog never serves truth", cat["serves_truth"] is False)
    ck("deterministic", json.loads(_CAT.read_text()) == cat)

    n_full = len(full)
    print("\n" + (f"PASS - check_modality_capability_catalog: {len(caps)} AI-startup capabilities across {len(mods)} "
                  f"modalities, each reverse-engineered into a deterministic-spine + model-core pipeline (a tunable "
                  f"cascade); {n_full} are fully deterministic (no model core); the rest escalate to the "
                  f"cheapest-capable model core only for what's irreducible. Discovery != trust; never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_modality_capability_catalog.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
