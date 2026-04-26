from app.db.constants import ID


def serialize_oid(oid):
    """
    Convert an ObjectId to its string representation.

    Args:
        oid (ObjectId): The ObjectId to be converted.

    Returns:
        str: The string representation of the ObjectId.
    """
    return str(oid)


def serialize_item(item):
    """
    Serializes the given item by converting its ID field to a serialized object ID.

    Args:
        item (dict): The item to be serialized. It must contain an 'ID' field.

    Returns:
        dict: The serialized item with the 'ID' field converted.
    """
    if item is not None:
        item[ID] = serialize_oid(item[ID])
    return item


def serialize_items(items):
    """
    Serializes a list of items.

    Args:
        items (list): A list of items to be serialized.

    Returns:
        list: A list of serialized items.
    """
    return [serialize_item(item) for item in items]

def serialize_class(class_doc: dict):
    return {
        "_id": serialize_oid(class_doc.get("_id")),
        "name": class_doc.get("name"),
        "description": class_doc.get("description"),
        "trainer_name": class_doc.get("trainer_name"),
        "date": class_doc.get("date"),
        "start_time": class_doc.get("start_time"),
        "end_time": class_doc.get("end_time"),
        "room_number": class_doc.get("room_number"),
        "capacity": class_doc.get("capacity"),
        "trainer_id": class_doc.get("trainer_id"),
        "user_ids": [serialize_oid(uid) for uid in class_doc.get("user_ids") or []]
    }