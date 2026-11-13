import pytest
from text2sql.guards import validate_sql

ALLOWED = [
    "SELECT COUNT(*) FROM member",
    "SELECT first_name, last_name FROM member",
    "SELECT event_name FROM event WHERE type = 'Meeting'",
    "WITH t AS (SELECT * FROM event) SELECT COUNT(*) FROM t",
]

BLOCKED = [
    "DELETE FROM expense",
    "DROP TABLE member",
    "UPDATE customers SET Currency = 'USD'",
    "SELECT 1; DROP TABLE member",
    "SELECT * FROM member",
    "SELECT m.* FROM member m",
    "SELECT email FROM member",
    "SELECT name FROM sqlite_master",
    "SELECT name FROM pragma_table_info('member')",
    "WITH x AS (SELECT expense_id FROM expense) DELETE FROM expense WHERE expense_id IN (SELECT expense_id FROM x)",
]


@pytest.mark.parametrize("sql", ALLOWED)
def test_safe_queries_are_allowed(sql):
    assert validate_sql(sql) is None


@pytest.mark.parametrize("sql", BLOCKED)
def test_dangerous_queries_are_blocked(sql):
    assert validate_sql(sql) is not None