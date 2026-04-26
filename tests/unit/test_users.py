"""
Unit tests for user endpoints.

Endpoints covered:
  POST /users/me/book/<class_id>  — book a class
  GET  /users/me/book             — get classes the current member is enrolled in
  PUT  /users/me/notifications    — update notification preferences
"""

import pytest
from http import HTTPStatus

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


# ─── Tests: Update notification preferences  (PUT /users/me/notifications) ────


def test_update_notifications_email_only(client, member_auth):
    """Enabling email notifications returns 200 with a success message."""
    headers = {"Authorization": f"Bearer {member_auth}"}
    resp = client.put("/users/me/notifications", json={
        "notification_prefs": {"email": True},
    }, headers=headers)
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json()[MSG] == "Notification preferences updated"


def test_update_notifications_telegram_with_chat_id(client, member_auth):
    """Enabling Telegram with a valid chat ID returns 200."""
    headers = {"Authorization": f"Bearer {member_auth}"}
    resp = client.put("/users/me/notifications", json={
        "notification_prefs": {"telegram": True},
        "telegram_chat_id": "123456789",
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
