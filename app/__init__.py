from app.apis.auth import api as auth_ns
from app.apis.classes import api as classes_ns
from app.apis.users import api as users_ns

from app.config import Config
from app.db import DB

from http import HTTPStatus
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restx import Api
from flask_jwt_extended.exceptions import NoAuthorizationError

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    DB.init_app(app)
    JWTManager(app)

    api = Api(
        title="Fitness Management System API",
        version="1.0",
        description="API for creating and managing fitness classes, users, and class memberships",
        authorizations={
            "Bearer": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Paste your JWT as: Bearer &lt;token&gt;",
            }
        },
    )

    api.init_app(app)
    api.add_namespace(auth_ns)
    api.add_namespace(classes_ns)
    api.add_namespace(users_ns)

    @api.errorhandler(NoAuthorizationError)
    def handle_missing_token(error):
        return {"message": str(error)}, HTTPStatus.UNAUTHORIZED

    @api.errorhandler(Exception)
    def handle_input_validation_error(error):
        return {"message": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR

    return app
