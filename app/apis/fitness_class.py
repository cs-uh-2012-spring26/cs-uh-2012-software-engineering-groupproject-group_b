from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.apis import MSG
from app.db.classes import ClassResource
from app.db.users import UserResource
from app.db.classes import CLASS_NAME,CLASS_DESCRIPTION,TRAINER_NAME,CLASS_START_TIME,CLASS_END_TIME,CLASS_ROOM_NUMBER,CLASS_CAPACITY
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

#CREATE CLASS ENDPOINT

_EXAMPLE_CLASS_1 = {
    CLASS_NAME: "Yoga",
    CLASS_DESCRIPTION: "Yoga class",
    TRAINER_NAME: "John",
    CLASS_START_TIME: "10:00",
    CLASS_END_TIME: "11:00",
    CLASS_ROOM_NUMBER: "101",
    CLASS_CAPACITY: 10,
}

CLASS_CREATE_FLDS = api.model(
    "NewClassEntry",
    {
        CLASS_NAME: fields.String(example=_EXAMPLE_CLASS_1[CLASS_NAME], required=True),
        CLASS_DESCRIPTION: fields.String(example=_EXAMPLE_CLASS_1[CLASS_DESCRIPTION], required=True),
        TRAINER_NAME: fields.String(example=_EXAMPLE_CLASS_1[CLASS_DESCRIPTION], required=True),
        CLASS_START_TIME: fields.String(example=_EXAMPLE_CLASS_1[CLASS_START_TIME], required=True),
        CLASS_END_TIME: fields.String(example=_EXAMPLE_CLASS_1[CLASS_END_TIME], required=True),
        CLASS_ROOM_NUMBER: fields.String(example=_EXAMPLE_CLASS_1[CLASS_ROOM_NUMBER], required=True),
        CLASS_CAPACITY: fields.Integer(example=_EXAMPLE_CLASS_1[CLASS_CAPACITY], required=True),
    },
)


@api.route("/")
class CreateClass(Resource):
    @api.expect(CLASS_CREATE_FLDS)
    @api.response(
        HTTPStatus.OK,
        "Success",
        api.model("All Classes", {MSG: fields.List(fields.Nested(CLASS_CREATE_FLDS), example=[_EXAMPLE_CLASS_1])})
    )
    @api.response(HTTPStatus.BAD_REQUEST, "Bad Request", api.model("Error", {MSG: fields.String()}))
    def post(self):
        assert isinstance(request.json, dict)
        data = request.json

        if not data:
            return {MSG: "Request body (JSON) or parameters are required"}, HTTPStatus.BAD_REQUEST

        name = data.get(CLASS_NAME)
        description = data.get(CLASS_DESCRIPTION)
        trainer_name = data.get(TRAINER_NAME)
        start_time = data.get(CLASS_START_TIME)
        end_time = data.get(CLASS_END_TIME)
        room_number = data.get(CLASS_ROOM_NUMBER)

        # Validate time format and that start_time is before end_time
        try:
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = datetime.strptime(end_time, "%H:%M")
        except (TypeError, ValueError):
            return {MSG: "Invalid time format, expected HH:MM"}, HTTPStatus.NOT_ACCEPTABLE

        if start_dt >= end_dt:
            return {MSG: "Start time must be before end time"}, HTTPStatus.NOT_ACCEPTABLE

        # Validate capacity type
        try:
            capacity = int(data.get(CLASS_CAPACITY))
        except (TypeError, ValueError):
            return {MSG: "Invalid value provided for capacity, must be an integer"}, HTTPStatus.NOT_ACCEPTABLE

        if not (
            isinstance(name, str) and len(name) > 0
            and isinstance(description, str) and len(description) > 0
            and isinstance(start_time, str)
            and isinstance(end_time, str)
            and isinstance(room_number, str)
        ):
            return {MSG: "Invalid value provided for one of the fields"}, HTTPStatus.NOT_ACCEPTABLE

        class_resource = ClassResource()
        class_id = class_resource.create_class(name, start_time, end_time, description, room_number, capacity)
        return {MSG: f"Class created with id: {class_id}"}, HTTPStatus.OK