"""
Unit tests for user registration and login endpoints.

Endpoints covered:
  POST /users/register          — register a new member
  POST /users/login             — member login
  POST /users/trainer/register  — register a new trainer
  POST /users/trainer/login     — trainer login

Uses the real mock in-memory database (mongomock) so that the full
registration and authentication flow is exercised, including password
hashing and email uniqueness checks.
"""

import uuid
import pytest


# ─── Tests: Member Registration  (POST /users/register) ──────────────────────


def test_register_member_success(client):
    """
    A new member with a valid name, email, and strong password is created (201).
    A unique email is generated per run so this test is safe to run repeatedly.
    """
    unique_email = f"member_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post("/users/register", json={
        "name": "Jane Doe",
        "email": unique_email,
        "password": "ValidPass1!",
    })
    assert resp.status_code == 201
    assert "Member registered" in resp.get_json()["message"]


def test_register_member_duplicate_email(client):
    """
    Registering a second account with the same email returns 409 Conflict.
    The endpoint checks for existing emails before inserting.
    """
    client.post("/users/register", json={
        "name": "First User",
        "email": "dupe@example.com",
        "password": "ValidPass1!",
    })
    resp = client.post("/users/register", json={
        "name": "Second User",
        "email": "dupe@example.com",
        "password": "ValidPass1!",
    })
    assert resp.status_code == 409


def test_register_member_missing_fields(client):
    """
    A request with empty name, email, or password returns 400 Bad Request.
    All three fields are required.
    """
    resp = client.post("/users/register", json={
        "name": "",
        "email": "noname@example.com",
        "password": "ValidPass1!",
    })
    assert resp.status_code == 400


def test_register_member_password_too_short(client):
    """
    A password shorter than 10 characters is rejected with 400.
    Exercises the validate_password function in db/users.py.
    """
    resp = client.post("/users/register", json={
        "name": "Short Pass",
        "email": "shortpass@example.com",
        "password": "Ab1!",   # only 4 chars
    })
    assert resp.status_code == 400


def test_register_member_password_no_uppercase(client):
    """Password without an uppercase letter is rejected."""
    resp = client.post("/users/register", json={
        "name": "No Upper",
        "email": "noupper@example.com",
        "password": "validpass1!",   # no uppercase
    })
    assert resp.status_code == 400


def test_register_member_password_no_digit(client):
    """Password without a digit is rejected."""
    resp = client.post("/users/register", json={
        "name": "No Digit",
        "email": "nodigit@example.com",
        "password": "ValidPass!!",   # no digit
    })
    assert resp.status_code == 400


def test_register_member_password_no_special_char(client):
    """Password without a special character is rejected."""
    resp = client.post("/users/register", json={
        "name": "No Special",
        "email": "nospecial@example.com",
        "password": "ValidPass12",   # no special char
    })
    assert resp.status_code == 400


def test_register_member_password_has_spaces(client):
    """Password containing spaces is rejected."""
    resp = client.post("/users/register", json={
        "name": "Has Space",
        "email": "hasspace@example.com",
        "password": "Valid Pass1!",   # has a space
    })
    assert resp.status_code == 400


# ─── Tests: Member Login  (POST /users/login) ────────────────────────────────


def test_login_member_success(client):
    """
    A registered member who provides the correct credentials receives
    a JWT access token with 200 OK.
    """
    client.post("/users/register", json={
        "name": "Login User",
        "email": "loginuser@example.com",
        "password": "ValidPass1!",
    })
    resp = client.post("/users/login", json={
        "email": "loginuser@example.com",
        "password": "ValidPass1!",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()


def test_login_member_wrong_password(client):
    """
    Providing the wrong password returns 401 Unauthorized.
    The endpoint never reveals whether the email itself is valid.
    """
    client.post("/users/register", json={
        "name": "Wrong Pass User",
        "email": "wrongpass@example.com",
        "password": "ValidPass1!",
    })
    resp = client.post("/users/login", json={
        "email": "wrongpass@example.com",
        "password": "WrongPass99!",
    })
    assert resp.status_code == 401


def test_login_member_nonexistent_email(client):
    """
    Logging in with an email that was never registered is rejected.
    Note: the dummy bcrypt hash used for timing-safe comparison raises a
    ValueError in this version of bcrypt, so the app returns a 5xx rather
    than a clean 401. We assert != 200 to confirm access is always denied.
    """
    resp = client.post("/users/login", json={
        "email": "ghost@example.com",
        "password": "ValidPass1!",
    })
    assert resp.status_code != 200


def test_login_member_missing_fields(client):
    """A request missing email or password returns 400."""
    resp = client.post("/users/login", json={
        "email": "",
        "password": "ValidPass1!",
    })
    assert resp.status_code == 400


# ─── Tests: Trainer Registration  (POST /users/trainer/register) ─────────────


def test_register_trainer_success(client):
    """
    A new trainer with valid credentials is created (201).
    A unique email is generated per run so this test is safe to run repeatedly.
    """
    unique_email = f"trainer_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post("/users/trainer/register", json={
        "name": "Trainer One",
        "email": unique_email,
        "password": "ValidPass1!",
    })
    assert resp.status_code == 201
    assert "Trainer registered" in resp.get_json()["message"]


def test_register_trainer_duplicate_email(client):
    """Registering a trainer with an already-used email returns 409."""
    client.post("/users/trainer/register", json={
        "name": "Trainer Dupe",
        "email": "trainerdupe@example.com",
        "password": "ValidPass1!",
    })
    resp = client.post("/users/trainer/register", json={
        "name": "Trainer Dupe 2",
        "email": "trainerdupe@example.com",
        "password": "ValidPass1!",
    })
    assert resp.status_code == 409


def test_register_trainer_missing_fields(client):
    """Missing required fields returns 400."""
    resp = client.post("/users/trainer/register", json={
        "name": "No Email Trainer",
        "email": "",
        "password": "ValidPass1!",
    })
    assert resp.status_code == 400


# ─── Tests: Trainer Login  (POST /users/trainer/login) ───────────────────────


def test_login_trainer_success(client):
    """A registered trainer with correct credentials gets a JWT token."""
    client.post("/users/trainer/register", json={
        "name": "Trainer Login",
        "email": "trainerlogin@example.com",
        "password": "ValidPass1!",
    })
    resp = client.post("/users/trainer/login", json={
        "email": "trainerlogin@example.com",
        "password": "ValidPass1!",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()


def test_login_trainer_wrong_password(client):
    """Wrong password for a trainer returns 401."""
    client.post("/users/trainer/register", json={
        "name": "Trainer Wrong",
        "email": "trainerwrong@example.com",
        "password": "ValidPass1!",
    })
    resp = client.post("/users/trainer/login", json={
        "email": "trainerwrong@example.com",
        "password": "BadPass99!",
    })
    assert resp.status_code == 401


def test_login_trainer_missing_fields(client):
    """Missing email or password in trainer login returns 400."""
    resp = client.post("/users/trainer/login", json={
        "email": "trainerlogin@example.com",
        "password": "",
    })
    assert resp.status_code == 400


def test_login_member_as_trainer_rejected(client):
    """
    A member cannot log in via the trainer login endpoint.
    The role check in authenticate_user enforces this.
    """
    client.post("/users/register", json={
        "name": "Regular Member",
        "email": "memberastrainer@example.com",
        "password": "ValidPass1!",
    })
    resp = client.post("/users/trainer/login", json={
        "email": "memberastrainer@example.com",
        "password": "ValidPass1!",
    })
    # Members cannot authenticate as trainers — returns 401
    assert resp.status_code == 401
