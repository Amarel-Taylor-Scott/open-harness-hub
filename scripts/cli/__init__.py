"""Open Harness Hub — the open-funnel developer CLI (``oh-baltor``).

This package is **M5 of the north-star wave** (``docs/codex/north-star.md`` §"The
execution sequence" — *"Open funnel polish … a dev installs, builds a governed
harness, pulls a verified corpus, runs it against their own agent — no
account."*). It is the **open, no-account, works-with-the-agent-you-run** surface:
a thin command-line front end that COMPOSES the already-shipped, already-
self-tested backend (M1 corroboration, M3 serving/tiering) into the three things
a developer does at the seam where they hand verified context to their own agent:

  * ``serve``  — emit the consumption surfaces (``llms.txt`` / ``llms-full.txt``
    and/or the MCP serve descriptor) so a dev drops a governed corpus into Claude
    Code / Codex / Cursor.
  * ``verify`` — run the multi-source corroborator on a claim + its sources and
    print the verdict (the "we check your docs are RIGHT" wedge as a one-liner).
  * ``tiers``  — show the raw/compressed/hyper-efficient token counts + measured
    fidelity for a corpus (the Baltor density story, runnable offline).

It owns **no** product logic of its own — every subcommand delegates to
``scripts.enrichment.serve`` / ``scripts.enrichment.tier_pipeline`` /
``scripts.processors.assurance.multi_source_corroborate``. Pure-stdlib, reads
small JSON, writes only to stdout (no network, no hidden filesystem writes).

Public entrypoint:
    python3 -m scripts.cli.oh_baltor --help
    python3 scripts/cli/oh_baltor.py --selftest
"""
