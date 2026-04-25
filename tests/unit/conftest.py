import os
import pytest
from dotenv import load_dotenv
from flask_jwt_extended import create_access_token
from app import create_app
from app.db import DB


@pytest.fixture(scope="session", autouse=True)
def app():
    os.environ["MOCK_DB"] = "true"
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
    os.environ.setdefault("AWS_SES_REGION", "us-east-1")
    os.environ.setdefault("SES_SENDER_EMAIL", "test@test.com")
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