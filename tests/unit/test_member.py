"""
Unit tests for member-facing class listing endpoints.

Endpoints covered:
  GET /member                   — view all upcoming classes (no auth required)
  GET /member/member/enrolled   — view classes the logged-in member is enrolled in

Uses a mix of real mock DB (mongomock) for the class listing endpoint,
and mocked JWT for the enrolled endpoint.
"""

import pytest
from datetime import datetime, timedelta

from flask_jwt_extended import create_access_token
from bson import ObjectId

from app.db.classes import ClassResource
from app.db.users import MEMBER_ROLE


# ─── Helpers ──────────────────────────────────────────────────────────────────


def make_member_header(app, user_id: str) -> dict:
    """Generate a JWT Authorization header for a member."""
    with app.app_context():
        token = create_access_token(
            identity=str(user_id),
            additional_claims={"role": MEMBER_ROLE},
        )
    return {"Authorization": f"Bearer {token}"}


def insert_future_class(app, name="Test Class", capacity=10, minutes_ahead=60):
    """
    Insert a class with a future start time directly into the mock DB.
    Returns the class_id as a string.
    """
    with app.app_context():
        cr = ClassResource()
        start = datetime.now() + timedelta(minutes=minutes_ahead)
        end = start + timedelta(hours=1)
        class_id = cr.create_class(
            name=name,
            trainer_name="Test Trainer",
            start_time=start,
            end_time=end,
            description="Test description",
            room_number="101",
            capacity=capacity,
        )
    return str(class_id)


# ─── Tests: View All Classes  (GET /member) ───────────────────────────────────


def test_view_classes_returns_upcoming(client, app):
    """
    GET /member returns a list of upcoming classes.
    Classes with a future start time should appear; past classes should not.
    No authentication is required for this endpoint.
    """
    insert_future_class(app, name="Upcoming Yoga", minutes_ahead=120)

    resp = client.get("/member")

    assert resp.status_code == 200
    data = resp.get_json()
    # At least the class we inserted should be in the list
    assert isinstance(data, list)
    names = [c["Class_name"] for c in data]
    assert "Upcoming Yoga" in names


def test_view_classes_shows_open_status(client, app):
    """
    A class that is not yet full should have status 'Open'.
    """
    insert_future_class(app, name="Open Class", capacity=10, minutes_ahead=180)

    resp = client.get("/member")

    assert resp.status_code == 200
    data = resp.get_json()
    open_class = next((c for c in data if c["Class_name"] == "Open Class"), None)
    assert open_class is not None
    assert open_class["Class_status"] == "Open"


def test_view_classes_shows_closed_status(client, app):
    """
    A class at full capacity should have status 'Closed'.
    We insert a class with capacity=1 and pre-fill the user_ids list.
    """
    with app.app_context():
        cr = ClassResource()
        start = datetime.now() + timedelta(hours=3)
        end = start + timedelta(hours=1)
        # Insert a class with one spot and one user already in it
        cr.create_class(
            name="Full Class",
            trainer_name="Trainer",
            start_time=start,
            end_time=end,
            description="desc",
            room_number="202",
            capacity=1,
            user_ids=[ObjectId()],  # one user already booked — class is full
        )

    resp = client.get("/member")

    assert resp.status_code == 200
    data = resp.get_json()
    full_class = next((c for c in data if c["Class_name"] == "Full Class"), None)
    assert full_class is not None
    assert full_class["Class_status"] == "Closed"


def test_view_classes_response_shape(client, app):
    """
    Each class in the response must include all expected fields:
    name, trainer, date, start_time, end_time, description, room, capacity, status.
    """
    insert_future_class(app, name="Shape Check Class", minutes_ahead=240)

    resp = client.get("/member")

    assert resp.status_code == 200
    data = resp.get_json()
    target = next((c for c in data if c["Class_name"] == "Shape Check Class"), None)
    assert target is not None

    # All fields defined in the CLASS_MODEL must be present
    for field in ["Class_name", "Trainer_name", "Class_date", "Class_start_time",
                  "Class_end_time", "Class_description", "Class_room_number",
                  "Class_capacity", "Class_status"]:
        assert field in target, f"Missing field: {field}"


# ─── Tests: View Enrolled Classes  (GET /member/member/enrolled) ──────────────


def test_view_enrolled_no_token(client):
    """
    Accessing the enrolled classes endpoint without a JWT returns a non-200 status.
    This endpoint requires member authentication.
    """
    resp = client.get("/member/member/enrolled")
    assert resp.status_code != 200


def test_view_enrolled_invalid_user_id_format(client, app):
    """
    A JWT containing a user_id that is not a valid ObjectId format
    should return 400 Bad Request.
    The endpoint wraps ObjectId() in a try/except for this case.
    """
    # Create a JWT with a user_id that cannot be cast to ObjectId
    with app.app_context():
        token = create_access_token(
            identity="not-a-valid-object-id",
            additional_claims={"role": MEMBER_ROLE},
        )
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/member/member/enrolled", headers=headers)

    # The endpoint catches the invalid ObjectId and returns 400
    assert resp.status_code == 400
