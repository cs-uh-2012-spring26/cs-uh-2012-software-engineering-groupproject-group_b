from http import HTTPStatus

from bson import ObjectId
from flask_jwt_extended import get_jwt_identity
from flask_restx import Namespace, Resource, fields

from app.apis import MSG
from app.db.classes import ClassResource
from app.db.users import UserResource
from app.services.auth import member_required
from app.services.email import send_class_reminder

api = Namespace("users", description="Endpoints for users")

# ---------------------------------------------------------------------------
# Shared response models
# ---------------------------------------------------------------------------

_ERROR_RESPONSE = api.model(
    "UserErrorResponse",
    {MSG: fields.String(description="Error description")},
)

# ---------------------------------------------------------------------------
# POST /classes/<class_id>/book — book a class
# ---------------------------------------------------------------------------

_BOOK_OK_RESPONSE = api.model(
    "BookClassOK",
    {MSG: fields.String(example="Booked successfully")},
)

# ---------------------------------------------------------------------------
# GET /classes/<class_id>/book — enrolled classes for current member
# ---------------------------------------------------------------------------

_ENROLLED_CLASS = api.model(
    "EnrolledClass",
    {
        "_id": fields.String(description="Class ID"),
        "Class_name": fields.String(),
        "Trainer_name": fields.String(),
        "Class_date": fields.String(description="YYYY-MM-DD"),
        "Class_start_time": fields.String(),
        "Class_end_time": fields.String(),
        "Class_description": fields.String(),
        "Class_room_number": fields.String(),
        "Class_capacity": fields.Integer(),
    },
)


# =========================================================================
# /classes/<class_id>/remind
# =========================================================================

# =========================================================================
# /classes/<class_id>/book
# =========================================================================


@api.route("/me/book/<class_id>")
@api.param("class_id", "Class ID to book")
class ClassBooking(Resource):

    @member_required
    @api.doc(security="Bearer")
    @api.response(HTTPStatus.OK, "Booked successfully", _BOOK_OK_RESPONSE)
    @api.response(HTTPStatus.UNAUTHORIZED, "JWT required", _ERROR_RESPONSE)
    @api.response(HTTPStatus.NOT_FOUND, "Class or user not found", _ERROR_RESPONSE)
    @api.response(HTTPStatus.CONFLICT, "Already booked or class full", _ERROR_RESPONSE)
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



@api.route("/me/book")
class UserEnrolledClasses(Resource):
    @member_required
    @api.doc(security="Bearer")
    @api.response(HTTPStatus.OK, "Enrolled classes returned", [_ENROLLED_CLASS])
    @api.response(HTTPStatus.UNAUTHORIZED, "JWT required", _ERROR_RESPONSE)
    @api.response(HTTPStatus.BAD_REQUEST, "Invalid user ID format", _ERROR_RESPONSE)
    def get(self):
        """Get all classes the current member is enrolled in."""
        current_user_id = get_jwt_identity()

        if not current_user_id:
            return {MSG: "User not found"}, HTTPStatus.UNAUTHORIZED

        try:
            ObjectId(current_user_id)
        except Exception:
            return {MSG: "Invalid user ID format"}, HTTPStatus.BAD_REQUEST

        user_resource = UserResource()
        enrolled_classes = user_resource.get_classes_by_user_id(current_user_id)


        return enrolled_classes