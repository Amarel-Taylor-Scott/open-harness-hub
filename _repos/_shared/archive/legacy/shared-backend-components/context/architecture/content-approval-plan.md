# Content Approval Plan

Dedupe resolution clears duplicate risk. It does not prove that generated content is ready to become an active component. The content approval planner adds the missing gate between dedupe resolution and active component promotion.

The planner reads:

- `component-candidates.jsonl`
- `normalized-objects.jsonl`
- `dedupe-resolutions.jsonl`

It writes:

- `content-approval-decisions.jsonl`
- `content-promotion-decisions.jsonl`
- `content-approval-decisions.csv`
- `content-promotion-decisions.csv`
- `content-approval-index-records.csv`
- `content-approval-review-tickets.csv`
- `load-content-approvals.sql`
- `content-approval-plan.json`

## Approval Boundary

The planner can make four decisions:

- `approve_for_promotion`
- `review_before_promotion`
- `hold`
- `reject`

Only `approve_for_promotion` creates a derived `promote_candidate` promotion decision. Every other decision creates a review path or hold path.

This keeps the factory additive while preserving a hard boundary between generated rows and active reusable components.

## Current Seed Behavior

The current seed candidates have dedupe resolution, public trust tier, public privacy boundary, and structured labels, but their content is still marked for review. The planner therefore emits content approval rows and review tickets rather than active promotion approvals.

The next step is to add a curator or policy-review worker that can mark selected content as approved, then feed those rows back through the approved component promotion planner.
