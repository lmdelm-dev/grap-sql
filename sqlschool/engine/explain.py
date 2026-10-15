"""Explain My Query.

Takes the SQL the learner actually typed and turns it into plain English,
one piece at a time.  Uses sqlglot (offline) to understand the structure;
if the query can't be understood we say so instead of guessing.
"""
from __future__ import annotations

import re

import sqlglot
import sqlglot.expressions as exp


def _condition(node) -> str:
    """A plain-English phrase for one WHERE-style condition."""
    if isinstance(node, exp.And):
        return "%s AND %s" % (_condition(node.left), _condition(node.right))
    if isinstance(node, exp.Or):
        return "%s OR %s" % (_condition(node.left), _condition(node.right))
    if isinstance(node, exp.Not):
        return "not (%s)" % _condition(node.this)
    if isinstance(node, exp.Paren):
        return "(%s)" % _condition(node.this)
    if isinstance(node, exp.Between):
        return "%s is between %s and %s" % (
            _column(node.this), _value(node.args.get("low")), _value(node.args.get("high")))
    if isinstance(node, exp.In):
        values = ", ".join(_value(v) for v in node.expressions)
        return "%s is one of: %s" % (_column(node.this), values)
    if isinstance(node, exp.Like):
        return "%s is like the pattern %s" % (_column(node.this), _value(node.expression))
    if isinstance(node, exp.Is):
        return "%s is %s" % (_column(node.this),
                             "missing (NULL)" if isinstance(node.expression, exp.Null) else _value(node.expression))
    if isinstance(node, exp.EQ):
        left, right = _operand(node.this), _operand(node.expression)
        return "%s equals %s" % (left, right)
    if isinstance(node, exp.NEQ):
        return "%s is not %s" % (_operand(node.this), _operand(node.expression))
    if isinstance(node, exp.GT):
        return "%s is bigger than %s" % (_operand(node.this), _operand(node.expression))
    if isinstance(node, exp.GTE):
        return "%s is %s or more" % (_operand(node.this), _operand(node.expression))
    if isinstance(node, exp.LT):
        return "%s is smaller than %s" % (_operand(node.this), _operand(node.expression))
    if isinstance(node, exp.LTE):
        return "%s is %s or less" % (_operand(node.this), _operand(node.expression))
    return "some condition on " + str(node)[:30]


def _operand(node) -> str:
    # check for arithmetic like quantity * price
    if isinstance(node, exp.Mul):
        return "%s times %s" % (_operand(node.left), _operand(node.right))
    if isinstance(node, exp.Add):
        return "%s plus %s" % (_operand(node.left), _operand(node.right))
    if isinstance(node, exp.Sub):
        return "%s minus %s" % (_operand(node.left), _operand(node.right))
    return _column(node)


def _column(node) -> str:
    if isinstance(node, exp.Column):
        name = node.name
        table = node.table
        return "%s.%s" % (table, name) if table else name
    if isinstance(node, exp.Alias):
        return "%s" % _column(node.this)
    if isinstance(node, exp.Literal):
        return _value(node)
    if isinstance(node, exp.AggFunc):
        return _aggregate(node)
    if isinstance(node, (exp.Count, exp.Sum, exp.Avg, exp.Max, exp.Min)):
        return _aggregate(node)
    if isinstance(node, exp.Func):
        return "%s(...)" % node.sql_name()
    if isinstance(node, exp.Window):
        return "a window result over %s" % node.this.sql_name()
    return str(node)[:24]


def _aggregate(node) -> str:
    name = node.sql_name().lower()
    if name == "count":
        this = node.this
        if this is None:
            return "count of rows"
        if isinstance(this, exp.Star) or this is None:
            return "count of rows"
        if isinstance(this, exp.Distinct):
            return "count of distinct %s values" % _column(this.this)
        return "count of %s" % _column(this)
    if name == "sum":
        return "total of %s" % _column(node.this)
    if name == "avg":
        return "average of %s" % _column(node.this)
    if name == "max":
        return "biggest %s" % _column(node.this)
    if name == "min":
        return "smallest %s" % _column(node.this)
    return "%s of %s" % (name, _column(node.this))


