# Web search allowlist (default)

*rule-pack* · `rule-pack/web-search-allowlist-default` · v0.1.0 · beta

Default online-search rule pack. Allowlist of trusted public-source
domains, per-source freshness windows, query sanitization rules,
and a small blocklist of dangerous source patterns. Designed to be
composed into any pipeline that does outbound web search.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | retrieval, safety_gating |
| modality | text |
| lifecycle | beta |
| trust_boundary | external |
| freshness | stable |
| license | MIT |



**family:** `online_search`

## Rules

| id | severity | category | pattern/condition |
|---|---|---|---|
| `allow_official_gov` | info | allowlist.government | `*.gov OR *.gov.* OR *.gob.* OR *.gouv.*` |
| `allow_ig_orgs` | info | allowlist.intergovernmental | `ilo.org OR un.org OR who.int OR worldbank.org OR imf.org OR iom.int OR unodc....` |
| `allow_academic` | info | allowlist.academic | `*.edu OR *.ac.* OR arxiv.org OR nature.com OR science.org OR pubmed.ncbi.nlm....` |
| `allow_major_news` | low | allowlist.news | `reuters.com OR apnews.com OR bbc.com OR bbc.co.uk OR ft.com OR economist.com ...` |
| `block_known_misinformation_pattern` | high | blocklist.misinformation | `<misinfo-domains-placeholder>` |
| `sanitize_pii_in_query` | critical | policy.privacy | `ANY pii_regex matches` |
| `freshness_window_default` | — | policy.freshness | `30d` |
| `min_corroboration` | high | policy.corroboration | `3` |

