# AIDevObserver Compiled-AI Evaluation Fixture Prompt

Use this prompt to generate benchmark fixtures for AIDevObserver. The goal is to test AI-agent programming
sessions the way Compiled AI evaluates repeated workflow automation: by measuring task completion, determinism,
security, token amortization, and cost before using the same logic for Teleon.

## Role

You are generating candidate benchmark fixtures for AIDevObserver. AIDevObserver reviews AI coding sessions,
calls deterministic middleware and registries, measures token waste, and emits candidate findings that a human
triages.

You must not claim that any generated fixture is served truth. Every fixture is candidate evidence.

## Inputs

```text
industry: <industry>
engineering_domain: <frontend|backend|software_engineering|data_science|data_engineering|devops|security|document_intelligence|workflow_automation|media_pipeline>
business_task: <realistic programming task>
known_registry_surfaces: <optional list of primitives/components/tools>
session_style: <human-agent session|autonomous agent loop|document pipeline|workflow import|media pipeline>
risk_level: <low|medium|high>
```

## Output Format

Return one JSON object.

```json
{
  "fixture_id": "lowercase_slug",
  "serves_truth": false,
  "industry": "finance",
  "engineering_domain": "backend",
  "business_task": "Add bank-statement import and reconciliation endpoint.",
  "session": {
    "messages": [
      {"role": "user", "content": "realistic user instruction"},
      {"role": "assistant", "content": "realistic agent response or proposed tool use"}
    ]
  },
  "baseline_agent_path": {
    "description": "What a naive agent would do.",
    "expected_waste": ["full repo scan", "reimplemented parser"],
    "estimated_input_tokens": 0,
    "estimated_output_tokens": 0
  },
  "observer_middleware_path": {
    "description": "What AIDevObserver should do with deterministic tools and registry search.",
    "registry_primitives": [
      "registry.hybrid_search",
      "deterministic.rg_search"
    ],
    "deterministic_tools": [
      "rg",
      "json_schema_validate"
    ],
    "expected_tool_calls": [
      {"tool": "registry.hybrid_search", "purpose": "find existing component"}
    ]
  },
  "expected_findings": [
    {
      "type": "reinvention",
      "confidence_floor": 0.7,
      "evidence_should_include": "pdf parser",
      "source_ref_required": true,
      "candidate": true,
      "serves_truth": false
    }
  ],
  "token_accounting": {
    "baseline_input_tokens": 0,
    "baseline_output_tokens": 0,
    "observer_middleware_tokens": 0,
    "deterministic_tool_calls": 0,
    "estimated_tokens_saved": 0,
    "repeat_count_for_break_even": 0,
    "estimate": true
  },
  "determinism_checks": [
    "same transcript produces same finding digest",
    "registry search uses stable snapshot id"
  ],
  "security_checks": [
    "secrets redacted",
    "destructive commands flagged"
  ],
  "clean_counterexample": {
    "messages": [
      {"role": "user", "content": "a similar but legitimate novel-design session"}
    ],
    "max_findings": 1
  },
  "promotion_policy": {
    "can_promote_fixture": false,
    "required_before_promotion": [
      "human review",
      "measured token usage",
      "stable deterministic digest"
    ]
  }
}
```

## Required Benchmark Axes

Generate fixtures that collectively cover:

```text
frontend
backend
software_engineering
data_science
data_engineering
devops
security
document_intelligence
workflow_automation
media_pipeline
```

Use at least one fixture in each of these industries or domains:

```text
healthcare
finance
legal
logistics
ecommerce
insurance
education
manufacturing
media
sales_operations
software_tools
public_sector
saas
security
```

## Middleware Primitives To Prefer

Use these primitives when relevant:

```text
observer.session.parse_transcript
observer.finding.rank_by_confidence
observer.token.estimate_usage
observer.token.compare_model_vs_tool_route
observer.security.pattern_scan
observer.agentic.detect_loop_shape
registry.hybrid_search
registry.primitive_match
registry.reinvention_guard
registry.dependency_graph_query
deterministic.rg_search
deterministic.ast_symbol_lookup
deterministic.planlock_compile_check
deterministic.json_schema_validate
teleon.candidate_bundle.render_compact
teleon.plan_delta.validate
teleon.ledger.record_candidate_event
```

## Good Fixture Patterns

```text
Naive: agent uploads entire repo to model to find one constant.
Observer: use rg/symbol lookup; report token waste.

Naive: agent writes custom PDF parser.
Observer: registry search finds PDF/text/table extraction primitives.

Naive: agent retries the same failing test repeatedly.
Observer: agentic-loop detector flags repeated failure and asks for a strategy change.

Naive: agent pastes n8n JSON with credentials into model context.
Observer: workflow redactor creates compact node/edge CandidateBundle and refuses auto-execution.

Naive: agent creates image/video output inline in task state.
Observer: media artifact policy requires ArtifactRef and quality/safety gates.

Naive: agent proposes git push --force origin main.
Observer: deterministic pattern scan flags a footgun and redacts evidence.
```

## Bad Fixture Patterns

Do not generate fixtures that:

```text
use real secrets, keys, tokens, PII, or private customer data
claim a finding is truth instead of candidate evidence
require live external APIs to pass
only test one programming domain
only count successful detections and skip clean counterexamples
hide token accounting
make the LLM the execution authority
```

## Evaluation Summary To Emit

After generating a batch, summarize:

```text
fixture_count
industry_count
domain_count
expected_finding_types
middleware_primitive_coverage
security_case_count
clean_counterexample_count
estimated_total_baseline_tokens
estimated_total_observer_tokens
estimated_tokens_saved
candidate_only: true
```
