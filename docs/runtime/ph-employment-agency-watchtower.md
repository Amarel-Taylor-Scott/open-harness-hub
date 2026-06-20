# PH Employment-Agency Watchtower

This is the concrete fragile-fact pattern for a context claim such as:

```text
Agency X is licensed to recruit overseas workers in the Philippines.
```

The source of record is official DMW/POEA licensing/status evidence, with DMW or
DOLE advisories as corroborating official sources where available. A customer
wiki, vendor screening cache, PDF handout, or LLM extraction is evidence only; it
does not become served context unless it reconciles against the official source.

Runtime shape:

- Teleon runs deterministic capabilities for source fetch, parser normalization,
  content-hash CDC, authority reconciliation, and context promotion/hold-out.
- Teleon may run LLM-assisted capabilities to detect source-layout changes,
  extract candidate rows from unstructured advisories, or summarize discrepancies.
  Those outputs are candidate evidence and `serves_truth=false`.
- Baltor owns the truth boundary: the current context pack serves only the
  authority-reconciled status with source handles, and keeps stale or conflicting
  claims in held-out evidence.

Proof:

```bash
python3 scripts/context_workers/ph_employment_agency_watchtower.py --self-test
```

The proof models an official DMW/DOLE suspended-status agreement, a stale customer
claim saying the agency is valid, and a vendor cache that is preserved but held
out. It also proves unavailable official sources create verification tasks rather
than fake clears.
