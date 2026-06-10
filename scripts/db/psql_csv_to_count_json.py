#!/usr/bin/env python3
"""Convert psql --csv object count output into JSON rows."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


def convert_csv_text(csv_text: str) -> dict[str, Any]:
    rows = []
    for row in csv.DictReader(csv_text.splitlines()):
        normalized = dict(row)
        if "row_count" in normalized:
            normalized["row_count"] = int(normalized["row_count"])
        rows.append(normalized)
    return {"rows": rows}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert psql --csv count output to JSON.")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    payload = convert_csv_text(sys.stdin.read())
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
