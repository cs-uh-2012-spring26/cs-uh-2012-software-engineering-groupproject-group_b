from app.db.utils import serialize_items
from app.db import DB

# Collection name
BOOKING_COLLECTION = "bookings"

# Field names
CLASS_ID = "class_id"
USER_NAME = "user_name"
USER_EMAIL = "user_email"
USER_CONTACT = "user_contact"


class BookingResource:

    def __init__(self):
        self.collection = DB.get_collection(BOOKING_COLLECTION)

    def get_class_members(self, class_id: str):
        """Return all booked members for the given class_id."""
        members = self.collection.find({CLASS_ID: class_id})
        return serialize_items(list(members))

    def delete_all_bookings(self):
        self.collection.delete_many({})

    def add_multiple_bookings(self, bookings: list[dict]):
        if not bookings:
            return
        self.collection.insert_many(bookings)
