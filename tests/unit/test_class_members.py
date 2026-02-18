from http import HTTPStatus
from app.apis import MSG
from app.db.bookings import CLASS_ID, USER_NAME, USER_EMAIL, USER_CONTACT
from unittest.mock import patch


def test_get_class_members_count(client):
    """Two members booked class_abc123 in the fixture; endpoint returns both."""
    response = client.get("/classes/class_abc123/members")
    assert response.status_code == HTTPStatus.OK
    data = response.json
    assert isinstance(data.get(MSG), list)
    assert len(data[MSG]) == 2


def test_get_class_members_correct_data(client):
    """Returned members match the seeded data for class_abc123."""
    response = client.get("/classes/class_abc123/members")
    assert response.status_code == HTTPStatus.OK
    emails = {m[USER_EMAIL] for m in response.json[MSG]}
    assert "alice@example.com" in emails
    assert "bob@example.com" in emails


def test_get_class_members_fields_present(client):
    """Each member entry includes name, email, and contact as required."""
    response = client.get("/classes/class_abc123/members")
    assert response.status_code == HTTPStatus.OK
    for member in response.json[MSG]:
        assert USER_NAME in member
        assert USER_EMAIL in member
        assert USER_CONTACT in member


def test_get_class_members_empty_class(client):
    """A class with no bookings returns an empty list, not an error."""
    response = client.get("/classes/class_no_members/members")
    assert response.status_code == HTTPStatus.OK
    assert response.json[MSG] == []


def test_get_class_members_different_class(client):
    """Only the single member from class_xyz789 is returned."""
    response = client.get("/classes/class_xyz789/members")
    assert response.status_code == HTTPStatus.OK
    assert len(response.json[MSG]) == 1
    assert response.json[MSG][0][USER_EMAIL] == "carol@example.com"


def test_exception_returns_500(client):
    """Unexpected errors still return a well-formed 500 response."""
    with patch("app.db.bookings.BookingResource.get_class_members") as func:
        func.side_effect = ValueError

        resp = client.get("/classes/class_abc123/members")
        assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert isinstance(resp.json.get(MSG), str)
