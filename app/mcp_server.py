from fastmcp import FastMCP
from app.api import SAFE_SETTINGS, MAX_ROWS, list_databases, schema
from text2sql.pipeline import ask

mcp = FastMCP("secure-text2sql")


@mcp.tool
def list_dbs() -> list[str]:
    """List the databases that can be queried."""
    return list_databases()


@mcp.tool
def describe_database(db_id: str) -> dict:
    """Show the tables and public columns of one database."""
    return schema(db_id)


@mcp.tool
def ask_database(db_id: str, question: str) -> dict:
    """Answer a question about a database in plain English.
    Only safe, read-only SQL is ever run; private data is protected."""
    if db_id not in list_databases():
        return {"error": f"Unknown database: {db_id}"}
    out = ask(db_id, question, **SAFE_SETTINGS)
    rows = out["rows"][:MAX_ROWS] if out["rows"] is not None else None
    return {"sql": out["sql"], "rows": rows, "error": out["error"]}


if __name__ == "__main__":
    mcp.run()