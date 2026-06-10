# Wikipedia citation reachability + source-text-integrity checker

*tool* · `tool/wikipedia-citation-checker` · v0.1.0 · experimental

For each citation in a supplied Wikipedia article, check:

 1. URL reachability (200 vs 404 vs paywall vs redirect chain).
 2. Archived-version availability (web.archive.org, archive.today).
 3. Reliable-source tier classification (WP:RSP cross-check).
 4. (Optional, on-demand only) Source-text-integrity sample —
    fetch a citation, locate the quoted claim, return
    supports / contradicts / not-found.

Does NOT modify the article. Does NOT make policy determinations.
Surfaces evidence for `harness/wikipedia-quality-review` and the
reviewer.

Implementation should rate-limit aggressively to avoid hitting
reliable-source paywalls or upsetting publishers; on-demand
source-text-integrity checks are explicit per-citation, not
bulk-scrape.

| axis | value |
|---|---|
| industry | media, media.editorial, media.factcheck |
| capability | verification, retrieval |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | external |
| license | MIT |



