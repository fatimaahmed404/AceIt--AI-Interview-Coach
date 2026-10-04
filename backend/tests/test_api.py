"""
Integration tests for the Flask API.

These run against a dedicated throwaway MongoDB database (set via MONGO_DB
before importing the app) so they never touch real session data. If MongoDB
is not reachable the whole module is skipped.
"""
import os
import importlib

import pytest

# Point the app at a throwaway DB BEFORE it is imported.
os.environ["MONGO_DB"] = "aceit_test_db"
# Keep uploads around only in temp during tests.
os.environ.setdefault("DELETE_VIDEO_AFTER_ANALYSIS", "true")


@pytest.fixture(scope="module")
def client():
    try:
        from pymongo import MongoClient
        MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/"),
                    serverSelectionTimeoutMS=1500).admin.command("ping")
    except Exception:  # noqa: BLE001
        pytest.skip("MongoDB not available")

    import app as app_module
    importlib.reload(app_module)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c
    # Clean up the throwaway database.
    try:
        app_module.client.drop_database("aceit_test_db")
    except Exception:  # noqa: BLE001
        pass


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_questions_seeded_and_filterable(client):
    r = client.get("/api/questions?category=Technical&subcategory=DBMS")
    assert r.status_code == 200
    data = r.get_json()
    assert data["categories"] == ["HR", "Behavioural", "Technical", "Situational"]
    assert all(q["category"] == "Technical" for q in data["questions"])


def test_questions_search(client):
    r = client.get("/api/questions?search=deadlock")
    assert r.status_code == 200
    assert r.get_json()["total"] >= 1


def test_history_save_and_fetch(client):
    payload = {"question": "Q", "overall_score": 7.5, "confidence": 8.0,
               "eye_contact_score": 7.0, "posture_score": 6.5}
    r = client.post("/api/history", json=payload)
    assert r.status_code == 200
    assert r.get_json()["saved"] is True

    r2 = client.get("/api/history")
    assert r2.status_code == 200
    assert any(s["question"] == "Q" for s in r2.get_json())


def test_progress_structure(client):
    r = client.get("/api/progress")
    assert r.status_code == 200
    data = r.get_json()
    for key in ("total_sessions", "trends", "averages", "strongest_metric",
                "weakest_metric", "streak", "recent"):
        assert key in data


def test_analyze_requires_transcript(client):
    r = client.post("/api/analyze", json={"question": "Q", "transcript": ""})
    assert r.status_code == 400


def test_analyze_video_requires_file(client):
    r = client.post("/api/analyze-video", data={})
    assert r.status_code == 400


def test_mock_start_and_complete(client):
    r = client.post("/api/mock-interview/start", json={"count": 3})
    assert r.status_code == 200
    mock_id = r.get_json()["mock_id"]

    client.post(f"/api/mock-interview/{mock_id}/answer",
                json={"overall_score": 7.0, "confidence": 8.0})
    client.post(f"/api/mock-interview/{mock_id}/answer",
                json={"overall_score": 6.0, "confidence": 7.0})

    r2 = client.post(f"/api/mock-interview/{mock_id}/complete")
    assert r2.status_code == 200
    report = r2.get_json()["report"]
    assert report["questions_answered"] == 2
    assert report["averages"]["overall_score"] == 6.5


def test_model_info(client):
    r = client.get("/api/model-info")
    assert r.status_code == 200
    data = r.get_json()
    assert "models" in data and len(data["models"]) == 3
    assert all(m["pretrained"] for m in data["models"])


def test_invalid_session_id(client):
    r = client.get("/api/sessions/not-a-valid-id")
    assert r.status_code == 400
