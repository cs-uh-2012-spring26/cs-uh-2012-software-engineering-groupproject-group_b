from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Tuple, Optional


class Classcreationtemplate(ABC):

    """ Template method for class creation """

    def create_class(self, data: Dict, trainer_id: str) -> Tuple[bool, str, int, Optional[str]]:
        """ Template method that defines the algorithm skeleton """

        error = self._validate_capacity(data)
        if error:
            return False, error, 406, None

        error = self._validate_time(data)
        if error:
            return False, error, 406, None

        error = self._validate_date(data)
        if error:
            return False, error, 406, None
        # parse datetime
        start_dt, end_dt = self._parse_datetime(data)

        # Build class document
        class_doc = self.class_document(data, trainer_id, start_dt, end_dt)
        class_id = self.save_class(class_doc)

        if not class_id:
            return False, "Failed to create class", 500, None
        return True, f"Class created with id: {class_id}", 200, class_id

    def validate_capacity(self, data: Dict) -> Optional[str]:
        capacity = data.get("capacity", 0)
        if capacity < 1:
            return "Capacity must be atleast 1"
        return None

    def validate_time_format(self, data: Dict) -> Optional[str]:
        try:
            start_t = datetime.strptime(data["start_time"], "%H:%M").time()
            end_t = datetime.strptime(data["end_time"], "%H:%M").time()
        except (TypeError, ValueError):
            return "Invalid time format, expected HH:MM"

        if start_t >= end_t:
            return "Start time must be before end time"
        return None

    def validate_date_format(self, data: Dict) -> Optional[str]:
        try:
            date_input = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return "Invalid date format, expected YYYY-MM-DD"

        now = datetime.now()
        if date_input < now.date():
            return "Date must be today or in the future"

        try:
            start_t = datetime.strptime(data["start_time"], "%H:%M").time()
        except:
            return None

        if date_input == now.date() and start_t <= now.time():
            return "Start time must be in the future for today classes"
        return None

    def parse_datetime(self, data: Dict) -> Tuple[datetime, datetime]:
        date_input = datetime.strptime(data["date"], "%Y-%m-%d").date()
        start_t = datetime.strptime(data["start_time"], "%H:%M").time()
        end_t = datetime.strptime(data["end_time"], "%H:%M").time()
        return datetime.combine(date_input, start_t), datetime.combine(date_input, end_t)

    # Hook methods
    @abstractmethod
    def class_document(self, data: Dict, trainer_id: str, start_dt: datetime, end_dt: datetime) -> Dict:
        pass

    def save_class(self, class_doc: Dict) -> Optional[str]:
        pass
