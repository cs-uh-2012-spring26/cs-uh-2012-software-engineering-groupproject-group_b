from app.apis.student import api as student_ns
from app.apis.hello import api as hello_ns
from app.apis.fitness_class import api as class_ns
from app.apis.user import api as user_ns
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
        title="Students",
        version="1.0",
        description="A simple student record keeping API",
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
    api.add_namespace(student_ns)
    api.add_namespace(hello_ns)
    api.add_namespace(class_ns)
    api.add_namespace(user_ns)
    @api.errorhandler(Exception)
    def handle_input_validation_error(error):
        return {"message": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR

    return app
