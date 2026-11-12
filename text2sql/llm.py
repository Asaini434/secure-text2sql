import re
import ollama

MODEL = "qwen2.5-coder:7b"


def generate(prompt):
    """Send a prompt to the local model and return its reply as text."""
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0},
    )
    return response["message"]["content"]


def clean_sql(text):
    """Pull the SQL out of the reply, removing ```sql fences if present."""
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    sql = match.group(1) if match else text
    return sql.strip().rstrip(";")