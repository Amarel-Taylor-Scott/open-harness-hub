"""OpenHubForAI — factory orchestration package.

The factory turns external knowledge trees into validated draft manifests
in `catalog/_inbox/` at scale (target 2000x current catalog).

Modules:
  processor_loader  — dynamic resolution of `implementations[].path` via importlib
  run_factory       — orchestrator CLI (walk → gate → dedup → emit → judge)
  run_report        — provenance + cost + quality reporter
"""
