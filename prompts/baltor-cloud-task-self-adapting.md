# SUPERSEDED → see baltor-purpose-driven-cloud-task-runtime.md

Renamed **Cloud Task → PurposeTask (Purpose-Driven Cloud Task)** on 2026-06-06: "Cloud Task" collides with
**Google Cloud Tasks** (a managed async queue/dispatch product). The canonical, fuller spec is:

**`prompts/baltor-purpose-driven-cloud-task-runtime.md`**

It carries the naming correction, the competitive wedge (AWS/GCP/Azure/ServiceNow/Kiro have parts, not the
whole), the 7 planes / 12-step lifecycle, the refined object model, the "embed CI/CD-like gates, don't eliminate
CI/CD" refinement, the 11-part build, hard safety rules, and the PURPOSE TASK CLAUSE. The shipped PoC + contract
live under `src/baltor/purpose_tasks/` + `schemas/purpose_tasks/PurposeTaskSpec` (flywheel 316). Use the
canonical file; do not build from this stub. (Kept as a redirect — no orphaned contradiction.)
