def estimate_cost(parsed, schema_stats):
    TABLE_SCAN_COST = 10
    INDEX_SCAN_COST = 2
    JOIN_COST = 500
    ORDER_BY_COST = 8
    GROUP_BY_COST = 12

    tables = parsed.get("tables", [])
    where = parsed.get("where") or ""
    raw = parsed.get("raw", "")
    rows_est = 0
    total_cost = 0

    for t in tables:
        meta = schema_stats.get(t, {"rows": 1000})
        rows = meta["rows"]
        rows_est += rows

        indexed = any(c.lower() in where.lower() for c in meta.get("columns", []))
        total_cost += rows * (INDEX_SCAN_COST if indexed else TABLE_SCAN_COST)

    if len(tables) > 1:
        total_cost += JOIN_COST

    if "ORDER BY" in raw.upper():
        total_cost += ORDER_BY_COST

    if "GROUP BY" in raw.upper():
        total_cost += GROUP_BY_COST

    return {"cost": total_cost, "rows_est": rows_est}
