from .parser import parse_query
from .rules import run_all_rules
from .generator import apply_rewrites
from .cost_estimator import estimate_cost

def analyze_query(query, schema_stats):
    parsed = parse_query(query)

    suggestions, fixes = run_all_rules(parsed, schema_stats)

    cost_before = estimate_cost(parsed, schema_stats)

    optimized_query, applied_rewrites = apply_rewrites(parsed, schema_stats)

    parsed_after = parse_query(optimized_query)
    cost_after = estimate_cost(parsed_after, schema_stats)

    return {
        "parsed": parsed,
        "suggestions": suggestions,
        "fixes": fixes,
        "optimized_query": optimized_query,
        "applied_rewrites": applied_rewrites,
        "cost_before": cost_before,
        "cost_after": cost_after
    }
