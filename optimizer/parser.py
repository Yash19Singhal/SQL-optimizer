import sqlparse

def extract_where(statement):
    where = ""
    start = False

    for token in statement.tokens:
        t = str(token).strip()

        if t.upper().startswith("WHERE"):
            start = True
            where = t[5:].strip()   # strip the word WHERE
            continue

        if start:
            where += " " + t

        # stop at semicolon or end of where clause
        if t.endswith(";"):
            break

    return where.strip()

from sqlparse.sql import IdentifierList, Identifier
from sqlparse.tokens import Keyword, DML

def extract_tables(statement):
    tables = []
    from_seen = False

    for token in statement.tokens:
        if from_seen:
            if isinstance(token, IdentifierList):
                for identifier in token.get_identifiers():
                    tables.append(identifier.get_name())
                from_seen = False
            elif isinstance(token, Identifier):
                tables.append(token.get_name())
                from_seen = False
        if token.ttype is Keyword and token.value.upper() == "FROM":
            from_seen = True

    return tables


def extract_select(statement):
    select_cols = []
    seen_select = False

    for token in statement.tokens:
        if token.ttype is None and token.value.upper().startswith("SELECT"):
            seen_select = True

        if seen_select and token.ttype is None and "FROM" in token.value.upper():
            break

        if seen_select and token.ttype is None:
            cols = str(token).replace("SELECT", "").strip()
            if cols:
                select_cols = [c.strip() for c in cols.split(",")]
    return select_cols

def extract_joins(statement):
    joins = []
    s = str(statement).upper()
    if "JOIN" in s:
        parts = s.split("JOIN")[1:]
        for p in parts:
            joins.append("JOIN " + p.strip())
    return joins

def parse_sql(query):
    parsed = sqlparse.parse(query)
    if not parsed:
        return {}

    statement = parsed[0]

    select_cols = extract_select(statement)
    tables = extract_tables(statement)
    where_clause = extract_where(statement)
    joins = extract_joins(statement)

    return {
        "raw": query,
        "select": select_cols,
        "tables": tables,
        "where": where_clause,
        "joins": joins
    }
