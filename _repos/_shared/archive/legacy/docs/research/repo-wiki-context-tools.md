# Repo Wiki And Code Context Tools

Updated: 2026-06-01

This note tracks DeepWiki-like tools that can turn repositories into
source-linked wiki/context artifacts for Baltor, Claude Code, and local memory
workflows.

## Positioning

DeepWiki-style tools should be treated as repo-context compilers, not as the
enterprise context authority.

```text
repo source / git host
-> repo wiki or code-intelligence generator
-> source-linked pages, diagrams, summaries, handles
-> Baltor context gateway adapter
-> context packs, cache manifests, audit, glossary/term checks
-> Claude Code / local memory / organization context service
```

Baltor should own policy, source-handle normalization, ACL filters, stale-source
warnings, cache manifests, and promotion rules. Repo-wiki tools can supply
high-value codebase summaries and architecture pages.

## Evaluation Dimensions

Use these dimensions when testing a repo-wiki tool:

| Dimension | Why it matters |
| --- | --- |
| Local/private repo support | Enterprise code cannot depend only on public GitHub indexing. |
| Output format | Markdown and JSON are easiest to cache, diff, review, and ingest. |
| Source links | Every page/claim needs file, commit, branch, or line provenance. |
| Commit identity | Generated context must record repo, branch, commit, and timestamp. |
| Incremental updates | Full regeneration can make docs stale or unstable. |
| MCP/API support | Claude Code and Baltor should call a bounded tool interface. |
| Model/provider control | Local CPU models and enterprise-approved providers matter. |
| Auditability | Cache, logs, and review traces are needed before trust promotion. |
| Diagrams | Useful, but must be source-linked and not treated as source truth. |
| License/hosting | Determines whether it can be used inside an enterprise gateway. |

## Project Shortlist

| Tool | Shape | Current fit for Baltor |
| --- | --- | --- |
| DeepWiki / Ask Devin | Hosted repo wiki and Q&A for indexed repos, with MCP access. | Good benchmark and optional public-repo source. Do not use as sole private-enterprise retrieval layer. |
| DeepWiki-Open | Self-hostable DeepWiki-like app with Next.js/FastAPI, RAG, diagrams, and multi-provider support. | Strong PoC candidate for private repo-wiki generation behind Baltor. |
| OpenDeepWiki | Open-source DeepWiki-style system with multiple Git platforms and database backends. | Worth evaluating for org-hosted repo wiki and conversational repo understanding. |
| RepoWiki | CLI-first open-source wiki generator with Markdown, JSON, and HTML outputs. | Strong local developer candidate because it can produce file artifacts without a database. |
| RepoAgent | LLM-powered repository documentation generator with incremental-update direction. | Good for docs-as-code and Markdown output; less directly a gateway unless wrapped. |
| CodeWiki | Open-source/research direction for holistic repository-level documentation. | Useful benchmark/research artifact for eval design. |
| repowise | MCP-oriented repo intelligence with dependency graph, git history, docs, decisions, and code health. | Strong match for Claude Code if it proves stable; evaluate as code-intelligence backend. |
| Synthadoc | Local-first knowledge compilation engine with Markdown, JSONL logs, SQLite audit, hooks, and custom skills. | Strong inspiration for Baltor cache/audit design and local wiki workflows. |
| karpathy-llm-wiki | Agent-skills wiki pattern for compiling sources into durable Markdown pages with citations and linting. | Good local memory pattern, especially for Claude Code/Codex skill packaging. |
| SwarmVault | Local-first LLM wiki/knowledge graph/memory store for many coding agents. | Relevant for agent memory interop; evaluate security and source-handle discipline. |
| deepwiki-to-md / deepwiki_to_md / deepwiki-down | Exporters for DeepWiki pages to Markdown. | Useful as ingestion bridges, not as source of truth. |
| deepwiki-rs | Rust repo-to-doc/context generator under the DeepWiki topic. | Evaluate for fast local CLI workflows. |
| GrokWiki | Repo wiki/search/Q&A via Grok CLI. | Experimental; useful if the org already uses Grok-compatible local tooling. |
| Denote | Markdown docs framework with llms.txt, MCP server, and structured JSON API. | Useful as an AI-readable docs publishing layer for generated repo-wiki artifacts. |
| ktext | `CONTEXT.yaml` generator, validator, and scorer for machine-readable project context. | Good complement for explicit constraints, decisions, risks, and CI gating. |
| CocoIndex codebase summarization examples | Indexing framework patterns for multi-codebase summarization. | Useful for custom pipelines that emit derived wiki pages from repo changes. |
| GitHub Actions doc generators | CI actions that generate PR/change documentation or docs sites. | Useful trigger mechanism, but generated text still needs Baltor provenance and policy wrapping. |

## Recommended Baltor Contract

Add a provider-neutral repo-wiki adapter surface:

```text
repo_wiki_status(provider, repo)
repo_wiki_generate(repo, ref, provider, output_format, max_pages)
repo_wiki_search(repo, ref, query, max_tokens)
repo_wiki_fetch(handle, max_tokens)
repo_wiki_manifest(repo, ref)
```

Every provider should normalize into:

```json
{
  "kind": "baltor.repo-wiki-page.v1",
  "provider": "repowiki",
  "repo": "org/project",
  "ref": "main",
  "commit_sha": "abc123",
  "generated_at": "2026-06-01T00:00:00Z",
  "title": "Request Pipeline",
  "summary": "...",
  "source_handles": [
    "ctx://repo/org/project/commit/abc123/path/src/request.py#L20-L80"
  ],
  "claims": [
    {
      "text": "The request pipeline validates input before queueing worker jobs.",
      "source_handles": [
        "ctx://repo/org/project/commit/abc123/path/src/request.py#L20-L80"
      ],
      "confidence": "medium",
      "promotion_allowed": false
    }
  ],
  "staleness_policy": {
    "source_of_truth": "git",
    "refresh_on_commit_change": true,
    "safe_to_cache_locally": true
  }
}
```

