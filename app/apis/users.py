import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from uuid import uuid4

from bson import ObjectId
from flask import request
from flask_jwt_extended import get_jwt_identity
from flask_restx import Namespace, Resource, fields

from app.apis import MSG
from app.config import Config
from app.db.classes import ClassResource
from app.db.users import (
    USER_NOTIFICATION_PREFS,
    USER_TELEGRAM_CHAT_ID,
    UserResource,
)
from app.services.auth import member_required

api = Namespace("users", description="Endpoints for users")

# ---------------------------------------------------------------------------
# Shared response models
# ---------------------------------------------------------------------------

_ERROR_RESPONSE = api.model(
    "UserErrorResponse",
    {MSG: fields.String(description="Error description")},
)

# ---------------------------------------------------------------------------
# POST /users/me/book/<class_id> — book a class
# ---------------------------------------------------------------------------

_BOOK_OK_RESPONSE = api.model(
    "BookClassOK",
    {MSG: fields.String(example="Booked successfully")},
)

# ---------------------------------------------------------------------------
# GET /users/me/book — enrolled classes for current member
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

# ---------------------------------------------------------------------------
# PUT /users/me/notifications — update notification preferences
# ---------------------------------------------------------------------------

_NOTIFICATION_PREFS_MODEL = api.model(
    "NotificationPrefs",
    {
        "email":    fields.Boolean(description="Receive email reminders",    example=True),
        "telegram": fields.Boolean(description="Receive Telegram reminders", example=False),
    },
)

_UPDATE_NOTIFICATIONS_MODEL = api.model(
    "UpdateNotifications",
    {
        "notification_prefs": fields.Nested(
            _NOTIFICATION_PREFS_MODEL,
            description="Per-channel opt-in flags (all optional)",
        ),
    },
)

_TELEGRAM_LINK_RESPONSE = api.model(
    "TelegramLinkResponse",
    {
        "link": fields.String(description="Telegram deep link to open the bot and start linking"),
        "expires_in": fields.Integer(description="Seconds until the link expires", example=600),
    },
)

_UPDATE_NOTIFICATIONS_OK = api.model(
    "UpdateNotificationsOK",
    {MSG: fields.String(example="Notification preferences updated")},
)

# =========================================================================
# /users/me/book/<class_id>
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


# =========================================================================
# /users/me/book
# =========================================================================


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


# =========================================================================
# /users/me/notifications
# =========================================================================


@api.route("/me/notifications")
class MemberNotificationPrefs(Resource):

    @member_required
    @api.doc(security="Bearer")
    @api.expect(_UPDATE_NOTIFICATIONS_MODEL)
    @api.response(HTTPStatus.OK, "Preferences updated", _UPDATE_NOTIFICATIONS_OK)
    @api.response(HTTPStatus.BAD_REQUEST, "No valid fields supplied", _ERROR_RESPONSE)
    @api.response(HTTPStatus.NOT_FOUND, "User not found", _ERROR_RESPONSE)
    @api.response(HTTPStatus.UNAUTHORIZED, "JWT required", _ERROR_RESPONSE)
    def put(self):
        """Update notification preferences for the current member.

        To enable Telegram, use GET /users/me/telegram/link instead of setting telegram=true here —
        that flow automatically captures your chat ID via the bot.
        """
        user_id = get_jwt_identity()
        data    = request.json or {}

        channels = {
            k: bool(v)
            for k, v in data.get("notification_prefs", {}).items()
            if k in {"email", "telegram"}
        }
        if not channels:
            return (
                {MSG: "notification_prefs must include at least one of: email, telegram"},
                HTTPStatus.BAD_REQUEST,
            )

        user_resource = UserResource()

        if channels.get("telegram"):
            user = user_resource.get_user_by_id(user_id)
            if not user or not user.get(USER_TELEGRAM_CHAT_ID):
                return (
                    {MSG: "Cannot enable Telegram: no telegram_chat_id on file. Use GET /users/me/telegram/link to link your account first."},
                    HTTPStatus.BAD_REQUEST,
                )

        update_fields = {USER_NOTIFICATION_PREFS: channels}

        ok, err = user_resource.update_notification_prefs(user_id, update_fields)
        if not ok:
            status = HTTPStatus.NOT_FOUND if "not found" in err else HTTPStatus.BAD_REQUEST
            return {MSG: err}, status

        return {MSG: "Notification preferences updated"}, HTTPStatus.OK


# =========================================================================
# /users/me/telegram/link
# =========================================================================


@api.route("/me/telegram/link")
class TelegramLink(Resource):

    @member_required
    @api.doc(security="Bearer")
    @api.response(HTTPStatus.OK, "Deep link generated", _TELEGRAM_LINK_RESPONSE)
    @api.response(HTTPStatus.UNAUTHORIZED, "JWT required", _ERROR_RESPONSE)
    @api.response(HTTPStatus.INTERNAL_SERVER_ERROR, "Could not reach Telegram API", _ERROR_RESPONSE)
    def get(self):
        """Generate a one-time Telegram deep link that auto-captures your chat ID.

        Open the returned link on your phone, press Start in Telegram, and the server
        will automatically save your chat ID and enable Telegram notifications.
        The link expires in 10 minutes.
        """
        user_id = get_jwt_identity()
        token = str(uuid4())
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10)

        user_resource = UserResource()
        ok = user_resource.set_telegram_link_token(user_id, token, expires_at)
        if not ok:
            return {MSG: "User not found"}, HTTPStatus.NOT_FOUND

        try:
            url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/getMe"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                bot_info = json.loads(resp.read())
            bot_username = bot_info["result"]["username"]
        except Exception as e:
            return {MSG: f"Could not reach Telegram API: {e}"}, HTTPStatus.INTERNAL_SERVER_ERROR

        deep_link = f"https://t.me/{bot_username}?start={token}"
        return {"link": deep_link, "expires_in": 600}, HTTPStatus.OK


# =========================================================================
# /users/telegram/webhook  (called by Telegram — no JWT auth)
# =========================================================================


@api.route("/telegram/webhook")
class TelegramWebhook(Resource):

    def post(self):
        """Receive updates from Telegram. Not for direct use — called by Telegram's servers."""
        if Config.TELEGRAM_WEBHOOK_SECRET:
            secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if secret != Config.TELEGRAM_WEBHOOK_SECRET:
                return {}, HTTPStatus.FORBIDDEN

        update = request.json or {}
        message = update.get("message", {})
        text = message.get("text", "")
        chat_id = str(message.get("chat", {}).get("id", ""))

        if not text.startswith("/start ") or not chat_id:
            return {}, HTTPStatus.OK

        token = text[len("/start "):].strip()
        user_resource = UserResource()
        user = user_resource.find_user_by_link_token(token)
        if user:
            user_resource.save_telegram_chat_id(user["_id"], chat_id)

        return {}, HTTPStatus.OK
