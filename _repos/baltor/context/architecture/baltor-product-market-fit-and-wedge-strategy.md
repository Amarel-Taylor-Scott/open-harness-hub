# Baltor Product-Market Fit And Wedge Strategy

Baltor has real product-market-fit potential, but the first product should not
launch as the full governed context fabric.

The sharp wedge is:

```text
Trusted context packs for engineering agents.
```

Baltor should give Claude Code, Cursor, Copilot, Rovo Dev, CI agents, and
internal agents the smallest permission-safe, source-linked context pack for a
ticket, PR/MR, repo, incident, or review, then record what the agent saw.

The broader Context Fabric architecture is still valuable, but the first
commercial problem is narrower:

```text
sync raw context
process it into source-linked claims and artifacts
find fragile, stale, contradictory, or high-risk information
keep that fragile information fresh
serve compact context packs to agents and reviewers
audit what was served
```

This keeps Baltor out of the generic enterprise-search trap. Downstream systems
already handle many pieces: chat, coding, IDE assistance, enterprise search,
MCP gateway access, vector storage, and source-system workflows. Baltor's wedge
is the trusted context supply chain between those systems.

## Product-Market Fit Verdict

Current product-market fit grade:

```text
promising but unproven: 7/10
```

Why:

```text
problem severity is high
market timing is strong
AI coding agents are spreading quickly
developer trust remains fragile
enterprise governance is becoming a blocker
differentiation is plausible through source handles, freshness, and audit
```

Main risks:

```text
adoption friction
incumbent bundling
connector complexity
security review burden
overbuilding before paid demand is proven
```

The launch message should not be:

```text
Governed context fabric for enterprise AI.
```

The launch message should be:

```text
Baltor gives AI coding agents trusted context packs for every ticket and pull
request: source-linked, permission-aware, fresh, and auditable.
```

## Core Hypothesis

Engineering organizations adopting AI coding agents are discovering that agent
quality is constrained less by model choice and more by context quality.

They need a governed, source-linked, permission-aware context layer that works
across tools, repos, tickets, docs, and agents.

Baltor wins if it becomes the standard context contract between enterprise
sources and AI agents.

Customer-facing version:

```text
Baltor helps engineering teams safely scale AI coding agents by giving them
approved, fresh, source-linked context for every ticket and pull request.
```

## Primary Niche

The primary niche is not broad memory, search, or AI governance.

It is:

```text
fragile engineering context freshness
```

Fragile context means information that is likely to cause bad AI-assisted work
if it is missing, stale, contradicted, or unaudited.

Examples:

```text
acceptance criteria
ADRs and architecture decisions
source ownership
service boundaries
retry policies
security requirements
deprecated APIs
recent incidents
merged PRs that changed behavior
feature flag behavior
test commands
known flaky tests
current parent-company/vendor ownership
current support escalation paths
```

Baltor should discover this context, mark fragile items, schedule refreshes,
detect contradictions, and serve the freshest safe pack to agents.

## Why Now

The market is moving from:

```text
Can AI help?
```

to:

```text
Can we let AI agents operate safely inside real workflows?
```

Important market signals:

```text
AI adoption is broad, but scaled value is uneven.
Developer trust in AI accuracy remains limited.
Coding agents are entering normal PR, issue, and CI workflows.
MCP is making agent-tool access easier and riskier.
Governance failures are becoming a board-level concern for agent rollout.
```

Relevant public references:

```text
McKinsey 2025 State of AI survey:
  https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai

Stack Overflow 2025 Developer Survey:
  https://survey.stackoverflow.co/2025

GitHub Octoverse 2025:
  https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/

GitHub Copilot code review GA:
  https://github.blog/changelog/2025-04-04-copilot-code-review-now-generally-available/

Claude Code GitHub Actions:
  https://code.claude.com/docs/en/github-actions

Anthropic MCP announcement:
  https://www.anthropic.com/news/model-context-protocol

MCP tool specification:
  https://modelcontextprotocol.io/specification/2025-06-18/server/tools

OWASP LLM Top 10:
  https://owasp.org/www-project-top-10-for-large-language-model-applications/

Cloudflare MCP Server Portals:
  https://blog.cloudflare.com/zero-trust-mcp-server-portals/
```

## Ideal Customer Profile

Best first ICP:

```text
mid-market to enterprise engineering organizations
100-2,000 developers
already piloting or using AI coding agents
```

Strong signals:

```text
Jira or Linear
GitHub or GitLab
Confluence or Notion
Slack or Teams
multiple repos or unclear ownership
Claude Code, Cursor, Copilot, Rovo Dev, or internal agents
platform/DevEx or AI enablement team
security concerns around MCP/tools/agents
PR/MR cycle-time, incident, onboarding, or review metrics
```

Avoid initially:

