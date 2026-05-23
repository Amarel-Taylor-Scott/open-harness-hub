# Redis / DynamoDB key shapes — Open Harness Hub

Key-value stores are used as a **runtime cache**, not authoritative
storage. The canonical store is PostgreSQL (or any backend in `db/`);
Redis holds derived views and per-request data.

## Keys

```
artifact:<id>                            STRING  — JSON manifest
artifact:by_type:<type>                  SET     — set of artifact ids
artifact:by_industry:<industry>          SET     — set of artifact ids
artifact:by_capability:<capability>      SET     — set of artifact ids
artifact:by_modality:<modality>          SET     — set of artifact ids
artifact:by_tag:<tag>                    SET     — set of artifact ids

rule:<pack_id>:<rule_id>                 STRING  — JSON rule body
rule:by_pack:<pack_id>                   SET     — set of rule ids
rule:by_family:<family>                  SET     — set of rule ids
rule:by_category:<category>              SET     — set of rule ids

leaf:<pack_id>:<leaf_id>                 STRING  — JSON leaf body
leaf:by_pack:<pack_id>                   SET     — set of leaf ids
leaf:by_type:<leaf_type>                 SET     — set of leaf ids

run:<run_id>                             HASH    — run state
run:by_pipeline:<pipeline_id>            ZSET    — score = started_at_ms
```

## TTLs

- `artifact:<id>` — 1 hour (refreshed from authoritative store on miss).
- `run:<run_id>` — 7 days (after which run lives only in cold storage).

## Cluster vs single

Use Redis Cluster only if you need horizontal scale. For most catalogs,
a single Redis instance is enough. The `artifact:by_*` SET sizes scale
with catalog size — even 100k artifacts fit easily.
