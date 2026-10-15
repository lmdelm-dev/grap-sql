"""Line-by-line translation of the learner's actual query."""
from __future__ import annotations

from sqlschool.engine.explain import explain_sql, plain_translation, statement_kind


def test_explain_returns_word_lines():
    steps = explain_sql("SELECT name, price FROM products WHERE price > 100;")
    assert steps
    for s in steps:
        assert s["word"] and s["english"]


def test_plain_translation_mentions_key_parts():
    text = plain_translation(
        "SELECT name FROM customers WHERE city = 'Marrakech';")
    low = text.lower()
    assert "name" in low
    assert "customers" in low
    assert "marrakech" in low


def test_statement_kinds():
    assert statement_kind("SELECT * FROM x") == "select"
    assert statement_kind("INSERT INTO x VALUES (1)") == "insert"
    assert statement_kind("UPDATE x SET a = 1") == "update"
    assert statement_kind("DELETE FROM x") == "delete"
    assert statement_kind("CREATE TABLE x (a TEXT)") == "create"


def test_explain_insert():
    steps = explain_sql("INSERT INTO products (name, price) VALUES ('X', 1);")
    assert any("insert" in s["word"].lower() or "add" in s["english"].lower()
               for s in steps)


def test_explain_join_mentions_connection():
    steps = explain_sql(
        "SELECT p.name, c.name FROM products p JOIN categories c "
        "ON p.category_id = c.id;")
    all_text = " ".join(s["english"] for s in steps).lower()
    assert "connect" in all_text