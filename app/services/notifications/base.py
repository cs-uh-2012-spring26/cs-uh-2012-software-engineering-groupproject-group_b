from abc import ABC, abstractmethod


class NotificationService(ABC):

    def _build_message(self, member_name: str, class_info: dict) -> dict:
        name    = class_info.get("name", "")
        date    = class_info.get("date", "")
        start   = class_info.get("start_time", "")
        end     = class_info.get("end_time", "")
        room    = class_info.get("room_number", "")
        trainer = class_info.get("trainer_name", "")
        desc    = class_info.get("description", "")

        subject = f"Reminder: Upcoming Class – {name}"
        body = (
            f"Dear {member_name},\n\n"
            f"This is a reminder for your upcoming fitness class:\n\n"
            f"  Class:       {name}\n"
            f"  Description: {desc}\n"
            f"  Trainer:     {trainer}\n"
            f"  Date:        {date}\n"
            f"  Time:        {start} – {end}\n"
            f"  Room:        {room}\n\n"
            f"We look forward to seeing you!\n"
        )
        return {"subject": subject, "body": body}

    @abstractmethod
    def send(self, member: dict, class_info: dict) -> tuple[bool, str]:
        """
        Send a class reminder to one member.

        Args:
            member:     Serialized user doc. Guaranteed: "name", "email".
                        Optional: "phone", "telegram_chat_id", "notification_prefs".
            class_info: Serialized class doc.

        Returns:
            (True, "")              – delivered successfully
            (False, error_message)  – delivery failed
        """