```text
very small startups
highly regulated mega-enterprises with slow procurement
company-wide knowledge-search buyers
teams that have not yet tried coding agents
```

Best first buyer:

```text
Head of Platform Engineering
Head of Developer Experience
VP Engineering
AI Enablement Lead
```

Security is an important approver, but engineering leadership is the likely
economic buyer.

## Best Wedge Use Case

Build around:

```text
context_for_ticket()
review_pack()
```

For a Jira ticket, Linear issue, GitHub issue, GitLab issue, PR, or MR, Baltor
returns a compact implementation or review pack containing:

```text
acceptance criteria
relevant decisions
related code pointers
past incidents
risks
tests to run
owner hints
source handles
freshness labels
policy decision
trace ID
```

First workflows:

```text
1. Developer starts a ticket.
   Baltor builds an implementation_pack instead of the agent crawling sources.

2. Agent opens or updates a PR/MR.
   Baltor attaches a review_pack showing what changed and what context applies.

3. Reviewer audits the AI-assisted change.
   Reviewer sees source handles, freshness labels, and policy decisions.

4. Platform/security reviews rollout.
   Admin sees who requested context, what sources were expanded, and what
   policies applied.
```

This wedge is measurable:

```text
less context gathering
faster first PR
fewer review cycles
fewer stale assumptions
fewer agent tool calls
lower token usage
better auditability
```

## Jobs To Be Done

Developer:

```text
When I pick up a ticket, I want the AI agent to understand the relevant repo,
requirements, decisions, and risks without making me spoon-feed context or
verify every assumption.
```

Reviewer:

```text
When an AI-assisted PR arrives, I want to know whether it satisfies the ticket,
respected architectural decisions, and used trustworthy context.
```

Platform / DevEx:

```text
When teams use many AI agents, I want one approved context contract instead of
every tool inventing retrieval, permissions, memory, and source expansion.
```

Security / compliance:

```text
When agents access internal systems, I want source permissions enforced before
model access, high-risk actions gated, sensitive data controlled, and every
context expansion logged.
```

## Assumption Validation Matrix

| Assumption | Confidence | Why it matters | Fast validation test | Pass threshold |
| --- | ---: | --- | --- | --- |
| Engineering teams feel context quality limits AI-agent adoption | High | Core pain | 30 interviews with AI-using engineering teams | 18+ call it a top-3 blocker |
| Developers will use context packs inside existing tools | High | Product surface | MCP/CLI prototype with Claude Code/Cursor | 50%+ of pilot users invoke weekly |
| Platform teams will pay for cross-agent context governance | Medium | Budget risk | Sell design-partner pilots | 3 paid pilots or LOIs in 60 days |
| Source handles increase trust | High | Differentiator | A/B review: pack with vs. without handles | Reviewers prefer sourced pack 70%+ |
| Context packs improve agent task success | Medium | Outcome proof | Baseline agent vs. Baltor pack on historical tickets | 20%+ accepted completion lift or 30%+ fewer corrections |
| Context packs reduce token/tool cost | Medium | Economic proof | Instrument tokens and source expansions | 25%+ reduction without quality loss |
| Permission-aware retrieval is required for approval | High | Security wedge | Security interviews | 70%+ say ACL/audit is required |
| Existing tools do not solve enough | Medium | Competition risk | Teardowns with Rovo, Glean, Sourcegraph, Augment, Copilot users | 50%+ still report cross-source gaps |
| Local encrypted memory is an early must-have | Low-medium | Scope risk | Ask devs and buyers separately | Build later unless 40%+ of pilots demand it |
| Relationship graph is needed before MVP | Low | Overbuild risk | Manual/heuristic linking in pilot | Delay unless pack quality fails |
| Model routing is needed for MVP | Low | Scope risk | Pilot telemetry | Delay unless model costs block adoption |
| Teams grant connector access quickly | Medium-low | Deployment risk | Jira + GitHub/GitLab + Confluence pilot | First pack within 1 day |

## MVP Scope

Build:

```text
Baltor Engineering Context Pack MVP
```

In scope:

```text
Jira or Linear connector
GitHub or GitLab connector
Confluence or Notion connector
optional linked Slack/Teams threads

ticket_pack
implementation_pack
review_pack

context_for_ticket(ticket_id)
context_for_mr(mr_url)
context_for_repo(repo_name)
context_trace(pack_id)
expand_source(handle)

MCP server
CLI
PR/MR comment or check
simple trace/audit console

read-only by default
ACL-before-model
source-handle expansion logging
basic sensitivity tags
feedback capture
```

Out of scope for MVP:

```text
industry packs
LoRA rerankers
full context object marketplace
general enterprise search
broad local encrypted memory sync
autonomous source-system writes
heavy model routing
full relationship graph UI
complex custom schema catalog
```

