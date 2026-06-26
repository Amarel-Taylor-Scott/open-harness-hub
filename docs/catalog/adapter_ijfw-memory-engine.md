# IJFW memory engine (markdown memory + promotion cycle)

*adapter* · `adapter/ijfw-memory-engine` · v0.1.0 · experimental

Wraps the memory engine from FerroxLabs/ijfw (MIT, v1.6.x): plain-
markdown memory with keyword+recency recall, pattern promotion after
repeated cross-session references, and bi-temporal validity windows.
CAUTION: upstream's "dream cycle" PRUNES stale notes — destructive
compaction that violates the lossless-distillation law — so the wrap
must run with pruning disabled or snapshot-before-prune. Useful as a
cheap local memory-provider candidate and as a benchmark foil.
WRAP CANDIDATE (discovery ≠ trust): admitted from the 2026-06 YC/tool
landscape research as a governed CANDIDATE behind a port — its output is
never served as truth, it is sandboxed, and measured lift is PENDING
(two-axis gate: lift AND structural durability) before any promotion.
Landscape record: docs/strategy/yc-context-landscape-2026-06.md.

| axis | value |
|---|---|
| industry | ai, software |
| capability | memory, retrieval |
| modality | text |
| lifecycle | experimental |
| trust_boundary | external |
| license | MIT |



