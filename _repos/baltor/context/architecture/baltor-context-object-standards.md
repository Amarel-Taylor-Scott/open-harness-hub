# Baltor Context Object Standards Profile

Updated: 2026-06-01

There is no single universal standard for LLM context objects. Current tools use
the phrase "context schema" for different things:

- LangChain `contextSchema` types read-only runtime context for one agent
  invocation. It is not persisted between invocations and is useful for request
  metadata, user identity, tenant, roles, deployment environment, feature flags,
  and middleware behavior.
- MCP schemas define protocol objects for tools, resources, prompts,
  capabilities, and metadata. MCP is the delivery protocol, not a full
  provenance or evidence model.
- JSON Schema validates shape.
- JSON-LD, schema.org, W3C PROV, W3C Web Annotation, RO-Crate, SPDX,
  OpenLineage, and OpenTelemetry cover adjacent standards concerns.

Baltor should therefore define a standards-aligned profile, not invent a
universal replacement.

## Recommended Stack

| Requirement | Standard or pattern |
| --- | --- |
| Agent delivery | MCP tools/resources/prompts |
| Runtime invocation context | LangChain/LangGraph `contextSchema` style typed context |
| Runtime validation | JSON Schema 2020-12 |
| Linked-data semantics | JSON-LD and schema.org |
| Provenance | W3C PROV / PROV-O |
| Evidence spans | W3C Web Annotation selectors |
| Packaged artifacts | RO-Crate |
| Software/repo artifacts | SPDX and optionally CycloneDX |
| Data/job lineage | OpenLineage |
| Logs/traces/checks | OpenTelemetry semantic conventions |

## Baltor Profile

Schema:

```text
_repos/shared-backend-components/schemas/context-object.schema.json
```

Kind:

```text
baltor.context-object
```

Required capabilities:

- stable object ID;
- object type;
- `ctx://` source handles;
- policy fields that say whether the object is derived context, whether raw
  source dumps are allowed, and whether promotion is allowed;
- provenance fields for derivation, generator, time, hash, commit, pipeline, or
  job;
- optional Web Annotation style selectors for evidence spans;
- optional MCP delivery metadata;
- optional OpenLineage-style job/run lineage.

## Runtime Context Versus Persistent Context

Do not conflate these:

| Type | Example | Lifetime | Use |
| --- | --- | --- | --- |
| Runtime context schema | LangChain `contextSchema` | One invocation | user ID, role, tenant, environment, request ID |
| Agent state schema | LangGraph state | One run or checkpointed conversation | evolving messages, tool results, work plan |
| Context object | `baltor.context-object` | Persistent or cacheable | source-linked claim, repo-wiki page, glossary packet, context-pack item |
| Context pack | `implementation_pack`, `review_pack` | Request/serving artifact | compressed set of context objects and handles |

LangChain `contextSchema` is useful for invoking the Baltor client:

```text
tenant_id
user_id
role
repo
deployment_env
token_budget
context_cache_dir
```

Baltor context objects are what the gateway returns or caches.

## Example

```json
{
  "kind": "baltor.context-object",
  "@context": {
    "schema": "https://schema.org/",
    "prov": "http://www.w3.org/ns/prov#",
    "oa": "http://www.w3.org/ns/oa#"
  },
  "context_object_id": "ctxobj_repo_wiki_001",
  "object_type": "repo_wiki_page",
  "title": "Request Pipeline",
  "summary": "The request pipeline validates input before queueing worker jobs.",
  "source_handles": [
    "ctx://repo/org/project/commit/abc123/path/src/request.py#L20-L80"
  ],
  "evidence": [
    {
      "source_handle": "ctx://repo/org/project/commit/abc123/path/src/request.py#L20-L80",
      "selector_type": "LineRangeSelector",
      "selector": { "start": 20, "end": 80 },
      "supports_claim": true
    }
  ],
  "provenance": {
    "wasDerivedFrom": ["gitlab:group/project@abc123"],
    "wasGeneratedBy": "repo_wiki.artifact.import",
    "generatedAtTime": "2026-06-01T00:00:00Z",
    "commit_sha": "abc123"
  },
  "policy": {
    "derived_context": true,
    "promotion_allowed": false,
    "raw_source_dump_allowed": false,
    "requires_commit_scope": true,
    "acl_filter_applied": true
  },
  "created_at": "2026-06-01T00:00:00Z"
}
```

## Rule

Use framework context schemas for invocation metadata. Use Baltor context objects
for durable, auditable, source-linked context.

## Sources

- LangChain `contextSchema`: <https://reference.langchain.com/javascript/langchain/index/CreateAgentParams/contextSchema>
- LangChain context engineering: <https://docs.langchain.com/oss/javascript/langchain/context-engineering>
- LangChain custom middleware context: <https://docs.langchain.com/oss/javascript/langchain/middleware/custom>
- MCP schema reference: <https://modelcontextprotocol.io/specification/2025-11-25/schema>
- MCP basic protocol: <https://modelcontextprotocol.io/specification/2025-11-25/basic>
- W3C PROV-O: <https://www.w3.org/TR/2012/WD-prov-o-20120503/>
- W3C Web Annotation: <https://www.w3.org/TR/annotation-model/>
- RO-Crate: <https://www.researchobject.org/ro-crate/specification/1.1/introduction.html>
- OpenLineage: <https://github.com/OpenLineage/OpenLineage/blob/main/spec/OpenLineage.md>
- SPDX: <https://spdx.dev/about/overview/>
- OpenTelemetry semantic conventions: <https://opentelemetry.io/docs/concepts/semantic-conventions/>
