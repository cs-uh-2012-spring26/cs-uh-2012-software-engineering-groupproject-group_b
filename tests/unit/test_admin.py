"""
Unit tests for Feature 4: View Member List

Endpoint: GET /admin/<class_id>/members

User story: As a trainer, I want to view the list of members who have
booked a spot in my class so I can see who is attending.

All tests use mock JWT (so no real token is needed) and mock the
ClassResource / UserResource so no real database calls are made.
"""

from http import HTTPStatus

import pytest

from app.apis import MSG

# ─── Tests ────────────────────────────────────────────────────────────────────


def test_view_members_success(client, mock_jwt, mocker):
    """
    A trainer requests the member list for a class that has enrolled members.

    Expected: 200 OK with a list containing each member's name, email,
    and contact fields.
    """
    mock_jwt("trainer")

    # Simulate fetching those two users from the database
    mock_members = [
        {"name": "Alice",   "email": "alice@example.com", "contact": "555-0001"},
        {"name": "Bob",     "email": "bob@example.com",   "contact": "555-0002"},
    ]

    mocker.patch(
        "app.apis.classes.StandardMemberAccess.get_enrolled_members",
        return_value=(mock_members, None)
    )

    response = client.get("/classes/class-1/members")

    assert response.status_code == HTTPStatus.OK
    members = response.get_json()
    assert len(members) == 2
    assert members[0]["name"] == "Alice"
    assert members[0]["email"] == "alice@example.com"
    assert members[1]["name"] == "Bob"
    assert members[1]["email"] == "bob@example.com"


def test_view_members_empty_class(client, mock_jwt, mocker):
    """
    A trainer requests the member list for a class that has no bookings yet.

    Expected: 200 OK with an empty list (not an error — the class exists,
    it just has no enrolled members).
    """
    mock_jwt("trainer")

    # Class exists but nobody has booked it yet
    mocker.patch(
        "app.apis.classes.StandardMemberAccess.get_enrolled_members",
        return_value=([], None)

    )

    response = client.get("/classes/class-1/members")

    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == []


def test_view_members_class_not_found(client, mock_jwt, mocker):
    """
    The class ID provided does not match any class in the database.

    Expected: 404 Not Found with a descriptive error message.
    The endpoint returns None from get_class_by_id when the ID is invalid
    or simply does not exist.
    """
    mock_jwt("trainer")

    # get_class_by_id returns None when the class does not exist
    mocker.patch(
        "app.apis.classes.StandardMemberAccess.get_enrolled_members",
        return_value=(None, "Class not found")
    )

    response = client.get("/classes/nonexistent-id/members")

    # Note: @api.marshal_list_with on this endpoint strips response body fields,
    # so we only assert the status code here — the 404 itself confirms the error.
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_view_members_forbidden_for_member_role(client, mock_jwt, mocker):
    """
    A regular member JWT tries to view the member list — this is not allowed.

    Expected: 403 Forbidden. Only trainers and admins can see who booked a class.
    The role check runs before any database lookup.
    """
    mock_jwt("member")

    response = client.get("/classes/class-1/members")

    # Note: @api.marshal_list_with on this endpoint strips response body fields,
    # so we only assert the status code here — the 403 itself confirms the error.
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_view_members_admin_role_allowed(client, mock_jwt, mocker):
    """
    An admin JWT (role='admin') should also be permitted to view the member list,
    not just trainers.

    Expected: 200 OK — verifies the role check allows both 'trainer' and 'admin'.
    """
    mock_jwt("admin")

    # Empty class — we just want to confirm the role check passes
    mocker.patch(
        "app.apis.classes.StandardMemberAccess.get_enrolled_members",
        return_value=([], None)
    )

    response = client.get("/classes/class-1/members")

    # Admin is allowed — should not get 403
    assert response.status_code == HTTPStatus.OK
