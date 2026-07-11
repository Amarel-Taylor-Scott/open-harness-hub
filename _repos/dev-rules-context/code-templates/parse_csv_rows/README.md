# parse_csv_rows

Deterministic CSV text parser for agent workflows that need structured rows
without spending model tokens on parsing.

## Contract

Input:

```json
{
  "csv_text": "name,email\nAlice,alice@example.com\n",
  "delimiter": ",",
  "has_header": true,
  "trim_whitespace": true,
  "max_rows": 100
}
```

Output:

```json
{
  "headers": ["name", "email"],
  "rows": [{"name": "Alice", "email": "alice@example.com"}],
  "row_count": 1,
  "delimiter": ",",
  "truncated": false
}
```

## Behavior

- Uses Python's stdlib `csv` parser.
- Preserves input row order.
- Pads missing cells with empty strings.
- Deduplicates repeated headers with numeric suffixes.
- Uses generated `column_N` names when `has_header` is false.
- Returns JSON-compatible dictionaries only.

## Why this exists

AI coding agents frequently regenerate CSV parsing helpers while building
importers, ETL flows, document review tools, and benchmark loaders. This
template gives AIDevObserver a concrete deterministic component to suggest
instead of letting the agent rebuild a parser and debug edge cases again.
