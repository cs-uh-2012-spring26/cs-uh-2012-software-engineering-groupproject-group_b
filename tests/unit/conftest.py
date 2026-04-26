import pytest
import os
from dotenv import load_dotenv
from flask_jwt_extended import create_access_token
from app import create_app
from app.db import DB
import uuid


@pytest.fixture(scope="session", autouse=True)
def app():
    os.environ["MOCK_DB"] = "true"
    load_dotenv(override=False)
    os.environ["MOCK_DB"] = "true"
    load_dotenv(override=False)
    app = create_app()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def trainer_token(app):
    with app.app_context():
        return create_access_token(
            identity="testId",
            additional_claims={"role": "trainer"},
        )


@pytest.fixture
def member_token(app):
    with app.app_context():
        return create_access_token(
            identity="testId",
            additional_claims={"role": "member"},
        )
    
@pytest.fixture
def member_auth(client):
    email = f"memeber_{uuid.uuid4() .hex[:8]}@example.com"
    client.post("/auth/register", json={
        "name": "Test Member",
        "email": email,
        "password": "Secur3P@ssword",
        "role":"member",
    })
    resp = client.post("/auth/login", json={
        "email": email,
        "password":"Secur3P@ssword",
    })
    return resp.get_json()["access_token"]

@pytest.fixture
def seeded_class(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}
    resp = client.post("/classes/", json={
        "name": "HIIT",
        "description": "Intense HIIT full-body session",
        "trainer_name": "Sam Smith",
        "date": "2030-01-01",
        "start_time": "10:00",
        "end_time": "11:00",
        "room_number": "101",
        "capacity": 10,
    }, headers=headers)
    return resp.get_json()["message"].split(":")[-1].strip()
