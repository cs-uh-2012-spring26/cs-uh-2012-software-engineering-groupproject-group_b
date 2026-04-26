from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.db.classes import ClassResource
from app.recurrence import get_recurrence_strategy, SUPPORTED_RECURRENCES
from app.services.templates.class_creation_template import ClassCreationTemplate


class RecurringClassCreation(ClassCreationTemplate):
    MAX_OCCURRENCES = 365

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

    def save_recurring_classes(self, class_doc: Dict, occurrence_dates: list) -> List[str]:
        class_resource = ClassResource()
        return class_resource.create_recurring_classes(class_doc, occurrence_dates)

    def create_recurring_class(self, data: Dict, trainer_id: str) -> Tuple[bool, str, int, Optional[List[str]]]:
        error = self.validate_capacity(data)
        if error:
            return False, error, 406, None

        error = self.validate_time(data)
        if error:
            return False, error, 406, None

        error = self.validate_date(data)
        if error:
            return False, error, 406, None

        recurrence = data.get("recurrence")
        strategy = get_recurrence_strategy(recurrence)
        if strategy is None:
            return False, f"Invalid recurrence type '{recurrence}'. Supported: {SUPPORTED_RECURRENCES}", 406, None

        recurrence_end_date_str = data.get("recurrence_end_date")
        if not recurrence_end_date_str:
            return False, "recurrence_end_date is required when recurrence is specified", 400, None

        try:
            recurrence_end = datetime.strptime(recurrence_end_date_str, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return False, "Invalid recurrence_end_date format, expected YYYY-MM-DD", 406, None

        date_input = datetime.strptime(data["date"], "%Y-%m-%d").date()
        if recurrence_end < date_input:
            return False, "recurrence_end_date must be on or after the class start date", 406, None

        occurrence_dates = list(strategy.generate_dates(date_input, recurrence_end))
        if len(occurrence_dates) > self.MAX_OCCURRENCES:
            return False, f"Recurrence generates {len(occurrence_dates)} classes, exceeding the maximum of {self.MAX_OCCURRENCES}", 406, None

        start_dt, end_dt = self.parse_datetime(data)
        class_doc = self.class_document(data, trainer_id, start_dt, end_dt)
        class_ids = self.save_recurring_classes(class_doc, occurrence_dates)

        return True, f"{len(class_ids)} recurring classes created", 200, class_ids
