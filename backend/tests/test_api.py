from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_extract_invalid_url():
    response = client.post("/api/extract", json={"repo_url": ""})
    assert response.status_code == 422


def test_extract_missing_field():
    response = client.post("/api/extract", json={})
    assert response.status_code == 422


def test_architecture_unknown_task():
    response = client.get("/api/architecture/nonexistent")
    assert response.status_code == 404


def test_extract_stream_unknown():
    response = client.get("/api/extract/stream/nonexistent")
    assert response.status_code == 404
