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

from app.services.email_strategy import Emailstrategy
from app.services.class_creation import Classcreation
from app.services.member_access import MemberAccess
from app.services.auth import trainer_required

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
    },
)

_CLASS_CREATED_RESPONSE = api.model(
    "ClassCreated",
    {MSG: fields.String(example="Class created with id: 664f1e...")},
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
        "contact": fields.String(description="Member's contact number"),
    },
)


_FAILED_EMAIL = api.model(
    "FailedEmail",
    {
        "email": fields.String(description="Recipient email address"),
        "error": fields.String(description="SES error message"),
    },
)

_REMINDER_RESPONSE = api.model(
    "ReminderResponse",
    {
        MSG: fields.String(description="Summary of reminder sending"),
        "sent_to": fields.List(fields.String(), description="Emails successfully sent"),
        "failed": fields.List(fields.Nested(_FAILED_EMAIL), description="Emails that failed"),
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
        self.class_template = Classcreation()

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
        trainer_id = get_jwt_identity()

        success, message, status_code, class_id = self.class_template.create_class(
            request.json, trainer_id
        )
        return {MSG: message}, status_code

    @api.response(HTTPStatus.OK, "All upcoming classes", _CLASS_LIST_RESPONSE)
    def get(self):
        """Get all upcoming classes."""
        class_resource = ClassResource()
        classes = class_resource.get_all_upcoming_classes()
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
        self.class_template = MemberAccess()

    @trainer_required
    @api.doc(security="Bearer")
    @api.response(HTTPStatus.OK, "List of enrolled members", [_MEMBER_ITEM])
    @api.response(HTTPStatus.NOT_FOUND, "Class not found", _ERROR_RESPONSE)
    @api.response(HTTPStatus.UNAUTHORIZED, "JWT required", _ERROR_RESPONSE)
    @api.response(HTTPStatus.FORBIDDEN, "Trainer access required", _ERROR_RESPONSE)
    def get(self, class_id):
        """View the list of members enrolled in a class (trainer only)."""

        members, error = self.member_access.get_enrolled_members(class_id)

        if error:
            return {MSG: error}, HTTPStatus.NOT_FOUND
        return members, HTTPStatus.OK

# =========================================================================
# /classes/<class_id>/remind
# =========================================================================


@api.route("/<class_id>/remind")
@api.param("class_id", "The ID of the class")
class SendClassReminder(Resource):

    """ send reminders to enrolled members """

    def __init__(self, api=None):
        super().__init__(api)
        self.email_strategy = Emailstrategy()
        self.member_access = MemberAccess()

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

        members, error = self.member_access.get_enroled_members(class_id)

        if error:
            return {MSG: error}, HTTPStatus.NOT_FOUND

        if not members:
            return {MSG: "No members enrolled", "sent_to": [], "failed": []}, HTTPStatus.OK

        # Verify that trainer owns the class
        class_resource = ClassResource()
        fitness_class = class_resource.get_class_by_id(class_id)
        if fitness_class is None:
            return {MSG: "Class not found"}, HTTPStatus.NOT_FOUND

        trainer_identity = get_jwt_identity()
        if fitness_class.get(CLASS_TRAINER_ID) != trainer_identity:
            return {MSG: "You are not the trainer assigned to this class"}, HTTPStatus.FORBIDDEN

        successes = []
        failures = []
        for member in members:
            email = member.get("email", "")
            name = member.get("name", "")
            ok, err = self.email_strategy.send_reminder(
                email, name, fitness_class)

            if ok:
                successes.append(email)
            else:
                failures.append({"email": email, "error": err})

        return {
            MSG: f"Reminders processed: {len(successes)} sent, {len(failures)} failed",
            "sent_to": successes,
            "failed": failures,
        }, HTTPStatus.OK
