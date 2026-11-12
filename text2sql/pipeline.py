from text2sql.db import get_schema, run_sql
from text2sql.llm import generate, clean_sql

PROMPT = """You are an expert SQLite developer.

Database schema:
{schema}

Hint: {evidence}

Write one SQLite query that answers the question. Return only the SQL.
Question: {question}"""

FIX_PROMPT = """{prompt}

Your previous query:
{sql}

It failed with this error:
{error}

Check the schema carefully and write a corrected SQLite query. Return only the SQL."""


def ask(db_id, question, evidence="", max_retries=0):
    """Question -> SQL -> result. On an SQL error, retry up to max_retries times."""
    prompt = PROMPT.format(schema=get_schema(db_id), evidence=evidence or "none", question=question)
    sql = clean_sql(generate(prompt))
    for attempt in range(max_retries + 1):
        try:
            return {"sql": sql, "rows": run_sql(db_id, sql), "error": None, "attempts": attempt + 1}
        except Exception as e:
            error = str(e)
            if attempt < max_retries:
                sql = clean_sql(generate(FIX_PROMPT.format(prompt=prompt, sql=sql, error=error)))
    return {"sql": sql, "rows": None, "error": error, "attempts": max_retries + 1}