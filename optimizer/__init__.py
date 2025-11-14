from .parser import parse_sql
from .rules import run_all_rules
from .generator import apply_rewrites
from .cost_estimator import estimate_cost

def analyze_query(query, schema_stats, apply_safe_rewrites=True):
    parsed = parse_sql(query)

    suggestions, fixes = run_all_rules(parsed, schema_stats)

    optimized_query = parsed["raw"]
    applied_rewrites = []

    if apply_safe_rewrites:
        optimized_query, applied_rewrites = apply_rewrites(parsed, schema_stats)
        parsed_after = parse_sql(optimized_query)
    else:
        parsed_after = parsed

    cost_before = estimate_cost(parsed, schema_stats)
    cost_after = estimate_cost(parsed_after, schema_stats)

    return {
        "parsed": parsed,
        "optimized_query": optimized_query,
        "applied_rewrites": applied_rewrites,
        "suggestions": suggestions,
        "cost_before": cost_before,
        "cost_after": cost_after
    }
