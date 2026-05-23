"""Tests for code-templates/extract_email."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from extract_email import run  # noqa: E402


def test_basic():
    out = run({"text": "Contact alice@example.com or bob@test.org."})
    assert sorted(out["emails"]) == ["alice@example.com", "bob@test.org"]
    assert out["count"] == 2


def test_dedup_case_insensitive():
    out = run({"text": "alice@example.com Alice@Example.COM"})
    # Original case of first occurrence preserved; dedup by lowercase.
    assert out["count"] == 1
    assert out["emails"][0] == "alice@example.com"


def test_empty():
    out = run({"text": ""})
    assert out == {"emails": [], "count": 0}


def test_no_emails():
    out = run({"text": "hello world. no addresses here."})
    assert out == {"emails": [], "count": 0}


def test_missing_text():
    out = run({})  # 'text' is optional — defaults to ""
    assert out == {"emails": [], "count": 0}


def test_type_error():
    import pytest
    with pytest.raises(TypeError):
        run({"text": 123})
