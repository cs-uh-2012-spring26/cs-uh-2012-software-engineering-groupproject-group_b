from http import HTTPStatus
import pytest
from pytest_mock import MockerFixture
from app.apis import MSG
from app.db.classes import CLASS_TRAINER_ID


def mock_jwt(mocker, role, identity="trainer-1"):
    # Mock JWT verification and trainer identity
    mocker.patch(
        "flask_jwt_extended.view_decorators.verify_jwt_in_request", return_value=None
    )
    mocker.patch("app.apis.admin.get_jwt", return_value={"role": role})
    mocker.patch("app.apis.admin.get_jwt_identity", return_value=identity)



def test_send_class_reminder_success_and_fail(client, mocker):
    mock_jwt(mocker, role="trainer", identity="trainer-1")

    # create fake class by trainer-1 with 2 members 
    fitness_class = {
        CLASS_TRAINER_ID: "trainer-1",
        "user_ids": ["user-1", "user-2"],
        "name": "Yoga",
    }

    # mock get_class_by_id -> return fake fitness class
    mocker.patch("app.apis.admin.ClassResource").return_value.get_class_by_id.return_value = (
        fitness_class
    )

    # mock getting users in the class
    mocker.patch("app.apis.admin.UserResource").return_value.get_users_by_ids.return_value = [
        {"email": "a@example.com", "name": "Alice"},
        {"email": "b@example.com", "name": "Bob"},
    ]

    # mock email sending service api
    mocked_send = mocker.patch("app.apis.admin.send_class_reminder")

    # testing: success and fail cases
    # real service return [bool, "Message"]
    mocked_send.side_effect = [
        (True, ""),
        (False, "Error in sending to this address"),
    ]

    response = client.post("/admin/class-1/remind")

    assert response.status_code == HTTPStatus.OK
    assert response.json[MSG] == "Reminders processed: 1 sent, 1 failed"
    assert response.json["sent_to"] == ["a@example.com"]
    assert response.json["failed"] == [
        {"email": "b@example.com", "error": "Error in sending to this address"}
    ]

    assert mocked_send.call_count == 2

def test_send_class_reminder_forbidden_member(client, mocker):
    mock_jwt(mocker, role="member")

    response = client.post("/admin/class-1/remind")

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json[MSG] == "Only trainers can send reminder emails"


def test_send_class_reminder_forbidden_not_assigned_trainer(client, mocker):
    mock_jwt(mocker, role="trainer", identity="trainer-1")

    mocked_class_resource = mocker.patch("app.apis.admin.ClassResource")

    # assign different trainer than mocked identity trainer
    mocked_class_resource.return_value.get_class_by_id.return_value = {
        CLASS_TRAINER_ID: "trainer-2",
        "user_ids": ["user-1"],
    }

    response = client.post("/admin/class-1/remind")

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json[MSG] == "You are not the trainer assigned to this class"


def test_send_class_reminder_class_not_found(client, mocker):
    mock_jwt(mocker, role="trainer", identity="trainer-1")

    mocker.patch("app.apis.admin.ClassResource").return_value.get_class_by_id.return_value = None

    response = client.post("/admin/missing-id/remind")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json[MSG] == "Class not found"



def test_send_class_reminder_no_members(client, mocker):
    mock_jwt(mocker, role="trainer", identity="trainer-1")

    mocker.patch("app.apis.admin.ClassResource").return_value.get_class_by_id.return_value = {
        CLASS_TRAINER_ID: "trainer-1",
        "user_ids": [],
    }

    # mocked email service sender (will not be called)
    mocked_send = mocker.patch("app.apis.admin.send_class_reminder")

    response = client.post("/admin/class-1/remind")

    assert response.status_code == HTTPStatus.OK
    assert response.json[MSG] == "No members enrolled in this class"
    assert response.json["sent_to"] == []
    assert response.json["failed"] == []
    mocked_send.assert_not_called()

