from datetime import datetime
from http import HTTPStatus

from flask import request
from flask_jwt_extended import get_jwt_identity
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
    CLASS_USER_IDS,
    TRAINER_NAME,
    ClassResource,
)
from app.db.users import UserResource

from app.recurrence import get_recurrence_strategy, SUPPORTED_RECURRENCES
from app.services.auth import trainer_required
from app.services.notifications.dispatcher import NotificationDispatcher

RECURRENCE = "recurrence"
RECURRENCE_END_DATE = "recurrence_end_date"
MAX_OCCURRENCES = 365

api = Namespace("classes", description="Endpoints for classes")

# ---------------------------------------------------------------------------
# Shared response models
# ---------------------------------------------------------------------------

_ERROR_RESPONSE = api.model(
    "ClassErrorResponse",
    {MSG: fields.String(description="Error description")},
)

# ---------------------------------------------------------------------------
# POST /classes — create a new class
# ---------------------------------------------------------------------------

_CLASS_CREATE_MODEL = api.model(
    "ClassCreate",
    {
        CLASS_NAME: fields.String(required=True, example="Yoga"),
        CLASS_DESCRIPTION: fields.String(required=True, example="Yoga class"),
        TRAINER_NAME: fields.String(required=True, example="John"),
        CLASS_DATE: fields.String(
            required=True,
            example="2026-03-01",
            description="Date of the class (YYYY-MM-DD), must be today or in the future",
        ),
        CLASS_START_TIME: fields.String(
            required=True, example="10:00", description="Start time (HH:MM)"
        ),
        CLASS_END_TIME: fields.String(
            required=True, example="11:00", description="End time (HH:MM)"
        ),
        CLASS_ROOM_NUMBER: fields.String(required=True, example="101"),
        CLASS_CAPACITY: fields.Integer(required=True, example=10),
        RECURRENCE: fields.String(
            required=False,
            example="weekly",
            description=f"Recurrence pattern. Supported: {SUPPORTED_RECURRENCES}. Omit for a one-off class.",
        ),
        RECURRENCE_END_DATE: fields.String(
            required=False,
            example="2030-06-01",
            description="Last date (inclusive) for the recurring series (YYYY-MM-DD). Required when 'recurrence' is set.",
        ),
    },
)

_CLASS_CREATED_RESPONSE = api.model(
    "ClassCreated",
    {MSG: fields.String(example="Class created with id: 664f1e...")},
)

_RECURRING_CLASS_RESPONSE = api.model(
    "RecurringClassCreated",
    {
        MSG: fields.String(description="Summary of recurring class creation"),
        "class_ids": fields.List(fields.String(), description="IDs of all created class instances"),
    },
)

# ---------------------------------------------------------------------------
# GET /classes — list upcoming classes
# ---------------------------------------------------------------------------

_CLASS_ITEM = api.model(
    "ClassItem",
    {
        "_id": fields.String(description="Class ID"),
        CLASS_NAME: fields.String(),
        CLASS_DESCRIPTION: fields.String(),
        TRAINER_NAME: fields.String(),
        CLASS_START_TIME: fields.String(),
        CLASS_END_TIME: fields.String(),
        CLASS_ROOM_NUMBER: fields.String(),
        CLASS_CAPACITY: fields.Integer(),
    },
)

_CLASS_LIST_RESPONSE = api.model(
    "ClassListResponse",
    {
        MSG: fields.String(example="All upcoming classes"),
        "classes": fields.List(fields.Nested(_CLASS_ITEM)),
    },
)

# ---------------------------------------------------------------------------
# GET /classes/<class_id> — enrolled members
# ---------------------------------------------------------------------------

_MEMBER_ITEM = api.model(
    "EnrolledMember",
    {
        "name": fields.String(description="Member's full name"),
        "email": fields.String(description="Member's email address"),
        "telegram_chat_id": fields.String(description="Member's Telegram chat ID"),
    },
)


_FAILED_NOTIFICATION = api.model(
    "FailedNotification",
    {
        "member": fields.String(description="Member email"),
        "errors": fields.List(fields.String(), description="Per-channel error messages"),
    },
)

_REMINDER_RESPONSE = api.model(
    "ReminderResponse",
    {
        MSG: fields.String(description="Summary of reminder sending"),
        "sent_to": fields.List(fields.String(), description="Emails of members fully notified"),
        "failed": fields.List(
            fields.Nested(_FAILED_NOTIFICATION),
            description="Members with at least one channel failure",
        ),
    },
)

