SCHEMA_STATS = {
    "users": {
        "columns": ["id", "name", "email", "age", "created_at"],
        "rows": 100000
    },
    "orders": {
        "columns": ["id", "user_id", "amount", "status", "created_at"],
        "rows": 500000
    },
    "products": {
        "columns": ["id", "name", "price", "category"],
        "rows": 20000
    }
}
