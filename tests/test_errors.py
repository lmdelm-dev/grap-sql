"""Friendly SQL error translation."""
from __future__ import annotations

from sqlschool.engine.errors import friendly_error, suggest, levenshtein


def test_levenshtein_and_suggest():
    assert levenshtein("cat", "cat") == 0
    assert levenshtein("cat", "cut") == 1
    assert suggest("produts", ["products", "customers"]) == "products"
    assert suggest("who", ["products"]) is None


def test_no_such_table_with_spelling_hint():
    msg = friendly_error("no such table: produts",
                         tables=["products", "customers"])
    assert "produts" in msg
    assert "products" in msg


def test_no_such_column():
    msg = friendly_error('no such column: nmae',
                         columns=["name", "price"])
    assert "nmae" in msg
    assert "name" in msg


def test_unterminated_string():
    msg = friendly_error("unterminated string")
    assert "quote" in msg.lower()


def test_near_keyword_help():
    msg = friendly_error('near "from": syntax error')
    assert "from" in msg and "recipe" in msg


def test_interrupted_friendly():
    msg = friendly_error("interrupted")
    assert "snappy" in msg


def test_unique_constraint():
    msg = friendly_error("UNIQUE constraint failed: products.id")
    assert "unique" in msg.lower()


def test_group_by_needed():
    msg = friendly_error("GROUP BY clause error")
    assert "GROUP BY" in msg or "group" in msg.lower()


def test_unknown_function():
    msg = friendly_error("no such function: cnunt")
    assert "cnunt" in msg
    assert "count" in msg