The out-of-scope items can become moat later. They are not needed to prove product-market fit.

## Validation Program

Phase 1: problem discovery, 2 weeks.

```text
30-40 interviews
10 developers
8 staff engineers/reviewers
8 platform/DevEx leaders
4 security/compliance reviewers
4 engineering executives
```

Discovery pass criteria:

```text
60%+ of target accounts describe agent context quality, source traceability, or
permission governance as a top-three blocker to scaling AI agents.
```

Phase 2: concierge validation, 2 weeks.

```text
manually create Baltor-style packs for 20 tickets from 3-5 teams
include requirements, related PRs, ADRs, code pointers, stale facts, conflicts,
freshness labels, and source handles
```

Concierge pass criteria:

```text
developers say packs save 30+ minutes on average
reviewers say packs improve review confidence
2+ teams ask to use it again
1+ team asks for MCP/CLI integration without prompting
```

Phase 3: thin technical MVP, 4-6 weeks.

```text
Jira + GitHub/GitLab + Confluence
one MCP server
one CLI
pack builder
source handles
basic ACL enforcement
audit log
feedback capture
```

MVP pass criteria:

```text
first useful pack within 24 hours of source access
70%+ packs rated useful
50%+ active pilot developers use weekly
25%+ reduction in context-gathering time
20%+ reduction in AI-assisted PR review back-and-forth or equivalent quality metric
3 paid pilots or signed expansion intent
```

Phase 4: paid pilot, 8-12 weeks.

```text
$10k-$25k fixed pilot
2-5 repos
1-2 ticket projects
20-50 developers
agreed success metrics before start
```

Paid pilot pass criteria:

```text
2 of 3 pilots convert or expand
buyer sees Baltor as platform capability, not productivity script
security/platform approve broader use
pilot asks for more connectors, repos, or CI integration
```

## Product-Market Fit Metrics

Activation:

```text
time from connector setup to first useful pack
users generating a pack in first week
packs used by agent or attached to PR
source handles expanded per pack
packs with positive feedback
```

Engagement:

```text
weekly active developers
weekly active repos/projects
packs per ticket
packs per PR/MR
repeat usage by same developer
pack reuse across team
```

Outcomes:

```text
ticket start to first PR
PR cycle time
review comment count
rework rate
test failure rate after AI-assisted change
stale assumptions caught
onboarding time for unfamiliar repo
token/tool-call cost per completed task
```

Trust and governance:

```text
claims with source handles
packs with freshness labels
policy denials/warnings
raw source expansions
sensitive-source accesses prevented
audit-log completeness
security approval time
```

Business:

```text
paid pilot conversion
team-to-team expansion
seats or repos under management
net revenue retention
gross margin per pack
sales cycle length
security review completion rate
```

## Competitive Position

Baltor should not compete as another coding agent, enterprise search product,
or generic MCP gateway.

It should be the governed context layer those systems use.

| Category | Examples | Strength | Baltor response |
| --- | --- | --- | --- |
| AI coding agents | Copilot, Claude Code, Cursor, Rovo Dev | Embedded workflows and code generation | Integrate with them |
| Atlassian work graph | Rovo, Teamwork Graph | Jira/Confluence context and permissions | Add cross-source, cross-agent packs |
| Enterprise search | Glean, Microsoft, Google, Elastic | Broad workplace search | Focus on engineering task packs |
| Code intelligence | Sourcegraph, Augment | Codebase context and symbols | Combine code with tickets, ADRs, incidents, audit |
| MCP gateways | Cloudflare, Microsoft, Portkey-like gateways | Tool access and policy | Own context-pack assembly and source trace |
| Frameworks | LangChain, LlamaIndex, internal RAG | DIY systems | Productize governance, handles, and outcomes |

Durable differentiation:

```text
context packs as unit of value
source handles
ACL-before-model
context trace
source precedence and conflict handling
fragile information detection
freshness refresh queues
local-to-cloud memory boundary
```

## Packaging

Developer Context Kit:

```text
local MCP
CLI
context_for_ticket
context_for_mr
GitHub/GitLab integration
source handles
pack feedback
optional local notes
```

Team Context Packs:

```text
shared packs
Jira/GitHub/GitLab/Confluence connectors
team source rules
PR comments/checks
pack history
basic audit
```

Enterprise Context Gateway:

```text
SSO
ACL-before-model
policy center
audit logs
DLP/sensitivity labels
MCP gateway integration
connector admin
pack retention
eval dashboard
enterprise support
```

Regulated/enclave tier:

```text
private deployment
dedicated VPC/on-prem
retention controls
strict audit exports
custom policy engine
regulated connectors
```

## Pricing Validation

Test three offers:

