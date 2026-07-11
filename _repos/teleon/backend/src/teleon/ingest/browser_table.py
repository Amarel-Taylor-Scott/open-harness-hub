"""Reusable browser/table ingestion primitives.

These primitives are intentionally small and edge-described so AIDevObserver
can reuse them without handing a coding harness the full implementation. The
browser fetch uses Playwright when it is installed, and otherwise falls back to
stdlib HTTP fetch for static pages.
"""
from __future__ import annotations

import csv
import html
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path


HtmlRow = dict[str, str]


@dataclass(frozen=True, slots=True)
class HtmlTable:
    """One extracted HTML table."""

    headers: tuple[str, ...]
    rows: tuple[HtmlRow, ...]


def fetch_page_html_with_playwright(url: str, *, timeout_ms: int = 30_000) -> str:
    """Fetch page HTML, preferring Playwright for browser-rendered pages."""

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        request = urllib.request.Request(url, headers={"User-Agent": "AIDevObserver/1.0"})
        with urllib.request.urlopen(request, timeout=max(1, timeout_ms / 1000)) as response:
            return response.read().decode("utf-8", errors="replace")

    with sync_playwright() as browser_api:
        browser = browser_api.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            return page.content()
        finally:
            browser.close()


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.tables: list[HtmlTable] = []
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._cell_chunks: list[str] = []
        self._current_row: list[str] = []
        self._rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001 - HTMLParser signature
        if tag == "table":
            self._in_table = True
            self._rows = []
        elif self._in_table and tag == "tr":
            self._in_row = True
            self._current_row = []
        elif self._in_table and self._in_row and tag in {"td", "th"}:
            self._in_cell = True
            self._cell_chunks = []

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_chunks.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._in_cell:
            self._cell_chunks.append(html.unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        if self._in_cell:
            self._cell_chunks.append(html.unescape(f"&#{name};"))

    def handle_endtag(self, tag: str) -> None:
        if self._in_table and self._in_row and self._in_cell and tag in {"td", "th"}:
            value = " ".join("".join(self._cell_chunks).split())
            self._current_row.append(value)
            self._in_cell = False
        elif self._in_table and self._in_row and tag == "tr":
            if self._current_row:
                self._rows.append(self._current_row)
            self._in_row = False
        elif self._in_table and tag == "table":
            table = _rows_to_table(self._rows)
            if table.rows:
                self.tables.append(table)
            self._in_table = False


def _rows_to_table(rows: list[list[str]]) -> HtmlTable:
    if not rows:
        return HtmlTable(headers=(), rows=())
    max_width = max(len(row) for row in rows)
    raw_headers = rows[0] if rows[0] else []
    headers = tuple(
        (raw_headers[index] if index < len(raw_headers) and raw_headers[index] else f"column_{index + 1}")
        for index in range(max_width)
    )
    records: list[HtmlRow] = []
    for row in rows[1:]:
        records.append({
            headers[index]: row[index] if index < len(row) else ""
            for index in range(max_width)
        })
    return HtmlTable(headers=headers, rows=tuple(records))


def extract_html_tables(document: str) -> list[HtmlTable]:
    """Extract HTML tables into row dictionaries."""

    parser = _TableParser()
    parser.feed(document)
    return parser.tables


def write_table_csv(table: HtmlTable, path: Path) -> Path:
    """Persist one extracted table as CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table.headers))
        writer.writeheader()
        writer.writerows(table.rows)
    return path


def write_table_parquet(table: HtmlTable, path: Path) -> Path:
    """Persist one extracted table as Parquet using pandas/pyarrow."""

    try:
        import pandas as pd  # type: ignore
    except ImportError as exc:
        raise RuntimeError("write_table_parquet requires pandas and a parquet engine such as pyarrow") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(list(table.rows), columns=list(table.headers)).to_parquet(path, index=False)
    return path
