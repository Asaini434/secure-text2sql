import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

# Folder holding the BIRD Mini-Dev files, found relative to this file
DATA = Path(__file__).resolve().parent.parent / "data" / "minidev" / "MINIDEV"


def load_questions():
    """Load the 500 BIRD Mini-Dev questions as a list of dicts."""
    with open(DATA / "mini_dev_sqlite.json") as f:
        return json.load(f)


def connect(db_id, read_only=False):
    """Open the SQLite file for one database."""
    path = DATA / "dev_databases" / db_id / f"{db_id}.sqlite"
    if read_only:
        return sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    return sqlite3.connect(path)


def get_schema(db_id):
    """Return the CREATE TABLE statements that describe every table."""
    with closing(connect(db_id)) as conn:
        rows = conn.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
    return "\n\n".join(r[0] for r in rows if r[0])


def run_sql(db_id, sql, read_only=False, timeout=30):
    """Run a query and return all result rows; stop it after `timeout` seconds."""
    with closing(connect(db_id, read_only)) as conn:
        deadline = time.time() + timeout
        conn.set_progress_handler(lambda: time.time() > deadline, 10_000)
        return conn.execute(sql).fetchall()