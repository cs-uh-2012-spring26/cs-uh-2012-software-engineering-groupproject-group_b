"""
Unit tests for Feature 4: View Member List

Endpoint: GET /classes/<class_id>/members

Refactored: Tests mock the template layer instead of database internals.
Uses mock_jwt fixture from conftest.py.
"""

from http import HTTPStatus
import pytest


def test_view_members_success(client, mock_jwt, mocker):
    mock_jwt("trainer")

    mock_members = [
        {"name": "Alice", "email": "alice@example.com", "contact": "555-0001"},
        {"name": "Bob",   "email": "bob@example.com",   "contact": "555-0002"},
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
    assert members[1]["name"] == "Bob"


def test_view_members_empty_class(client, mock_jwt, mocker):
    mock_jwt("trainer")
    mocker.patch(
        "app.apis.classes.StandardMemberAccess.get_enrolled_members",
        return_value=([], None)
    )
    response = client.get("/classes/class-1/members")
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == []


def test_view_members_class_not_found(client, mock_jwt, mocker):
    mock_jwt("trainer")
    mocker.patch(
        "app.apis.classes.StandardMemberAccess.get_enrolled_members",
        return_value=(None, "Class not found")
    )
    response = client.get("/classes/nonexistent-id/members")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_view_members_forbidden_for_member_role(client, mock_jwt, mocker):
    mock_jwt("member")
    response = client.get("/classes/class-1/members")
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_view_members_admin_role_allowed(client, mock_jwt, mocker):
    mock_jwt("admin")
    mocker.patch(
        "app.apis.classes.StandardMemberAccess.get_enrolled_members",
        return_value=([], None)
    )
    response = client.get("/classes/class-1/members")
    assert response.status_code == HTTPStatus.OK
