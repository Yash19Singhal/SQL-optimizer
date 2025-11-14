import re

def replace_select_star(query, cols):
    return re.sub(r"SELECT\s+\*\s+FROM", f"SELECT {cols} FROM", query, flags=re.IGNORECASE)

def or_to_in_rewrite(query):
    q = " ".join(query.split())

    pattern = re.compile(
        r"(\b[a-zA-Z_][a-zA-Z0-9_\.]*\b)\s*=\s*('[^']*'|\"[^\"]*\"|\d+)"
        r"(?:\s+OR\s+\1\s*=\s*('[^']*'|\"[^\"]*\"|\d+))+",
        flags=re.IGNORECASE
    )

    matches = list(pattern.finditer(q))
    if not matches:
        return query, 0

    new_q = q
    count = 0

    for m in reversed(matches):
        col = m.group(1)
        full = m.group(0)

        vals = re.findall(
            r"=\s*('[^']*'|\"[^\"]*\"|\d+)",
            full
        )

        in_clause = f"{col} IN ({', '.join(vals)})"
        new_q = new_q[:m.start()] + in_clause + new_q[m.end():]
        count += 1

    return new_q, count

def remove_unnecessary_distinct(query, parsed, schema_stats):
    if "DISTINCT" not in query.upper():
        return query, False

    sel = parsed.get("select", [])
    if len(sel) == 1:
        col = sel[0].split('.')[-1].lower()
        if col in ("id", "user_id", "order_id"):
            newq = re.sub(r"\bDISTINCT\b", "", query, flags=re.IGNORECASE)
            return newq, True

    return query, False

def apply_rewrites(parsed, schema_stats):
    q = parsed["raw"]
    applied = []

    if parsed.get("select") == ["*"]:
        t = parsed.get("tables", [])
        if t and t[0] in schema_stats:
            cols = ", ".join(schema_stats[t[0]]["columns"])
            q = replace_select_star(q, cols)
            applied.append("SELECT * → explicit columns")

    new_q, n = or_to_in_rewrite(q)
    if n > 0:
        q = new_q
        applied.append("OR → IN rewrite")

    new_q2, removed = remove_unnecessary_distinct(q, parsed, schema_stats)
    if removed:
        q = new_q2
        applied.append("Removed unnecessary DISTINCT")

    return q, applied
