"""
Integration tests for the Flask API (feature endpoints).

Run against a dedicated throwaway MongoDB database (set via MONGO_DB before the
app is imported). Protected endpoints are exercised with an authenticated test
client. If MongoDB is not reachable the whole module is skipped.
"""
import os
import importlib

import pytest

os.environ["MONGO_DB"] = "aceit_test_db"
os.environ.setdefault("DELETE_VIDEO_AFTER_ANALYSIS", "true")
os.environ.setdefault("MAIL_CONSOLE_FALLBACK", "true")

from helpers import register_verify_login, csrf_from_client  # noqa: E402,F401


@pytest.fixture(scope="module")
def app_module():
    try:
        from pymongo import MongoClient
        MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/"),
                    serverSelectionTimeoutMS=1500).admin.command("ping")
    except Exception:  # noqa: BLE001
        pytest.skip("MongoDB not available")

    import app as app_module
    importlib.reload(app_module)
    app_module.app.config["TESTING"] = True
    yield app_module
    try:
        app_module.client.drop_database("aceit_test_db")
    except Exception:  # noqa: BLE001
        pass


@pytest.fixture()
def client(app_module):
    return app_module.app.test_client()


@pytest.fixture()
def auth(app_module):
    """An authenticated client + csrf for a fresh verified user."""
    import uuid
    c = app_module.app.test_client()
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    user, csrf = register_verify_login(c, app_module.db, email)
    return c, csrf, user


# --- Public endpoints ------------------------------------------------------
def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_questions_public_and_filterable(client):
    r = client.get("/api/questions?category=Technical&subcategory=DBMS")
    assert r.status_code == 200
    data = r.get_json()
    assert data["categories"] == ["HR", "Behavioural", "Technical", "Situational"]
    assert all(q["category"] == "Technical" for q in data["questions"])


def test_model_info_public(client):
    r = client.get("/api/model-info")
    assert r.status_code == 200
    assert len(r.get_json()["models"]) == 3


# --- Protected endpoints require auth --------------------------------------
def test_history_requires_auth(client):
    assert client.get("/api/history").status_code == 401
    assert client.post("/api/history", json={"question": "Q"}).status_code == 401


def test_progress_requires_auth(client):
    assert client.get("/api/progress").status_code == 401


def test_history_save_and_fetch_authenticated(auth):
    c, csrf, _ = auth
    r = c.post("/api/history",
               json={"question": "Q", "overall_score": 7.5, "confidence": 8.0},
               headers={"X-CSRF-Token": csrf})
    assert r.status_code == 200
    r2 = c.get("/api/history")
    assert r2.status_code == 200
    assert any(s["question"] == "Q" for s in r2.get_json())


def test_write_without_csrf_is_rejected(auth):
    c, _csrf, _ = auth
    # Authenticated but missing CSRF header -> 403.
    assert c.post("/api/history", json={"question": "NoCSRF"}).status_code == 403


def test_progress_structure_authenticated(auth):
    c, _csrf, _ = auth
    r = c.get("/api/progress")
    assert r.status_code == 200
    for key in ("total_sessions", "trends", "averages", "strongest_metric",
                "weakest_metric", "streak", "recent"):
        assert key in r.get_json()


def test_mock_flow_authenticated(auth):
    c, csrf, _ = auth
    r = c.post("/api/mock-interview/start", json={"count": 3}, headers={"X-CSRF-Token": csrf})
    assert r.status_code == 200
    mock_id = r.get_json()["mock_id"]
    c.post(f"/api/mock-interview/{mock_id}/answer",
           json={"overall_score": 7.0}, headers={"X-CSRF-Token": csrf})
    c.post(f"/api/mock-interview/{mock_id}/answer",
           json={"overall_score": 6.0}, headers={"X-CSRF-Token": csrf})
    r2 = c.post(f"/api/mock-interview/{mock_id}/complete", headers={"X-CSRF-Token": csrf})
    assert r2.status_code == 200
    assert r2.get_json()["report"]["questions_answered"] == 2


def test_analyze_requires_transcript_authenticated(auth):
    c, csrf, _ = auth
    r = c.post("/api/analyze", json={"question": "Q", "transcript": ""},
               headers={"X-CSRF-Token": csrf})
    assert r.status_code == 400


def test_invalid_session_id_authenticated(auth):
    c, _csrf, _ = auth
    assert c.get("/api/sessions/not-a-valid-id").status_code == 400
