

def estimate_cost(parsed, schema_stats):
    raw = parsed["raw"].upper()
    tables = parsed.get("tables", [])

    total_cost = 0
    rows_est = 0

    where = parsed.get("where") or ""
    where_upper = where.upper()

    for t in tables:
        meta = schema_stats.get(t, None)
        if not meta:
            continue

        rows = meta["rows"]
        rows_est += rows

        indexed_cols = meta.get("indexes", [])
        indexed_used = False

        # IN() pattern → index-friendly
        if " IN " in where_upper:
            for col in indexed_cols:
                if col.upper() in where_upper:
                    indexed_used = True

        # OR chain → not index friendly
        elif " OR " in where_upper:
            indexed_used = False

        # Simple predicate → index OK
        else:
            for col in indexed_cols:
                if col.upper() in where_upper:
                    indexed_used = True

        # Cost
        scan_cost = 2 if indexed_used else 10
        total_cost += rows * scan_cost

    # JOIN cost
    if "JOIN" in raw:
        total_cost += 500

    # Sorting cost
    if "ORDER BY" in raw:
        total_cost += 8000

    # Grouping cost
    if "GROUP BY" in raw:
        total_cost += 12000

    # DISTINCT cost
    if "DISTINCT" in raw:
        total_cost += 6000

    return {"cost": total_cost, "rows_est": rows_est}
