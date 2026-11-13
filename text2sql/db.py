import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from functools import lru_cache

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

@lru_cache(maxsize=None)
def describe_db(db_id, n_examples=3):
    """Compact schema: columns with example values, plus how tables link (foreign keys)."""
    lines = []
    with closing(connect(db_id)) as conn:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for t in tables:
            lines.append(f"Table {t}:")
            for col in conn.execute(f'PRAGMA table_info("{t}")').fetchall():
                name, ctype = col[1], col[2]
                vals = conn.execute(f'SELECT DISTINCT "{name}" FROM "{t}" '
                                    f'WHERE "{name}" IS NOT NULL LIMIT {n_examples}').fetchall()
                examples = ", ".join(repr(v[0][:40] if isinstance(v[0], str) else v[0]) for v in vals)
                lines.append(f"  - {t}.`{name}` ({ctype}), e.g. {examples}")
            for fk in conn.execute(f'PRAGMA foreign_key_list("{t}")').fetchall():
                lines.append(f"  * link: {t}.{fk[3]} -> {fk[2]}.{fk[4] or 'primary key'}")
            lines.append("")
    return "\n".join(lines)

@lru_cache(maxsize=None)
def column_tables(db_id):
    """Map each column name (lowercase) to the list of tables that contain it."""
    index = {}
    with closing(connect(db_id)) as conn:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for t in tables:
            for col in conn.execute(f'PRAGMA table_info("{t}")').fetchall():
                index.setdefault(col[1].lower(), []).append(t)
    return index

DATA = Path(__file__).resolve().parent.parent / "data" / "minidev" / "MINIDEV"
DB_DIR = DATA / "dev_databases"   # the attack script points this at a sandbox copy


def connect(db_id, read_only=False):
    """Open the SQLite file for one database."""
    path = DB_DIR / db_id / f"{db_id}.sqlite"
    if read_only:
        return sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    return sqlite3.connect(path, isolation_level=None)