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
from app.recurrence import SUPPORTED_RECURRENCES
from app.services.auth import trainer_required
from app.services.notifications.dispatcher import NotificationDispatcher
from app.services.templates.recurring_class_creation import RecurringClassCreation
from app.services.templates.standard_class_creation import StandardClassCreation
from app.services.templates.standard_member_access import StandardMemberAccess

RECURRENCE = "recurrence"
RECURRENCE_END_DATE = "recurrence_end_date"

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

    """ Handles class creation and listing """

    def __init__(self, api=None):
        super().__init__(api)
        self.class_template = StandardClassCreation()
        self.recurring_template = RecurringClassCreation()

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

        recurrence = data.get(RECURRENCE)
        if recurrence:
            success, message, status_code, class_ids = self.recurring_template.create_recurring_class(data, trainer_id)
            if not success:
                return {MSG: message}, status_code
            return {MSG: message, "class_ids": class_ids}, status_code

        success, message, status_code, class_id = self.class_template.create_class(data, trainer_id)
        return {MSG: message}, status_code

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

    """ View members enrolled in a class """

    def __init__(self, api=None):
        super().__init__(api)
        self.class_template = StandardMemberAccess()

    @trainer_required
    @api.doc(security="Bearer")
    @api.response(HTTPStatus.OK, "List of enrolled members", [_MEMBER_ITEM])
    @api.response(HTTPStatus.NOT_FOUND, "Class not found", _ERROR_RESPONSE)
    @api.response(HTTPStatus.UNAUTHORIZED, "JWT required", _ERROR_RESPONSE)
    @api.response(HTTPStatus.FORBIDDEN, "Trainer access required", _ERROR_RESPONSE)
    def get(self, class_id):
        """View the list of members enrolled in a class (trainer only)."""
        members, error = self.class_template.get_enrolled_members(class_id)
        if error:
            return {MSG: error}, HTTPStatus.NOT_FOUND

        if not members:
            return []

        return members


# =========================================================================
# /classes/<class_id>/remind
# =========================================================================


@api.route("/<class_id>/remind")
@api.param("class_id", "The ID of the class")
class SendClassReminder(Resource):

    """ Send reminders to enrolled members """

    def __init__(self, api=None):
        super().__init__(api)
        self.member_access = StandardMemberAccess()

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
        members, fitness_class, error = self.member_access.get_enrolled_members_with_class(class_id)

        if error:
            return {MSG: error}, HTTPStatus.NOT_FOUND

        trainer_identity = get_jwt_identity()
        if fitness_class.get(CLASS_TRAINER_ID) != trainer_identity:
            return {MSG: "You are not the trainer assigned to this class"}, HTTPStatus.FORBIDDEN

        if not members:
            return {MSG: "No members enrolled in this class", "sent_to": [], "failed": []}, HTTPStatus.OK

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
