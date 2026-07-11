"""OpenHubForAI — processor implementations.

This package holds the Python implementations of the deterministic
runtime processors declared in `_repos/shared-backend-components/catalog/processors/`. Each processor
manifest's `implementations[].path` should resolve to a `run(...)`
callable here.

Modules:
  wikipedia_category_walker  — backs processor/wikipedia-category-walker
  (more walkers + processors land here as they are implemented)
"""
