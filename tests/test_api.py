from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


def test_lists_databases():
    r = client.get("/databases")
    assert r.status_code == 200
    assert "student_club" in r.json()


def test_schema_hides_private_columns():
    member = client.get("/schema/student_club").json()["member"]
    assert "first_name" in member
    assert "email" not in member and "phone" not in member


def test_unknown_database_is_rejected():
    assert client.get("/schema/not_a_database").status_code == 404


def test_attack_returns_403(monkeypatch):
    # Pretend the model obeyed an attacker, without needing Ollama
    monkeypatch.setattr("text2sql.pipeline.generate", lambda prompt: "DELETE FROM expense")
    r = client.post("/ask", json={"db_id": "student_club", "question": "anything"})
    assert r.status_code == 403