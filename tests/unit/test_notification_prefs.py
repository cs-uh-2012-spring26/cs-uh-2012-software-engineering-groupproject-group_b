from http import HTTPStatus
import pytest
from flask_jwt_extended import create_access_token
from app.apis import MSG
from app.db.users import USER_NOTIFICATION_PREFS, USER_TELEGRAM_CHAT_ID


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


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


def test_prefs_email_only(client, member_token, mocker):
    mock_resource = mocker.patch("app.apis.users.UserResource").return_value
    mock_resource.update_notification_prefs.return_value = (True, "")

    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {"email": True}},
        headers=_auth(member_token),
    )

    assert resp.status_code == HTTPStatus.OK
    mock_resource.update_notification_prefs.assert_called_once_with(
        "testId", {USER_NOTIFICATION_PREFS: {"email": True}}
    )


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
    assert "telegram_chat_id" in resp.json[MSG]


def test_prefs_telegram_with_chat_id(client, member_token, mocker):
    mock_resource = mocker.patch("app.apis.users.UserResource").return_value
    mock_resource.update_notification_prefs.return_value = (True, "")

    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {"telegram": True}, "telegram_chat_id": "12345"},
        headers=_auth(member_token),
    )

    assert resp.status_code == HTTPStatus.OK
    mock_resource.update_notification_prefs.assert_called_once_with(
        "testId",
        {USER_NOTIFICATION_PREFS: {"telegram": True}, USER_TELEGRAM_CHAT_ID: "12345"},
    )


def test_prefs_telegram_disabled_no_chat_id_needed(client, member_token, mocker):
    mock_resource = mocker.patch("app.apis.users.UserResource").return_value
    mock_resource.update_notification_prefs.return_value = (True, "")

    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {"telegram": False}},
        headers=_auth(member_token),
    )

    assert resp.status_code == HTTPStatus.OK
    called_args = mock_resource.update_notification_prefs.call_args[0]
    assert USER_TELEGRAM_CHAT_ID not in called_args[1]


def test_prefs_user_not_found(client, member_token, mocker):
    mock_resource = mocker.patch("app.apis.users.UserResource").return_value
    mock_resource.update_notification_prefs.return_value = (False, "User not found")

    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {"email": True}},
        headers=_auth(member_token),
    )

    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_prefs_db_error(client, member_token, mocker):
    mock_resource = mocker.patch("app.apis.users.UserResource").return_value
    mock_resource.update_notification_prefs.return_value = (False, "Invalid user ID")

    resp = client.put(
        "/users/me/notifications",
        json={"notification_prefs": {"email": True}},
        headers=_auth(member_token),
    )

    assert resp.status_code == HTTPStatus.BAD_REQUEST
