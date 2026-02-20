from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.apis import MSG
from app.db import DB
from app.db.users import UserResource
from app.db.classes import ClassResource
from app.db.classes import CLASS_NAME, TRAINER_NAME, CLASS_START_TIME, CLASS_END_TIME, CLASS_DESCRIPTION, CLASS_ROOM_NUMBER, CLASS_CAPACITY, CLASS_USER_IDS
from datetime import datetime
from http import HTTPStatus
from flask import request
from bson import ObjectId
api = Namespace("member", description="Endpoints for member")
# VIEW LIST OF ALL CLASSES

_EXAMPLE_CLASS_1 = {
    "Class_name": "Morning_yoga",
    "Trainer_name": "John",
    "class_start_time": "7:00 AM",
    "Class_end_time": "8:00 AM",
    "Class_description": "Yoga for beginners",
    "Class_room_number": "100",
    "Class_capacity": 15,
    "Class_status": "Open"
}

_EXAMPLE_CLASS_2 = {
    "Class_name": "HIIT",
    "Trainer_name": "Mary",
    "class_start_time": "7:00 PM",
    "Class_end_time": "8:00 PM",
    "Class_description": "full_workout",
    "Class_room_number": "101",
    "Class_capacity": 20,
    "Class_status": "Closed"
}

CLASS_MODEL = api.model(
    "ClassListItem",  # name of the model which shows up in swagger
    {
        "Class_name": fields.String(description="Name of the class"),

        "Trainer_name": fields.String(description="Name of the trainer"),

        "Class_date": fields.String(description="Date of the class (YYYY-MM-DD)"),

        "Class_start_time": fields.String(description="When the class begins"),

        "Class_end_time": fields.String(description="When the class ends"),

        "Class_description": fields.String(description="What the class is about"),

        "Class_room_number": fields.String(description="class location"),

        "Class_capacity": fields.Integer(description="Class total capacity"),

        "Class_status": fields.String(description="Class open or closed", enum=["Open", "Closed"])

    }
)


@api.route("")
# The resource handler for the class list endpoint. this class handles GET requests for fetching up
# upcoming classes
class ClassList(Resource):
    @api.marshal_list_with(CLASS_MODEL)
    # Possible resposne in Swagger
    @api.response(HTTPStatus.OK, "Success-List of upcoming classes returned")
    def get(self):
        """Get all classes"""

        # Get list of upcoming fitness classes. return all fitness classes regardless of their status
        # Guest/Members can see the complete list of all available options
        # Classes are sorted by their start time

        # This endpoint doesn't accept query parameters

        now = datetime.now()  # get current time to filter for upcoming classes

        classes = DB.get_collection("classes")
        # if collection doesn't exist, return empty collection
        if classes is None:
            return []

        cursor = classes.find({
            CLASS_START_TIME: {"$gte": now}
        }).sort(CLASS_START_TIME, 1)

        # convert to list
        all_classes = list(cursor)

        # transform each class to match class model

        result = []
        for c in all_classes:
            # Calculate class status based on bookings and capacity

            booked = len(c.get(CLASS_USER_IDS, []))
            capacity = c.get(CLASS_CAPACITY, 0)

            # response for class list

            start_dt = c.get(CLASS_START_TIME)
            result.append({
                "Class_name": c.get(CLASS_NAME, ""),
                "Trainer_name": c.get(TRAINER_NAME, ""),
                "Class_date": start_dt.strftime("%Y-%m-%d") if start_dt else "",
                "Class_start_time": start_dt.strftime("%H:%M") if start_dt else "",
                "Class_end_time": c.get(CLASS_END_TIME).strftime("%H:%M") if c.get(CLASS_END_TIME) else "",
                "Class_description": c.get(CLASS_DESCRIPTION, ""),
                "Class_room_number": c.get(CLASS_ROOM_NUMBER, ""),
                "Class_capacity": capacity,
                "Class_status": "Closed" if booked >= capacity else "Open"
            })

        return result


@api.route("/member/enrolled")
# The resource handler for the class list endpoint. this class handles GET requests for fetching up
# upcoming classes
class EnrolledClasses(Resource):
    @jwt_required()
    @api.marshal_list_with(CLASS_MODEL)
    # Possible resposne in Swagger
    @api.response(HTTPStatus.OK, "Success-Your enroled classes returned")
    @api.response(HTTPStatus.UNAUTHORIZED, "Missing or Invalid JWT token")
    @api.response(HTTPStatus.BAD_REQUEST, "Invalid user ID format")
    def get(self):

        # Get list of all fitness classes the current user is currently enrolled in. return all fitness classes regardless of their status
        # Only retunrs upcoming classes and helps members see which classes they are already enrolled in
        # Classes are sorted by their start time

        # Get current user's id form the JWT token
        current_user_id = get_jwt_identity()

        if not current_user_id:
            return {"MSG": "User not found"}, HTTPStatus.UNAUTHORIZED

        try:
            # convert string id to ObjectID for databse query

            member_oid = ObjectId(current_user_id)

        except Exception:
            return {"MSG": "Invalid user ID format"}, HTTPStatus.BAD_REQUEST

        # Find all classes this member is among the users and the class is among upcoming classes

        classes = DB.get_collection("classes")
        # if collection doesn't exist, return empty collection
        if classes is None:
            return []

        now = datetime.now()  # get current time to filter for upcoming classes

        enrolled = self.correction.find({
            "user_ids": member_oid,  # check if memebr id is among user ids

            "start_time": {"$gte": now}  # only upcoming classes
        }).sort("start_time", 1)  # start woth the earliest class

        # transform each class to match class model

        result = []
        for c in enrolled:
            # Calculate class status based on bookings and capacity

            booked = len(c.get("user_ids", []))
            capacity = c.get("capacity", 0)

            # response for class list

            class_data = {

                "Class_name": c.get("name", ""),
                "Trainer_name": c.get("trainer_name", ""),
                "Class_start_Time": str(c.get("start_time", "")),
                "Class_end_time": str(c.get("end_time", "")),
                "Class_description": c.get("description", ""),
                "Class_room_number": c.get("room_number", ""),
                "Class_capacity": capacity,
                "Class_status": "Closed" if booked >= capacity else "Open"
            }

            result.append(class_data)

        return result


# BOOK CLASS FEATURE (FOR MEMBER)
_UNAUTHORIZED_RESPONSE = api.model(
    "BookClassUnauthorized", {MSG: fields.String(
        example="Missing or invalid token")}
)


@api.route("/<class_id>/book")
@api.param("class_id", "Class id to book")
class ClassBooking(Resource):

    @jwt_required()
    @api.doc(security="Bearer")
    @api.response(
        HTTPStatus.OK,
        "Booked",
        api.model("BookClassOK", {MSG: fields.String(
            example="Booked successfully")}),
    )
    @api.response(
        HTTPStatus.UNAUTHORIZED,
        "Unauthorized — valid JWT required",
        _UNAUTHORIZED_RESPONSE,
    )
    @api.response(
        HTTPStatus.NOT_FOUND,
        "Not Found",
        api.model("BookClassNotFound", {
                  MSG: fields.String(example="Class not found")}),
    )
    @api.response(
        HTTPStatus.CONFLICT,
        "Conflict",
        api.model("BookClassConflict", {MSG: fields.String(
            example="Class is full / already booked")}),
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
