"""Tests for Feature 6: Create Recurring Classes."""

from datetime import date
from http import HTTPStatus

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
from app.services.recurrence import (
    DailyRecurrence,
    WeeklyRecurrence,
    get_recurrence_strategy,
    SUPPORTED_RECURRENCES,
)

RECURRENCE = "recurrence"
RECURRENCE_END_DATE = "recurrence_end_date"


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
    return {**base, **overrides}


# ---------------------------------------------------------------------------
# Pure unit tests for RecurrenceStrategy implementations
# ---------------------------------------------------------------------------

class TestDailyRecurrence:
    strategy = DailyRecurrence()

    def test_generates_consecutive_dates(self):
        result = list(self.strategy.generate_dates(date(2030, 1, 1), date(2030, 1, 7)))
        assert len(result) == 7
        assert result[0] == date(2030, 1, 1)
        assert result[-1] == date(2030, 1, 7)
        for i in range(1, len(result)):
            assert (result[i] - result[i - 1]).days == 1

    def test_single_occurrence_when_start_equals_end(self):
        result = list(self.strategy.generate_dates(date(2030, 6, 15), date(2030, 6, 15)))
        assert result == [date(2030, 6, 15)]

    def test_empty_when_end_before_start(self):
        result = list(self.strategy.generate_dates(date(2030, 1, 10), date(2030, 1, 1)))
        assert result == []


class TestWeeklyRecurrence:
    strategy = WeeklyRecurrence()

    def test_generates_weekly_dates(self):
        result = list(self.strategy.generate_dates(date(2030, 1, 1), date(2030, 1, 22)))
        assert len(result) == 4
        assert result[0] == date(2030, 1, 1)
        assert result[1] == date(2030, 1, 8)
        assert result[2] == date(2030, 1, 15)
        assert result[3] == date(2030, 1, 22)

    def test_single_occurrence_when_start_equals_end(self):
        result = list(self.strategy.generate_dates(date(2030, 3, 5), date(2030, 3, 5)))
        assert result == [date(2030, 3, 5)]

    def test_does_not_exceed_end_date(self):
        result = list(self.strategy.generate_dates(date(2030, 1, 1), date(2030, 1, 7)))
        assert result == [date(2030, 1, 1)]


class TestGetRecurrenceStrategy:
    def test_returns_daily_strategy(self):
        assert isinstance(get_recurrence_strategy("daily"), DailyRecurrence)

    def test_returns_weekly_strategy(self):
        assert isinstance(get_recurrence_strategy("weekly"), WeeklyRecurrence)

    def test_returns_none_for_unsupported_type(self):
        assert get_recurrence_strategy("monthly") is None
        assert get_recurrence_strategy("hourly") is None

    def test_case_insensitive(self):
        assert get_recurrence_strategy("DAILY") is not None
        assert get_recurrence_strategy("Weekly") is not None

    def test_supported_recurrences_contains_expected(self):
        assert "daily" in SUPPORTED_RECURRENCES
        assert "weekly" in SUPPORTED_RECURRENCES


# ---------------------------------------------------------------------------
# HTTP endpoint tests — success paths
# ---------------------------------------------------------------------------

def test_daily_recurring_class_creates_correct_count(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{
        RECURRENCE: "daily",
        RECURRENCE_END_DATE: "2030-01-07",  # 7 days inclusive
    }), headers=headers)

    assert response.status_code == HTTPStatus.OK
    data = response.json
    assert data[MSG] == "7 recurring classes created"
    assert len(data["class_ids"]) == 7


def test_weekly_recurring_class_creates_correct_count(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{
        RECURRENCE: "weekly",
        RECURRENCE_END_DATE: "2030-01-22",  # Jan 1, 8, 15, 22 → 4 occurrences
    }), headers=headers)

    assert response.status_code == HTTPStatus.OK
    data = response.json
    assert data[MSG] == "4 recurring classes created"
    assert len(data["class_ids"]) == 4


def test_recurrence_end_date_equals_start_creates_one_class(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{
        RECURRENCE: "daily",
        RECURRENCE_END_DATE: "2030-01-01",  # same as CLASS_DATE → 1 occurrence
    }), headers=headers)

    assert response.status_code == HTTPStatus.OK
    data = response.json
    assert data[MSG] == "1 recurring classes created"
    assert len(data["class_ids"]) == 1


def test_recurring_class_ids_are_unique_strings(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{
        RECURRENCE: "weekly",
        RECURRENCE_END_DATE: "2030-03-26",  # 13 weeks
    }), headers=headers)

    assert response.status_code == HTTPStatus.OK
    class_ids = response.json["class_ids"]
    assert len(class_ids) == len(set(class_ids)), "all class IDs must be unique"
    assert all(isinstance(id_, str) for id_ in class_ids)


# ---------------------------------------------------------------------------
# HTTP endpoint tests — backward compatibility (single class unchanged)
# ---------------------------------------------------------------------------

def test_no_recurrence_field_creates_single_class(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(), headers=headers)

    assert response.status_code == HTTPStatus.OK
    assert response.json[MSG].startswith("Class created with id:")


def test_empty_recurrence_field_creates_single_class(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{RECURRENCE: ""}), headers=headers)

    assert response.status_code == HTTPStatus.OK
    assert response.json[MSG].startswith("Class created with id:")


# ---------------------------------------------------------------------------
# HTTP endpoint tests — validation failures
# ---------------------------------------------------------------------------

def test_forbidden_for_members(client, member_token):
    headers = {"Authorization": f"Bearer {member_token}"}

    response = client.post("/classes/", json=payload(**{
        RECURRENCE: "daily",
        RECURRENCE_END_DATE: "2030-01-07",
    }), headers=headers)

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_invalid_recurrence_type_returns_406(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{
        RECURRENCE: "monthly",
        RECURRENCE_END_DATE: "2030-06-01",
    }), headers=headers)

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert "monthly" in response.json[MSG]
    assert "Supported" in response.json[MSG]


def test_missing_recurrence_end_date_returns_400(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{RECURRENCE: "daily"}), headers=headers)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "recurrence_end_date" in response.json[MSG]


def test_invalid_recurrence_end_date_format_returns_406(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{
        RECURRENCE: "daily",
        RECURRENCE_END_DATE: "01/07/2030",  # wrong format
    }), headers=headers)

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert "recurrence_end_date" in response.json[MSG]


def test_recurrence_end_date_before_start_returns_406(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{
        RECURRENCE: "daily",
        RECURRENCE_END_DATE: "2029-12-31",  # before CLASS_DATE 2030-01-01
    }), headers=headers)

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert "recurrence_end_date" in response.json[MSG]


def test_too_many_occurrences_returns_406(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    # 2030-01-01 to 2032-01-01 is ~730 days — exceeds MAX_OCCURRENCES (365)
    response = client.post("/classes/", json=payload(**{
        RECURRENCE: "daily",
        RECURRENCE_END_DATE: "2032-01-01",
    }), headers=headers)

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert "365" in response.json[MSG]


def test_existing_date_validations_still_apply(client, trainer_token):
    headers = {"Authorization": f"Bearer {trainer_token}"}

    response = client.post("/classes/", json=payload(**{
        CLASS_DATE: "2000-01-01",
        RECURRENCE: "daily",
        RECURRENCE_END_DATE: "2000-01-07",
    }), headers=headers)

    assert response.status_code == HTTPStatus.NOT_ACCEPTABLE
    assert response.json[MSG] == "Date must be today or in the future"
