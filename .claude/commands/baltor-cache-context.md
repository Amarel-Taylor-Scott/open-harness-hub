---
description: Cache a bounded Baltor context pack and glossary packet summary into local Markdown memory
---

Use the Baltor context gateway as the only source of retrieved context, then
write a safe local Markdown cache with source handles and glossary packets.

Run:

```bash
python3 scripts/baltor_context_cache.py \
  --base-url "${BALTOR_CONTEXT_GATEWAY_URL:-http://127.0.0.1:9304}" \
  --query "$ARGUMENTS"
```

Then inspect:

```bash
sed -n '1,80p' dist/baltor-context-cache/INDEX.md
tail -5 dist/baltor-context-cache/cache-writes.jsonl
```

Rules:

- Do not cache raw source-system dumps.
- Keep `ctx://baltor/...` handles with every durable claim.
- Treat glossary packets as source-scoped until reviewed.
- Do not promote cached terms or ownership claims into global memory.
