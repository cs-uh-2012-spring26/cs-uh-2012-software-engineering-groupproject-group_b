import pytest
import os
from dotenv import load_dotenv
from flask_jwt_extended import create_access_token
from flask_jwt_extended import create_access_token
from app import create_app
from app.db import DB


@pytest.fixture(scope="session", autouse=True)
def app():
    os.environ["MOCK_DB"] = "true"
    load_dotenv(override=False)
    os.environ["MOCK_DB"] = "true"
    load_dotenv(override=False)
    app = create_app()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def trainer_token(app):
    with app.app_context():
        return create_access_token(
            identity="testId",
            additional_claims={"role": "trainer"},
        )


@pytest.fixture
def member_token(app):
    with app.app_context():
        return create_access_token(
            identity="testId",
            additional_claims={"role": "member"},
        )


@pytest.fixture
def mock_jwt(mocker):
    def setup(role):
        mocker.patch(
            "flask_jwt_extended.view_decorators.verify_jwt_in_request",
            return_value=None
        )
        mocker.patch("flask_jwt_extended.get_jwt", return_value={"role": role})
        mocker.patch("flask_jwt_extended.get_jwt_identity",
                     return_value="test_trainer_id")
    return setup
