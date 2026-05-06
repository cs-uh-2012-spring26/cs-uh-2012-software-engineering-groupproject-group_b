"""
Unit tests for user endpoints.

Endpoints covered:
  POST /users/me/book/<class_id>  — book a class
  GET  /users/me/book             — get classes the current member is enrolled in
  PUT  /users/me/notifications    — update notification preferences
"""

import json
import pytest
import uuid
from datetime import datetime, timedelta
from http import HTTPStatus
from unittest.mock import MagicMock, patch
from flask_jwt_extended import create_access_token, decode_token
from app.db.users import UserResource, USER_TELEGRAM_CHAT_ID, USER_NOTIFICATION_PREFS
from app.apis import MSG


# ─── Tests: Book a class  (POST /users/me/book/<class_id>) ────────────────────


def test_book_class_success(client, member_auth, seeded_class):
    """A valid member can book an available class and gets 200."""
    headers = {"Authorization": f"Bearer {member_auth}"}
    resp = client.post(f"/users/me/book/{seeded_class}", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[MSG] == "Booked successfully"


def test_book_class_no_token(client, seeded_class):
    """Booking without a JWT returns 401 Unauthorized."""
    resp = client.post(f"/users/me/book/{seeded_class}")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


def test_book_class_already_booked(client, member_auth, seeded_class):
    """Booking the same class twice returns 409 Conflict."""
    headers = {"Authorization": f"Bearer {member_auth}"}
    client.post(f"/users/me/book/{seeded_class}", headers=headers)
    resp = client.post(f"/users/me/book/{seeded_class}", headers=headers)
    assert resp.status_code == HTTPStatus.CONFLICT
    assert resp.get_json()[MSG] == "User already booked this class"


def test_book_class_not_found(client, member_auth):
    """Booking a class ID that does not exist returns 404."""
    headers = {"Authorization": f"Bearer {member_auth}"}
    fake_id = "000000000000000000000001"
    resp = client.post(f"/users/me/book/{fake_id}", headers=headers)
    assert resp.status_code == HTTPStatus.NOT_FOUND

def test_book_class_full(client, seeded_class,trainer_token):
    """Booking a full class returns 409 Class is full."""
    headers_trainer = {"Authorization": f"Bearer {trainer_token}"}
    resp = client.post("/classes/", json={ 
        "name": "Full Class", 
        "description":"Only one spot",
        "trainer_name" : "Sam Smith",
        "date": "2030-01-01",
        "start_time": "10:00",
        "end_time": "11:00",
        "room_number": "101",
        "capacity": 1,}, headers=headers_trainer)
    full_class_id = resp.get_json()["message"].split(":")[-1].strip()

    #first member books successfully
    email1 = f"member_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/register", json={
        "name": "Mem1", 
        "email": email1, 
        "password": "Secur3P@ssword",
        "role": "member"})
    token1 = client.post("/auth/login", json={
        "email": email1,
        "password": "Secur3P@ssword"}).get_json()["access_token"]
    client.post(f"/users/me/book/{full_class_id}", headers={"Authorization": f"Bearer {token1}"})
    

    #second member gets 409 
    email2 = f"member_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/auth/register", json={
        "name": "Mem2", 
        "email": email2, 
        "password": "Secur3P@ssword",
        "role": "member"})
    token2 = client.post("/auth/login", json={
        "email": email2,
        "password": "Secur3P@ssword"}).get_json()["access_token"]
    resp = client.post(f"/users/me/book/{full_class_id}", headers={"Authorization": f"Bearer {token2}"})
   
    assert resp.status_code == HTTPStatus.CONFLICT
    assert resp.get_json()[MSG] == "Class is full"

def test_book_class_user_not_found(client, seeded_class, app):
    """Booking with a JWT whose identity has no matching user returns 404."""
    with app.app_context():
        ghost_token = create_access_token(
            identity="000000000000000000000099",
            additional_claims={"role":"member"},
        )
    headers = {"Authorization": f"Bearer {ghost_token}"}
    resp = client.post(f"/users/me/book/{seeded_class}", headers=headers)

    assert resp.status_code == HTTPStatus.NOT_FOUND
    assert resp.get_json()[MSG] == "User not found"
    


# ─── Tests: Get enrolled classes  (GET /users/me/book) ────────────────────────


