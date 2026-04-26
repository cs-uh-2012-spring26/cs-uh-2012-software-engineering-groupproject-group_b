from http import HTTPStatus
from datetime import datetime, timedelta

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


def payload(**overrides):
    base = {
        CLASS_NAME: "NEW CLASS TEST",
        CLASS_DESCRIPTION: "Relaxing yoga session",
        TRAINER_NAME: "John Doe",
        CLASS_DATE: "2030-01-01",
        CLASS_START_TIME: "10:00",
        CLASS_END_TIME: "11:00",
        CLASS_ROOM_NUMBER: "101",
        CLASS_CAPACITY: 10,
    }
    return {**base, **overrides}

'''   TESTS   '''

def test_create_class_success(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(), headers=headers)

    assert response.status_code == HTTPStatus.OK
    assert response.json[MSG].startswith("Class created with id:")


def test_create_class_forbidden(client, member_token):
    headers = {"Authorization": f"Bearer {member_token}"}

    response = client.post("/classes/", json=payload(), headers=headers)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json[MSG] == "Access forbidden: insufficient permissions"


def test_create_class_empty_body(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json={}, headers=headers)

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] == "Capacity must be atleast 1"


def test_create_class_missing_required_field(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    body = payload()
    body.pop(CLASS_NAME)
    response = client.post("/classes/", json=body, headers=headers)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


def test_create_class_invalid_capacity_value(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{CLASS_CAPACITY: 0}), headers=headers)

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] == "Capacity must be atleast 1"


def test_create_class_invalid_time_format(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{CLASS_START_TIME: "10"}), headers=headers)

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] == "Invalid time format, expected HH:MM"


def test_create_class_start_time_not_before_end_time(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{CLASS_START_TIME: "12:00", CLASS_END_TIME: "11:00"}), headers=headers)

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] == "Start time must be before end time"


def test_create_class_invalid_date_format(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{CLASS_DATE: "2030/01/01"}), headers=headers)

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] == "Invalid date format, expected YYYY-MM-DD"


def test_create_class_date_in_past(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{CLASS_DATE: "2000-01-01"}), headers=headers)

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] == "Date must be today or in the future"

def test_create_class_time_in_past(client,trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    # get date today and set input to a time in the past
    # warning: test will fail if current testing time is 00:00
    date_input = datetime.today().strftime("%Y-%m-%d")
    time_now = datetime.now().strftime("%H:%M")
    start_time = (datetime.now() - timedelta(minutes=1)).strftime("%H:%M")
    response = client.post(
        "/classes/",
        json=payload(**{CLASS_DATE: date_input, CLASS_START_TIME: start_time, CLASS_END_TIME: time_now}),
        headers=headers,
    )

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] == "Start time must be in the future for today classes"


def test_create_class_invalid_capacity_type(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}


    response = client.post("/classes/", json=payload(**{CLASS_CAPACITY: "ten"}), headers=headers)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
