from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from text2sql import db
from text2sql.guards import PRIVATE_COLUMNS
from text2sql.pipeline import ask

# The service ALWAYS runs with defenses on; callers can't turn them off.
SAFE_SETTINGS = {"max_retries": 2, "column_hints": True, "validate": True, "read_only": True}
MAX_ROWS = 100

app = FastAPI(title="Secure Text-to-SQL",
              description="Ask questions about a database in plain English, with guardrails.")


class Question(BaseModel):
    db_id: str
    question: str
    evidence: str = ""


class Answer(BaseModel):
    sql: str
    rows: list | None
    error: str | None


def check_db(db_id):
    """Only allow known database names (also stops path tricks like '../')."""
    if db_id not in list_databases():
        raise HTTPException(status_code=404, detail=f"Unknown database: {db_id}")


@app.get("/databases")
def list_databases():
    return sorted(p.name for p in db.DB_DIR.iterdir() if p.is_dir())


@app.get("/schema/{db_id}")
def schema(db_id: str):
    check_db(db_id)
    tables = {}
    for col, table_list in db.column_tables(db_id).items():
        for t in table_list:
            if col not in PRIVATE_COLUMNS.get(t, set()):
                tables.setdefault(t, []).append(col)
    return tables


@app.post("/ask", response_model=Answer)
def ask_question(q: Question):
    check_db(q.db_id)
    out = ask(q.db_id, q.question, q.evidence, **SAFE_SETTINGS)
    rows = out["rows"][:MAX_ROWS] if out["rows"] is not None else None
    return Answer(sql=out["sql"], rows=rows, error=out["error"])