"""src.teleon.infra — infra SCALE-DECISION ports: each heavy backend behind ONE agnostic seam.

The scale substrate from docs/architecture/scale-architecture-review-2026-06-25.md (durable
orchestration, OLTP/OLAP split, ANN vector search, the CDC/event-log spine) lives behind agnostic
ports so the backend is a DEPLOY-TIME config choice, never a caller change — mirroring how
src.teleon.storage.record_store swaps a storage tier's backend. Each role is HONEST-UNAVAILABLE (no
fabrication) when its real client lib/endpoint is absent, with a local in-memory fallback so the
descent still runs offline. serves_truth=false. See :mod:`src.teleon.infra.scale_ports`.
"""
