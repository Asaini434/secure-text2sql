import sqlglot
from sqlglot import exp

# Security policy for this project (state it in the report)
PRIVATE_COLUMNS = {"member": {"email", "phone"}}   # table -> columns users may not read
READ_ONLY_TYPES = (exp.Select, exp.Union, exp.Intersect, exp.Except)


def validate_sql(sql):
    """Return None if the SQL is allowed, otherwise a short reason it was blocked."""
    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except Exception:
        return "could not parse SQL"
    if len(statements) != 1:
        return "only one statement is allowed"
    stmt = statements[0]
    if not isinstance(stmt, READ_ONLY_TYPES):
        return f"only SELECT queries are allowed (got {type(stmt).__name__})"

    lowered = sql.lower()
    if "sqlite_" in lowered or "pragma" in lowered:
        return "system tables and pragmas are not accessible"

    tables = {t.name.lower() for t in stmt.find_all(exp.Table)}
    if any(t.startswith(("sqlite_", "pragma_")) for t in tables):
        return "system tables are not accessible"

    for table, private in PRIVATE_COLUMNS.items():
        if table in tables:
            if stmt.find(exp.Star):
                return f"SELECT * is not allowed on table {table}"
            cols = {c.name.lower() for c in stmt.find_all(exp.Column)}
            if cols & private:
                return f"columns {sorted(cols & private)} are private"
    return None