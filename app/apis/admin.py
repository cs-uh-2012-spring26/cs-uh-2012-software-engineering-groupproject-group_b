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
    CLASS_TRAINER_ID,
    TRAINER_NAME,
    ClassResource,
)
from app.db.users import UserResource
from app.email import send_class_reminder
from http import HTTPStatus

api = Namespace("admin", description="Endpoints for admin")


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
        trainer_id = get_jwt_identity()
        class_id = class_resource.create_class(name, trainer_name, start_dt, end_dt, description, room_number, capacity, trainer_id=trainer_id)
        return {MSG: f"Class created with id: {class_id}"}, HTTPStatus.OK


# VIEW LIST OF ENROLLED MEMBERS (FOR ADMIN)


# Model for a single booked member entry returned in the response
MEMBER_MODEL = api.model(
    "BookedMember",
    {
        "name": fields.String(description="Member's full name"),
        "email": fields.String(description="Member's email address"),
        "contact": fields.String(description="Member's contact number"),
    },
)

#FEATURE 4: View list of enrolled members for a class (admin/trainer only)

@api.route("/<class_id>/members")
@api.param("class_id", "The ID of the class")
class ClassMemberList(Resource):

    @jwt_required()
    @api.doc(security="Bearer")
    @api.marshal_list_with(MEMBER_MODEL)
    @api.response(HTTPStatus.OK, "List of booked members returned")
    @api.response(HTTPStatus.UNAUTHORIZED, "Missing or invalid JWT token", api.model("MembersUnauthorized", {MSG: fields.String()}))
    @api.response(HTTPStatus.FORBIDDEN, "Access restricted to trainers and admins", api.model("MembersForbidden", {MSG: fields.String()}))
    @api.response(HTTPStatus.NOT_FOUND, "Class not found", api.model("MembersNotFound", {MSG: fields.String()}))
    def get(self, class_id):
        """View the list of members who booked a spot in a class (trainer/admin only)"""

        # Check that the requester's role is trainer or admin (A2: Insufficient role)
        claims = get_jwt()
        role = claims.get("role", "")
        if role not in ("trainer", "admin"):
            return {MSG: "Access restricted to trainers and admins"}, HTTPStatus.FORBIDDEN

        # Look up the class by its ID (A3: Class not found)
        class_resource = ClassResource()
        fitness_class = class_resource.get_class_by_id(class_id, str)
        if fitness_class is None:
            return {MSG: "Class not found"}, HTTPStatus.NOT_FOUND

        # Get the list of ObjectIds of users who booked this class
        user_oids = fitness_class.get("user_ids", [])

        # A4: Class has no bookings — return empty list with 200 OK
        if not user_oids:
            return []

        # Fetch full details for each booked user
        user_resource = UserResource()
        members = user_resource.get_users_by_ids(user_oids)

        # Return only name, email, and contact for each member
        return [
            {
                "name": m.get("name", ""),
                "email": m.get("email", ""),
                "contact": m.get("contact", ""),
            }
            for m in members
        ]


# SEND REMINDER EMAILS (FOR TRAINER)

_FAILED_EMAIL_MODEL = api.model(
    "FailedEmail",
    {
        "email": fields.String(description="Recipient email address"),
        "error": fields.String(description="SES error message"),
    },
)

REMINDER_RESPONSE_MODEL = api.model(
    "ReminderResponse",
    {
        MSG: fields.String(description="Summary of reminder sending"),
        "sent_to": fields.List(fields.String(), description="Emails successfully sent"),
        "failed": fields.List(fields.Nested(_FAILED_EMAIL_MODEL), description="Emails that failed"),
    },
)


@api.route("/<class_id>/remind")
@api.param("class_id", "The ID of the class")
class SendClassReminder(Resource):

    @jwt_required()
    @api.doc(security="Bearer")
    @api.response(HTTPStatus.OK, "Reminder emails processed", REMINDER_RESPONSE_MODEL)
    @api.response(HTTPStatus.UNAUTHORIZED, "Missing or invalid JWT token", api.model("RemindUnauthorized", {MSG: fields.String()}))
    @api.response(HTTPStatus.FORBIDDEN, "Only the class trainer can send reminders", api.model("RemindForbidden", {MSG: fields.String()}))
    @api.response(HTTPStatus.NOT_FOUND, "Class not found", api.model("RemindNotFound", {MSG: fields.String()}))
    def post(self, class_id):
        """Send reminder emails to all members enrolled in a class (trainer only).

        The logged-in trainer must be the trainer assigned to the class.
        In SES sandbox mode, each recipient email must be individually verified
        in the AWS SES console before emails can be delivered.
        """
        claims = get_jwt()
        if claims.get("role") != "trainer":
            return {MSG: "Only trainers can send reminder emails"}, HTTPStatus.FORBIDDEN

        # Look up the class
        class_resource = ClassResource()
        fitness_class = class_resource.get_class_by_id(class_id, str)
        if fitness_class is None:
            return {MSG: "Class not found"}, HTTPStatus.NOT_FOUND

        # Verify the logged-in trainer is the one assigned to this class
        trainer_identity = get_jwt_identity()
        if fitness_class.get(CLASS_TRAINER_ID) != trainer_identity:
            return {MSG: "You are not the trainer assigned to this class"}, HTTPStatus.FORBIDDEN

        user_resource = UserResource()

        # Get enrolled members
        user_oids = fitness_class.get("user_ids", [])
        if not user_oids:
            return {MSG: "No members enrolled in this class", "sent_to": [], "failed": []}, HTTPStatus.OK

        members = user_resource.get_users_by_ids(user_oids)

        # Send a reminder email to each member
        successes = []
        failures = []
        for member in members:
            email = member.get("email", "")
            name = member.get("name", "")
            ok, err = send_class_reminder(
                member_email=email,
                member_name=name,
                class_info=fitness_class,
            )
            if ok:
                successes.append(email)
            else:
                failures.append({"email": email, "error": err})

        return {
            MSG: f"Reminders processed: {len(successes)} sent, {len(failures)} failed",
            "sent_to": successes,
            "failed": failures,
        }, HTTPStatus.OK