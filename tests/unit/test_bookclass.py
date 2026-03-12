import pytest
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from bson import ObjectId

from app.db.users import UserResource, MEMBER_ROLE
from app.db.classes import ClassResource

def make_auth_header(app, user_id: str, role: str = MEMBER_ROLE) -> dict:
    """
    Generate a JWT Authorization header for the given user_id and role.
    Must be called inside an app context.
    """
    with app.app_context():
        token = create_access_token(
            identity=str(user_id),
            additional_claims={"role": role},
        )
    return {"Authorization": f"Bearer {token}"}


def register_member(client, name="Test User", email="test@example.com", password="ValidPass1!"):
    """Helper to register a member and return the response."""
    return client.post("/users/register", json={
        "name": name,
        "email": email,
        "password": password,
    })


def create_test_class(app, capacity=10, minutes_from_now=60):
    """
    Insert a class directly via ClassResource (uses mock DB).
    Returns the string class_id.
    """
    with app.app_context():
        cr = ClassResource()
        start = datetime.now() + timedelta(minutes=minutes_from_now)
        end = start + timedelta(hours=1)
        class_id = cr.create_class(
            name="Test Yoga",
            trainer_name="Trainer Jane",
            start_time=start,
            end_time=end,
            description="A test class",
            room_number="101",
            capacity=capacity,
        )
    return str(class_id)

def get_user_id(app,email:str) -> str: 
    """Look up a user by email and return their _id as a plain string."""
    with app.app_context():
        ur = UserResource()
        user = ur.get_user_by_email(email)
    return str(user["_id"])

class TestBookClass:
 
    def test_successful_booking(self, client, app):
        """A valid member with a valid JWT can book an open class."""
        register_member(client, email="booker@example.com")
        user_id = get_user_id(app, "booker@example.com")
        class_id = create_test_class(app, capacity=10)
 
        headers = make_auth_header(app, user_id)
        resp = client.post(f"/member/{class_id}/book", headers=headers)
 
        assert resp.status_code == 200
        assert "Booked successfully" in resp.get_json()["message"]
 
    def test_book_class_not_found(self, client, app):
        """Booking a non-existent class returns 404."""
        register_member(client, email="notfound@example.com")
        user_id = get_user_id(app, "notfound@example.com")
 
        fake_class_id = str(ObjectId()) 
        headers = make_auth_header(app, user_id)
        resp = client.post(f"/member/{fake_class_id}/book", headers=headers)
 
        assert resp.status_code == 404
        assert "not found" in resp.get_json()["message"].lower()
 
    def test_book_class_user_not_found(self, client, app):
        """
        JWT contains a user_id that doesn't exist in the DB.
        get_user_by_id returns None -> 404.
        """
        class_id = create_test_class(app, capacity=10)
 
        fake_user_id = str(ObjectId())
        headers = make_auth_header(app, fake_user_id)
 
        resp = client.post(f"/member/{class_id}/book", headers=headers)
 
        assert resp.status_code == 404
        assert "not found" in resp.get_json()["message"].lower()
 
    def test_book_class_already_booked(self, client, app):
        """A member cannot book the same class twice."""
        register_member(client, email="twice@example.com")
        user_id = get_user_id(app, "twice@example.com")
        class_id = create_test_class(app, capacity=10)
        headers = make_auth_header(app, user_id)
 
        resp1 = client.post(f"/member/{class_id}/book", headers=headers)
        assert resp1.status_code == 200
 
        resp2 = client.post(f"/member/{class_id}/book", headers=headers)
        assert resp2.status_code == 409
        assert "already booked" in resp2.get_json()["message"].lower()
 
    def test_book_class_full(self, client, app):
        """Booking a class at full capacity returns 409."""
        register_member(client, email="filler@example.com")
        register_member(client, email="latejoiner@example.com")
 
        filler_id = get_user_id(app, "filler@example.com")
        late_id = get_user_id(app, "latejoiner@example.com")
 
        class_id = create_test_class(app, capacity=1)
 
        resp1 = client.post(f"/member/{class_id}/book", headers=make_auth_header(app, filler_id))
        assert resp1.status_code == 200
 
        resp2 = client.post(f"/member/{class_id}/book", headers=make_auth_header(app, late_id))
        assert resp2.status_code == 409
        assert "full" in resp2.get_json()["message"].lower()
 
    def test_book_class_invalid_class_id_format(self, client, app):
        """
        A malformed class_id (not a valid ObjectId) causes
        ClassResource.add_user_to_class to hit the except branch -> CLASS_NOT_FOUND -> 404.
        """
        register_member(client, email="invalidid@example.com")
        user_id = get_user_id(app, "invalidid@example.com")
 
        headers = make_auth_header(app, user_id)
        resp = client.post("/member/not-a-valid-id/book", headers=headers)
 
        assert resp.status_code == 404
 
    def test_book_class_no_token(self, client, app):
        """
        Booking without any JWT token is rejected.
        Flask-JWT-Extended returns 422 for a completely missing token
        and 401 for an invalid/expired one — both are acceptable here.
        """
        class_id = create_test_class(app, capacity=5)
        resp = client.post(f"/member/{class_id}/book")
        assert resp.status_code != 200