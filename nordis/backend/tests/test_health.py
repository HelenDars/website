from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_is_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready_checks_database_and_redis():
    """Требует запущенных PostgreSQL и Redis (docker compose up db redis)."""
    r = client.get("/health/ready")
    assert r.status_code == 200, r.json()
    assert r.json()["checks"] == {"database": "ok", "redis": "ok"}
