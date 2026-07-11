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
from src.teleon.ingest.csv_import import (
    CsvImportResult,
    CsvRow,
    read_uploaded_csv_rows,
    summarize_csv_import,
    validate_required_columns,
)

__all__ = [
    "CsvImportResult",
    "CsvRow",
    "REGISTRY_FORMATS",
    "ingest_dump",
    "ingest_to_feed",
    "map_entry",
    "read_uploaded_csv_rows",
    "summarize_csv_import",
    "validate_required_columns",
]
