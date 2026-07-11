---
status: live_generated_registry
legacy: false
archive: do_not_archive
---
# STATUS — root `catalog/` is the LIVE component registry (NOT legacy)

This directory is the live component/registry substrate: read by `scripts/dev_status.py` and the catalog build.
It is **not** outdated context and must **not** be moved to `archive/legacy/`. High-volume rows are slated to
migrate to DB/staging per the North Star (CLAUDE.md), but until then this is current, tracked, live data.
