from http import HTTPStatus

import pytest

from app.apis import MSG
from app.db.classes import (
    CLASS_CAPACITY,
    CLASS_DATE,
    CLASS_DESCRIPTION,
    CLASS_END_TIME,
    CLASS_NAME,
    CLASS_ROOM_NUMBER,
    CLASS_START_TIME,
    CLASS_TRAINER_ID,
    CLASS_USER_IDS,
    TRAINER_NAME,
    ClassResource,
)
from app.db.users import UserResource

def _class_doc(user_ids=None):
    return {
        CLASS_NAME: "Member List Test Class",
        CLASS_DESCRIPTION: "A class for testing member list endpoint",
        TRAINER_NAME: "John Doe",
        CLASS_DATE: "2030-01-01",
        CLASS_START_TIME: "10:00",
        CLASS_END_TIME: "11:00",
        CLASS_ROOM_NUMBER: "101",
        CLASS_CAPACITY: 10,
        CLASS_TRAINER_ID: "testId",
        CLASS_USER_IDS: user_ids or [],
    }

@pytest.fixture
def seeded_members_class():
    user_resource = UserResource()
    member_a_id = user_resource.collection.insert_one(
        {
            "name": "Alice Member",
            "email": "alice@example.com",
            "role": "member",
            "telegram_chat_id": "alice_telegram",
            "class_ids": [],
        }
    ).inserted_id
    member_b_id = user_resource.collection.insert_one(
        {
            "name": "Bob Member",
            "email": "bob@example.com",
            "role": "member",
            "telegram_chat_id": "bob_telegram",
            "class_ids": [],
        }
    ).inserted_id
    class_resource = ClassResource()

    class_id = class_resource.collection.insert_one(
        _class_doc([member_a_id, member_b_id])
    ).inserted_id

    return str(class_id)


@pytest.fixture
def empty_members_class():
    class_resource = ClassResource()
    class_id = class_resource.collection.insert_one(_class_doc([])).inserted_id
    return str(class_id)


def test_view_members_forbidden_for_member_role(client, member_token,seeded_members_class):
    response = client.get(
        f"/classes/{seeded_members_class}/members",
        headers={"Authorization": f"Bearer {member_token}"},
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json[MSG] == "Access forbidden: insufficient permissions"


def test_view_members_class_not_found(client, trainer_token):
    response = client.get(
        "/classes/random_class_id/members",
        headers={"Authorization": f"Bearer {trainer_token}"},
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json[MSG] == "Class not found"


def test_view_members_empty(client, trainer_token, empty_members_class):
    response = client.get(
        f"/classes/{empty_members_class}/members",
        headers={"Authorization": f"Bearer {trainer_token}"},
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json == []


def test_view_members_returns_enrolled_members(client, trainer_token, seeded_members_class):
    response = client.get(
        f"/classes/{seeded_members_class}/members",
        headers={"Authorization": f"Bearer {trainer_token}"},
    )

    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 2

    emails = {member["email"] for member in response.json}
    names = {member["name"] for member in response.json}
    telegram_ids = {member["telegram_chat_id"] for member in response.json}

    assert emails == {"alice@example.com", "bob@example.com"}
    assert names == {"Alice Member", "Bob Member"}
    assert telegram_ids == {"alice_telegram", "bob_telegram"}
