from http import HTTPStatus
import pytest
from app.apis import MSG
from app.db.classes import CLASS_TRAINER_ID


_CLASS = {
    CLASS_TRAINER_ID: "testId",
    "user_ids": ["uid-1", "uid-2"],
    "name": "Yoga",
}

_MEMBERS = [
    {"email": "alice@example.com", "name": "Alice"},
    {"email": "bob@example.com",   "name": "Bob"},
]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_remind_no_auth(client):
    resp = client.post("/classes/class-1/remind")
    assert resp.status_code != HTTPStatus.OK


def test_remind_member_forbidden(client, member_token):
    resp = client.post("/classes/class-1/remind", headers=_auth(member_token))
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_remind_class_not_found(client, trainer_token, mocker):
    mocker.patch("app.apis.classes.ClassResource").return_value.get_class_by_id.return_value = None

    resp = client.post("/classes/missing-id/remind", headers=_auth(trainer_token))

    assert resp.status_code == HTTPStatus.NOT_FOUND
    assert resp.json[MSG] == "Class not found"


def test_remind_wrong_trainer(client, trainer_token, mocker):
    mocker.patch("app.apis.classes.ClassResource").return_value.get_class_by_id.return_value = {
        CLASS_TRAINER_ID: "someone-else",
        "user_ids": ["uid-1"],
    }

    resp = client.post("/classes/class-1/remind", headers=_auth(trainer_token))

    assert resp.status_code == HTTPStatus.FORBIDDEN
    assert resp.json[MSG] == "You are not the trainer assigned to this class"


def test_remind_no_members(client, trainer_token, mocker):
    mocker.patch("app.apis.classes.ClassResource").return_value.get_class_by_id.return_value = {
        CLASS_TRAINER_ID: "testId",
        "user_ids": [],
    }
    mock_dispatcher = mocker.patch("app.apis.classes.NotificationDispatcher")

    resp = client.post("/classes/class-1/remind", headers=_auth(trainer_token))

    assert resp.status_code == HTTPStatus.OK
    assert resp.json["sent_to"] == []
    assert resp.json["failed"] == []
    mock_dispatcher.return_value.dispatch_to_member.assert_not_called()


def test_remind_all_success(client, trainer_token, mocker):
    mocker.patch("app.apis.classes.ClassResource").return_value.get_class_by_id.return_value = _CLASS
    mocker.patch("app.apis.classes.UserResource").return_value.get_users_by_ids.return_value = _MEMBERS
    mock_dispatch = mocker.patch("app.apis.classes.NotificationDispatcher").return_value.dispatch_to_member
    mock_dispatch.return_value = (True, [])

    resp = client.post("/classes/class-1/remind", headers=_auth(trainer_token))

    assert resp.status_code == HTTPStatus.OK
    assert resp.json["sent_to"] == ["alice@example.com", "bob@example.com"]
    assert resp.json["failed"] == []
    assert mock_dispatch.call_count == 2


def test_remind_partial_failure(client, trainer_token, mocker):
    mocker.patch("app.apis.classes.ClassResource").return_value.get_class_by_id.return_value = _CLASS
    mocker.patch("app.apis.classes.UserResource").return_value.get_users_by_ids.return_value = _MEMBERS
    mock_dispatch = mocker.patch("app.apis.classes.NotificationDispatcher").return_value.dispatch_to_member
    mock_dispatch.side_effect = [
        (True, []),
        (False, ["[email] SES error"]),
    ]

    resp = client.post("/classes/class-1/remind", headers=_auth(trainer_token))

    assert resp.status_code == HTTPStatus.OK
    assert resp.json["sent_to"] == ["alice@example.com"]
    assert len(resp.json["failed"]) == 1
    assert resp.json["failed"][0]["member"] == "bob@example.com"
    assert resp.json["failed"][0]["errors"] == ["[email] SES error"]


def test_remind_all_failures(client, trainer_token, mocker):
    mocker.patch("app.apis.classes.ClassResource").return_value.get_class_by_id.return_value = _CLASS
    mocker.patch("app.apis.classes.UserResource").return_value.get_users_by_ids.return_value = _MEMBERS
    mock_dispatch = mocker.patch("app.apis.classes.NotificationDispatcher").return_value.dispatch_to_member
    mock_dispatch.return_value = (False, ["[email] delivery failed"])

    resp = client.post("/classes/class-1/remind", headers=_auth(trainer_token))

    assert resp.status_code == HTTPStatus.OK
    assert resp.json["sent_to"] == []
    assert len(resp.json["failed"]) == 2
    assert resp.json[MSG] == "Reminders processed: 0 sent, 2 with failures"
