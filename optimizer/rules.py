import re

def _col(x):
    return x.split('.')[-1]

def _is_pk(c):
    return c.lower() in ("id", "pk", "user_id", "order_id")

def check_select_star(parsed, schema_stats):
    sel = parsed.get("select", [])
    fix = None
    s = []
    if sel == ["*"]:
        t = parsed.get("tables", [])
        if t and t[0] in schema_stats:
            fix = ", ".join(schema_stats[t[0]]["columns"])
        s.append("Avoid SELECT *; select required columns.")
    return s, fix

def check_unused_columns(parsed, schema_stats):
    sel = parsed.get("select", [])
    if not sel or sel == ["*"] or len(sel) < 5:
        return []
    where = parsed.get("where") or ""
    used = set(re.findall(r"([a-zA-Z_][a-zA-Z0-9_\.]*)", where))
    for j in parsed.get("joins") or []:
        used |= set(re.findall(r"([a-zA-Z_][a-zA-Z0-9_\.]*)", j))
    if len(used) <= 2:
        return ["Many columns selected but few used; reduce projection."]
    return []

def check_limit_suggestion(parsed, schema_stats):
    s = []
    q = parsed.get("raw", "")
    for t in parsed.get("tables", []):
        if t in schema_stats and schema_stats[t]["rows"] > 100000:
            if "LIMIT" not in q.upper():
                s.append(f"Table `{t}` is large; add LIMIT or pagination.")
    return s

def check_missing_index(parsed, schema_stats):
    s = []
    w = parsed.get("where")
    if not w:
        return s
    cols = re.findall(r"([a-zA-Z_][a-zA-Z0-9_\.]*)\s*(?:=|>|<|LIKE|IN)\s*", w, re.IGNORECASE)
    seen = set()
    for col in cols:
        c = _col(col)
        if c in seen:
            continue
        seen.add(c)
        for t, meta in schema_stats.items():
            if c in meta["columns"]:
                s.append(f"Consider indexing `{t}({c})`.")
    return s

def check_or_to_in(parsed):
    w = parsed.get("where") or ""
    if re.search(r"([a-zA-Z_][a-zA-Z0-9_\.]*)\s*=\s*[^)\s]+(?:\s+OR\s+\1\s*=\s*[^)\s]+)+", w, re.IGNORECASE):
        return ["Rewrite OR conditions as IN(...)."]
    return []

def check_non_sargable(parsed):
    s = []
    w = parsed.get("where") or ""
    if "YEAR(" in w.upper():
        s.append("Avoid YEAR(col); use range conditions.")
    if re.search(r"LIKE\s+'%[^']+'", w, re.IGNORECASE):
        s.append("Leading wildcard in LIKE disables index.")
    if "UPPER(" in w.upper() or "LOWER(" in w.upper():
        s.append("Avoid functions on indexed columns.")
    return s

def check_not_in_and_not_equals(parsed):
    w = parsed.get("where") or ""
    if " NOT IN " in w.upper() or "!=" in w or "<>" in w:
        return ["Avoid NOT IN / != ; hurts index usage."]
    return []

def check_cartesian_join(parsed):
    s = []
    q = parsed.get("raw", "").upper()
    t = parsed.get("tables", [])
    if len(t) > 1 and "," in q and "JOIN" not in q:
        s.append("Implicit join may cause Cartesian product.")
    if "JOIN" in q and "ON" not in q:
        s.append("JOIN without ON detected.")
    return s

def check_join_order(parsed, schema_stats):
    t = parsed.get("tables", [])
    if len(t) <= 1:
        return []
    rows = [schema_stats.get(x, {"rows": 1000})["rows"] for x in t]
    if rows == sorted(rows, reverse=True):
        return ["Large tables joined first; reorder joins."]
    return []

def check_unnecessary_left_join(parsed):
    q = parsed.get("raw", "")
    if "LEFT JOIN" in q.upper() and "IS NOT NULL" in q.upper():
        return ["LEFT JOIN unnecessary; could be INNER JOIN."]
    return []

def check_exists_to_join(parsed):
    if "EXISTS" in parsed.get("raw", "").upper():
        return ["EXISTS detected; JOIN may be faster."]
    return []

def check_in_subquery(parsed):
    if re.search(r"\bIN\s*\(\s*SELECT", parsed.get("raw",""), re.IGNORECASE):
        return ["IN (SELECT ...) detected; consider JOIN."]
    return []

