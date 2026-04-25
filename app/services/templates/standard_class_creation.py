from app.services.templates.class_creation_template import ClassCreationTemplate
from app.db.classes import ClassResource
from datetime import datetime
from typing import Dict, Tuple, Optional


class StandardClassCreation(ClassCreationTemplate):
    def class_document(self, data: Dict, trainer_id: str, start_dt: datetime, end_dt: datetime) -> Dict:

        return {
            "name": data["name"],
            "description": data["description"],
            "trainer_name": data["trainer_name"],
            "date": data["date"],
            "start_time": data["start_time"],
            "end_time": data["end_time"],
            "room_number": data["room_number"],
            "capacity": data["capacity"],
            "trainer_id": trainer_id,
            "user_ids": [],
        }

    def save_class(self, class_doc: Dict) -> Optional[str]:
        class_resource = ClassResource()
        return class_resource.create_class(class_doc)
