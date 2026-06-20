---
description: Read the local Baltor context cache manifest without contacting the gateway
---

Read the local Baltor cache manifest and summarize the latest cached context
pack, glossary packet file, audit log, and cache policy.

Run:

```bash
python3 scripts/baltor_context_cache_read.py \
  --out-dir "${BALTOR_CONTEXT_CACHE_DIR:-dist/baltor-context-cache}"
```

For machine-readable output:

```bash
python3 scripts/baltor_context_cache_read.py \
  --out-dir "${BALTOR_CONTEXT_CACHE_DIR:-dist/baltor-context-cache}" \
  --format json
```

Rules:

- This command must not contact source systems or the context gateway.
- Treat the cache as local memory, not source of truth.
- Do not promote cached glossary terms or ownership facts into global memory.
