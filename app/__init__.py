from app.apis.fitness_class import api as class_ns
from app.apis.classlist import api as classlist_ns
from app.apis.user import api as user_ns
from app.apis.class_members import api as class_members_ns
from app.config import Config
from app.db import DB

from http import HTTPStatus
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restx import Api


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
    api.add_namespace(class_ns)
    api.add_namespace(user_ns)
    api.add_namespace(class_members_ns)
    api.add_namespace(classlist_ns)

    @api.errorhandler(Exception)
    def handle_input_validation_error(error):
        return {"message": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR

    return app