# =========================================================================
# /classes
# =========================================================================


@api.route("/")
class ClassList(Resource):

    @trainer_required
    @api.doc(security="Bearer")
    @api.expect(_CLASS_CREATE_MODEL)
    @api.response(HTTPStatus.OK, "Class created", _CLASS_CREATED_RESPONSE)
    @api.response(HTTPStatus.BAD_REQUEST, "Missing or invalid fields", _ERROR_RESPONSE)
    @api.response(HTTPStatus.NOT_ACCEPTABLE, "Semantic validation failed", _ERROR_RESPONSE)
    @api.response(HTTPStatus.UNAUTHORIZED, "JWT required", _ERROR_RESPONSE)
    @api.response(HTTPStatus.FORBIDDEN, "Trainer access required", _ERROR_RESPONSE)
    def post(self):
        """Create a new class. Requires a trainer JWT."""
        data = request.json
        trainer_id = get_jwt_identity()

        name = data[CLASS_NAME]
        description = data[CLASS_DESCRIPTION]
        trainer_name = data[TRAINER_NAME]
        date_str = data[CLASS_DATE]
        start_time = data[CLASS_START_TIME]
        end_time = data[CLASS_END_TIME]
        room_number = data[CLASS_ROOM_NUMBER]
        capacity = data[CLASS_CAPACITY]

        # capacity validation
        if capacity < 1:
            return {MSG: "Capacity must be at least 1"}, HTTPStatus.NOT_ACCEPTABLE

        # time validation
        try:
            start_t = datetime.strptime(start_time, "%H:%M").time()
            end_t = datetime.strptime(end_time, "%H:%M").time()
        except (TypeError, ValueError):
            return {MSG: "Invalid time format, expected HH:MM"}, HTTPStatus.NOT_ACCEPTABLE

        if start_t >= end_t:
            return {MSG: "Start time must be before end time"}, HTTPStatus.NOT_ACCEPTABLE

        try:
            date_input = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return {MSG: "Invalid date format, expected YYYY-MM-DD"}, HTTPStatus.NOT_ACCEPTABLE

        now = datetime.now()
        if date_input < now.date():
            return {MSG: "Date must be today or in the future"}, HTTPStatus.NOT_ACCEPTABLE

        if date_input == now.date() and start_t <= now.time():
            return {MSG: "Start time must be in the future for today's classes"}, HTTPStatus.NOT_ACCEPTABLE

        start_dt = datetime.combine(date_input, start_t)
        end_dt = datetime.combine(date_input, end_t)


        new_class = {
            CLASS_NAME: name,
            CLASS_DESCRIPTION: description,
            TRAINER_NAME: trainer_name,
            CLASS_DATE: date_str,
            CLASS_START_TIME: start_time,
            CLASS_END_TIME: end_time,
            CLASS_ROOM_NUMBER: room_number,
            CLASS_CAPACITY: capacity,
            CLASS_TRAINER_ID: trainer_id,
            CLASS_USER_IDS: [],
        }

        recurrence = data.get(RECURRENCE)
        class_resource = ClassResource()

        if recurrence:
            strategy = get_recurrence_strategy(recurrence)
            if strategy is None:
                return {MSG: f"Invalid recurrence type '{recurrence}'. Supported: {SUPPORTED_RECURRENCES}"}, HTTPStatus.NOT_ACCEPTABLE

            recurrence_end_date_str = data.get(RECURRENCE_END_DATE)
            if not recurrence_end_date_str:
                return {MSG: "recurrence_end_date is required when recurrence is specified"}, HTTPStatus.BAD_REQUEST

            try:
                recurrence_end = datetime.strptime(recurrence_end_date_str, "%Y-%m-%d").date()
            except (TypeError, ValueError):
                return {MSG: "Invalid recurrence_end_date format, expected YYYY-MM-DD"}, HTTPStatus.NOT_ACCEPTABLE

            if recurrence_end < date_input:
                return {MSG: "recurrence_end_date must be on or after the class start date"}, HTTPStatus.NOT_ACCEPTABLE

            occurrence_dates = list(strategy.generate_dates(date_input, recurrence_end))
            if len(occurrence_dates) > MAX_OCCURRENCES:
                return {MSG: f"Recurrence generates {len(occurrence_dates)} classes, exceeding the maximum of {MAX_OCCURRENCES}"}, HTTPStatus.NOT_ACCEPTABLE

            class_ids = class_resource.create_recurring_classes(new_class, occurrence_dates)
            return {MSG: f"{len(class_ids)} recurring classes created", "class_ids": class_ids}, HTTPStatus.OK

        class_id = class_resource.create_class(new_class)
        return {MSG: f"Class created with id: {class_id}"}, HTTPStatus.OK

    @api.response(HTTPStatus.OK, "All upcoming classes", _CLASS_LIST_RESPONSE)
    def get(self):
        """Get all upcoming classes."""
        class_resource = ClassResource()
        classes = class_resource.get_all_upcoming_classes()
        for c in classes:
            c.pop("trainer_id", None)
            c.pop("user_ids", None)
        return {MSG: "All upcoming classes", "classes": classes}, HTTPStatus.OK


