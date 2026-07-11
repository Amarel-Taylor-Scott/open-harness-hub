# AI Startup Source Surface Discovery Map

**Status:** candidate-source map  
**Purpose:** find high-signal AI products, startup workflows, open-source tools, launch patterns, and builder pain points, then convert them into candidate primitive opportunities.  
**Truth boundary:** all derived rows remain `serves_truth=false` until source rights, contract proof, execution proof, and promotion gates pass.

## Operating Rule

These sources should be mined as metadata first:

- source URL, title, date, category, tags, company/tool/repo name;
- compact internal summary;
- candidate input/output edge guesses;
- primitive opportunity IDs;
- proof and license tasks.

Do not republish profile copy, article bodies, newsletter bodies, comments, repo code, or product descriptions unless the source license and redaction gates explicitly allow it.

## Highest-Signal Sources

| Source | Lane | Primitive families to mine |
|---|---|---|
| YC AI Companies | startup directory | vertical AI workflows, product surfaces, integration templates, company/category maps |
| YC Requests for Startups | market thesis | startup request to primitive gap, benchmark seed, AI-native service template |
| Product Hunt AI | launch tracker | launch to microsurface, AI tool category map, pricing/use-case signals |
| Hacker News Show HN | builder launch forum | developer launch gaps, technical patterns, early integration opportunities |
| Hugging Face Spaces | AI app demos | demo input/output contracts, model app route, multimodal primitives |
| GitHub AI topic | open-source repos | repo to primitive edge cards, tool wrappers, benchmark fixtures |
| OSSInsight Trending AI | open-source momentum | trending capability watchlist, agent/tooling demand signals |
| Futurepedia | AI tool directory | task taxonomy, tool category map, integration template candidates |
| There's An AI For That | AI task directory | task-to-existing-tool signals, use-case taxonomy seeds |
| StartupHub.ai | startup database | sector maps, investor themes, vertical workflow candidates |
| TopStartups.io | startup tracker | funding and sector signals, product category mapper |
| BetaList AI | prelaunch startups | early product signals, landing-page to use-case seeds |
| CB Insights AI 100 | market map | later-stage product patterns, enterprise AI workflow signals |
| Forbes AI 50 | market map | category mapping, notable private-company workflow hints |
| Dealroom AI | startup database | geography, sector, funding, ecosystem signals |
| Crunchbase News AI | funding/news | funding round signal, company event source seeds |

## Newsletters And Builder Feeds

Use title/link metadata first:

- TLDR AI;
- The Rundown AI;
- The Batch by DeepLearning.AI;
- Import AI;
- Latent Space;
- Interconnects;
- Ben's Bites;
- The Sequence;
- AlphaSignal;
- Last Week in AI;
- TechCrunch AI;
- VentureBeat AI;
- Crunchbase News AI;
- Sifted AI;
- Hacker News.

The first RSS rows wired into the loop are:

- `hn-show-hn-ai`;
- `techcrunch-ai`;
- `venturebeat-ai`;
- `crunchbase-news`;
- `latent-space`;
- `import-ai`.

## Open-Source Indexes

Use link/heading metadata first:

- GitHub AI topic;
- Awesome LLM Apps;
- Model Context Protocol servers;
- Awesome MCP Servers;
- Awesome LLM;
- Awesome AI Agents;
- Awesome Generative AI;
- Awesome Open Source AI;
- Papers With Code;
- Hugging Face Daily Papers.

## Startup-Derived Primitive Families

The foundry should prefer reusable primitives in these families:

- `startup_product_pattern_miner`;
- `vertical_ai_workflow_seed`;
- `product_launch_to_microsurface`;
- `startup_landing_page_to_use_case`;
- `ai_tool_category_mapper`;
- `integration_template_opportunity`;
- `repo_to_primitive_edge_cards`;
- `open_source_tool_pattern`;
- `agent_framework_candidate`;
- `mcp_connector_candidate`;
- `space_app_to_primitive_route`;
- `model_demo_task_template`;
- `demo_input_output_contract`;
- `venture_thesis_to_primitive_gap`;
- `market_pattern_to_benchmark_seed`;
- `funding_round_signal`;
- `enterprise_ai_workflow_signal`.

## Domain Expansion

These startup surfaces should cross-feed NAICS, stock trading, and employment-agency coverage:

- stock trading: market data ingest, OHLCV normalization, backtest gates, broker adapters, portfolio risk policies, sandbox trading compliance;
- employment agencies: candidate intake, job order schema, resume parsing, screening gates, placement workflows, staffing compliance;
- NAICS-wide: every industry code should generate industry entity schemas, workflow templates, dataset loaders, compliance checklists, and eval fixtures.

Adjacent high-volume feedstock:

- algorithm repositories: deterministic algorithm edges, data-structure
  primitives, complexity records, and equivalence tests;
- developer dictionaries and programming resource indexes: intent-parser
  vocabulary, edge synonyms, architecture/checklist candidates, and reusable
  software engineering workflows;
- job boards and role/career taxonomies: skill-to-primitive maps, job workflow
  templates, candidate-screening surfaces, and labor-market demand signals;
- federal procurement sources: SAM.gov opportunity ingest, RFP classification,
  NAICS/PSC matching, set-aside gates, proposal pipelines, USAspending award
  enrichment, and Grants.gov funding workflow primitives.

## Files Wired Into The Foundry

- `catalog/knowledge-packs/data/primitive-source-surface-map/surfaces.jsonl`
- `catalog/knowledge-packs/data/aidevobserver-source-discovery-search-seeds/search-topics.jsonl`
- `catalog/knowledge-packs/data/aidevobserver-multilingual-search-scopes/scopes.jsonl`
- `catalog/knowledge-packs/data/aidevobserver-rss-source-feeds/feeds.jsonl`
- `catalog/knowledge-packs/data/aidevobserver-markdown-index-sources/indexes.jsonl`
- `scripts/naics_primitive_scope_generator.py`

## Weekly Routine

Daily:

- Product Hunt AI;
- Show HN AI;
- GitHub AI topic;
- OSSInsight Trending AI;
- Hugging Face Spaces;
- TechCrunch AI;
- VentureBeat AI.

Weekly:

- YC AI Companies;
- Futurepedia;
- There's An AI For That;
- StartupHub.ai;
- TopStartups.io;
- Latent Space;
- Import AI;
- The Batch.

Monthly or quarterly:

- YC Requests for Startups;
- CB Insights AI 100;
- Forbes AI 50;
- Dealroom AI;
- Sifted AI 100;
- a16z AI;
- Sequoia AI Ascent;
- Stanford AI Index.