def check_group_by_having(parsed):
    s = []
    q = parsed.get("raw","")
    if "HAVING" in q.upper() and "WHERE" not in q.upper():
        s.append("HAVING without WHERE; inefficient.")
    if "GROUP BY" in q.upper():
        m = re.search(r"GROUP\s+BY\s+(.*?)(ORDER|LIMIT|$)", q, re.IGNORECASE|re.DOTALL)
        if m:
            cols = re.findall(r"([a-zA-Z_][a-zA-Z0-9_\.]*)", m.group(1))
            for c in cols:
                if _is_pk(_col(c)):
                    s.append("Grouping by PK is unnecessary.")
                    break
    return s

def check_order_by_index(parsed, schema_stats):
    s = []
    q = parsed.get("raw","")
    if "ORDER BY" in q.upper():
        m = re.search(r"ORDER\s+BY\s+(.*?)(LIMIT|$)", q, re.IGNORECASE|re.DOTALL)
        if m:
            cols = re.findall(r"([a-zA-Z_][a-zA-Z0-9_\.]*)", m.group(1))
            for c in cols:
                cn = _col(c)
                for t, meta in schema_stats.items():
                    if cn in meta["columns"]:
                        s.append(f"Consider index on `{t}({cn})` for ORDER BY.")
    return s

def check_order_by_rand(parsed):
    if "ORDER BY RAND()" in parsed.get("raw","").upper():
        return ["ORDER BY RAND() is expensive."]
    return []

def check_distinct_unnecessary(parsed, schema_stats):
    q = parsed.get("raw","")
    if "DISTINCT" in q.upper():
        sel = parsed.get("select", [])
        if len(sel) == 1:
            c = _col(sel[0])
            for t, meta in schema_stats.items():
                if c in meta["columns"] and _is_pk(c):
                    return ["DISTINCT on PK is unnecessary."]
    return []

def check_offset_pagination(parsed):
    q = parsed.get("raw","")
    if "OFFSET" in q.upper() and "ORDER BY" not in q.upper():
        return ["OFFSET without ORDER BY is unsafe."]
    return []

def check_redundant_conditions(parsed):
    w = parsed.get("where") or ""
    if re.search(r"AND\s+[a-zA-Z_][a-zA-Z0-9_\.]*\s*>\s*\d+\s+AND\s+[a-zA-Z_][a-zA-Z0-9_\.]*\s*>\s*\d+", w, re.IGNORECASE):
        return ["Redundant WHERE conditions detected."]
    return []

def check_join_without_on(parsed):
    q = parsed.get("raw","")
    if "," in q and "JOIN" in q and "ON" not in q:
        return ["JOIN missing ON clause."]
    return []

def check_pagination_index(parsed, schema_stats):
    s = []
    q = parsed.get("raw","")
    if "LIMIT" in q.upper() and "ORDER BY" in q.upper():
        s += check_order_by_index(parsed, schema_stats)
    return s

def check_window_function_usage(parsed):
    if "OVER (" in parsed.get("raw","").upper():
        return ["Window functions are expensive."]
    return []

def check_casts_in_predicates(parsed):
    w = parsed.get("where") or ""
    if "CAST(" in w.upper():
        return ["CAST in WHERE prevents index usage."]
    return []

ALL_RULES = [
    check_select_star,
    check_unused_columns,
    check_limit_suggestion,
    check_missing_index,
    check_or_to_in,
    check_non_sargable,
    check_not_in_and_not_equals,
    check_cartesian_join,
    check_join_order,
    check_unnecessary_left_join,
    check_exists_to_join,
    check_in_subquery,
    check_group_by_having,
    check_order_by_index,
    check_order_by_rand,
    check_distinct_unnecessary,
    check_offset_pagination,
    check_redundant_conditions,
    check_join_without_on,
    check_pagination_index,
    check_window_function_usage,
    check_casts_in_predicates
]

def run_all_rules(parsed, schema_stats):
    suggestions = []
    fixes = {}

    for rule in ALL_RULES:
        res = rule(parsed, schema_stats) if rule.__code__.co_argcount == 2 else rule(parsed)
        if isinstance(res, tuple):
            s, fix = res
            if s:
                suggestions += s
            if fix:
                fixes[rule.__name__] = fix
        elif isinstance(res, list):
            suggestions += res

    final = []
    seen = set()
    for s in suggestions:
        if s not in seen:
            final.append(s)
            seen.add(s)

    return final, fixes
