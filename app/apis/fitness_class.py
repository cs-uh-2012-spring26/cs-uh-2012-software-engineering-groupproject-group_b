from flask_restx import Namespace, Resource, fields
from app.apis import MSG
from app.db.classes import ClassResource

from http import HTTPStatus
from flask import request

api = Namespace("classes", description="Endpoint for classes")