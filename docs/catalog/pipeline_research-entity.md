# Research Entity

*pipeline* · `pipeline/research-entity` · v0.1.0 · experimental

Given an entity name + entity kind (company / person / place / product),
produce a sourced one-page profile. Verifiable, cited, redacted.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | research, retrieval, extraction, summarization, verification |
| modality | text |
| lifecycle | experimental |
| trust_boundary | mixed |
| license | MIT |



## Task

Given (entity_name, entity_kind, optional_country), produce a one-page
sourced profile with: short description, key facts, recent events,
conflict-or-controversy section, and a citation list. Every claim is
cited; PII is redacted before any external call.

**pipeline_kind:** `research_entity`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `redact_query` | harness | `harness/redact-pii-text` | — |
| 2 | `plan` | harness | `harness/text-safety-review` | — |
| 3 | `search` | tool | `tool/web-search` | — |
| 4 | `verify_sources` | harness | `harness/text-safety-review` | — |
| 5 | `extract_facts` | harness | `harness/text-safety-review` | — |
| 6 | `compose` | harness | `harness/text-safety-review` | — |

## Sample runs

### company-acme
```json
{
  "pipeline": "pipeline/research-entity",
  "scenario": "company-acme",
  "inputs": {
    "entity_name": "Acme Corp",
    "entity_kind": "company",
    "country": "US",
    "freshness_window_days": 30
  },
  "trace": [
    {
      "step_id": "redact_query",
      "kind": "harness",
      "ref": "harness/redact-pii-text",
      "input": {
        "text": "Acme Corp"
      },
      "output": {
        "redacted_text": "Acme Corp",
        "audit": []
      },
      "ms": 4,
      "simulated": false
    },
    {
      "step_id": "plan",
      "kind": "harness",
      "ref": "harness/text-safety-review",
      "input": {
        "messages": [
          {
            "role": "user",
            "content": "Plan a 5-step research outline for Acme Corp (company)."
          }
        ]
      },
      "output": {
        "text": "1. Find official company filings (SEC, Companies House)\n2. Identify recent press releases (past 30 days)\n3. Cross-check with trade press\n4. Check controversies (regulator actions, lawsuits)\n5. Compose one-page profile with citations",
        "citations": [],
        "trace": []
      },
      "ms": 423,
      "simulated": false
    },
    {
      "step_id": "search",
      "kind": "tool",
      "ref": "tool/web-search",
      "input": {
        "query": "Acme Corp",
        "max_results": 10
      },
      "output": {
        "results": [
          {
            "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=acmecorp",
            "title": "Acme Corp filings \u2014 SEC EDGAR",
            "snippet": "Form 10-K (annual) filed 2026-03-14.",
            "score": 0.92
          },
          {
            "url": "https://www.reuters.com/company/acme-corp/",
            "title": "Acme Corp \u2014 Reuters company profile",
            "snippet": "Industrial conglomerate headquartered in Wilmington, DE.",
            "score": 0.81
          }
        ]
      },
      "ms": 312,
      "simulated": false
    },
    {
      "step_id": "verify_sources",
      "kind": "harness",
      "ref": "harness/text-safety-review",
      "input": {
        "messages": [
          {
            "role": "user",
            "content": "Score each source for credibility; drop low-credibility entries."
          }
        ]
      },
      "output": {
        "accepted": [
          "sec.gov filing",
          "reuters profile"
        ],
        "dropped": []
      },
      "ms": 287,
      "simulated": false
    },
    {
      "step_id": "extract_facts",
      "kind": "harness",
      "ref": "harness/text-safety-review",
      "input": {
        "messages": [
          {
            "role": "user",
            "content": "Extract typed facts (date, claim, evidence_url)."
          }
        ]
      },
      "output": {
        "facts": [
          {
            "date": "2026-03-14",
            "claim": "Acme Corp filed Form 10-K for FY 2025.",
            "evidence_url": "https://www.sec.gov/..."
          },
          {
            "date": "2026",
            "claim": "Acme Corp is headquartered in Wilmington, Delaware.",
            "evidence_url": "https://www.reuters.com/..."
          }
        ]
      },
      "ms": 612,
      "simulated": false
    },
    {
      "step_id": "compose",
      "kind": "harness",
      "ref": "harness/text-safety-review",
      "input": {
        "messages": [
          {
            "role": "user",
            "content": "Compose a one-page profile from extracted facts. Cite every claim."
          }
        ]
      },
      "output": {
        "text": "## Acme Corp\n\nAcme Corp is an industrial conglomerate headquartered in Wilmington, Delaware [1]. The company filed Form 10-K for fiscal year 2025 on 2026-03-14 [2].\n\n[1] https://www.reuters.com/company/acme-corp/\n[2] https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=acmecorp",
        "citations": [
          "https://www.reuters.com/company/acme-corp/",
          "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=acmecorp"
        ]
      },
      "ms": 1810,
      "simulated": false
    }
  ],
  "output": {
    "profile_markdown": "## Acme Corp\n\nAcme Corp is an industrial conglomerate headquartered in Wilmington, Delaware [1]. The company filed Form 10-K for fiscal year 2025 on 2026-03-14 [2].\n\n[1] https://www.reuters.com/company/acme-corp/\n[2] https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=acmecorp",
    "citations": [
      "https://www.reuters.com/company/acme-corp/",
      "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=acmecorp"
    ],
    "trace": []
  },
  "model": "ollama/llama3.1:8b",
  "frozen_at": "2026-05-19T12:00:00Z",
  "license": "MIT"
}
```