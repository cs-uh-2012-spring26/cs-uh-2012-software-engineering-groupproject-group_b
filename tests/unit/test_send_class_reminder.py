from http import HTTPStatus
import pytest
from bson import ObjectId
from app.apis import MSG
from app.db.classes import (
    ClassResource,
    CLASS_TRAINER_ID,
    CLASS_USER_IDS,
    CLASS_NAME,
    CLASS_DESCRIPTION,
    CLASS_DATE,
    CLASS_START_TIME,
    CLASS_END_TIME,
    CLASS_ROOM_NUMBER,
    CLASS_CAPACITY,
    TRAINER_NAME,
)
from app.db.users import UserResource


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _class_doc(trainer_id, user_ids):
    return {
        CLASS_NAME: "Yoga",
        CLASS_DESCRIPTION: "A yoga class",
        TRAINER_NAME: "Test Trainer",
        CLASS_DATE: "2099-01-01",
        CLASS_START_TIME: "10:00",
        CLASS_END_TIME: "11:00",
        CLASS_ROOM_NUMBER: "101",
        CLASS_CAPACITY: 10,
        CLASS_TRAINER_ID: trainer_id,
        CLASS_USER_IDS: user_ids,
    }


@pytest.fixture
def seeded_class_with_members():
    user_resource = UserResource()
    uid1 = user_resource.create_user("Alice", "alice@example.com", "member")
    uid2 = user_resource.create_user("Bob", "bob@example.com", "member")

    class_resource = ClassResource()
    class_oid = class_resource.collection.insert_one(
        _class_doc("testId", [uid1, uid2])
    ).inserted_id

    yield str(class_oid), ["alice@example.com", "bob@example.com"]

    user_resource.collection.delete_many({"_id": {"$in": [uid1, uid2]}})
    class_resource.collection.delete_one({"_id": class_oid})


@pytest.fixture
def seeded_empty_class():
    class_resource = ClassResource()
    class_oid = class_resource.collection.insert_one(
        _class_doc("testId", [])
    ).inserted_id

    yield str(class_oid)

    class_resource.collection.delete_one({"_id": class_oid})


@pytest.fixture
def seeded_class_wrong_trainer():
    class_resource = ClassResource()
    class_oid = class_resource.collection.insert_one(
        _class_doc("other-trainer", [])
    ).inserted_id

    yield str(class_oid)

    class_resource.collection.delete_one({"_id": class_oid})


def test_remind_no_auth(client):
    resp = client.post(f"/classes/{str(ObjectId())}/remind")
    assert resp.status_code != HTTPStatus.OK


def test_remind_member_forbidden(client, member_token):
    resp = client.post(f"/classes/{str(ObjectId())}/remind", headers=_auth(member_token))
    assert resp.status_code == HTTPStatus.FORBIDDEN


def test_remind_class_not_found(client, trainer_token):
    resp = client.post(f"/classes/{str(ObjectId())}/remind", headers=_auth(trainer_token))
    assert resp.status_code == HTTPStatus.NOT_FOUND
    assert resp.json[MSG] == "Class not found"


def test_remind_wrong_trainer(client, trainer_token, seeded_class_wrong_trainer):
    resp = client.post(
        f"/classes/{seeded_class_wrong_trainer}/remind", headers=_auth(trainer_token)
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN
    assert resp.json[MSG] == "You are not the trainer assigned to this class"


def test_remind_no_members(client, trainer_token, mocker, seeded_empty_class):
    mock_dispatch = mocker.patch("app.apis.classes.NotificationDispatcher")

    resp = client.post(f"/classes/{seeded_empty_class}/remind", headers=_auth(trainer_token))

    assert resp.status_code == HTTPStatus.OK
    assert resp.json["sent_to"] == []
    assert resp.json["failed"] == []
    mock_dispatch.return_value.dispatch_to_member.assert_not_called()


def test_remind_all_success(client, trainer_token, mocker, seeded_class_with_members):
    class_id, member_emails = seeded_class_with_members
    mock_dispatch = (
        mocker.patch("app.apis.classes.NotificationDispatcher")
        .return_value.dispatch_to_member
    )
    mock_dispatch.return_value = (True, [])

    resp = client.post(f"/classes/{class_id}/remind", headers=_auth(trainer_token))

    assert resp.status_code == HTTPStatus.OK
    assert sorted(resp.json["sent_to"]) == sorted(member_emails)
    assert resp.json["failed"] == []
    assert mock_dispatch.call_count == 2


def test_remind_partial_failure(client, trainer_token, mocker, seeded_class_with_members):
    class_id, _ = seeded_class_with_members
    mock_dispatch = (
        mocker.patch("app.apis.classes.NotificationDispatcher")
        .return_value.dispatch_to_member
    )
    mock_dispatch.side_effect = [
        (True, []),
        (False, ["[email] SES error"]),
    ]

    resp = client.post(f"/classes/{class_id}/remind", headers=_auth(trainer_token))

    assert resp.status_code == HTTPStatus.OK
    assert len(resp.json["sent_to"]) == 1
    assert len(resp.json["failed"]) == 1
    assert resp.json["failed"][0]["errors"] == ["[email] SES error"]


def test_remind_all_failures(client, trainer_token, mocker, seeded_class_with_members):
    class_id, _ = seeded_class_with_members
    mock_dispatch = (
        mocker.patch("app.apis.classes.NotificationDispatcher")
        .return_value.dispatch_to_member
    )
    mock_dispatch.return_value = (False, ["[email] delivery failed"])

    resp = client.post(f"/classes/{class_id}/remind", headers=_auth(trainer_token))

    assert resp.status_code == HTTPStatus.OK
    assert resp.json["sent_to"] == []
    assert len(resp.json["failed"]) == 2
    assert resp.json[MSG] == "Reminders processed: 0 sent, 2 with failures"
