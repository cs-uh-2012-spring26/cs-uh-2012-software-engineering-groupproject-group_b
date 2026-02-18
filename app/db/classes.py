from app.db.utils import serialize_item, serialize_items
from app.db import DB
from bson import ObjectId


# Class collection
CLASS_COLLECTION = "classes"
CLASS_NAME = "name"
CLASS_START_TIME = "start_time"
CLASS_END_TIME = "end_time"
CLASS_DESCRIPTION = "description"
CLASS_ROOM_NUMBER = "room_number"
CLASS_CAPACITY = "capacity"

CLASS_USER_IDS = "user_ids"

class ClassResource:
    def __init__(self):
        self.collection = DB.get_collection(CLASS_COLLECTION)

    def create_class(
        self,
        name: str,
        start_time: str,
        end_time: str,
        description: str,
        room_number: str,
        capacity: int,
        user_ids: list[str] | None = None,
    ):
        class_doc = {
            CLASS_NAME: name,
            CLASS_START_TIME: start_time,
            CLASS_END_TIME: end_time,
            CLASS_DESCRIPTION: description,
            CLASS_ROOM_NUMBER: room_number,
            CLASS_CAPACITY: capacity,
            CLASS_USER_IDS: user_ids or [],
        }
        result = self.collection.insert_one(class_doc)
        return result.inserted_id

    def get_class_by_id(self,class_id,str):
        """
        Find ONE class document by its Mongo _id.

        class_id (str): string version of ObjectId from API request

        Returns:
            dict (serialized) if found, else None
        """
        try: 
            oid = ObjectId(class_id)
        except Exception:
            return None

        class_doc = self.collection.find_one({"_id": oid})
        return serialize_item(class_doc)

    def add_user_to_class(self, class_id: str, user_id: str):
        """
        Add a user to the class's booked list.

        Returns one of these strings so the API layer knows what happened:
            "CLASS_NOT_FOUND"
            "ALREADY_BOOKED"
            "CLASS_FULL"
            "BOOKED"
        """
        try:
            class_oid = ObjectId(class_id)
            user_oid = ObjectId(user_id)
        except Exception:
            return "CLASS_NOT_FOUND" 

        class_doc = self.collection.find_one({"_id": class_oid})
        if class_doc is None:
            return "CLASS_NOT_FOUND"

        user_ids = class_doc.get(CLASS_USER_IDS, [])

        capacity = class_doc.get(CLASS_CAPACITY, 0)

        if user_oid in user_ids:
            return "ALREADY_BOOKED"

        if isinstance(capacity, int) and len(user_ids) >= capacity:
            return "CLASS_FULL"

        self.collection.update_one(
            {"_id": class_oid},                
            {"$push": {CLASS_USER_IDS: user_oid}},  
        )

        return "BOOKED"



    def get_class(self):
        class_doc = self.collection.find({})
        return serialize_items(list(class_doc))