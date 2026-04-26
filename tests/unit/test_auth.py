from http import HTTPStatus
import uuid

from app.apis import MSG



def _register_payload(role: str = "member", email: str = None) -> dict:
    return {
        "name": "Test User",
        "email": email,
        "password": "ValidPass1!",
        "role": role,
    }


def test_register_success_member(client):
    payload = _register_payload("member", "member@example.com")
    response = client.post("/auth/register", json=payload)

    assert response.status_code == HTTPStatus.CREATED
    assert "Member registered successfully with id:" in response.json[MSG]


def test_register_success_trainer(client):
    payload = _register_payload("trainer", "trainer@example.com")
    response = client.post("/auth/register", json=payload)

    assert response.status_code == HTTPStatus.CREATED
    assert "Trainer registered successfully with id:" in response.json[MSG]


def test_register_missing_required_field(client):
    payload = _register_payload("member", "member@example.com")
    payload["name"] = ""
    response = client.post("/auth/register", json=payload)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json[MSG] == "name is required"


def test_register_invalid_role(client):
    payload = _register_payload("admin", "admin@example.com")
    response = client.post("/auth/register", json=payload)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "role must be one of:" in response.json[MSG]


def test_register_weak_password(client):
    payload = _register_payload("member", "member@example.com")
    payload["password"] = "short"
    response = client.post("/auth/register", json=payload)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json[MSG] == "Password must be atleast 10 characters long"


def test_register_duplicate_email(client):
    payload = _register_payload("member", "member@example.com")
    first = client.post("/auth/register", json=payload)
    second = client.post("/auth/register", json=payload)

    assert first.status_code == HTTPStatus.CREATED
    assert second.status_code == HTTPStatus.CONFLICT
    assert second.json[MSG] == "Email already registered"

def test_register_password_no_uppercase(client):
    resp = client.post("/auth/register", json={
        "name": "Test", "email": "test@test.com",
        "password": "validpass1!", "role": "member"
    })
    assert resp.status_code == 400

# LOGIN TESTS

def test_login_success(client):
    payload = _register_payload("member", "member@example.com")
    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == HTTPStatus.CREATED

    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )

    assert login_response.status_code == HTTPStatus.OK
    assert login_response.json[MSG] == "Login successful"
    assert "access_token" in login_response.json


def test_login_missing_fields(client):
    response = client.post(
        "/auth/login",
        json={"email": "", "password": "ValidPass1!"},
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json[MSG] == "email and password are required"


def test_login_wrong_password(client):
    payload = _register_payload("trainer", "trainer@example.com")
    register_response = client.post("/auth/register", json=payload)
    assert register_response.status_code == HTTPStatus.CREATED

    response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": "WrongPass1!"},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json[MSG] == "Invalid email or password"


def test_login_nonexistent_email(client):
    response = client.post(
        "/auth/login",
        json={"email": "ghost@example.com", "password": "ValidPass1!"},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json[MSG] == "Invalid email or password"
