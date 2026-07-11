# Repo-to-repo dependency graph

15 surfaces, 32 dependency edges. Direction: `A --> B`
means A may consume B's published interface.

```mermaid
graph TD
  shared_backend_components --> dev_rules_context
  openhubforai --> dev_rules_context
  openhubforai --> shared_backend_components
  teleon --> dev_rules_context
  teleon --> shared_backend_components
  teleon --> openhubforai
  baltor --> dev_rules_context
  baltor --> shared_backend_components
  baltor --> openhubforai
  baltor --> teleon
  aidevobserver --> dev_rules_context
  aidevobserver --> shared_backend_components
  aidoneright --> dev_rules_context
  aidoneright --> teleon
  aidoneright --> baltor
  aidoneright --> aidevobserver
  aidoneright --> openhubforai
  api_endpoint_wrappers --> dev_rules_context
  api_endpoint_wrappers --> shared_backend_components
  scraping --> dev_rules_context
  scraping --> shared_backend_components
  scraping --> api_endpoint_wrappers
  context_injection --> dev_rules_context
  context_injection --> shared_backend_components
  business_context --> dev_rules_context
  edge_graph_generator --> dev_rules_context
  pitch_decks --> dev_rules_context
  pitch_decks --> aidoneright
  yc_applications --> dev_rules_context
  yc_applications --> aidoneright
  fundraising --> dev_rules_context
  fundraising --> aidoneright
```

## Adjacency (who each repo may consume)
- **aidevobserver** → dev-rules-context, shared-backend-components
- **aidoneright** → aidevobserver, baltor, dev-rules-context, openhubforai, teleon
- **api-endpoint-wrappers** → dev-rules-context, shared-backend-components
- **baltor** → dev-rules-context, openhubforai, shared-backend-components, teleon
- **business-context** → dev-rules-context
- **context-injection** → dev-rules-context, shared-backend-components
- **dev-rules-context** → (none)
- **edge-graph-generator** → dev-rules-context
- **fundraising** → aidoneright, dev-rules-context
- **openhubforai** → dev-rules-context, shared-backend-components
- **pitch-decks** → aidoneright, dev-rules-context
- **scraping** → api-endpoint-wrappers, dev-rules-context, shared-backend-components
- **shared-backend-components** → dev-rules-context
- **teleon** → dev-rules-context, openhubforai, shared-backend-components
- **yc-applications** → aidoneright, dev-rules-context
