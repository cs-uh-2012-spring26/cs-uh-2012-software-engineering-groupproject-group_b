# Include required libraries
import pytest
from datetime import datetime, timedelta
import pymongo
from pymongo import MongoClient
from bson import ObjectId
from flask import Flask
from flask_restx import Api
from flask_jwt_extended import JWTManager, create_access_token
from app.apis.member import api as member_api
from app.db import DB
from pytest_mock import MockerFixture
from unittest.mock import patch, MagicMock
from http import HTTPStatus

MOCK_CLASSES = [
    {
        "id": ObjectId(),
        "Class_name": "Morning_yoga",
        "Trainer_name": "John",
        "Class_start_time": datetime.now() + timedelta(hours=2),
        "Class_end_time": datetime.now() + timedelta(hours=3),
        "Class_description": "Yoga for beginners",
        "Class_room_number": "100",
        "Class_capacity": 15,
        # User ids to show class capacity, 2 for 2/15
        "User_ids": [ObjectId(), ObjectId()]

    },

    {
        "id": ObjectId(),
        "Class_name": "HIIT",
        "Trainer_name": "Mary",
        "Class_start_time": datetime.now() + timedelta(hours=5),
        "Class_end_time": datetime.now() + timedelta(hours=7),
        "Class_description": "full_workout",
        "Class_room_number": "101",
        "Class_capacity": 20,
        # Full capacity/class closed
        "User_ids": [ObjectId() for _ in range(20)]
    },

    {
        "id": ObjectId(),
        "Class_name": "Past class",
        "Trainer_name": "Previous trainer",
        "Class_start_time": datetime.now() - timedelta(hours=2),  # happened 2 hours ago
        "Class_end_time": datetime.now() - timedelta(hours=1),  # ended 1 hour ago
        "Class_description": "This class already happened",
        "Class_room_number": "102",
        "Class_capacity": 10,
        "User_ids": []  # No boookings and class shouldn't show because it ended

    }
]

# Create a test Flask app, a fixture that runs before each test


@pytest.fixture
def app():
    # Create and configure a flask app for testing
    app = Flask(__name__)
    # Create a Flask restx api and attach it to the app
    app.config["JWT_SECRET_KEY"] = "test-secret-key"
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    app.config["JWT_HEADER_NAME"] = "Authorization"
    app.config["JWT_HEADER_TYPE"] = "Bearer"
    api = Api(app)
    api.add_namespace(member_api, path="/api/member")
    JWTManager(app)
    return app

# Creating a test client fixture that sends HTTP requests to the app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(app):

    with app.app_context():
        # Generating a random user ID for testing
        user_id = str(ObjectId())
        access_token = create_access_token(identity=user_id)
        return {"Authorization": f"Bearer {access_token}"}

# replace the real database with an in-memory mock


@pytest.fixture
def mock_db():
    # Mock the database with im-memory collection
    with patch("app.apis.member.DB") as mock_db:

        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        upcoming_classes = [
            c for c in MOCK_CLASSES if c["Class_start_time"] >= datetime.now()]
        mock_cursor.__iter__.return_value = iter(upcoming_classes)
        mock_collection.find.return_value = mock_cursor
        mock_db.get_collection.return_value = mock_collection
        yield mock_db


def test_get_all_classes_success(client, mock_db):
    # Test for successfully getting all upcoming classes
    response = client.get("/api/member")

    assert response.status_code == HTTPStatus.OK

    data = response.json

    # Verify that past classes are not returned
    assert len(data) == 2

    # Check the first class

    assert data[0]["Class_name"] == "Morning_yoga"
    assert data[0]["Trainer_name"] == "John"
    assert data[0]["Class_status"] == "Open"

    # Check the second class

    assert data[0]["Class_name"] == "HIIT"
    assert data[0]["Trainer_name"] == "Mary"
    assert data[0]["Class_status"] == "Closed"

# Test handling for empty database


def test_get_all_classes_empty_db(client):

    with patch("app.apis.member.DB.get_collection") as mock_get_collection:
        mock_get_collection.return_value = None

        response = client.get("/api/member")

        assert response.status_code == HTTPStatus.OK
        assert response.json == []  # Should return an empty list

# Test for enrolled classes endpoint


