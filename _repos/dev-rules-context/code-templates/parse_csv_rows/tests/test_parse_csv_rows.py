"""Tests for code-templates/parse_csv_rows."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from parse_csv_rows import run  # noqa: E402


def test_header_rows():
    out = run({"csv_text": "name,email\nAlice,alice@example.com\nBob,bob@example.com\n"})
    assert out["headers"] == ["name", "email"]
    assert out["rows"] == [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
    ]
    assert out["row_count"] == 2
    assert out["truncated"] is False


def test_semicolon_delimiter_and_trim():
    out = run({"csv_text": "name; email\n Alice ; alice@example.com \n", "delimiter": ";"})
    assert out["headers"] == ["name", "email"]
    assert out["rows"] == [{"name": "Alice", "email": "alice@example.com"}]
    assert out["delimiter"] == ";"


def test_no_header_generates_column_names():
    out = run({"csv_text": "Alice,alice@example.com\nBob,bob@example.com\n", "has_header": False})
    assert out["headers"] == ["column_1", "column_2"]
    assert out["rows"][0] == {"column_1": "Alice", "column_2": "alice@example.com"}


def test_duplicate_and_blank_headers_are_stable():
    out = run({"csv_text": "name,name,\nAlice,A.,extra\n"})
    assert out["headers"] == ["name", "name_2", "column_3"]
    assert out["rows"] == [{"name": "Alice", "name_2": "A.", "column_3": "extra"}]


def test_missing_cells_are_empty_strings():
    out = run({"csv_text": "name,email,role\nAlice,alice@example.com\n"})
    assert out["rows"] == [{"name": "Alice", "email": "alice@example.com", "role": ""}]


def test_max_rows_truncates():
    out = run({"csv_text": "n\n1\n2\n3\n", "max_rows": 2})
    assert out["rows"] == [{"n": "1"}, {"n": "2"}]
    assert out["row_count"] == 2
    assert out["truncated"] is True


def test_empty_csv():
    assert run({"csv_text": ""}) == {
        "headers": [],
        "rows": [],
        "row_count": 0,
        "delimiter": ",",
        "truncated": False,
    }


def test_type_errors():
    with pytest.raises(TypeError):
        run({"csv_text": 123})
    with pytest.raises(TypeError):
        run({"csv_text": "", "has_header": "yes"})
    with pytest.raises(ValueError):
        run({"csv_text": "", "delimiter": "::"})