## Integration Pattern

The first useful integration is not full automation. It is a controlled import
path:

```text
RepoWiki / DeepWiki-Open / OpenDeepWiki generates Markdown or JSON
-> Baltor imports generated pages as repo-wiki objects
-> context gateway returns repo-wiki pages only with commit-scoped handles
-> cache writer stores summaries, handles, and generated-at metadata
-> local memory treats generated pages as derived context, not source truth
```

This keeps the same trust boundary used for glossary packets and changing
ownership facts: generated documentation helps routing and understanding, but
does not silently promote claims into canonical graph facts.

## Event-Driven Sync Patterns

Repo-wiki tools are most useful when they stay close to repository changes.
Baltor should support these trigger shapes even when the first implementation is
mocked or manually registered:

| Trigger | Example use | Baltor handling |
| --- | --- | --- |
| Post-commit hook | `repowise hook install` style local auto-sync after commit. | Accept generated page manifest with commit SHA and local path handles. |
| File watcher | Local dev sync while editing. | Mark outputs as local draft context until committed. |
| Push webhook | GitHub/GitLab push event. | Queue repo-wiki generation for changed files/ref. |
| MR/PR webhook | Merge request opened, updated, merged. | Generate review-oriented repo context and changed-file pages. |
| Pipeline artifact | CI job uploads generated wiki JSON/Markdown. | Ingest artifact as derived context, preserving build ID and commit SHA. |
| Scheduled poll | Periodic sync for repos without webhooks. | Refresh only when ref/commit changes. |
| Release/tag event | Generate stable version docs. | Promote versioned repo-wiki pages to longer-lived context. |

The preferred enterprise form is CI-generated artifacts:

```text
commit / push / MR
-> CI job runs RepoWiki, CodeWiki, OpenDeepWiki exporter, ktext, or custom job
-> artifact contains markdown/json + manifest + commit SHA
-> Baltor imports artifact as repo_wiki_page derived context
-> context gateway serves commit-scoped handles
```

This is safer than allowing an agent to re-scan raw repos whenever it wants,
because the generated artifact can be reviewed, stored, diffed, and tied to the
exact pipeline that produced it.

## First PoC Candidates

1. RepoWiki
   - Reason: CLI-first, Markdown/JSON/HTML outputs, no database required.
   - PoC: generate docs for the Baltor admin demo scripts and import the JSON
     output into a Baltor `repo_wiki_page` export.

2. repowise
   - Reason: explicitly supports auto-sync methods such as post-commit hooks,
     file watcher, GitHub/GitLab webhooks, and polling, while exposing
     code-intelligence layers through MCP.
   - PoC: install on one repo, generate docs/history/decision layers, and
     verify its MCP tools can be wrapped behind Baltor without broad raw scans.

3. DeepWiki-Open
   - Reason: closest self-hostable analogue to DeepWiki with RAG and diagrams.
   - PoC: run locally against one public repo and one local repo, then inspect
     source links, output shape, and model/provider control.

4. OpenDeepWiki
   - Reason: shared service shape with MCP support and multiple Git platforms.
   - PoC: deploy internally for one repo family and check auth, refresh, and
     page provenance behavior.

5. Synthadoc or karpathy-llm-wiki
   - Reason: local-first wiki/memory patterns align with Baltor cache manifests.
   - PoC: compare their audit/log/source-citation pattern against
     `baltor.local-context-cache-manifest.v1`.

6. ktext
   - Reason: explicit `CONTEXT.yaml` style project constraints can be generated,
     validated, and scored in CI.
   - PoC: produce a machine-readable context file and import it as a
     high-trust, human-reviewable companion to generated repo wiki pages.

## Open Questions

- Which tools emit structured JSON with enough file/line provenance?
- Which tools can pin output to a commit SHA?
- Which tools support local models or enterprise-approved model routing?
- Which tools can run incrementally without regenerating trusted pages
  unnecessarily?
- Which tools can be safely operated behind a team MCP gateway?
- Which outputs should be imported into Baltor as derived context versus kept as
  external fetch handles?
- Which tools emit CI artifacts that can be ingested without giving the agent
  direct repository read access?
- Which triggers are deterministic enough for production: post-commit hooks,
  webhooks, CI artifacts, or scheduled polling?

## Sources

- DeepWiki docs: <https://docs.devin.ai/work-with-devin/deepwiki>
- DeepWiki MCP blog: <https://cognition.ai/blog/deepwiki-mcp-server>
- GitHub DeepWiki topic: <https://github.com/topics/deepwiki>
- DeepWiki-Open: <https://github.com/AsyncFuncAI/deepwiki-open>
- OpenDeepWiki: <https://deepwiki.com/AIDotNet/OpenDeepWiki>
- RepoWiki: <https://github.com/he-yufeng/RepoWiki>
- RepoAgent: <https://github.com/OpenBMB/RepoAgent>
- RepoAgent paper: <https://arxiv.org/abs/2402.16667>
- CodeWiki paper: <https://arxiv.org/abs/2510.24428>
- repowise: <https://github.com/repowise-dev/repowise>
- repowise hook docs: <https://docs.repowise.dev/docs/cli/hook>
- Synthadoc: <https://github.com/axoviq-ai/synthadoc>
- karpathy-llm-wiki: <https://github.com/Astro-Han/karpathy-llm-wiki>
- SwarmVault: <https://github.com/swarmclawai/swarmvault>
- Denote: <https://denote.sh/>
- ktext: <https://ktext.dev/>
