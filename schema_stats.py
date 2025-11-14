SCHEMA_STATS = {
    "users": {
        "columns": ["id", "name", "email", "age", "created_at"],
        "rows": 100000,
        "indexes": ["id", "email", "age"]
    },
    "products": {
        "columns": ["id", "name", "price", "category"],
        "rows": 20000,
        "indexes": ["id", "price", "category"]
    },
    "orders": {
        "columns": ["id", "user_id", "amount", "status"],
        "rows": 50000,
        "indexes": ["id", "user_id", "status"]
    }
}