# =========================================================================
# /classes/<class_id>
# =========================================================================


@api.route("/<class_id>/members")
@api.param("class_id", "The ID of the class")
class ClassDetail(Resource):

    @trainer_required
    @api.doc(security="Bearer")
    @api.response(HTTPStatus.OK, "List of enrolled members", [_MEMBER_ITEM])
    @api.response(HTTPStatus.NOT_FOUND, "Class not found", _ERROR_RESPONSE)
    @api.response(HTTPStatus.UNAUTHORIZED, "JWT required", _ERROR_RESPONSE)
    @api.response(HTTPStatus.FORBIDDEN, "Trainer access required", _ERROR_RESPONSE)
    def get(self, class_id):
        """View the list of members enrolled in a class (trainer only)."""
        class_resource = ClassResource()
        fitness_class = class_resource.get_class_by_id(class_id)
        if fitness_class is None:
            return {MSG: "Class not found"}, HTTPStatus.NOT_FOUND

        user_oids = fitness_class.get("user_ids", [])
        if not user_oids:
            return []

        user_resource = UserResource()
        members = user_resource.get_users_by_ids(user_oids)

        return [
            {
                "name": m.get("name", ""),
                "email": m.get("email", ""),
                "telegram_chat_id": m.get("telegram_chat_id"),
            }
            for m in members
        ]

# =========================================================================
# /classes/<class_id>/remind
# =========================================================================


@api.route("/<class_id>/remind")
@api.param("class_id", "The ID of the class")
class SendClassReminder(Resource):

    @trainer_required
    @api.doc(security="Bearer")
    @api.response(HTTPStatus.OK, "Reminder emails processed", _REMINDER_RESPONSE)
    @api.response(HTTPStatus.UNAUTHORIZED, "JWT required", _ERROR_RESPONSE)
    @api.response(HTTPStatus.FORBIDDEN, "Trainer access required", _ERROR_RESPONSE)
    @api.response(HTTPStatus.NOT_FOUND, "Class not found", _ERROR_RESPONSE)
    def post(self, class_id):
        """Send reminder emails to all members enrolled in a class (trainer only).

        The logged-in trainer must be the trainer assigned to the class.
        In SES sandbox mode, each recipient email must be individually verified
        in the AWS SES console before emails can be delivered.
        """
        class_resource = ClassResource()
        fitness_class = class_resource.get_class_by_id(class_id)
        if fitness_class is None:
            return {MSG: "Class not found"}, HTTPStatus.NOT_FOUND

        trainer_identity = get_jwt_identity()
        if fitness_class.get(CLASS_TRAINER_ID) != trainer_identity:
            return {MSG: "You are not the trainer assigned to this class"}, HTTPStatus.FORBIDDEN

        user_resource = UserResource()

        user_oids = fitness_class.get("user_ids", [])
        if not user_oids:
            return {MSG: "No members enrolled in this class", "sent_to": [], "failed": []}, HTTPStatus.OK

        members = user_resource.get_users_by_ids(user_oids)

        dispatcher = NotificationDispatcher()
        successes: list[str] = []
        failures:  list[dict] = []

        for member in members:
            all_ok, errors = dispatcher.dispatch_to_member(member, fitness_class)
            if all_ok:
                successes.append(member.get("email", ""))
            else:
                failures.append({"member": member.get("email", ""), "errors": errors})

        return {
            MSG: f"Reminders processed: {len(successes)} sent, {len(failures)} with failures",
            "sent_to": successes,
            "failed":  failures,
        }, HTTPStatus.OK
