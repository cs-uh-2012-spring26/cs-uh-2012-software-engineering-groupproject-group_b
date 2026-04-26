from http import HTTPStatus
import pytest
from bson import ObjectId
from flask_jwt_extended import create_access_token
from app.apis import MSG
from app.db.users import UserResource, USER_NOTIFICATION_PREFS, USER_TELEGRAM_CHAT_ID


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def member_with_token(app):
    user_resource = UserResource()
    uid = user_resource.create_user("Test Member", "testmember@example.com", "member")

    with app.app_context():
        token = create_access_token(
            identity=str(uid), additional_claims={"role": "member"}
        )

    yield token, str(uid)

    user_resource.collection.delete_one({"_id": uid})


def test_prefs_no_auth(client):
    resp = client.put("/users/me/notifications", json={"notification_prefs": {"email": True}})
    assert resp.status_code != HTTPStatus.OK


def test_prefs_wrong_role_forbidden(client, app):
    with app.app_context():
        guest_token = create_access_token(
            identity="testId", additional_claims={"role": "guest"}
        )
    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {"email": True}},
        headers=_auth(guest_token),
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_prefs_missing_prefs_key(client, member_token):
    resp = client.put("/users/me/notifications", json={}, headers=_auth(member_token))
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "email" in resp.json[MSG] and "telegram" in resp.json[MSG]


def test_prefs_empty_prefs(client, member_token):
    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {}},
        headers=_auth(member_token),
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_prefs_unknown_channels_only(client, member_token):
    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {"sms": True}},
        headers=_auth(member_token),
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_prefs_telegram_no_chat_id(client, member_token):
    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {"telegram": True}},
        headers=_auth(member_token),
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert "telegram_chat_id" in resp.json[MSG]


def test_prefs_telegram_empty_chat_id(client, member_token):
    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {"telegram": True}, "telegram_chat_id": "   "},
        headers=_auth(member_token),
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_prefs_email_only(client, member_with_token):
    token, user_id = member_with_token

    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {"email": True}},
        headers=_auth(token),
    )

    assert resp.status_code == HTTPStatus.OK
    user = UserResource().get_user_by_id(user_id)
    assert user[USER_NOTIFICATION_PREFS] == {"email": True}
    assert USER_TELEGRAM_CHAT_ID not in user


def test_prefs_telegram_with_chat_id(client, member_with_token):
    token, user_id = member_with_token

    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {"telegram": True}, "telegram_chat_id": "12345"},
        headers=_auth(token),
    )

    assert resp.status_code == HTTPStatus.OK
    user = UserResource().get_user_by_id(user_id)
    assert user[USER_NOTIFICATION_PREFS] == {"telegram": True}
    assert user[USER_TELEGRAM_CHAT_ID] == "12345"


def test_prefs_telegram_disabled(client, member_with_token):
    token, user_id = member_with_token

    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {"telegram": False}},
        headers=_auth(token),
    )

    assert resp.status_code == HTTPStatus.OK
    user = UserResource().get_user_by_id(user_id)
    assert user[USER_NOTIFICATION_PREFS] == {"telegram": False}
    assert user.get(USER_TELEGRAM_CHAT_ID) is None


def test_prefs_user_not_found(client, app):
    with app.app_context():
        token = create_access_token(
            identity=str(ObjectId()),
            additional_claims={"role": "member"},
        )

    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {"email": True}},
        headers=_auth(token),
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_prefs_db_error(client, member_token):
    # member_token identity is "testId" — not a valid ObjectId
    # → update_notification_prefs catches the ObjectId error → returns 400
    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {"email": True}},
        headers=_auth(member_token),
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST
