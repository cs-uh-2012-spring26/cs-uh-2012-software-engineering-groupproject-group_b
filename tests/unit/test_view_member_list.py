"""
Unit tests for Feature 4: View Member List

Endpoint: GET /classes/<class_id>/members

Uses trainer_token/member_token fixtures from conftest.py.
"""

from http import HTTPStatus
import pytest


def test_view_members_success(client, trainer_token, mocker):
    mock_members = [
        {"name": "Alice", "email": "alice@example.com", "contact": "555-0001"},
        {"name": "Bob",   "email": "bob@example.com",   "contact": "555-0002"},
    ]
    mocker.patch(
        "app.apis.classes.StandardMemberAccess.get_enrolled_members",
        return_value=(mock_members, None)
    )

    response = client.get(
        "/classes/class-1/members",
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    members = response.get_json()
    assert len(members) == 2
    assert members[0]["name"] == "Alice"
    assert members[1]["name"] == "Bob"


def test_view_members_empty_class(client, trainer_token, mocker):
    mocker.patch(
        "app.apis.classes.StandardMemberAccess.get_enrolled_members",
        return_value=([], None)
    )
    response = client.get(
        "/classes/class-1/members",
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.get_json() == []


def test_view_members_class_not_found(client, trainer_token, mocker):
    mocker.patch(
        "app.apis.classes.StandardMemberAccess.get_enrolled_members",
        return_value=(None, "Class not found")
    )
    response = client.get(
        "/classes/nonexistent-id/members",
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_view_members_forbidden_for_member_role(client, member_token):
    response = client.get(
        "/classes/class-1/members",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
