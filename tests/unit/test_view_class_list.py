from http import HTTPStatus
from datetime import datetime, timedelta

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


def _class_doc(class_name: str):
    return {
        CLASS_NAME: class_name,
        CLASS_DESCRIPTION: "A class for testing",
        TRAINER_NAME: "John Doe",
        CLASS_DATE: "2030-01-01",
        CLASS_START_TIME: "10:00",
        CLASS_END_TIME: "11:00",
        CLASS_ROOM_NUMBER: "101",
        CLASS_CAPACITY: 10,
        CLASS_TRAINER_ID: "testId",
        CLASS_USER_IDS: [],
    }


@pytest.fixture
def seeded_classes():
    class_resource = ClassResource()
    class_oid_a = class_resource.collection.insert_one(
        _class_doc("Test Class A")
    ).inserted_id
    class_oid_b = class_resource.collection.insert_one(
        _class_doc("Test Class B")
    ).inserted_id

    yield ["Test Class A", "Test Class B"]

    class_resource.collection.delete_one({"_id": class_oid_a})
    class_resource.collection.delete_one({"_id": class_oid_b})


'''   TESTS   '''

def test_view_classes_empty(client):
    response = client.get("/classes/")

    assert response.status_code == HTTPStatus.OK
    assert response.json[MSG] == "All upcoming classes"
    assert response.json["classes"] == []


def test_view_classes_returns_all_upcoming(client, seeded_classes):
    response = client.get("/classes/")

    assert response.status_code == HTTPStatus.OK
    assert response.json[MSG] == "All upcoming classes"
    names = [c[CLASS_NAME] for c in response.json["classes"]]
    assert names == seeded_classes
