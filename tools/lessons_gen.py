"""Schema-driven exercise generator: thousands of coherent drill lessons.

Reads the *real* practice shop (tables, columns, foreign keys and actual
values) and writes themed lessons that teach one SQL feature at a time:
reading columns, filtering text and numbers, sorting, aggregates, grouping
and joins.

Every reference solution is executed while generating; a step is only kept
when its reference runs and returns rows.  Nothing broken can ship.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlschool.db.sandbox import Sandbox  # noqa: E402

LESSON_SIZE = 40
MAX_TOTAL = 10400

OP_WORDS = {
    ">": "bigger than",
    ">=": "at least",
    "<": "smaller than",
    "<=": "at most",
    "=": "exactly",
    "!=": "not equal to",
}

AGG_WORDS = {
    "count": "count how many rows",
    "sum": "add up the values",
    "avg": "work out the average",
    "min": "find the smallest value",
    "max": "find the biggest value",
}

NICK = {"products": "p", "categories": "c", "customers": "cu", "sales": "s",
        "sale_items": "si", "employees": "e", "suppliers": "su"}


def _lit(v) -> str:
    if isinstance(v, str):
        return "'" + v.replace("'", "''") + "'"
    return str(v)


def _h(a, b, c, d):
    return [a, b, c, d]


def _step(kind, title, prompt, task, sql, hints, *, trick="", real="", require=None):
    d = {
        "type": kind,
        "title": title,
        "prompt": prompt,
        "task": task,
        "hints": hints,
        "expected_sql": sql,
    }
    if trick:
        d["memory_trick"] = trick
    if real:
        d["real_life"] = real
    if require:
        d["check"] = {"require": require}
    return d


class _Book:
    def __init__(self) -> None:
        self.lessons: list[dict] = []
        self._seen: set = set()

    def add(self, title: str, tags: list[str], difficulty: int,
            steps: list[dict]) -> None:
        uniq = []
        for s in steps:
            key = (s["title"], s["expected_sql"])
            if key in self._seen:
                continue
            self._seen.add(key)
            uniq.append(s)
        for i in range(0, len(uniq), LESSON_SIZE):
            chunk = uniq[i:i + LESSON_SIZE]
            part = i // LESSON_SIZE + 1
            self.lessons.append({
                "title": title if part == 1 else "%s · part %d" % (title, part),
                "tags": tags,
                "difficulty": difficulty,
                "steps": chunk,
            })


# --------------------------------------------------------------------------
# schema helpers
# --------------------------------------------------------------------------
def _num_cols(info) -> list[str]:
    return [c["name"] for c in info["columns"] if c["type"] in ("INTEGER", "REAL")]


def _text_cols(info) -> list[str]:
    return [c["name"] for c in info["columns"] if c["type"] in ("TEXT", "")]


def _distinct(sb: Sandbox, table: str, col: str, cap: int = 45) -> list:
    res = sb.run(
        'SELECT DISTINCT "%s" FROM "%s" WHERE "%s" IS NOT NULL '
        'ORDER BY "%s" LIMIT %d' % (col, table, col, col, cap)
    )
    if res.ok and res.kind == "select":
        return [r[0] for r in res.rows]
    return []


def _valid(sb: Sandbox, sql: str) -> bool:
    res = sb.run(sql)
    if not res.ok:
        return False
    if res.kind == "select" and not res.rows:
        return False
    return True


# --------------------------------------------------------------------------
# families
# --------------------------------------------------------------------------
def _reading(sb, info, book) -> None:
    table = info["name"]
    cols = [c["name"] for c in info["columns"]]
    steps = []
    star = "SELECT * FROM %s;" % table
    if _valid(sb, star):
        steps.append(_step(
            "type", "Every column with *",
            "The star ( * ) means 'every column'.\n"
            "Here we open the whole %s table and take every column it has." % table,
            "Try typing: %s" % star, star,
            _h("Start with SELECT *.", "Then FROM %s." % table,
               "Finish with a semicolon ;", "Write: %s" % star),
            trick="* = all the columns, in table order."))
    for col in cols:
        sql = "SELECT %s FROM %s;" % (col, table)
        if not _valid(sb, sql):
            continue
        steps.append(_step(
            "type", "Read the %s column" % col,
            "SELECT chooses the COLUMNS you see.\n"
            "Ask for just the %s column from the %s table." % (col, table),
            "Try typing: %s" % sql, sql,
            _h("Start with SELECT %s." % col, "The table is %s." % table,
               "FROM names the table you read from.",
               "Write: %s" % sql),
            trick="You get back only the column you name."))
    if len(cols) >= 2:
        a, b = cols[0], cols[1]
        sql = "SELECT %s, %s FROM %s;" % (a, b, table)
        if _valid(sb, sql):
            steps.append(_step(
                "type", "Two columns at once",
                "List columns after SELECT, separated by commas.\n"
                "Here we ask for %s and %s together." % (a, b),
                "Try typing: %s" % sql, sql,
                _h("Start with SELECT %s," % a, "Add the second column %s." % b,
                   "FROM %s." % table, "Write: %s" % sql),
                trick="A comma says 'and also show me this'."))
    if len(cols) >= 3:
        c0, c1, c2 = cols[0], cols[1], cols[2]
        sql = "SELECT %s, %s, %s FROM %s;" % (c0, c1, c2, table)
        if _valid(sb, sql):
            steps.append(_step(
                "type", "Three columns",
                "More columns, same idea - just keep adding commas.",
                "Try typing: %s" % sql, sql,
                _h("Start with SELECT %s, %s," % (c0, c1),
                   "Add the third column %s." % c2, "Two commas in total.",
                   "Write: %s" % sql),
                trick="Three columns need two commas."))
    if steps:
        book.add("Reading the %s table" % table, ["select", "columns"], 1, steps)


def _text_filters(sb, info, book) -> None:
    table = info["name"]
    steps = []
    for col in _text_cols(info):
        values = _distinct(sb, table, col, cap=60)
        for v in values:
            lit = _lit(v)
            sql = "SELECT * FROM %s WHERE %s = %s;" % (table, col, lit)
            if not _valid(sb, sql):
                continue
            steps.append(_step(
                "type", "Keep rows where %s is %s" % (col, v),
                "WHERE is a sieve: only rows that pass the test stay.\n"
                "Text values wear quotes, like %s." % lit,
                "Try typing: %s" % sql, sql,
                _h("Start with SELECT * FROM %s." % table,
                   "Add WHERE %s = …" % col,
                   "Wrap the text value in single quotes.",
                   "Write: %s" % sql),
                trick="Text in quotes, numbers bare.",
                require=["where"]))
            first = str(v)[:3]
            like = "SELECT * FROM %s WHERE %s LIKE %s;" % (
                table, col, _lit(first + "%"))
            if first and _valid(sb, like):
                steps.append(_step(
                    "type", "Search with LIKE for names starting '%s'" % first,
                    "LIKE searches by pattern using the %% wildcard.\n"
                    "%s means 'starts with'." % (first + "%" if first else "%"),
                    "Try typing: %s" % like, like,
                    _h("Start with SELECT * FROM %s." % table,
                       "Add WHERE %s LIKE …" % col,
                       "The %% wildcard means 'anything after'.",
                       "Write: %s" % like),
                    trick="%% = 'any characters here'.",
                    require=["where"]))
            mid = str(v)[1:4]
            if len(str(v)) >= 4 and mid:
                contains = "SELECT * FROM %s WHERE %s LIKE %s;" % (
                    table, col, _lit("%" + mid + "%"))
                if _valid(sb, contains):
                    steps.append(_step(
                        "type", "Search with LIKE for '%s' anywhere" % mid,
                        "Putting %% on BOTH sides matches the text anywhere.\n"
                        "This %s means 'contains'." % ("%" + mid + "%"),
                        "Try typing: %s" % contains, contains,
                        _h("Start with SELECT * FROM %s." % table,
                           "Add WHERE %s LIKE …" % col,
                           "Wrap the text in %% on both sides.",
                           "Write: %s" % contains),
                        trick="%%word%% = 'found anywhere inside'.",
                        require=["where"]))
    if steps:
        book.add("Filtering the %s table by text" % table,
                 ["where", "text"], 2, steps)


def _number_filters(sb, info, book) -> None:
    table = info["name"]
    steps = []
    cols = [c["name"] for c in info["columns"]]
    show = cols[0]
    for col in _num_cols(info):
        values = _distinct(sb, table, col, cap=200)
        for v in values:
            for op in (">", ">=", "<", "<=", "=", "!="):
                cond = "%s %s %s" % (col, op, _lit(v))
                sql = "SELECT %s FROM %s WHERE %s;" % (show, table, cond)
                if not _valid(sb, sql):
                    continue
                steps.append(_step(
                    "type", "Keep %s %s %s" % (col, op, v),
                    "Numbers compare with small symbols:\n"
                    "  > bigger   < smaller   = exactly   != not equal\n"
                    "Keep the rows where %s is %s %s." % (col, OP_WORDS[op], v),
                    "Try typing: %s" % sql, sql,
                    _h("Start with SELECT %s FROM %s." % (show, table),
                       "Add WHERE after the table name.",
                       "The test is %s." % cond,
                       "Write: %s" % sql),
                    trick="WHERE keeps only the rows that pass the test.",
                    require=["where"]))
                csql = "SELECT count(*) FROM %s WHERE %s;" % (table, cond)
                if _valid(sb, csql):
                    steps.append(_step(
                        "type", "Count rows %s %s %s" % (col, op, v),
                        "COUNT(*) counts how many rows survive the filter.",
                        "Try typing: %s" % csql, csql,
                        _h("Start with SELECT count(*).", "FROM %s." % table,
                           "Add WHERE %s." % cond, "Write: %s" % csql),
                        trick="count(*) + WHERE = 'how many pass?'",
                        require=["where"]))
                osql = ("SELECT %s FROM %s WHERE %s ORDER BY %s LIMIT 3;"
                        % (show, table, cond, col))
                if show != col and _valid(sb, osql):
                    steps.append(_step(
                        "type", "Filter then sort: %s %s %s" % (col, op, v),
                        "Filter first, then ORDER BY tidies what is left.\n"
                        "LIMIT 3 keeps the top of that sorted list.",
                        "Try typing: %s" % osql, osql,
                        _h("Start with SELECT %s FROM %s." % (show, table),
                           "Add WHERE %s." % cond,
                           "Add ORDER BY %s LIMIT 3." % col,
                           "Write: %s" % osql),
                        trick="WHERE trims, ORDER BY sorts, LIMIT cuts.",
                        require=["where", "order by", "limit"]))
    if steps:
        book.add("Filtering the %s table by numbers" % table,
                 ["where", "comparison"], 2, steps)


def _sorting(sb, info, book) -> None:
    table = info["name"]
    cols = [c["name"] for c in info["columns"]]
    steps = []
    for col in cols:
        for direction, word in (("", "smallest first"), ("DESC", "biggest first")):
            sql = "SELECT %s FROM %s ORDER BY %s %s;" % (col, table, col, direction)
            sql = sql.replace("  ", " ")
            if not _valid(sb, sql):
                continue
            steps.append(_step(
                "type", "Sort %s %s" % (col, word),
                "ORDER BY puts rows in a tidy line.\n"
                "Add DESC to flip from smallest-first to biggest-first.",
                "Try typing: %s" % sql, sql,
                _h("Start with SELECT %s FROM %s." % (col, table),
                   "Add ORDER BY %s." % col,
                   "Add DESC for biggest-first (leave it out for smallest).",
                   "Write: %s" % sql),
                trick="DESC = descending = biggest on top.",
                require=["order by"]))
        for n in (1, 3, 5, 10):
            sql = "SELECT %s FROM %s ORDER BY %s DESC LIMIT %d;" % (col, table, col, n)
            if not _valid(sb, sql):
                continue
            steps.append(_step(
                "type", "Top %d by %s" % (n, col),
                "LIMIT cuts the list after N rows.\n"
                "Sort first, then keep only %d." % n,
                "Try typing: %s" % sql, sql,
                _h("Start with SELECT %s FROM %s." % (col, table),
                   "Add ORDER BY %s DESC." % col,
                   "Finish with LIMIT %d." % n, "Write: %s" % sql),
                trick="ORDER BY then LIMIT = a top-N chart.",
                require=["order by", "limit"]))
        dsq = "SELECT DISTINCT %s FROM %s ORDER BY %s;" % (col, table, col)
        if _valid(sb, dsq) and sb.run(dsq).rows:
            steps.append(_step(
                "type", "The distinct values of %s" % col,
                "DISTINCT removes duplicate rows from the result.\n"
                "It answers 'which different %s values exist?'" % col,
                "Try typing: %s" % dsq, dsq,
                _h("Start with SELECT DISTINCT %s." % col,
                   "FROM %s." % table, "Add ORDER BY %s to sort them." % col,
                   "Write: %s" % dsq),
                trick="DISTINCT = 'each value only once'.",
                require=["distinct"]))
    if steps:
        book.add("Sorting and trimming the %s table" % table,
                 ["order by", "limit"], 2, steps)


def _aggregates(sb, info, book) -> None:
    table = info["name"]
    cols = [c["name"] for c in info["columns"]]
    steps = []
    sql = "SELECT count(*) FROM %s;" % table
    if _valid(sb, sql):
        steps.append(_step(
            "type", "How many rows in %s?" % table,
            "COUNT(*) answers 'how many rows?' with one number.",
            "Try typing: %s" % sql, sql,
            _h("Start with SELECT count(*).", "FROM %s." % table,
               "Finish with a semicolon.", "Write: %s" % sql),
            trick="count(*) = 'how many rows?'"))
    for col in cols:
        csql = "SELECT count(%s) FROM %s;" % (col, table)
        if _valid(sb, csql):
            steps.append(_step(
                "type", "Count the %s values" % col,
                "COUNT(column) counts rows where that column is not empty "
                "(it skips NULLs).",
                "Try typing: %s" % csql, csql,
                _h("Start with SELECT count(%s)." % col, "FROM %s." % table,
                   "Empty values (NULL) are skipped.", "Write: %s" % csql),
                trick="COUNT(column) skips NULLs; COUNT(*) skips nothing."))
    for col in _num_cols(info):
        for fn in ("sum", "avg", "min", "max"):
            sql = "SELECT %s(%s) FROM %s;" % (fn, col, table)
            if not _valid(sb, sql):
                continue
            steps.append(_step(
                "type", "%s of %s" % (fn.upper(), col),
                "%s %s: %s." % (fn.upper(), col, AGG_WORDS[fn]),
                "Try typing: %s" % sql, sql,
                _h("Start with SELECT %s(%s)." % (fn, col), "FROM %s." % table,
                   "%s works on numbers." % fn.upper(), "Write: %s" % sql),
                trick="%s = %s." % (fn, AGG_WORDS[fn])))
    if steps:
        book.add("Counting and totals in %s" % table,
                 ["aggregate", "count"], 3, steps)


def _grouping(sb, info, book) -> None:
    table = info["name"]
    num = _num_cols(info)
    group_cols = [c["name"] for c in info["columns"]
                  if c["name"].endswith("_id") or c["name"] in ("city", "role", "name")]
    steps = []
    for g in group_cols[:3]:
        for fn, target in [("count", "*")] + [(f, c) for c in num[:3] for f in ("sum", "avg")]:
            sql = "SELECT %s, %s(%s) FROM %s GROUP BY %s;" % (g, fn, target, table, g)
            if not _valid(sb, sql):
                continue
            steps.append(_step(
                "type", "%s per %s" % (fn.upper(), g),
                "GROUP BY bundles rows into piles that share the same %s.\n"
                "Then %s(%s) works on each pile." % (g, fn, target),
                "Try typing: %s" % sql, sql,
                _h("Start with SELECT %s, %s(%s)." % (g, fn, target),
                   "FROM %s." % table, "Finish with GROUP BY %s." % g,
                   "Write: %s" % sql),
                trick="GROUP BY = one output row per pile.",
                require=["group by"]))
        for v in _distinct(sb, table, g, cap=12):
            sql = ("SELECT %s, count(*) FROM %s GROUP BY %s HAVING %s = %s;"
                   % (g, table, g, g, _lit(v)))
            if not _valid(sb, sql):
                continue
            steps.append(_step(
                "type", "Just the %s pile (%s)" % (g, v),
                "HAVING filters the piles after they are built - WHERE filters "
                "rows before.",
                "Try typing: %s" % sql, sql,
                _h("Build the piles with GROUP BY %s." % g,
                   "Add HAVING to keep one pile.",
                   "The test is %s = %s." % (g, _lit(v)), "Write: %s" % sql),
                trick="WHERE filters rows; HAVING filters piles.",
                require=["group by"]))
    if steps:
        book.add("Grouping the %s table" % table,
                 ["group by", "having"], 3, steps)


def _joins(sb, book) -> None:
    steps = []
    for info in sb.schema:
        child = info["name"]
        for fk in info.get("foreign_keys", []):
            parent = fk["table"]
            col, pcol = fk["from"], fk["to"]
            n1, n2 = NICK.get(child, "a"), NICK.get(parent, "b")
            proj = ("SELECT %s.%s, %s.%s FROM %s %s JOIN %s %s "
                    "ON %s.%s = %s.%s;"
                    % (n1, "name" if "name" in [c["name"] for c in info["columns"]] else col,
                       n2, pcol, child, n1, parent, n2, n1, col, n2, pcol))
            if _valid(sb, proj):
                steps.append(_step(
                    "type", "Join %s to %s" % (child, parent),
                    "JOIN glues two tables by matching a key.\n"
                    "ON %s.%s = %s.%s says how they line up." % (n1, col, n2, pcol),
                    "Try typing: %s" % proj, proj,
                    _h("Give the tables short nicknames %s and %s." % (n1, n2),
                       "Write JOIN %s %s ON …" % (parent, n2),
                       "Match %s.%s to %s.%s." % (n1, col, n2, pcol),
                       "Write: %s" % proj),
                    trick="JOIN = glue; ON = where to glue.",
                    require=["join"]))
            csql = ("SELECT count(*) FROM %s %s JOIN %s %s ON %s.%s = %s.%s;"
                    % (child, n1, parent, n2, n1, col, n2, pcol))
            if _valid(sb, csql):
                steps.append(_step(
                    "type", "Count the %s↔%s matches" % (child, parent),
                    "Every child row glues to one parent row in an inner join.",
                    "Try typing: %s" % csql, csql,
                    _h("Start with SELECT count(*).",
                       "Join %s to %s." % (child, parent),
                       "ON %s.%s = %s.%s." % (n1, col, n2, pcol),
                       "Write: %s" % csql),
                    trick="INNER JOIN keeps only rows that find a partner.",
                    require=["join"]))
    if steps:
        book.add("Joining tables together", ["join"], 3, steps)


def _subqueries(sb, book) -> None:
    steps = []
    for info in sb.schema:
        table = info["name"]
        num = _num_cols(info)
        name_col = "name" if "name" in [c["name"] for c in info["columns"]] else None
        if name_col and num:
            col = num[0]
            sql = ("SELECT %s FROM %s WHERE %s > (SELECT avg(%s) FROM %s);"
                   % (name_col, table, col, col, table))
            if _valid(sb, sql):
                steps.append(_step(
                    "type", "Above the average %s" % col,
                    "A sub-query is a question inside a question.\n"
                    "(SELECT avg(%s) FROM %s) finds the average first, then the "
                    "outer query compares each row to it." % (col, table),
                    "Try typing: %s" % sql, sql,
                    _h("First work out the average with a sub-query.",
                       "Wrap it in brackets after >.",
                       "The outer query reads FROM %s." % table,
                       "Write: %s" % sql),
                    trick="A sub-query answers one part before the rest runs."))
    for info in sb.schema:
        table = info["name"]
        name_col = "name" if "name" in [c["name"] for c in info["columns"]] else None
        fk = (info.get("foreign_keys") or [None])[0]
        if not name_col or not fk:
            continue
        parent = fk["table"]
        pname = "name" if "name" in [
            c["name"] for t in sb.schema if t["name"] == parent
            for c in t["columns"]] else fk["to"]
        sql = ("SELECT %s FROM %s WHERE %s IN (SELECT %s FROM %s);"
               % (name_col, table, fk["from"], fk["to"], parent))
        if _valid(sb, sql):
            steps.append(_step(
                "type", "Rows that appear in %s" % parent,
                "IN (SELECT …) keeps rows whose key appears in another table.",
                "Try typing: %s" % sql, sql,
                _h("Start with SELECT %s FROM %s." % (name_col, table),
                   "Add WHERE %s IN (…) ." % fk["from"],
                   "The sub-query selects %s from %s." % (fk["to"], parent),
                   "Write: %s" % sql),
                trick="IN (SELECT …) = 'whose id is in that other list'."))
    if steps:
        book.add("Questions inside questions (sub-queries)",
                 ["subquery"], 4, steps)


def _ranges(sb, info, book) -> None:
    table = info["name"]
    cols = [c["name"] for c in info["columns"]]
    show = cols[0]
    steps = []
    for col in _num_cols(info):
        values = _distinct(sb, table, col, cap=60)
        for i in range(len(values) - 1):
            lo, hi = values[i], values[i + 1]
            if lo == hi:
                continue
            sql = "SELECT %s FROM %s WHERE %s BETWEEN %s AND %s;" % (
                show, table, col, _lit(lo), _lit(hi))
            if not _valid(sb, sql):
                continue
            steps.append(_step(
                "type", "Keep %s from %s to %s" % (col, lo, hi),
                "BETWEEN lo AND hi keeps a range (both ends included).\n"
                "It is a tidy way to write two comparisons at once.",
                "Try typing: %s" % sql, sql,
                _h("Start with SELECT %s FROM %s." % (show, table),
                   "Add WHERE %s BETWEEN …" % col,
                   "Write the two ends with AND between them.",
                   "Write: %s" % sql),
                trick="BETWEEN a AND b = a <= x <= b.",
                require=["where"]))
            if _valid(sb, "SELECT %s FROM %s WHERE NOT (%s BETWEEN %s AND %s);"
                      % (show, table, col, _lit(lo), _lit(hi))):
                nsql = ("SELECT %s FROM %s WHERE NOT (%s BETWEEN %s AND %s);"
                        % (show, table, col, _lit(lo), _lit(hi)))
                steps.append(_step(
                    "type", "Keep %s outside %s..%s" % (col, lo, hi),
                    "NOT flips a test: NOT (something) means 'the opposite'.",
                    "Try typing: %s" % nsql, nsql,
                    _h("Start with SELECT %s FROM %s." % (show, table),
                       "Wrap the range in brackets after NOT.",
                       "NOT ( %s BETWEEN %s AND %s )." % (col, lo, hi),
                       "Write: %s" % nsql),
                    trick="NOT reverses whatever is inside the brackets.",
                    require=["where"]))
    if steps:
        book.add("Ranges and NOT in %s" % table,
                 ["where", "between"], 2, steps)


def _lists(sb, info, book) -> None:
    table = info["name"]
    cols = [c["name"] for c in info["columns"]]
    show = cols[0]
    steps = []
    for col in cols:
        values = _distinct(sb, table, col, cap=12)[:6]
        if len(values) < 2:
            continue
        chosen = values[:3]
        lst = ", ".join(_lit(v) for v in chosen)
        sql = "SELECT %s FROM %s WHERE %s IN (%s);" % (show, table, col, lst)
        if not _valid(sb, sql):
            continue
        steps.append(_step(
            "type", "Keep a short list of %s" % col,
            "IN ( … ) keeps a row when the value is in your list.\n"
            "It is a shorthand for several OR tests.",
            "Try typing: %s" % sql, sql,
            _h("Start with SELECT %s FROM %s." % (show, table),
               "Add WHERE %s IN (…)." % col,
               "Put the values inside the brackets, commas between.",
               "Write: %s" % sql),
            trick="IN (a, b, c) = 'any of these'.",
            require=["where"]))
        lst2 = ", ".join(_lit(v) for v in values[:4])
        nsql = "SELECT %s FROM %s WHERE %s NOT IN (%s);" % (
            show, table, col, lst2)
        if _valid(sb, nsql):
            steps.append(_step(
                "type", "Keep %s NOT IN a list" % col,
                "NOT IN ( … ) keeps the rows whose value is not in the list.",
                "Try typing: %s" % nsql, nsql,
                _h("Start with SELECT %s FROM %s." % (show, table),
                   "Add WHERE %s NOT IN (…)." % col,
                   "List the values in brackets.",
                   "Write: %s" % nsql),
                trick="NOT IN = 'none of these'.",
                require=["where"]))
    if steps:
        book.add("Pick from a list in %s" % table, ["where", "in"], 2, steps)


def _combos(sb, info, book) -> None:
    table = info["name"]
    cols = [c["name"] for c in info["columns"]]
    show = cols[0]
    tcols = _text_cols(info)
    ncols = _num_cols(info)
    if not tcols or not ncols:
        return
    steps = []
    tcol, ncol = tcols[0], ncols[0]
    for tv in _distinct(sb, table, tcol, cap=6):
        for nv in _distinct(sb, table, ncol, cap=6):
            cond = "%s = %s AND %s = %s" % (tcol, _lit(tv), ncol, _lit(nv))
            sql = "SELECT %s FROM %s WHERE %s;" % (show, table, cond)
            if not _valid(sb, sql):
                continue
            steps.append(_step(
                "type", "Two tests joined by AND",
                "AND means BOTH tests must be true for a row to stay.",
                "Try typing: %s" % sql, sql,
                _h("Start with SELECT %s FROM %s." % (show, table),
                   "Add WHERE %s = …" % tcol,
                   "Join with AND %s = …" % ncol, "Write: %s" % sql),
                trick="AND = both; OR = either.",
                require=["where"]))
    for tv in _distinct(sb, table, tcol, cap=4):
        for nv in _distinct(sb, table, ncol, cap=4):
            cond = "%s = %s OR %s = %s" % (tcol, _lit(tv), ncol, _lit(nv))
            sql = "SELECT %s FROM %s WHERE %s;" % (show, table, cond)
            if not _valid(sb, sql):
                continue
            steps.append(_step(
                "type", "Two tests joined by OR",
                "OR means a row stays when EITHER test is true.",
                "Try typing: %s" % sql, sql,
                _h("Start with SELECT %s FROM %s." % (show, table),
                   "Add WHERE %s = …" % tcol,
                   "Join with OR %s = …" % ncol, "Write: %s" % sql),
                trick="OR widens the net; AND narrows it.",
                require=["where"]))
    if steps:
        book.add("Combining tests with AND and OR in %s" % table,
                 ["where", "and", "or"], 3, steps)


def _sort_extra(sb, info, book) -> None:
    table = info["name"]
    cols = [c["name"] for c in info["columns"]]
    steps = []
    if len(cols) >= 2:
        for c1, c2 in [(cols[0], cols[1]), (cols[1], cols[0])]:
            sql = "SELECT %s, %s FROM %s ORDER BY %s, %s;" % (
                c1, c2, table, c1, c2)
            if not _valid(sb, sql):
                continue
            steps.append(_step(
                "type", "Sort by two columns",
                "ORDER BY can take more than one column.\n"
                "Rows tie on the first column, then the second breaks the tie.",
                "Try typing: %s" % sql, sql,
                _h("Start with SELECT %s, %s FROM %s." % (c1, c2, table),
                   "Add ORDER BY %s," % c1, "Then the tie-breaker %s." % c2,
                   "Write: %s" % sql),
                trick="List keys left to right: primary, then tie-breaker.",
                require=["order by"]))
    for col in cols[:3]:
        for n in (2, 5):
            sql = "SELECT %s FROM %s ORDER BY %s LIMIT %d OFFSET %d;" % (
                col, table, col, n, n)
            if not _valid(sb, sql):
                continue
            steps.append(_step(
                "type", "Skip %d then take %d of %s" % (n, n, col),
                "OFFSET skips that many rows before LIMIT starts counting.\n"
                "Together they page through a long list.",
                "Try typing: %s" % sql, sql,
                _h("Start with SELECT %s FROM %s." % (col, table),
                   "ORDER BY %s first." % col,
                   "Finish with LIMIT %d OFFSET %d." % (n, n),
                   "Write: %s" % sql),
                trick="LIMIT = how many; OFFSET = how many to skip.",
                require=["order by", "limit"]))
    if steps:
        book.add("More sorting tricks in %s" % table,
                 ["order by", "limit", "offset"], 3, steps)


def _agg_where(sb, info, book) -> None:
    table = info["name"]
    cols = [c["name"] for c in info["columns"]]
    steps = []
    for col in _num_cols(info):
        for v in _distinct(sb, table, col, cap=8):
            cond = "%s > %s" % (col, _lit(v))
            for fn in ("count", "sum", "avg", "min", "max"):
                target = "*" if fn == "count" else col
                sql = "SELECT %s(%s) FROM %s WHERE %s;" % (fn, target, table, cond)
                if not _valid(sb, sql):
                    continue
                steps.append(_step(
                    "type", "%s of %s where %s" % (fn.upper(), target, cond),
                    "A WHERE filter can narrow a total.\n"
                    "SQL filters the rows first, then %s runs on what is left." % fn,
                    "Try typing: %s" % sql, sql,
                    _h("Start with SELECT %s(%s)." % (fn, target),
                       "FROM %s." % table,
                       "Add WHERE %s." % cond, "Write: %s" % sql),
                    trick="WHERE first, then the total - the filter still counts.",
                    require=["where"]))
    if steps:
        book.add("Totals over a filtered set in %s" % table,
                 ["aggregate", "where"], 3, steps)


def _group_having(sb, info, book) -> None:
    table = info["name"]
    num = _num_cols(info)
    group_cols = [c["name"] for c in info["columns"]
                  if c["name"].endswith("_id") or c["name"] in ("city", "role")]
    steps = []
    for g in group_cols[:2]:
        for threshold in (1, 2, 3):
            sql = ("SELECT %s, count(*) FROM %s GROUP BY %s "
                   "HAVING count(*) >= %d;" % (g, table, g, threshold))
            if not _valid(sb, sql):
                continue
            steps.append(_step(
                "type", "%s with at least %d rows" % (g, threshold),
                "HAVING can hold any test about the piles.\n"
                "Here we keep only piles with count(*) >= %d." % threshold,
                "Try typing: %s" % sql, sql,
                _h("Start with SELECT %s, count(*)." % g,
                   "FROM %s GROUP BY %s." % (table, g),
                   "Add HAVING count(*) >= %d." % threshold,
                   "Write: %s" % sql),
                trick="HAVING = WHERE for piles.",
                require=["group by"]))
        for fn in ("sum", "avg", "max"):
            for c in num[:2]:
                sql = ("SELECT %s, %s(%s) FROM %s GROUP BY %s ORDER BY %s(%s) DESC;"
                       % (g, fn, c, table, g, fn, c))
                if not _valid(sb, sql):
                    continue
                steps.append(_step(
                    "type", "Groups ranked by %s(%s)" % (fn, c),
                    "You can sort by a total, not just a column.\n"
                    "ORDER BY %s(%s) DESC puts the biggest pile-total first."
                    % (fn, c),
                    "Try typing: %s" % sql, sql,
                    _h("Start with SELECT %s, %s(%s)." % (g, fn, c),
                       "FROM %s GROUP BY %s." % (table, g),
                       "Add ORDER BY %s(%s) DESC." % (fn, c),
                       "Write: %s" % sql),
                    trick="You may sort by an aggregate you computed.",
                    require=["group by", "order by"]))
    if steps:
        book.add("Grouping with tests and ranking in %s" % table,
                 ["group by", "having", "order by"], 4, steps)


def _join_extra(sb, book) -> None:
    steps = []
    for info in sb.schema:
        child = info["name"]
        ccols = [c["name"] for c in info["columns"]]
        cname = "name" if "name" in ccols else ccols[0]
        for fk in info.get("foreign_keys", []):
            parent = fk["table"]
            col, pcol = fk["from"], fk["to"]
            pinfo = next((t for t in sb.schema if t["name"] == parent), None)
            if pinfo is None:
                continue
            pcols = [c["name"] for c in pinfo["columns"]]
            pname = "name" if "name" in pcols else pcol
            n1, n2 = NICK.get(child, "a"), NICK.get(parent, "b")
            join = "FROM %s %s JOIN %s %s ON %s.%s = %s.%s" % (
                child, n1, parent, n2, n1, col, n2, pcol)
            for v in _distinct(sb, parent, pcol, cap=4):
                sql = "SELECT %s.%s, %s.%s %s WHERE %s.%s = %s;" % (
                    n1, cname, n2, pname, join, n2, pcol, _lit(v))
                if not _valid(sb, sql):
                    continue
                steps.append(_step(
                    "type", "Join, then keep one %s" % parent[:-1],
                    "Filters work the same after a JOIN.\n"
                    "Here we glue the tables, then keep one %s row."
                    % parent[:-1],
                    "Try typing: %s" % sql, sql,
                    _h("Glue with JOIN %s ON …" % parent,
                       "SELECT the two 'name' columns.",
                       "Add WHERE %s.%s = %s." % (n2, pcol, _lit(v)),
                       "Write: %s" % sql),
                    trick="JOIN first, WHERE after - the filter sees both tables.",
                    require=["join", "where"]))
            gsql = ("SELECT %s.%s, count(*) %s GROUP BY %s.%s ORDER BY count(*) DESC;"
                    % (n2, pname, join, n2, pname))
            if _valid(sb, gsql):
                steps.append(_step(
                    "type", "Count matches per %s" % parent[:-1],
                    "JOIN and GROUP BY are a famous pair.\n"
                    "Count how many %s rows belong to each %s."
                    % (child, parent[:-1]),
                    "Try typing: %s" % gsql, gsql,
                    _h("Join %s to %s." % (child, parent),
                       "GROUP BY %s.%s." % (n2, pname),
                       "SELECT the name and count(*).",
                       "Write: %s" % gsql),
                    trick="JOIN + GROUP BY = 'how many children each parent has'.",
                    require=["join", "group by"]))
    if steps:
        book.add("Joins with filters and counts", ["join", "where", "group by"],
                 4, steps)


# --------------------------------------------------------------------------
def generate() -> list[dict]:
    sb = Sandbox()
    book = _Book()
    try:
        for info in sb.schema:
            _reading(sb, info, book)
            _text_filters(sb, info, book)
            _number_filters(sb, info, book)
            _sorting(sb, info, book)
            _aggregates(sb, info, book)
            _grouping(sb, info, book)
            _ranges(sb, info, book)
            _lists(sb, info, book)
            _combos(sb, info, book)
            _sort_extra(sb, info, book)
            _agg_where(sb, info, book)
            _group_having(sb, info, book)
        _joins(sb, book)
        _join_extra(sb, book)
        _subqueries(sb, book)
    finally:
        sb.close()

    lessons = book.lessons
    total = 0
    trimmed = []
    for lesson in lessons:
        room = MAX_TOTAL - total
        if room <= 0:
            break
        if len(lesson["steps"]) > room:
            lesson = dict(lesson)
            lesson["steps"] = lesson["steps"][:room]
        total += len(lesson["steps"])
        trimmed.append(lesson)

    out = []
    for i, lesson in enumerate(trimmed, start=21):
        item = dict(lesson)
        item["id"] = "L%03d" % i
        item["order"] = i
        out.append(item)
    return out


LESSONS = generate()

if __name__ == "__main__":
    steps = sum(len(l["steps"]) for l in LESSONS)
    print("generated lessons:", len(LESSONS), "steps:", steps)
