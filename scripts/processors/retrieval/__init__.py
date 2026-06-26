"""OpenHubForAI — retrieval / prompt-assembly processors (taxonomy steps R0–R6).

This package holds the implementations behind the `catalog/processors/retrieval/`
manifests — the swappable method-components of the governed retrieval pipeline
(see `docs/concepts/retrieval-and-prompt-taxonomy.md`). Each manifest's
`implementations[].path` resolves to a `run(...)` callable here.

Design rules shared by every module:

  * pure stdlib; deterministic wherever the manifest allows;
  * model/embedding dependencies are INJECTED callables (the model-route
    idiom) — offline defaults are deterministic, honest, and LABELED as such
    (a fallback never masquerades as a model);
  * `run()` is read-only unless the manifest says side_effects=write;
  * invalid arguments raise (on_error=raise) — nothing is silently guessed.
"""
