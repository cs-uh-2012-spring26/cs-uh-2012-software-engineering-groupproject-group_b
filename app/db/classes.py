from datetime import datetime
from uuid import uuid4

from app.db.utils import serialize_item, serialize_items, serialize_class
from app.db import DB
from bson import ObjectId


# fix: remove comment -> return type indicator. 
#add get_all_upcoming_classes to return [] or list of upcoming classes

# Class collection
CLASS_COLLECTION = "classes"
CLASS_NAME = "name"
TRAINER_NAME = "trainer_name"
CLASS_DATE = "date"
CLASS_START_TIME = "start_time"
CLASS_END_TIME = "end_time"
CLASS_DESCRIPTION = "description"
CLASS_ROOM_NUMBER = "room_number"
CLASS_CAPACITY = "capacity"

CLASS_USER_IDS = "user_ids"
CLASS_TRAINER_ID = "trainer_id"
CLASS_RECURRENCE_GROUP_ID = "recurrence_group_id"

class ClassResource:
    def __init__(self):
        self.collection = DB.get_collection(CLASS_COLLECTION)

    def create_class(self,class_data: dict)->str:
        class_doc = {
            CLASS_NAME: class_data[CLASS_NAME],
            CLASS_DESCRIPTION: class_data[CLASS_DESCRIPTION],
            TRAINER_NAME: class_data[TRAINER_NAME],
            CLASS_DATE: class_data[CLASS_DATE],
            CLASS_TRAINER_ID: class_data[CLASS_TRAINER_ID],
            CLASS_START_TIME: class_data[CLASS_START_TIME],
            CLASS_END_TIME: class_data[CLASS_END_TIME],
            CLASS_ROOM_NUMBER: class_data[CLASS_ROOM_NUMBER],
            CLASS_CAPACITY: class_data[CLASS_CAPACITY],
            CLASS_USER_IDS: [],
        }
        result = self.collection.insert_one(class_doc)
        return result.inserted_id


    def create_recurring_classes(self, base_data: dict, occurrence_dates: list) -> list[str]:
        """Bulk-insert one class document per occurrence date. Returns list of inserted IDs."""
        if not occurrence_dates:
            return []
        group_id = str(uuid4())
        docs = [
            {
                **base_data,
                CLASS_DATE: occ_date.strftime("%Y-%m-%d"),
                CLASS_USER_IDS: [],
                CLASS_RECURRENCE_GROUP_ID: group_id,
            }
            for occ_date in occurrence_dates
        ]
        result = self.collection.insert_many(docs)
        return [str(oid) for oid in result.inserted_ids]

    def get_all_upcoming_classes(self)->list[dict]:
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        current_time_str = now.strftime("%H:%M")

        classes = self.collection.find({
            "$or": [
                {CLASS_DATE: {"$gt": today_str}},
                {CLASS_DATE: today_str, CLASS_START_TIME: {"$gt": current_time_str}},
            ]
        }).sort([(CLASS_DATE, 1), (CLASS_START_TIME, 1)])

        if classes is None:
            return []
        return [serialize_class(class_doc) for class_doc in classes]

    def get_class_by_id(self,class_id:str)->dict|None:
        try: 
            oid = ObjectId(class_id)
        except Exception:
            return None

        class_doc = self.collection.find_one({"_id": oid})
        return serialize_class(class_doc)

    def add_user_to_class(self, class_id: str, user_id: str)->str:
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


