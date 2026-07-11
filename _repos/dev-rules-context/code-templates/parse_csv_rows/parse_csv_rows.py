"""Parse CSV text into deterministic row dictionaries.

Contract: see input.schema.json / output.schema.json.
Token cost: 0 (Python stdlib csv parser).
"""
from __future__ import annotations

import csv
import io
from typing import Any


def _bool_input(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise TypeError(f"expected boolean option, got {type(value).__name__}")


def _delimiter_input(value: Any) -> str:
    if value is None:
        return ","
    if not isinstance(value, str):
        raise TypeError(f"expected delimiter: str, got {type(value).__name__}")
    if len(value) != 1:
        raise ValueError("delimiter must be exactly one character")
    return value


def _max_rows_input(value: Any) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"expected max_rows: int, got {type(value).__name__}")
    if value < 0:
        raise ValueError("max_rows must be non-negative")
    return value


def _dedupe_headers(headers: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out: list[str] = []
    for index, raw_header in enumerate(headers):
        header = raw_header if raw_header else f"column_{index + 1}"
        count = seen.get(header, 0) + 1
        seen[header] = count
        out.append(header if count == 1 else f"{header}_{count}")
    return out


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    """Parse `csv_text` into JSON-compatible row dictionaries.

    Args:
        inputs: {
            "csv_text": str,
            "delimiter": str = ",",
            "has_header": bool = True,
            "trim_whitespace": bool = True,
            "max_rows": int | None = None
        }

    Returns:
        {
            "headers": list[str],
            "rows": list[dict[str, str]],
            "row_count": int,
            "delimiter": str,
            "truncated": bool
        }
    """
    csv_text = inputs.get("csv_text", "")
    if not isinstance(csv_text, str):
        raise TypeError(f"expected csv_text: str, got {type(csv_text).__name__}")

    delimiter = _delimiter_input(inputs.get("delimiter"))
    has_header = _bool_input(inputs.get("has_header"), True)
    trim_whitespace = _bool_input(inputs.get("trim_whitespace"), True)
    max_rows = _max_rows_input(inputs.get("max_rows"))

    reader = csv.reader(io.StringIO(csv_text), delimiter=delimiter)
    raw_rows = list(reader)
    if not raw_rows:
        return {
            "headers": [],
            "rows": [],
            "row_count": 0,
            "delimiter": delimiter,
            "truncated": False,
        }

    if trim_whitespace:
        raw_rows = [[cell.strip() for cell in row] for row in raw_rows]

    if has_header:
        headers = _dedupe_headers(raw_rows[0])
        data_rows = raw_rows[1:]
    else:
        column_count = max((len(row) for row in raw_rows), default=0)
        headers = [f"column_{index + 1}" for index in range(column_count)]
        data_rows = raw_rows

    truncated = max_rows is not None and len(data_rows) > max_rows
    selected_rows = data_rows[:max_rows] if max_rows is not None else data_rows

    rows: list[dict[str, str]] = []
    for raw_row in selected_rows:
        row: dict[str, str] = {}
        for index, header in enumerate(headers):
            row[header] = raw_row[index] if index < len(raw_row) else ""
        rows.append(row)

    return {
        "headers": headers,
        "rows": rows,
        "row_count": len(rows),
        "delimiter": delimiter,
        "truncated": truncated,
    }


if __name__ == "__main__":
    import json
    import sys

    sample = sys.stdin.read() or "name,email\nAlice,alice@example.com\nBob,bob@example.com\n"
    print(json.dumps(run({"csv_text": sample}), indent=2, sort_keys=True))
