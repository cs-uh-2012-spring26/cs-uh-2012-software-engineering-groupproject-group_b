from app.db.utils import serialize_item, serialize_items
from app.db import DB

# User collection name and fields
USER_COLLECTION = "users"
USER_NAME = "name"
USER_EMAIL = "email"
USER_ROLE = "role"
USER_CONTACT = "contact"

USER_CLASS_IDS = "class_ids"



class UserResource:
    def __init__(self):
        self.collection = DB.get_collection(USER_COLLECTION)

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

    def create_user(
        self,
        name: str,
        email: str,
        role: str,
        class_ids: list[str] | None = None,
    ):
        user = {
            USER_NAME: name,
            USER_EMAIL: email,
            USER_ROLE: role,
            USER_CLASS_IDS: class_ids or [],
        }
        result = self.collection.insert_one(user)
        return result.inserted_id
