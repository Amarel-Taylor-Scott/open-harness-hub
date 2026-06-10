# Federal Register API

*tool* · `tool/federal-register-api` · v0.1.0 · experimental

Searches and fetches U.S. Federal Register documents (rules, proposed rules,
notices, presidential documents) with full metadata: agencies, publication
date, effective date, CFR references, and the canonical document URL.

Capability lift: a bare LLM cannot reliably recall current/effective federal
rules or their exact citations and dates. This tool returns the authoritative
record with an effective date and source URL, enabling cite-and-verify and
CDC/freshness handling for volatile regulatory facts.

| axis | value |
|---|---|
| industry | government, legal, compliance |
| capability | retrieval, tool_use, verification |
| modality | structured, text |
| lifecycle | experimental |
| trust_boundary | external |
| freshness | volatile |
| license | MIT |



