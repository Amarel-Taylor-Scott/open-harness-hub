"""Reusable CSV import primitives for uploaded vendor files.

These functions are intentionally small, typed, and side-effect free. They are
safe for AIDevObserver to expose as edge summaries so a coding harness can
reuse the capability without reading or rewriting the implementation.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


CsvRow = dict[str, str]


@dataclass(frozen=True, slots=True)
class CsvImportResult:
    """Summary of a validated CSV import."""

    rows: tuple[CsvRow, ...]
    columns: tuple[str, ...]
    row_count: int
    missing_required_columns: tuple[str, ...] = ()


def read_uploaded_csv_rows(path: Path) -> list[CsvRow]:
    """Read an uploaded CSV file into dictionaries keyed by header names."""

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            {str(key or "").strip(): str(value or "").strip() for key, value in row.items()}
            for row in reader
        ]


def validate_required_columns(rows: list[CsvRow], required_columns: tuple[str, ...]) -> CsvImportResult:
    """Validate required columns and return a deterministic import summary."""

    columns = tuple(rows[0].keys()) if rows else ()
    available = set(columns)
    missing = tuple(column for column in required_columns if column not in available)
    return CsvImportResult(
        rows=tuple(rows),
        columns=columns,
        row_count=len(rows),
        missing_required_columns=missing,
    )


def summarize_csv_import(result: CsvImportResult) -> dict[str, object]:
    """Convert a CSV import result into a JSON-compatible response packet."""

    return {
        "row_count": result.row_count,
        "columns": list(result.columns),
        "missing_required_columns": list(result.missing_required_columns),
        "valid": not result.missing_required_columns,
    }