def test_get_enrolled_classes_success(client, auth_headers, mock_db, app):

    user_id = str(MOCK_CLASSES[0]["User_ids"][0])

    with app.app_context():

        with patch("app.apis.member.get_jwt_identity", return_value=user_id):

            response = client.get(
                "/api/member/member/enrolled", headers=auth_headers)

            assert response.status_code == HTTPStatus.OK
            data = response.json

            assert len(data) == 1
            assert data[0]["Class_name"] == "Morning_yoga"
            assert data[0]["Class_status"] == "Open"

# Checking the authentication requirement


def test_get_enrolled_no_jwt(client):
    response = client.get("/api/member/member/enrolled")

    assert response.status_code == HTTPStatus.UNAUTHORIZED

# Error handling for invalid user id


def test_get_invalid_user_id(client, auth_headers):

    with patch("app.apis.member.get_jwt_identity", return_value="invalid-object-id"):

        response = client.get(
            "/api/member/member/enrolled", headers=auth_headers)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "Invalid user ID format" in response.json["MSG"]

# Test member with no enrolled classes


def test_get_empty_enrollment(client, auth_headers):

    new_user_id = str(ObjectId())

    with patch("app.apis.member.get_jwt_identity", return_value=new_user_id):
        # Patch databse to return empty results

        with patch("app.apis.member.DB.get_collection") as mock_get_collection:

            # A mock collection that returns an empty cursor

            mock_collection = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.sort.return_value = []  # No enrolled classes
            mock_collection.find.return_value = mock_cursor
            mock_get_collection.return_value = mock_collection

            response = client.get(
                "/api/member/member/enrolled", headers=auth_headers)

            # Returns 200 OK with empty list
            assert response.status_code == HTTPStatus.OK
            assert response.json == []


def test_no_class_collection(client, auth_headers):
    with patch("app.apis.member.get_jwt_identity", return_value=str(ObjectId())):

        with patch("app.apis.member.DB.get_collection") as mock_get_collection:

            mock_get_collection.return_value = None

            response = client.get(
                "/api/member/member/enrolled", headers=auth_headers)

            assert response.status_code == HTTPStatus.OK
            assert response.json == []


def test_class_status_calculation(client, mock_db):

    # Testing that he class status(Open or Closed) is calcuated successfully
    response = client.get("/api/member")
    assert response.status_code == HTTPStatus.OK
    data = response.json

    yoga_class = next(c for c in data if c["Class_name"] == "Morning_yoga")

    HIIT = next(c for c in data if c["Class_name"] == "HIIT")

    assert yoga_class["Class_status"] == "Open"
    assert HIIT["Class_status"] == "Closed"


def test_date_formatting(client, mock_db):

    response = client.get("/api/member")
    data = response.json

    for class_item in data:

       # length of date format should be 10 characters
        assert len(class_item["Class_date"]) == 10
        assert class_item["Class_date"][4] == "-"
        assert class_item["Class_date"][7] == "-"

       # Checking time format
        assert len(class_item["Class_start_time"]) == 5
        assert class_item["Class_start_time"][2] == ":"

        assert len(class_item["Class_end_time"]) == 5
        assert class_item["Class_end_time"][2] == ":"


def test_complete_workflow(client, auth_headers, app):

    user_id = str(MOCK_CLASSES[0]["User_ids"][0])

    with patch("app.apis.member.DB") as mock_db:

        mock_collection = MagicMock()

        all_classes_cursor = MagicMock()
        upcoming_classes = [
            c for c in MOCK_CLASSES if c["Class_start_time"] >= datetime.now()]

        enrolled_cursor = MagicMock()
        enrolled_cursor.__iter__.return_value = [MOCK_CLASSES[0]]
        enrolled_cursor.sort.return_value = enrolled_cursor

        def find_side_effect(query=None):
            if query and "User_ids" in query:

                return enrolled_cursor
            return all_classes_cursor

        mock_collection.find.side_effect = find_side_effect
        mock_db.get_collection.return_value = mock_collection

        # Get all classes
        response1 = client.get("/api/member")
        assert len(response1.json) == 2  # Two upcoming classes are shown

        # Get enrolled classes for a member

        with app.app_context():
            with patch("app.apis.member.get_jwt_identity", return_value=user_id):

                response2 = client.get(
                    "/api/member/member/enrolled", headers=auth_headers)

                assert response2.status_code == HTTPStatus.OK
                # 1 enrolled class should be seen
                assert len(response2.json) == 1

                assert response2.json[0]["Class_name"] == "Morning_yoga"
