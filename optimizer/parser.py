import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where
from sqlparse.tokens import Keyword, DML
import re

def _is_subselect(parsed):
    if not parsed.is_group:
        return False
    for item in parsed.tokens:
        if item.ttype is DML and item.value.upper() == 'SELECT':
            return True
    return False

def extract_from_part(parsed):
    from_seen = False
    tables = []
    for token in parsed.tokens:
        if from_seen:
            if isinstance(token, IdentifierList):
                for identifier in token.get_identifiers():
                    tables.append(str(identifier.get_real_name()))
                break
            if isinstance(token, Identifier):
                tables.append(str(token.get_real_name()))
                break
            if token.ttype is Keyword:
                break
        if token.ttype is Keyword and token.value.upper() == 'FROM':
            from_seen = True
    return tables

def get_select_columns(parsed):
    cols = []
    select_seen = False
    for token in parsed.tokens:
        if select_seen:
            if isinstance(token, IdentifierList):
                for iden in token.get_identifiers():
                    cols.append(str(iden).strip())
                break
            if isinstance(token, Identifier):
                cols.append(str(token).strip())
                break
            if token.ttype is Keyword:
                break
        if token.ttype is DML and token.value.upper() == 'SELECT':
            select_seen = True
    return cols or ["*"]

def has_distinct(parsed):
    return 'DISTINCT' in str(parsed).upper()

def has_order_by(parsed):
    return 'ORDER BY' in str(parsed).upper()

def detect_subquery(parsed):
    return bool(re.search(r"\(\s*SELECT\s", str(parsed), re.IGNORECASE))

def parse_query(query):
    parsed = sqlparse.parse(query)[0]
    select_cols = get_select_columns(parsed)
    tables = extract_from_part(parsed)

    where = None
    for token in parsed.tokens:
        if isinstance(token, Where):
            where = str(token)

    joins = []
    raw = str(parsed).upper()
    if "JOIN" in raw:
        joins.append("JOIN")

    return {
        "raw": query,
        "select": select_cols,
        "tables": tables,
        "where": where,
        "joins": joins,
        "distinct": has_distinct(parsed),
        "order_by": has_order_by(parsed),
        "has_subquery": detect_subquery(parsed)
    }
