from flask_restx import Namespace, Resource, fields
from app.apis import MSG
from app.db.classes import ClassResource
from app.db.users import UserResource

from http import HTTPStatus
from flask import request

api = Namespace("classes", description="Endpoint for classes")

BOOK_CLASS_REQ = api.model(
    "BookClassRequest",
    {
        "user_id": fields.String(
            required=True,
            description="User id booking the class",
            example="65f0c2a2c9b3f4b2a6f2d111",
        )
    },
)

@api.route("/<class_id>/book")
@api.param("class_id", "Class id to book")
class ClassBooking(Resource):

    @api.expect(BOOK_CLASS_REQ)

    @api.response(
        HTTPStatus.OK,
        "Booked",
        api.model("BookClassOK", {MSG: fields.String(example="Booked successfully")}),
    )
    @api.response(
        HTTPStatus.NOT_FOUND,
        "Not Found",
        api.model("BookClassNotFound", {MSG: fields.String(example="Class not found")}),
    )
    @api.response(
        HTTPStatus.NOT_ACCEPTABLE,
        "Bad Request",
        api.model("BookClassBadRequest", {MSG: fields.String(example="Invalid value provided")}),
    )
    @api.response(
        HTTPStatus.CONFLICT,
        "Conflict",
        api.model("BookClassConflict", {MSG: fields.String(example="Class is full / already booked")}),
    )
    def post(self, class_id):
        assert isinstance(request.json, dict)

        user_id = request.json.get("user_id")

        if not (isinstance(user_id, str) and len(user_id) > 0):
            return {MSG: "Invalid value provided"}, HTTPStatus.NOT_ACCEPTABLE

        user_resource = UserResource()
        user = user_resource.get_user_by_id(user_id)
        if user is None:
            return {MSG: "User not found"}, HTTPStatus.NOT_FOUND

        class_resource = ClassResource()
        status = class_resource.add_user_to_class(class_id, user_id)

        if status == "CLASS_NOT_FOUND":
            return {MSG: "Class not found"}, HTTPStatus.NOT_FOUND
        if status == "ALREADY_BOOKED":
            return {MSG: "User already booked this class"}, HTTPStatus.CONFLICT
        if status == "CLASS_FULL":
            return {MSG: "Class is full"}, HTTPStatus.CONFLICT

        ok = user_resource.add_class_to_user(user_id, class_id)
        if not ok:
            return {MSG: "User not found"}, HTTPStatus.NOT_FOUND

        return {MSG: "Booked successfully"}, HTTPStatus.OK