"""src.teleon.digestion — the Skill/Tool Digestion Lab: digest an expensive skill into a cheaper, more
DETERMINISTIC runtime candidate while preserving the original skill as fallback.

The money loop: observe skill → parse (PARSE ONLY, never execute) → infer capability + I/O contracts + required
tools/models → extract deterministic substeps → recommend a cheap→expensive cascade → emit a candidate runtime
path (status candidate, original kept as fallback). Discovery≠trust; LLM-assist is advisory (via the Inference
Gateway); promotion needs sandbox (the Sandbox Gateway) + eval + redteam. Lives in Teleon; no src.baltor import.
"""
from .digester import (parse_skill_md, digest_skill, build_runtime_candidate, extract_determinism, is_unsafe,
                       RUNTIME_CASCADE)
from .open_hub_outputs import emit_open_hub_candidates
from .model_compatibility import run_model_compatibility

__all__ = ["parse_skill_md", "digest_skill", "build_runtime_candidate", "extract_determinism", "is_unsafe",
           "RUNTIME_CASCADE", "emit_open_hub_candidates", "run_model_compatibility"]
