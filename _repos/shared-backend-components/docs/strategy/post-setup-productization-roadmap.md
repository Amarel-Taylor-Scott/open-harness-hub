# Post-setup productization roadmap (owner-directed 2026-07-07)

> Owner directive: *"Once we get all of this setup, we need to do research, and prove out our token savings,
> and then think about MCP authentication for users, adding MCP binaries/tools to coder/claude
> folders/installations, economics of the product, economics of the system, avoiding stale context."*
>
> This doc pins that sequence to the assets that already exist so no track starts from scratch.
> Everything here is candidate planning; numbers live in receipts, never retyped in prose.

## Track 1 — Research + prove out token savings (ACTIVE)

> **Canonical measurement (owner-canonized 2026-07-07):** real-world savings = `bare` vs `orchestrated`
> on real cloud lanes, executed + cross-tested — see
> [`orchestrated-lane-savings-contract.md`](../codex/orchestrated-lane-savings-contract.md). Everything
> below is supporting evidence around that headline.

- **Done (receipts):** realistic multi-prompt session benchmarks with base-model comparison at 262K context —
  mixed SaaS/app, ML-lifecycle, and large-org lanes, all coverage 1.0 and every session net-positive
  (`data/dev-intel/realistic_session_benchmarks/runs/`); token-spend frontier
  (`data/dev-intel/session_emulation/workload_token_receipt.json`); cross-session consumption proof
  (`scripts/primitive_consumption_proof.py` receipts).
- **Next (the rigorous gaps):**
  1. compare against REAL Claude Code session logs (`scripts/session_context.py` /
     `scripts/session_redundancy.py` already mine `~/.claude/projects/*` deterministically — measured
     redundancy is the addressable-savings denominator);
  2. a real-model A/B on the thinking lane (scaffold-vs-scratch was UNMEASURED — output cap saturates;
     needs a capped-decode protocol);
  3. external replication: run the same session pack through a second model lane (Ollama GLM / Gemma 4)
     and diff receipts.
- **Proof standard:** every claim = receipt + reproduce command; benchmark misses feed `gap_queue.jsonl`.

## Track 2 — MCP authentication for users

- **Read-first (existing):** `docs/architecture/service-auth-and-consumption-model.md` (API keys, service
  accounts, delegated calls, private-bench enforcement), `docs/architecture/auth-identity-kit.md`,
  `docs/architecture/local-dev-tunnels-and-auth.md` (+ `scripts/check_local_dev_tunnel_auth_runtime.py`).
- **Shape:** the MCP servers (`scripts/capability_retrieval_mcp_server.py`,
  `scripts/aidevobserver_mcp_server.py`) get a keyed transport: per-user API keys minted by the identity
  plane, env-names-only credential law, deny-by-default scopes (search/read free tier; compose/verified
  lanes metered). Separate login per product, NO SSO (design law).
- **First move:** add a `--require-api-key` mode to the capability-retrieval server + a key-mint endpoint in
  the identity seam; receipts for every keyed call (token_usage_record).

## Track 3 — MCP binaries/tools into coder/claude folders/installations

- **Existing:** the companion pack `../dev-rules-context/mcp/aidevobserver.md` + `connections.md` document
  the Claude Code wiring; both servers run stdio today.
- **Shape:** an installer (`scripts/install_mcp_pack.py`) that writes the server entries into
  `~/.claude.json` / project `.mcp.json` / Codex + opencode configs, plus a packaged binary lane
  (pipx/uvx entry point) so a coder folder gets `capability-retrieval` with one command. Distribution
  artifact = the funnel's free tier (open-core law).
- **Gate:** never auto-edit a user's global config without an explicit flag; print the diff first.

## Track 4 — Economics (product + system)

- **Product economics:** price against MEASURED savings — the benchmark receipts give tokens-saved/session
  per scenario; charge a fraction of realized savings (metered via the keyed MCP calls' token_usage_records).
  Anchors: `docs/strategy/` monetization + open-core memos; exports free, governed live layer paid.
- **System economics:** cost-to-serve is local-first and near-zero at current scale (SQLite + memmap
  embeddings + fastembed/model2vec CPU lanes); the config-only swap points (pgvector HNSW, Postgres FTS,
  object storage) are already stubbed — cost model = storage GB + embed CPU-seconds + zero LLM tokens on
  the deterministic path. Add a `cost_record` receipt per serving call so the unit economics are computed,
  not estimated.

## Track 5 — Avoiding stale context

- **Existing law + tooling:** promotion boundary requires CDC/revocation handling for volatile facts;
  enrichment coverage RATCHETS (`primitive_enrichment_coverage.py` — coverage may never drop, store
  freshness checked); `check_handoff_docs_freshness.py`; memory law: a doc/memory naming a file is a claim
  about a past state — re-verify before relying on it.
- **Shape:** every served card carries `content_digest` + `verified_at`; a staleness sweep re-hashes sources
  by handle and files `review_ticket`s on drift; index rebuilds are resumable appends (multi-index cursor)
  so refresh is incremental; serving prefers cards whose digests match the latest source snapshot.
- **First move:** add `verified_at`/`digest_checked_at` to the serving payload and a freshness column to the
  multi-index wide table so stale candidates are filterable at query time.

## Sequence

1. Finish current setup (multi-index full build + verification pipeline over the database).
2. Track 1 items 1–3 (proof pack) → publishable savings claims.
3. Track 2 + 3 together (keyed server, installer) → first external users.
4. Track 4 metering on those calls → real unit economics.
5. Track 5 freshness columns before any serves_truth promotion.