def _value(node) -> str:
    if node is None:
        return "something"
    if isinstance(node, exp.Literal):
        return str(node.this) if isinstance(node.this, str) else str(node.this)
    if isinstance(node, exp.Null):
        return "missing (NULL)"
    if isinstance(node, exp.Distinct):
        return "distinct"
    if isinstance(node, exp.Star):
        return "*"
    return _column(node)


def _order_direction(node) -> str:
    if isinstance(node, exp.Ordered):
        if node.args.get("desc"):
            return "biggest first"
        return "smallest first"
    if node.args.get("desc"):
        return "from biggest to smallest"
    return "from smallest to biggest"


def _order_item(node) -> str:
    if isinstance(node, exp.Ordered):
        return "%s, %s" % (_column(node.this), _order_direction(node))
    return "%s, %s" % (_column(node), _order_direction(node))


def explain_sql(sql: str) -> list[dict]:
    """Return a list of steps: {word, english, detail?} for a SELECT-family query.

    Empty list means "I can't understand this yet" - callers say so kindly.
    """
    try:
        parsed = sqlglot.parse_one(sql, read="sqlite")
    except Exception:
        return []
    if parsed is None:
        return []

    steps: list[dict] = []

    # sqlglot returns a Block for multi-statement SQL; explain each part.
    if isinstance(parsed, exp.Block):
        for stmt in parsed.expressions:
            _explain_one(stmt, steps)
        return steps

    _explain_one(parsed, steps)
    return steps


def _explain_one(parsed, steps: list[dict]) -> None:
    if isinstance(parsed, exp.Select):
        _explain_select(parsed, steps)
    elif isinstance(parsed, exp.Insert):
        steps.append({"word": "INSERT", "english": "add a new row to a table"})
        steps.append({"word": "INTO",
                      "english": "to the %s table" % _table(parsed.args.get("this"))})
        cols = parsed.args.get("columns")
        if cols:
            names = ", ".join(c.name for c in cols)
            steps.append({"word": "columns", "english": "filling in the columns: %s" % names})
        sel = parsed.args.get("expression")
        if isinstance(sel, exp.Select) and sel.args.get("expressions"):
            vals = ", ".join(_value(e) for e in sel.expressions)
            steps.append({"word": "VALUES", "english": "with the values: %s" % vals})
        elif parsed.args.get("expressions"):
            vals = ", ".join(_value(e) for e in parsed.args["expressions"])
            steps.append({"word": "VALUES", "english": "with the values: %s" % vals})
    elif isinstance(parsed, exp.Update):
        steps.append({"word": "UPDATE", "english": "change some rows"})
    elif isinstance(parsed, exp.Delete):
        steps.append({"word": "DELETE", "english": "remove some rows"})
    elif isinstance(parsed, exp.Create):
        steps.append({"word": "CREATE", "english": "build a new table"})
    elif isinstance(parsed, exp.Drop):
        steps.append({"word": "DROP", "english": "remove a table"})
    else:
        steps.append({"word": getattr(parsed, "sql_name", lambda: "…")(), "english": "…"})


def _table(node) -> str:
    if isinstance(node, exp.Table):
        return node.name
    if isinstance(node, exp.From):
        t = node.this
        if isinstance(t, exp.Table):
            return t.name
    if isinstance(node, exp.Alias):
        return _table(node.this)
    if node is None:
        return "some table"
    return str(node)[:24]


