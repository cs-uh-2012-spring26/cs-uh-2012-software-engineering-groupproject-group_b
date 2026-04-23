import re

import bcrypt

from app.db import DB
from app.db.utils import serialize_item, serialize_items, serialize_class
from bson import ObjectId
from app.db.classes import CLASS_COLLECTION
# User collection name and fields
USER_COLLECTION = "users"
USER_NAME = "name"
USER_EMAIL = "email"
USER_ROLE = "role"
USER_CONTACT = "contact"
USER_PASSWORD_HASH = "password_hash"
USER_CLASS_IDS = "class_ids"
USER_NOTIFICATION_PREFS = "notification_prefs"
USER_TELEGRAM_CHAT_ID   = "telegram_chat_id"

# Role constants
MEMBER_ROLE = "member"
TRAINER_ROLE = "trainer"

# ---------------------------------------------------------------------------
# Password policy
# ---------------------------------------------------------------------------
# Rules:
#   1. 10–128 characters long
#   2. At least one uppercase letter (A-Z)
#   3. At least one lowercase letter (a-z)
#   4. At least one digit (0-9)
#   5. At least one special character from: !@#$%^&*()-_=+[]{}|;:,.<>?/\
#   6. No whitespace characters
# ---------------------------------------------------------------------------
_MIN_LENGTH = 10
_MAX_LENGTH = 128
_RE_UPPERCASE = re.compile(r"[A-Z]")
_RE_LOWERCASE = re.compile(r"[a-z]")
_RE_DIGIT = re.compile(r"\d")
_RE_SPECIAL = re.compile(r"[!@#$%^&*()\-_=+\[\]{}|;:,.<>?/\\]")
_RE_WHITESPACE = re.compile(r"\s")

