import os
from app.db import DB
from app import create_app
from dotenv import load_dotenv
import pytest


@pytest.fixture
def mock_jwt(mocker):
    """ Shared JWT mock fixture """
    def setup(role):
        mocker.patch(
            "flask_jwt_extended.view_decorators.verify_jwt_in_request",
            return_value=None,
        )
        mocker.patch("app.services.auth.get_jwt", return_value={"role": role})
    return setup


@pytest.fixture(scope="session", autouse=True)
def app():
    load_dotenv()
    app = create_app()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def runner(app):
    return app.test_cli_runner()