def _explain_select(select, steps: list[dict]) -> None:
    # CTEs come first
    withs = select.args.get("with")
    if withs:
        for cte in withs.expressions:
            name = cte.alias
            steps.append({"word": "WITH",
                          "english": "first build a temporary list called %s" % name})
            steps.append({"word": "AS",
                          "english": "from a smaller query we reuse below"})

    projects = select.args.get("expressions") or []
    plain = [p for p in projects if not isinstance(p, exp.Window)]
    for proj in projects:
        if isinstance(proj, exp.Window):
            steps.append({"word": "window function",
                          "english": "%s - a running total/rank that looks at rows around each row"
                          % _column(proj.this if proj.this is not None else proj)})
    if plain:
        phrases = [_column(p) for p in plain]
        if len(phrases) == 1:
            steps.append({"word": "SELECT", "english": "show one thing: %s" % phrases[0]})
        else:
            steps.append({"word": "SELECT",
                          "english": "show these columns: %s" % ", then ".join(phrases)})
    else:
        steps.append({"word": "SELECT", "english": "show…"})

    src = select.args.get("from_") or select.args.get("from")
    if src:
        _explain_from(src, steps)

    joins = select.args.get("joins") or []
    for join in joins:
        kind = (join.args.get("kind") or "").lower()
        on = join.args.get("on")
        how = "connect" if kind in ("", "inner") else {
            "left": "connect, keeping every row on the left even if unmatched",
            "right": "connect, keeping every row on the right even if unmatched",
            "full": "connect, keeping both sides even if unmatched",
            "cross": "connect every row with every other row",
        }.get(kind, "connect")
        table = _table(join.this)
        msg = "%s with the %s table" % (how, table)
        if on is not None:
            msg += ", matching %s" % _condition(on)
        steps.append({"word": (kind or "JOIN").upper(), "english": msg})

    where = select.args.get("where")
    if where:
        steps.append({"word": "WHERE",
                      "english": "keep only the rows where %s" % _condition(where.this)})

    group = select.args.get("group")
    if group:
        cols = ", ".join(_column(e) for e in group.expressions)
        steps.append({"word": "GROUP BY",
                      "english": "bundle the rows into groups that share the same %s" % cols})

    having = select.args.get("having")
    if having:
        steps.append({"word": "HAVING",
                      "english": "keep only the groups where %s" % _condition(having.this)})

    order = select.args.get("order")
    if order:
        items = ", ".join(_order_item(e) for e in order.expressions)
        steps.append({"word": "ORDER BY", "english": "sort the rows by: %s" % items})

    limit = select.args.get("limit")
    if limit:
        n = limit.expression if isinstance(limit, exp.Limit) else limit
        steps.append({"word": "LIMIT", "english": "show only the first %s rows" % _value(n)})


def _explain_from(from_node, steps: list[dict]) -> None:
    this = from_node.this
    if isinstance(this, exp.Table):
        steps.append({"word": "FROM", "english": "from the %s table" % this.name})
    elif isinstance(this, exp.Select):
        steps.append({"word": "FROM", "english": "from a smaller query (a sub-query)"})
        _explain_select(this, steps)
    elif isinstance(this, exp.Subquery):
        steps.append({"word": "FROM", "english": "from a smaller query"})
        _explain_select(this.this, steps)
    else:
        steps.append({"word": "FROM", "english": "from %s" % _table(this)})


def plain_translation(sql: str) -> str:
    """A single friendly sentence for the whole query."""
    lines = explain_sql(sql)
    if not lines:
        return ""
    def key(l):
        order = {"SELECT":0,"FROM":1,"JOIN":2,"WHERE":3,"GROUP BY":4,"HAVING":5,"ORDER BY":6,"LIMIT":7}
        return order.get(l["word"], 50)
    ordered = sorted(lines, key=key)
    seen = set()
    text = []
    for l in ordered:
        eng = l["english"]
        if eng in seen:
            continue
        seen.add(eng)
        text.append(eng.capitalize())
    return " ".join(text) + "."


def statement_kind(sql: str) -> str:
    """'select' | 'insert' | 'update' | 'delete' | 'create' | 'drop' | 'other'"""
    try:
        parsed = sqlglot.parse_one(sql, read="sqlite")
    except Exception:
        parsed = None
    if parsed is None:
        first = sql.lstrip().split(None, 1)[0].lower()
        return {"insert": "insert", "update": "update", "delete": "delete",
                "create": "create", "drop": "drop", "alter": "alter"}.get(first, "other")
    if isinstance(parsed, exp.Select):
        return "select"
    if isinstance(parsed, exp.Insert):
        return "insert"
    if isinstance(parsed, exp.Update):
        return "update"
    if isinstance(parsed, exp.Delete):
        return "delete"
    if isinstance(parsed, exp.Create):
        return "create"
    if isinstance(parsed, exp.Drop):
        return "drop"
    return "other"