```text
Team productivity:
  reduce AI-assisted ticket cycle time and PR review churn
  price by active developer seat

Agent governance:
  safely approve Claude Code/Cursor/Copilot/Rovo Dev across teams
  price by platform fee plus seats

Context infrastructure:
  standard context-pack API for all internal agents
  price by annual platform contract plus usage
```

Most likely first paid wedge:

```text
Offer B: agent governance plus productivity
```

Pure productivity competes with existing AI tool seats. Pure governance can be
seen as overhead. Baltor should sell the combination:

```text
better agent outcomes with auditable control
```

## Go-To-Market

Start design-partner led, not self-serve only.

Sequence:

```text
1. Focused landing page:
   Trusted context packs for AI coding agents.

2. 10-ticket context audit:
   show what context was needed, missing, stale, or conflicting.

3. Paid pilot:
   2-5 repos, 20-50 developers, 8-12 weeks.

4. Platform rollout:
   more repos, CI review packs, security policy, audit dashboards.
```

Content that sells:

```text
Why AI coding agents fail: context, not intelligence
How to audit what an AI agent saw
The context pack pattern for agentic software development
MCP is not enough: agents need governed context
From Jira ticket to PR: a source-linked context trail
```

Community wedge:

```text
open context-pack.schema.json
reference MCP server
source-handle convention
```

The company can still charge for connectors, governance, audit, pack builders,
enterprise deployment, evals, and refresh/freshness infrastructure.

## Biggest Risks

Too broad, too early:

```text
Mitigation: ship only ticket/MR/review packs first.
```

Incumbents bundle the feature:

```text
Mitigation: be cross-agent and cross-source; own pack format, source handles,
traceability, freshness, and source precedence.
```

Abstract positioning:

```text
Mitigation: sell safer/faster AI-assisted tickets and PRs.
```

Integration burden:

```text
Mitigation: start with Jira + GitHub/GitLab + Confluence + Claude Code/Cursor/Copilot.
```

Developers bypass it:

```text
Mitigation: integrate into CLI, MCP, PR comments, IDE/agent hooks. Avoid new UI dependency.
```

Context quality is hard to prove:

```text
Mitigation: measure deltas, attach source handles, show conflicts, and record
what changed because of the pack.
```

Security promise is hard:

```text
Mitigation: read-only first, mirror source permissions, log expansions, avoid
write actions until trust is established.
```

## Pivot Options

| Failed assumption | Pivot |
| --- | --- |
| Developers do not care enough | Sell agent audit and MCP governance to platform/security |
| Platform teams will not pay | Open-source local MCP and sell paid team sync |
| Coding tools solve enough | Focus on cross-source PR review packs and compliance trace |
| Atlassian dominates | Become a Teamwork Graph enhancer or focus non-Atlassian stacks |
| Source permissions are too hard | Start repo-local with opt-in source handles |
| Context packs do not improve coding | Move to incident response, support escalation, or security triage |
| Local memory is strongest pull | Ship encrypted developer memory plus promotion workflow |

## What To Keep

Keep:

```text
context packs
source handles
ACL-before-model
context trace
pack lineage
source precedence
fragile-information detection
freshness refresh queues
local/cloud memory distinction
MCP/API delivery
engineering-first market
```

De-emphasize for MVP:

```text
broad industry packs
LoRA rerankers
model routing
full context object registry
marketplace language
general enterprise knowledge graph
multi-standard ontology mapping
```

These are strategic architecture, not first paid workflow.

## 90-Day Plan

Days 1-15:

```text
30-40 interviews
10-ticket manual context audit
landing page test
5 design partners
choose first source stack
```

Days 16-45:

```text
MCP server
CLI
Jira/GitHub/GitLab/Confluence connectors
context_for_ticket
context_for_mr
source handles
basic audit
feedback capture
```

Days 46-75:

```text
3 design partners
20-50 developers each
measure cycle time, review churn, pack usefulness, stale context, token/tool reduction
weekly feedback with platform and developer users
```

Days 76-90:

Continue if:

```text
3 paid pilots or 2 paid pilots plus 1 strong enterprise LOI
50%+ weekly active usage among pilot developers
70%+ packs rated useful
measurable outcome improvement
security/platform asks for expansion
```

Pause or pivot if:

```text
teams like the idea but will not install it
usage depends on founder hand-holding
packs are viewed as summaries, not workflow-critical artifacts
no one will pay separately from existing AI tools
```

## Bottom Line

Baltor should not start as a universal context platform.

It should start as:

```text
the trusted context-pack layer for AI-assisted engineering
```

The strongest first promise:

```text
For every ticket and PR, Baltor gives your AI agent the right context and gives
your team proof of what it saw.
```

That is specific, urgent, measurable, and aligned with where the market is
going. If that wedge works, Baltor can expand into the larger context fabric.
