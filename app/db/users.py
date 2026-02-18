from app.db.utils import serialize_item, serialize_items
from app.db import DB
from bson import ObjectId

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

    def get_user_by_id(self,user_id: str):
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
