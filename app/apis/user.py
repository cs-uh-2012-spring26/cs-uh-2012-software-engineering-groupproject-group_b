from flask_restx import Namespace, Resource, fields
from app.apis import MSG
from app.db.users import UserResource

from http import HTTPStatus
from flask import request

api = Namespace("users", description="Endpoint for users")