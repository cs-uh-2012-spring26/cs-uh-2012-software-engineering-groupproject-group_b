from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.apis import MSG
from app.db.classes import ClassResource
from app.db.users import UserResource

from http import HTTPStatus

api = Namespace("classes", description="Endpoint for classes")

_UNAUTHORIZED_RESPONSE = api.model(
    "BookClassUnauthorized", {MSG: fields.String(example="Missing or invalid token")}
)

@api.route("/<class_id>/book")
@api.param("class_id", "Class id to book")
class ClassBooking(Resource):

    @jwt_required()
    @api.doc(security="Bearer")
    @api.response(
        HTTPStatus.OK,
        "Booked",
        api.model("BookClassOK", {MSG: fields.String(example="Booked successfully")}),
    )
    @api.response(
        HTTPStatus.UNAUTHORIZED,
        "Unauthorized — valid JWT required",
        _UNAUTHORIZED_RESPONSE,
    )
    @api.response(
        HTTPStatus.NOT_FOUND,
        "Not Found",
        api.model("BookClassNotFound", {MSG: fields.String(example="Class not found")}),
    )
    @api.response(
        HTTPStatus.CONFLICT,
        "Conflict",
        api.model("BookClassConflict", {MSG: fields.String(example="Class is full / already booked")}),
    )
    def post(self, class_id):
        """Book a class. Requires a valid member JWT (Bearer token)."""
        user_id = get_jwt_identity()

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