def test_get_enrolled_classes_empty(client, member_auth):
    """A newly registered member with no bookings receives an empty list."""
    headers = {"Authorization": f"Bearer {member_auth}"}
    resp = client.get("/users/me/book", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json() == []


def test_get_enrolled_classes_after_booking(client, member_auth, seeded_class):
    """After booking a class it appears in the enrolled list."""
    headers = {"Authorization": f"Bearer {member_auth}"}
    client.post(f"/users/me/book/{seeded_class}", headers=headers)

    resp = client.get("/users/me/book", headers=headers)
    assert resp.status_code == HTTPStatus.OK
    classes = resp.get_json()
    assert len(classes) == 1
    assert classes[0]["_id"] == seeded_class


def test_get_enrolled_classes_no_token(client):
    """Getting enrolled classes without a JWT returns 401."""
    resp = client.get("/users/me/book")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED

def test_get_enrolled_classes_invalid_id_format(client,member_token):
    """A JWT with a non-ObjectId identity returns 400 and Bad Request."""
    headers = {"Authorization": f"Bearer {member_token}"}
    resp = client.get("/users/me/book", headers=headers)
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.get_json()[MSG] == "Invalid user ID format"

def test_get_enrolled_classes_returns_list(client, member_auth, seeded_class):
    """Enrolled classes return a list after booking."""
    headers = {"Authorization": f"Bearer {member_auth}"}
    client.post(f"/users/me/book{seeded_class}", headers=headers)
    resp = client.get("/users/me/book", headers=headers)
    assert isinstance(resp.get_json(),list)

def test_get_enrolled_classes_empty_identity(client, app):
    """JWT with empty identity returns 401."""
    with app.app_context():
        token = create_access_token(identity="", additional_claims={"role": "member"})
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/users/me/book", headers=headers)
    assert resp.status_code == HTTPStatus.UNAUTHORIZED

# ─── Tests: Update notification preferences  (PUT /users/me/notifications) ────


def test_update_notifications_email_only(client, member_auth):
    """Enabling email notifications returns 200 with a success message."""
    headers = {"Authorization": f"Bearer {member_auth}"}
    resp = client.put("/users/me/notifications", json={
        "notification_prefs": {"email": True},
    }, headers=headers)
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[MSG] == "Notification preferences updated"


def test_update_notifications_telegram_with_chat_id(client, member_auth, app):
    """Enabling Telegram succeeds when telegram_chat_id is already in the DB."""
    with app.app_context():
        user_id = decode_token(member_auth)["sub"]
    UserResource().update_notification_prefs(user_id, {USER_TELEGRAM_CHAT_ID: "123456789"})

    headers = {"Authorization": f"Bearer {member_auth}"}
    resp = client.put("/users/me/notifications", json={
        "notification_prefs": {"telegram": True},
    }, headers=headers)
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[MSG] == "Notification preferences updated"


def test_update_notifications_telegram_missing_chat_id(client, member_auth):
    """Enabling Telegram without a chat_id returns 400."""
    headers = {"Authorization": f"Bearer {member_auth}"}
    resp = client.put("/users/me/notifications", json={
        "notification_prefs": {"telegram": True},
    }, headers=headers)
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "telegram_chat_id" in resp.get_json()[MSG]


def test_update_notifications_empty_prefs(client, member_auth):
    """Sending an empty notification_prefs object returns 400."""
    headers = {"Authorization": f"Bearer {member_auth}"}
    resp = client.put("/users/me/notifications", json={
        "notification_prefs": {},
    }, headers=headers)
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_update_notifications_no_token(client):
    """Updating notifications without a JWT returns 401."""
    resp = client.put("/users/me/notifications", json={
        "notification_prefs": {"email": True},
    })
    assert resp.status_code == HTTPStatus.UNAUTHORIZED

def test_update_notifications_unkown_channel(client,member_token):
    """Sending an unrecognized channel key return 400."""
    headers = {"Authorization": f"Bearer {member_token}"}
    resp = client.put("/users/me/notifications", json={
        "notification_prefs": {"sms": True},},headers=headers)
    assert resp.status_code == HTTPStatus.BAD_REQUEST

def test_update_notifications_telegram_disabled_no_chat_id_needed(client, member_auth):
    """Disabling telegram does not require a chat_id and returns 200."""
    headers = {"Authorization": f"Bearer {member_auth}"}
    resp = client.put("/users/me/notifications", json={
        "notification_prefs": {"telegram": False},
    }, headers=headers)

    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[MSG] == "Notification preferences updated"

def test_update_notifications_telegram_whitespace_chat_id(client, member_auth):
    """Enabling telegram with a whitespace chat_id returns 400."""
    headers = {"Authorization": f"Bearer {member_auth}"}
    resp = client.put("/users/me/notifications", json={
        "notification_prefs": {"telegram": True}, 
        "telegram_chat_id": " ",
    }, headers=headers)
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "telegram_chat_id" in resp.get_json()[MSG] 


def test_update_notifications_persisted_in_db(client, member_auth, app):
    """After a successful PUT, preferences are actually saved in the DB."""

    headers = {"Authorization": f"Bearer {member_auth}"}
    client.put("/users/me/notifications", json={
        "notification_prefs": {"email": True},
    }, headers=headers)

    with app.app_context():
        user_id = decode_token(member_auth)["sub"]
        user = UserResource().get_user_by_id(user_id)

    assert user["notification_prefs"] == {"email": True}


# ─── Tests: Generate Telegram link  (GET /users/me/telegram/link) ─────────────


def _mock_get_me(bot_username="test_bot"):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(
        {"ok": True, "result": {"username": bot_username}}
    ).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_telegram_link_no_auth(client):
    """Calling the link endpoint without a JWT returns non-200."""
    resp = client.get("/users/me/telegram/link")
    assert resp.status_code != HTTPStatus.OK


def test_telegram_link_user_not_found(client, app):
    """A JWT with a valid-format but non-existent user ID returns 404."""
    with app.app_context():
        token = create_access_token(
            identity=str(__import__("bson").ObjectId()),
            additional_claims={"role": "member"},
        )
    resp = client.get("/users/me/telegram/link", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_telegram_link_success(client, member_auth):
    """A valid member gets a deep link containing the bot username and a token."""
    with patch("app.apis.users.urllib.request.urlopen", return_value=_mock_get_me("test_bot")):
        resp = client.get(
            "/users/me/telegram/link",
            headers={"Authorization": f"Bearer {member_auth}"},
        )
    assert resp.status_code == HTTPStatus.OK
    data = resp.get_json()
    assert "https://t.me/test_bot?start=" in data["link"]
    assert data["expires_in"] == 600


def test_telegram_link_telegram_api_fails(client, member_auth):
    """If the Telegram getMe call fails the endpoint returns 500."""
    with patch("app.apis.users.urllib.request.urlopen", side_effect=Exception("timeout")):
        resp = client.get(
            "/users/me/telegram/link",
            headers={"Authorization": f"Bearer {member_auth}"},
        )
    assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert "Could not reach Telegram API" in resp.get_json()[MSG]


# ─── Tests: Telegram webhook  (POST /users/telegram/webhook) ──────────────────


def test_webhook_empty_body(client):
    """An empty update body is accepted and returns 200."""
    resp = client.post("/users/telegram/webhook", json={})
    assert resp.status_code == HTTPStatus.OK


def test_webhook_non_start_message(client):
    """A regular message (not /start) is ignored and returns 200."""
    resp = client.post("/users/telegram/webhook", json={
        "message": {"text": "hello", "chat": {"id": 123}}
    })
    assert resp.status_code == HTTPStatus.OK


def test_webhook_invalid_token(client):
    """A /start command with an unknown token returns 200 and saves nothing."""
    resp = client.post("/users/telegram/webhook", json={
        "message": {"text": "/start nonexistent-token", "chat": {"id": 999}}
    })
    assert resp.status_code == HTTPStatus.OK


def test_webhook_valid_token_saves_chat_id(client, member_auth, app):
    """A /start with a valid token saves the chat_id and enables telegram in prefs."""
    with app.app_context():
        user_id = decode_token(member_auth)["sub"]

    # Seed a valid unexpired link token directly into the DB
    from datetime import timezone
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10)
    UserResource().set_telegram_link_token(user_id, "valid-token-abc", expires_at)

    resp = client.post("/users/telegram/webhook", json={
        "message": {"text": "/start valid-token-abc", "chat": {"id": 8888888}}
    })
    assert resp.status_code == HTTPStatus.OK

    user = UserResource().get_user_by_id(user_id)
    assert user[USER_TELEGRAM_CHAT_ID] == "8888888"
    assert user[USER_NOTIFICATION_PREFS]["telegram"] is True


def test_webhook_expired_token_does_not_save(client, member_auth, app):
    """A /start with an expired token returns 200 but does not save the chat_id."""
    with app.app_context():
        user_id = decode_token(member_auth)["sub"]

    from datetime import timezone
    expired_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    UserResource().set_telegram_link_token(user_id, "expired-token-xyz", expired_at)

    resp = client.post("/users/telegram/webhook", json={
        "message": {"text": "/start expired-token-xyz", "chat": {"id": 7777777}}
    })
    assert resp.status_code == HTTPStatus.OK

    user = UserResource().get_user_by_id(user_id)
    assert user.get(USER_TELEGRAM_CHAT_ID) != "7777777"