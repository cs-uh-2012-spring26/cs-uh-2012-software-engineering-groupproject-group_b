import pytest
from flask_jwt_extended import create_access_token
from app import create_app
from app.config import TestConfig
from app.db import DB


@pytest.fixture(scope="session", autouse=True)
def app():
    app = create_app(TestConfig)
    yield app


@pytest.fixture(autouse=True)
def _clean_db(app):
    # Wipe every collection in the (mongomock) test DB before and after each
    # test so leftover documents from one test can't leak into another.
    db = DB._get()
    for name in db.list_collection_names():
        db[name].delete_many({})
    yield
    for name in db.list_collection_names():
        db[name].delete_many({})


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


