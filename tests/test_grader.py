"""The grader: result-based grading that is fair to many valid answers."""
from __future__ import annotations

from sqlschool.engine.grader import (
    compare_select,
    compare_state,
    compare_state_contains,
)


def test_equal_rows_pass_in_any_order():
    v = compare_select(["a", "b"], [(1, "x"), (2, "y")],
                       ["a", "b"], [(2, "y"), (1, "x")])
    assert v.passed


def test_column_names_may_differ_aliases():
    v = compare_select(["price"], [(13.5,)],
                       ["p"], [(13.5,)])
    assert v.passed


def test_column_count_mismatch_fails():
    v = compare_select(["a"], [(1,)], ["a", "b"], [(1, 2)])
    assert not v.passed
    assert "columns" in v.detail


def test_float_tolerance():
    v = compare_select(["price"], [(13.5,)],
                       ["price"], [(13.5000001,)])
    assert v.passed


def test_nulls_are_values_not_empty_strings():
    a = compare_select(["x"], [(None,)], ["x"], [("",)])
    assert not a.passed
    b = compare_select(["x"], [(None,)], ["x"], [(None,)])
    assert b.passed


def test_row_count_mismatch_fails_helpfully():
    v = compare_select(["a"], [(1,), (2,)], ["a"], [(1,)])
    assert not v.passed
    assert "row" in v.detail


def test_same_rows_any_order_passes_even_ordered_reference():
    v = compare_select(["name"], [("b",), ("a",)],
                       ["name"], [("a",), ("b",)],
                       reference_sql="SELECT name FROM t ORDER BY name;")
    assert v.passed
    # …but genuinely different rows still fail
    v2 = compare_select(["name"], [("a",), ("c",)],
                        ["name"], [("a",), ("b",)],
                        reference_sql="SELECT name FROM t ORDER BY name;")
    assert not v2.passed


def test_duplicate_rows_are_not_ignored():
    v = compare_select(["n"], [(1,), (1,)], ["n"], [(1,)])
    assert not v.passed


def test_no_rows_on_both_sides_is_a_pass():
    v = compare_select(["a"], [], ["a"], [])
    assert v.passed


def test_state_equal_passes_unequal_fails():
    ref = {"products": ((1, "x"), (2, "y")), "sales": ()}
    same = {"products": ((1, "x"), (2, "y")), "sales": ()}
    assert compare_state(same, ref).passed
    diff = {"products": ((1, "z"), (2, "y")), "sales": ()}
    assert not compare_state(diff, ref).passed


def test_compare_state_contains_delegates():
    ref = {"products": ((1, "x"),)}
    assert compare_state_contains({"products": ((1, "x"),)}, ref).passed