from text2sql.db import get_schema, run_sql
from text2sql.llm import generate, clean_sql

PROMPT = """You are an expert SQLite developer.

Database schema:
{schema}

Hint: {evidence}

Write one SQLite query that answers the question. Return only the SQL.
Question: {question}"""


def ask(db_id, question, evidence=""):
    """Turn a question into SQL, run it, and return the SQL plus the result."""
    prompt = PROMPT.format(schema=get_schema(db_id), evidence=evidence or "none", question=question)
    sql = clean_sql(generate(prompt))
    try:
        return {"sql": sql, "rows": run_sql(db_id, sql), "error": None}
    except Exception as e:
        return {"sql": sql, "rows": None, "error": str(e)}