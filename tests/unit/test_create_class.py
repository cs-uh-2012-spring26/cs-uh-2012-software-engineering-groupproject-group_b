from http import HTTPStatus
from datetime import datetime,timedelta

import pytest
from pytest_mock import MockerFixture

from app.apis import MSG
from app.db.classes import (
    CLASS_CAPACITY,
    CLASS_DATE,
    CLASS_DESCRIPTION,
    CLASS_END_TIME,
    CLASS_NAME,
    CLASS_ROOM_NUMBER,
    CLASS_START_TIME,
    TRAINER_NAME,
)

# mocking jwt token verification
def mock_jwt(mocker, role):
    """
    Bypass JWT verification and return a fake set of claims.
    """
    mocker.patch(
        "flask_jwt_extended.view_decorators.verify_jwt_in_request", return_value=None
    )
    mocker.patch("app.apis.admin.get_jwt", return_value={"role": role})

# input class
def payload(**overrides):
    base = {
        CLASS_NAME: "Yoga",
        CLASS_DESCRIPTION: "Relaxing yoga session",
        TRAINER_NAME: "John Doe",
        CLASS_DATE: "2030-01-01",
        CLASS_START_TIME: "10:00",
        CLASS_END_TIME: "11:00",
        CLASS_ROOM_NUMBER: "101",
        CLASS_CAPACITY: 10,
    }
    return {**base,**overrides}

'''   TESTS   '''

def test_create_class_success(client, mocker):
    mock_jwt(mocker, role="trainer")

    mocked_class_resource = mocker.patch("app.apis.admin.ClassResource")
    mocked_instance = mocked_class_resource.return_value
    mocked_instance.create_class.return_value = "123"

    response = client.post("/admin/", json=payload())

    assert response.status_code == HTTPStatus.OK
    assert response.json[MSG] == "Class created with id: 123"

    mocked_instance.create_class.assert_called_once()


def test_create_class_forbidden(client, mocker):
    mock_jwt(mocker, role="member")

    response = client.post("/admin/", json=payload())

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json[MSG] == "Only trainers can create classes"


def test_create_class_missing_body(client, mocker):
    mock_jwt(mocker, role="trainer")

    response = client.post("/admin/",json={})

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json[MSG] == "Request body (JSON) or parameters are required"


def test_create_class_invalid_fields(client, mocker):
    mock_jwt(mocker, role="trainer")

    # empty class name input 
    response = client.post("/admin/", json=payload(**{CLASS_NAME:""}))

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] == "Invalid value provided for one of the fields"


def test_create_class_invalid_time_format(client, mocker):
    mock_jwt(mocker, role="trainer")

    response = client.post("/admin/", json=payload(**{CLASS_START_TIME:"10"}))

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] == "Invalid time format, expected HH:MM"


def test_create_class_start_time_not_before_end_time(client, mocker):
    mock_jwt(mocker, role="trainer")

    response = client.post("/admin/", json=payload(**{CLASS_START_TIME: "12:00", CLASS_END_TIME: "11:00"}))

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] == "Start time must be before end time"


def test_create_class_invalid_date_format(client, mocker):
    mock_jwt(mocker, role="trainer")

    response = client.post("/admin/", json=payload(**{CLASS_DATE: "2030/01/01"}))

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] == "Invalid date format, expected YYYY-MM-DD"


def test_create_class_date_in_past(client, mocker):
    mock_jwt(mocker, role="trainer")

    response = client.post("/admin/", json=payload(**{CLASS_DATE: "2000-01-01"}))

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] == "Date must be today or in the future"

def test_create_class_time_in_past(client,mocker):
    mock_jwt(mocker, role="trainer")

    # get date today and set input to a time in the past
    # warning: test will fail if current testing time is 00:00
    date_input = datetime.today().strftime("%Y-%m-%d")
    time_now = datetime.now().strftime("%H:%M")
    start_time = (datetime.now()- timedelta(minutes=1)).strftime("%H:%M")    
    response = client.post("/admin/", json=payload(**{CLASS_DATE: date_input, CLASS_START_TIME: start_time,CLASS_END_TIME:time_now}))

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] ==  "Start time must be in the future for today's classes"

def test_create_class_invalid_capacity_type(client, mocker):
    mock_jwt(mocker, role="trainer")

    response = client.post("/admin/", json=payload(**{CLASS_CAPACITY: "ten"}))

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] == "Invalid value provided for capacity, must be an integer"
