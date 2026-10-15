"""The sandbox: safe execution against a throw-away in-memory shop copy."""
from __future__ import annotations

import pytest

from sqlschool.db import sandbox as sbmod
from sqlschool.db.sandbox import Sandbox


def test_basic_select(sandbox):
    res = sandbox.run("SELECT name FROM products LIMIT 3;")
    assert res.ok
    assert res.kind == "select"
    assert res.columns == ["name"]
    assert len(res.rows) == 3
    assert "3 rows" in res.message


def test_known_facts(sandbox):
    assert sandbox.scalar("SELECT count(*) FROM products") == 40
    assert sandbox.scalar("SELECT count(*) FROM customers") == 30
    assert sandbox.scalar("SELECT count(*) FROM sales") == 45
    assert sandbox.scalar(
        "SELECT count(*) FROM products WHERE price > 100") == 21
    # a never-sold product
    res = sandbox.run(
        "SELECT p.name FROM products p LEFT JOIN sale_items si "
        "ON si.product_id = p.id WHERE si.sale_id IS NULL LIMIT 1")
    assert res.ok and res.rows[0][0] == "Picholine Olive Oil 1L"


def test_dml_returns_modify_result(sandbox):
    res = sandbox.run("INSERT INTO products (name, price, category_id) "
                      "VALUES ('X', 1.0, 1);")
    assert res.ok
    assert res.kind == "modify"
    assert res.state is not None
    assert sandbox.scalar("SELECT count(*) FROM products") == 41


def test_reset_restores_original(sandbox):
    sandbox.run("UPDATE products SET stock = 0 WHERE id = 2;")
    sandbox.run("DELETE FROM sale_items WHERE quantity >= 9;")
    sandbox.reset()
    assert sandbox.scalar("SELECT count(*) FROM products") == 40
    assert sandbox.scalar("SELECT count(*) FROM sale_items") == 111
    # product 2's original stock is 3 in the pristine shop
    assert sandbox.scalar("SELECT stock FROM products WHERE id = 2") == 3


def test_attach_is_denied(sandbox):
    res = sandbox.run("ATTACH DATABASE ':memory:' AS other;")
    assert not res.ok
    assert "can't open other files" in res.message.lower() or "attach" in res.message.lower()


def test_dangerous_pragma_is_denied(sandbox):
    res = sandbox.run("PRAGMA journal_mode=WAL;")
    assert not res.ok
    assert "so I've kept it out" in res.message


def test_safe_pragma_is_allowed(sandbox):
    res = sandbox.run("PRAGMA table_info(products);")
    assert res.ok
    assert any("id" in str(r[1]) for r in res.rows)


def test_load_extension_is_denied(sandbox):
    res = sandbox.run("SELECT load_extension('x');")
    assert not res.ok


def test_empty_sql(sandbox):
    res = sandbox.run("   ")
    assert not res.ok
    assert "nothing to run" in res.message


def test_multiple_statements_run_and_report_last(sandbox):
    res = sandbox.run(
        "INSERT INTO products (name, price, category_id) VALUES ('A', 1, 1); "
        "SELECT count(*) FROM products;")
    assert res.ok
    assert res.statements == 2
    assert res.rows[0][0] == 41


def test_semicolon_inside_string_is_not_a_split(sandbox):
    res = sandbox.run(
        "INSERT INTO products (name, price, category_id) VALUES ('a;b', 2, 1); "
        "SELECT count(*) FROM products;")
    assert res.ok
    assert res.statements == 2
    assert res.rows[0][0] == 41


def test_row_cap(sandbox):
    capped = Sandbox(row_cap=5)
    res = capped.run("SELECT * FROM products;")
    assert res.truncated
    assert len(res.rows) == 5
    capped.close()


def test_timeout_aborts_long_query():
    sb = Sandbox(time_ms=120)
    res = sb.run(
        "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM c "
        "WHERE x < 1000000000) SELECT count(*) FROM c;")
    assert not res.ok
    assert "taking a long time" in res.message
    sb.close()


def test_unknown_table_error_is_friendly(sandbox):
    res = sandbox.run("SELECT * FROM produts;")
    assert not res.ok
    assert "produts" in res.message
    assert "products" in res.message  # spelling suggestion


def test_split_statements_handles_quotes_and_comments():
    sql = """-- header comment
    INSERT INTO t (v) VALUES ('x;y');  /* block ; comment */
    SELECT 'a;b' AS t;
    """
    parts = sbmod._split_statements(sql)
    assert len(parts) == 2
    assert "INSERT" in parts[0]
    assert "SELECT" in parts[1]


def test_connection_is_in_memory_not_a_file(sandbox):
    res = sandbox.run("PRAGMA database_list;")
    assert res.ok
    # the main database's filename is empty for a true :memory: database
    assert res.rows[0][2] == ""