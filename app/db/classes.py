from app.db.utils import serialize_item, serialize_items
from app.db import DB


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
    def get_class(self):
        class_doc = self.collection.find({})
        return serialize_items(list(class_doc))