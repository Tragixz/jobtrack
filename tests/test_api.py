from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app


@pytest.fixture
def client():
    # Each test gets a fresh in-memory database, so tests never touch your real data.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_application(client, **overrides):
    data = {"company": "Acme", "role": "Backend Intern", **overrides}
    response = client.post("/applications", json=data)
    assert response.status_code == 201
    return response.json()


def test_create_application(client):
    application = make_application(client)
    assert application["id"] is not None
    assert application["status"] == "applied"
    assert application["applied_on"] == date.today().isoformat()


def test_create_rejects_empty_company(client):
    response = client.post("/applications", json={"company": "", "role": "Dev"})
    assert response.status_code == 422


def test_list_and_filter_by_status(client):
    make_application(client, company="A")
    make_application(client, company="B", status="interviewing")

    assert len(client.get("/applications").json()) == 2
    interviewing = client.get("/applications", params={"status": "interviewing"}).json()
    assert [a["company"] for a in interviewing] == ["B"]


def test_get_missing_application_returns_404(client):
    assert client.get("/applications/999").status_code == 404


def test_update_application(client):
    application = make_application(client)
    response = client.patch(f"/applications/{application['id']}", json={"status": "offer"})
    assert response.status_code == 200
    assert response.json()["status"] == "offer"
    assert response.json()["company"] == "Acme"


def test_delete_application(client):
    application = make_application(client)
    assert client.delete(f"/applications/{application['id']}").status_code == 204
    assert client.get(f"/applications/{application['id']}").status_code == 404


def test_stats(client):
    make_application(client)
    make_application(client, status="interviewing")
    stats = client.get("/stats").json()
    assert stats["total"] == 2
    assert stats["by_status"]["interviewing"] == 1
    assert stats["response_rate"] == 50.0


def test_follow_ups(client):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    next_week = (date.today() + timedelta(days=7)).isoformat()
    make_application(client, company="Due", follow_up_on=yesterday)
    make_application(client, company="Later", follow_up_on=next_week)
    make_application(client, company="Closed", follow_up_on=yesterday, status="rejected")

    due = client.get("/follow-ups").json()
    assert [a["company"] for a in due] == ["Due"]


def test_export_csv(client):
    make_application(client)
    response = client.get("/export")
    assert response.status_code == 200
    assert "Acme" in response.text

def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "JobTrack" in response.text

def signup(client, username="alice", password="password123"):
    return client.post("/auth/signup", json={"username": username, "password": password})


def login(client, username="alice", password="password123"):
    return client.post("/auth/login", data={"username": username, "password": password})


def test_signup_and_login(client):
    response = signup(client)
    assert response.status_code == 201
    assert "password" not in response.json()
    assert "hashed_password" not in response.json()

    response = login(client)
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "alice"


def test_signup_rejects_duplicate_username(client):
    signup(client)
    assert signup(client).status_code == 409


def test_signup_rejects_short_password(client):
    assert signup(client, password="short").status_code == 422


def test_login_rejects_wrong_password(client):
    signup(client)
    assert login(client, password="wrong-password").status_code == 401


def test_me_requires_login(client):
    assert client.get("/auth/me").status_code == 401


def test_me_rejects_fake_token(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 401