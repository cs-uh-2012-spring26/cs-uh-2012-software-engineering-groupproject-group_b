import pytest
import os
from app.db import DB
from app import create_app
from dotenv import load_dotenv
import pytest

from app import create_app
from app.db import DB


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
def runner(app):
    return app.test_cli_runner()
