from datetime import datetime

from flask import request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask_restx import Namespace, Resource, fields

from app.apis import MSG
from app.db.classes import (
    CLASS_CAPACITY,
    CLASS_DATE,
    CLASS_DESCRIPTION,
    CLASS_END_TIME,
    CLASS_NAME,
    CLASS_ROOM_NUMBER,
    CLASS_START_TIME,
    TRAINER_NAME,
    ClassResource,
)
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

#CREATE CLASS ENDPOINT

_EXAMPLE_CLASS_1 = {
    CLASS_NAME: "Yoga",
    CLASS_DESCRIPTION: "Yoga class",
    TRAINER_NAME: "John",
    CLASS_DATE: "2026-03-01",
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
        TRAINER_NAME: fields.String(example=_EXAMPLE_CLASS_1[TRAINER_NAME], required=True),
        CLASS_DATE: fields.String(example=_EXAMPLE_CLASS_1[CLASS_DATE], required=True, description="Date of the class (YYYY-MM-DD), must be today or in the future"),
        CLASS_START_TIME: fields.String(example=_EXAMPLE_CLASS_1[CLASS_START_TIME], required=True, description="Start time (HH:MM)"),
        CLASS_END_TIME: fields.String(example=_EXAMPLE_CLASS_1[CLASS_END_TIME], required=True, description="End time (HH:MM)"),
        CLASS_ROOM_NUMBER: fields.String(example=_EXAMPLE_CLASS_1[CLASS_ROOM_NUMBER], required=True),
        CLASS_CAPACITY: fields.Integer(example=_EXAMPLE_CLASS_1[CLASS_CAPACITY], required=True),
    },
)


@api.route("/")
class CreateClass(Resource):
    @jwt_required()
    @api.doc(security="Bearer")
    @api.expect(CLASS_CREATE_FLDS)
    @api.response(
        HTTPStatus.OK,
        "Success",
        api.model("All Classes", {MSG: fields.List(fields.Nested(CLASS_CREATE_FLDS), example=[_EXAMPLE_CLASS_1])})
    )
    @api.response(HTTPStatus.UNAUTHORIZED, "Trainer JWT required", api.model("CreateClassUnauthorized", {MSG: fields.String()}))
    @api.response(HTTPStatus.FORBIDDEN, "Only trainers can create classes", api.model("CreateClassForbidden", {MSG: fields.String()}))
    @api.response(HTTPStatus.BAD_REQUEST, "Bad Request", api.model("Error", {MSG: fields.String()}))
    def post(self):
        """Create a new class. Requires a trainer JWT."""
        claims = get_jwt()
        if claims.get("role") != "trainer":
            return {MSG: "Only trainers can create classes"}, HTTPStatus.FORBIDDEN

        assert isinstance(request.json, dict)
        data = request.json

        if not data:
            return {MSG: "Request body (JSON) or parameters are required"}, HTTPStatus.BAD_REQUEST

        name = data.get(CLASS_NAME)
        description = data.get(CLASS_DESCRIPTION)
        trainer_name = data.get(TRAINER_NAME)
        date_str = data.get(CLASS_DATE)
        start_time = data.get(CLASS_START_TIME)
        end_time = data.get(CLASS_END_TIME)
        room_number = data.get(CLASS_ROOM_NUMBER)

        if not (
            isinstance(name, str) and len(name) > 0
            and isinstance(description, str) and len(description) > 0
            and isinstance(room_number, str)
        ):
            return {MSG: "Invalid value provided for one of the fields"}, HTTPStatus.NOT_ACCEPTABLE

        # Validate time format and that start_time is before end_time
        try:
            start_t = datetime.strptime(start_time, "%H:%M").time()
            end_t = datetime.strptime(end_time, "%H:%M").time()
        except (TypeError, ValueError):
            return {MSG: "Invalid time format, expected HH:MM"}, HTTPStatus.NOT_ACCEPTABLE

        if start_t >= end_t:
            return {MSG: "Start time must be before end time"}, HTTPStatus.NOT_ACCEPTABLE

        # Validate date format and that the class is not in the past
        try:
            date_input = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return {MSG: "Invalid date format, expected YYYY-MM-DD"}, HTTPStatus.NOT_ACCEPTABLE

        now = datetime.now()
        if date_input < now.date():
            return {MSG: "Date must be today or in the future"}, HTTPStatus.NOT_ACCEPTABLE

        if date_input == now.date() and start_t <= now.time():
            return {MSG: "Start time must be in the future for today's classes"}, HTTPStatus.NOT_ACCEPTABLE

        # Combine date + time into full datetime objects for storage
        start_dt = datetime.combine(date_input, start_t)
        end_dt = datetime.combine(date_input, end_t)

        # Validate capacity type
        try:
            capacity = int(data.get(CLASS_CAPACITY))
        except (TypeError, ValueError):
            return {MSG: "Invalid value provided for capacity, must be an integer"}, HTTPStatus.NOT_ACCEPTABLE

        class_resource = ClassResource()
        class_id = class_resource.create_class(name, trainer_name, start_dt, end_dt, description, room_number, capacity)
        return {MSG: f"Class created with id: {class_id}"}, HTTPStatus.OK