SPECIAL_CHARS = "!@#$%^&*()-_=+[]{}|;:,.<>?/\\"


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate a plaintext password against the project's password policy.

    Returns:
        (True, "")               – password is acceptable
        (False, reason_string)   – password is rejected; reason explains why
    """
    if len(password) < _MIN_LENGTH:
        return False, f"Password must be at least {_MIN_LENGTH} characters long"
    if len(password) > _MAX_LENGTH:
        return False, f"Password must not exceed {_MAX_LENGTH} characters"
    if _RE_WHITESPACE.search(password):
        return False, "Password must not contain spaces or whitespace"
    if not _RE_UPPERCASE.search(password):
        return False, "Password must contain at least one uppercase letter (A-Z)"
    if not _RE_LOWERCASE.search(password):
        return False, "Password must contain at least one lowercase letter (a-z)"
    if not _RE_DIGIT.search(password):
        return False, "Password must contain at least one digit (0-9)"
    if not _RE_SPECIAL.search(password):
        return (
            False,
            f"Password must contain at least one special character ({SPECIAL_CHARS})",
        )
    return True, ""


class UserResource:
    def __init__(self):
        self.collection = DB.get_collection(USER_COLLECTION)
        self.classes_collection = DB.get_collection(CLASS_COLLECTION)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_users(
        self,
        name: str | None = None,
        email: str | None = None,
        role: str | None = None,
    ):
        query = {}
        if name is not None:
            query[USER_NAME] = {"$regex": name}
        if email is not None:
            query[USER_EMAIL] = email
        if role is not None:
            query[USER_ROLE] = role

        users = self.collection.find(query)
        return serialize_items(list(users))


    def get_user_by_id(self, user_id: str):
        """
        Find ONE user document by its Mongo _id.

        Returns:
            dict (serialized) if found, else None
        """
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None

        user = self.collection.find_one({"_id": oid})
        return serialize_item(user)


    def get_user_by_email(self, email: str):
        """
        Find ONE raw user document by email (not serialized).
        Used internally for authentication; never returned directly to clients.
        """
        return self.collection.find_one({USER_EMAIL: email})

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def create_user(
        self,
        name: str,
        email: str,
        role: str,
        class_ids: list[str] | None = None,
    ):
        """Create a user without a password (legacy / admin seeding)."""
        user = {
            USER_NAME: name,
            USER_EMAIL: email,
            USER_ROLE: role,
            USER_CLASS_IDS: class_ids or [],
        }
        result = self.collection.insert_one(user)
        return result.inserted_id

    def register_user(self, name: str, email: str, password: str, role: str):
        """
        Register a new user account (member or trainer).

        - Validates the password against the password policy.
        - Rejects duplicate email addresses.
        - Stores a bcrypt hash of the password (never the plaintext).

        Returns:
            (str inserted_id, None)      – success
            (None, str error_message)    – failure
        """
        valid, reason = validate_password(password)
        if not valid:
            return None, reason

        if self.get_user_by_email(email) is not None:
            return None, "A user with that email already exists"

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        user = {
            USER_NAME: name,
            USER_EMAIL: email,
            USER_ROLE: role,
            USER_PASSWORD_HASH: pw_hash,
            USER_CLASS_IDS: [],
        }
        result = self.collection.insert_one(user)
        return str(result.inserted_id), None

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate_user(self, email: str, password: str):
        """
        Authenticate a user by email + password

        Returns a generic "Invalid email or password" message for both bad
        credentials and wrong role to avoid leaking account existence.

        Returns:
            (dict serialized_user, None)    – success
            (None, str error_message)       – failure
        """
        user = self.get_user_by_email(email)

        # Use a constant-time-safe path: always check password if user exists
        # to avoid timing attacks that reveal valid email addresses.
        dummy_hash = "$2b$12$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

        stored_hash = (user or {}).get(USER_PASSWORD_HASH, dummy_hash)
        try:
            password_ok = bcrypt.checkpw(password.encode(), stored_hash.encode())
        except (ValueError, TypeError):
            password_ok = False

        if user is None or not password_ok:
            return None, "Invalid email or password"

        return serialize_item(user), None

    # ------------------------------------------------------------------
    # Class enrollment
    # ------------------------------------------------------------------

    def get_users_by_ids(self, user_ids: list) -> list:
        """
        Fetch multiple users by a list of user IDs (strings or ObjectIds).
        Returns a list of serialized user dicts.
        """
        oids = [ObjectId(uid) if not isinstance(uid, ObjectId) else uid for uid in user_ids]
        users = self.collection.find({"_id": {"$in": oids}})
        return serialize_items(list(users))

    def add_class_to_user(self, user_id: str, class_id: str):
        """
        Add a class id into the user's class_ids list.

        Uses $addToSet so the same class id can't be added twice.

        Returns:
            True if user exists and update happened, False otherwise
        """
        try:
            user_oid = ObjectId(user_id)
            class_oid = ObjectId(class_id)
        except Exception:
            return False

        result = self.collection.update_one(
            {"_id": user_oid},
            {"$addToSet": {USER_CLASS_IDS: class_oid}},
        )
        return result.matched_count == 1
    
    def get_classes_by_user_id(self, user_id: str)->list[dict]:
        """
        Fetch all classes for a user by their ObjectId.
        Returns a list of serialized class dicts.
        """
        user_oid = ObjectId(user_id)
        user = self.collection.find_one({"_id": user_oid})
        if user is None:
            return []

        class_ids = user.get(USER_CLASS_IDS, [])
        if not class_ids:
            return []

        classes = self.classes_collection.find({"_id": {"$in": class_ids}})
        return [serialize_class(class_doc) for class_doc in classes]

    def update_notification_settings(
        self,
        user_id: str,
        notification_prefs: dict | None = None,
        telegram_chat_id: str | None = None,
    ) -> tuple[bool, str]:
        """
        Partial update — only fields explicitly passed (non-None) are written.
        Existing saved values are left untouched if not included in the call.
        """
        try:
            user_oid = ObjectId(user_id)
        except Exception:
            return False, "Invalid user ID"

        set_fields: dict = {}
        if notification_prefs is not None:
            set_fields[USER_NOTIFICATION_PREFS] = notification_prefs
        if telegram_chat_id is not None:
            set_fields[USER_TELEGRAM_CHAT_ID] = telegram_chat_id

        if not set_fields:
            return False, "No fields to update"

        result = self.collection.update_one({"_id": user_oid}, {"$set": set_fields})
        if result.matched_count == 0:
            return False, "User not found"
        return True, ""