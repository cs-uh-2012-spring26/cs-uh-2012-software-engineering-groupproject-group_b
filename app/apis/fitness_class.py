from flask_restx import Namespace, Resource, fields
from app.apis import MSG
from app.db.classes import ClassResource
from app.db.classes import CLASS_NAME, CLASS_DESCRIPTION, CLASS_ROOM_NUMBER, CLASS_START_TIME, CLASS_END_TIME, CLASS_CAPACITY
from http import HTTPStatus
from flask import request
from datetime import datetime

api = Namespace("classes", description="Endpoint for classes")

_EXAMPLE_CLASS_1 = {
    CLASS_NAME: "Yoga",
    CLASS_DESCRIPTION: "Yoga class",
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
        CLASS_START_TIME: fields.String(example=_EXAMPLE_CLASS_1[CLASS_START_TIME], required=True),
        CLASS_END_TIME: fields.String(example=_EXAMPLE_CLASS_1[CLASS_END_TIME], required=True),
        CLASS_ROOM_NUMBER: fields.String(example=_EXAMPLE_CLASS_1[CLASS_ROOM_NUMBER], required=True),
        CLASS_CAPACITY: fields.Integer(example=_EXAMPLE_CLASS_1[CLASS_CAPACITY], required=True),
    },
)


@api.route("/")
class CreateClass(Resource):
    # create class
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

        # validate capacity type
        try:
            capacity = int(data.get(CLASS_CAPACITY))
        except (TypeError, ValueError):
            return {MSG: "Invalid value provided for capacity, must be an integer"}, HTTPStatus.NOT_ACCEPTABLE
        
        if not (
            isinstance(name, str)
            and len(name) > 0
            and isinstance(description, str)
            and len(description) > 0
            and isinstance(start_time, str)
            and isinstance(end_time, str)
            and isinstance(room_number, str)
        ):
            return {
                MSG: "Invalid value provided for one of the fields"
            }, HTTPStatus.NOT_ACCEPTABLE
        class_resource = ClassResource()
        class_id = class_resource.create_class(name, start_time, end_time, description, room_number, capacity)
        return {MSG: f"Class created with id: {class_id}"}, HTTPStatus.OK