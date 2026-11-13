from text2sql.db import get_schema, describe_db, column_tables, run_sql
from text2sql.llm import generate, clean_sql

PROMPT = """You are an expert SQLite developer.

Database schema:
{schema}

Hint: {evidence}

Use only the tables and columns listed. To combine tables, follow the "link" lines.
Write one SQLite query that answers the question. Return only the SQL.
Question: {question}"""

FIX_PROMPT = """{prompt}

Your previous query:
{sql}

It failed with this error:
{error}
{hint}

Check the schema carefully and write a corrected SQLite query. Return only the SQL."""

def error_hint(db_id, error):
    """For 'no such column: T1.HGB', tell the model which tables really have HGB."""
    if not error.startswith("no such column"):
        return ""
    col = error.split(":", 1)[1].strip().split(".")[-1].strip("`\"")
    tables = column_tables(db_id).get(col.lower())
    if tables:
        return f"Note: column `{col}` exists only in table(s): {', '.join(tables)}. Join to that table."
    return f"Note: no table has a column named `{col}`."

def ask(db_id, question, evidence="", max_retries=0, rich_schema=False, column_hints=False):
    """Question -> SQL -> result. On an SQL error, retry up to max_retries times."""
    schema = describe_db(db_id) if rich_schema else get_schema(db_id)
    prompt = PROMPT.format(schema=schema, evidence=evidence or "none", question=question)
    sql = clean_sql(generate(prompt))
    for attempt in range(max_retries + 1):
        try:
            return {"sql": sql, "rows": run_sql(db_id, sql), "error": None, "attempts": attempt + 1}
        except Exception as e:
            error = str(e)
            if attempt < max_retries:
                hint = error_hint(db_id, error) if column_hints else ""
                sql = clean_sql(generate(FIX_PROMPT.format(prompt=prompt, sql=sql, error=error, hint=hint)))
    return {"sql": sql, "rows": None, "error": error, "attempts": max_retries + 1}