---
name: research-official-regulatory-source
description: Find the current official value from an authoritative regulatory source.
required_tools: [http.fetch, source_handle.generate, browser.use]
required_models: [reasoning]
license: MIT
---
# Research official regulatory source

When asked for a regulatory value:
1. Restrict to the official domain allowlist (e.g. cfpb.gov, ecfr.gov, federalregister.gov).
2. Rank sources by authority: regulation text > official FAQ > summary.
3. HTTP fetch the official page first; generate a source handle.
4. Parse the deadline/value with a deterministic parser rule.
5. Only if the page renders client-side, fall back to the browser tool.
6. Only if the value is ambiguous, ask the LLM to summarize (cite the source handle).
7. Never serve an FAQ value over the regulation text; hold out the conflict.
