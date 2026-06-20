"""src.teleon.ingest — bulk-ingest machine-readable capability registry dumps into candidate feeds WITHOUT an LLM.

The deterministic, free path from thousands to hundreds of thousands of capabilities: per-registry field-mapping
adapters + a heuristic category/determinism prior (Stage-1 of screen-before-confirm). Writes discovered-feed JSON
the existing runner ingests. Teleon-layer — never imports src.baltor; everything stays a candidate, never truth."""
from src.teleon.ingest.bulk_registry import (
    REGISTRY_FORMATS,
    ingest_dump,
    ingest_to_feed,
    map_entry,
)

__all__ = ["REGISTRY_FORMATS", "ingest_dump", "ingest_to_feed", "map_entry"]
